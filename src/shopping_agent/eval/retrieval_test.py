"""Evaluación final de la recuperación con las consultas de test. Se corre una sola vez.

Uso::

    python -m shopping_agent.eval.retrieval_test

Compara BM25, denso, híbrido (RRF) y el híbrido con cada reranker (el control sin
grafo y GraphSAGE), con dos medidas por consulta:

- **nDCG@10 sobre los candidatos anotados** (ganancias E=1, S=0,1, C=0,01, I=0), la
  métrica del enunciado.
- **recall@50**: fracción de los productos exactos que quedan entre los 50 primeros
  de todo el catálogo. Los rerankers reordenan los 50 primeros del híbrido, así que
  su recall@50 es el del híbrido.

Los rerankers se entrenan igual que en la validación (las mismas consultas de
ajuste, los mismos hiperparámetros y las mismas semillas) y puntúan las consultas
de test como lo hace el agente con una consulta nueva: entran al grafo conectadas
solo a sus 50 candidatos, sin etiquetas. Las etiquetas de test solo se usan para
medir. Los intervalos son del 95 %, por bootstrap de consultas.

Es el único módulo que lee las consultas de test. Para que no se use para ajustar
nada, se niega a repetirse si el resultado ya existe (``--force`` lo permite, para
el caso de que una corrida fallara a medias). ``--render`` vuelve a escribir la
tabla a partir del resultado guardado, sin leer test: sirve para actualizar la
columna de validación si esa tabla se regenera.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import HeteroData

from shopping_agent.eval.provenance import current_commit
from shopping_agent.eval.reranker import BASELINES, paired_difference, protocol
from shopping_agent.retrieval.dev_data import VALIDATION_QUERIES, load_dev_data
from shopping_agent.retrieval.first_stage import FirstStage, first_stage
from shopping_agent.retrieval.graph import EDGE_TYPES, PRODUCT, QUERY, candidate_edges
from shopping_agent.retrieval.metrics import ndcg_by_query
from shopping_agent.retrieval.retrievers import BM25Retriever
from shopping_agent.retrieval.text import ALL_FIELDS, product_texts
from shopping_agent.retrieval.train import (
    CANDIDATES,
    DEFAULT_DATA_DIR,
    VARIANTS,
    Development,
    RankingLists,
    TrainConfig,
    annotated_lists,
    annotated_scores,
    build_development,
    default_device,
    load_dense,
    train_reranker,
)

NDCG, RECALL = "ndcg@10", "recall@50"
RERANKERS = {"control": "Híbrido + control sin grafo", "sage": "Híbrido + GraphSAGE"}
# Papel de cada reranker en el agente; se muestra junto a su nombre en la tabla.
ROLES = {"control": "la configuración del agente", "sage": "la variante del GNN"}
HYBRID = "Híbrido RRF"
OUT_NAME = "retrieval_test"
VALIDATION_FILE = "reranker_validation.json"

Scores = dict[str, np.ndarray]  # por métrica, un valor por consulta


@dataclass(frozen=True)
class EvalSet:
    """Las consultas de test, sus etiquetas (ordenadas por consulta) y su primera etapa."""

    qrels: pd.DataFrame
    stage: FirstStage
    query_index: dict[int, int]
    product_index: dict[str, int]

    @property
    def pairs(self) -> tuple[np.ndarray, np.ndarray]:
        """Fila de la consulta y del producto de cada etiqueta."""
        return self.qrels["query_id"].map(self.query_index).to_numpy(), self.qrels["product_id"].map(self.product_index).to_numpy()


def make_eval_set(queries: pd.DataFrame, qrels: pd.DataFrame, product_ids: list[str], stage: FirstStage) -> EvalSet:
    return EvalSet(
        qrels=qrels.sort_values("query_id", kind="stable").reset_index(drop=True),
        stage=stage,
        query_index={query_id: row for row, query_id in enumerate(queries["query_id"])},
        product_index={product_id: row for row, product_id in enumerate(product_ids)},
    )


def recall_by_query(scores: np.ndarray, test: EvalSet, depth: int = CANDIDATES) -> np.ndarray:
    """Por consulta con algún producto exacto: fracción de ellos entre los ``depth`` primeros."""
    top = np.argpartition(-scores, depth, axis=1)[:, :depth]
    query_rows, product_rows = test.pairs
    exact = (test.qrels["esci_label"] == "E").to_numpy()
    found = (top[query_rows[exact]] == product_rows[exact, None]).any(axis=1)
    return pd.Series(found).groupby(query_rows[exact]).mean().to_numpy()


def baseline_scores(test: EvalSet, depth: int = CANDIDATES) -> dict[str, Scores]:
    """Las dos medidas, por consulta, de BM25, denso e híbrido."""
    results = {}
    for name, signal in BASELINES.items():
        scores = getattr(test.stage, signal)
        ndcg = ndcg_by_query(test.qrels, scores[test.pairs]).to_numpy()
        results[name] = {NDCG: ndcg, RECALL: recall_by_query(scores, test, depth)}
    return results


def with_new_queries(graph: HeteroData, stage: FirstStage) -> tuple[HeteroData, int]:
    """El grafo con las consultas de ``stage`` añadidas como las añade el agente: cada
    una conectada solo a sus candidatos. Devuelve también el índice de la primera."""
    offset, device = graph[QUERY].num_nodes, graph[PRODUCT].x.device
    new_edges = candidate_edges(stage.top(CANDIDATES)).to(device)
    new_edges[1] += offset
    candidate = EDGE_TYPES["candidate"]
    extended = copy.copy(graph)
    extended[candidate].edge_index = torch.cat([graph[candidate].edge_index, new_edges], dim=1)
    extended[QUERY].x = torch.cat([graph[QUERY].x, torch.as_tensor(stage.query_embeddings, device=device)])
    return extended, offset


def lists_for(test: EvalSet, offset: int, device: str) -> RankingLists:
    """Los candidatos anotados de cada consulta de test, con su nodo en el grafo ampliado."""
    lists = annotated_lists(test.qrels, test.query_index, test.product_index, test.stage)
    return replace(lists, queries=lists.queries + offset).to(device)


def reranker_ndcg(variant: str, seeds: int, development: Development, test: EvalSet) -> list[np.ndarray]:
    """nDCG@10 por consulta de test de una variante, una lista por semilla de entrenamiento."""
    graph, offset = with_new_queries(development.graph, test.stage)
    lists = lists_for(test, offset, str(graph[PRODUCT].x.device))
    per_seed = []
    for seed in range(seeds):
        model = train_reranker(VARIANTS[variant], TrainConfig(seed=seed), development.graph, development.fit)
        per_seed.append(ndcg_by_query(test.qrels, annotated_scores(model, graph, lists)).to_numpy())
        print(f"{variant}, semilla {seed}: {per_seed[-1].mean():.4f}", flush=True)
    return per_seed


def interval(values: np.ndarray) -> dict[str, Any]:
    """Media e intervalo del 95 % por bootstrap de consultas."""
    found = paired_difference(values, np.zeros_like(values))
    return {"mean": found["diff"], "ci95": found["ci95"]}


def summarize(baselines: dict[str, Scores], rerankers: dict[str, list[np.ndarray]]) -> dict[str, Any]:
    """Cada sistema con sus intervalos y su diferencia, consulta a consulta, con el híbrido y el control."""
    hybrid = baselines[HYBRID]
    by_query = {label: np.mean(rerankers[variant], axis=0) for variant, label in RERANKERS.items()}
    systems: dict[str, Any] = {}
    for name, scores in baselines.items():
        systems[name] = {NDCG: interval(scores[NDCG]), RECALL: interval(scores[RECALL])}
        systems[name]["vs_hybrid"] = paired_difference(scores[NDCG], hybrid[NDCG])
    for variant, label in RERANKERS.items():
        per_seed = [float(run.mean()) for run in rerankers[variant]]
        systems[label] = {NDCG: interval(by_query[label]), RECALL: interval(hybrid[RECALL]), "variant": variant}
        systems[label]["per_seed"] = per_seed
        systems[label]["std"] = float(np.std(per_seed, ddof=1)) if len(per_seed) > 1 else 0.0
        systems[label]["vs_hybrid"] = paired_difference(by_query[label], hybrid[NDCG])
        systems[label]["vs_control"] = paired_difference(by_query[label], by_query[RERANKERS["control"]])
    return systems


# --- Informe ------------------------------------------------------------------------------


def _number(value: float) -> str:
    return f"{value:.4f}".replace(".", ",")


def _signed(value: float) -> str:
    return f"{value:+.4f}".replace(".", ",").replace("-", "−")


def _with_interval(found: dict[str, Any]) -> str:
    return f"{_number(found['mean'])} [{_number(found['ci95'][0])}; {_number(found['ci95'][1])}]"


def _difference(found: dict[str, Any] | None) -> str:
    if found is None:
        return ""
    return f"{_signed(found['diff'])} [{_signed(found['ci95'][0])}; {_signed(found['ci95'][1])}]"


def validation_ndcg(results_dir: Path) -> dict[str, float]:
    """nDCG@10 de cada sistema en validación, si está guardado, para ponerlo al lado."""
    path = results_dir / VALIDATION_FILE
    if not path.exists():
        return {}
    saved = json.loads(path.read_text(encoding="utf-8"))
    found = {name: metrics[NDCG] for name, metrics in saved["baselines"].items()}
    found.update({label: saved["rerankers"][variant][NDCG]["mean"] for variant, label in RERANKERS.items()})
    return found


def to_markdown(record: dict[str, Any]) -> str:
    info, validation = record["protocol"], record["validation_ndcg@10"]
    lines = [
        "# Recuperación: evaluación final en test",
        "",
        f"- Fecha: {record['date']}; commit `{record['commit']}`. Evaluación única: nada se ajustó después de ver estos números.",
        f"- {record['test_queries']} consultas de test, que no se habían usado antes. Rerankers entrenados con "
        f"{info['fit_queries']} consultas de ajuste de train y {len(info['seeds'])} semillas, las mismas que en validación.",
        "- nDCG@10 sobre los candidatos anotados (E=1, S=0,1, C=0,01, I=0) y recall@50 de productos exactos sobre todo el catálogo.",
        "- Entre corchetes, intervalo del 95 % por bootstrap de consultas; en los rerankers, sobre la media entre semillas "
        "de cada consulta. Las diferencias son consulta a consulta.",
        "- Los rerankers reordenan los 50 primeros del híbrido: su recall@50 es el del híbrido.",
        "",
        "| Sistema | nDCG@10 en test | Desv. entre semillas | recall@50 | Dif. con el híbrido | Dif. con el control | nDCG@10 en validación |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, found in record["systems"].items():
        spread = f"± {_number(found['std'])}" if "std" in found else ""
        role = f" ({ROLES[found['variant']]})" if found.get("variant") in ROLES else ""
        cells = [name + role, _with_interval(found[NDCG]), spread, _with_interval(found[RECALL])]
        cells += [_difference(found["vs_hybrid"]), _difference(found.get("vs_control"))]
        cells.append(_number(validation[name]) if name in validation else "")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


# --- Comando ------------------------------------------------------------------------------


def evaluate(data_dir: Path, seeds: int, device: str) -> dict[str, Any]:
    """Entrena con train como en la validación y mide en test."""
    data = load_dev_data(data_dir)
    dense = load_dense(data_dir)
    bm25 = BM25Retriever(product_texts(data.catalog, ALL_FIELDS))
    stage = first_stage(data.queries["query"].tolist(), bm25, dense)
    development = build_development(data, stage, dense.doc_embeddings, VALIDATION_QUERIES, device)
    queries = pd.read_parquet(data_dir / "queries_test.parquet").reset_index(drop=True)
    qrels = pd.read_parquet(data_dir / "qrels_test.parquet")
    test_stage = first_stage(queries["query"].tolist(), bm25, dense)
    test = make_eval_set(queries, qrels, data.catalog["product_id"].tolist(), test_stage)
    rerankers = {variant: reranker_ndcg(variant, seeds, development, test) for variant in RERANKERS}
    return {
        "test_queries": len(queries),
        "protocol": protocol(development, seeds, TrainConfig().epochs),
        "systems": summarize(baseline_scores(test), rerankers),
    }


def render(out_dir: Path) -> None:
    """Reescribe la tabla desde el resultado guardado, con la validación que haya ahora. No lee test."""
    record = json.loads((out_dir / f"{OUT_NAME}.json").read_text(encoding="utf-8"))
    record["validation_ndcg@10"] = validation_ndcg(out_dir)
    (out_dir / f"{OUT_NAME}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / f"{OUT_NAME}.md").write_text(to_markdown(record), encoding="utf-8")
    print(to_markdown(record))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluación final de la recuperación en test (una sola vez).")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--seeds", type=int, default=5, help="semillas de entrenamiento, como en validación")
    parser.add_argument("--out", type=Path, default=Path("results"))
    parser.add_argument("--force", action="store_true", help="repite la evaluación aunque ya exista el resultado")
    parser.add_argument("--render", action="store_true", help="solo reescribe la tabla desde el resultado guardado")
    args = parser.parse_args()
    if args.render:
        return render(args.out)
    target = args.out / f"{OUT_NAME}.json"
    if target.exists() and not args.force:
        sys.exit(f"{target} ya existe: la evaluación en test se hace una sola vez. Con --force se repite.")
    record = {"date": datetime.now().isoformat(timespec="seconds"), "commit": current_commit()}
    record.update(evaluate(args.data, args.seeds, default_device()))
    record["validation_ndcg@10"] = validation_ndcg(args.out)
    args.out.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    (args.out / f"{OUT_NAME}.md").write_text(to_markdown(record), encoding="utf-8")
    print(to_markdown(record))


if __name__ == "__main__":
    main()
