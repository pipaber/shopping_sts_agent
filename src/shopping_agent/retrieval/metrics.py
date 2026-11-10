"""Métricas de recuperación con las etiquetas ESCI.

Las qrels solo se usan aquí y en el entrenamiento; el agente no las consulta.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def dcg(gains: np.ndarray, k: int) -> float:
    top = np.asarray(gains, dtype=float)[:k]
    return float((top / np.log2(np.arange(2, len(top) + 2))).sum())


def ndcg(ranked_gains: np.ndarray, k: int = 10) -> float:
    """nDCG@k de una lista ya ordenada por el sistema. Vale 0 si nada es relevante."""
    ideal = dcg(np.sort(ranked_gains)[::-1], k)
    return dcg(ranked_gains, k) / ideal if ideal > 0 else 0.0


def evaluate(
    scores: np.ndarray,
    query_ids: list[int],
    product_ids: list[str],
    qrels: pd.DataFrame,
    k: int = 10,
    recall_depth: int = 50,
) -> dict[str, float]:
    """Evalúa una matriz de puntuaciones ``(n_consultas, n_productos)``.

    - ``ndcg@k``: métrica del enunciado. Ordena solo los candidatos anotados de
      cada consulta.
    - ``recall@depth``: fracción de productos exactos (E) entre los primeros
      ``depth`` de todo el catálogo. Mide si la primera etapa deja a tiempo los
      buenos candidatos para el reranker.
    """
    column = {product_id: index for index, product_id in enumerate(product_ids)}
    row = {query_id: index for index, query_id in enumerate(query_ids)}

    ndcgs, recalls = [], []
    for query_id, group in qrels.groupby("query_id"):
        query_scores = scores[row[query_id]]
        candidates = group["product_id"].map(column).to_numpy()
        gains = group["gain"].to_numpy()

        order = np.argsort(-query_scores[candidates], kind="stable")
        ndcgs.append(ndcg(gains[order], k))

        exact = candidates[group["esci_label"].to_numpy() == "E"]
        if len(exact):
            top = np.argpartition(-query_scores, recall_depth)[:recall_depth]
            recalls.append(np.isin(exact, top).mean())

    return {
        f"ndcg@{k}": float(np.mean(ndcgs)),
        f"recall@{recall_depth}": float(np.mean(recalls)),
        "queries": len(ndcgs),
    }
