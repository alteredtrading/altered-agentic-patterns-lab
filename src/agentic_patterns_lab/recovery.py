from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    attempts: int = 3
    initial_delay_seconds: float = 0.05
    multiplier: float = 2.0
    max_delay_seconds: float = 1.0

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValueError("attempts deve essere almeno 1")


def run_with_retry(
    operation: Callable[[], T],
    policy: RetryPolicy = RetryPolicy(),
    *,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    delay = policy.initial_delay_seconds
    last_error: BaseException | None = None
    for attempt in range(1, policy.attempts + 1):
        try:
            return operation()
        except retry_on as exc:
            last_error = exc
            if attempt == policy.attempts:
                break
            time.sleep(delay)
            delay = min(delay * policy.multiplier, policy.max_delay_seconds)
    assert last_error is not None
    raise last_error
