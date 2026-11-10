import threading

import pytest

from shopping_agent.store import ops
from shopping_agent.store.db import SCHEMA, connect

# producto: (precio en céntimos, stock)
INVENTORY = {"A": (1000, 5), "B": (2500, 2), "C": (400, 0), "D": (999, 50)}


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "store.sqlite"
    conn = connect(path)
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO inventory (product_id, price_cents, stock) VALUES (?, ?, ?)",
        [(product_id, price, stock) for product_id, (price, stock) in INVENTORY.items()],
    )
    conn.close()
    return path


@pytest.fixture
def conn(db_path):
    connection = connect(db_path)
    yield connection
    connection.close()


def stock(conn, product_id):
    return conn.execute("SELECT stock FROM inventory WHERE product_id = ?", (product_id,)).fetchone()[0]


def snapshot(conn):
    """Todo lo que una compra puede modificar."""
    return {
        table: conn.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()
        for table in ("inventory", "cart_items", "orders", "order_items")
    }


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_format_eur():
    assert ops.format_eur(1234) == "12,34 €"
    assert ops.format_eur(5) == "0,05 €"
    assert ops.format_eur(123456789) == "1.234.567,89 €"


def test_price_and_stock(conn):
    assert ops.price_and_stock(conn, "A").data == {"product_id": "A", "price_cents": 1000, "stock": 5}
    assert ops.price_and_stock(conn, "ZZZ").codes == [ops.UNKNOWN_PRODUCT]


def test_successful_purchase(conn):
    assert ops.add_to_cart(conn, "c1", "A", 2, budget_cents=5000).ok
    cart = ops.add_to_cart(conn, "c1", "B", 1, budget_cents=5000)
    assert cart.ok and cart.data["total_cents"] == 4500

    quote = ops.create_quote(conn, "c1", budget_cents=5000)
    assert quote.ok and quote.data["total_cents"] == 4500
    assert count(conn, "orders") == 0 and stock(conn, "A") == 5  # cotizar no compra ni reserva

    order = ops.confirm_quote(conn, quote.data["quote_id"])
    assert order.ok and not order.data["already_confirmed"]
    assert order.data["total_cents"] == 4500
    assert [(item["product_id"], item["quantity"]) for item in order.data["items"]] == [("A", 2), ("B", 1)]
    assert (stock(conn, "A"), stock(conn, "B")) == (3, 1)
    assert ops.get_cart(conn, "c1").data["items"] == []


def test_add_accumulates_and_set_replaces(conn):
    ops.add_to_cart(conn, "c1", "A", 2)
    assert ops.add_to_cart(conn, "c1", "A", 1).data["items"][0]["quantity"] == 3
    assert ops.set_quantity(conn, "c1", "A", 1).data["items"][0]["quantity"] == 1
    assert ops.set_quantity(conn, "c1", "B", 1).codes == [ops.NOT_IN_CART]
    assert ops.remove_from_cart(conn, "c1", "A").data["items"] == []
    assert ops.remove_from_cart(conn, "c1", "A").codes == [ops.NOT_IN_CART]


@pytest.mark.parametrize("quantity", [0, -1, 1.5, 2.0, "2", None, True])
def test_invalid_quantity_is_rejected(conn, quantity):
    before = snapshot(conn)
    assert ops.add_to_cart(conn, "c1", "A", quantity).codes == [ops.INVALID_QUANTITY]
    ops.add_to_cart(conn, "c2", "A", 1)
    before_set = snapshot(conn)
    assert ops.set_quantity(conn, "c2", "A", quantity).codes == [ops.INVALID_QUANTITY]
    assert snapshot(conn) == before_set != before


def test_unknown_product_is_rejected(conn):
    assert ops.add_to_cart(conn, "c1", "ZZZ", 1).codes == [ops.UNKNOWN_PRODUCT]
    assert count(conn, "cart_items") == 0


def test_budget_exceeded_when_adding(conn):
    result = ops.add_to_cart(conn, "c1", "A", 3, budget_cents=2500)
    assert result.codes == [ops.BUDGET_EXCEEDED]
    details = result.issues[0].details
    assert details["total_cents"] == 3000 and details["excess_cents"] == 500
    assert details["max_quantity"] == 2
    assert count(conn, "cart_items") == 0

    assert ops.add_to_cart(conn, "c1", "A", 2, budget_cents=2500).ok
    # El presupuesto cuenta todo el carrito, no solo la línea que se cambia.
    assert ops.add_to_cart(conn, "c1", "D", 1, budget_cents=2500).codes == [ops.BUDGET_EXCEEDED]
    assert ops.set_quantity(conn, "c1", "A", 3, budget_cents=2500).codes == [ops.BUDGET_EXCEEDED]
    assert ops.get_cart(conn, "c1").data["total_cents"] == 2000


def test_budget_exceeded_when_quoting_and_confirming(conn):
    ops.add_to_cart(conn, "c1", "A", 3)  # sin presupuesto todavía
    before = snapshot(conn)
    assert ops.create_quote(conn, "c1", budget_cents=2500).codes == [ops.BUDGET_EXCEEDED]
    assert count(conn, "quotes") == 0 and snapshot(conn) == before
    assert ops.create_quote(conn, "c1", budget_cents=0).codes == [ops.INVALID_BUDGET]


def test_out_of_stock_product(conn):
    result = ops.add_to_cart(conn, "c1", "C", 1)
    assert result.codes == [ops.OUT_OF_STOCK]
    assert result.issues[0].product_id == "C"
    assert count(conn, "cart_items") == 0

    over = ops.add_to_cart(conn, "c1", "B", 3)
    assert over.codes == [ops.INSUFFICIENT_STOCK]
    assert over.issues[0].details == {"requested": 3, "available": 2}


def test_empty_cart_cannot_be_quoted(conn):
    assert ops.create_quote(conn, "c1").codes == [ops.EMPTY_CART]
    assert ops.confirm_quote(conn, "no-existe").codes == [ops.UNKNOWN_QUOTE]


def test_stock_change_between_quote_and_confirmation(conn, db_path):
    ops.add_to_cart(conn, "c1", "A", 2)
    ops.add_to_cart(conn, "c1", "B", 2)
    quote = ops.create_quote(conn, "c1")
    assert quote.ok

    other = connect(db_path)  # otro cliente compra entre medias
    other.execute("UPDATE inventory SET stock = 1 WHERE product_id = 'B'")
    other.close()
    before = snapshot(conn)

    result = ops.confirm_quote(conn, quote.data["quote_id"])
    assert result.codes == [ops.INSUFFICIENT_STOCK]
    assert result.issues[0].product_id == "B"
    assert result.issues[0].details == {"requested": 2, "available": 1}
    # Ni pedido ni inventario modificado: tampoco el producto A, que sí tenía stock.
    assert snapshot(conn) == before
    assert count(conn, "orders") == 0 and stock(conn, "A") == 5

    # Tras ajustar la cantidad se cotiza de nuevo y la compra funciona.
    assert ops.confirm_quote(conn, quote.data["quote_id"]).codes == [ops.INSUFFICIENT_STOCK]
    ops.set_quantity(conn, "c1", "B", 1)
    assert ops.confirm_quote(conn, quote.data["quote_id"]).codes == [ops.STALE_QUOTE]
    assert ops.confirm_quote(conn, ops.create_quote(conn, "c1").data["quote_id"]).ok
    assert (stock(conn, "A"), stock(conn, "B")) == (3, 0)


def test_sold_out_between_quote_and_confirmation(conn):
    ops.add_to_cart(conn, "c1", "A", 1)
    quote = ops.create_quote(conn, "c1")
    conn.execute("UPDATE inventory SET stock = 0 WHERE product_id = 'A'")
    before = snapshot(conn)
    assert ops.confirm_quote(conn, quote.data["quote_id"]).codes == [ops.OUT_OF_STOCK]
    assert snapshot(conn) == before


def test_price_change_between_quote_and_confirmation(conn):
    ops.add_to_cart(conn, "c1", "A", 2, budget_cents=2000)
    quote = ops.create_quote(conn, "c1", budget_cents=2000)
    conn.execute("UPDATE inventory SET price_cents = 1100 WHERE product_id = 'A'")
    before = snapshot(conn)
    result = ops.confirm_quote(conn, quote.data["quote_id"])
    assert result.codes == [ops.PRICE_CHANGED, ops.BUDGET_EXCEEDED]
    assert snapshot(conn) == before


def test_double_confirmation_creates_one_order(conn):
    ops.add_to_cart(conn, "c1", "A", 2)
    quote_id = ops.create_quote(conn, "c1").data["quote_id"]

    first = ops.confirm_quote(conn, quote_id)
    after_first = snapshot(conn)
    second = ops.confirm_quote(conn, quote_id)

    assert first.ok and second.ok
    assert not first.data["already_confirmed"] and second.data["already_confirmed"]
    assert second.data["order_id"] == first.data["order_id"]
    assert second.data["items"] == first.data["items"]
    assert count(conn, "orders") == 1
    assert stock(conn, "A") == 3  # descontado una sola vez
    assert snapshot(conn) == after_first


def test_concurrent_confirmations_create_one_order(conn, db_path):
    ops.add_to_cart(conn, "c1", "A", 2)
    quote_id = ops.create_quote(conn, "c1").data["quote_id"]
    results = []

    def confirm():
        own = connect(db_path)
        try:
            results.append(ops.confirm_quote(own, quote_id))
        finally:
            own.close()

    threads = [threading.Thread(target=confirm) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert all(result.ok for result in results)
    assert sum(not result.data["already_confirmed"] for result in results) == 1
    assert count(conn, "orders") == 1 and stock(conn, "A") == 3


def test_rollback_on_unexpected_error(conn):
    """Si el esquema rechaza el descuento, no queda ni el pedido ni cambio alguno."""
    ops.add_to_cart(conn, "c1", "A", 2)
    ops.add_to_cart(conn, "c1", "D", 1)
    quote_id = ops.create_quote(conn, "c1").data["quote_id"]
    # Un disparador simula un fallo a mitad de la transacción, tras insertar el pedido.
    conn.execute(
        "CREATE TRIGGER fallo BEFORE UPDATE ON inventory WHEN NEW.product_id = 'D' "
        "BEGIN SELECT RAISE(ABORT, 'fallo simulado'); END"
    )
    before = snapshot(conn)
    with pytest.raises(Exception, match="fallo simulado"):
        ops.confirm_quote(conn, quote_id)
    assert snapshot(conn) == before
    assert count(conn, "orders") == 0 and stock(conn, "A") == 5
    assert not conn.in_transaction
