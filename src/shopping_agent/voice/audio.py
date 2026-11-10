"""Lectura y escritura de audio como arrays mono en coma flotante."""

from __future__ import annotations

from math import gcd
from pathlib import Path

import numpy as np


def to_mono(audio: np.ndarray) -> np.ndarray:
    """Array ``float32`` de una dimensión; si llega (muestras, canales) se promedian los canales."""
    audio = np.asarray(audio)
    if np.issubdtype(audio.dtype, np.integer):
        audio = audio.astype(np.float32) / float(np.iinfo(audio.dtype).max)
    audio = audio.astype(np.float32, copy=False)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    return np.ascontiguousarray(audio.reshape(-1))


def resample(audio: np.ndarray, rate: int, target_rate: int) -> np.ndarray:
    """Cambia la frecuencia de muestreo con un filtro polifásico."""
    if rate == target_rate:
        return to_mono(audio)
    from scipy.signal import resample_poly

    divisor = gcd(int(rate), int(target_rate))
    return resample_poly(to_mono(audio), target_rate // divisor, rate // divisor).astype(np.float32)


def read_audio(path: str | Path, target_rate: int | None = None) -> tuple[np.ndarray, int]:
    """Lee un archivo de audio como mono ``float32``.

    WAV, FLAC, OGG y MP3 se leen con ``soundfile``; el resto (por ejemplo M4A de un
    móvil) se decodifica con PyAV, que viene con ``faster-whisper``.
    """
    import soundfile as sf

    path = Path(path)
    try:
        audio, rate = sf.read(str(path), dtype="float32", always_2d=False)
    except (sf.LibsndfileError, RuntimeError):
        from faster_whisper.audio import decode_audio

        rate = target_rate or 16000
        return decode_audio(str(path), sampling_rate=rate), rate
    audio = to_mono(audio)
    if target_rate and rate != target_rate:
        return resample(audio, rate, target_rate), target_rate
    return audio, rate


def write_wav(path: str | Path, audio: np.ndarray, rate: int) -> Path:
    """Guarda un WAV PCM de 16 bits."""
    import soundfile as sf

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), np.clip(to_mono(audio), -1.0, 1.0), rate, subtype="PCM_16")
    return path


def duration(audio: np.ndarray, rate: int) -> float:
    return len(audio) / float(rate)
