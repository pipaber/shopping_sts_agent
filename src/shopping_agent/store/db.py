"""Tienda simulada en SQLite: esquema, datos ficticios con semilla y restauración.

Los importes se guardan en céntimos (enteros) para que las sumas sean exactas.

Uso::

    python -m shopping_agent.store.db --catalog datasets/processed/catalog.parquet
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from collections.abc import Iterable
from pathlib import Path

import numpy as np

SCHEMA = """
CREATE TABLE inventory (
    product_id  TEXT PRIMARY KEY,
    price_cents INTEGER NOT NULL CHECK (price_cents > 0),
    stock       INTEGER NOT NULL CHECK (stock >= 0)
);
CREATE TABLE carts (
    cart_id TEXT PRIMARY KEY
);
CREATE TABLE cart_items (
    cart_id    TEXT NOT NULL REFERENCES carts (cart_id),
    product_id TEXT NOT NULL REFERENCES inventory (product_id),
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (cart_id, product_id)
);
CREATE TABLE quotes (
    quote_id     TEXT PRIMARY KEY,
    cart_id      TEXT NOT NULL REFERENCES carts (cart_id),
    total_cents  INTEGER NOT NULL CHECK (total_cents >= 0),
    budget_cents INTEGER CHECK (budget_cents IS NULL OR budget_cents >= 0)
);
CREATE TABLE quote_items (
    quote_id         TEXT NOT NULL REFERENCES quotes (quote_id),
    product_id       TEXT NOT NULL REFERENCES inventory (product_id),
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents > 0),
    PRIMARY KEY (quote_id, product_id)
);
-- UNIQUE (quote_id): confirmar dos veces la misma cotización no crea otro pedido.
CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id    TEXT NOT NULL UNIQUE REFERENCES quotes (quote_id),
    total_cents INTEGER NOT NULL CHECK (total_cents >= 0)
);
CREATE TABLE order_items (
    order_id         INTEGER NOT NULL REFERENCES orders (order_id),
    product_id       TEXT NOT NULL REFERENCES inventory (product_id),
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents > 0),
    PRIMARY KEY (order_id, product_id)
);
"""

OUT_OF_STOCK_RATE = 0.10
MAX_STOCK = 50


def connect(path: Path | str) -> sqlite3.Connection:
    """Conexión en autocommit; las transacciones se abren de forma explícita."""
    conn = sqlite3.connect(path, isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _remove(path: Path) -> None:
    for candidate in (path, Path(f"{path}-wal"), Path(f"{path}-shm"), Path(f"{path}-journal")):
        candidate.unlink(missing_ok=True)


def build_seed(product_ids: Iterable[str], seed_path: Path, seed: int = 42) -> int:
    """Crea la tienda inicial. El resultado solo depende de los ids y de la semilla."""
    ids = sorted(set(product_ids))
    rng = np.random.default_rng(seed)

    euros = np.clip(rng.lognormal(mean=3.0, sigma=0.9, size=len(ids)), 1.0, 2000.0)
    prices = np.round(euros * 100).astype(int)
    out_of_stock = rng.random(len(ids)) < OUT_OF_STOCK_RATE
    stock = np.where(out_of_stock, 0, rng.integers(1, MAX_STOCK + 1, size=len(ids)))

    seed_path.parent.mkdir(parents=True, exist_ok=True)
    _remove(seed_path)
    conn = connect(seed_path)
    try:
        conn.executescript(SCHEMA)
        conn.execute("BEGIN")
        conn.executemany(
            "INSERT INTO inventory (product_id, price_cents, stock) VALUES (?, ?, ?)",
            zip(ids, prices.tolist(), stock.tolist(), strict=True),
        )
        conn.execute("COMMIT")
    finally:
        conn.close()
    return len(ids)


def restore(seed_path: Path, db_path: Path) -> None:
    """Devuelve la tienda de trabajo a su estado inicial."""
    if not seed_path.exists():
        raise FileNotFoundError(f"No existe la tienda inicial: {seed_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _remove(db_path)
    shutil.copyfile(seed_path, db_path)


def main() -> None:
    import pandas as pd

    parser = argparse.ArgumentParser(description="Tienda simulada: genera el estado inicial y lo restaura.")
    parser.add_argument("--catalog", type=Path, default=Path("datasets/processed/catalog.parquet"))
    parser.add_argument("--seed-db", type=Path, default=Path("datasets/processed/store_seed.sqlite"))
    parser.add_argument("--db", type=Path, default=Path("datasets/processed/store.sqlite"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    ids = pd.read_parquet(args.catalog, columns=["product_id"])["product_id"]
    n = build_seed(ids, args.seed_db, args.seed)
    restore(args.seed_db, args.db)
    print(f"productos en la tienda: {n}")


if __name__ == "__main__":
    main()
