"""Señales de la primera etapa (BM25, denso y fusión RRF) para un grupo de consultas.

Es lo único que el reranker sabe de una consulta además de su embedding: no usa
etiquetas. El entrenamiento y el agente las calculan con esta misma función, para
que las características sean idénticas en los dos sitios.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from shopping_agent.retrieval.retrievers import RRF_K, rrf

FEATURES = ("coseno denso", "BM25 relativo al máximo de la consulta", "RRF relativo a su máximo")


class Lexical(Protocol):
    def score(self, queries: list[str]) -> np.ndarray: ...


class Embedder(Protocol):
    doc_embeddings: np.ndarray

    def embed(self, queries: list[str]) -> np.ndarray: ...


@dataclass(frozen=True)
class FirstStage:
    """Matrices ``(n_consultas, n_productos)`` ya escaladas como características.

    Escalar por consulta no cambia el orden, así que también sirven para evaluar
    los modelos base.
    """

    query_embeddings: np.ndarray
    dense: np.ndarray  # coseno entre la consulta y el producto
    lexical: np.ndarray  # BM25 dividido por el máximo de la consulta
    fused: np.ndarray  # RRF de los dos, con 1 para un producto primero en ambos

    def top(self, k: int) -> np.ndarray:
        """Filas del catálogo de los ``k`` primeros del híbrido, por consulta."""
        return np.argsort(-self.fused, axis=1, kind="stable")[:, :k]

    def features(self, query_rows: np.ndarray, product_rows: np.ndarray) -> np.ndarray:
        """Características de cada par (consulta, producto), en el orden de ``FEATURES``."""
        pairs = (query_rows, product_rows)
        return np.stack([self.dense[pairs], self.lexical[pairs], self.fused[pairs]], axis=-1)


def first_stage(queries: list[str], bm25: Lexical, dense: Embedder) -> FirstStage:
    query_embeddings = dense.embed(queries)
    dense_scores = query_embeddings @ dense.doc_embeddings.T
    bm25_scores = bm25.score(queries)
    best = np.maximum(bm25_scores.max(axis=1, keepdims=True), 1e-9)
    return FirstStage(
        query_embeddings=query_embeddings,
        dense=dense_scores,
        lexical=bm25_scores / best,
        fused=rrf([bm25_scores, dense_scores]) * (RRF_K + 1) / 2,
    )
