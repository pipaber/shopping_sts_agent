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

from shopping_agent.agent.state import AgentState, Step

RECURSION_LIMIT = 80  # cada decisión del LLM son hasta tres nodos


@dataclass
class TurnResult:
    user: str
    response: str
    awaiting_confirmation: bool  # el agente repitió el pedido y espera un sí
    seconds: float
    operations: list[Step] = field(default_factory=list)  # ejecutadas o rechazadas en el turno


class ShoppingSession:
    def __init__(self, graph: Any, thread_id: str, user_id: str = "anonimo") -> None:
        self.graph = graph
        self.thread_id = thread_id
        self.config = {
            "configurable": {"thread_id": thread_id, "user_id": user_id},
            "recursion_limit": RECURSION_LIMIT,
        }

    @property
    def state(self) -> AgentState:
        return self.graph.get_state(self.config).values

    @property
    def awaiting_confirmation(self) -> bool:
        return bool(self.graph.get_state(self.config).interrupts)

    def send(self, text: str) -> TurnResult:
        before = self.graph.get_state(self.config)
        done = len(before.values.get("ops_log") or [])
        payload = Command(resume=text) if before.interrupts else {"user_input": text}

        start = time.perf_counter()
        self.graph.invoke(payload, self.config)
        seconds = time.perf_counter() - start

        after = self.graph.get_state(self.config)
        waiting = bool(after.interrupts)
        response = after.interrupts[0].value["mensaje"] if waiting else after.values.get("response", "")
        operations = (after.values.get("ops_log") or [])[done:]
        return TurnResult(text, response, waiting, seconds, operations)
