from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable


class PolicyViolation(ValueError):
    """Azione o dato bloccato da una policy deterministica."""


@dataclass(slots=True)
class Guardrail:
    """Collezione di controlli puri: ogni policy restituisce True oppure una motivazione."""

    policies: list[Callable[[Any], bool | str]] = field(default_factory=list)

    def add(self, policy: Callable[[Any], bool | str]) -> None:
        self.policies.append(policy)

    def validate(self, value: Any) -> Any:
        violations: list[str] = []
        for policy in self.policies:
            verdict = policy(value)
            if verdict is True:
                continue
            violations.append(verdict if isinstance(verdict, str) else policy.__name__)
        if violations:
            raise PolicyViolation("; ".join(violations))
        return value


def require_fields(fields: Iterable[str]) -> Callable[[Any], bool | str]:
    required = tuple(fields)

    def policy(value: Any) -> bool | str:
        if not isinstance(value, dict):
            return "output non strutturato come dizionario"
        missing = [field for field in required if field not in value]
        return True if not missing else f"campi mancanti: {', '.join(missing)}"

    return policy


def max_numeric(field: str, maximum: float) -> Callable[[Any], bool | str]:
    def policy(value: Any) -> bool | str:
        if not isinstance(value, dict) or field not in value:
            return f"campo {field!r} assente"
        try:
            number = float(value[field])
        except (TypeError, ValueError):
            return f"campo {field!r} non numerico"
        return True if number <= maximum else f"{field}={number} supera il limite {maximum}"

    return policy
