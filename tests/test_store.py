import sqlite3

import pytest

from shopping_agent.store.db import build_seed, connect, restore

IDS = [f"P{i:04d}" for i in range(500)]


def rows(path):
    conn = connect(path)
    try:
        return conn.execute("SELECT * FROM inventory ORDER BY product_id").fetchall()
    finally:
        conn.close()


def test_seed_is_deterministic_and_order_independent(tmp_path):
    build_seed(IDS, tmp_path / "a.sqlite", seed=7)
    build_seed(reversed(IDS), tmp_path / "b.sqlite", seed=7)
    assert rows(tmp_path / "a.sqlite") == rows(tmp_path / "b.sqlite")

    build_seed(IDS, tmp_path / "c.sqlite", seed=8)
    assert rows(tmp_path / "a.sqlite") != rows(tmp_path / "c.sqlite")


def test_seed_has_valid_prices_and_some_out_of_stock(tmp_path):
    build_seed(IDS, tmp_path / "seed.sqlite")
    data = rows(tmp_path / "seed.sqlite")
    assert len(data) == len(IDS)
    assert all(price > 0 and stock >= 0 for _, price, stock in data)
    assert 0 < sum(stock == 0 for _, _, stock in data) < len(IDS)


def test_restore_reverts_changes(tmp_path):
    seed, db = tmp_path / "seed.sqlite", tmp_path / "store.sqlite"
    build_seed(IDS, seed)
    restore(seed, db)

    conn = connect(db)
    conn.execute("UPDATE inventory SET stock = 0")
    conn.execute("INSERT INTO carts (cart_id) VALUES ('c1')")
    conn.close()
    assert rows(db) != rows(seed)

    restore(seed, db)
    assert rows(db) == rows(seed)
    conn = connect(db)
    assert conn.execute("SELECT COUNT(*) FROM carts").fetchone()[0] == 0
    conn.close()


def test_stock_cannot_go_negative(tmp_path):
    build_seed(IDS, tmp_path / "seed.sqlite")
    conn = connect(tmp_path / "seed.sqlite")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE inventory SET stock = -1 WHERE product_id = 'P0000'")
    conn.close()


def test_one_order_per_quote(tmp_path):
    build_seed(IDS, tmp_path / "seed.sqlite")
    conn = connect(tmp_path / "seed.sqlite")
    conn.execute("INSERT INTO carts (cart_id) VALUES ('c1')")
    conn.execute("INSERT INTO quotes (quote_id, cart_id, total_cents) VALUES ('q1', 'c1', 100)")
    conn.execute("INSERT INTO orders (quote_id, total_cents) VALUES ('q1', 100)")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO orders (quote_id, total_cents) VALUES ('q1', 100)")
    conn.close()
