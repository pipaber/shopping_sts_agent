"""Variante C: F5-TTS con el ajuste al español ``jpgallegoar/F5-Spanish``.

Clona con un audio corto y su transcripción: usa el fragmento que deja ``preparar.py``.
Corre en un entorno temporal propio (``pip install f5-tts``), fuera del proyecto:

    python experiments/comparacion_voz/f5_spanish.py C_f5_spanish
"""

from __future__ import annotations

import sys
import time

import numpy as np
from comun import REFERENCES, SEED, save_variant
from f5_tts.api import F5TTS
from huggingface_hub import hf_hub_download

REPO = "jpgallegoar/F5-Spanish"  # pesos CC-BY-NC-4.0 (uso no comercial); código de F5-TTS, MIT
CHECKPOINT = "model_1200000.safetensors"  # el que nombra la ficha del modelo
# variante: (recorte de referencia, descripción)
VARIANTS = {
    "C_f5_spanish": ("referencia_corta", "F5-TTS con el ajuste al español (F5-Spanish), 7 s de la referencia nueva y su transcripción"),
    "C2_f5_turnos": ("turnos_cortos", "F5-Spanish clonando de dos turnos reales (11,5 s) en vez de la grabación de referencia"),
}
STEPS = 32  # pasos del muestreo (el valor por defecto de F5-TTS)


def load() -> tuple[F5TTS, float]:
    start = time.perf_counter()
    checkpoint, vocab = (hf_hub_download(REPO, CHECKPOINT), hf_hub_download(REPO, "vocab.txt"))
    model = F5TTS(model="F5TTS_Base", ckpt_file=checkpoint, vocab_file=vocab)
    return model, time.perf_counter() - start


def main() -> None:
    variant = sys.argv[1]
    reference = REFERENCES / f"{VARIANTS[variant][0]}.wav"
    model, load_seconds = load()
    reference_text = reference.with_suffix(".txt").read_text(encoding="utf-8").strip()

    def synthesize(text: str) -> np.ndarray:
        audio, _, _ = model.infer(str(reference), reference_text, text, nfe_step=STEPS, seed=SEED, show_info=lambda *_: None)
        return audio

    synthesize("Hola, ¿qué tal?")  # deja fuera de la medida la inicialización perezosa
    settings = {"model": f"{REPO}/{CHECKPOINT}", "references": [str(reference)], "steps": STEPS, "speed": 1.0}
    settings["load_seconds"] = load_seconds
    save_variant(variant, VARIANTS[variant][1], model.target_sample_rate, synthesize, settings)


if __name__ == "__main__":
    main()
