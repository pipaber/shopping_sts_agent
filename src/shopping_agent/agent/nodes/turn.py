"""Nodos de la conversación: abrir el turno, preguntar al LLM qué hacer, comprobar
lo que quiere decir y cerrar el turno."""

from __future__ import annotations

from dataclasses import replace
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from shopping_agent.agent import guards, prompt, references, texts, tools
from shopping_agent.agent.deps import Deps, cart_id, user_id
from shopping_agent.agent.llm import DecisionLLM, LLMError
from shopping_agent.agent.nodes.steps import rejected, step
from shopping_agent.agent.state import AgentState, Candidate, Decision, Message, Step, Update, decision_args, new_turn
from shopping_agent.store import ops
from shopping_agent.store.ops import Issue

MAX_STEPS = 6  # decisiones del LLM por turno
PROPOSED = 2  # alternativas que añade el código cuando un producto está agotado
# Rechazos pensados para el LLM: no se le dicen al usuario en la respuesta de respaldo.
NOT_FOR_USER = guards.INTERNAL_CODES | references.CODES | {tools.REPEATED_SEARCH}


def iniciar_turno(
    state: AgentState, config: RunnableConfig, *, deps: Deps
) -> Command[Literal["interpretar", "registrar_pedido", "responder"]]:
    """Anota el mensaje, sincroniza el estado con la tienda y reinicia el trabajo del turno."""
    text = state.user_input.strip()
    synced = _synced_with_shop(state, config, deps)
    update: Update = {**new_turn(state, text), **synced}
    if not text:
        return Command(update={**update, "response": texts.EMPTY_INPUT}, goto="responder")
    # El LLM ve el estado tal como está al empezar el turno; lo que cambie después
    # le llega en el resultado de cada herramienta.
    update["turn_context"] = prompt.turn_context(replace(state, **synced), text)
    return Command(update=update, goto="registrar_pedido" if _repeats_confirmation(state, text) else "interpretar")


def _synced_with_shop(state: AgentState, config: RunnableConfig, deps: Deps) -> Update:
    """Carrito y candidatos con los precios y existencias de ahora; en el primer turno
    del hilo, también las preferencias guardadas del usuario."""
    with deps.shop() as conn:
        cart = deps.cart(conn, cart_id(config))
        refreshed = [deps.candidate(conn, candidate["product_id"]) for candidate in state.candidates]
    preferences = state.preferences
    if not state.messages:
        preferences = deps.saved_preferences(user_id(config)) or preferences
    candidates = [candidate for candidate in refreshed if candidate is not None]
    return {"cart": cart, "candidates": candidates, "preferences": preferences}


def _repeats_confirmation(state: AgentState, text: str) -> bool:
    """¿Es otro "sí" justo después de registrar el pedido? No pasa por el LLM: se
    vuelve a confirmar la misma cotización, que es idempotente."""
    order, history = state.order, state.messages
    if order is None or not history or history[-1]["content"] != order["message"]:
        return False
    return guards.classify_confirmation(text) == "si"


def interpretar(
    state: AgentState, *, deps: Deps
) -> Command[Literal["recuperar", "validar", "cotizar", "pedir_aclaracion", "validar_respuesta", "responder"]]:
    """El LLM propone el siguiente paso; cada herramienta sabe qué nodo la atiende."""
    decision = _next_decision(state, deps.llm)
    if decision is None:
        text = _fallback_text(state.steps)
        decision = {"motivo": "respuesta de respaldo del sistema", "herramienta": tools.RESPOND, "texto": text}
        return Command(update={"decision": decision, "response": text}, goto="responder")

    tool = tools.TOOLS.get(str(decision.get("herramienta")))
    if tool is None:  # una herramienta que no existe la rechaza validar
        return Command(update={"decision": decision}, goto="validar")
    if tool.name != tools.RESPOND:
        return Command(update={"decision": decision}, goto=tool.node)
    text = texts.one_line(decision.get("texto"))
    update = {"decision": decision, "response": text or texts.FALLBACK}
    return Command(update=update, goto="validar_respuesta" if text else "responder")


def _next_decision(state: AgentState, llm: DecisionLLM) -> Decision | None:
    """La decisión del LLM, o ``None`` si se agotaron los pasos del turno, el LLM
    falló o repite el paso anterior (que no aportaría nada)."""
    steps = state.steps
    if len(steps) >= MAX_STEPS:
        return None
    schema = tools.decision_schema(tools.known_product_ids(state))
    try:
        decision = llm.decide(prompt.build_messages(state, tools.SYSTEM_PROMPT), schema)
    except LLMError:
        return None
    if steps and decision.get("herramienta") == steps[-1]["tool"] and decision_args(decision) == steps[-1]["args"]:
        return None
    return decision


def _fallback_text(steps: list[Step]) -> str:
    """Respuesta de respaldo: el último rechazo de la tienda, que sí es para el usuario."""
    for previous in reversed(steps):
        reasons = [issue["message"] for issue in previous["issues"] if issue["code"] not in NOT_FOR_USER]
        if reasons:
            return texts.could_not_complete(reasons)
    return texts.FALLBACK


def validar_respuesta(state: AgentState) -> Command[Literal["responder", "interpretar"]]:
    """Comprueba la respuesta del LLM contra lo que tuvo delante; si no se sostiene, se la devuelve."""
    recent = state.messages[-prompt.HISTORY_MESSAGES - 1 :]
    evidence = "\n".join(
        [
            state.turn_context,
            *(message["content"] for message in recent),
            *(previous["summary"] for previous in state.steps),
        ]
    )
    issues = guards.check_response(state.response, evidence, has_order=state.order is not None)
    issues = issues or _unquoted_checkout(state)
    if issues:
        return Command(update=rejected(state, issues), goto="interpretar")
    return Command(goto="responder")


def _unquoted_checkout(state: AgentState) -> list[Issue]:
    """El usuario pidió cerrar la compra y el LLM quiere acabar el turno sin cotizar.

    Se le devuelve una vez. No aplica si el carrito está vacío, si ya lo intentó o si
    la tienda rechazó algo en este turno (entonces lo que toca es explicarlo)."""
    attempted = any(step["tool"] == tools.QUOTE for step in state.steps)
    refused = any(not step["ok"] and step["tool"] != tools.RESPOND for step in state.steps)
    reminded = any(issue["code"] == guards.MUST_QUOTE for step in state.steps for issue in step["issues"])
    if attempted or refused or reminded or not state.cart or not guards.wants_checkout(state.user_input):
        return []
    message = (
        "El usuario pide cerrar la compra y el carrito tiene productos: usa cotizar. El sistema repetirá el "
        "pedido y esperará su confirmación."
    )
    return [Issue(guards.MUST_QUOTE, message)]


def pedir_aclaracion(state: AgentState) -> Update:
    """Termina el turno con una pregunta al usuario."""
    question = texts.one_line(state.decision.get("pregunta")) or texts.EMPTY_INPUT
    return {
        "pending_clarification": question,
        "response": question,
        "messages": [Message(role="assistant", content=question)],
        "ops_log": [step(state, True, "pregunta enviada al usuario")],
    }


# Rechazos de la tienda que dicen cuántas unidades caben: dónde viene ese dato y cómo se le dice al LLM.
_LIMITS = {
    ops.INSUFFICIENT_STOCK: ("available", "por falta de existencias"),
    ops.BUDGET_EXCEEDED: ("max_quantity", "porque no cabe en el presupuesto"),
}


def _fitting(step: Step, state: AgentState) -> tuple[str, str, int, str] | None:
    """Si el paso es una cantidad que la tienda rechazó diciendo cuánta cabe: herramienta,
    producto, unidades que caben con esa herramienta y motivo."""
    if step["ok"] or step["tool"] not in (tools.ADD, tools.SET_QUANTITY):
        return None
    product_id = step["args"]["product_id"]
    in_cart = next((line["quantity"] for line in state.cart if line["product_id"] == product_id), 0)
    for issue in step["issues"]:
        key, reason = _LIMITS.get(issue["code"], ("", ""))
        fits = issue["details"].get(key, 0) - (in_cart if step["tool"] == tools.ADD else 0)
        if fits > 0:
            return step["tool"], product_id, fits, reason
    return None


def _in_stock_instead(state: AgentState) -> list[Candidate]:
    """Si la tienda rechazó un producto por agotado y la respuesta del LLM no cita ningún
    otro, los candidatos con existencias que el código propone en su lugar."""
    sold_out = {issue["product_id"] for step in state.steps for issue in step["issues"] if issue["code"] == ops.OUT_OF_STOCK}
    options = [c for c in state.candidates if c["product_id"] not in sold_out and c["stock"] > 0]
    if not sold_out or any(_cites(state.response, option) for option in options):
        return []
    return options[:PROPOSED]


def _cites(text: str, candidate: Candidate) -> bool:
    """¿Nombra el texto ese producto, por su precio o por su marca?"""
    return f"{candidate['price_cents'] / 100:g}" in guards.numbers_in(text) or references.mentions_brand(text, candidate)


def responder(state: AgentState) -> Update:
    """Cierra el turno. Si el carrito cambió, el código añade su contenido exacto; si un
    producto estaba agotado y el LLM no propone otro, añade los que sí tienen existencias.
    Si la tienda rechazó una cantidad y dijo cuánta cabe, lo deja anotado para el turno siguiente."""
    text = state.response or texts.FALLBACK
    if state.cart_changed or (state.budget_changed and state.cart):
        text = f"{text} {texts.cart_summary(state.cart, state.budget_cents)}"
    elif state.budget_changed and state.budget_cents is not None:
        text = f"{text} {texts.budget_noted(state.budget_cents)}"
    elif options := _in_stock_instead(state):
        text = f"{text} {texts.alternatives(options)}"
    update: Update = {"response": text, "messages": [Message(role="assistant", content=text)], "pending_clarification": None}
    fitting = None if state.cart_changed else next(filter(None, (_fitting(step, state) for step in reversed(state.steps))), None)
    if fitting:
        update["pending_offer"] = prompt.quantity_offer(*fitting)
    return update
