"""Reranker ya entrenado, listo para el agente: reordena los primeros del híbrido.

La consulta entra al grafo conectada solo a sus candidatos, sin etiquetas, y se
puntúa con las mismas señales de la primera etapa que en el entrenamiento.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from shopping_agent.retrieval.first_stage import Embedder, Lexical, first_stage
from shopping_agent.retrieval.gnn import Reranker, RerankerConfig
from shopping_agent.retrieval.graph import RerankGraph
from shopping_agent.retrieval.train import weights_path


class GraphReranker:
    def __init__(self, variant: str, model: Reranker, graph: RerankGraph, bm25: Lexical, dense: Embedder) -> None:
        self.variant = variant
        self.model = model.eval()
        self.graph = graph
        self.bm25 = bm25
        self.dense = dense

    @classmethod
    def load(cls, data_dir: Path, variant: str, bm25: Lexical, dense: Embedder, device: str) -> GraphReranker:
        """Lee los pesos y el grafo que guardó ``shopping_agent.retrieval.train``."""
        path = weights_path(data_dir, variant)
        if not path.exists():
            raise FileNotFoundError(
                f"No están los pesos del reranker en {path}. Se generan con "
                f"`python -m shopping_agent.retrieval.train --variant {variant}`; para buscar "
                "sin reranker, define SHOPPING_AGENT_RERANKER=off."
            )
        saved = torch.load(path, map_location=device, weights_only=True)
        if saved["products"] != len(dense.doc_embeddings):
            raise ValueError(f"{path} se entrenó con otro catálogo; vuelve a entrenar el reranker.")
        model = Reranker(RerankerConfig(**saved["config"]))
        model.load_state_dict(saved["state"])
        graph = RerankGraph(torch.as_tensor(dense.doc_embeddings), saved["query_x"], saved["edges"])
        return cls(variant, model.to(device), graph.to(device), bm25, dense)

    @torch.no_grad()
    def rank(self, query: str, top: int) -> np.ndarray:
        """Filas del catálogo de los ``top`` primeros del híbrido, reordenadas."""
        stage = first_stage([query], self.bm25, self.dense)
        rows = stage.top(top)[0]
        device = self.graph.product_x.device
        candidates = torch.as_tensor(rows, device=device)
        embedding = torch.as_tensor(stage.query_embeddings[0], device=device)
        graph, node = self.graph.with_query(embedding, candidates)
        features = torch.as_tensor(stage.features(np.zeros_like(rows), rows), device=device)
        scores = self.model.score(self.model.encode(graph), torch.full_like(candidates, node), candidates, features)
        return rows[scores.argsort(descending=True, stable=True).cpu().numpy()]
