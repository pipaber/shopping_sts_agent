"""Variantes D y E: Chatterbox multilingüe (Resemble AI, MIT) y su conversión de voz.

D1 es el modelo multilingüe V3 con el idioma «es»; D2, el ajuste al español de
Latinoamérica; E pasa los audios de otra variante al timbre del usuario (conversión de
voz). Corre en un entorno temporal propio (Chatterbox instalado desde su repositorio):

    python experiments/comparacion_voz/chatterbox_es.py D1_chatterbox_v3
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from comun import OUT, REFERENCE, REFERENCES, join, save_variant, split_text
from huggingface_hub import hf_hub_download

BASE = "ResembleAI/chatterbox"
LATAM = "ResembleAI/Chatterbox-Multilingual-es-mx-latam"
SHARED = ("ve.pt", "conds.pt", "grapheme_mtl_merged_expanded_v1.json", "Cangjie5_TC.json")
CONVERTED = "A_xtts_actual"  # la variante cuyos audios convierte E
SETTINGS = {"exaggeration": 0.5, "cfg_weight": 0.5, "temperature": 0.8}  # los valores por defecto


FIXED_TABLES = {"tokenizer._mel_filters", "tokenizer.window"}  # no se aprenden: el modelo las calcula al crearse


def latam_folder(folder: Path) -> Path:
    """Junta en una carpeta lo que el cargador espera: lo común del modelo base y el
    T3 del ajuste a Latinoamérica."""
    folder.mkdir(parents=True, exist_ok=True)
    files = {name: hf_hub_download(BASE, name) for name in (*SHARED, "s3gen.pt")}
    files["t3_es_mx_latam.safetensors"] = hf_hub_download(LATAM, "t3_es_mx_latam.safetensors")
    for name, source in files.items():
        if not (folder / name).is_symlink():
            (folder / name).symlink_to(source)
    return folder


def load_latam(folder: Path) -> Any:
    """El ajuste a Latinoamérica: su T3 y, encima del decodificador base, los pesos del
    decodificador V3 que publica (al archivo solo le faltan dos tablas fijas)."""
    import torch
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    model = ChatterboxMultilingualTTS.from_local(latam_folder(folder), "cuda", t3_model="t3_es_mx_latam.safetensors")
    decoder = torch.load(hf_hub_download(LATAM, "s3gen_v3.pt"), map_location="cuda", weights_only=True)
    missing, unexpected = model.s3gen.load_state_dict(decoder, strict=False)
    if set(missing) - FIXED_TABLES or unexpected:
        raise RuntimeError(f"El decodificador V3 no encaja: faltan {missing}, sobran {unexpected}")
    return model


def load_tts(variant: str) -> Any:
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    if variant == "D1_chatterbox_v3":
        return ChatterboxMultilingualTTS.from_pretrained(device="cuda", t3_model="v3")
    return load_latam(Path(sys.argv[2]))


def speak(variant: str, description: str) -> None:
    reference = REFERENCES / "turnos.wav" if variant.endswith("_turnos") else REFERENCE
    start = time.perf_counter()
    model = load_tts(variant)
    model.prepare_conditionals(str(reference), exaggeration=SETTINGS["exaggeration"])
    load_seconds = time.perf_counter() - start

    def synthesize(text: str) -> np.ndarray:
        pieces = [model.generate(chunk, language_id="es", **SETTINGS) for chunk in split_text(text)]
        return join([piece.squeeze(0).cpu().numpy() for piece in pieces], model.sr)

    synthesize("Hola, ¿qué tal?")  # deja fuera de la medida la inicialización perezosa
    settings = {**SETTINGS, "references": [str(reference)], "load_seconds": load_seconds}
    save_variant(variant, description, model.sr, synthesize, settings)


def convert(variant: str, description: str) -> None:
    """E: cada audio de ``CONVERTED`` pasado al timbre de la grabación de referencia."""
    from chatterbox.vc import ChatterboxVC

    start = time.perf_counter()
    model = ChatterboxVC.from_pretrained("cuda")
    model.set_target_voice(str(REFERENCE))
    load_seconds = time.perf_counter() - start
    sources = iter(sorted((OUT / CONVERTED).glob("*.wav")))

    def synthesize(_: str) -> np.ndarray:
        return model.generate(str(next(sources))).squeeze(0).cpu().numpy()

    settings = {"converted": CONVERTED, "references": [str(REFERENCE)], "load_seconds": load_seconds}
    save_variant(variant, description, model.sr, synthesize, settings)


VARIANTS = {
    "D1_chatterbox_v3": (speak, "Chatterbox multilingüe V3 (idioma «es»), referencia nueva"),
    "D2_chatterbox_latam": (speak, "Chatterbox, ajuste al español de Latinoamérica, referencia nueva"),
    "D3_chatterbox_latam_turnos": (speak, "Como D2 clonando de los 12 turnos reales seguidos (43 s) en vez de la grabación de referencia"),
    "E_xtts_conversion": (
        convert,
        f"Conversión de voz de Chatterbox sobre los audios de {CONVERTED} (su tiempo se suma al de esa variante)",
    ),
}


def main() -> None:
    run, description = VARIANTS[sys.argv[1]]
    run(sys.argv[1], description)


if __name__ == "__main__":
    main()
