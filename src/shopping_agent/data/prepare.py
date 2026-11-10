"""Prepara el catálogo y las consultas a partir de ESCI (versión reducida, español).

Salidas en ``out_dir``:

- ``catalog.parquet``: productos con título, descripción, atributos e identificador.
- ``queries_{train,test}.parquet``: ``query_id`` y texto de la consulta.
- ``qrels_{train,test}.parquet``: etiquetas ESCI y ganancia por pareja consulta-producto.

Las qrels se guardan aparte del catálogo a propósito: sirven para entrenar (train)
y evaluar (test), y el agente nunca debe leerlas.

Uso::

    python -m shopping_agent.data.prepare --raw datasets --out datasets/processed
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

EXAMPLES_FILE = "shopping_queries_dataset_examples.parquet"
PRODUCTS_FILE = "shopping_queries_dataset_products.parquet"

LOCALE = "es"
GAINS = {"E": 1.0, "S": 0.1, "C": 0.01, "I": 0.0}
CATALOG_COLUMNS = [
    "product_id",
    "product_title",
    "product_description",
    "product_bullet_point",
    "product_brand",
    "product_color",
]
MIN_CATALOG = 5000
MIN_TEST_QUERIES = 200


def load_examples(raw_dir: Path) -> pd.DataFrame:
    """Parejas consulta-producto de la versión reducida en español."""
    df = pd.read_parquet(raw_dir / EXAMPLES_FILE)
    df = df[(df["product_locale"] == LOCALE) & (df["small_version"] == 1)]
    return df[["query_id", "query", "product_id", "esci_label", "split"]].reset_index(drop=True)


def load_products(raw_dir: Path) -> pd.DataFrame:
    """Productos en español; un ``product_id`` puede repetirse en otros locales."""
    df = pd.read_parquet(
        raw_dir / PRODUCTS_FILE,
        columns=[*CATALOG_COLUMNS, "product_locale"],
        filters=[("product_locale", "==", LOCALE)],
    )
    return df[CATALOG_COLUMNS].drop_duplicates("product_id").reset_index(drop=True)


def select_queries(
    examples: pd.DataFrame,
    available_products: set[str],
    n_train: int,
    n_test: int,
    seed: int,
) -> pd.DataFrame:
    """Muestrea consultas por ``query_id`` y devuelve sus parejas anotadas.

    Solo son elegibles las consultas cuyos productos anotados existen todos en
    ``available_products``, para que el catálogo las cubra por completo.
    """
    covered = examples["product_id"].isin(available_products)
    eligible = covered.groupby(examples["query_id"]).all()
    eligible_ids = set(eligible[eligible].index)

    rng = np.random.default_rng(seed)
    chosen: list[int] = []
    for split, n in (("train", n_train), ("test", n_test)):
        ids = sorted(set(examples.loc[examples["split"] == split, "query_id"]) & eligible_ids)
        if len(ids) < n:
            raise ValueError(f"Solo hay {len(ids)} consultas elegibles en {split}; se pidieron {n}.")
        chosen.extend(rng.choice(ids, size=n, replace=False).tolist())

    return examples[examples["query_id"].isin(chosen)].reset_index(drop=True)


def prepare(raw_dir: Path, out_dir: Path, n_train: int, n_test: int, seed: int) -> dict[str, int]:
    if n_test < MIN_TEST_QUERIES:
        raise ValueError(f"El enunciado exige al menos {MIN_TEST_QUERIES} consultas de evaluación.")

    examples = load_examples(raw_dir)
    products = load_products(raw_dir)
    selected = select_queries(examples, set(products["product_id"]), n_train, n_test, seed)

    catalog = (
        products[products["product_id"].isin(set(selected["product_id"]))]
        .sort_values("product_id")
        .reset_index(drop=True)
    )
    if len(catalog) < MIN_CATALOG:
        raise ValueError(
            f"El catálogo tiene {len(catalog)} productos; se exigen {MIN_CATALOG}. "
            "Aumenta --n-train o --n-test."
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    catalog.to_parquet(out_dir / "catalog.parquet", index=False)

    selected = selected.assign(gain=selected["esci_label"].map(GAINS))
    for split in ("train", "test"):
        part = selected[selected["split"] == split]
        queries = part[["query_id", "query"]].drop_duplicates("query_id").sort_values("query_id")
        qrels = part[["query_id", "product_id", "esci_label", "gain"]].sort_values(
            ["query_id", "product_id"]
        )
        queries.to_parquet(out_dir / f"queries_{split}.parquet", index=False)
        qrels.to_parquet(out_dir / f"qrels_{split}.parquet", index=False)

    return {
        "catalog": len(catalog),
        "train_queries": int(selected.loc[selected["split"] == "train", "query_id"].nunique()),
        "test_queries": int(selected.loc[selected["split"] == "test", "query_id"].nunique()),
        "judgments": len(selected),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara catálogo, consultas y qrels de ESCI (es, versión reducida).")
    parser.add_argument("--raw", type=Path, default=Path("datasets"))
    parser.add_argument("--out", type=Path, default=Path("datasets/processed"))
    parser.add_argument("--n-train", type=int, default=1500)
    parser.add_argument("--n-test", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    stats = prepare(args.raw, args.out, args.n_train, args.n_test, args.seed)
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
