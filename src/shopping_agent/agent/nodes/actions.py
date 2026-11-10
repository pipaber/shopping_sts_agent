"""Nodos de las acciones que propone el LLM: buscar en el catálogo y ejecutar una
herramienta, con la validación por código de por medio."""

from __future__ import annotations

from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from shopping_agent.agent import prompt, references, tools
from shopping_agent.agent.deps import Deps, cart_id, user_id
from shopping_agent.agent.nodes.steps import record, rejected, step
from shopping_agent.agent.state import AgentState, Candidate, Update, cart_total, decision_args
from shopping_agent.store.ops import Issue

SEARCH_DEPTH = 50  # resultados de la búsqueda híbrida que se consideran
SHOWN_CANDIDATES = 5
RERANK_WINDOW = 20  # entre los primeros se priorizan los que se pueden comprar
# Una búsqueda que devuelve lo que el LLM ya tiene delante no aporta nada: sin esto, a
# veces contesta a una pregunta sobre un producto repitiendo la búsqueda y la lista.
REPEATED_SEARCH_MESSAGE = (
    "Esa búsqueda devuelve los mismos CANDIDATOS que ya tienes, con sus precios y existencias al día. No la "
    "repitas. Si el usuario pregunta por un dato de un producto, míralo con detalle_producto; si tampoco "
    "aparece ahí, usa responder para decir que el catálogo no lo indica."
)


def recuperar(state: AgentState, *, deps: Deps) -> Update:
    """Búsqueda híbrida en el catálogo; guarda los candidatos con su evidencia."""
    query = state.decision.get("consulta")
    if not isinstance(query, str) or not query.strip():
        return rejected(state, [Issue(tools.INVALID_ARGS, "La consulta de búsqueda está vacía.")])

    with deps.shop() as conn:
        found = [deps.candidate(conn, product_id) for product_id in deps.search.rank(query, top=SEARCH_DEPTH)]
    ranked = [candidate for candidate in found if candidate is not None]
    budget = state.budget_cents
    remaining = None if budget is None else budget - cart_total(state.cart)
    shown = buyable_first(ranked, remaining)[:SHOWN_CANDIDATES]
    if shown and [candidate["product_id"] for candidate in shown] == [candidate["product_id"] for candidate in state.candidates]:
        return rejected(state, [Issue(tools.REPEATED_SEARCH, REPEATED_SEARCH_MESSAGE)])
    entry = step(state, True, prompt.candidates_found(shown), result=[candidate["product_id"] for candidate in shown])
    return record(state, entry, candidates=shown, last_query=query.strip())


def buyable_first(ranked: list[Candidate], remaining_cents: int | None) -> list[Candidate]:
    """Regla de negocio: entre los primeros resultados van antes los que se pueden
    comprar (con existencias y dentro de lo que queda de presupuesto)."""

    def buyable(candidate: Candidate) -> bool:
        return candidate["stock"] > 0 and (remaining_cents is None or candidate["price_cents"] <= remaining_cents)

    window, rest = ranked[:RERANK_WINDOW], ranked[RERANK_WINDOW:]
    return [c for c in window if buyable(c)] + [c for c in window if not buyable(c)] + rest


def validar(state: AgentState) -> Command[Literal["ejecutar_herramienta", "interpretar"]]:
    """Comprueba la llamada antes de tocar la tienda; si no vale, vuelve al LLM con el motivo."""
    decision = state.decision
    issues = tools.validate_call(decision.get("herramienta"), decision_args(decision), state) or _reference_issues(state)
    if issues:
        return Command(update=rejected(state, issues), goto="interpretar")
    return Command(goto="ejecutar_herramienta")


def _reference_issues(state: AgentState) -> list[Issue]:
    """Si el usuario señaló un candidato por su posición, la llamada tiene que respetarlo."""
    decision = state.decision
    tool = decision.get("herramienta")
    if tool not in tools.CANDIDATE_TOOLS:
        return []
    product_ids = decision.get("product_ids") or [decision.get("product_id")]
    return references.check_products(state.user_input, state.candidates, product_ids, adding=tool == tools.ADD)


def ejecutar_herramienta(state: AgentState, config: RunnableConfig, *, deps: Deps) -> Update:
    """Ejecuta una herramienta ya validada. Stock y presupuesto los decide ``store.ops``."""
    run = tools.TOOLS[state.decision["herramienta"]].run
    assert run is not None  # validar solo deja pasar herramientas con función
    with deps.shop() as conn:
        call = tools.ToolCall(decision_args(state.decision), state, deps, conn, cart_id(config), user_id(config))
        outcome = run(call)
    entry = step(state, outcome.ok, outcome.summary, outcome.result, outcome.issues)
    return record(state, entry, **outcome.update)
