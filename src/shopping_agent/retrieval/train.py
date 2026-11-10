"""Entrenamiento del reranker con las consultas de ajuste.

Uso::

    python -m shopping_agent.retrieval.train --variant control --seed 0

Entrena la variante con las 1 200 consultas de ajuste y guarda los pesos y el
grafo en ``datasets/processed/reranker_<variante>.v2.pt`` (fuera de git; se
regenera con este comando). La comparación entre variantes está en ``shopping_agent.eval.reranker``.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import HeteroData

from shopping_agent.retrieval.dev_data import SPLIT_SEED, VALIDATION_QUERIES, DevData, load_dev_data, split_queries
from shopping_agent.retrieval.first_stage import Embedder, FirstStage, first_stage
from shopping_agent.retrieval.gnn import Reranker, RerankerConfig, pairwise_gain_loss
from shopping_agent.retrieval.graph import (
    PRODUCT,
    QUERY,
    brand_edges,
    candidate_edges,
    edges_by_relation,
    exact_edges,
    hetero_graph,
    similar_edges,
    without_labels_of,
)
from shopping_agent.retrieval.metrics import ndcg_by_query
from shopping_agent.retrieval.retrievers import DEFAULT_DENSE_MODEL, BM25Retriever, DenseRetriever
from shopping_agent.retrieval.text import ALL_FIELDS, SHORT_FIELDS, product_texts

DEFAULT_DATA_DIR = Path("datasets/processed")
DEFAULT_VARIANT = "control"  # la que usa el agente si no se le pide otra
# Va en el nombre del archivo de pesos. La 2 es la de las capas con HeteroConv, que
# cambiaron los nombres de los parámetros: unos pesos anteriores no se pueden cargar.
WEIGHTS_VERSION = 2
CANDIDATES = 50  # los mismos que el agente pide al híbrido
NEIGHBOURS = 10
BRAND_NEIGHBOURS = 5
RANDOM_NEGATIVES = 20  # productos al azar que se añaden como irrelevantes a cada consulta de ajuste
RANDOM_LABEL = "azar"

NO_LABELS = ("candidate", "similar", "brand")

# Variantes que se comparan en validación. ``control`` no tiene paso de mensajes:
# es el mismo modelo de puntuación sin grafo.
VARIANTS = {
    "control": RerankerConfig(relations=()),
    "sage_candidate": RerankerConfig(relations=("candidate",)),
    "sage_similar": RerankerConfig(relations=("similar",)),
    "sage_brand": RerankerConfig(relations=("brand",)),
    "sage_exact_only": RerankerConfig(relations=("exact",)),
    "sage": RerankerConfig(relations=NO_LABELS),
    "sage_exact": RerankerConfig(relations=(*NO_LABELS, "exact")),
    "gatv2": RerankerConfig(relations=NO_LABELS, conv="gatv2"),
    "gatv2_exact": RerankerConfig(relations=(*NO_LABELS, "exact"), conv="gatv2"),
}


@dataclass(frozen=True)
class TrainConfig:
    """Los mismos valores para todas las variantes, elegidos en validación."""

    epochs: int = 12
    batch_size: int = 64
    lr: float = 1e-3
    weight_decay: float = 1e-2
    seed: int = 0


@dataclass(frozen=True)
class RankingLists:
    """Candidatos de varias consultas, rellenados hasta el mismo largo.

    ``queries`` es el nodo de cada consulta; el resto es ``(consultas, candidatos)``
    y ``mask`` marca las posiciones que no son relleno.
    """

    queries: torch.Tensor
    products: torch.Tensor
    features: torch.Tensor
    gains: torch.Tensor
    mask: torch.Tensor

    def to(self, device: torch.device | str) -> RankingLists:
        return RankingLists(*(getattr(self, name).to(device) for name in self.__dataclass_fields__))

    def batch(self, rows: torch.Tensor) -> RankingLists:
        return RankingLists(*(getattr(self, name)[rows] for name in self.__dataclass_fields__))


@dataclass(frozen=True)
class Development:
    """Lo que hace falta para entrenar y validar: el grafo, con todas las consultas
    de desarrollo como nodos y etiquetas solo de las de ajuste; los candidatos
    anotados de cada parte (los de ajuste, con sus irrelevantes al azar), y los
    primeros del híbrido para las de validación (lo que el agente le daría a
    reordenar al reranker)."""

    graph: HeteroData
    fit: RankingLists
    validation: RankingLists
    validation_top: RankingLists
    validation_qrels: pd.DataFrame


def add_random_negatives(qrels: pd.DataFrame, product_ids: np.ndarray, per_query: int, seed: int) -> pd.DataFrame:
    """Añade a cada consulta productos del catálogo al azar, como irrelevantes.

    Los candidatos anotados de una consulta tienen todos algo que ver con ella. El
    agente, en cambio, reordena los primeros del híbrido, donde también hay
    productos fuera de tema; sin estos ejemplos el modelo no aprende a dejarlos
    atrás. Un producto al azar entre decenas de miles casi nunca es relevante.
    """
    rng = np.random.default_rng(seed)
    size = min(per_query, len(product_ids))
    judged = qrels.groupby("query_id", sort=True)["product_id"].agg(set)
    rows = [
        (query_id, product_id)
        for query_id, seen in judged.items()
        for product_id in rng.choice(product_ids, size=size, replace=False)
        if product_id not in seen
    ]
    extra = pd.DataFrame(rows, columns=["query_id", "product_id"]).assign(esci_label=RANDOM_LABEL, gain=0.0)
    return pd.concat([qrels, extra]).sort_values("query_id", kind="stable").reset_index(drop=True)


def annotated_lists(
    qrels: pd.DataFrame, query_index: dict[int, int], product_index: dict[str, int], stage: FirstStage
) -> RankingLists:
    """Los candidatos anotados de cada consulta de ``qrels``, que viene ordenada por
    consulta: las posiciones con ``mask`` siguen el orden de sus filas."""
    query_rows = qrels["query_id"].map(query_index).to_numpy()
    product_rows = qrels["product_id"].map(product_index).to_numpy()
    by_query = qrels.groupby("query_id", sort=True)
    cell = (by_query.ngroup().to_numpy(), by_query.cumcount().to_numpy())
    shape = (cell[0].max() + 1, cell[1].max() + 1)

    def padded(values: np.ndarray) -> torch.Tensor:
        table = np.zeros(shape + values.shape[1:], dtype=values.dtype)
        table[cell] = values
        return torch.as_tensor(table)

    return RankingLists(
        queries=padded(query_rows)[:, 0],
        products=padded(product_rows),
        features=padded(stage.features(query_rows, product_rows).astype(np.float32)),
        gains=padded(qrels["gain"].to_numpy(dtype=np.float32)),
        mask=padded(np.ones(len(qrels), dtype=bool)),
    )


def candidate_lists(stage: FirstStage, top: np.ndarray, query_rows: np.ndarray) -> RankingLists:
    """Los primeros del híbrido de cada consulta, sin etiquetas (las ganancias van a cero)."""
    products = top[query_rows]
    queries = np.repeat(query_rows[:, None], products.shape[1], axis=1)
    return RankingLists(
        queries=torch.as_tensor(query_rows),
        products=torch.as_tensor(products),
        features=torch.as_tensor(stage.features(queries, products).astype(np.float32)),
        gains=torch.zeros(products.shape),
        mask=torch.ones(products.shape, dtype=torch.bool),
    )


def build_graph(
    data: DevData, stage: FirstStage, top: np.ndarray, doc_embeddings: np.ndarray, exact: torch.Tensor, device: str
) -> HeteroData:
    """Grafo con todas las consultas de desarrollo. ``exact`` son las aristas con
    etiqueta, que solo deben salir de consultas de ajuste."""
    product_x = torch.as_tensor(doc_embeddings, device=device)
    edges = {
        "candidate": candidate_edges(top),
        "similar": similar_edges(product_x, NEIGHBOURS),
        "brand": brand_edges(data.catalog["product_brand"].tolist(), product_x, BRAND_NEIGHBOURS),
        "exact": exact,
    }
    return hetero_graph(product_x, torch.as_tensor(stage.query_embeddings), edges).to(device)


def build_development(
    data: DevData, stage: FirstStage, doc_embeddings: np.ndarray, validation: int, device: str
) -> Development:
    fit_ids, validation_ids = split_queries(data.queries["query_id"].tolist(), validation)
    is_fit = data.qrels["query_id"].isin(fit_ids)
    fit_qrels, validation_qrels = data.qrels[is_fit], data.qrels[~is_fit]
    query_index = {query_id: row for row, query_id in enumerate(data.queries["query_id"])}
    product_index = {product_id: row for row, product_id in enumerate(data.catalog["product_id"])}
    top = stage.top(CANDIDATES)
    exact = exact_edges(fit_qrels, query_index, product_index)
    fit_qrels = add_random_negatives(fit_qrels, data.catalog["product_id"].to_numpy(), RANDOM_NEGATIVES, SPLIT_SEED)
    validation_rows = np.array([query_index[query_id] for query_id in validation_ids])
    return Development(
        graph=build_graph(data, stage, top, doc_embeddings, exact, device),
        fit=annotated_lists(fit_qrels, query_index, product_index, stage).to(device),
        validation=annotated_lists(validation_qrels, query_index, product_index, stage).to(device),
        validation_top=candidate_lists(stage, top, validation_rows).to(device),
        validation_qrels=validation_qrels,
    )


def score_lists(model: Reranker, graph: HeteroData, lists: RankingLists) -> torch.Tensor:
    """Puntuación de cada candidato de cada lista, ``(consultas, candidatos)``."""
    states = model.encode(graph)
    queries = lists.queries.unsqueeze(1).expand_as(lists.products)
    return model.score(states, queries, lists.products, lists.features)


def train_step(model: Reranker, optimizer: torch.optim.Optimizer, graph: HeteroData, batch: RankingLists) -> float:
    """Un paso con un lote de consultas, que no ven sus propias etiquetas en el grafo."""
    model.train()
    scores = score_lists(model, without_labels_of(graph, batch.queries), batch)
    loss = pairwise_gain_loss(scores, batch.gains, batch.mask)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    return loss.item()


def train_reranker(config: RerankerConfig, training: TrainConfig, graph: HeteroData, lists: RankingLists) -> Reranker:
    device = graph[PRODUCT].x.device
    torch.manual_seed(training.seed)
    model = Reranker(config).to(device)
    model.set_feature_scale(lists.features[lists.mask])
    optimizer = torch.optim.AdamW(model.parameters(), lr=training.lr, weight_decay=training.weight_decay)
    for _ in range(training.epochs):
        for rows in torch.randperm(len(lists.queries)).split(training.batch_size):
            train_step(model, optimizer, graph, lists.batch(rows.to(device)))
    return model.eval()


@torch.no_grad()
def annotated_scores(model: Reranker, graph: HeteroData, lists: RankingLists) -> np.ndarray:
    """Una puntuación por fila de las qrels con las que se hicieron las listas."""
    return score_lists(model, graph, lists)[lists.mask].cpu().numpy()


def save_reranker(path: Path, model: Reranker, graph: HeteroData) -> None:
    """Pesos, configuración y grafo. Los embeddings de los productos no se guardan:
    son los del catálogo, que el agente ya tiene."""
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "config": asdict(model.config),
            "state": {name: value.cpu() for name, value in model.state_dict().items()},
            "query_x": graph[QUERY].x.cpu(),
            "edges": {relation: index.cpu() for relation, index in edges_by_relation(graph).items()},
            "products": graph[PRODUCT].num_nodes,
        },
        path,
    )


def weights_path(data_dir: Path, variant: str) -> Path:
    """Dónde se guardan los pesos de una variante."""
    return data_dir / f"reranker_{variant}.v{WEIGHTS_VERSION}.pt"


def prepare(data_dir: Path, dense: Embedder, validation: int, device: str) -> Development:
    """Carga los datos de desarrollo y calcula la primera etapa y el grafo."""
    data = load_dev_data(data_dir)
    bm25 = BM25Retriever(product_texts(data.catalog, ALL_FIELDS))
    stage = first_stage(data.queries["query"].tolist(), bm25, dense)
    return build_development(data, stage, dense.doc_embeddings, validation, device)


def default_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def load_dense(data_dir: Path, model_name: str = DEFAULT_DENSE_MODEL) -> DenseRetriever:
    """El recuperador denso con los embeddings del catálogo ya calculados."""
    catalog = pd.read_parquet(data_dir / "catalog.parquet")
    cache = data_dir / f"emb_{model_name.replace('/', '__')}.npy"
    return DenseRetriever(product_texts(catalog, SHORT_FIELDS), model_name, cache_path=cache)


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena el reranker con las consultas de ajuste.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--variant", choices=sorted(VARIANTS), default=DEFAULT_VARIANT)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=None, help="por defecto, <data>/reranker_<variante>.v2.pt")
    args = parser.parse_args()

    development = prepare(args.data, load_dense(args.data), VALIDATION_QUERIES, default_device())
    model = train_reranker(VARIANTS[args.variant], TrainConfig(seed=args.seed), development.graph, development.fit)
    out = args.out or weights_path(args.data, args.variant)
    save_reranker(out, model, development.graph)
    scores = annotated_scores(model, development.graph, development.validation)
    validation = ndcg_by_query(development.validation_qrels, scores).mean()
    print(f"Variante {args.variant}, semilla {args.seed}: nDCG@10 en validación {validation:.4f}; pesos en {out}")


if __name__ == "__main__":
    main()
