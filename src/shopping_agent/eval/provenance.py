"""De qué versión del código sale un resultado."""

from __future__ import annotations

import subprocess


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout.strip()


def current_commit() -> str:
    """El commit en curso; con ``+cambios`` si hay archivos versionados sin confirmar.

    No cuentan los de ``results/``: los reescribe cada corrida y no cambian el código."""
    commit = _git("rev-parse", "--short", "HEAD") or "desconocido"
    dirty = _git("status", "--porcelain", "--untracked-files=no", "--", ".", ":(exclude,top)results")
    return f"{commit}+cambios" if dirty else commit
