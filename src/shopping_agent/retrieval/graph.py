"""Grafo heterogéneo consulta–producto sobre el que trabaja el reranker.

Es un ``HeteroData`` de PyTorch Geometric con dos tipos de nodo, ``product`` y
``query``, cuyas características son los embeddings de texto, y cuatro tipos de
arista. Cada ``edge_index`` es ``(2, n_aristas)`` con el origen en la primera fila
y el destino en la segunda; el mensaje viaja del origen al destino.

- ``(product, candidate, query)``: los primeros del híbrido para esa consulta.
  No usa etiquetas, así que una consulta nueva entra al grafo igual que las demás.
- ``(product, similar, product)``: vecinos más cercanos en el espacio de embeddings.
- ``(product, brand, product)``: productos de la misma marca.
- ``(query, exact, product)``: la consulta de ajuste tiene ese producto anotado
  como exacto. Es la única relación que lleva etiquetas, y solo va hacia el
  producto: ninguna consulta recibe mensajes por ella.
"""

from __future__ import annotations

import copy
from collections.abc import Sequence

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import HeteroData

from shopping_agent.retrieval.text import clean

PRODUCT, QUERY = "product", "query"
NODE_TYPES = (PRODUCT, QUERY)
# Tipo de arista de cada relación: (nodo de origen, relación, nodo de destino).
EDGE_TYPES = {
    "candidate": (PRODUCT, "candidate", QUERY),
    "similar": (PRODUCT, "similar", PRODUCT),
    "brand": (PRODUCT, "brand", PRODUCT),
    "exact": (QUERY, "exact", PRODUCT),
}
RELATIONS = tuple(EDGE_TYPES)


def hetero_graph(product_x: torch.Tensor, query_x: torch.Tensor, edges: dict[str, torch.Tensor]) -> HeteroData:
    """El grafo a partir de las características de los nodos y las aristas de cada relación."""
    graph = HeteroData()
    graph[PRODUCT].x = product_x
    graph[QUERY].x = query_x
    for relation, edge_index in edges.items():
        graph[EDGE_TYPES[relation]].edge_index = edge_index
    return graph


def edges_by_relation(graph: HeteroData) -> dict[str, torch.Tensor]:
    return {relation: graph[edge_type].edge_index for relation, edge_type in EDGE_TYPES.items()}


def without_labels_of(graph: HeteroData, queries: torch.Tensor) -> HeteroData:
    """El mismo grafo sin las aristas ``exact`` que salen de ``queries``.

    Es lo que impide que una consulta de ajuste vea sus propias etiquetas: al
    entrenar con ella, sus productos exactos no la tienen como vecina, igual
    que le pasará a una consulta nueva.
    """
    exact = graph[EDGE_TYPES["exact"]].edge_index
    masked = copy.copy(graph)
    masked[EDGE_TYPES["exact"]].edge_index = exact[:, ~torch.isin(exact[0], queries)]
    return masked


def with_query(graph: HeteroData, embedding: torch.Tensor, candidates: torch.Tensor) -> tuple[HeteroData, int]:
    """Añade una consulta nueva conectada solo a sus candidatos. Devuelve el grafo
    ampliado y el índice de la consulta; el grafo original no cambia."""
    index = graph[QUERY].num_nodes
    new_edges = torch.stack([candidates, torch.full_like(candidates, index)])
    extended = copy.copy(graph)
    extended[QUERY].x = torch.cat([graph[QUERY].x, embedding.unsqueeze(0)])
    candidate = EDGE_TYPES["candidate"]
    extended[candidate].edge_index = torch.cat([graph[candidate].edge_index, new_edges], dim=1)
    return extended, index


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
