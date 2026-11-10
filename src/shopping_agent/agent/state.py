"""Estado tipado de la conversación.

Lo que persiste entre turnos (y queda en los checkpoints) es la memoria de la
compra: presupuesto, preferencias, carrito, candidatos con su evidencia,
aclaración pendiente, cotización, pedido e historial. El resto es trabajo del
turno en curso y se reinicia al empezar el siguiente (:func:`new_turn`).

Todos los campos tienen un valor por defecto, así que un nodo puede leer
cualquiera sin comprobar antes si existe.
"""

from __future__ import annotations

import operator
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Annotated, Any, TypedDict

from shopping_agent.agent.search import Evidence
from shopping_agent.store.ops import Issue

# Campos del estado que un nodo cambia. Es un diccionario parcial: tiparlo campo a
# campo obligaría a repetir aquí toda la definición de ``AgentState``.
Update = dict[str, Any]

# Decisión del LLM tal como la emite: ``motivo``, ``herramienta`` y sus argumentos.
# Un diccionario vacío significa que en este turno todavía no hay ninguna.
Decision = dict[str, Any]


class Message(TypedDict):
    role: str  # "user" o "assistant"
    content: str


class Candidate(Evidence):
    """Producto recuperado: la evidencia del catálogo más su precio y existencias."""

    price_cents: int
    stock: int


class PricedLine(TypedDict):
    product_id: str
    title: str
    quantity: int
    unit_price_cents: int
    subtotal_cents: int


class CartLine(PricedLine):
    stock: int  # en una cotización, la instantánea vista al cotizar


class Quote(TypedDict):
    quote_id: str
    items: list[CartLine]
    total_cents: int
    budget_cents: int | None
    message: str  # lo que se le repite al usuario antes de confirmar


class Order(TypedDict):
    order_id: int
    quote_id: str
    items: list[PricedLine]
    total_cents: int
    message: str


class IssueRecord(TypedDict):
    """Un rechazo de la tienda o del agente, en la forma que se guarda en el estado."""

    code: str
    message: str
    product_id: str | None
    details: dict[str, Any]


class Step(TypedDict):
    """Una decisión del LLM en el turno y lo que el código hizo con ella."""

    turn: int
    tool: str
    args: dict[str, Any]
    reason: str
    ok: bool
    summary: str  # texto que vuelve al LLM como observación
    result: Any
    issues: list[IssueRecord]


@dataclass
class AgentState:
    # --- Memoria de la conversación ---
    messages: Annotated[list[Message], operator.add] = field(default_factory=list)
    budget_cents: int | None = None
    preferences: list[str] = field(default_factory=list)
    cart: list[CartLine] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    last_query: str | None = None
    pending_clarification: str | None = None
    quote: Quote | None = None
    order: Order | None = None
    ops_log: Annotated[list[Step], operator.add] = field(default_factory=list)  # todo lo ejecutado o rechazado
    turn: int = 0

    # --- Trabajo del turno en curso ---
    user_input: str = ""
    turn_context: str = ""  # estado al empezar el turno, tal como lo ve el LLM
    decision: Decision = field(default_factory=dict)
    steps: list[Step] = field(default_factory=list)
    cart_changed: bool = False
    budget_changed: bool = False
    confirm_issues: list[IssueRecord] = field(default_factory=list)
    response: str = ""
    route: str = ""


def new_turn(state: AgentState, text: str) -> Update:
    """Lo que cambia al empezar un turno: el mensaje del usuario entra en el
    historial y el trabajo del turno anterior se borra."""
    return {
        "messages": [Message(role="user", content=text)],
        "turn": state.turn + 1,
        "steps": [],
        "decision": {},
        "cart_changed": False,
        "budget_changed": False,
        "confirm_issues": [],
        "response": "",
    }


def cart_total(lines: Sequence[PricedLine]) -> int:
    return sum(line["subtotal_cents"] for line in lines)


def issue_record(issue: Issue) -> IssueRecord:
    return IssueRecord(code=issue.code, message=issue.message, product_id=issue.product_id, details=dict(issue.details))


def decision_args(decision: Decision) -> dict[str, Any]:
    """Los argumentos de la herramienta: todo menos ``motivo`` y ``herramienta``."""
    return {key: value for key, value in decision.items() if key not in ("motivo", "herramienta")}
