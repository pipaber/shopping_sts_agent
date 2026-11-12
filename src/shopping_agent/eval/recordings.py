"""Comprueba que cada grabación del usuario dice el texto de su turno.

Uso::

    python -m shopping_agent.eval.recordings

Transcribe, con el mismo ASR que usa el agente, cada audio que haya en
``audio/escenarios/<escenario>/NN.wav`` y lo compara con el guion. No corre el
agente ni toca los audios. Escribe ``results/escenarios/grabaciones.json`` y
``grabaciones.md``: qué archivos faltan, qué se entendió en cada uno y cuáles no
dicen el texto de su turno. Si lo entendido se parece más al texto de otro turno
del mismo escenario, se indica: es la señal de un archivo mal numerado.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from shopping_agent.eval.scenario_format import DEFAULT_DIR, Say, Scenario, load_scenarios
from shopping_agent.eval.voice import asr_errors, normalize, summarize_asr
from shopping_agent.voice import chat as voice_chat
from shopping_agent.voice.asr import Transcription, WhisperASR

RESULTS_DIR = Path("results/escenarios")
REPORT_NAME = "grabaciones"

Transcribe = Callable[[Path], Transcription]


def recording(folder: Path, number: int) -> Path | None:
    """El audio del turno ``number`` en la carpeta de un escenario, si está."""
    found = [path for suffix in voice_chat.AUDIO_SUFFIXES if (path := folder / f"{number:02d}{suffix}").is_file()]
    return found[0] if found else None


def closest_turn(transcript: str, says: list[Say], number: int) -> int:
    """El turno del escenario cuyo texto más se parece a lo entendido. Si el propio
    turno empata con otro (hay textos repetidos, como «Sí.»), gana el propio."""
    heard = normalize(transcript)
    scores = [SequenceMatcher(None, normalize(say.text), heard).ratio() for say in says]
    return number if scores[number - 1] == max(scores) else scores.index(max(scores)) + 1


def check_file(path: Path, number: int, says: list[Say], transcribe: Transcribe) -> dict[str, Any]:
    """Lo que el ASR entiende de un archivo frente al texto de su turno."""
    say, heard = says[number - 1], transcribe(path)
    errors = asr_errors(say.text, heard.text, say.terms)
    return {
        "file": str(path),
        "turn": number,
        "audio_seconds": round(heard.audio_seconds, 1),
        **errors,
        "exact": normalize(say.text) == normalize(heard.text),
        "closest_turn": closest_turn(heard.text, says, number),
    }


def check_scenario(scenario: Scenario, folder: Path, transcribe: Transcribe) -> dict[str, Any]:
    says, files, missing = scenario.says, [], []
    for number in range(1, len(says) + 1):
        path = recording(folder, number)
        if path is None:
            missing.append(f"{number:02d}")
        else:
            files.append(check_file(path, number, says, transcribe))
    return {"id": scenario.id, "turns": len(says), "files": files, "missing": missing}


def check_recordings(scenarios: list[Scenario], folder: Path, transcribe: Transcribe) -> dict[str, Any]:
    """Todas las grabaciones de los escenarios de voz, y el resumen del ASR sobre ellas."""
    checked = [check_scenario(scenario, folder / scenario.id, transcribe) for scenario in scenarios if scenario.voice]
    files = [file for scenario in checked for file in scenario["files"]]
    return {
        "folder": str(folder),
        "expected": sum(scenario["turns"] for scenario in checked),
        "found": len(files),
        "asr": summarize_asr(files),
        "scenarios": checked,
    }


# --- Markdown ---------------------------------------------------------------------------


def _verdict(file: dict[str, Any]) -> str:
    if file["exact"]:
        return "igual"
    if file["closest_turn"] != file["turn"]:
        return f"**se parece más al turno {file['closest_turn']:02d}**"
    return f"distinto (WER {100 * file['wer']['wer']:.0f} %)"


def _scenario_lines(scenario: dict[str, Any]) -> list[str]:
    missing = f"; faltan: {', '.join(scenario['missing'])}" if scenario["missing"] else ""
    lines = [f"## {scenario['id']}", "", f"{len(scenario['files'])} de {scenario['turns']} archivos{missing}.", ""]
    lines += ["| Archivo | Duración | Texto del guion | Lo que entiende el ASR | Resultado |", "|---|---|---|---|---|"]
    for file in scenario["files"]:
        cells = [f"`{file['turn']:02d}`", f"{file['audio_seconds']} s", file["reference"], file["hypothesis"] or "(nada)", _verdict(file)]
        lines.append("| " + " | ".join(cells) + " |")
    return [*lines, ""]


def to_markdown(report: dict[str, Any]) -> str:
    asr = report["asr"]
    lines = [
        "# Grabaciones del usuario frente al guion",
        "",
        f"Audios en `{report['folder']}` (sin versionar): {report['found']} de {report['expected']} archivos.",
        f"Transcritos con el ASR del agente, sin correr el agente: {asr['exact']} de {asr['cases']} dicen el texto de su turno "
        f"tras normalizar; WER {100 * asr['wer']:.1f} %." if asr["cases"] else "No hay ninguna grabación.",
        "",
    ]
    for scenario in report["scenarios"]:
        lines += _scenario_lines(scenario)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara las grabaciones del usuario con el guion.")
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--recordings", type=Path, default=voice_chat.SCENARIO_AUDIO_DIR)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    asr = WhisperASR()
    report = {"asr_model": asr.model_name, **check_recordings(load_scenarios(args.scenarios), args.recordings, asr.transcribe)}
    (args.out / f"{REPORT_NAME}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (args.out / f"{REPORT_NAME}.md").write_text(to_markdown(report), encoding="utf-8")
    print(to_markdown(report))


if __name__ == "__main__":
    main()
