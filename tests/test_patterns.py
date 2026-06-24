from agentic_patterns_lab import AgentContext, ParallelExecutor, Reflector, StepResult
from agentic_patterns_lab.guardrails import Guardrail, PolicyViolation, max_numeric, require_fields
from agentic_patterns_lab.patterns import Router, SequentialPipeline


def test_sequential_pipeline_passes_output() -> None:
    def add_one(context, value):
        return StepResult.success(value + 1)

    pipeline = SequentialPipeline([("a", add_one), ("b", add_one)])
    result = pipeline.run(AgentContext(goal="test"), 1)
    assert result.ok
    assert result.value == 3


def test_router_selects_specialist() -> None:
    router = Router(
        {"number": lambda context, payload: StepResult.success(payload * 2)},
        selector=lambda context, payload: "number" if isinstance(payload, int) else "other",
    )
    result = router.run(AgentContext(goal="route"), 4)
    assert result.value == 8


def test_parallel_executor_preserves_worker_names() -> None:
    executor = ParallelExecutor(
        {
            "one": lambda context, payload: StepResult.success(payload + 1),
            "two": lambda context, payload: StepResult.success(payload + 2),
        }
    )
    result = executor.run(AgentContext(goal="parallel"), 10)
    assert result.ok
    assert result.value["one"].value == 11
    assert result.value["two"].value == 12


def test_reflector_accepts_checked_output() -> None:
    def maker(context, payload):
        return StepResult.success({"claim": payload, "sources": 2})

    def checker(context, draft):
        return StepResult.success({"accepted": draft["sources"] >= 2})

    result = Reflector(maker, checker).run(AgentContext(goal="verify"), "x")
    assert result.ok
    assert result.value.accepted is True


def test_guardrail_rejects_excessive_position() -> None:
    guardrail = Guardrail(
        [require_fields(["asset", "position_pct"]), max_numeric("position_pct", 2.0)]
    )
    assert guardrail.validate({"asset": "BTC", "position_pct": 1.0})["asset"] == "BTC"
    try:
        guardrail.validate({"asset": "BTC", "position_pct": 3.0})
    except PolicyViolation as exc:
        assert "supera il limite" in str(exc)
    else:
        raise AssertionError("La policy avrebbe dovuto bloccare il valore")
