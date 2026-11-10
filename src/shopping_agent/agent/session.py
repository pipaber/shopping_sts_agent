"""Conversación por turnos sobre el grafo: un mensaje entra, una respuesta sale.

Oculta la mecánica de ``interrupt``: si el grafo está esperando la confirmación
del pedido, el siguiente mensaje del usuario lo reanuda; si no, abre un turno.
La voz (ASR antes, TTS después) se monta encima de :meth:`ShoppingSession.send`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from langgraph.types import Command

from shopping_agent.agent.state import Step

RECURSION_LIMIT = 80  # cada decisión del LLM son hasta tres nodos

# Etapa a la que se imputa el tiempo de cada nodo del grafo. Lo que no aparece
# aquí (validar, ejecutar, cotizar, confirmar, registrar…) cuenta como herramientas.
RETRIEVAL, LLM, TOOLS = "recuperacion", "llm", "herramientas"
NODE_STAGE = {"interpretar": LLM, "recuperar": RETRIEVAL, "proponer_alternativa": RETRIEVAL}


@dataclass
class TurnResult:
    user: str
    response: str
    awaiting_confirmation: bool  # el agente repitió el pedido y espera un sí
    seconds: float
    operations: list[Step] = field(default_factory=list)  # ejecutadas o rechazadas en el turno
    # Segundos por etapa (recuperación, LLM, herramientas); suman ``seconds``.
    stages: dict[str, float] = field(default_factory=dict)


class ShoppingSession:
    def __init__(self, graph: Any, thread_id: str, user_id: str = "anonimo") -> None:
        self.graph = graph
        self.thread_id = thread_id
        self.config = {
            "configurable": {"thread_id": thread_id, "user_id": user_id},
            "recursion_limit": RECURSION_LIMIT,
        }

    @property
    def state(self) -> dict[str, Any]:
        """Valores guardados del estado. Solo trae los campos ya escritos por algún nodo."""
        return self.graph.get_state(self.config).values

    @property
    def awaiting_confirmation(self) -> bool:
        return bool(self.graph.get_state(self.config).interrupts)

    def send(self, text: str) -> TurnResult:
        before = self.graph.get_state(self.config)
        done = len(before.values.get("ops_log") or [])
        payload = Command(resume=text) if before.interrupts else {"user_input": text}

        # El grafo avisa al terminar cada nodo: el tiempo entre avisos es el del nodo
        # (con su checkpoint) y se suma a la etapa que le corresponde.
        stages = {RETRIEVAL: 0.0, LLM: 0.0, TOOLS: 0.0}
        start = last = time.perf_counter()
        for update in self.graph.stream(payload, self.config, stream_mode="updates"):
            now = time.perf_counter()
            node = next(iter(update), "")
            stages[NODE_STAGE.get(node, TOOLS)] += now - last
            last = now
        seconds = time.perf_counter() - start
        stages[TOOLS] += seconds - sum(stages.values())

        after = self.graph.get_state(self.config)
        waiting = bool(after.interrupts)
        response = after.interrupts[0].value["mensaje"] if waiting else after.values.get("response", "")
        operations = (after.values.get("ops_log") or [])[done:]
        return TurnResult(text, response, waiting, seconds, operations, stages)
