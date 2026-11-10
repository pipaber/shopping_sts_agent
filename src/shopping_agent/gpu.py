"""Medición de la memoria de GPU del proceso.

Se usa ``nvidia-smi`` y no ``torch.cuda`` porque no todos los modelos viven en
PyTorch: el LLM (llama.cpp) y Whisper (CTranslate2) reservan memoria por su cuenta.
"""

from __future__ import annotations

import os
import subprocess


def process_vram_mib() -> int | None:
    """Memoria de GPU que ocupa este proceso según ``nvidia-smi`` (``None`` si no se puede saber)."""
    try:
        output = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    for line in output.splitlines():
        pid, _, used = line.partition(",")
        if pid.strip() == str(os.getpid()):
            try:
                return int(used.strip())
            except ValueError:
                return None
    return None
