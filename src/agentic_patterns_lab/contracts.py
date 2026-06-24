from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class TraceEvent:
    """Evento append-only utile per audit, debugging e valutazione."""

    stage: str
    status: str
    detail: str = ""
    timestamp: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AgentContext:
    """Contesto condiviso, intenzionalmente piccolo e serializzabile."""

    goal: str
    inputs: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)
    trace: list[TraceEvent] = field(default_factory=list)
    run_id: str = field(default_factory=lambda: str(uuid4()))

    def record(
        self,
        stage: str,
        status: str,
        detail: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        self.trace.append(
            TraceEvent(
                stage=stage,
                status=status,
                detail=detail,
                metadata=dict(metadata or {}),
            )
        )


@dataclass(slots=True)
class StepResult:
    """Contratto standard tra passaggi: niente stringhe ambigue come unico output."""

    ok: bool
    value: Any = None
    error: str | None = None
    confidence: float | None = None
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(
        cls,
        value: Any,
        *,
        confidence: float | None = None,
        evidence: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "StepResult":
        return cls(
            ok=True,
            value=value,
            confidence=confidence,
            evidence=evidence or [],
            metadata=metadata or {},
        )

    @classmethod
    def failure(cls, error: str, *, metadata: dict[str, Any] | None = None) -> "StepResult":
        return cls(ok=False, error=error, metadata=metadata or {})
