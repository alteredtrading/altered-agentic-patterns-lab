from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Protocol

from .contracts import AgentContext, StepResult


class AgentFn(Protocol):
    def __call__(self, context: AgentContext, payload: Any) -> StepResult: ...


class SequentialPipeline:
    """Prompt chaining generalizzato: l'output di uno step diventa l'input del successivo."""

    def __init__(self, steps: Iterable[tuple[str, AgentFn]]) -> None:
        self.steps = list(steps)
        if not self.steps:
            raise ValueError("La pipeline deve contenere almeno uno step")

    def run(self, context: AgentContext, initial_payload: Any) -> StepResult:
        payload = initial_payload
        for name, step in self.steps:
            context.record(name, "started")
            result = step(context, payload)
            if not isinstance(result, StepResult):
                raise TypeError(f"Lo step {name!r} non ha restituito StepResult")
            if not result.ok:
                context.record(name, "failed", result.error or "errore non specificato")
                return result
            payload = result.value
            context.record(name, "completed")
        return StepResult.success(payload)


class Router:
    """Seleziona uno specialista mediante una funzione di classificazione deterministica o LLM."""

    def __init__(
        self,
        routes: Mapping[str, AgentFn],
        selector: Callable[[AgentContext, Any], str],
        *,
        fallback: AgentFn | None = None,
    ) -> None:
        self.routes = dict(routes)
        self.selector = selector
        self.fallback = fallback

    def run(self, context: AgentContext, payload: Any) -> StepResult:
        route = self.selector(context, payload)
        agent = self.routes.get(route, self.fallback)
        context.record("router", "selected", metadata={"route": route})
        if agent is None:
            return StepResult.failure(f"Nessuna route disponibile per {route!r}")
        return agent(context, payload)


class ParallelExecutor:
    """Esegue analisi indipendenti in parallelo e conserva risultati ed errori."""

    def __init__(self, workers: Mapping[str, AgentFn], *, max_workers: int | None = None) -> None:
        self.workers = dict(workers)
        self.max_workers = max_workers or max(1, len(self.workers))

    def run(self, context: AgentContext, payload: Any) -> StepResult:
        results: dict[str, StepResult] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            future_to_name = {
                pool.submit(worker, context, payload): name for name, worker in self.workers.items()
            }
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    results[name] = future.result()
                except Exception as exc:  # noqa: BLE001 - confine di recupero intenzionale
                    results[name] = StepResult.failure(f"{type(exc).__name__}: {exc}")
                context.record(
                    f"parallel:{name}",
                    "completed" if results[name].ok else "failed",
                    results[name].error or "",
                )
        return StepResult.success(results)


@dataclass(slots=True)
class ReflectionOutcome:
    accepted: bool
    draft: Any
    critique: Any
    revision: Any | None = None


class Reflector:
    """Maker-checker: un produttore genera, un verificatore indipendente giudica."""

    def __init__(
        self,
        maker: AgentFn,
        checker: AgentFn,
        reviser: AgentFn | None = None,
        *,
        max_rounds: int = 2,
    ) -> None:
        if max_rounds < 1:
            raise ValueError("max_rounds deve essere almeno 1")
        self.maker = maker
        self.checker = checker
        self.reviser = reviser
        self.max_rounds = max_rounds

    def run(self, context: AgentContext, payload: Any) -> StepResult:
        draft_result = self.maker(context, payload)
        if not draft_result.ok:
            return draft_result
        draft = draft_result.value

        for round_number in range(1, self.max_rounds + 1):
            check = self.checker(context, draft)
            if not check.ok:
                return check
            verdict = check.value
            accepted = bool(verdict.get("accepted")) if isinstance(verdict, dict) else bool(verdict)
            context.record(
                "reflection",
                "accepted" if accepted else "revision_requested",
                metadata={"round": round_number},
            )
            if accepted:
                return StepResult.success(
                    ReflectionOutcome(True, draft=draft, critique=verdict),
                    confidence=check.confidence,
                    evidence=check.evidence,
                )
            if self.reviser is None:
                return StepResult.failure("Il checker ha rifiutato il risultato e manca un reviser")
            revision = self.reviser(context, {"draft": draft, "critique": verdict})
            if not revision.ok:
                return revision
            draft = revision.value

        return StepResult.success(
            ReflectionOutcome(False, draft=draft, critique="max_rounds raggiunto", revision=draft)
        )


@dataclass(slots=True)
class PlanStep:
    name: str
    action: AgentFn
    completion_check: Callable[[StepResult], bool] = lambda result: result.ok


class Planner:
    """Esegue un piano esplicito e verifica ogni criterio di completamento."""

    def __init__(self, steps: Iterable[PlanStep]) -> None:
        self.steps = list(steps)

    def run(self, context: AgentContext, payload: Any) -> StepResult:
        current = payload
        completed: list[str] = []
        for step in self.steps:
            result = step.action(context, current)
            if not step.completion_check(result):
                context.record(step.name, "incomplete", result.error or "criterio non soddisfatto")
                return StepResult.failure(
                    f"Criterio di completamento non soddisfatto: {step.name}",
                    metadata={"completed": completed},
                )
            completed.append(step.name)
            current = result.value
            context.record(step.name, "completed")
        return StepResult.success(current, metadata={"completed": completed})
