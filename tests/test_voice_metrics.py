import json

import numpy as np
import pytest

from shopping_agent.eval.voice import (
    asr_errors,
    compare_figures,
    compare_terms,
    cosine,
    evaluate_run,
    extract_figures,
    normalize,
    pooled_wer,
    read_number,
    similarity_among,
    speaker_comparison,
    summarize_asr,
    to_markdown,
    wer,
)
from shopping_agent.voice.speech_text import number_to_words


def test_normalize_makes_notations_comparable():
    assert normalize("Tengo un presupuesto de 60 €.") == normalize("tengo un presupuesto de sesenta euros")
    assert normalize("¿Cuánto dura la batería?") == "cuanto dura la bateria"
    assert normalize("De'Longhi") == "delonghi"


def test_wer_counts_word_errors():
    result = wer("Añade dos del primero al carrito.", "añade dos del primero al carrito")
    assert result["wer"] == 0.0 and result["hits"] == 6
    result = wer("Añade dos del primero al carrito", "Añade tres del primero carrito")
    assert result["substitutions"] == 1 and result["deletions"] == 1
    assert result["wer"] == pytest.approx(2 / 6)


def test_wer_with_empty_texts():
    assert wer("", "")["wer"] == 0.0
    assert wer("", "hola")["wer"] is None
    assert wer("sí confirmo", "")["wer"] == 1.0


def test_pooled_wer_weights_by_length():
    results = [wer("uno dos tres cuatro", "uno dos tres cuatro"), wer("sí", "no")]
    assert pooled_wer(results) == pytest.approx(1 / 5)
    assert pooled_wer([]) is None


@pytest.mark.parametrize("number", [0, 1, 7, 16, 21, 30, 45, 99, 100, 101, 250, 999, 1000, 1001, 2021, 21000, 345678, 1000000, 2500000])
def test_read_number_inverts_number_to_words(number):
    tokens = normalize(number_to_words(number)).split()
    assert read_number(tokens, 0) == (number, len(tokens))


def test_read_number_does_not_merge_separate_numbers():
    tokens = "dos tres".split()
    assert read_number(tokens, 0) == (2, 1)
    assert read_number("hola".split(), 0) is None


def test_extract_figures_separates_amounts_from_quantities():
    figures = extract_figures("Añade 2 del primero; tengo un presupuesto de 60 euros.")
    assert figures.quantities == [2] and figures.amounts == [6000]
    figures = extract_figures("Son catorce euros con cincuenta y cinco céntimos por tres unidades")
    assert figures.amounts == [1455] and figures.quantities == [3]
    assert extract_figures("Total: 0,50 € y 1 €").amounts == [50, 100]
    assert extract_figures("mil doscientos euros").amounts == [120000]


def test_articles_are_not_quantities():
    assert extract_figures("busco una cafetera y un regalo").quantities == []
    assert extract_figures("añade una unidad").quantities == [1]
    assert extract_figures("quiero uno").quantities == [1]
    assert extract_figures("cuesta un euro").amounts == [100]


def test_compare_figures_detects_a_misheard_quantity_and_amount():
    result = compare_figures("Añade dos del primero, tengo sesenta euros", "Añade 12 del primero, tengo 70 euros")
    assert result["quantities"] == {"reference": [2], "hypothesis": [12], "missing": [2], "extra": [12], "errors": 1}
    assert result["amounts"]["missing"] == [6000] and result["amounts"]["extra"] == [7000]
    same = compare_figures("Mejor que sean tres.", "Mejor que sean 3")
    assert same["quantities"]["errors"] == 0 and same["amounts"]["errors"] == 0


def test_compare_terms_reports_what_the_asr_understood_instead():
    result = compare_terms(["auriculares bluetooth", "De'Longhi"], "busco unos auriculares blutuz de la marca delonghi")
    assert result["total"] == 2 and result["errors"] == 1
    assert result["missing"][0]["term"] == "auriculares bluetooth"
    assert result["missing"][0]["closest"] == "auriculares blutuz"
    assert 0.5 < result["missing"][0]["similarity"] < 1
    assert compare_terms([], "lo que sea") == {"total": 0, "missing": [], "errors": 0}


def test_summarize_asr_pools_the_cases():
    cases = [
        asr_errors("Añade dos auriculares por sesenta euros", "Añade dos auriculares por 60 euros", ["auriculares"]),
        asr_errors("Mejor que sean tres cafeteras", "Mejor que sean seis cafeterías", ["cafeteras"]),
    ]
    summary = summarize_asr(cases)
    assert summary["cases"] == 2 and summary["exact"] == 1
    assert summary["amounts"] == {"total": 1, "errors": 0, "error_rate": 0.0}
    assert summary["quantities"] == {"total": 2, "errors": 1, "error_rate": 0.5}
    assert summary["products"] == {"total": 2, "errors": 1, "error_rate": 0.5}
    assert summary["wer"] == pytest.approx(2 / 11)


def test_cosine():
    assert cosine(np.array([1.0, 0.0]), np.array([2.0, 0.0])) == pytest.approx(1.0)
    assert cosine(np.array([1.0, 0.0]), np.array([0.0, 3.0])) == pytest.approx(0.0)
    assert cosine(np.array([1.0, 1.0]), np.array([-1.0, -1.0])) == pytest.approx(-1.0)
    assert cosine(np.zeros(3), np.ones(3)) == 0.0


class FakeEmbedder:
    """El "hablante" es la frecuencia dominante: basta para probar el cableado."""

    def embed(self, audio, rate):
        spectrum = np.abs(np.fft.rfft(audio, n=rate))
        return spectrum / (np.linalg.norm(spectrum) or 1.0)


def _tone(frequency, rate=16000):
    return (0.3 * np.sin(2 * np.pi * frequency * np.arange(rate) / rate)).astype(np.float32), rate


TONES = {"ref.wav": 220, "real_1.wav": 220, "real_2.wav": 1500, "respuesta_01.wav": 220, "respuesta_02.wav": 1500}


def _read_tone(path):
    return _tone(TONES[path.name])


def test_synthesis_is_compared_with_the_reference_and_with_real_recordings(tmp_path):
    real = [tmp_path / "real_1.wav", tmp_path / "real_2.wav"]
    compare = speaker_comparison(FakeEmbedder(), tmp_path / "ref.wav", real, _read_tone)
    same, other = compare(tmp_path / "respuesta_01.wav"), compare(tmp_path / "respuesta_02.wav")
    assert same["similarity"] == pytest.approx(1.0, abs=1e-3) and other["similarity"] < 0.1
    # con las grabaciones reales es la media: cada respuesta se parece a una de las dos
    assert same["similarity_real"] == pytest.approx(0.5, abs=1e-2) == pytest.approx(other["similarity_real"], abs=1e-2)
    only_real = speaker_comparison(FakeEmbedder(), None, real, _read_tone)
    assert set(only_real(tmp_path / "respuesta_01.wav")) == {"similarity_real"}
    only_reference = speaker_comparison(FakeEmbedder(), tmp_path / "ref.wav", [], _read_tone)
    assert set(only_reference(tmp_path / "respuesta_01.wav")) == {"similarity"}
    assert speaker_comparison(None, tmp_path / "ref.wav", real, _read_tone) is None
    assert speaker_comparison(FakeEmbedder(), None, [], _read_tone) is None


def test_similarity_among_recordings_leaves_each_one_out(tmp_path):
    alike = [tmp_path / "real_1.wav", tmp_path / "ref.wav"]
    assert similarity_among(FakeEmbedder(), alike, _read_tone) == pytest.approx(1.0, abs=1e-3)
    assert similarity_among(FakeEmbedder(), [tmp_path / "real_1.wav", tmp_path / "real_2.wav"], _read_tone) < 0.1
    assert similarity_among(FakeEmbedder(), alike[:1], _read_tone) is None


def test_evaluate_run_without_models(tmp_path):
    record = {
        "turns": [
            {
                "turn": 1, "input_audio": "entrada_01.wav", "expected_text": "Añade dos auriculares.",
                "transcript": "Añade 12 auriculares.", "product_terms": ["auriculares"],
                "spoken_text": "Hecho, añadidas dos unidades.", "output_audio": "respuesta_01.wav",
            },
            {   # turno repetido con el texto correcto: no hay audio de entrada que evaluar
                "turn": 2, "input_audio": None, "expected_text": "Sí.", "transcript": None,
                "spoken_text": "Pedido número uno registrado.", "output_audio": "respuesta_02.wav",
            },
        ]
    }
    (tmp_path / "turnos.json").write_text(json.dumps(record), encoding="utf-8")
    heard = {"respuesta_01.wav": "Hecho, añadidas dos unidades", "respuesta_02.wav": "Pedido número uno registrados"}
    real = [tmp_path / "real_1.wav", tmp_path / "real_2.wav"]
    compare = speaker_comparison(FakeEmbedder(), tmp_path / "ref.wav", real, _read_tone)

    metrics = evaluate_run(tmp_path, lambda path: heard[path.name], compare)
    asr = metrics["asr"]
    assert asr["summary"]["cases"] == 1
    assert asr["summary"]["quantities"] == {"total": 1, "errors": 1, "error_rate": 1.0}
    assert asr["summary"]["products"]["errors"] == 0
    tts = metrics["tts"]
    assert tts["summary"]["cases"] == 2
    assert tts["summary"]["wer"] == pytest.approx(1 / 8)
    assert tts["cases"][0]["similarity"] == pytest.approx(1.0, abs=1e-3)
    assert tts["summary"]["similarity_min"] < 0.1
    assert tts["summary"]["similarity_real_mean"] == pytest.approx(0.5, abs=1e-2)
    report = to_markdown(metrics)
    assert "Cantidades: 1 errores de 1" in report and "Semejanza con la referencia" in report
    assert "Semejanza con las grabaciones reales (coseno ECAPA): media 0.5" in report and "sale optimista" not in report

    metrics["real_recordings"] = {"count": 2, "similarity_among": 0.01}
    report = to_markdown(metrics)
    assert "las 2 grabaciones reales se parecen entre sí 0.010" in report and "sale optimista" in report

    no_reference = evaluate_run(tmp_path, lambda path: heard[path.name], None)
    assert no_reference["tts"]["summary"]["similarity_mean"] is None
    assert no_reference["tts"]["summary"]["similarity_real_mean"] is None
