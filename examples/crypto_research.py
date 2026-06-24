"""Demo sicura: ricerca parallela + maker-checker, senza esecuzione di ordini."""

from __future__ import annotations

from agentic_patterns_lab import AgentContext, ParallelExecutor, Reflector, StepResult


def market_structure(context: AgentContext, payload: dict) -> StepResult:
    prices = payload["prices"]
    direction = "rialzista" if prices[-1] > prices[0] else "ribassista"
    return StepResult.success({"dimensione": "struttura", "direzione": direction})


def volatility(context: AgentContext, payload: dict) -> StepResult:
    prices = payload["prices"]
    returns = [(b / a) - 1 for a, b in zip(prices, prices[1:], strict=False)]
    avg_abs_move = sum(abs(value) for value in returns) / max(1, len(returns))
    return StepResult.success({"dimensione": "volatilità", "media_assoluta": avg_abs_move})


def positioning(context: AgentContext, payload: dict) -> StepResult:
    funding = float(payload.get("funding", 0.0))
    crowding = "long" if funding > 0.0005 else "short" if funding < -0.0005 else "neutrale"
    return StepResult.success({"dimensione": "posizionamento", "crowding": crowding})


def make_thesis(context: AgentContext, payload: dict) -> StepResult:
    analyses = payload["analyses"]
    structure = analyses["structure"].value
    vol = analyses["volatility"].value
    pos = analyses["positioning"].value
    thesis = {
        "asset": payload["asset"],
        "bias": structure["direzione"],
        "risk_flag": "alto" if vol["media_assoluta"] > 0.03 else "normale",
        "crowding": pos["crowding"],
        "evidence_count": 3,
    }
    return StepResult.success(thesis, confidence=0.72)


def check_thesis(context: AgentContext, thesis: dict) -> StepResult:
    required = {"asset", "bias", "risk_flag", "crowding", "evidence_count"}
    missing = sorted(required - set(thesis))
    accepted = not missing and thesis["evidence_count"] >= 3
    return StepResult.success(
        {
            "accepted": accepted,
            "missing": missing,
            "reason": "contratto valido" if accepted else "tesi incompleta",
        },
        confidence=1.0,
    )


def main() -> None:
    context = AgentContext(goal="Produrre una tesi di mercato verificata")
    payload = {
        "asset": "BTC",
        "prices": [100.0, 101.5, 100.8, 103.2, 104.0],
        "funding": 0.0007,
    }

    parallel = ParallelExecutor(
        {
            "structure": market_structure,
            "volatility": volatility,
            "positioning": positioning,
        }
    )
    analysis_result = parallel.run(context, payload)
    if not analysis_result.ok:
        raise RuntimeError(analysis_result.error)

    reflector = Reflector(make_thesis, check_thesis)
    verified = reflector.run(
        context,
        {"asset": payload["asset"], "analyses": analysis_result.value},
    )
    print(verified.value)
    print(f"Eventi di trace: {len(context.trace)}")


if __name__ == "__main__":
    main()
