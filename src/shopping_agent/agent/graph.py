"""Grafo explícito del agente de compras.

::

    iniciar_turno → interpretar ─┬─ recuperar ──────────────────────→ interpretar
                                 ├─ validar ─ ejecutar_herramienta ─→ interpretar
                                 ├─ pedir_aclaracion → FIN
                                 ├─ validar_respuesta ─┬─ responder → FIN
                                 │                     └─ (rechazada) → interpretar
                                 └─ cotizar → confirmar (interrupt) ─┬─ sí → registrar_pedido ─┬→ responder
                                                                     ├─ no → responder          └→ proponer_alternativa → responder
                                                                     └─ otra cosa → iniciar_turno

El LLM solo interviene en ``interpretar``: propone una herramienta por paso. Todo
lo demás es código: qué productos existen, si la cantidad es válida, si hay
existencias, si cabe en el presupuesto, si las cifras de la respuesta salen de los
datos, qué se le repite al usuario antes de comprar y cuándo se registra el pedido
(solo tras un sí explícito).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from dataclasses import replace
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.base import BaseStore
from langgraph.types import interrupt

from shopping_agent.agent import prompt, texts, tools
from shopping_agent.agent.llm import DecisionLLM, LLMError
from shopping_agent.agent.search import CatalogSearch
from shopping_agent.agent.state import (
    AgentState,
    Candidate,
    CartLine,
    Decision,
    Order,
    PricedLine,
    Quote,
    Step,
    Update,
    cart_total,
    decision_args,
    issue_record,
    new_turn,
)
from shopping_agent.store import ops
from shopping_agent.store.db import connect
from shopping_agent.store.ops import Issue, format_eur

MAX_STEPS = 6  # decisiones del LLM por turno
SHOWN_CANDIDATES = 5
RERANK_WINDOW = 20  # entre los primeros se priorizan los que se pueden comprar
ALTERNATIVES = 3
PROFILE_NAMESPACE = "usuarios"
DETAIL_CHARS = (1600, 800)  # viñetas y descripción de un producto
COMPARE_CHARS = (600, 300)  # por producto al comparar varios

def _by_route(state: AgentState) -> str:
    return state.route


def build_graph(
    llm: DecisionLLM,
    search: CatalogSearch,
    db_path: Path | str,
    checkpointer: BaseCheckpointSaver,
    store: BaseStore | None = None,
):
    """Compila el grafo. ``db_path`` es la tienda SQLite; el carrito es el del hilo."""

    @contextmanager
    def shop() -> Iterator[sqlite3.Connection]:
        conn = connect(db_path)
        try:
            yield conn
        finally:
            conn.close()

    def cart_id(config: RunnableConfig) -> str:
        return str(config.get("configurable", {})["thread_id"])

    def user_id(config: RunnableConfig) -> str:
        return str(config.get("configurable", {}).get("user_id", "anonimo"))

    def priced_line(item: dict[str, Any]) -> PricedLine:
        return PricedLine(
            product_id=item["product_id"],
            title=search.title(item["product_id"]),
            quantity=item["quantity"],
            unit_price_cents=item["unit_price_cents"],
            subtotal_cents=item["subtotal_cents"],
        )

    def cart_line(item: dict[str, Any]) -> CartLine:
        return CartLine(**priced_line(item), stock=item["stock"])

    def read_cart(conn: sqlite3.Connection, config: RunnableConfig) -> list[CartLine]:
        return [cart_line(item) for item in ops.get_cart(conn, cart_id(config)).data["items"]]

    def priced(conn: sqlite3.Connection, product_id: str, *chars: int) -> Candidate:
        """Evidencia del catálogo con el precio y las existencias de ahora."""
        offer = ops.price_and_stock(conn, product_id).data
        return Candidate(**search.evidence(product_id, *chars), price_cents=offer["price_cents"], stock=offer["stock"])

    def candidate(conn: sqlite3.Connection, product_id: str) -> Candidate | None:
        if product_id not in search or not ops.price_and_stock(conn, product_id).ok:
            return None
        return priced(conn, product_id)

    def step(state: AgentState, ok: bool, summary: str, result: Any = None, issues: Iterable[Issue] = ()) -> Step:
        decision = state.decision
        return Step(
            turn=state.turn,
            tool=str(decision.get("herramienta")),
            args=decision_args(decision),
            reason=str(decision.get("motivo", "")),
            ok=ok,
            summary=summary,
            result=result,
            issues=[issue_record(issue) for issue in issues],
        )

    def record(state: AgentState, entry: Step, **update: Any) -> Update:
        """Añade el paso a los del turno y al registro de operaciones."""
        return {"steps": [*state.steps, entry], "ops_log": [entry], **update}

    # --- Nodos ---------------------------------------------------------------------

    def iniciar_turno(state: AgentState, config: RunnableConfig) -> Update:
        """Anota el mensaje, sincroniza el estado con la tienda y reinicia el trabajo del turno."""
        text = state.user_input.strip()
        update = {**new_turn(state, text), "route": "interpretar"}
        with shop() as conn:
            cart = read_cart(conn, config)
            refreshed = [candidate(conn, c["product_id"]) for c in state.candidates]
        candidates = [c for c in refreshed if c is not None]
        preferences = state.preferences
        if not state.messages and store is not None:
            # Primera vez en este hilo: recupera las preferencias guardadas del usuario.
            profile = store.get((PROFILE_NAMESPACE, user_id(config)), "perfil")
            if profile is not None:
                preferences = list(profile.value.get("preferencias", []))
        update.update(cart=cart, candidates=candidates, preferences=preferences)

        if not text:
            update.update(response=texts.EMPTY_INPUT, route="responder")
            return update
        # El LLM ve el estado tal como está al empezar el turno; lo que cambie después
        # le llega en el resultado de cada herramienta.
        context = prompt.render_state(replace(state, cart=cart, candidates=candidates, preferences=preferences))
        hint = prompt.amount_hint(text)
        update["turn_context"] = f"{context}\n{hint}" if hint else context

        # Repetir la confirmación justo después de registrar el pedido no pasa por el
        # LLM: se vuelve a confirmar la misma cotización, que es idempotente.
        order, history = state.order, state.messages
        if (
            order
            and history
            and history[-1]["content"] == order["message"]
            and tools.classify_confirmation(text) == "si"
        ):
            update["route"] = "registrar_pedido"
        return update

    def interpretar(state: AgentState) -> Update:
        """El LLM propone el siguiente paso; el código decide a qué nodo va."""
        steps = state.steps
        decision: Decision | None = None
        if len(steps) < MAX_STEPS:
            schema = tools.decision_schema(tools.known_product_ids(state))
            try:
                decision = llm.decide(prompt.build_messages(state), schema)
            except LLMError:
                decision = None
            if decision is not None and steps:
                last = steps[-1]
                if decision.get("herramienta") == last["tool"] and decision_args(decision) == last["args"]:
                    decision = None  # repetir el mismo paso no aporta nada

        if decision is None:
            # Respuesta de respaldo: el último rechazo de la tienda, que sí es para el usuario.
            text = texts.FALLBACK
            for previous in reversed(steps):
                reasons = [i["message"] for i in previous["issues"] if i["code"] not in tools.INTERNAL_CODES]
                if reasons:
                    text = texts.could_not_complete(reasons)
                    break
            decision = {"motivo": "respuesta de respaldo del sistema", "herramienta": tools.RESPOND, "texto": text}
            return {"decision": decision, "response": text, "route": "responder"}

        tool = decision.get("herramienta")
        update: Update = {"decision": decision}
        if tool == tools.RESPOND:
            text = decision.get("texto")
            # Una sola línea: la respuesta se leerá en voz alta.
            text = " ".join(text.split()) if isinstance(text, str) else ""
            update.update(response=text or texts.FALLBACK, route="validar_respuesta" if text else "responder")
        elif tool == tools.CLARIFY:
            update["route"] = "pedir_aclaracion"
        elif tool == tools.SEARCH:
            update["route"] = "recuperar"
        elif tool == tools.QUOTE:
            update["route"] = "cotizar"
        else:
            update["route"] = "validar"
        return update

    def validar_respuesta(state: AgentState) -> Update:
        """Comprueba la respuesta del LLM contra lo que tuvo delante; si no se sostiene, se la devuelve."""
        history = state.messages
        evidence = "\n".join(
            [
                state.turn_context,
                *(message["content"] for message in history[-prompt.HISTORY_MESSAGES - 1 :]),
                *(previous["summary"] for previous in state.steps),
            ]
        )
        issues = tools.check_response(state.response, evidence, has_order=state.order is not None)
        if issues:
            return record(state, step(state, False, prompt.rejection(issues), issues=issues), route="interpretar")
        return {"route": "responder"}

    def pedir_aclaracion(state: AgentState) -> Update:
        question = state.decision.get("pregunta")
        question = " ".join(question.split()) if isinstance(question, str) else ""
        question = question or texts.EMPTY_INPUT
        entry = step(state, True, "pregunta enviada al usuario")
        return {
            "pending_clarification": question,
            "response": question,
            "messages": [{"role": "assistant", "content": question}],
            "ops_log": [entry],
        }

    def recuperar(state: AgentState) -> Update:
        """Búsqueda híbrida en el catálogo; guarda los candidatos con su evidencia."""
        query = state.decision.get("consulta")
        if not isinstance(query, str) or not query.strip():
            issue = Issue(tools.INVALID_ARGS, "La consulta de búsqueda está vacía.")
            return record(state, step(state, False, prompt.rejection([issue]), issues=[issue]))

        budget = state.budget_cents
        remaining = None if budget is None else budget - cart_total(state.cart)
        with shop() as conn:
            found = [candidate(conn, product_id) for product_id in search.rank(query, top=50)]
        ranked = [c for c in found if c is not None]
        # Regla de negocio: entre los primeros resultados van antes los que se pueden
        # comprar (con existencias y dentro de lo que queda de presupuesto).
        window, rest = ranked[:RERANK_WINDOW], ranked[RERANK_WINDOW:]

        def buyable(c: Candidate) -> bool:
            return c["stock"] > 0 and (remaining is None or c["price_cents"] <= remaining)

        ordered = [c for c in window if buyable(c)] + [c for c in window if not buyable(c)] + rest
        shown = ordered[:SHOWN_CANDIDATES]
        entry = step(state, True, prompt.candidates_found(shown), result=[c["product_id"] for c in shown])
        return record(state, entry, candidates=shown, last_query=query.strip())

    def validar(state: AgentState) -> Update:
        """Comprueba la llamada antes de tocar la tienda; si no vale, vuelve al LLM con el motivo."""
        decision = state.decision
        issues = tools.validate_call(decision.get("herramienta"), decision_args(decision), state)
        if issues:
            return record(state, step(state, False, prompt.rejection(issues), issues=issues), route="interpretar")
        return {"route": "ejecutar_herramienta"}

    def ejecutar_herramienta(state: AgentState, config: RunnableConfig) -> Update:
        """Ejecuta una herramienta ya validada. Stock y presupuesto los decide ``store.ops``."""
        decision = state.decision
        tool, args = decision["herramienta"], decision_args(decision)
        budget = state.budget_cents

        if tool == tools.SET_BUDGET:
            cents = tools.budget_to_cents(args["importe_eur"])
            assert cents is not None  # lo garantiza la validación previa
            total = cart_total(state.cart)
            summary = f"presupuesto fijado en {format_eur(cents)}."
            if total > cents:
                summary += f" Aviso: el carrito suma {format_eur(total)} y lo supera en {format_eur(total - cents)}."
            entry = step(state, True, summary, result={"budget_cents": cents})
            return record(state, entry, budget_cents=cents, quote=None, budget_changed=True)

        if tool == tools.SAVE_PREFERENCE:
            preference = args["preferencia"].strip()
            preferences = list(dict.fromkeys([*state.preferences, preference]))
            if store is not None:
                store.put((PROFILE_NAMESPACE, user_id(config)), "perfil", {"preferencias": preferences})
            return record(state, step(state, True, "preferencia guardada.", result=preferences), preferences=preferences)

        with shop() as conn:
            if tool in (tools.DETAIL, tools.COMPARE):
                ids = [args["product_id"]] if tool == tools.DETAIL else list(dict.fromkeys(args["product_ids"]))
                chars = DETAIL_CHARS if tool == tools.DETAIL else COMPARE_CHARS
                rows = [priced(conn, product_id, *chars) for product_id in ids]
                summary = "\n" + "\n".join(prompt.candidate_line(i, row) for i, row in enumerate(rows, 1))
                return record(state, step(state, True, summary, result=[row["product_id"] for row in rows]))

            if tool == tools.PRICE_STOCK:
                offer = ops.price_and_stock(conn, args["product_id"])
                if not offer.ok:
                    return record(state, step(state, False, prompt.rejection(offer.issues), issues=offer.issues))
                stock = offer.data["stock"]
                summary = (
                    f"precio {format_eur(offer.data['price_cents'])}; "
                    + (f"quedan {stock} unidades." if stock else "agotado.")
                    + " Esta herramienta no da características: para color, batería, medidas u otros datos"
                    " del producto usa detalle_producto."
                )
                return record(state, step(state, True, summary, result=offer.data))

            if tool == tools.ADD:
                result = ops.add_to_cart(conn, cart_id(config), args["product_id"], args["cantidad"], budget)
            elif tool == tools.SET_QUANTITY:
                result = ops.set_quantity(conn, cart_id(config), args["product_id"], args["cantidad"], budget)
            else:
                result = ops.remove_from_cart(conn, cart_id(config), args["product_id"])
            cart = read_cart(conn, config)

        if not result.ok:
            return record(state, step(state, False, prompt.rejection(result.issues), issues=result.issues), cart=cart)
        summary = f"hecho. Así queda el carrito.\n{prompt.render_cart(cart)}"
        entry = step(state, True, summary, result={"total_cents": cart_total(cart)})
        # Cualquier cambio en el carrito invalida la cotización anterior.
        return record(state, entry, cart=cart, quote=None, cart_changed=True)

    def cotizar(state: AgentState, config: RunnableConfig) -> Update:
        """Congela el carrito en una cotización y redacta lo que se repite al usuario."""
        with shop() as conn:
            result = ops.create_quote(conn, cart_id(config), state.budget_cents)
            cart = read_cart(conn, config)
        if not result.ok:
            entry = step(state, False, prompt.rejection(result.issues), issues=result.issues)
            return record(state, entry, cart=cart, route="interpretar")
        data = result.data
        items = [cart_line(item) for item in data["items"]]
        message = texts.quote_message(items, data["total_cents"], data["budget_cents"])
        quote = Quote(
            quote_id=data["quote_id"],
            items=items,
            total_cents=data["total_cents"],
            budget_cents=data["budget_cents"],
            message=message,
        )
        entry = step(state, True, "cotización creada; falta la confirmación del usuario.", result=quote["quote_id"])
        return record(
            state,
            entry,
            cart=cart,
            quote=quote,
            response=message,
            messages=[{"role": "assistant", "content": message}],
            pending_clarification=None,
            route="confirmar",
        )

    def confirmar(state: AgentState) -> Update:
        """Pausa hasta que el usuario conteste a la cotización. Sin efectos antes del ``interrupt``."""
        quote = state.quote
        assert quote is not None  # a este nodo solo se llega desde cotizar
        answer = interrupt(
            {
                "tipo": "confirmacion_pedido",
                "mensaje": quote["message"],
                "quote_id": quote["quote_id"],
                "total_cents": quote["total_cents"],
            }
        )
        text = str(answer or "").strip()
        verdict = tools.classify_confirmation(text)
        if verdict == "otro":
            # No es un sí ni un no: no se compra nada y el mensaje se atiende como turno nuevo.
            return {"user_input": text, "route": "iniciar_turno"}
        update = new_turn(state, text)
        if verdict == "si":
            return {**update, "route": "registrar_pedido"}
        return {**update, "quote": None, "response": texts.CANCELLED, "route": "responder"}

    def registrar_pedido(state: AgentState, config: RunnableConfig) -> Update:
        """Confirma la cotización en una transacción que vuelve a comprobarlo todo."""
        pending = state.quote or state.order  # la cotización a confirmar o, si se repite el sí, la ya confirmada
        assert pending is not None
        quote_id = pending["quote_id"]
        with shop() as conn:
            result = ops.confirm_quote(conn, quote_id)
            cart = read_cart(conn, config)
        entry = Step(
            turn=state.turn,
            tool="confirmar_pedido",
            args={"quote_id": quote_id},
            reason="el usuario confirmó la cotización",
            ok=result.ok,
            summary="pedido registrado" if result.ok else prompt.rejection(result.issues),
            result=result.data or None,
            issues=[issue_record(issue) for issue in result.issues],
        )
        if not result.ok:
            return {
                "ops_log": [entry],
                "cart": cart,
                "quote": None,
                "confirm_issues": entry["issues"],
                "route": "proponer_alternativa",
            }
        data = result.data
        items = [priced_line(item) for item in data["items"]]
        if data["already_confirmed"]:
            entry["summary"] = "el pedido ya estaba registrado; no se duplicó"
            message = texts.order_already_registered(data["order_id"], data["total_cents"])
        else:
            message = texts.order_message(data["order_id"], items, data["total_cents"])
        order = Order(
            order_id=data["order_id"],
            quote_id=data["quote_id"],
            items=items,
            total_cents=data["total_cents"],
            message=message,
        )
        return {"ops_log": [entry], "cart": cart, "quote": None, "order": order, "response": message, "route": "responder"}

    def proponer_alternativa(state: AgentState, config: RunnableConfig) -> Update:
        """La confirmación falló: explica qué cambió y propone una salida, sin LLM."""
        issues = state.confirm_issues
        cart = state.cart
        budget = state.budget_cents
        total = cart_total(cart)
        parts = [texts.NOT_REGISTERED]
        alternatives: list[Candidate] = []

        with shop() as conn:
            for issue in issues:
                code, product_id = issue["code"], issue["product_id"]
                if product_id is None or code not in (ops.OUT_OF_STOCK, ops.INSUFFICIENT_STOCK):
                    parts.append(issue["message"])
                    continue
                line = next((item for item in cart if item["product_id"] == product_id), None)
                title = search.title(product_id)
                wanted, available = issue["details"]["requested"], issue["details"]["available"]
                parts.append(texts.less_stock(title, available, wanted) if available else texts.sold_out(title))
                # Productos parecidos que sí se pueden comprar en la misma cantidad.
                others = total - (line["subtotal_cents"] if line else 0)
                in_cart = {item["product_id"] for item in cart}
                for other_id in search.rank(search.title(product_id), top=50):
                    if len(alternatives) >= ALTERNATIVES:
                        break
                    option = candidate(conn, other_id)
                    if option is None or other_id in in_cart or other_id in {a["product_id"] for a in alternatives}:
                        continue
                    affordable = budget is None or others + option["price_cents"] * wanted <= budget
                    if option["stock"] >= wanted and affordable:
                        alternatives.append(option)

        if alternatives:
            parts.append(texts.alternatives(alternatives))
        if any(issue["code"] in (ops.PRICE_CHANGED, ops.STALE_QUOTE, ops.BUDGET_EXCEEDED) for issue in issues):
            parts.append(texts.NEW_QUOTE_OFFER)
        parts.append(texts.WHAT_NEXT)
        update: Update = {"response": " ".join(parts), "route": "responder"}
        if alternatives:
            update.update(candidates=alternatives, last_query=None)
        return update

    def responder(state: AgentState) -> Update:
        """Cierra el turno. Si el carrito cambió, el código añade su contenido exacto."""
        text = state.response or texts.FALLBACK
        if state.cart_changed or (state.budget_changed and state.cart):
            text = f"{text} {texts.cart_summary(state.cart, state.budget_cents)}"
        elif state.budget_changed and state.budget_cents is not None:
            text = f"{text} {texts.budget_noted(state.budget_cents)}"
        return {
            "response": text,
            "messages": [{"role": "assistant", "content": text}],
            "pending_clarification": None,
        }

    # --- Grafo -----------------------------------------------------------------------

    nodes: dict[str, Callable[..., Update]] = {
        "iniciar_turno": iniciar_turno,
        "interpretar": interpretar,
        "validar_respuesta": validar_respuesta,
        "pedir_aclaracion": pedir_aclaracion,
        "recuperar": recuperar,
        "validar": validar,
        "ejecutar_herramienta": ejecutar_herramienta,
        "cotizar": cotizar,
        "confirmar": confirmar,
        "registrar_pedido": registrar_pedido,
        "proponer_alternativa": proponer_alternativa,
        "responder": responder,
    }
    builder = StateGraph(AgentState)
    for name, node in nodes.items():
        builder.add_node(name, node)

    def routes(*names: str) -> list[str]:
        return list(names)

    builder.add_edge(START, "iniciar_turno")
    builder.add_conditional_edges("iniciar_turno", _by_route, routes("interpretar", "registrar_pedido", "responder"))
    builder.add_conditional_edges(
        "interpretar",
        _by_route,
        routes("pedir_aclaracion", "recuperar", "validar", "cotizar", "validar_respuesta", "responder"),
    )
    builder.add_conditional_edges("validar_respuesta", _by_route, routes("responder", "interpretar"))
    builder.add_edge("recuperar", "interpretar")
    builder.add_conditional_edges("validar", _by_route, routes("ejecutar_herramienta", "interpretar"))
    builder.add_edge("ejecutar_herramienta", "interpretar")
    builder.add_conditional_edges("cotizar", _by_route, routes("confirmar", "interpretar"))
    builder.add_conditional_edges("confirmar", _by_route, routes("registrar_pedido", "responder", "iniciar_turno"))
    builder.add_conditional_edges("registrar_pedido", _by_route, routes("responder", "proponer_alternativa"))
    builder.add_edge("proponer_alternativa", "responder")
    builder.add_edge("pedir_aclaracion", END)
    builder.add_edge("responder", END)
    return builder.compile(checkpointer=checkpointer, store=store)
