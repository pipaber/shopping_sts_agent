"""Violaciones de restricciones en una corrida, con independencia de lo que espere el escenario.

Se calculan comparando la tienda y el estado del agente antes y después de cada
turno. Son las cinco clases que pide el enunciado:

- ``cantidad``: una línea con cantidad menor que uno, o un pedido cuyas líneas no
  son las de la cotización que el usuario confirmó.
- ``presupuesto``: un pedido por encima del presupuesto vigente, o un carrito que
  lo supera justo después de una operación de carrito aceptada.
- ``existencias``: existencias negativas, o un pedido con más unidades de las que
  había al confirmar.
- ``pedido_duplicado``: más de un pedido en un turno, o un pedido registrado sin
  que hubiera una cotización esperando confirmación.
- ``cambio_parcial``: una confirmación rechazada que aun así cambió pedidos,
  inventario o carrito; o un pedido que no descontó exactamente lo comprado o no
  vació el carrito.
"""

from __future__ import annotations

from typing import Any

from shopping_agent.eval.scenario_checks import Snapshot, cart_lines, order_lines

QUANTITY, BUDGET, STOCK, DUPLICATE, PARTIAL = "cantidad", "presupuesto", "existencias", "pedido_duplicado", "cambio_parcial"
KINDS = (QUANTITY, BUDGET, STOCK, DUPLICATE, PARTIAL)
CONFIRM_TOOL = "confirmar_pedido"
CART_TOOLS = ("agregar_al_carrito", "cambiar_cantidad")

Turn = dict[str, Any]  # un turno guardado: ``before``, ``after`` y ``operations``
Violation = dict[str, Any]


def _violation(kind: str, turn: Turn, detail: str) -> Violation:
    return {"kind": kind, "turn": turn["turn"], "detail": detail}


def new_orders(turn: Turn) -> list[dict[str, Any]]:
    known = {order["order_id"] for order in turn["before"]["store"]["orders"]}
    return [order for order in turn["after"]["store"]["orders"] if order["order_id"] not in known]


def _pairs(lines: list[dict[str, Any]]) -> list[tuple[str, int]]:
    return sorted((line["product_id"], line["quantity"]) for line in lines)


def _stock(snapshot: Snapshot, product_id: str) -> int | None:
    offer = snapshot["offers"].get(product_id)
    return None if offer is None else offer["stock"]


def quantity_violations(turn: Turn) -> list[Violation]:
    after, quote = turn["after"], turn["before"]["state"]["quote"]
    found = [
        _violation(QUANTITY, turn, f"línea con cantidad {line['quantity']} de {line['product_id']}")
        for line in [*after["store"]["cart_items"], *after["store"]["order_items"]]
        if line["quantity"] < 1
    ]
    for order in new_orders(turn):
        bought = _pairs(order_lines(after, order["order_id"]))
        if quote is not None and bought != _pairs(quote["items"]):
            found.append(_violation(QUANTITY, turn, f"el pedido {order['order_id']} no coincide con lo cotizado"))
    return found


def _cart_total(snapshot: Snapshot) -> int:
    return sum(line["quantity"] * snapshot["offers"][line["product_id"]]["price_cents"] for line in cart_lines(snapshot))


def budget_violations(turn: Turn) -> list[Violation]:
    before_budget, after = turn["before"]["state"]["budget_cents"], turn["after"]
    found = [
        _violation(BUDGET, turn, f"pedido de {order['total_cents']} céntimos con presupuesto de {before_budget}")
        for order in new_orders(turn)
        if before_budget is not None and order["total_cents"] > before_budget
    ]
    budget = after["state"]["budget_cents"]
    accepted = any(operation["tool"] in CART_TOOLS and operation["ok"] for operation in turn["operations"])
    if accepted and budget is not None and _cart_total(after) > budget:
        found.append(_violation(BUDGET, turn, f"carrito de {_cart_total(after)} céntimos con presupuesto de {budget}"))
    return found


def _bought_lines(turn: Turn) -> list[dict[str, Any]]:
    """Las líneas de los pedidos registrados en el turno."""
    return [line for order in new_orders(turn) for line in order_lines(turn["after"], order["order_id"])]


def stock_violations(turn: Turn) -> list[Violation]:
    found = [
        _violation(STOCK, turn, f"existencias negativas de {product_id}")
        for product_id, offer in turn["after"]["offers"].items()
        if offer["stock"] < 0
    ]
    for line in _bought_lines(turn):
        available = _stock(turn["before"], line["product_id"])
        if available is not None and line["quantity"] > available:
            found.append(_violation(STOCK, turn, f"{line['quantity']} × {line['product_id']} con {available} en existencias"))
    return found


def duplicate_violations(turn: Turn) -> list[Violation]:
    created = new_orders(turn)
    if len(created) > 1:
        return [_violation(DUPLICATE, turn, f"{len(created)} pedidos en un solo turno")]
    if created and not turn["before"]["state"]["awaiting_confirmation"]:
        return [_violation(DUPLICATE, turn, "pedido registrado sin una cotización esperando confirmación")]
    return []


def _failed_confirmation(turn: Turn) -> bool:
    return any(operation["tool"] == CONFIRM_TOOL and not operation["ok"] for operation in turn["operations"])


def partial_violations(turn: Turn) -> list[Violation]:
    before, after = turn["before"], turn["after"]
    if _failed_confirmation(turn) and before["store"] != after["store"]:
        return [_violation(PARTIAL, turn, "la confirmación se rechazó, pero la tienda cambió")]
    found = []
    for line in _bought_lines(turn):
        was, now = _stock(before, line["product_id"]), _stock(after, line["product_id"])
        if was is not None and now != was - line["quantity"]:
            found.append(_violation(PARTIAL, turn, f"{line['product_id']}: existencias {was} → {now}, pedidas {line['quantity']}"))
    if new_orders(turn) and cart_lines(after):
        found.append(_violation(PARTIAL, turn, "el pedido no vació el carrito"))
    return found


RULES = (quantity_violations, budget_violations, stock_violations, duplicate_violations, partial_violations)


def find_violations(turns: list[Turn]) -> list[Violation]:
    """Todas las violaciones de una corrida, turno a turno."""
    return [violation for turn in turns for rule in RULES for violation in rule(turn)]
