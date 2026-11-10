"""Nodos del cierre de la compra: cotizar, esperar la confirmación del usuario,
registrar el pedido y, si la tienda cambió entre medias, proponer una salida."""

from __future__ import annotations

import sqlite3
from typing import Any, Literal

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command, interrupt

from shopping_agent.agent import guards, prompt, texts
from shopping_agent.agent.deps import Deps, cart_id
from shopping_agent.agent.nodes.actions import SEARCH_DEPTH
from shopping_agent.agent.nodes.steps import record, rejected, step
from shopping_agent.agent.state import (
    AgentState,
    Candidate,
    IssueRecord,
    Message,
    Order,
    Quote,
    Step,
    Update,
    cart_total,
    issue_record,
    new_turn,
)
from shopping_agent.store import ops
from shopping_agent.store.ops import OpResult

ALTERNATIVES = 3
STOCK_CODES = (ops.OUT_OF_STOCK, ops.INSUFFICIENT_STOCK)
REQUOTE_CODES = (ops.PRICE_CHANGED, ops.STALE_QUOTE, ops.BUDGET_EXCEEDED)  # se arreglan cotizando otra vez


def cotizar(state: AgentState, config: RunnableConfig, *, deps: Deps) -> Command[Literal["confirmar", "interpretar"]]:
    """Congela el carrito en una cotización y redacta lo que se repite al usuario."""
    with deps.shop() as conn:
        result = ops.create_quote(conn, cart_id(config), state.budget_cents)
        cart = deps.cart(conn, cart_id(config))
    if not result.ok:
        return Command(update=rejected(state, result.issues, cart=cart), goto="interpretar")

    data = result.data
    items = [deps.cart_line(item) for item in data["items"]]
    message = texts.quote_message(items, data["total_cents"], data["budget_cents"])
    quote = Quote(
        quote_id=data["quote_id"],
        items=items,
        total_cents=data["total_cents"],
        budget_cents=data["budget_cents"],
        message=message,
    )
    entry = step(state, True, "cotización creada; falta la confirmación del usuario.", result=quote["quote_id"])
    update = record(
        state,
        entry,
        cart=cart,
        quote=quote,
        response=message,
        messages=[Message(role="assistant", content=message)],
        pending_clarification=None,
    )
    return Command(update=update, goto="confirmar")


def confirmar(state: AgentState) -> Command[Literal["registrar_pedido", "responder", "iniciar_turno"]]:
    """Pausa hasta que el usuario conteste a la cotización. Sin efectos antes del ``interrupt``."""
    quote = state.quote
    assert quote is not None  # a este nodo solo se llega desde cotizar
    answer = interrupt(
        {
            "type": "order_confirmation",
            "message": quote["message"],
            "quote_id": quote["quote_id"],
            "total_cents": quote["total_cents"],
        }
    )
    text = str(answer or "").strip()
    verdict = guards.classify_confirmation(text)
    if verdict == "otro":
        # No es un sí ni un no: no se compra nada y el mensaje se atiende como turno nuevo.
        return Command(update={"user_input": text}, goto="iniciar_turno")
    update = new_turn(state, text)
    if verdict == "si":
        return Command(update=update, goto="registrar_pedido")
    return Command(update={**update, "quote": None, "response": texts.CANCELLED}, goto="responder")


def registrar_pedido(
    state: AgentState, config: RunnableConfig, *, deps: Deps
) -> Command[Literal["responder", "proponer_alternativa"]]:
    """Confirma la cotización en una transacción que vuelve a comprobarlo todo."""
    pending = state.quote or state.order  # la cotización a confirmar o, si se repite el sí, la ya confirmada
    assert pending is not None
    with deps.shop() as conn:
        result = ops.confirm_quote(conn, pending["quote_id"])
        cart = deps.cart(conn, cart_id(config))
    entry = _confirmation_step(state, pending["quote_id"], result)
    update: Update = {"ops_log": [entry], "cart": cart, "quote": None}
    if not result.ok:
        return Command(update={**update, "confirm_issues": entry["issues"]}, goto="proponer_alternativa")
    order = _order(deps, result.data)
    return Command(update={**update, "order": order, "response": order["message"]}, goto="responder")


def _confirmation_step(state: AgentState, quote_id: str, result: OpResult) -> Step:
    """La confirmación no la decide el LLM: se anota como una operación propia."""
    if not result.ok:
        summary = prompt.rejection(result.issues)
    elif result.data["already_confirmed"]:
        summary = "el pedido ya estaba registrado; no se duplicó"
    else:
        summary = "pedido registrado"
    return Step(
        turn=state.turn,
        tool="confirmar_pedido",
        args={"quote_id": quote_id},
        reason="el usuario confirmó la cotización",
        ok=result.ok,
        summary=summary,
        result=result.data or None,
        issues=[issue_record(issue) for issue in result.issues],
    )


def _order(deps: Deps, data: dict[str, Any]) -> Order:
    items = [deps.priced_line(item) for item in data["items"]]
    if data["already_confirmed"]:
        message = texts.order_already_registered(data["order_id"], data["total_cents"])
    else:
        message = texts.order_message(data["order_id"], items, data["total_cents"])
    return Order(
        order_id=data["order_id"],
        quote_id=data["quote_id"],
        items=items,
        total_cents=data["total_cents"],
        message=message,
    )


def proponer_alternativa(state: AgentState, *, deps: Deps) -> Update:
    """La confirmación falló: explica qué cambió y propone una salida, sin LLM."""
    issues = state.confirm_issues
    parts = [texts.NOT_REGISTERED, *(_what_changed(issue, deps) for issue in issues)]
    options = _alternatives(state, deps)
    if options:
        parts.append(texts.alternatives(options))
    if any(issue["code"] in REQUOTE_CODES for issue in issues):
        parts.append(texts.NEW_QUOTE_OFFER)
    parts.append(texts.WHAT_NEXT)

    update: Update = {"response": " ".join(parts)}
    if options:
        update.update(candidates=options, last_query=None)
    return update


def _alternatives(state: AgentState, deps: Deps) -> list[Candidate]:
    """Hasta ``ALTERNATIVES`` productos parecidos a los que faltan, entre todos los rechazos."""
    options: list[Candidate] = []
    with deps.shop() as conn:
        for issue in filter(_is_stock_issue, state.confirm_issues):
            options += _similar_in_stock(state, issue, deps, conn, taken=options)
    return options


def _is_stock_issue(issue: IssueRecord) -> bool:
    return issue["product_id"] is not None and issue["code"] in STOCK_CODES


def _what_changed(issue: IssueRecord, deps: Deps) -> str:
    """Lo que se le dice al usuario sobre un rechazo de la confirmación."""
    product_id = issue["product_id"]
    if product_id is None or issue["code"] not in STOCK_CODES:
        return issue["message"]
    title = deps.search.title(product_id)
    wanted, available = issue["details"]["requested"], issue["details"]["available"]
    return texts.less_stock(title, available, wanted) if available else texts.sold_out(title)


def _similar_in_stock(
    state: AgentState, issue: IssueRecord, deps: Deps, conn: sqlite3.Connection, taken: list[Candidate]
) -> list[Candidate]:
    """Productos parecidos al que falta que sí se pueden comprar en la misma cantidad
    sin salirse del presupuesto; ``taken`` son los ya propuestos por otro rechazo."""
    product_id, wanted = str(issue["product_id"]), issue["details"]["requested"]
    line = next((item for item in state.cart if item["product_id"] == product_id), None)
    others_cents = cart_total(state.cart) - (line["subtotal_cents"] if line else 0)
    excluded = {item["product_id"] for item in state.cart} | {option["product_id"] for option in taken}
    budget, found = state.budget_cents, []
    for other_id in deps.search.rank(deps.search.title(product_id), top=SEARCH_DEPTH):
        if len(taken) + len(found) >= ALTERNATIVES:
            break
        option = None if other_id in excluded else deps.candidate(conn, other_id)
        if option is None or option["stock"] < wanted:
            continue
        if budget is None or others_cents + option["price_cents"] * wanted <= budget:
            found.append(option)
    return found
