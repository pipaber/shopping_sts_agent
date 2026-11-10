"""Nodos de la conversación: abrir el turno, preguntar al LLM qué hacer, comprobar
lo que quiere decir y cerrar el turno."""

from __future__ import annotations

from dataclasses import replace
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from shopping_agent.agent import guards, prompt, texts, tools
from shopping_agent.agent.deps import Deps, cart_id, user_id
from shopping_agent.agent.llm import DecisionLLM, LLMError
from shopping_agent.agent.nodes.steps import rejected, step
from shopping_agent.agent.state import AgentState, Decision, Message, Step, Update, decision_args, new_turn

MAX_STEPS = 6  # decisiones del LLM por turno


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
        reasons = [issue["message"] for issue in previous["issues"] if issue["code"] not in guards.INTERNAL_CODES]
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
    if issues:
        return Command(update=rejected(state, issues), goto="interpretar")
    return Command(goto="responder")


def pedir_aclaracion(state: AgentState) -> Update:
    """Termina el turno con una pregunta al usuario."""
    question = texts.one_line(state.decision.get("pregunta")) or texts.EMPTY_INPUT
    return {
        "pending_clarification": question,
        "response": question,
        "messages": [Message(role="assistant", content=question)],
        "ops_log": [step(state, True, "pregunta enviada al usuario")],
    }


def responder(state: AgentState) -> Update:
    """Cierra el turno. Si el carrito cambió, el código añade su contenido exacto."""
    text = state.response or texts.FALLBACK
    if state.cart_changed or (state.budget_changed and state.cart):
        text = f"{text} {texts.cart_summary(state.cart, state.budget_cents)}"
    elif state.budget_changed and state.budget_cents is not None:
        text = f"{text} {texts.budget_noted(state.budget_cents)}"
    return {
        "response": text,
        "messages": [Message(role="assistant", content=text)],
        "pending_clarification": None,
    }
