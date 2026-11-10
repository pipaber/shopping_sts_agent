"""Operaciones de la tienda simulada y sus validaciones.

Todo lo que decide si una compra es válida vive aquí y es código determinista:
cantidades (enteros positivos), presupuesto y existencias. Ninguna función
depende del LLM. Cada operación devuelve un :class:`OpResult`; cuando se rechaza,
``issues`` lleva un código estable, un mensaje en español y los datos necesarios
para que el agente explique el motivo o proponga una alternativa.

Los importes van siempre en céntimos (enteros). Las escrituras abren una
transacción ``BEGIN IMMEDIATE`` y, si algo se rechaza, no queda ningún cambio.
"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from typing import Any

# Códigos de rechazo. Son estables: el agente y las pruebas se apoyan en ellos.
INVALID_QUANTITY = "cantidad_invalida"
INVALID_BUDGET = "presupuesto_invalido"
UNKNOWN_PRODUCT = "producto_desconocido"
OUT_OF_STOCK = "agotado"
INSUFFICIENT_STOCK = "stock_insuficiente"
BUDGET_EXCEEDED = "presupuesto_excedido"
NOT_IN_CART = "no_esta_en_el_carrito"
EMPTY_CART = "carrito_vacio"
UNKNOWN_QUOTE = "cotizacion_inexistente"
STALE_QUOTE = "cotizacion_obsoleta"
PRICE_CHANGED = "precio_cambiado"


@dataclass(frozen=True)
class Issue:
    """Motivo por el que se rechazó una operación."""

    code: str
    message: str
    product_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OpResult:
    """Resultado de una operación: ``data`` si se aplicó, ``issues`` si se rechazó."""

    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    issues: tuple[Issue, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "data": self.data, "issues": [issue.to_dict() for issue in self.issues]}

    @property
    def codes(self) -> list[str]:
        return [issue.code for issue in self.issues]


class _Rejected(Exception):
    """Interrumpe una transacción para deshacerla; lleva los motivos."""

    def __init__(self, *issues: Issue) -> None:
        super().__init__(", ".join(issue.code for issue in issues))
        self.issues = issues


def format_eur(cents: int) -> str:
    """``1234`` → ``"12,34 €"``."""
    sign = "-" if cents < 0 else ""
    euros, rest = divmod(abs(cents), 100)
    return f"{sign}{euros:,}".replace(",", ".") + f",{rest:02d} €"


# --- Validaciones puras -------------------------------------------------------


def check_quantity(quantity: object) -> Issue | None:
    """La cantidad debe ser un entero positivo (``True`` o ``2.0`` no valen)."""
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        return Issue(
            INVALID_QUANTITY,
            f"La cantidad debe ser un número entero mayor que cero (se recibió {quantity!r}).",
            details={"quantity": quantity if isinstance(quantity, (int, float, str)) else repr(quantity)},
        )
    return None


def check_budget(budget_cents: object) -> Issue | None:
    """El presupuesto es opcional; si existe, es un entero positivo de céntimos."""
    if budget_cents is None:
        return None
    if isinstance(budget_cents, bool) or not isinstance(budget_cents, int) or budget_cents <= 0:
        return Issue(
            INVALID_BUDGET,
            f"El presupuesto debe ser un importe mayor que cero (se recibió {budget_cents!r}).",
        )
    return None


def _budget_issue(total_cents: int, budget_cents: int, **details: Any) -> Issue:
    return Issue(
        BUDGET_EXCEEDED,
        f"El total sería {format_eur(total_cents)} y supera el presupuesto de "
        f"{format_eur(budget_cents)} por {format_eur(total_cents - budget_cents)}.",
        details={
            "total_cents": total_cents,
            "budget_cents": budget_cents,
            "excess_cents": total_cents - budget_cents,
            **details,
        },
    )


def _stock_issue(product_id: str, requested: int, available: int) -> Issue:
    if available == 0:
        return Issue(
            OUT_OF_STOCK,
            f"El producto {product_id} está agotado.",
            product_id,
            {"requested": requested, "available": 0},
        )
    return Issue(
        INSUFFICIENT_STOCK,
        f"Solo {'queda 1 unidad' if available == 1 else f'quedan {available} unidades'} del producto "
        f"{product_id} y se pidieron {requested}.",
        product_id,
        {"requested": requested, "available": available},
    )


# --- Transacciones ------------------------------------------------------------


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[None]:
    """``BEGIN IMMEDIATE`` … ``COMMIT``; cualquier excepción deshace todo."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")


def _write(conn: sqlite3.Connection, action: Callable[[], dict[str, Any]]) -> OpResult:
    try:
        with transaction(conn):
            return OpResult(True, action())
    except _Rejected as rejected:
        return OpResult(False, issues=rejected.issues)


# --- Lecturas -----------------------------------------------------------------


def _inventory_row(conn: sqlite3.Connection, product_id: str) -> tuple[int, int] | None:
    return conn.execute(
        "SELECT price_cents, stock FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchone()


def _cart_view(conn: sqlite3.Connection, cart_id: str) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT ci.product_id, ci.quantity, inv.price_cents, inv.stock
        FROM cart_items AS ci JOIN inventory AS inv USING (product_id)
        WHERE ci.cart_id = ? ORDER BY ci.rowid
        """,
        (cart_id,),
    ).fetchall()
    items = [
        {
            "product_id": product_id,
            "quantity": quantity,
            "unit_price_cents": price,
            "subtotal_cents": price * quantity,
            "stock": stock,
        }
        for product_id, quantity, price, stock in rows
    ]
    return {"cart_id": cart_id, "items": items, "total_cents": sum(item["subtotal_cents"] for item in items)}


def price_and_stock(conn: sqlite3.Connection, product_id: str) -> OpResult:
    """Precio y existencias actuales de un producto."""
    row = _inventory_row(conn, product_id)
    if row is None:
        return OpResult(False, issues=(_unknown_product(product_id),))
    return OpResult(True, {"product_id": product_id, "price_cents": row[0], "stock": row[1]})


def get_cart(conn: sqlite3.Connection, cart_id: str) -> OpResult:
    """Contenido del carrito con precios y existencias actuales."""
    return OpResult(True, _cart_view(conn, cart_id))


def _unknown_product(product_id: object) -> Issue:
    return Issue(UNKNOWN_PRODUCT, f"El producto {product_id!r} no existe en la tienda.", str(product_id))


# --- Carrito ------------------------------------------------------------------


def _put_in_cart(
    conn: sqlite3.Connection,
    cart_id: str,
    product_id: str,
    quantity: int,
    budget_cents: int | None,
    *,
    add: bool,
) -> OpResult:
    """Deja el producto con ``quantity`` unidades (o las suma si ``add``)."""
    invalid = [issue for issue in (check_quantity(quantity), check_budget(budget_cents)) if issue]
    if invalid:
        return OpResult(False, issues=tuple(invalid))

    def action() -> dict[str, Any]:
        row = _inventory_row(conn, product_id)
        if row is None:
            raise _Rejected(_unknown_product(product_id))
        price, stock = row
        cart = _cart_view(conn, cart_id)
        current = next((item["quantity"] for item in cart["items"] if item["product_id"] == product_id), 0)
        target = current + quantity if add else quantity
        if target > stock:
            raise _Rejected(_stock_issue(product_id, target, stock))
        if budget_cents is not None:
            others = cart["total_cents"] - current * price
            total = others + target * price
            if total > budget_cents:
                affordable = max((budget_cents - others) // price, 0)
                raise _Rejected(
                    _budget_issue(
                        total,
                        budget_cents,
                        product_id=product_id,
                        unit_price_cents=price,
                        max_quantity=min(affordable, stock),
                    )
                )
        conn.execute("INSERT OR IGNORE INTO carts (cart_id) VALUES (?)", (cart_id,))
        conn.execute(
            """
            INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (?, ?, ?)
            ON CONFLICT (cart_id, product_id) DO UPDATE SET quantity = excluded.quantity
            """,
            (cart_id, product_id, target),
        )
        return _cart_view(conn, cart_id)

    return _write(conn, action)


def add_to_cart(
    conn: sqlite3.Connection, cart_id: str, product_id: str, quantity: int, budget_cents: int | None = None
) -> OpResult:
    """Suma ``quantity`` unidades al carrito si hay existencias y cabe en el presupuesto."""
    return _put_in_cart(conn, cart_id, product_id, quantity, budget_cents, add=True)


def set_quantity(
    conn: sqlite3.Connection, cart_id: str, product_id: str, quantity: int, budget_cents: int | None = None
) -> OpResult:
    """Cambia la cantidad de un producto que ya está en el carrito."""
    invalid = check_quantity(quantity)
    if invalid:
        return OpResult(False, issues=(invalid,))
    in_cart = conn.execute(
        "SELECT 1 FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, product_id)
    ).fetchone()
    if in_cart is None:
        return OpResult(False, issues=(_not_in_cart(product_id),))
    return _put_in_cart(conn, cart_id, product_id, quantity, budget_cents, add=False)


def remove_from_cart(conn: sqlite3.Connection, cart_id: str, product_id: str) -> OpResult:
    """Quita un producto del carrito."""

    def action() -> dict[str, Any]:
        deleted = conn.execute(
            "DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, product_id)
        ).rowcount
        if deleted == 0:
            raise _Rejected(_not_in_cart(product_id))
        return _cart_view(conn, cart_id)

    return _write(conn, action)


def _not_in_cart(product_id: str) -> Issue:
    return Issue(NOT_IN_CART, f"El producto {product_id} no está en el carrito.", product_id)


# --- Cotización y pedido --------------------------------------------------------


def create_quote(
    conn: sqlite3.Connection, cart_id: str, budget_cents: int | None = None, quote_id: str | None = None
) -> OpResult:
    """Congela el carrito en una cotización tras validar existencias y presupuesto.

    La cotización guarda los precios unitarios y el presupuesto vigentes; no
    reserva existencias, por eso la confirmación vuelve a comprobarlo todo.
    """
    invalid = check_budget(budget_cents)
    if invalid:
        return OpResult(False, issues=(invalid,))

    def action() -> dict[str, Any]:
        cart = _cart_view(conn, cart_id)
        if not cart["items"]:
            raise _Rejected(Issue(EMPTY_CART, "El carrito está vacío; no hay nada que cotizar."))
        issues = [
            _stock_issue(item["product_id"], item["quantity"], item["stock"])
            for item in cart["items"]
            if item["quantity"] > item["stock"]
        ]
        if budget_cents is not None and cart["total_cents"] > budget_cents:
            issues.append(_budget_issue(cart["total_cents"], budget_cents))
        if issues:
            raise _Rejected(*issues)

        new_id = quote_id or uuid.uuid4().hex
        conn.execute(
            "INSERT INTO quotes (quote_id, cart_id, total_cents, budget_cents) VALUES (?, ?, ?, ?)",
            (new_id, cart_id, cart["total_cents"], budget_cents),
        )
        conn.executemany(
            "INSERT INTO quote_items (quote_id, product_id, quantity, unit_price_cents) VALUES (?, ?, ?, ?)",
            [(new_id, item["product_id"], item["quantity"], item["unit_price_cents"]) for item in cart["items"]],
        )
        return {
            "quote_id": new_id,
            "cart_id": cart_id,
            "items": cart["items"],  # incluye el stock visto al cotizar
            "total_cents": cart["total_cents"],
            "budget_cents": budget_cents,
        }

    return _write(conn, action)


def _order_view(conn: sqlite3.Connection, order_id: int) -> dict[str, Any]:
    order_id, quote_id, total = conn.execute(
        "SELECT order_id, quote_id, total_cents FROM orders WHERE order_id = ?", (order_id,)
    ).fetchone()
    items = [
        {
            "product_id": product_id,
            "quantity": quantity,
            "unit_price_cents": price,
            "subtotal_cents": price * quantity,
        }
        for product_id, quantity, price in conn.execute(
            "SELECT product_id, quantity, unit_price_cents FROM order_items WHERE order_id = ? ORDER BY rowid",
            (order_id,),
        )
    ]
    return {"order_id": order_id, "quote_id": quote_id, "items": items, "total_cents": total}


def confirm_quote(conn: sqlite3.Connection, quote_id: str) -> OpResult:
    """Registra el pedido de una cotización en una sola transacción.

    Dentro de ``BEGIN IMMEDIATE`` se vuelve a comprobar, contra el estado actual
    de la tienda, que el carrito sigue siendo el cotizado, que los precios no
    cambiaron, que hay existencias y que el total cabe en el presupuesto. Solo
    entonces se crea el pedido, se descuenta el inventario y se vacía el carrito.
    Si algo falla no queda ningún cambio. Confirmar otra vez la misma cotización
    devuelve el pedido ya registrado (``already_confirmed``) sin tocar nada.
    """

    def action() -> dict[str, Any]:
        existing = conn.execute("SELECT order_id FROM orders WHERE quote_id = ?", (quote_id,)).fetchone()
        if existing is not None:
            return {**_order_view(conn, existing[0]), "already_confirmed": True}

        quote = conn.execute(
            "SELECT cart_id, total_cents, budget_cents FROM quotes WHERE quote_id = ?", (quote_id,)
        ).fetchone()
        if quote is None:
            raise _Rejected(Issue(UNKNOWN_QUOTE, f"No existe la cotización {quote_id!r}."))
        cart_id, quoted_total, budget_cents = quote
        quoted = conn.execute(
            "SELECT product_id, quantity, unit_price_cents FROM quote_items WHERE quote_id = ? ORDER BY rowid",
            (quote_id,),
        ).fetchall()

        cart = _cart_view(conn, cart_id)
        in_cart = {item["product_id"]: item["quantity"] for item in cart["items"]}
        if in_cart != {product_id: quantity for product_id, quantity, _ in quoted}:
            raise _Rejected(
                Issue(STALE_QUOTE, "El carrito cambió después de cotizar; hay que cotizar de nuevo.")
            )

        issues: list[Issue] = []
        total_now = 0
        for product_id, quantity, quoted_price in quoted:
            # La clave foránea de quote_items garantiza que el producto existe.
            price, stock = _inventory_row(conn, product_id) or (quoted_price, 0)
            total_now += price * quantity
            if quantity > stock:
                issues.append(_stock_issue(product_id, quantity, stock))
            if price != quoted_price:
                issues.append(
                    Issue(
                        PRICE_CHANGED,
                        f"El precio del producto {product_id} cambió de {format_eur(quoted_price)} "
                        f"a {format_eur(price)}.",
                        product_id,
                        {"quoted_price_cents": quoted_price, "price_cents": price},
                    )
                )
        if budget_cents is not None and total_now > budget_cents:
            issues.append(_budget_issue(total_now, budget_cents))
        if issues:
            raise _Rejected(*issues)

        order_id = conn.execute(
            "INSERT INTO orders (quote_id, total_cents) VALUES (?, ?)", (quote_id, quoted_total)
        ).lastrowid
        conn.executemany(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price_cents) VALUES (?, ?, ?, ?)",
            [(order_id, product_id, quantity, price) for product_id, quantity, price in quoted],
        )
        # El CHECK (stock >= 0) del esquema es la última barrera: si fallara, se deshace todo.
        conn.executemany(
            "UPDATE inventory SET stock = stock - ? WHERE product_id = ?",
            [(quantity, product_id) for product_id, quantity, _ in quoted],
        )
        conn.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart_id,))
        assert order_id is not None
        return {**_order_view(conn, order_id), "already_confirmed": False}

    return _write(conn, action)
