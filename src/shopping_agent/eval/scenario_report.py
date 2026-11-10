"""Fichas por escenario y resumen de las corridas de evaluación.

Uso, sobre las corridas ya guardadas por ``shopping_agent.eval.scenarios``::

    python -m shopping_agent.eval.scenario_report

Lee ``results/escenarios/<corrida>/`` y escribe ``results/escenarios/resumen.json``
y ``resumen.md``: porcentaje de escenarios correctos por corrida, violaciones de
restricciones, errores del ASR, voz sintetizada, latencia por etapa y la lista de
comprobaciones fallidas, que es el material para analizar aciertos y fallos.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import fields
from pathlib import Path
from typing import Any

from shopping_agent.agent.report import store_lines
from shopping_agent.eval.scenario_violations import KINDS
from shopping_agent.store.ops import format_eur
from shopping_agent.voice.pipeline import STAGES, TOTAL, VoiceTurn, comparable_store, compare_runs, summarize_timings
from shopping_agent.voice.report import STAGE_LABELS, timing_lines, turn_lines

DEFAULT_DIR = Path("results/escenarios")
RUN_FILE, SUMMARY_NAME, VOICE_METRICS_FILE = "corrida.json", "resumen", "metricas_voz.json"
AUDIO_RUN, TEXT_REPEAT_RUN = "voz", "voz_texto_correcto"
RUN_ORDER = ("texto", "texto_sage", "texto_sin_reranker", AUDIO_RUN, TEXT_REPEAT_RUN)
_TURN_FIELDS = tuple(field.name for field in fields(VoiceTurn))
_MARK = {True: "✔", False: "✘"}

Record = dict[str, Any]  # la corrida de un escenario, tal como la devuelve ``ScenarioRun``


def turns_of(record: Record) -> list[Record]:
    return [step for step in record["steps"] if step["kind"] == "turn"]


def voice_turns(record: Record) -> list[VoiceTurn]:
    """Los turnos guardados, otra vez como ``VoiceTurn`` para reutilizar sus resúmenes."""
    return [VoiceTurn(**{name: turn[name] for name in _TURN_FIELDS}) for turn in turns_of(record)]


def failed_checks(record: Record) -> list[dict[str, Any]]:
    """Las comprobaciones que no se cumplieron, con el turno en el que estaban (o "final")."""
    failed = [
        {"turn": turn["turn"], **check} for turn in turns_of(record) for check in turn["checks"] if not check["ok"]
    ]
    return failed + [{"turn": "final", **check} for check in record["final"]["checks"] if not check["ok"]]


# --- Ficha de un escenario --------------------------------------------------------------


def _check_lines(checks: list[dict[str, Any]]) -> list[str]:
    lines = []
    for check in checks:
        params = ", ".join(f"{key}={json.dumps(value, ensure_ascii=False)}" for key, value in check["params"].items())
        lines.append(f"- {_MARK[check['ok']]} `{check['check']}({params})` — {check['detail']}")
    return [*lines, ""] if lines else []


def _event_line(step: Record) -> str:
    changes = []
    if step["price_cents"] is not None:
        changes.append(f"precio {format_eur(step['price_cents'])}")
    if step["stock"] is not None:
        changes.append(f"existencias {step['stock']}")
    return f"> **Suceso externo:** la tienda deja `{step['product_id']}` ({step['product']}) con {' y '.join(changes)}."


def _step_lines(step: Record) -> list[str]:
    kind = step["kind"]
    if kind == "turn":
        return turn_lines(step) + _check_lines(step["checks"])
    if kind == "event":
        return [_event_line(step), ""]
    if kind == "remember":
        return [f"> `@{step['name']}` = `{step['product_id']}` ({step['ref']}): {step['title']}", ""]
    if kind == "new_conversation":
        return [f"> **Conversación nueva** del mismo usuario (hilo `{step['thread_id']}`).", ""]
    return ["```", step["traceback"].rstrip(), "```", ""]


def _header_lines(record: Record) -> list[str]:
    source = f" ({record['audio_source']})" if record["audio_source"] else ""
    return [
        f"# {record['id']} — {record['title']}",
        "",
        f"- Veredicto: **{'correcto' if record['passed'] else 'fallo'}**",
        f"- Entrada: {record['input']}{source}",
        f"- Tipo: `{record['kind']}`",
        f"- Qué se prueba: {record['description']}",
        "",
    ]


def _closing_lines(record: Record) -> list[str]:
    lines = ["## Comprobaciones finales", "", *_check_lines(record["final"]["checks"])]
    lines += ["## Violaciones de restricciones", ""]
    lines += [f"- `{found['kind']}` en el turno {found['turn']}: {found['detail']}" for found in record["violations"]]
    lines += ["- Ninguna."] if not record["violations"] else []
    lines += [f"- Problema de la corrida: {problem}" for problem in record["problems"]]
    return [*lines, "", *store_lines(record["final"]["snapshot"]["store"]), ""]


def ficha(record: Record) -> str:
    """Ficha en Markdown de la corrida de un escenario: todo lo necesario para analizarla."""
    lines = _header_lines(record)
    for step in record["steps"]:
        lines += _step_lines(step)
    lines += _closing_lines(record)
    lines += timing_lines({"turns": turns_of(record), "timings": record["timings"]})
    return "\n".join(lines) + "\n"


# --- Resumen de una corrida ---------------------------------------------------------------


def run_summary(records: list[Record]) -> dict[str, Any]:
    """Aciertos, violaciones y latencias de una corrida de varios escenarios."""
    turns = [turn for record in records for turn in voice_turns(record)]
    violations = Counter(found["kind"] for record in records for found in record["violations"])
    passed = [record["id"] for record in records if record["passed"]]
    return {
        "scenarios": len(records),
        "passed": len(passed),
        "pass_rate": len(passed) / len(records) if records else None,
        "failed": [record["id"] for record in records if not record["passed"]],
        "turns": len(turns),
        "violations": {kind: violations.get(kind, 0) for kind in KINDS},
        "timings": summarize_timings(turns),
    }


def _comparable(store: dict[str, Any]) -> dict[str, Any]:
    """La tienda sin lo que cambia de una corrida a otra: cotizaciones e hilos."""
    cleaned = comparable_store(store)
    cleaned["cart_items"] = [{key: value for key, value in row.items() if key != "cart_id"} for row in cleaned["cart_items"]]
    return cleaned


def compare_with_text(audio: Record, text: Record) -> dict[str, Any]:
    """El mismo escenario con audio y con la transcripción correcta: ¿cambió algo el ASR?"""
    rows = compare_runs(voice_turns(audio), voice_turns(text))
    stores = [_comparable(record["final"]["snapshot"]["store"]) for record in (audio, text)]
    return {
        "id": audio["id"],
        "passed_audio": audio["passed"],
        "passed_text": text["passed"],
        "asr_changed_words": [row["turn"] for row in rows if not row["same_words"]],
        "different_operations": [row["turn"] for row in rows if not row["same_operations"]],
        "same_store": stores[0] == stores[1],
    }


# --- Resumen de todas las corridas --------------------------------------------------------


def load_run(run_dir: Path) -> dict[str, Any]:
    info = json.loads((run_dir / RUN_FILE).read_text(encoding="utf-8"))
    records = [json.loads((run_dir / f"{row['id']}.json").read_text(encoding="utf-8")) for row in info["scenarios"]]
    metrics = run_dir / VOICE_METRICS_FILE
    voice = json.loads(metrics.read_text(encoding="utf-8")) if metrics.exists() else None
    return {"name": run_dir.name, "info": info, "records": records, "voice_metrics": voice}


def load_runs(folder: Path) -> list[dict[str, Any]]:
    """Las corridas guardadas, en un orden fijo: texto, ablación, voz y su repetición."""
    names = [path.parent.name for path in folder.glob(f"*/{RUN_FILE}")]
    names.sort(key=lambda name: (RUN_ORDER.index(name) if name in RUN_ORDER else len(RUN_ORDER), name))
    return [load_run(folder / name) for name in names]


_INFO_KEYS = ("date", "commit", "input", "models", "voice", "load", "memory_backend", "audio_sources")


def _run_entry(run: dict[str, Any]) -> dict[str, Any]:
    """Lo que el resumen guarda de una corrida."""
    records = run["records"]
    return {
        **{key: run["info"].get(key) for key in _INFO_KEYS},
        **run_summary(records),
        "verdicts": {record["id"]: record["passed"] for record in records},
        "failed_checks": {record["id"]: failed_checks(record) for record in records if not record["passed"]},
        "voice_metrics": run["voice_metrics"]["summary"] if run["voice_metrics"] else None,
    }


def _audio_vs_text(runs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Cada escenario de voz frente a su repetición con la transcripción correcta."""
    if AUDIO_RUN not in runs or TEXT_REPEAT_RUN not in runs:
        return []
    texts = {record["id"]: record for record in runs[TEXT_REPEAT_RUN]["records"]}
    return [compare_with_text(record, texts[record["id"]]) for record in runs[AUDIO_RUN]["records"] if record["id"] in texts]


def summarize(runs: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {run["name"]: run for run in runs}
    return {
        "runs": {name: _run_entry(run) for name, run in by_name.items()},
        "audio_vs_correct_text": _audio_vs_text(by_name),
    }


# --- Markdown del resumen -----------------------------------------------------------------


def _percent(value: float | None) -> str:
    return "—" if value is None else f"{100 * value:.1f} %"


def _runs_table(runs: dict[str, Any]) -> list[str]:
    lines = ["| Corrida | Entrada | Reranker | Escenarios | Correctos | % correctos |", "|---|---|---|---|---|---|"]
    for name, run in runs.items():
        reranker = run["models"]["reranker"] or "sin reranker"
        cells = [f"`{name}`", run["input"], reranker, run["scenarios"], run["passed"], _percent(run["pass_rate"])]
        lines.append("| " + " | ".join(map(str, cells)) + " |")
    return [*lines, ""]


def _verdict_table(runs: dict[str, Any]) -> list[str]:
    ids = sorted({scenario for run in runs.values() for scenario in run["verdicts"]})
    lines = ["| Escenario | " + " | ".join(f"`{name}`" for name in runs) + " |", "|---" * (len(runs) + 1) + "|"]
    for scenario in ids:
        marks = [_MARK[run["verdicts"][scenario]] if scenario in run["verdicts"] else "" for run in runs.values()]
        lines.append(f"| `{scenario}` | " + " | ".join(marks) + " |")
    return [*lines, ""]


def _violation_table(runs: dict[str, Any]) -> list[str]:
    lines = ["| Corrida | " + " | ".join(KINDS) + " |", "|---" * (len(KINDS) + 1) + "|"]
    lines += [f"| `{name}` | " + " | ".join(str(run["violations"][kind]) for kind in KINDS) + " |" for name, run in runs.items()]
    return [*lines, ""]


def _latency_table(runs: dict[str, Any]) -> list[str]:
    columns = (*STAGES, TOTAL)
    header = "| Corrida | Turnos | " + " | ".join(STAGE_LABELS[stage] for stage in columns) + " |"
    lines = [header, "|---" * (len(columns) + 2) + "|"]
    for name, run in runs.items():
        for key, label in (("with_llm", "con LLM"), ("without_llm", "sin LLM")):
            stats = run["timings"][key]
            if stats["turns"]:
                cells = " | ".join(f"{stats[stage]['mean']:.2f} (máx. {stats[stage]['max']:.2f})" for stage in columns)
                lines.append(f"| `{name}`, {label} | {stats['turns']} | {cells} |")
    return [*lines, ""]


def _load_lines(runs: dict[str, Any]) -> list[str]:
    lines = []
    for name, run in runs.items():
        load = run["load"]
        parts = [f"catálogo y recuperadores {load['search_seconds']} s", f"LLM {load['llm_seconds']} s"]
        parts += [f"ASR {load['asr_seconds']} s"] if load.get("asr_seconds") is not None else []
        parts += [f"TTS {load['tts_seconds']} s"] if load.get("tts_seconds") is not None else []
        lines.append(f"- `{name}`: {', '.join(parts)}; total {load['total_seconds']} s.")
    return [*lines, ""]


def _voice_lines(run: dict[str, Any]) -> list[str]:
    """Errores del ASR y voz sintetizada de la corrida por audio."""
    metrics = run["voice_metrics"]
    if not metrics:
        return []
    asr, tts = metrics["asr"], metrics["tts"]
    lines = [f"- Audios de entrada: {'; '.join(sorted(set(run['audio_sources'].values())))}."]
    lines.append(f"- ASR: {asr['cases']} turnos, {asr['exact']} idénticos tras normalizar; WER {_percent(asr['wer'])}.")
    for key, label in (("amounts", "importes"), ("quantities", "cantidades"), ("products", "nombres de producto")):
        lines.append(f"- Errores del ASR en {label}: {asr[key]['errors']} de {asr[key]['total']} ({_percent(asr[key]['error_rate'])}).")
    lines.append(f"- Inteligibilidad de la voz generada (WER de Whisper sobre {tts['cases']} respuestas): {_percent(tts['wer'])}.")
    if tts["similarity_mean"] is not None:
        lines.append(f"- Semejanza con la voz de referencia (coseno ECAPA): media {tts['similarity_mean']:.3f}, mínima {tts['similarity_min']:.3f}.")
    return [*lines, ""]


def _comparison_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Escenario | Con audio | Con el texto correcto | Turnos con palabras cambiadas por el ASR | Turnos con operaciones distintas | Misma tienda final |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        cells = [f"`{row['id']}`", _MARK[row["passed_audio"]], _MARK[row["passed_text"]]]
        cells += [str(row["asr_changed_words"] or "ninguno"), str(row["different_operations"] or "ninguno")]
        lines.append("| " + " | ".join([*cells, "sí" if row["same_store"] else "no"]) + " |")
    return [*lines, ""]


def _where(turn: int | str) -> str:
    return "al final" if turn == "final" else f"turno {turn}"


def _failure_lines(runs: dict[str, Any]) -> list[str]:
    lines = []
    for name, run in runs.items():
        for scenario, checks in run["failed_checks"].items():
            lines.append(f"- `{name}` / [{scenario}]({name}/{scenario}.md):")
            lines += [f"  - {_where(check['turn'])}: `{check['check']}` — {check['detail']}" for check in checks]
    return [*(lines or ["- Ninguna."]), ""]


def to_markdown(summary: dict[str, Any]) -> str:
    runs = summary["runs"]
    lines = ["# Evaluación con escenarios: resumen", "", "Cada corrida tiene una ficha por escenario en su carpeta.", ""]
    lines += ["## Escenarios correctos por corrida", "", *_runs_table(runs), *_verdict_table(runs)]
    lines += ["## Violaciones de restricciones", "", *_violation_table(runs)]
    if AUDIO_RUN in runs:
        lines += ["## Voz", "", *_voice_lines(runs[AUDIO_RUN])]
    if summary["audio_vs_correct_text"]:
        lines += ["## Audio frente a transcripción correcta", "", *_comparison_table(summary["audio_vs_correct_text"])]
    lines += ["## Latencia por etapa (segundos por turno, media y máximo)", "", *_latency_table(runs)]
    lines += ["Carga inicial de los modelos, aparte de los turnos:", "", *_load_lines(runs)]
    lines += ["## Comprobaciones que fallaron", "", *_failure_lines(runs)]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume las corridas de escenarios guardadas.")
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    summary = summarize(load_runs(args.dir))
    (args.dir / f"{SUMMARY_NAME}.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (args.dir / f"{SUMMARY_NAME}.md").write_text(to_markdown(summary), encoding="utf-8")
    print(to_markdown(summary))


if __name__ == "__main__":
    main()
