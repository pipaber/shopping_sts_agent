"""Fichas por escenario y resumen de las corridas de evaluación.

Uso, sobre las corridas ya guardadas por ``shopping_agent.eval.scenarios``::

    python -m shopping_agent.eval.scenario_report

Lee ``results/escenarios/<corrida>/`` y escribe ``results/escenarios/resumen.json``
y ``resumen.md``: porcentaje de escenarios correctos por corrida, violaciones de
restricciones, errores del ASR, voz sintetizada, latencia por etapa y la lista de
comprobaciones fallidas, que es el material para analizar aciertos y fallos.

Una corrida por audio se resume además según de dónde salieron los audios de
entrada (grabaciones del usuario o hablante sintético), porque una misma corrida
puede mezclar las dos cosas. ``voz_sintetica`` es la corrida con audio sintético
que se conserva para comparar con la voz real, ``voz_referencia_anterior`` la
corrida con la voz del agente de antes de cambiar su grabación de referencia y
la velocidad del habla, y ``voz_velocidad_1_15`` la de la voz nueva a 1,15, antes
de bajar la velocidad por defecto a 1,10.
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
from shopping_agent.eval.voice import SIMILARITY, SIMILARITY_NOTE, SIMILARITY_REAL, normalize, similarity_lines, summarize_asr, summarize_tts
from shopping_agent.store.ops import format_eur
from shopping_agent.voice.pipeline import STAGES, TOTAL, TTS, VoiceTurn, comparable_store, compare_runs, summarize_timings
from shopping_agent.voice.report import STAGE_LABELS, timing_lines, turn_lines, voice_label

DEFAULT_DIR = Path("results/escenarios")
BASELINE_DIR = Path("results/escenarios_base")  # corridas de antes de corregir el agente
RUN_FILE, SUMMARY_NAME, VOICE_METRICS_FILE = "corrida.json", "resumen", "metricas_voz.json"
AUDIO_RUN, TEXT_REPEAT_RUN, SYNTHETIC_RUN = "voz", "voz_texto_correcto", "voz_sintetica"
PREVIOUS_VOICE_RUNS = ("voz_velocidad_1_15", "voz_referencia_anterior")  # voces del agente anteriores a la actual
RUN_ORDER = ("texto", "texto_sage", "texto_sin_reranker", AUDIO_RUN, TEXT_REPEAT_RUN, *PREVIOUS_VOICE_RUNS, SYNTHETIC_RUN)
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


# --- Una corrida por audio, según de dónde salió el audio ---------------------------------


def _asr_differences(records: list[Record], metrics: dict[str, Any]) -> list[dict[str, Any]]:
    """Los turnos en los que el ASR no entendió el texto dicho, con lo que entendió."""
    return [
        {"scenario": record["id"], "turn": case["turn"], "reference": case["reference"], "hypothesis": case["hypothesis"]}
        for record in records
        for case in metrics[record["id"]]["asr"]["cases"]
        if normalize(case["reference"]) != normalize(case["hypothesis"])
    ]


def _source_entry(source: str, records: list[Record], metrics: dict[str, Any]) -> dict[str, Any]:
    """Aciertos, ASR, voz generada y latencias de los escenarios con una misma procedencia de audio."""

    def cases(kind: str) -> list[dict[str, Any]]:
        return [case for record in records for case in metrics[record["id"]][kind]["cases"]]

    return {
        "source": source,
        "ids": [record["id"] for record in records],
        **run_summary(records),
        "asr": summarize_asr(cases("asr")),
        "tts": summarize_tts(cases("tts")),
        "asr_differences": _asr_differences(records, metrics),
    }


def by_source(run: dict[str, Any]) -> list[dict[str, Any]]:
    """Una corrida por audio partida por la procedencia de sus audios de entrada."""
    if not run["voice_metrics"]:
        return []
    groups: dict[str, list[Record]] = {}
    for record in run["records"]:
        groups.setdefault(record["audio_source"], []).append(record)
    return [_source_entry(source, records, run["voice_metrics"]["scenarios"]) for source, records in groups.items()]


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


def _response_audio_seconds(records: list[Record]) -> float | None:
    """Duración media del audio de las respuestas; ``None`` si la corrida no sintetizó."""
    seconds = [turn["output_seconds"] for record in records for turn in turns_of(record) if turn["output_seconds"]]
    return sum(seconds) / len(seconds) if seconds else None


def _run_entry(run: dict[str, Any]) -> dict[str, Any]:
    """Lo que el resumen guarda de una corrida."""
    records, voice = run["records"], run["voice_metrics"] or {}
    return {
        **{key: run["info"].get(key) for key in _INFO_KEYS},
        **run_summary(records),
        "verdicts": {record["id"]: record["passed"] for record in records},
        "failed_checks": {record["id"]: failed_checks(record) for record in records if not record["passed"]},
        "voice_metrics": voice.get("summary"),
        "real_recordings": voice.get("real_recordings"),
        "response_audio_seconds": _response_audio_seconds(records),
        "by_source": by_source(run),
    }


def _audio_vs_text(runs: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Por cada corrida con audio, sus escenarios frente a la repetición con la transcripción correcta."""
    if TEXT_REPEAT_RUN not in runs:
        return {}
    texts = {record["id"]: record for record in runs[TEXT_REPEAT_RUN]["records"]}
    return {
        name: [compare_with_text(record, texts[record["id"]]) for record in run["records"] if record["id"] in texts]
        for name, run in runs.items()
        if run["voice_metrics"]
    }


def summarize(runs: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {run["name"]: run for run in runs}
    return {
        "runs": {name: _run_entry(run) for name, run in by_name.items()},
        "audio_vs_correct_text": _audio_vs_text(by_name),
    }


def before_after(current: dict[str, Any], baseline: dict[str, Any]) -> list[dict[str, Any]]:
    """Por cada corrida que está en los dos resúmenes: aciertos antes y después, qué
    escenarios se arreglaron y cuáles se rompieron."""
    rows = []
    for name in (name for name in current["runs"] if name in baseline["runs"]):
        old, new = baseline["runs"][name]["verdicts"], current["runs"][name]["verdicts"]
        shared = [scenario for scenario in new if scenario in old]
        rows.append({
            "run": name,
            "scenarios": len(shared),
            "before": sum(old[scenario] for scenario in shared),
            "after": sum(new[scenario] for scenario in shared),
            "fixed": [scenario for scenario in shared if new[scenario] and not old[scenario]],
            "regressions": [scenario for scenario in shared if old[scenario] and not new[scenario]],
            "verdicts": {scenario: [old[scenario], new[scenario]] for scenario in shared},
        })
    return rows


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


def _asr_lines(asr: dict[str, Any]) -> list[str]:
    lines = [f"- ASR: {asr['cases']} turnos, {asr['exact']} idénticos tras normalizar; WER {_percent(asr['wer'])}."]
    for key, label in (("amounts", "importes"), ("quantities", "cantidades"), ("products", "nombres de producto")):
        lines.append(f"- Errores del ASR en {label}: {asr[key]['errors']} de {asr[key]['total']} ({_percent(asr[key]['error_rate'])}).")
    return lines


def _difference_lines(differences: list[dict[str, Any]]) -> list[str]:
    lines = [f"- Turnos en los que el ASR cambió palabras: {len(differences) or 'ninguno'}."]
    lines += [
        f"  - `{found['scenario']}`, turno {found['turn']}: se dijo «{found['reference']}» y entendió «{found['hypothesis']}»."
        for found in differences
    ]
    return lines


def _tts_lines(tts: dict[str, Any], real: dict[str, Any] | None) -> list[str]:
    intelligibility = f"- Inteligibilidad de la voz generada (WER de Whisper sobre {tts['cases']} respuestas): {_percent(tts['wer'])}."
    return [intelligibility, *similarity_lines(tts, real)]


def _latency_line(stats: dict[str, Any]) -> list[str]:
    if not stats["turns"]:
        return []
    stages = ", ".join(f"{STAGE_LABELS[stage]} {stats[stage]['mean']:.2f}" for stage in (*STAGES, TOTAL))
    return [f"- Latencia media por turno con LLM ({stats['turns']} turnos, segundos): {stages}; máximo {stats[TOTAL]['max']:.2f}."]


def _voice_lines(name: str, run: dict[str, Any]) -> list[str]:
    """Una corrida por audio: aciertos, ASR, voz generada y latencia, por procedencia del audio."""
    lines = [f"### `{name}`", ""]
    for entry in run["by_source"]:
        scenarios = ", ".join(scenario[:2] for scenario in entry["ids"])
        lines += [f"**Audios de entrada: {entry['source']}.** Escenarios {scenarios}: {entry['passed']} de {entry['scenarios']} correctos.", ""]
        lines += [*_asr_lines(entry["asr"]), *_difference_lines(entry["asr_differences"])]
        lines += [*_tts_lines(entry["tts"], run.get("real_recordings")), *_latency_line(entry["timings"]["with_llm"]), ""]
    return lines


def _number(value: float | None, digits: int) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def _agent_voice_table(runs: dict[str, Any]) -> list[str]:
    """La voz del agente en cada corrida por audio, lado a lado: sirve para comparar
    una voz con otra (otra referencia, otra velocidad) sobre los mismos escenarios."""
    lines = [
        "| Corrida | Voz del agente | Correctos | Inteligibilidad (WER) | Semejanza con la referencia | Semejanza con las grabaciones reales "
        "| Audio de respuesta (s) | TTS (s por turno) | Total (s por turno) | Total con LLM (s) |",
        "|---" * 10 + "|",
    ]
    for name, run in runs.items():
        tts, timings = run["voice_metrics"]["tts"], run["timings"]
        similarities = [_number(tts.get(f"{key}_mean"), 3) for key in (SIMILARITY, SIMILARITY_REAL)]
        seconds = [run["response_audio_seconds"], timings["all"][TTS]["mean"], timings["all"][TOTAL]["mean"], timings["with_llm"][TOTAL]["mean"]]
        cells = [f"`{name}`", voice_label(run["voice"]), f"{run['passed']} de {run['scenarios']}", _percent(tts["wer"]), *similarities]
        lines.append("| " + " | ".join([*cells, *(_number(value, 2) for value in seconds)]) + " |")
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


def _before_after_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Aciertos por corrida antes y después, y el veredicto de cada escenario en las dos."""
    lines = ["| Corrida | Antes | Después | Arreglados | Regresiones |", "|---|---|---|---|---|"]
    for row in rows:
        fixed, broken = (", ".join(name[:2] for name in row[key]) or "ninguno" for key in ("fixed", "regressions"))
        lines.append(f"| `{row['run']}` | {row['before']} de {row['scenarios']} | {row['after']} de {row['scenarios']} | {fixed} | {broken} |")
    scenarios = sorted({scenario for row in rows for scenario in row["verdicts"]})
    lines += ["", "| Escenario (antes → después) | " + " | ".join(f"`{row['run']}`" for row in rows) + " |", "|---" * (len(rows) + 1) + "|"]
    for scenario in scenarios:
        cells = [" → ".join(_MARK[verdict] for verdict in row["verdicts"][scenario]) if scenario in row["verdicts"] else "" for row in rows]
        lines.append(f"| `{scenario}` | " + " | ".join(cells) + " |")
    return [*lines, ""]


def _voice_section(runs: dict[str, Any]) -> list[str]:
    audio_runs = {name: run for name, run in runs.items() if run.get("by_source")}
    lines = ["## Voz", "", *_agent_voice_table(audio_runs)] if audio_runs else []
    if any(run.get("real_recordings") for run in audio_runs.values()):
        lines += [SIMILARITY_NOTE, ""]
    for name, run in audio_runs.items():
        lines += _voice_lines(name, run)
    return lines


def _comparison_section(comparisons: dict[str, list[dict[str, Any]]]) -> list[str]:
    lines = ["## Audio frente a transcripción correcta", ""] if comparisons else []
    for name, rows in comparisons.items():
        lines += [f"### `{name}`", "", *_comparison_table(rows)]
    return lines


def to_markdown(summary: dict[str, Any]) -> str:
    runs = summary["runs"]
    lines = ["# Evaluación con escenarios: resumen", "", "Cada corrida tiene una ficha por escenario en su carpeta.", ""]
    lines += ["## Escenarios correctos por corrida", "", *_runs_table(runs), *_verdict_table(runs)]
    if summary.get("before_after"):
        lines += ["## Antes y después de corregir el agente", "", f"Línea base: `{summary['baseline']}`.", ""]
        lines += _before_after_lines(summary["before_after"])
    lines += ["## Violaciones de restricciones", "", *_violation_table(runs)]
    lines += [*_voice_section(runs), *_comparison_section(summary["audio_vs_correct_text"])]
    lines += ["## Latencia por etapa (segundos por turno, media y máximo)", "", *_latency_table(runs)]
    lines += ["Carga inicial de los modelos, aparte de los turnos:", "", *_load_lines(runs)]
    lines += ["## Comprobaciones que fallaron", "", *_failure_lines(runs)]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume las corridas de escenarios guardadas.")
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--baseline", type=Path, default=BASELINE_DIR, help="corridas anteriores con las que comparar")
    args = parser.parse_args()
    summary = summarize(load_runs(args.dir))
    if args.baseline.is_dir():
        summary.update(baseline=str(args.baseline), before_after=before_after(summary, summarize(load_runs(args.baseline))))
    (args.dir / f"{SUMMARY_NAME}.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (args.dir / f"{SUMMARY_NAME}.md").write_text(to_markdown(summary), encoding="utf-8")
    print(to_markdown(summary))


if __name__ == "__main__":
    main()
