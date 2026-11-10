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


def ndcg_by_query(qrels: pd.DataFrame, scores: np.ndarray, k: int = 10) -> pd.Series:
    """nDCG@k de cada consulta sobre sus candidatos anotados.

    ``scores`` trae la puntuación del sistema para cada fila de ``qrels``.
    """
    order = np.lexsort((-np.asarray(scores, dtype=float), qrels["query_id"].to_numpy()))
    ranked = qrels.iloc[order]
    return ranked.groupby("query_id", sort=True)["gain"].agg(lambda gains: ndcg(gains.to_numpy(), k))


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
    pairs = (qrels["query_id"].map(row).to_numpy(), qrels["product_id"].map(column).to_numpy())
    ndcgs = ndcg_by_query(qrels, scores[pairs], k)

    recalls = []
    exact = qrels[qrels["esci_label"] == "E"]
    for query_id, group in exact.groupby("query_id"):
        query_scores = scores[row[query_id]]
        top = np.argpartition(-query_scores, recall_depth)[:recall_depth]
        recalls.append(np.isin(group["product_id"].map(column).to_numpy(), top).mean())

    return {
        f"ndcg@{k}": float(ndcgs.mean()),
        f"recall@{recall_depth}": float(np.mean(recalls)),
        "queries": len(ndcgs),
    }
