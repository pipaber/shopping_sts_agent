"""Limpieza del texto de producto y tokenización para la búsqueda léxica."""

from __future__ import annotations

import html
import re
import unicodedata

import pandas as pd

_TAG = re.compile(r"<[^>]+>")
_BROKEN_ENTITY = re.compile(r"&\s*#?\s*\w{1,8}\s*;")  # restos como "& # xFFFD;"
_SPACE = re.compile(r"\s+")
_TOKEN = re.compile(r"[a-z0-9]+")

STOPWORDS = frozenset(
    "a al con de del el en es la las lo los o para por que se su sus un una unas unos y".split()
)

# Campos que forman el documento de cada producto, en orden de importancia.
SHORT_FIELDS = ["product_title", "product_brand", "product_color", "product_bullet_point"]
ALL_FIELDS = [*SHORT_FIELDS, "product_description"]


def clean(value: object) -> str:
    """Quita HTML, entidades rotas y espacios sobrantes. Los nulos quedan vacíos."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = html.unescape(str(value))
    text = _TAG.sub(" ", text)
    text = _BROKEN_ENTITY.sub(" ", text).replace("�", " ")
    return _SPACE.sub(" ", text).strip()


def product_texts(catalog: pd.DataFrame, fields: list[str]) -> list[str]:
    """Un documento por producto con los campos indicados."""
    columns = [catalog[field].map(clean) for field in fields]
    return [" . ".join(part for part in parts if part) for parts in zip(*columns, strict=True)]


def tokenize(text: str) -> list[str]:
    """Minúsculas, sin acentos, solo letras y números, sin palabras vacías."""
    folded = unicodedata.normalize("NFKD", text.lower())
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    return [token for token in _TOKEN.findall(folded) if token not in STOPWORDS]
