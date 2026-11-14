"""Variantes de XTTS-v2 para la comparación de voces (entorno del proyecto).

A es la voz del agente tal como está. Las B cambian solo de qué grabaciones sale la
voz y cuánto audio condiciona el ritmo; el modelo y el troceado del texto son los del
agente (``XttsTTS``), que no se modifica.

    PYTHONPATH=src python experiments/comparacion_voz/xtts_variantes.py [variante ...]
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from comun import CLONE_SCENARIOS, PREVIOUS_REFERENCE, REFERENCE, recordings, save_variant

from shopping_agent.voice.tts import XttsTTS

TURNS = recordings(CLONE_SCENARIOS)
# nombre: (descripción, grabaciones, argumentos de get_conditioning_latents, velocidad, temperatura)
VARIANTS: dict[str, tuple[str, list[Path], dict[str, int], float, float]] = {
    "A_xtts_actual": ("XTTS-v2 como está: referencia nueva, ritmo de 6 s, velocidad 1,10", [REFERENCE], {}, 1.10, 0.65),
    "B1_xtts_ritmo30": (
        "XTTS-v2, referencia nueva, ritmo condicionado con 30 s, velocidad 1,0",
        [REFERENCE],
        {"gpt_cond_len": 30},
        1.0,
        0.65,
    ),
    "B2_xtts_varias": (
        "XTTS-v2, timbre promediado de las dos referencias y 12 turnos reales; ritmo como B1 (30 s de la referencia nueva)",
        [REFERENCE, PREVIOUS_REFERENCE, *TURNS],
        {"gpt_cond_len": 30, "max_ref_length": 60},
        1.0,
        0.65,
    ),
    "B3_xtts_varias_t075": (
        "Como B2 con temperatura 0,75 (la de XTTS-v2 por defecto)",
        [REFERENCE, PREVIOUS_REFERENCE, *TURNS],
        {"gpt_cond_len": 30, "max_ref_length": 60},
        1.0,
        0.75,
    ),
    "B5_xtts_todo": (
        "XTTS-v2, timbre y ritmo de todas las grabaciones de clonar (113 s), velocidad 1,0",
        [REFERENCE, PREVIOUS_REFERENCE, *TURNS],
        {"gpt_cond_len": 120, "max_ref_length": 60},
        1.0,
        0.65,
    ),
    "B4_xtts_turnos": (
        "XTTS-v2 solo con los 12 turnos reales (sin las grabaciones de referencia), velocidad 1,0",
        TURNS,
        {"gpt_cond_len": 30, "max_ref_length": 60},
        1.0,
        0.65,
    ),
}


def use_voice(tts: XttsTTS, audios: list[Path], conditioning: dict[str, int], speed: float, temperature: float) -> None:
    """Cambia la voz del sintetizador ya cargado sin tocar su código."""
    paths = [str(path) for path in audios]
    tts.gpt_cond_latent, tts.speaker_embedding = tts.model.get_conditioning_latents(audio_path=paths, **conditioning)
    tts.speed, tts.temperature = speed, temperature


def main() -> None:
    tts = XttsTTS(REFERENCE)
    chosen = sys.argv[1:] or list(VARIANTS)
    for name in chosen:
        description, audios, conditioning, speed, temperature = VARIANTS[name]
        use_voice(tts, audios, conditioning, speed, temperature)
        settings: dict[str, Any] = {"references": [str(path) for path in audios], "conditioning": conditioning}
        settings |= {"speed": speed, "temperature": temperature, "load_seconds": tts.load_seconds}
        save_variant(name, description, tts.sample_rate, lambda text: tts.synthesize(text).audio, settings)


if __name__ == "__main__":
    main()
