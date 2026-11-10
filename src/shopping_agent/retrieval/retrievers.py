"""Recuperadores sobre el catálogo: léxico (BM25), denso y fusión por rangos.

Todos devuelven una matriz ``(n_consultas, n_productos)`` de puntuaciones alineada
con el orden del catálogo, de modo que la evaluación y la fusión son comunes.
"""

from __future__ import annotations

from pathlib import Path

import bm25s
import numpy as np

from shopping_agent.retrieval.text import tokenize

DEFAULT_DENSE_MODEL = "intfloat/multilingual-e5-small"


class BM25Retriever:
    """Modelo base de búsqueda léxica."""

    def __init__(self, docs: list[str]) -> None:
        self.n_docs = len(docs)
        self.index = bm25s.BM25()
        self.index.index([tokenize(doc) for doc in docs], show_progress=False)

    def score(self, queries: list[str]) -> np.ndarray:
        scores = np.zeros((len(queries), self.n_docs), dtype=np.float32)
        for row, query in enumerate(queries):
            tokens = tokenize(query)
            if tokens:
                scores[row] = self.index.get_scores(tokens)
        return scores


class DenseRetriever:
    """Embeddings de frases con similitud coseno exacta.

    Con decenas de miles de productos el producto matricial es instantáneo, así
    que no hace falta un índice aproximado.
    """

    def __init__(
        self,
        docs: list[str],
        model_name: str = DEFAULT_DENSE_MODEL,
        cache_path: Path | None = None,
        max_seq_length: int = 256,
        batch_size: int = 64,
    ) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.model.max_seq_length = max_seq_length
        self.batch_size = batch_size
        # Los modelos E5 esperan estos prefijos; el resto no usa ninguno.
        e5 = "e5" in model_name.lower()
        self.query_prefix, self.doc_prefix = ("query: ", "passage: ") if e5 else ("", "")

        if cache_path is not None and cache_path.exists():
            self.doc_embeddings = np.load(cache_path)
            if len(self.doc_embeddings) != len(docs):
                raise ValueError(f"{cache_path} no corresponde a este catálogo; bórralo y repite.")
        else:
            self.doc_embeddings = self._encode([self.doc_prefix + doc for doc in docs], progress=True)
            if cache_path is not None:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                np.save(cache_path, self.doc_embeddings)

    def _encode(self, texts: list[str], progress: bool = False) -> np.ndarray:
        return self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=progress,
            convert_to_numpy=True,
        ).astype(np.float32)

    def score(self, queries: list[str]) -> np.ndarray:
        query_embeddings = self._encode([self.query_prefix + query for query in queries])
        return query_embeddings @ self.doc_embeddings.T


def rrf(score_matrices: list[np.ndarray], k: int = 60) -> np.ndarray:
    """Reciprocal Rank Fusion: suma de ``1 / (k + rango)`` en cada recuperador."""
    fused = np.zeros_like(score_matrices[0], dtype=np.float32)
    positions = np.arange(1, fused.shape[1] + 1, dtype=np.float32)
    for scores in score_matrices:
        order = np.argsort(-scores, axis=1, kind="stable")
        ranks = np.empty_like(order, dtype=np.float32)
        np.put_along_axis(ranks, order, np.broadcast_to(positions, order.shape), axis=1)
        fused += 1.0 / (k + ranks)
    return fused
