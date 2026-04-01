import logging
import time
from typing import Callable, TypeVar

from workflow.utils.logging import log_event

T = TypeVar("T")


def retry_call(
    func: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 1.0,
    backoff: float = 2.0,
    sleep: Callable[[float], None] = time.sleep,
    logger: logging.Logger | None = None,
    operation: str = "operation",
) -> T:
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    for attempt in range(1, attempts + 1):
        try:
            return func()
        except Exception as exc:
            is_last = attempt >= attempts
            if logger is not None:
                log_event(
                    logger,
                    logging.WARNING,
                    "retry.error",
                    operation=operation,
                    attempt=attempt,
                    attempts=attempts,
                    is_last=is_last,
                    error=str(exc),
                )
            if is_last:
                raise
            delay = max(base_delay * (backoff ** (attempt - 1)), 0)
            if logger is not None:
                log_event(
                    logger,
                    logging.INFO,
                    "retry.sleep",
                    operation=operation,
                    attempt=attempt,
                    sleep_seconds=delay,
                )
            sleep(delay)

    # Unreachable
    raise RuntimeError("retry_call reached an unexpected state")

