"""Nodos de las acciones que propone el LLM: buscar en el catálogo y ejecutar una
herramienta, con la validación por código de por medio."""

from __future__ import annotations

from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from shopping_agent.agent import prompt, tools
from shopping_agent.agent.deps import Deps, cart_id, user_id
from shopping_agent.agent.nodes.steps import record, rejected, step
from shopping_agent.agent.state import AgentState, Candidate, Update, cart_total, decision_args
from shopping_agent.store.ops import Issue

SEARCH_DEPTH = 50  # resultados de la búsqueda híbrida que se consideran
SHOWN_CANDIDATES = 5
RERANK_WINDOW = 20  # entre los primeros se priorizan los que se pueden comprar


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
    issues = tools.validate_call(decision.get("herramienta"), decision_args(decision), state)
    if issues:
        return Command(update=rejected(state, issues), goto="interpretar")
    return Command(goto="ejecutar_herramienta")


def ejecutar_herramienta(state: AgentState, config: RunnableConfig, *, deps: Deps) -> Update:
    """Ejecuta una herramienta ya validada. Stock y presupuesto los decide ``store.ops``."""
    run = tools.TOOLS[state.decision["herramienta"]].run
    assert run is not None  # validar solo deja pasar herramientas con función
    with deps.shop() as conn:
        call = tools.ToolCall(decision_args(state.decision), state, deps, conn, cart_id(config), user_id(config))
        outcome = run(call)
    entry = step(state, outcome.ok, outcome.summary, outcome.result, outcome.issues)
    return record(state, entry, **outcome.update)
