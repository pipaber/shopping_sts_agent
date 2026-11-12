"""Comprobación de las grabaciones del usuario frente al guion, con un ASR simulado."""

from shopping_agent.eval import recordings
from shopping_agent.eval.scenario_format import parse_scenario
from shopping_agent.voice.asr import Transcription

SCENARIO = parse_scenario({
    "id": "compra",
    "title": "Compra de prueba",
    "kind": "compra_confirmada",
    "voice": True,
    "description": "Busca, añade, corrige y confirma.",
    "steps": [
        {"say": "Busco una cafetera italiana.", "terms": ["cafetera italiana"]},
        {"say": "Añade dos de la primera."},
        {"say": "No, espera, he dicho doce, no dos."},
        {"say": "Sí."},
        {"say": "Sí."},
    ],
})


def check(tmp_path, heard):
    """``heard``: lo que el ASR simulado entiende de cada archivo que existe."""
    for name in heard:
        (tmp_path / "compra").mkdir(exist_ok=True)
        (tmp_path / "compra" / f"{name}.wav").touch()
    return recordings.check_recordings([SCENARIO], tmp_path, lambda path: Transcription(heard[path.stem], 0.1, 2.0))


def test_recordings_that_say_their_turn_are_exact(tmp_path):
    heard = {"01": "Busco una cafetera italiana", "02": "Añade 2 de la primera.", "03": "No, espera, he dicho 12, no 2.", "04": "sí", "05": "Sí."}
    report = check(tmp_path, heard)
    scenario = report["scenarios"][0]
    assert (report["expected"], report["found"], scenario["missing"]) == (5, 5, [])
    assert all(file["exact"] and file["closest_turn"] == file["turn"] for file in scenario["files"])  # el «Sí.» repetido no despista


def test_a_misheard_product_and_a_shifted_file_are_reported(tmp_path):
    heard = {"01": "Busco una cafetería italiana.", "02": "No, espera, he dicho 12, no 2.", "04": "Sí."}
    report = check(tmp_path, heard)
    first, second, fourth = report["scenarios"][0]["files"]
    assert report["scenarios"][0]["missing"] == ["03", "05"] and report["asr"]["products"]["errors"] == 1
    assert not first["exact"] and first["closest_turn"] == 1 and first["products"]["missing"][0]["closest"] == "cafeteria italiana"
    assert not second["exact"] and second["closest_turn"] == 3 and fourth["exact"]
    assert report["misplaced"] == [str(tmp_path / "compra" / "02.wav")] and report["asr"]["cases"] == 2  # el mal numerado no cuenta en el WER
    text = recordings.to_markdown(report)
    assert "2 de 5 archivos; faltan: 03, 05." not in text and "3 de 5 archivos; faltan: 03, 05." in text
    assert "**se parece más al turno 03**" in text and "distinto (WER 25 %)" in text
    assert "De los 2 que sí corresponden, 1 se entienden igual" in text and "nombres de producto: 1 de 1" in text
