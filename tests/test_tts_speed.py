"""La medida de la velocidad del habla, con un TTS y un ASR simulados: sin GPU ni modelos."""

import json

import numpy as np
import pytest

from shopping_agent.eval.tts_speed import measure, summarize, texts_to_speak, to_markdown
from shopping_agent.voice.tts import Synthesis


class SpeedTTS:
    """Un segundo de audio por palabra a velocidad 1,0; más corto cuanto más rápido."""

    sample_rate = 8000
    speed = 1.0

    def synthesize(self, text):
        seconds = len(text.split()) / self.speed
        audio = np.zeros(int(self.sample_rate * seconds), dtype=np.float32)
        return Synthesis(audio, self.sample_rate, seconds=0.5, first_chunk_seconds=0.2, audio_seconds=seconds, chunks=[text], retries=1)


def saved_run(folder, spoken):
    """Una corrida de escenarios guardada con lo mínimo: lo que se envió al TTS en cada turno."""
    steps = [{"kind": "turn", "spoken_text": text} for text in spoken]
    (folder / "corrida.json").write_text(json.dumps({"scenarios": [{"id": "compra"}]}), encoding="utf-8")
    (folder / "compra.json").write_text(json.dumps({"id": "compra", "steps": [*steps, {"kind": "event"}]}), encoding="utf-8")
    return folder


def test_texts_come_from_a_script_and_a_saved_run_without_repeats(tmp_path):
    script = tmp_path / "frases.txt"
    script.write_text("El total es 19,00 €.\n\nHecho.\n", encoding="utf-8")
    run = saved_run(tmp_path, ["Hecho.", "Pedido número uno registrado.", ""])
    assert texts_to_speak(script, run) == ["El total es diecinueve euros.", "Hecho.", "Pedido número uno registrado."]
    assert texts_to_speak(None, None) == []


def test_each_speed_is_measured_on_the_same_texts(tmp_path):
    texts = ["Hecho, añadidas dos unidades.", "Pedido número uno registrado."]
    heard = {"01.wav": "Hecho, añadidas dos unidades", "02.wav": "Pedido número uno registrados"}
    tts, report = SpeedTTS(), {"speeds": {}}
    for speed in (1.0, 2.0):
        tts.speed = speed
        cases = measure(texts, tts, lambda path: heard[path.name], lambda path: {"similarity": 0.5}, tmp_path / f"{speed:.2f}")
        report["speeds"][f"{speed:.2f}"] = {"summary": summarize(cases), "cases": cases}
    assert (tmp_path / "2.00" / "02.wav").is_file()
    slow, fast = (report["speeds"][speed]["summary"] for speed in ("1.00", "2.00"))
    assert slow["wer"] == fast["wer"] == pytest.approx(1 / 8) and slow["exact"] == 1
    assert slow["audio_seconds"] == pytest.approx(8.0) and fast["audio_seconds"] == pytest.approx(4.0)
    assert slow["words_per_second"] == pytest.approx(1.0) and fast["words_per_second"] == pytest.approx(2.0)
    assert slow["similarity"] == 0.5 and slow["similarity_real"] is None and slow["retries"] == 2

    report |= {"texts": 2, "asr_model": "simulado", "voice": {"reference": "voz.wav", "speaker": None}}
    report["real_recordings"] = {"count": 0, "similarity_among": None}
    text = to_markdown(report)
    assert "| 2.00 | 12.5 % | 1 de 2 | 0.500 | — | 4.0 | 2.00 | 1.0 | 2 |" in text
    assert "### Velocidad 1.00: 1 de 2 textos con alguna palabra distinta" in text
    assert "«Pedido número uno registrado.» → «Pedido número uno registrados»" in text
