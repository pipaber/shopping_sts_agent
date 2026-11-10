"""Reconocimiento de voz con Whisper (``faster-whisper``), en español.

Uso::

    python -m shopping_agent.voice.asr grabacion.wav

El idioma se fija en español: no se gasta tiempo en detectarlo y no se cuelan
transcripciones en otro idioma con audios cortos ("sí", "vale").
"""

from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from shopping_agent.gpu import process_vram_mib
from shopping_agent.voice.audio import duration, read_audio, resample, to_mono

DEFAULT_MODEL = "large-v3-turbo"
MODEL_ENV = "SHOPPING_AGENT_ASR_MODEL"
SAMPLE_RATE = 16000  # la que espera Whisper


@dataclass
class Transcription:
    text: str
    seconds: float  # tiempo de transcripción, sin la carga del modelo
    audio_seconds: float
    language: str = "es"
    segments: list[dict[str, Any]] = field(default_factory=list)


class SpeechRecognizer(Protocol):
    """Lo que el turno por voz necesita de un ASR (permite sustituirlo en las pruebas)."""

    def transcribe(self, audio: str | Path | np.ndarray, sample_rate: int = SAMPLE_RATE) -> Transcription: ...


def clean_transcript(text: str) -> str:
    return " ".join(text.split())


class WhisperASR:
    """Whisper large-v3-turbo en GPU (``float16``) o, si no hay GPU, en CPU (``int8``).

    ``vad_filter`` descarta los tramos sin voz antes de transcribir. Sin él, Whisper
    inventa frases con silencio o ruido ("Gracias por ver el vídeo"), y en un agente
    que compra eso no puede llegar como si lo hubiera dicho el usuario.
    """

    def __init__(
        self,
        model: str | None = None,
        *,
        device: str = "auto",
        compute_type: str | None = None,
        language: str = "es",
        beam_size: int = 5,
        initial_prompt: str | None = None,
        vad_filter: bool = True,
    ) -> None:
        import ctranslate2
        from faster_whisper import WhisperModel

        self.model_name = model or os.environ.get(MODEL_ENV) or DEFAULT_MODEL
        if device == "auto":
            device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        self.device = device
        self.compute_type = compute_type or ("float16" if device == "cuda" else "int8")
        self.language = language
        self.beam_size = beam_size
        self.initial_prompt = initial_prompt
        self.vad_filter = vad_filter

        vram_before = process_vram_mib() or 0
        start = time.perf_counter()
        self.model = WhisperModel(self.model_name, device=device, compute_type=self.compute_type)
        # Una pasada en vacío deja reservada la memoria de trabajo y fuera de la
        # medida del primer turno la inicialización perezosa de CUDA.
        self._run(np.zeros(SAMPLE_RATE, dtype=np.float32))
        self.load_seconds = time.perf_counter() - start
        vram_after = process_vram_mib()
        self.vram_mib = None if vram_after is None else vram_after - vram_before

    def _run(self, audio: np.ndarray) -> tuple[str, list[dict[str, Any]]]:
        segments, _ = self.model.transcribe(
            audio,
            language=self.language,
            task="transcribe",
            beam_size=self.beam_size,
            temperature=0.0,
            condition_on_previous_text=False,
            initial_prompt=self.initial_prompt,
            vad_filter=self.vad_filter,
        )
        found = [
            {"start": round(segment.start, 2), "end": round(segment.end, 2), "text": segment.text.strip()}
            for segment in segments  # es un generador: la transcripción ocurre al recorrerlo
        ]
        return clean_transcript(" ".join(segment["text"] for segment in found)), found

    def transcribe(self, audio: str | Path | np.ndarray, sample_rate: int = SAMPLE_RATE) -> Transcription:
        """Transcribe un archivo o un array mono; ``sample_rate`` solo se usa con arrays."""
        start = time.perf_counter()
        if isinstance(audio, (str, Path)):
            samples, _ = read_audio(audio, SAMPLE_RATE)
        else:
            samples = resample(to_mono(audio), sample_rate, SAMPLE_RATE)
        text, segments = self._run(samples)
        return Transcription(
            text=text,
            seconds=time.perf_counter() - start,
            audio_seconds=duration(samples, SAMPLE_RATE),
            language=self.language,
            segments=segments,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe audios en español con Whisper.")
    parser.add_argument("audio", type=Path, nargs="+")
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    asr = WhisperASR(args.model)
    print(f"[{asr.model_name} en {asr.device} ({asr.compute_type}); carga {asr.load_seconds:.1f} s; VRAM {asr.vram_mib} MiB]")
    for path in args.audio:
        result = asr.transcribe(path)
        print(f"{path.name} ({result.audio_seconds:.1f} s de audio, {result.seconds:.2f} s): {result.text}")


if __name__ == "__main__":
    main()
