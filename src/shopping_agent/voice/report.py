"""Transcripción en Markdown de una conversación por voz."""

from __future__ import annotations

from typing import Any

from shopping_agent.agent.report import operation_lines, store_lines
from shopping_agent.agent.session import LLM, RETRIEVAL, TOOLS
from shopping_agent.voice.pipeline import ASR, STAGES, TOTAL, TTS

STAGE_LABELS = {ASR: "ASR", RETRIEVAL: "Recuperación", LLM: "LLM", TOOLS: "Herramientas", TTS: "TTS", TOTAL: "Total"}
SUMMARY_ROWS = (("with_llm", "Media de los turnos con LLM"), ("without_llm", "Media de los turnos sin LLM"))


def voice_label(voice: dict[str, Any]) -> str:
    """De dónde sale la voz y a qué velocidad habla. Las corridas guardadas antes de
    que la velocidad fuera un ajuste no la anotan: iban a 1,0."""
    speed = f", velocidad del habla {voice['speed']:.2f}".replace(".", ",") if voice.get("speed") else ""
    if voice.get("reference"):
        return f"clonada de la grabación de referencia `{voice['reference']}`{speed}"
    if voice.get("speaker"):
        return f"hablante incluido en XTTS-v2 «{voice['speaker']}»{speed}"
    return "sin síntesis"


def header_lines(record: dict[str, Any]) -> list[str]:
    models, load = record["models"], record["load"]
    note = [f"- Nota: {record['note']}"] if record.get("note") else []
    return [
        "# Transcripción de una compra por voz",
        "",
        f"- Fecha: {record['date']}",
        *note,
        f"- LLM: `{models['llm']}`; ASR: `{models['asr']}`; TTS: `{models['tts']}`; embeddings: `{models['embeddings']}`",
        f"- Voz del agente: {voice_label(record['voice'])}",
        f"- Carga inicial: catálogo y recuperadores {load['search_seconds']} s, LLM {load['llm_seconds']} s, "
        f"ASR {load['asr_seconds']} s, TTS {load['tts_seconds']} s; total {load['total_seconds']} s",
        f"- VRAM del proceso: {load['vram_mib']['loaded']} MiB con todo cargado, "
        f"{load['vram_mib']['after_run']} MiB al terminar la conversación",
        f"- Memoria del agente: {record['memory_backend']}; hilo `{record['thread_id']}`",
        "",
    ]


def timing_lines(record: dict[str, Any]) -> list[str]:
    """Tabla de latencias: una fila por turno y las medias con y sin LLM."""
    columns = (*STAGES, TOTAL)
    lines = [
        "## Latencia por turno (segundos)",
        "",
        "| Turno | " + " | ".join(STAGE_LABELS[stage] for stage in columns) + " | Audio de respuesta |",
        "|---" * (len(columns) + 2) + "|",
    ]
    for turn in record["turns"]:
        cells = " | ".join(f"{turn['timings'][stage]:.2f}" for stage in columns)
        lines.append(f"| {turn['turn']} | {cells} | {turn['output_seconds'] or 0:.1f} s |")
    for key, label in SUMMARY_ROWS:
        stats = record["timings"][key]
        if stats["turns"]:
            cells = " | ".join(f"{stats[stage]['mean']:.2f}" for stage in columns)
            lines.append(f"| **{label} ({stats['turns']})** | {cells} | |")
    return [*lines, ""]


def turn_lines(turn: dict[str, Any]) -> list[str]:
    lines = [f"## Turno {turn['turn']} ({turn['timings'][TOTAL]:.1f} s)", ""]
    if turn["transcript"] is None:
        lines += [f"**Usuario (texto):** {turn['agent_input']}", ""]
    else:
        lines += [f"**Usuario (transcripción del ASR):** {turn['transcript']}", ""]
        if turn["expected_text"] and turn["expected_text"] != turn["transcript"]:
            lines += [f"**Texto correcto:** {turn['expected_text']}", ""]
    waiting = " *(esperando confirmación)*" if turn["awaiting_confirmation"] else ""
    lines += operation_lines(turn["operations"])
    return [*lines, f"**Agente:** {turn['response']}{waiting}", "", f"**Enviado al TTS:** {turn['spoken_text']}", ""]


def repeat_lines(text_run: dict[str, Any]) -> list[str]:
    """Qué cambió al repetir la conversación con el texto correcto en lugar del audio."""
    comparison = text_run["comparison"]

    def turns_where(condition: Any) -> Any:
        return [row["turn"] for row in comparison if condition(row)] or "ninguno"

    return [
        "",
        "## Misma conversación con las transcripciones correctas",
        "",
        f"- Turnos en los que el ASR cambió alguna palabra: {turns_where(lambda row: not row['same_words'])}",
        "- Turnos en los que solo cambió la forma de escribirlo (mayúsculas, puntuación, cifras): "
        f"{turns_where(lambda row: row['same_words'] and not row['same_input'])}",
        f"- Turnos en los que el agente hizo operaciones distintas: {turns_where(lambda row: not row['same_operations'])}",
        f"- Estado final de la tienda igual que con audio: {'sí' if text_run['same_store'] else 'no'}",
    ]


def to_markdown(record: dict[str, Any]) -> str:
    lines = header_lines(record) + timing_lines(record)
    for turn in record["turns"]:
        lines += turn_lines(turn)
    lines += store_lines(record["store"])
    if record.get("text_run"):
        lines += repeat_lines(record["text_run"])
    return "\n".join(lines) + "\n"
