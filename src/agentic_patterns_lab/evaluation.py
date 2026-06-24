from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .contracts import StepResult


@dataclass(slots=True)
class EvaluationReport:
    passed: bool
    scores: dict[str, float] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)


def evaluate_result(
    result: StepResult,
    checks: Mapping[str, Callable[[Any], bool | float]],
) -> EvaluationReport:
    failures: list[str] = []
    scores: dict[str, float] = {}
    if not result.ok:
        return EvaluationReport(False, failures=[result.error or "step fallito"])

    for name, check in checks.items():
        verdict = check(result.value)
        if isinstance(verdict, bool):
            scores[name] = 1.0 if verdict else 0.0
            if not verdict:
                failures.append(name)
        else:
            score = float(verdict)
            scores[name] = score
            if score < 1.0:
                failures.append(name)
    return EvaluationReport(not failures, scores=scores, failures=failures)
