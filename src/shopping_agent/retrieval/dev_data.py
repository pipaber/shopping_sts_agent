"""Datos de desarrollo del reranker: las consultas de train, en ajuste y validación.

El reranker se entrena con las consultas de ajuste y se elige con las de validación.
Las consultas de test y sus qrels no se leen aquí ni en ningún módulo de
entrenamiento: este es el único punto por el que entran consultas y etiquetas.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

SPLIT_SEED = 42
VALIDATION_QUERIES = 300


@dataclass(frozen=True)
class DevData:
    """Catálogo, consultas de train y sus qrels (ordenadas por consulta)."""

    catalog: pd.DataFrame
    queries: pd.DataFrame
    qrels: pd.DataFrame


def load_dev_data(data_dir: Path) -> DevData:
    """Lee el catálogo y la partición de train; la de test no se toca."""
    qrels = pd.read_parquet(data_dir / "qrels_train.parquet")
    return DevData(
        catalog=pd.read_parquet(data_dir / "catalog.parquet").reset_index(drop=True),
        queries=pd.read_parquet(data_dir / "queries_train.parquet").reset_index(drop=True),
        qrels=qrels.sort_values("query_id", kind="stable").reset_index(drop=True),
    )


def split_queries(
    query_ids: list[int], validation: int = VALIDATION_QUERIES, seed: int = SPLIT_SEED
) -> tuple[list[int], list[int]]:
    """Reparte las consultas por ``query_id`` en ajuste y validación, con semilla fija.

    El resultado no depende del orden de entrada.
    """
    if not 0 < validation < len(query_ids):
        raise ValueError(f"No se pueden apartar {validation} consultas de {len(query_ids)}.")
    shuffled = np.random.default_rng(seed).permutation(sorted(query_ids)).tolist()
    return sorted(shuffled[validation:]), sorted(shuffled[:validation])
