"""Prepara lo que comparten las variantes: las frases, un fragmento corto de la
grabación de referencia con su transcripción (lo piden los modelos que clonan con una
muestra de pocos segundos) y una copia de la voz real para escucharla al lado.

Todo queda en ``audio/comparacion_voz`` (sin versionar). Entorno del proyecto:

    PYTHONPATH=src python experiments/comparacion_voz/preparar.py
"""

from __future__ import annotations

import itertools
import shutil
from pathlib import Path

import librosa
import numpy as np
from comun import CLONE_SCENARIOS, MEASURE_SCENARIOS, OUT, PHRASES, REFERENCE, REFERENCES, join, recordings, with_text

from shopping_agent.voice.asr import WhisperASR
from shopping_agent.voice.audio import read_audio, write_wav

SHORT_WINDOW = (6.0, 11.0)  # segundos: dónde buscar la pausa en la que cortar
SILENCE_DB = 35
SHORT_TURNS = ("01_compra_confirmada/01.wav", "03_cambio_cantidad/01.wav")  # 11,5 s entre los dos
REAL = OUT / "voz_real"


def cut_at_pause(audio: np.ndarray, rate: int) -> np.ndarray:
    """El comienzo de la grabación hasta su pausa más larga dentro de ``SHORT_WINDOW``."""
    spans = librosa.effects.split(audio, top_db=SILENCE_DB)
    low, high = (int(seconds * rate) for seconds in SHORT_WINDOW)
    pauses = [(start - end, end) for (_, end), (start, _) in itertools.pairwise(spans) if low <= end <= high]
    _, end = max(pauses)
    return audio[: end + int(0.15 * rate)]


def join_turns(name: str, turns: list[tuple[Path, str]]) -> None:
    """Una referencia hecha de turnos reales seguidos, con el texto de lo que dicen."""
    audios = [read_audio(path) for path, _ in turns]
    write_wav(REFERENCES / f"{name}.wav", join([audio for audio, _ in audios], audios[0][1]), audios[0][1])
    (REFERENCES / f"{name}.txt").write_text(" ".join(text for _, text in turns) + "\n", encoding="utf-8")


def main() -> None:
    REFERENCES.mkdir(parents=True, exist_ok=True)
    REAL.mkdir(parents=True, exist_ok=True)
    shutil.copy(PHRASES, OUT / "frases.txt")
    audio, rate = read_audio(REFERENCE)
    short = write_wav(REFERENCES / "referencia_corta.wav", cut_at_pause(audio, rate), rate)
    text = WhisperASR().transcribe(short).text
    (REFERENCES / "referencia_corta.txt").write_text(text + "\n", encoding="utf-8")
    turns = with_text(CLONE_SCENARIOS)
    join_turns("turnos", turns)
    join_turns("turnos_cortos", [pair for pair in turns if str(pair[0]).endswith(SHORT_TURNS)])
    for path in recordings(MEASURE_SCENARIOS):
        shutil.copy(path, REAL / f"{path.parent.name[:2]}_{path.name}")
    print(f"[referencia corta: {len(cut_at_pause(audio, rate)) / rate:.1f} s, {len(text.split())} palabras]")


if __name__ == "__main__":
    main()
