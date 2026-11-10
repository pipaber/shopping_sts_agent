"""Búsqueda en el catálogo para el agente: recuperación híbrida y evidencia textual.

Envuelve los recuperadores existentes (BM25 + denso con fusión RRF). Solo lee el
catálogo: las etiquetas de relevancia de ESCI no se cargan aquí ni en ningún
módulo del agente.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd

from shopping_agent.retrieval.retrievers import DEFAULT_DENSE_MODEL, BM25Retriever, DenseRetriever, rrf
from shopping_agent.retrieval.text import ALL_FIELDS, SHORT_FIELDS, clean, product_texts

DEFAULT_DATA_DIR = Path("datasets/processed")

# Campos del catálogo que forman la evidencia de un producto.
EVIDENCE_FIELDS = {
    "title": "product_title",
    "brand": "product_brand",
    "color": "product_color",
    "bullets": "product_bullet_point",
    "description": "product_description",
}


class Scorer(Protocol):
    def score(self, queries: list[str]) -> np.ndarray: ...


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:") + "…"


class CatalogSearch:
    """Ordena el catálogo para una consulta y devuelve los campos tal cual están."""

    def __init__(self, catalog: pd.DataFrame, bm25: Scorer, dense: Scorer | None = None) -> None:
        self.catalog = catalog.reset_index(drop=True)
        self.product_ids: list[str] = self.catalog["product_id"].tolist()
        self._row = {product_id: row for row, product_id in enumerate(self.product_ids)}
        self.bm25 = bm25
        self.dense = dense

    @classmethod
    def from_catalog(cls, catalog: pd.DataFrame, dense: Scorer | None = None) -> CatalogSearch:
        return cls(catalog, BM25Retriever(product_texts(catalog, ALL_FIELDS)), dense)

    @classmethod
    def from_dir(
        cls, data_dir: Path = DEFAULT_DATA_DIR, model_name: str = DEFAULT_DENSE_MODEL
    ) -> CatalogSearch:
        """Misma configuración que la evaluación: BM25 con todo el texto y denso con
        los campos cortos, reutilizando los embeddings ya calculados."""
        catalog = pd.read_parquet(data_dir / "catalog.parquet")
        cache = data_dir / f"emb_{model_name.replace('/', '__')}.npy"
        dense = DenseRetriever(product_texts(catalog, SHORT_FIELDS), model_name, cache_path=cache)
        return cls.from_catalog(catalog, dense)

    def __contains__(self, product_id: object) -> bool:
        return product_id in self._row

    def rank(self, query: str, top: int = 50) -> list[str]:
        """Identificadores de los ``top`` productos por fusión RRF de BM25 y denso."""
        if not query.strip():
            return []
        lexical = self.bm25.score([query])
        if self.dense is None:
            # Sin modelo denso (pruebas): solo cuentan los productos con algún término.
            order = np.argsort(-lexical[0], kind="stable")[:top]
            return [self.product_ids[row] for row in order if lexical[0, row] > 0]
        fused = rrf([lexical, self.dense.score([query])])[0]
        return [self.product_ids[row] for row in np.argsort(-fused, kind="stable")[:top]]

    def evidence(self, product_id: str, bullets_chars: int = 240, description_chars: int = 200) -> dict[str, Any]:
        """Texto del catálogo para un producto, recortado para caber en el contexto.

        Los campos que el catálogo no trae quedan en ``None`` (desconocidos).
        """
        record = self.catalog.iloc[self._row[product_id]]
        fields = {name: clean(record[column]) or None for name, column in EVIDENCE_FIELDS.items()}
        if fields["bullets"]:
            fields["bullets"] = _truncate(fields["bullets"], bullets_chars)
        if fields["description"]:
            fields["description"] = _truncate(fields["description"], description_chars)
        return {"product_id": product_id, **fields, "title": fields["title"] or product_id}

    def title(self, product_id: str) -> str:
        if product_id not in self._row:
            return product_id
        return clean(self.catalog.at[self._row[product_id], "product_title"]) or product_id
