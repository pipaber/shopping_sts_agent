"""Lo que se guarda de una conversación: las operaciones de cada turno y el estado
final de la tienda, en datos y en Markdown. Lo comparten el chat por texto y el de voz."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from shopping_agent.agent.state import Step
from shopping_agent.store.db import connect
from shopping_agent.store.ops import format_eur

OPERATION_FIELDS = ("tool", "args", "reason", "ok", "summary", "issues")
SUMMARY_CHARS = 300

_ORDERS = "SELECT order_id, quote_id, total_cents FROM orders"
_ORDER_ITEMS = "SELECT order_id, product_id, quantity, unit_price_cents FROM order_items"
_CART_ITEMS = "SELECT cart_id, product_id, quantity FROM cart_items"
_INVENTORY_CHANGES = (
    "SELECT inv.product_id, seed.inventory.stock AS initial_stock, inv.stock FROM inventory AS inv "
    "JOIN seed.inventory USING (product_id) WHERE inv.stock != seed.inventory.stock"
)


def _rows(conn: sqlite3.Connection, query: str) -> list[dict[str, Any]]:
    cursor = conn.execute(query)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor]


def store_snapshot(db_path: Path, seed_path: Path) -> dict[str, Any]:
    """Pedidos, carritos y cambios de inventario respecto a la tienda inicial."""
    conn = connect(db_path)
    try:
        snapshot = {
            "orders": _rows(conn, _ORDERS),
            "order_items": _rows(conn, _ORDER_ITEMS),
            "cart_items": _rows(conn, _CART_ITEMS),
        }
        if seed_path.exists():
            conn.execute("ATTACH DATABASE ? AS seed", (str(seed_path),))
            snapshot["inventory_changes"] = _rows(conn, _INVENTORY_CHANGES)
        return snapshot
    finally:
        conn.close()


def operation_records(operations: Sequence[Step]) -> list[dict[str, Any]]:
    """Las operaciones de un turno sin su resultado en bruto, que no se guarda."""
    return [{key: operation.get(key) for key in OPERATION_FIELDS} for operation in operations]


def operation_lines(operations: Sequence[dict[str, Any]]) -> list[str]:
    """Una línea de Markdown por operación; lista vacía si el turno no tuvo ninguna."""
    lines = []
    for operation in operations:
        args = ", ".join(f"{key}={json.dumps(value, ensure_ascii=False)}" for key, value in operation["args"].items())
        status = "OK" if operation["ok"] else "RECHAZADO"
        summary = " ".join(str(operation["summary"]).split())
        if len(summary) > SUMMARY_CHARS:
            summary = summary[:SUMMARY_CHARS] + "…"
        lines.append(f"- `{operation['tool']}({args})` → {status}: {summary}")
    return [*lines, ""] if lines else []


def store_lines(store: dict[str, Any]) -> list[str]:
    lines = ["## Estado final de la tienda", ""]
    lines += [f"- Pedido {order['order_id']}: total {format_eur(order['total_cents'])}" for order in store["orders"]]
    lines += [
        f"  - pedido {item['order_id']}: {item['quantity']} × `{item['product_id']}` a {format_eur(item['unit_price_cents'])}"
        for item in store["order_items"]
    ]
    lines += [
        f"- Inventario `{change['product_id']}`: {change['initial_stock']} → {change['stock']}"
        for change in store.get("inventory_changes", [])
    ]
    lines.append(f"- Líneas de carrito pendientes: {len(store['cart_items'])}")
    return lines
