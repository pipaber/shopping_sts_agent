import numpy as np
import pytest

from shopping_agent.voice.asr import clean_transcript
from shopping_agent.voice.audio import duration, read_audio, resample, to_mono, write_wav


def test_audio_roundtrip_and_resampling(tmp_path):
    rate = 24000
    tone = (0.3 * np.sin(2 * np.pi * 440 * np.arange(rate) / rate)).astype(np.float32)
    path = write_wav(tmp_path / "sub" / "tono.wav", tone, rate)
    audio, read_rate = read_audio(path)
    assert read_rate == rate and audio.dtype == np.float32
    assert np.allclose(audio, tone, atol=1e-3)
    audio16, rate16 = read_audio(path, 16000)
    assert rate16 == 16000 and len(audio16) == 16000
    assert duration(audio16, rate16) == pytest.approx(1.0)
    assert len(resample(tone, rate, 16000)) == 16000


def test_to_mono_handles_stereo_and_integers():
    stereo = np.stack([np.ones(10), -np.ones(10)], axis=1)
    assert np.allclose(to_mono(stereo), 0.0)
    pcm = np.array([0, 16384, -16384], dtype=np.int16)
    assert np.allclose(to_mono(pcm), [0.0, 0.5, -0.5], atol=1e-3)


def test_clean_transcript_collapses_whitespace():
    assert clean_transcript("  Hola,   busco \n auriculares. ") == "Hola, busco auriculares."
