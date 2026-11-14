"""Lo común a los scripts de la comparación de voces: frases, grabaciones y guardado.

Solo usa la biblioteca estándar, NumPy, soundfile y PyTorch, para que funcione igual
en el entorno del proyecto y en los entornos temporales de los modelos nuevos.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
PHRASES = HERE / "frases.txt"
OUT = Path("audio/comparacion_voz")  # carpeta sin versionar: la voz del usuario no entra en git
REFERENCE = Path("audio/referencia/referencia.wav")
PREVIOUS_REFERENCE = Path("audio/referencia/referencia_anterior.wav")
RECORDINGS = Path("audio/escenarios")
SCRIPTS = Path("scenarios/evaluacion")
REFERENCES = OUT / "_referencias"  # recortes de las grabaciones de clonar, con su texto
# Grabaciones reales para clonar (además de las dos de referencia) y grabaciones que
# solo sirven para medir: ninguna variante las usa como referencia.
CLONE_SCENARIOS = ("01_compra_confirmada", "02_pedido_ambiguo", "03_cambio_cantidad")
MEASURE_SCENARIOS = ("04_sin_existencias", "05_correccion_transcripcion", "06_cambio_stock_confirmacion_repetida")
SEED = 0  # una sola semilla por variante
MAX_CHARS = 200  # como el agente: fragmentos por debajo del límite de XTTS-v2
PAUSE_SECONDS = 0.25

Synthesize = Callable[[str], np.ndarray]


def phrases() -> list[str]:
    return [line.strip() for line in PHRASES.read_text(encoding="utf-8").splitlines() if line.strip()]


def recordings(scenarios: tuple[str, ...]) -> list[Path]:
    return [path for name in scenarios for path in sorted((RECORDINGS / name).glob("*.wav"))]


def said(scenario: str) -> list[str]:
    """Lo que el usuario dice en cada turno grabado de un escenario."""
    steps = json.loads((SCRIPTS / f"{scenario}.json").read_text(encoding="utf-8"))["steps"]
    return [step["say"] for step in steps if "say" in step]


def with_text(scenarios: tuple[str, ...]) -> list[tuple[Path, str]]:
    return [(path, text) for name in scenarios for path, text in zip(recordings((name,)), said(name), strict=True)]


def _pack(parts: list[str], max_chars: int) -> list[str]:
    """Junta trozos seguidos mientras quepan en ``max_chars``."""
    chunks: list[str] = []
    for part in parts:
        if chunks and len(chunks[-1]) + 1 + len(part) <= max_chars:
            chunks[-1] = f"{chunks[-1]} {part}"
        else:
            chunks.append(part)
    return chunks


def split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Parte un texto largo por frases (y por comas si una frase no cabe)."""
    sentences = re.split(r"(?<=[.?!:;])\s+", text.strip())
    parts = [piece for sentence in sentences for piece in _split_long(sentence, max_chars)]
    return _pack(parts, max_chars)


def _split_long(sentence: str, max_chars: int) -> list[str]:
    return [sentence] if len(sentence) <= max_chars else _pack(re.split(r"(?<=,)\s+", sentence), max_chars)


def join(pieces: list[np.ndarray], rate: int) -> np.ndarray:
    pause = np.zeros(int(rate * PAUSE_SECONDS), dtype=np.float32)
    joined = [pieces[0]]
    for piece in pieces[1:]:
        joined += [pause, piece]
    return np.concatenate(joined).astype(np.float32)


def process_vram_mib() -> int | None:
    """Memoria de GPU de este proceso según ``nvidia-smi``."""
    query = ["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"]
    try:
        rows = subprocess.run(query, capture_output=True, text=True, check=True).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        return None
    mine = [int(row.split(",")[1]) for row in rows if row.split(",")[0].strip() == str(os.getpid())]
    return mine[0] if mine else None


def _speak(text: str, synthesize: Synthesize, path: Path, rate: int) -> dict[str, Any]:
    start = time.perf_counter()
    audio = np.asarray(synthesize(text), dtype=np.float32).reshape(-1)
    seconds = time.perf_counter() - start
    sf.write(path, audio, rate)
    return {"file": path.name, "text": text, "synth_seconds": seconds, "audio_seconds": len(audio) / rate}


def save_variant(name: str, description: str, rate: int, synthesize: Synthesize, settings: dict[str, Any]) -> Path:
    """Sintetiza todas las frases con una variante y deja los audios y lo medido al
    generarlos (tiempo de síntesis y memoria de GPU) en ``audio/comparacion_voz/<variante>``."""
    import torch

    folder = OUT / name
    folder.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(SEED)
    torch.cuda.reset_peak_memory_stats()
    cases = [_speak(text, synthesize, folder / f"{i:02d}.wav", rate) for i, text in enumerate(phrases(), 1)]
    meta = {"variant": name, "description": description, "seed": SEED, "sample_rate": rate, "settings": settings}
    meta["torch_peak_mib"] = round(torch.cuda.max_memory_allocated() / 2**20)
    meta["process_vram_mib"] = process_vram_mib()
    meta["phrases"] = cases
    (folder / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    total = sum(case["synth_seconds"] for case in cases)
    print(f"[{name}: {len(cases)} frases en {total:.1f} s, {meta['process_vram_mib']} MiB]", flush=True)
    return folder
