"""Grafo sintético pequeño para las pruebas del reranker (sin GPU ni modelos)."""

import numpy as np
import pandas as pd
import torch

from shopping_agent.retrieval import train
from shopping_agent.retrieval.dev_data import DevData, split_queries
from shopping_agent.retrieval.first_stage import FirstStage
from shopping_agent.retrieval.gnn import Reranker, RerankerConfig
from shopping_agent.retrieval.graph import RELATIONS

DIM, PRODUCTS, QUERIES, VALIDATION = 8, 12, 6, 2
BRANDS = ["Sony", "sony ", "JBL", None, "JBL", "Única", "", "Sony", "JBL", None, "Otra", "otra"]
GAIN = {"E": 1.0, "S": 0.1, "C": 0.01, "I": 0.0}
ALL = RerankerConfig(relations=RELATIONS, input_dim=DIM, hidden=16)
CONTROL = RerankerConfig(relations=(), input_dim=DIM, hidden=16)


def unit(rows: int, seed: int) -> np.ndarray:
    vectors = np.random.default_rng(seed).normal(size=(rows, DIM)).astype(np.float32)
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


DOC_EMBEDDINGS = unit(PRODUCTS, seed=1)


def make_data(seed: int = 0) -> DevData:
    """Seis consultas con cinco productos anotados cada una; ``seed`` cambia las etiquetas."""
    rng = np.random.default_rng(seed)
    catalog = pd.DataFrame({"product_id": [f"p{row}" for row in range(PRODUCTS)], "product_brand": BRANDS})
    queries = pd.DataFrame({"query_id": [10 + row for row in range(QUERIES)], "query": ["x"] * QUERIES})
    rows = [
        (query_id, f"p{product}", label)
        for number, query_id in enumerate(queries["query_id"])
        for product, label in zip(range(number, number + 5), rng.permutation(["E", "E", "S", "C", "I"]), strict=True)
    ]
    qrels = pd.DataFrame(rows, columns=["query_id", "product_id", "esci_label"])
    return DevData(catalog, queries, qrels.assign(gain=qrels["esci_label"].map(GAIN)))


def make_stage() -> FirstStage:
    query_embeddings = unit(QUERIES, seed=2)
    dense = query_embeddings @ DOC_EMBEDDINGS.T
    lexical = np.random.default_rng(3).random((QUERIES, PRODUCTS)).astype(np.float32)
    return FirstStage(query_embeddings, dense, lexical, fused=(dense + lexical) / 2)


def make_development(data: DevData | None = None) -> train.Development:
    return train.build_development(data or make_data(), make_stage(), DOC_EMBEDDINGS, VALIDATION, "cpu")


def trained_like(config: RerankerConfig) -> Reranker:
    """Modelo en modo de evaluación con la corrección ya distinta de cero, como tras entrenar."""
    torch.manual_seed(0)
    model = Reranker(config).eval()
    torch.nn.init.normal_(model.correction[-1].weight)
    return model


def fit_and_validation_nodes(data: DevData) -> tuple[set[int], set[int]]:
    node = {query_id: row for row, query_id in enumerate(data.queries["query_id"])}
    fit, validation = split_queries(data.queries["query_id"].tolist(), VALIDATION)
    return {node[query_id] for query_id in fit}, {node[query_id] for query_id in validation}


class FakeDense:
    """Recuperador denso de mentira: embeddings fijos, distintos para cada texto de consulta."""

    def __init__(self):
        self.doc_embeddings = DOC_EMBEDDINGS

    def embed(self, queries):
        return np.stack([unit(1, seed=sum(map(ord, query)))[0] for query in queries])

    def score(self, queries):
        return self.embed(queries) @ self.doc_embeddings.T
