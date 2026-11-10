"""Medición de la memoria de GPU del proceso.

Se usa ``nvidia-smi`` y no ``torch.cuda`` porque no todos los modelos viven en
PyTorch: el LLM (llama.cpp) y Whisper (CTranslate2) reservan memoria por su cuenta.
"""

from __future__ import annotations

import os
import subprocess


QUERY = ["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"]


def process_vram_mib() -> int | None:
    """Memoria de GPU que ocupa este proceso según ``nvidia-smi`` (``None`` si no se puede saber)."""
    try:
        output = subprocess.run(QUERY, capture_output=True, text=True, timeout=10, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    used = {pid.strip(): memory.strip() for pid, _, memory in (line.partition(",") for line in output.splitlines())}
    memory = used.get(str(os.getpid()), "")
    return int(memory) if memory.isdigit() else None
