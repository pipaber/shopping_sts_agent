"""El motor F5 sin cargar el modelo: de dónde clona, cuánto pide que dure y cómo detecta texto perdido."""

import json
from pathlib import Path

import numpy as np
import pytest

from shopping_agent.voice import f5
from shopping_agent.voice.audio import write_wav
from shopping_agent.voice.f5 import (
    DEFAULT_TURNS,
    EDGE_SECONDS,
    SAMPLE_RATE,
    TURNS_ENV,
    F5SpanishTTS,
    count_syllables,
    lost_text,
    read_reference,
    resolve_turns,
    speech_seconds,
    trim_silence,
)
from shopping_agent.voice.report import cloned_from, voice_label
from shopping_agent.voice.tts import ENGINE_ENV, VoiceNotConfigured, XttsTTS, load_tts, resolve_engine

ORDER_DONE = "Pedido número uno registrado. ¡Gracias por tu compra!"


def voiced(seconds: float, rate: int = SAMPLE_RATE) -> np.ndarray:
    """Un tono que hace de voz."""
    return (0.1 * np.sin(2 * np.pi * 150 * np.arange(int(seconds * rate)) / rate)).astype(np.float32)


def silence(seconds: float, rate: int = SAMPLE_RATE) -> np.ndarray:
    return np.zeros(int(seconds * rate), dtype=np.float32)


@pytest.fixture
def recorded_turns(tmp_path, monkeypatch):
    """Un escenario con dos turnos grabados, en las carpetas donde los busca el motor."""
    monkeypatch.setattr(f5, "RECORDINGS_DIR", tmp_path / "audio")
    monkeypatch.setattr(f5, "SCRIPTS_DIR", tmp_path / "guiones")
    steps = [{"say": "Busco una cafetera. Tengo 60 euros."}, {"event": "set_offer"}, {"say": "Añade 2 de la primera."}]
    (tmp_path / "guiones").mkdir()
    (tmp_path / "guiones" / "compra.json").write_text(json.dumps({"steps": steps}), encoding="utf-8")
    for number, seconds, rate in ((1, 2.0, 16000), (2, 1.0, SAMPLE_RATE)):  # cada grabación a su frecuencia de muestreo
        audio = np.concatenate([silence(0.5, rate), voiced(seconds, rate), silence(0.5, rate)])
        write_wav(tmp_path / "audio" / "compra" / f"{number:02d}.wav", audio, rate)
    return tmp_path


def test_turns_come_from_the_argument_the_environment_or_the_default(monkeypatch):
    monkeypatch.delenv(TURNS_ENV, raising=False)
    assert resolve_turns() == DEFAULT_TURNS == ("01_compra_confirmada/01", "03_cambio_cantidad/01")
    monkeypatch.setenv(TURNS_ENV, "02_pedido_ambiguo/01, 04_sin_existencias/02")
    assert resolve_turns() == ("02_pedido_ambiguo/01", "04_sin_existencias/02")
    assert resolve_turns(("compra/01",)) == ("compra/01",)  # el argumento manda sobre el entorno


def test_reference_joins_the_recorded_turns_and_spells_out_their_text(recorded_turns):
    audio, text, files = read_reference(("compra/01", "compra/02"))
    # con cifras la transcripción queda más corta que el audio y F5 se salta el comienzo de lo que dice después
    assert text == "Busco una cafetera. Tengo sesenta euros. Añade dos de la primera."
    assert [path.name for path in files] == ["01.wav", "02.wav"]
    # los dos turnos seguidos, sin el silencio de los extremos: 2 s, la pausa interior (0,5 + 0,25 + 0,5 s) y 1 s
    assert len(audio) / SAMPLE_RATE == pytest.approx(4.25, abs=0.2)


def test_missing_turns_stop_with_instructions(recorded_turns):
    for wrong in ("compra/03", "compra/09", "otro/01", "compra"):
        with pytest.raises(VoiceNotConfigured, match=TURNS_ENV):
            read_reference((wrong,))


def test_reference_longer_than_the_model_accepts_is_rejected(recorded_turns):
    write_wav(recorded_turns / "audio" / "compra" / "02.wav", voiced(11.0), SAMPLE_RATE)
    with pytest.raises(VoiceNotConfigured, match="elige menos turnos"):
        read_reference(("compra/01", "compra/02"))


def test_silence_is_trimmed_from_both_ends():
    audio = np.concatenate([silence(1.0), voiced(0.5), silence(0.3), voiced(0.5), silence(2.0)])
    trimmed = trim_silence(audio, SAMPLE_RATE)
    assert len(trimmed) / SAMPLE_RATE == pytest.approx(1.4, abs=0.05)  # 1,3 s de habla con su pausa y el margen de los lados
    assert speech_seconds(audio, SAMPLE_RATE) == pytest.approx(1.0, abs=0.05)
    assert len(trim_silence(silence(1.0), SAMPLE_RATE)) == SAMPLE_RATE  # sin voz no hay nada que recortar


def test_lost_text_is_detected_by_speech_time_against_syllables():
    assert count_syllables(ORDER_DONE) == 18
    # lo que pasó en la comparación: 2,5 s de silencio y solo «Gracias por tu compra» (1,2 s de voz)
    assert lost_text(np.concatenate([silence(2.5), voiced(1.2)]), SAMPLE_RATE, ORDER_DONE)
    assert not lost_text(np.concatenate([silence(0.3), voiced(2.7)]), SAMPLE_RATE, ORDER_DONE)  # dicha entera
    assert lost_text(silence(1.0), SAMPLE_RATE, "¿Lo confirmo?")  # un fragmento que salió en silencio
    assert lost_text(1e-4 * voiced(1.0), SAMPLE_RATE, "¿Lo confirmo?")  # ni con un ruido de fondo casi inaudible
    assert not lost_text(voiced(0.4), SAMPLE_RATE, "Sí.")


def unloaded(outputs: list[np.ndarray]) -> tuple[F5SpanishTTS, list[int]]:
    """El motor sin cargar el modelo: ``_generate`` devuelve los audios dados y anota las semillas."""
    tts, seeds = F5SpanishTTS.__new__(F5SpanishTTS), []
    tts.seed, tts.max_chars, tts.device, tts.speed = 5, 135, "cpu", 1.0

    def generate(chunk: str, seed: int) -> np.ndarray:
        seeds.append(seed)
        return outputs[len(seeds) - 1]

    tts._generate = generate
    return tts, seeds


def test_chunk_with_lost_text_is_retried_with_another_seed():
    whole = voiced(2.7)
    tts, seeds = unloaded([voiced(1.2), whole])
    result = tts.synthesize(ORDER_DONE)
    assert seeds == [5, 6] and result.retries == 1
    assert result.audio is not whole and np.array_equal(result.audio, whole)

    tts, seeds = unloaded([whole])
    assert tts.synthesize(ORDER_DONE).retries == 0 and seeds == [5]


def test_when_every_attempt_loses_text_the_one_with_most_speech_is_kept():
    tts, seeds = unloaded([voiced(0.5), voiced(1.5), voiced(1.0)])
    result = tts.synthesize(ORDER_DONE)
    assert seeds == [5, 6, 7] and result.retries == 2
    assert result.audio_seconds == pytest.approx(1.5)


def test_requested_duration_follows_the_reference_pace_the_speed_and_a_margin():
    tts, _ = unloaded([])
    tts.reference_audio, tts.reference_text = silence(10.0), "x" * 100  # 0,1 s por byte de texto
    assert tts._total_seconds("y" * 50) == pytest.approx(10.0 + 5.0 + EDGE_SECONDS)
    tts.speed = 0.5  # la mitad de rápido: el doble de tiempo para el fragmento
    assert tts._total_seconds("y" * 50) == pytest.approx(10.0 + 10.0 + EDGE_SECONDS)
    # a una frase muy corta le queda sitio aunque por su longitud le tocaran décimas de segundo
    assert tts._total_seconds("Sí.") - 10.0 > EDGE_SECONDS


def test_engine_comes_from_the_environment_and_defaults_to_f5(monkeypatch):
    monkeypatch.delenv(ENGINE_ENV, raising=False)
    assert resolve_engine() == "f5"
    monkeypatch.setenv(ENGINE_ENV, "XTTS")
    assert resolve_engine() == "xtts"
    monkeypatch.setenv(ENGINE_ENV, "otro")
    with pytest.raises(VoiceNotConfigured, match=ENGINE_ENV):
        resolve_engine()


def test_load_tts_builds_the_chosen_engine(monkeypatch):
    built = []
    monkeypatch.setattr(XttsTTS, "__init__", lambda self, reference, speaker, speed=None: built.append(("xtts", reference, speaker, speed)))
    monkeypatch.setattr(F5SpanishTTS, "__init__", lambda self, speed=None: built.append(("f5", speed)))
    monkeypatch.setenv(ENGINE_ENV, "xtts")
    assert isinstance(load_tts("voz.wav", None, 1.2), XttsTTS)
    monkeypatch.setenv(ENGINE_ENV, "f5")
    assert isinstance(load_tts(speed=0.8), F5SpanishTTS)
    assert built == [("xtts", "voz.wav", None, 1.2), ("f5", 0.8)]
    for reference, speaker in (("voz.wav", None), (None, "Prueba")):  # son de XTTS-v2: F5 clona de turnos grabados
        with pytest.raises(VoiceNotConfigured, match="SHOPPING_AGENT_TTS=xtts"):
            load_tts(reference, speaker)


def test_saved_voice_says_which_turns_it_was_cloned_from():
    tts, _ = unloaded([])
    tts.references = [Path("audio/escenarios/compra/01.wav"), Path("audio/escenarios/compra/02.wav")]
    voice = tts.voice
    assert voice == {"references": ["audio/escenarios/compra/01.wav", "audio/escenarios/compra/02.wav"], "speaker": None, "speed": 1.0}
    assert voice_label(voice) == (
        "clonada de los turnos grabados `audio/escenarios/compra/01.wav`, `audio/escenarios/compra/02.wav`, velocidad del habla 1,00"
    )
    assert cloned_from(voice) == tts.references
    assert cloned_from({"reference": "voz.wav", "speaker": None}) == [Path("voz.wav")]  # una corrida con XTTS-v2
    assert cloned_from({"reference": None, "speaker": "Prueba"}) == cloned_from({}) == []
