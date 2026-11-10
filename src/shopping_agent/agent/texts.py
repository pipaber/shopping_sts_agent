"""Lo que el agente le dice al usuario cuando el texto lo escribe el código.

Los importes, cantidades y productos que se repiten antes de comprar salen de
aquí, no del LLM. Todo está redactado para leerse en voz alta: frases seguidas,
sin listas. Lo que ve el LLM (reglas, contexto, resultados) está en ``prompt.py``.
"""

from __future__ import annotations

from collections.abc import Sequence

from shopping_agent.agent.state import Candidate, PricedLine, cart_total
from shopping_agent.store.ops import format_eur

FALLBACK = "Perdona, no he podido completar tu petición. ¿Puedes decírmelo de otra forma?"
EMPTY_INPUT = "No te he entendido. ¿Puedes repetirlo?"
CANCELLED = "De acuerdo, no registro el pedido. Tu carrito sigue como estaba; dime si quieres cambiar algo."
NOT_REGISTERED = "No he registrado el pedido porque la tienda cambió después de la cotización."
NEW_QUOTE_OFFER = "Puedo preparar una cotización nueva con los datos actuales."
WHAT_NEXT = "¿Qué prefieres?"


def short_title(title: str, limit: int = 70) -> str:
    """Título recortado para decirlo en voz alta."""
    if len(title) <= limit:
        return title
    return title[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:-") + "…"


def one_line(text: object) -> str:
    """Texto en una sola línea, como se leerá en voz alta; vacío si no es texto."""
    return " ".join(text.split()) if isinstance(text, str) else ""


def units(quantity: int) -> str:
    return "1 unidad" if quantity == 1 else f"{quantity} unidades"


def cart_lines_text(lines: Sequence[PricedLine]) -> str:
    return "; ".join(
        f"{units(line['quantity'])} de «{short_title(line['title'])}» a {format_eur(line['unit_price_cents'])}"
        f" cada una, {format_eur(line['subtotal_cents'])}"
        for line in lines
    )


def budget_text(total_cents: int, budget_cents: int | None) -> str:
    if budget_cents is None:
        return ""
    if total_cents > budget_cents:
        return f" Tu presupuesto es de {format_eur(budget_cents)} y lo superas en {format_eur(total_cents - budget_cents)}."
    return f" Tu presupuesto es de {format_eur(budget_cents)} y te quedan {format_eur(budget_cents - total_cents)}."


def could_not_complete(reasons: Sequence[str]) -> str:
    """Respuesta de respaldo con los motivos por los que la tienda rechazó la operación."""
    return "No he podido completar la operación. " + " ".join(reasons)


# --- Carrito y presupuesto -------------------------------------------------------------


def cart_summary(lines: Sequence[PricedLine], budget_cents: int | None) -> str:
    """Resumen del carrito que el código añade a la respuesta cuando cambia."""
    if not lines:
        return "El carrito está vacío."
    total = cart_total(lines)
    return f"En el carrito hay {cart_lines_text(lines)}. Total: {format_eur(total)}.{budget_text(total, budget_cents)}"


def budget_noted(budget_cents: int) -> str:
    return f"He anotado un presupuesto de {format_eur(budget_cents)}."


# --- Cotización y pedido ---------------------------------------------------------------


def quote_message(lines: Sequence[PricedLine], total_cents: int, budget_cents: int | None) -> str:
    """Lo que se repite al usuario antes de registrar nada."""
    return (
        f"Te repito el pedido antes de registrarlo: {cart_lines_text(lines)}. "
        f"Total: {format_eur(total_cents)}.{budget_text(total_cents, budget_cents)} "
        "¿Lo confirmo? Di sí para registrarlo, o dime qué quieres cambiar."
    )


def order_message(order_id: int, items: Sequence[PricedLine], total_cents: int) -> str:
    return (
        f"Pedido número {order_id} registrado: {cart_lines_text(items)}. "
        f"Total: {format_eur(total_cents)}. Gracias por tu compra."
    )


def order_already_registered(order_id: int, total_cents: int) -> str:
    return (
        f"Ese pedido ya estaba registrado con el número {order_id}, así que no lo he "
        f"duplicado. Total: {format_eur(total_cents)}."
    )


# --- La tienda cambió entre la cotización y la confirmación ----------------------------


def less_stock(title: str, available: int, wanted: int) -> str:
    return (
        f"De «{short_title(title)}» solo {'queda' if available == 1 else 'quedan'} "
        f"{units(available)} y habías pedido {wanted}. "
        f"Puedo dejarlo en {available}."
    )


def sold_out(title: str) -> str:
    return f"«{short_title(title)}» se ha agotado."


def alternatives(options: Sequence[Candidate]) -> str:
    listed = "; ".join(
        f"«{short_title(option['title'])}» a {format_eur(option['price_cents'])}, con {option['stock']} en existencias"
        for option in options
    )
    return f"Como alternativa tengo: {listed}."
