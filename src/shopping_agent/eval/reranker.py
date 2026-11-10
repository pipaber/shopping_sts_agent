"""Compara en validación los modelos base, el control sin grafo y las variantes del reranker.

Uso::

    python -m shopping_agent.eval.reranker --seeds 5

Todo se entrena con las 1 200 consultas de ajuste y se mide con las 300 de
validación; las de test no se leen. Cada variante se entrena con varias semillas.
Escribe ``results/reranker_validation.json`` y ``.md``.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from shopping_agent.retrieval.dev_data import SPLIT_SEED, VALIDATION_QUERIES, DevData, load_dev_data
from shopping_agent.retrieval.first_stage import FirstStage, first_stage
from shopping_agent.retrieval.gnn import Reranker
from shopping_agent.retrieval.graph import edges_by_relation
from shopping_agent.retrieval.metrics import ndcg_by_query, ndcg_of_rankings
from shopping_agent.retrieval.retrievers import BM25Retriever
from shopping_agent.retrieval.text import ALL_FIELDS, product_texts
from shopping_agent.retrieval.train import (
    BRAND_NEIGHBOURS,
    CANDIDATES,
    DEFAULT_DATA_DIR,
    NEIGHBOURS,
    RANDOM_NEGATIVES,
    VARIANTS,
    Development,
    TrainConfig,
    annotated_scores,
    build_development,
    default_device,
    load_dense,
    score_lists,
    train_reranker,
)

ANNOTATED = "ndcg@10"  # la métrica del enunciado: solo los candidatos anotados
CATALOG = "ndcg@10_catalog"  # la lista sobre todo el catálogo; sin anotar = irrelevante
BASELINES = {"BM25 (base léxica)": "lexical", "Denso (e5-small)": "dense", "Híbrido RRF": "fused"}
CONTROL = "control"
REFERENCES = {"dense": "Denso (e5-small)", "hybrid": "Híbrido RRF"}  # el agente sin reranker usa el híbrido
# Diferencias que se reportan: métrica y sistema de referencia.
COMPARISONS = [(ANNOTATED, "dense"), (ANNOTATED, CONTROL), (ANNOTATED, "hybrid"), (CATALOG, "hybrid"), (CATALOG, CONTROL)]
OUT_NAME = "reranker_validation"


@dataclass(frozen=True)
class ValidationSet:
    """Las consultas de validación, ordenadas por ``query_id`` como sus qrels."""

    qrels: pd.DataFrame
    pairs: tuple[np.ndarray, np.ndarray]  # fila de la consulta y del producto de cada qrel
    query_rows: np.ndarray
    gains: np.ndarray  # (consultas, productos), cero en lo no anotado


def validation_set(data: DevData, qrels: pd.DataFrame) -> ValidationSet:
    query_index = {query_id: row for row, query_id in enumerate(data.queries["query_id"])}
    product_index = {product_id: row for row, product_id in enumerate(data.catalog["product_id"])}
    query_ids = sorted(qrels["query_id"].unique())
    position = {query_id: row for row, query_id in enumerate(query_ids)}
    product_rows = qrels["product_id"].map(product_index).to_numpy()
    gains = np.zeros((len(query_ids), len(data.catalog)), dtype=np.float32)
    gains[qrels["query_id"].map(position).to_numpy(), product_rows] = qrels["gain"].to_numpy()
    return ValidationSet(
        qrels=qrels,
        pairs=(qrels["query_id"].map(query_index).to_numpy(), product_rows),
        query_rows=np.array([query_index[query_id] for query_id in query_ids]),
        gains=gains,
    )


def baseline_metrics(stage: FirstStage, validation: ValidationSet) -> dict[str, dict[str, np.ndarray]]:
    """Las dos métricas, por consulta, de cada modelo base."""
    metrics = {}
    for name, signal in BASELINES.items():
        scores = getattr(stage, signal)
        ranked = np.argsort(-scores[validation.query_rows], axis=1, kind="stable")[:, :10]
        metrics[name] = {
            ANNOTATED: ndcg_by_query(validation.qrels, scores[validation.pairs]).to_numpy(),
            CATALOG: ndcg_of_rankings(ranked, validation.gains),
        }
    return metrics


@torch.no_grad()
def reranker_metrics(model: Reranker, development: Development, validation: ValidationSet) -> dict[str, np.ndarray]:
    """Las dos métricas, por consulta, de un reranker ya entrenado."""
    scores = annotated_scores(model, development.graph, development.validation)
    top = development.validation_top
    order = score_lists(model, development.graph, top).argsort(dim=1, descending=True)
    ranked = top.products.gather(1, order).cpu().numpy()
    return {
        ANNOTATED: ndcg_by_query(validation.qrels, scores).to_numpy(),
        CATALOG: ndcg_of_rankings(ranked, validation.gains),
    }


def paired_difference(system: np.ndarray, reference: np.ndarray, samples: int = 10_000) -> dict[str, float | list[float]]:
    """Diferencia media por consulta e intervalo del 95 % por bootstrap de consultas."""
    difference = system - reference
    rows = np.random.default_rng(0).integers(0, len(difference), size=(samples, len(difference)))
    low, high = np.quantile(difference[rows].mean(axis=1), [0.025, 0.975])
    return {"diff": float(difference.mean()), "ci95": [float(low), float(high)]}


def mean_by_query(runs: list[dict[str, np.ndarray]]) -> dict[str, np.ndarray]:
    """Media entre semillas de cada métrica, consulta a consulta."""
    return {metric: np.mean([run[metric] for run in runs], axis=0) for metric in (ANNOTATED, CATALOG)}


def summarize(
    runs: list[dict[str, np.ndarray]], references: dict[str, dict[str, np.ndarray]]
) -> dict[str, object]:
    """Media y desviación entre semillas, y diferencia con cada referencia."""
    summary: dict[str, object] = {}
    for metric in (ANNOTATED, CATALOG):
        per_seed = [float(run[metric].mean()) for run in runs]
        spread = float(np.std(per_seed, ddof=1)) if len(per_seed) > 1 else 0.0
        summary[metric] = {"mean": float(np.mean(per_seed)), "std": spread, "per_seed": per_seed}
    by_query = mean_by_query(runs)
    summary["differences"] = {
        f"{metric}_vs_{name}": paired_difference(by_query[metric], references[name][metric])
        for metric, name in COMPARISONS
    }
    return summary


def compare(
    development: Development, validation: ValidationSet, stage: FirstStage, seeds: int, epochs: int
) -> dict[str, object]:
    baselines = baseline_metrics(stage, validation)
    runs = {}
    for name, config in VARIANTS.items():
        trainings = [TrainConfig(epochs=epochs, seed=seed) for seed in range(seeds)]
        models = [train_reranker(config, training, development.graph, development.fit) for training in trainings]
        runs[name] = [reranker_metrics(model, development, validation) for model in models]
        print(f"{name}: {np.mean([run[ANNOTATED].mean() for run in runs[name]]):.4f}", flush=True)
    references = {name: baselines[system] for name, system in REFERENCES.items()}
    references[CONTROL] = mean_by_query(runs[CONTROL])
    return {
        "baselines": {
            name: {metric: float(values.mean()) for metric, values in metrics.items()}
            for name, metrics in baselines.items()
        },
        "rerankers": {
            name: {"relations": list(config.relations), "conv": config.conv, **summarize(runs[name], references)}
            for name, config in VARIANTS.items()
        },
    }


def protocol(development: Development, seeds: int, epochs: int) -> dict[str, object]:
    edges = {relation: int(index.shape[1]) for relation, index in edges_by_relation(development.graph).items()}
    return {
        "fit_queries": len(development.fit.queries),
        "validation_queries": len(development.validation.queries),
        "split_seed": SPLIT_SEED,
        "seeds": list(range(seeds)),
        "training": asdict(replace(TrainConfig(epochs=epochs), seed=0)) | {"seed": "una por corrida"},
        "model": asdict(VARIANTS[CONTROL]) | {"relations": "según la variante"},
        "graph": {"candidates": CANDIDATES, "neighbours": NEIGHBOURS, "brand_neighbours": BRAND_NEIGHBOURS, "edges": edges},
        "random_negatives_per_fit_query": RANDOM_NEGATIVES,
    }


def signed(value: float) -> str:
    return f"{value:+.4f}".replace(".", ",").replace("-", "−")


def number(value: float) -> str:
    return f"{value:.4f}".replace(".", ",")


def difference(result: dict, metric: str, reference: str) -> str:
    found = result["differences"][f"{metric}_vs_{reference}"]
    low, high = found["ci95"]
    return f"{signed(found['diff'])} [{signed(low)}; {signed(high)}]"


def reranker_row(name: str, result: dict) -> str:
    cells = [f"`{name}`", ", ".join(result["relations"]) or "ninguna"]
    cells += [f"{number(result[metric]['mean'])} ± {number(result[metric]['std'])}" for metric in (ANNOTATED, CATALOG)]
    cells += [difference(result, ANNOTATED, "dense"), difference(result, ANNOTATED, CONTROL)]
    return "| " + " | ".join(cells) + " |"


def agent_row(name: str, result: dict) -> str:
    cells = [f"`{name}`", difference(result, ANNOTATED, "hybrid")]
    cells += [difference(result, CATALOG, "hybrid"), difference(result, CATALOG, CONTROL)]
    return "| " + " | ".join(cells) + " |"


def explanation(info: dict) -> list[str]:
    return [
        "# Reranker: comparación en validación",
        "",
        f"{info['fit_queries']} consultas de ajuste y {info['validation_queries']} de validación (partición de train, "
        f"semilla {info['split_seed']}); {len(info['seeds'])} semillas de entrenamiento por variante. "
        "Las consultas de test no se han usado.",
        "",
        "- **nDCG@10 anotados**: la métrica del enunciado (solo los candidatos anotados de cada consulta).",
        "- **nDCG@10 catálogo**: los 10 primeros sobre todo el catálogo, contando lo no anotado como irrelevante. "
        f"Los rerankers reordenan los {info['graph']['candidates']} primeros del híbrido, como en el agente.",
        "- Media ± desviación típica entre semillas. Las diferencias se calculan consulta a consulta, "
        "con intervalo del 95 % por bootstrap de consultas.",
        "",
    ]


def to_markdown(record: dict) -> str:
    baselines, rerankers = record["baselines"].items(), record["rerankers"].items()
    lines = explanation(record["protocol"])
    lines += ["| Sistema | nDCG@10 anotados | nDCG@10 catálogo |", "|---|---|---|"]
    lines += [f"| {name} | {number(found[ANNOTATED])} | {number(found[CATALOG])} |" for name, found in baselines]
    lines += [
        "",
        "| Reranker | Aristas | nDCG@10 anotados | nDCG@10 catálogo | Anotados: dif. con el denso "
        "| Anotados: dif. con el control |",
        "|---|---|---|---|---|---|",
    ]
    lines += [reranker_row(name, result) for name, result in rerankers]
    lines += [
        "",
        "Frente al híbrido, que es lo que usa el agente sin reranker:",
        "",
        "| Reranker | Anotados: dif. con el híbrido | Catálogo: dif. con el híbrido | Catálogo: dif. con el control |",
        "|---|---|---|---|",
    ]
    lines += [agent_row(name, result) for name, result in rerankers]
    return "\n".join(lines) + "\n"


def run(data_dir: Path, seeds: int, epochs: int, out_dir: Path, device: str) -> dict[str, object]:
    data = load_dev_data(data_dir)
    dense = load_dense(data_dir)
    bm25 = BM25Retriever(product_texts(data.catalog, ALL_FIELDS))
    stage = first_stage(data.queries["query"].tolist(), bm25, dense)
    development = build_development(data, stage, dense.doc_embeddings, VALIDATION_QUERIES, device)
    validation = validation_set(data, development.validation_qrels)
    record = {"protocol": protocol(development, seeds, epochs), **compare(development, validation, stage, seeds, epochs)}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{OUT_NAME}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / f"{OUT_NAME}.md").write_text(to_markdown(record), encoding="utf-8")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara el reranker con sus controles en validación.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--seeds", type=int, default=5, help="semillas de entrenamiento por variante")
    parser.add_argument("--epochs", type=int, default=TrainConfig().epochs)
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()
    record = run(args.data, args.seeds, args.epochs, args.out, default_device())
    print(to_markdown(record))


if __name__ == "__main__":
    main()
