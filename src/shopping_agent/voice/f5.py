"""Síntesis de voz con F5-TTS y su ajuste al español (``jpgallegoar/F5-Spanish``).

Es el motor por defecto del agente (``SHOPPING_AGENT_TTS=f5``). Clona la voz de unos
pocos segundos de audio con su transcripción: aquí, turnos que el usuario grabó para
los escenarios (``audio/escenarios/<escenario>/<turno>.wav``, sin versionar) y el
texto de esos turnos en ``scenarios/evaluacion``. Qué turnos se usan lo dice
``SHOPPING_AGENT_VOICE_TURNS`` (``escenario/turno`` separados por comas); por defecto,
los dos que el usuario eligió de oído en ``experiments/comparacion_voz``.

F5-TTS decide de antemano cuánto dura el audio a partir de la longitud del texto, y
reparte el texto en esa duración. De ahí salen sus dos fallos conocidos, que este
módulo evita y además vigila:

- Si la transcripción de la referencia es más corta que lo que se oye («60 euros» por
  «sesenta euros»), el comienzo del texto nuevo cae dentro de la referencia y no se
  dice. Por eso la transcripción pasa por ``to_speech``, como las respuestas.
- A una frase muy corta le toca tan poco tiempo que sale en silencio. Por eso cada
  fragmento recibe un margen fijo, y el silencio de los bordes se recorta después.

Tras sintetizar cada fragmento se comprueba que el tiempo con voz alcanza para sus
sílabas; si no, se repite con otra semilla.

Los pesos de F5-Spanish figuran como CC-BY-NC-4.0 (uso no comercial) en los metadatos
de su repositorio, aunque el texto de su ficha dice CC0; el código de F5-TTS es MIT.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from shopping_agent.gpu import process_vram_mib
from shopping_agent.voice.audio import read_audio
from shopping_agent.voice.speech_text import split_for_tts, to_speech
from shopping_agent.voice.tts import (
    Synthesis,
    VoiceNotConfigured,
    join_chunks,
    pick_device,
    release_gpu_cache,
    resolve_speed,
    synthesize_chunks,
)

REPO = "jpgallegoar/F5-Spanish"
CHECKPOINT, VOCAB = "model_1200000.safetensors", "vocab.txt"  # el punto de control que nombra la ficha del modelo
ARCHITECTURE = "F5TTS_Base"
TURNS_ENV = "SHOPPING_AGENT_VOICE_TURNS"
DEFAULT_TURNS = ("01_compra_confirmada/01", "03_cambio_cantidad/01")  # los de la variante elegida de oído
RECORDINGS_DIR = Path("audio/escenarios")  # grabaciones del usuario; carpeta sin versionar
SCRIPTS_DIR = Path("scenarios/evaluacion")
AUDIO_SUFFIXES = (".wav", ".flac", ".ogg", ".mp3", ".m4a", ".aac", ".opus", ".webm")
DEFAULT_SPEED = 0.9
SAMPLE_RATE = 24000  # salida de F5-TTS
STEPS = 32  # pasos del muestreo (el valor por defecto de F5-TTS)
MAX_CHARS = 135  # referencia y fragmento juntos deben caber en los ~22 s con los que trabaja el modelo
MAX_REFERENCE_SECONDS = 12.0  # F5-TTS no admite más
EDGE_SECONDS = 0.6  # margen por fragmento para el silencio que el modelo deja en los bordes
KEPT_EDGE_SECONDS = 0.05  # silencio que se conserva a cada lado al recortar
MAX_ATTEMPTS = 3  # síntesis de un fragmento antes de quedarse con la que más habla tiene
MAX_SYLLABLES_PER_SECOND = 10.0  # nadie habla más rápido: por encima falta texto
FRAME_SECONDS = 0.02
SILENCE_DB = 35.0  # por debajo del tramo más fuerte: silencio
SILENCE_FLOOR = 0.002  # amplitud por debajo de la cual un tramo es silencio aunque sea el más fuerte


def resolve_turns(turns: tuple[str, ...] | None = None) -> tuple[str, ...]:
    """Los turnos grabados de los que se clona: el argumento, ``SHOPPING_AGENT_VOICE_TURNS`` o los dos por defecto."""
    if turns:
        return turns
    written = os.environ.get(TURNS_ENV, "")
    return tuple(part.strip() for part in written.split(",") if part.strip()) or DEFAULT_TURNS


def turn_recording(turn: str) -> tuple[Path, str]:
    """La grabación de un turno (``escenario/número``) y lo que el usuario dice en él."""
    scenario, _, number = turn.partition("/")
    script = SCRIPTS_DIR / f"{scenario}.json"
    found = [path for suffix in AUDIO_SUFFIXES if (path := RECORDINGS_DIR / scenario / f"{number}{suffix}").is_file()]
    if not (number.isdigit() and script.is_file() and found):
        raise VoiceNotConfigured(
            f"Falta el turno «{turn}» para clonar la voz: hace falta su grabación en {RECORDINGS_DIR / scenario} y su guion "
            f"en {script}. Elige otros turnos con {TURNS_ENV} (escenario/turno, separados por comas)."
        )
    says = [step["say"] for step in json.loads(script.read_text(encoding="utf-8"))["steps"] if "say" in step]
    if int(number) > len(says):
        raise VoiceNotConfigured(f"El escenario {scenario} solo tiene {len(says)} turnos: no existe «{turn}» ({TURNS_ENV}).")
    return found[0], says[int(number) - 1]


def speech_frames(audio: np.ndarray, rate: int) -> np.ndarray:
    """Qué tramos de 20 ms tienen voz: los que no quedan 35 dB por debajo del más fuerte
    ni por debajo de un suelo fijo (así un audio sin habla no cuenta como voz)."""
    size = int(rate * FRAME_SECONDS)
    frames = audio[: len(audio) // size * size].reshape(-1, size)
    if not len(frames):
        return np.zeros(0, dtype=bool)
    energy = np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1))
    return energy > max(SILENCE_FLOOR, energy.max() * 10 ** (-SILENCE_DB / 20))


def speech_seconds(audio: np.ndarray, rate: int) -> float:
    return float(speech_frames(audio, rate).sum() * FRAME_SECONDS)


def trim_silence(audio: np.ndarray, rate: int) -> np.ndarray:
    """Quita el silencio del principio y del final, dejando un margen corto."""
    voiced = np.flatnonzero(speech_frames(audio, rate))
    if not len(voiced):
        return audio
    size, margin = int(rate * FRAME_SECONDS), int(rate * KEPT_EDGE_SECONDS)
    return audio[max(0, voiced[0] * size - margin) : (voiced[-1] + 1) * size + margin]


def count_syllables(text: str) -> int:
    """Sílabas aproximadas: grupos de vocales seguidas."""
    return len(re.findall(r"[aeiouáéíóúü]+", text.lower()))


def lost_text(audio: np.ndarray, rate: int, text: str) -> bool:
    """¿Falta texto en el audio? Sí cuando el tiempo con voz no alcanza para decir
    sus sílabas ni hablando muy rápido (un fragmento en silencio no tiene ninguno)."""
    return speech_seconds(audio, rate) * MAX_SYLLABLES_PER_SECOND < count_syllables(text)


def read_reference(turns: tuple[str, ...]) -> tuple[np.ndarray, str, list[Path]]:
    """El audio del que se clona (los turnos seguidos), su transcripción y sus archivos."""
    recordings = [turn_recording(turn) for turn in turns]
    pieces = [read_audio(path, SAMPLE_RATE)[0] for path, _ in recordings]
    audio = trim_silence(join_chunks(pieces, SAMPLE_RATE), SAMPLE_RATE)
    if len(audio) > MAX_REFERENCE_SECONDS * SAMPLE_RATE:
        raise VoiceNotConfigured(
            f"Los turnos de {TURNS_ENV} suman {len(audio) / SAMPLE_RATE:.1f} s y F5-TTS clona de {MAX_REFERENCE_SECONDS:.0f} s como mucho: elige menos turnos."
        )
    # Deletreada, como las respuestas: con cifras el texto queda más corto que el audio y F5 se come el comienzo de lo que dice después.
    text = to_speech(" ".join(text for _, text in recordings))
    return audio, text, [path for path, _ in recordings]


def _load_model(device: str) -> Any:
    from f5_tts.api import F5TTS
    from huggingface_hub import hf_hub_download

    with contextlib.redirect_stdout(sys.stderr):  # F5-TTS anuncia por la salida estándar lo que carga
        checkpoint, vocab = hf_hub_download(REPO, CHECKPOINT), hf_hub_download(REPO, VOCAB)
        return F5TTS(model=ARCHITECTURE, ckpt_file=checkpoint, vocab_file=vocab, device=device)


class F5SpanishTTS:
    """F5-TTS en español con la voz clonada de turnos grabados por el usuario."""

    name = "F5-Spanish"
    sample_rate = SAMPLE_RATE

    def __init__(
        self,
        turns: tuple[str, ...] | None = None,
        *,
        device: str = "auto",
        seed: int = 0,
        max_chars: int = MAX_CHARS,
        speed: float | None = None,
    ) -> None:
        self.turns = resolve_turns(turns)
        self.speed = resolve_speed(speed, DEFAULT_SPEED)
        self.seed = seed
        self.max_chars = max_chars
        self.device = pick_device(device)
        self.reference_audio, self.reference_text, self.references = read_reference(self.turns)

        vram_before = process_vram_mib() or 0
        start = time.perf_counter()
        self.model = _load_model(self.device)
        self._generate("Hola, ¿qué tal?", seed)  # deja fuera del primer turno la inicialización perezosa
        release_gpu_cache(self.device)
        self.load_seconds = time.perf_counter() - start
        vram_after = process_vram_mib()
        self.vram_mib = None if vram_after is None else vram_after - vram_before

    @property
    def voice(self) -> dict[str, Any]:
        """De dónde sale la voz, para dejarlo escrito en los resultados."""
        return {"references": [str(path) for path in self.references], "speaker": None, "speed": self.speed}

    def _total_seconds(self, chunk: str) -> float:
        """Duración que se pide a F5-TTS (referencia más fragmento): el fragmento, al
        ritmo de la referencia en segundos por byte de texto —como lo estima F5-TTS—
        entre la velocidad, más el margen de los bordes."""
        reference_seconds = len(self.reference_audio) / self.sample_rate
        pace = reference_seconds / len(self.reference_text.encode("utf-8"))
        return reference_seconds + len(chunk.encode("utf-8")) * pace / self.speed + EDGE_SECONDS

    def _generate(self, chunk: str, seed: int) -> np.ndarray:
        import torch
        from f5_tts.infer.utils_infer import infer_batch_process

        torch.manual_seed(seed)  # muestreo aleatorio: misma entrada, misma salida
        reference = (torch.from_numpy(self.reference_audio).unsqueeze(0), self.sample_rate)
        model, vocoder = self.model.ema_model, self.model.vocoder
        made = infer_batch_process(
            reference, self.reference_text, [chunk], model, vocoder, progress=None, nfe_step=STEPS,
            fix_duration=self._total_seconds(chunk), device=self.device,
        )  # fmt: skip
        wave, _, _ = next(made)
        return trim_silence(np.asarray(wave, dtype=np.float32).reshape(-1), self.sample_rate)

    def _generate_checked(self, chunk: str) -> tuple[np.ndarray, int]:
        """Sintetiza un fragmento; si le falta texto lo reintenta con otra semilla y se
        queda con el intento que más habla tiene. Devuelve el audio y los reintentos."""
        attempts: list[np.ndarray] = []
        for attempt in range(MAX_ATTEMPTS):
            attempts.append(self._generate(chunk, self.seed + attempt))
            if not lost_text(attempts[-1], self.sample_rate, chunk):
                return attempts[-1], attempt
        return max(attempts, key=lambda audio: speech_seconds(audio, self.sample_rate)), MAX_ATTEMPTS - 1

    def synthesize(self, text: str) -> Synthesis:
        """Sintetiza un texto ya preparado para voz (véase ``speech_text.to_speech``)."""
        result = synthesize_chunks(split_for_tts(text, self.max_chars), self._generate_checked, self.sample_rate)
        release_gpu_cache(self.device)
        return result
