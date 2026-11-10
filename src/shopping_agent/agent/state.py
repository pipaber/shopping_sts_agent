"""Estado tipado de la conversación.

Lo que persiste entre turnos (y queda en los checkpoints) es la memoria de la
compra: presupuesto, preferencias, carrito, candidatos con su evidencia,
aclaración pendiente, cotización, pedido e historial. El resto es trabajo del
turno en curso y se reinicia al empezar el siguiente.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class Message(TypedDict):
    role: str  # "user" o "assistant"
    content: str


class Candidate(TypedDict):
    """Producto recuperado. Los campos de texto son la evidencia del catálogo;
    ``None`` significa que el catálogo no trae ese dato (desconocido)."""

    product_id: str
    title: str
    brand: str | None
    color: str | None
    bullets: str | None
    description: str | None
    price_cents: int
    stock: int


class CartLine(TypedDict):
    product_id: str
    title: str
    quantity: int
    unit_price_cents: int
    subtotal_cents: int
    stock: int


class Quote(TypedDict):
    quote_id: str
    items: list[CartLine]  # ``stock`` es la instantánea vista al cotizar
    total_cents: int
    budget_cents: int | None
    message: str  # lo que se le repite al usuario antes de confirmar


class Order(TypedDict):
    order_id: int
    quote_id: str
    items: list[dict[str, Any]]
    total_cents: int
    message: str


class Step(TypedDict, total=False):
    """Una decisión del LLM en el turno y lo que el código hizo con ella."""

    turn: int
    tool: str
    args: dict[str, Any]
    reason: str
    ok: bool
    summary: str  # texto que vuelve al LLM como observación
    result: Any
    issues: list[dict[str, Any]]


class AgentState(TypedDict, total=False):
    # --- Memoria de la conversación ---
    messages: Annotated[list[Message], operator.add]
    budget_cents: int | None
    preferences: list[str]
    cart: list[CartLine]
    candidates: list[Candidate]
    last_query: str | None
    pending_clarification: str | None
    quote: Quote | None
    order: Order | None
    ops_log: Annotated[list[Step], operator.add]  # todo lo ejecutado o rechazado
    turn: int

    # --- Trabajo del turno en curso ---
    user_input: str
    turn_context: str  # estado al empezar el turno, tal como lo ve el LLM
    decision: dict[str, Any] | None
    steps: list[Step]
    cart_changed: bool
    budget_changed: bool
    confirm_issues: list[dict[str, Any]]
    response: str
    route: str
