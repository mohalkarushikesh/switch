"""Logging setup and lightweight per-run timing."""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager

from advanced_rag.models import TraceStep

_CONFIGURED = False


def setup_logging(level: str = "INFO") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    # These are chatty at INFO and drown out the pipeline's own logs.
    for noisy in ("httpx", "httpcore", "anthropic", "urllib3", "qdrant_client"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _CONFIGURED = True


_DEGRADED_SEEN: set[str] = set()


def log_degraded(logger: logging.Logger, key: str, message: str, exc: BaseException) -> None:
    """Report a handled degradation: in full once, then one line per occurrence.

    `logger.exception` on an expected fallback is a real problem, not just noise.
    HyDE failing on 15 eval cases emitted 15 identical 40-line tracebacks and
    buried the results table completely. The first occurrence still carries the
    stack trace, because that is what you need to diagnose an unexpected cause.
    """
    summary = f"{message}: {type(exc).__name__}: {str(exc).splitlines()[0][:160]}"
    if key in _DEGRADED_SEEN:
        logger.warning("%s (repeat)", summary)
        return
    _DEGRADED_SEEN.add(key)
    logger.warning(summary, exc_info=logger.isEnabledFor(logging.DEBUG))
    logger.debug("Full traceback for %s", key, exc_info=exc)


def reset_degraded_log() -> None:
    """Test hook - forget which degradations have already been reported."""
    _DEGRADED_SEEN.clear()


@contextmanager
def timed(trace: list[TraceStep], node: str, detail: str = ""):
    """Append a TraceStep for a graph node, recording its wall time.

    The step is written on the way out even if the node raises, so a failed run
    still shows how far the pipeline got.
    """
    start = time.perf_counter()
    step = TraceStep(node=node, detail=detail)
    try:
        yield step
    finally:
        step.elapsed_ms = int((time.perf_counter() - start) * 1000)
        trace.append(step)
