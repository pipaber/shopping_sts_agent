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

Aquí solo se cablea el grafo; los nodos están en ``nodes/``.
"""

from __future__ import annotations

from functools import partial
from pathlib import Path

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.base import BaseStore

from shopping_agent.agent.deps import Deps
from shopping_agent.agent.llm import DecisionLLM
from shopping_agent.agent.nodes import actions, checkout, turn
from shopping_agent.agent.search import CatalogSearch
from shopping_agent.agent.state import AgentState

# Nodos que eligen el siguiente (devuelven ``Command(goto=...)``) y a dónde pueden ir.
BRANCHES: dict[str, tuple[str, ...]] = {
    "iniciar_turno": ("interpretar", "registrar_pedido", "responder"),
    "interpretar": ("recuperar", "validar", "cotizar", "pedir_aclaracion", "validar_respuesta", "responder"),
    "validar_respuesta": ("responder", "interpretar"),
    "validar": ("ejecutar_herramienta", "interpretar"),
    "cotizar": ("confirmar", "interpretar"),
    "confirmar": ("registrar_pedido", "responder", "iniciar_turno"),
    "registrar_pedido": ("responder", "proponer_alternativa"),
}
# Nodos con un único destino.
EDGES: dict[str, str] = {
    START: "iniciar_turno",
    "recuperar": "interpretar",
    "ejecutar_herramienta": "interpretar",
    "proponer_alternativa": "responder",
    "pedir_aclaracion": END,
    "responder": END,
}


def build_graph(
    llm: DecisionLLM,
    search: CatalogSearch,
    db_path: Path | str,
    checkpointer: BaseCheckpointSaver,
    store: BaseStore | None = None,
):
    """Compila el grafo. ``db_path`` es la tienda SQLite; el carrito es el del hilo."""
    deps = Deps(llm, search, db_path, store)
    nodes = {
        "iniciar_turno": partial(turn.iniciar_turno, deps=deps),
        "interpretar": partial(turn.interpretar, deps=deps),
        "validar_respuesta": turn.validar_respuesta,
        "pedir_aclaracion": turn.pedir_aclaracion,
        "responder": turn.responder,
        "recuperar": partial(actions.recuperar, deps=deps),
        "validar": actions.validar,
        "ejecutar_herramienta": partial(actions.ejecutar_herramienta, deps=deps),
        "cotizar": partial(checkout.cotizar, deps=deps),
        "confirmar": checkout.confirmar,
        "registrar_pedido": partial(checkout.registrar_pedido, deps=deps),
        "proponer_alternativa": partial(checkout.proponer_alternativa, deps=deps),
    }
    builder = StateGraph(AgentState)
    for name, node in nodes.items():
        builder.add_node(name, node, destinations=BRANCHES.get(name))
    for source, target in EDGES.items():
        builder.add_edge(source, target)
    return builder.compile(checkpointer=checkpointer, store=store)
