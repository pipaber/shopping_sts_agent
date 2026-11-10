"""El turno por voz con ASR y TTS simulados: sin GPU ni modelos."""

import json

import numpy as np
import pytest

from shopping_agent.agent import tools
from shopping_agent.agent.session import LLM, RETRIEVAL, TOOLS
from shopping_agent.voice.asr import Transcription
from shopping_agent.voice.audio import read_audio, write_wav
from shopping_agent.voice.pipeline import STAGES, VoicePipeline, compare_runs, summarize_timings, to_markdown
from shopping_agent.voice.tts import (
    REFERENCE_ENV,
    SPEAKER_ENV,
    Synthesis,
    VoiceNotConfigured,
    join_chunks,
    resolve_voice,
)
from test_agent import Shop, call, say


class FakeASR:
    """Devuelve la transcripción guionizada del siguiente audio."""

    def __init__(self, transcripts):
        self.transcripts = list(transcripts)
        self.heard = []

    def transcribe(self, audio, sample_rate=16000):
        self.heard.append(audio)
        return Transcription(text=self.transcripts.pop(0), seconds=0.25, audio_seconds=2.0)


class FakeTTS:
    sample_rate = 8000

    def __init__(self):
        self.texts = []

    def synthesize(self, text):
        self.texts.append(text)
        audio = np.full(self.sample_rate, 0.1, dtype=np.float32)
        return Synthesis(audio, self.sample_rate, seconds=0.5, first_chunk_seconds=0.2, audio_seconds=1.0, chunks=[text])


def new_shop(folder):
    folder.mkdir()
    return Shop(folder)


@pytest.fixture
def shop(tmp_path):
    return new_shop(tmp_path / "tienda")


def purchase_script():
    return [
        call(tools.SET_BUDGET, importe_eur=50),
        call(tools.SEARCH, consulta="auriculares bluetooth"),
        say("Tengo los Sony por 20,00 € y los JBL por 15,00 €."),
        call(tools.ADD, product_id="P1", cantidad=2),
        say("Añadidos."),
        call(tools.QUOTE),
    ]


def test_voice_turn_keeps_audio_text_and_timings(shop, tmp_path):
    shop.llm.extend(purchase_script()[:3])
    asr, tts = FakeASR(["Busco auriculares bluetooth y tengo 50 euros"]), FakeTTS()
    out_dir = tmp_path / "corrida"
    pipeline = VoicePipeline(shop.session(), asr, tts, out_dir)
    recording = write_wav(tmp_path / "pregunta.wav", np.zeros(16000, dtype=np.float32), 16000)

    turn = pipeline.run_turn(recording, expected_text="Busco auriculares bluetooth y tengo 50 euros.")

    assert turn.transcript == turn.agent_input == "Busco auriculares bluetooth y tengo 50 euros"
    assert turn.input_audio == "entrada_01.wav" and (out_dir / "entrada_01.wav").exists()
    assert turn.output_audio == "respuesta_01.wav"
    audio, rate = read_audio(out_dir / "respuesta_01.wav")
    assert rate == 8000 and len(audio) == 8000
    # La transcripción guarda el texto del agente; al TTS llega la versión hablada.
    assert "20,00 €" in turn.response
    assert "veinte euros" in turn.spoken_text and "€" not in turn.spoken_text
    assert tts.texts == [turn.spoken_text]
    assert [operation["tool"] for operation in turn.operations] == [tools.SET_BUDGET, tools.SEARCH]
    # Tiempos por etapa: los cinco, y el total es su suma.
    assert set(STAGES) <= set(turn.timings)
    assert turn.timings["asr"] == 0.25 and turn.timings["tts"] == 0.5
    assert turn.timings[LLM] > 0 and turn.timings[RETRIEVAL] > 0 and turn.timings[TOOLS] > 0
    assert turn.timings["total"] == pytest.approx(sum(turn.timings[stage] for stage in STAGES), abs=0.01)
    assert turn.timings["tts_primer_fragmento"] == 0.2


def test_session_reports_stage_times_that_add_up(shop):
    shop.llm.extend(purchase_script()[:3])
    result = shop.session().send("Busco auriculares bluetooth y tengo 50 euros")
    assert set(result.stages) == {LLM, RETRIEVAL, TOOLS}
    assert sum(result.stages.values()) == pytest.approx(result.seconds)


def test_purchase_by_voice_registers_the_order_after_a_spoken_yes(shop, tmp_path):
    shop.llm.extend(purchase_script())
    asr = FakeASR(["Busco auriculares bluetooth y tengo 50 euros", "Añade dos del primero", "Quiero cerrar el pedido", "Sí, confirmo."])
    pipeline = VoicePipeline(shop.session(), asr, FakeTTS(), tmp_path / "corrida")
    silence = np.zeros(16000, dtype=np.float32)

    turns = [pipeline.run_turn(silence) for _ in range(4)]

    assert turns[2].awaiting_confirmation
    assert not turns[3].awaiting_confirmation and shop.orders() == 1
    assert turns[3].timings[LLM] == 0.0  # confirmar no pasa por el LLM
    assert shop.stock("P1") == 8
    assert "cuarenta euros" in turns[3].spoken_text
    assert (tmp_path / "corrida" / "entrada_04.wav").exists()  # los arrays también se guardan


def test_same_turn_can_be_repeated_with_the_correct_text(shop, tmp_path):
    """El ASR oye "doce" donde se dijo "dos"; con el texto correcto se ve la diferencia."""
    spoken_shop, written_shop = shop, new_shop(tmp_path / "otra")
    for target in (spoken_shop, written_shop):
        target.llm.extend([call(tools.SEARCH, consulta="auriculares bluetooth"), say("Tengo los Sony y los JBL.")])
    spoken_shop.llm.extend([call(tools.ADD, product_id="P1", cantidad=12), say("No hay tantas unidades.")])
    written_shop.llm.extend([call(tools.ADD, product_id="P1", cantidad=2), say("Añadidas.")])

    correct = ["Busco auriculares bluetooth", "Añade dos del primero"]
    by_voice = VoicePipeline(spoken_shop.session(), FakeASR(["Busco auriculares bluetooth", "Añade doce del primero"]), None)
    by_text = VoicePipeline(written_shop.session(), None, None)
    for text in correct:
        by_voice.run_turn(np.zeros(8000, dtype=np.float32), expected_text=text)
        by_text.run_turn(text=text, expected_text=text)

    assert by_text.turns[1].transcript is None and by_text.turns[1].timings["asr"] == 0.0
    assert by_text.turns[1].input_audio is None and by_text.turns[1].output_audio is None
    comparison = compare_runs(by_voice.turns, by_text.turns)
    assert comparison[0] == {"turn": 1, "same_input": True, "same_operations": True, "same_response": True}
    assert comparison[1]["same_input"] is False and comparison[1]["same_operations"] is False
    assert written_shop.sql("SELECT quantity FROM cart_items") == [(2,)]
    assert spoken_shop.sql("SELECT quantity FROM cart_items") == []  # doce no caben: rechazado por código


def test_turn_needs_exactly_one_input(shop):
    pipeline = VoicePipeline(shop.session(), FakeASR([]), None)
    with pytest.raises(ValueError):
        pipeline.run_turn()
    with pytest.raises(ValueError):
        pipeline.run_turn(np.zeros(10, dtype=np.float32), text="hola")
    with pytest.raises(ValueError):
        VoicePipeline(shop.session(), None, None).run_turn(np.zeros(10, dtype=np.float32))


def test_summary_and_report(shop, tmp_path):
    shop.llm.extend(purchase_script())
    asr = FakeASR(["Busco auriculares bluetooth y tengo 50 euros", "Añade dos del primero", "Quiero cerrar el pedido", "Sí"])
    pipeline = VoicePipeline(shop.session(), asr, FakeTTS(), tmp_path / "corrida")
    for _ in range(4):
        pipeline.run_turn(np.zeros(16000, dtype=np.float32), expected_text="lo que se dijo")

    summary = summarize_timings(pipeline.turns)
    assert summary["all"]["turns"] == 4 and summary["with_llm"]["turns"] == 3 and summary["without_llm"]["turns"] == 1
    assert summary["without_llm"]["llm"]["mean"] == 0.0
    assert summary["all"]["tts"] == {"mean": 0.5, "max": 0.5}

    from dataclasses import asdict

    record = {
        "date": "2026-11-10T10:00:00", "note": "audios sintéticos", "mode": "audio",
        "models": {"llm": "guion", "asr": "simulado", "tts": "simulado", "embeddings": "ninguno"},
        "voice": {"mode": "hablante_incluido", "reference": None, "speaker": "Prueba"},
        "load": {"search_seconds": 1.0, "llm_seconds": 2.0, "asr_seconds": 3.0, "tts_seconds": 4.0, "total_seconds": 10.0,
                 "vram_mib": {"loaded": 100, "after_run": 120}},
        "memory_backend": "memoria", "thread_id": "hilo-1",
        "turns": [asdict(turn) for turn in pipeline.turns], "timings": summary,
        "store": {"orders": [{"order_id": 1, "quote_id": "q", "total_cents": 4000}], "order_items": [], "cart_items": []},
        "text_run": None,
    }
    json.dumps(record)  # todo lo guardado es serializable
    report = to_markdown(record)
    assert "| Turno | ASR | Recuperación | LLM | Herramientas | TTS | Total |" in report
    assert "**Usuario (transcripción del ASR):** Sí" in report
    assert "**Enviado al TTS:**" in report and "Pedido 1: total 40,00 €" in report
    assert "audios sintéticos" in report


def test_join_chunks_inserts_pauses():
    pieces = [np.ones(100, dtype=np.float32), np.ones(50, dtype=np.float32)]
    joined = join_chunks(pieces, sample_rate=1000, pause_seconds=0.1)
    assert len(joined) == 250 and joined[100:200].sum() == 0
    assert len(join_chunks([], 1000)) == 0


def test_resolve_voice_prefers_the_reference_recording(tmp_path, monkeypatch):
    monkeypatch.delenv(REFERENCE_ENV, raising=False)
    monkeypatch.delenv(SPEAKER_ENV, raising=False)
    with pytest.raises(VoiceNotConfigured):
        resolve_voice()
    reference = write_wav(tmp_path / "mi_voz.wav", np.zeros(100, dtype=np.float32), 16000)
    monkeypatch.setenv(SPEAKER_ENV, "Hablante de prueba")
    assert resolve_voice() == (None, "Hablante de prueba")
    monkeypatch.setenv(REFERENCE_ENV, str(reference))
    assert resolve_voice() == (reference, None)
    assert resolve_voice(speaker="Otro") == (None, "Otro")  # los argumentos mandan sobre el entorno
    with pytest.raises(VoiceNotConfigured):
        resolve_voice(reference=tmp_path / "no_existe.wav")
