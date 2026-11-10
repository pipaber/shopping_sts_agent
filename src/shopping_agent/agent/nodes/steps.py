"""Anotación de los pasos del turno: lo que el LLM decidió y lo que el código hizo."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from shopping_agent.agent import prompt
from shopping_agent.agent.state import AgentState, Step, Update, decision_args, issue_record
from shopping_agent.store.ops import Issue


def step(state: AgentState, ok: bool, summary: str, result: Any = None, issues: Iterable[Issue] = ()) -> Step:
    """El paso que corresponde a la decisión en curso."""
    decision = state.decision
    return Step(
        turn=state.turn,
        tool=str(decision.get("herramienta")),
        args=decision_args(decision),
        reason=str(decision.get("motivo", "")),
        ok=ok,
        summary=summary,
        result=result,
        issues=[issue_record(issue) for issue in issues],
    )


def record(state: AgentState, entry: Step, **update: Any) -> Update:
    """Añade el paso a los del turno (los ve el LLM) y al registro de operaciones."""
    return {"steps": [*state.steps, entry], "ops_log": [entry], **update}


def rejected(state: AgentState, issues: Iterable[Issue], **update: Any) -> Update:
    """Anota que la decisión en curso se rechazó, con sus motivos."""
    issues = tuple(issues)
    return record(state, step(state, False, prompt.rejection(issues), issues=issues), **update)
