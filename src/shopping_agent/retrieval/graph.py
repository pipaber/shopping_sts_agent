"""Grafo consulta–producto sobre el que trabaja el reranker.

Nodos: consultas y productos, con su embedding de texto como características.
Cada relación es un tensor ``(2, n_aristas)`` con el origen en la primera fila y
el destino en la segunda; el mensaje viaja del origen al destino.

- ``candidate`` (producto → consulta): los primeros del híbrido para esa consulta.
  No usa etiquetas, así que una consulta nueva entra al grafo igual que las demás.
- ``similar`` (producto → producto): vecinos más cercanos en el espacio de embeddings.
- ``brand`` (producto → producto): productos de la misma marca.
- ``exact`` (consulta → producto): la consulta de ajuste tiene ese producto anotado
  como exacto. Es la única relación que lleva etiquetas, y solo va hacia el
  producto: ninguna consulta recibe mensajes por ella.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd
import torch

from shopping_agent.retrieval.text import clean

# Tipo de nodo de origen y de destino de cada relación.
ENDPOINTS = {
    "candidate": ("product", "query"),
    "similar": ("product", "product"),
    "brand": ("product", "product"),
    "exact": ("query", "product"),
}
RELATIONS = tuple(ENDPOINTS)


@dataclass(frozen=True)
class RerankGraph:
    product_x: torch.Tensor
    query_x: torch.Tensor
    edges: dict[str, torch.Tensor]

    def to(self, device: torch.device | str) -> RerankGraph:
        edges = {relation: index.to(device) for relation, index in self.edges.items()}
        return RerankGraph(self.product_x.to(device), self.query_x.to(device), edges)

    def without_labels_of(self, queries: torch.Tensor) -> RerankGraph:
        """El mismo grafo sin las aristas ``exact`` que salen de ``queries``.

        Es lo que impide que una consulta de ajuste vea sus propias etiquetas: al
        entrenar con ella, sus productos exactos no la tienen como vecina, igual
        que le pasará a una consulta nueva.
        """
        exact = self.edges["exact"]
        keep = ~torch.isin(exact[0], queries)
        return replace(self, edges={**self.edges, "exact": exact[:, keep]})

    def with_query(self, embedding: torch.Tensor, candidates: torch.Tensor) -> tuple[RerankGraph, int]:
        """Añade una consulta nueva conectada solo a sus candidatos. Devuelve su índice."""
        index = len(self.query_x)
        new_edges = torch.stack([candidates, torch.full_like(candidates, index)])
        edges = {**self.edges, "candidate": torch.cat([self.edges["candidate"], new_edges], dim=1)}
        return RerankGraph(self.product_x, torch.cat([self.query_x, embedding.unsqueeze(0)]), edges), index


def similar_edges(embeddings: torch.Tensor, k: int, chunk: int = 4096) -> torch.Tensor:
    """Cada producto recibe de sus ``k`` vecinos más parecidos por coseno."""
    k = min(k, len(embeddings) - 1)
    if k < 1:
        return torch.empty((2, 0), dtype=torch.long, device=embeddings.device)
    neighbours = []
    for start in range(0, len(embeddings), chunk):
        scores = embeddings[start : start + chunk] @ embeddings.T
        _mask_self(scores, start)
        neighbours.append(scores.topk(k).indices)
    sources = torch.cat(neighbours)
    targets = torch.arange(len(embeddings), device=embeddings.device).unsqueeze(1).expand_as(sources)
    return torch.stack([sources.reshape(-1), targets.reshape(-1)])


def _mask_self(scores: torch.Tensor, start: int) -> None:
    """Un producto no es vecino de sí mismo: ``scores`` empieza en la fila ``start``."""
    rows = torch.arange(len(scores), device=scores.device)
    scores[rows, rows + start] = -torch.inf


def brand_edges(brands: Sequence[object], embeddings: torch.Tensor, k: int) -> torch.Tensor:
    """Cada producto recibe de hasta ``k`` productos de su marca, los más parecidos."""
    names = pd.Series([clean(brand).lower() for brand in brands])
    parts = [torch.empty((2, 0), dtype=torch.long, device=embeddings.device)]
    for name, rows in names.groupby(names).indices.items():
        if name and len(rows) > 1:
            rows = torch.as_tensor(rows, device=embeddings.device)
            parts.append(rows[similar_edges(embeddings[rows], k)])
    return torch.cat(parts, dim=1)


def candidate_edges(top: np.ndarray) -> torch.Tensor:
    """``top[i]`` son las filas del catálogo de los candidatos de la consulta ``i``."""
    queries = np.repeat(np.arange(len(top)), top.shape[1])
    return torch.as_tensor(np.stack([top.reshape(-1), queries]), dtype=torch.long)


def exact_edges(qrels: pd.DataFrame, query_index: dict[int, int], product_index: dict[str, int]) -> torch.Tensor:
    """Aristas consulta → producto exacto. ``qrels`` solo debe traer consultas de ajuste."""
    is_exact = (qrels["esci_label"] == "E").to_numpy()
    queries = qrels["query_id"].map(query_index).to_numpy()[is_exact]
    products = qrels["product_id"].map(product_index).to_numpy()[is_exact]
    return torch.as_tensor(np.stack([queries, products]), dtype=torch.long)
