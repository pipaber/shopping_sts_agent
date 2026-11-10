"""Configuración local: variables de entorno leídas de un ``.env`` sin versionar.

El paquete carga el ``.env`` al importarse, antes que cualquier biblioteca de
modelos, para que variables como ``HF_HOME`` decidan dónde se descargan los pesos.
Las variables ya definidas en el entorno tienen prioridad sobre el archivo.
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_FILE = ".env"


def find_env_file(start: Path | None = None) -> Path | None:
    """Busca ``.env`` en el directorio de trabajo y sus ancestros, hasta la raíz del repo."""
    current = (start or Path.cwd()).resolve()
    for folder in (current, *current.parents):
        candidate = folder / ENV_FILE
        if candidate.is_file():
            return candidate
        if (folder / "pyproject.toml").is_file():
            return None
    return None


def parse_env(text: str) -> dict[str, str]:
    """Líneas ``CLAVE=valor``; admite comentarios, ``export`` y comillas."""
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def load_env(path: Path | None = None) -> dict[str, str]:
    """Aplica el ``.env`` al entorno sin pisar lo ya definido. Devuelve lo que añadió."""
    path = path or find_env_file()
    if path is None:
        return {}
    added = {}
    for key, value in parse_env(path.read_text(encoding="utf-8")).items():
        if key not in os.environ:
            os.environ[key] = value
            added[key] = value
    return added
