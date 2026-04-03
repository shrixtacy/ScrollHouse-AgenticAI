"""
Scrollhouse Logging & LangSmith Tracing Utilities

Provides:
    - Standard Python logger for structured console/file output
    - A LangSmith tracing decorator that wraps each graph node
"""

from __future__ import annotations

import functools
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable

from langsmith import traceable

# ── Configure root logger ────────────────────────────────────────────────────

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

logger = logging.getLogger("scrollhouse.ps01")


# ── LangSmith tracing wrapper ────────────────────────────────────────────────

def traced_node(
    node_name: str,
    *,
    run_type: str = "chain",
    project_name: str | None = None,
) -> Callable:
    """
    Decorator that wraps a LangGraph node function with LangSmith tracing.

    Usage::

        @traced_node("validate_input")
        def validate_input(state: OnboardingState) -> dict:
            ...
    """
    project = project_name or os.getenv("LANGSMITH_PROJECT", "scrollhouse-ps01")

    def decorator(fn: Callable) -> Callable:
        # Apply LangSmith's @traceable first
        traced_fn = traceable(
            name=node_name,
            run_type=run_type,
            project_name=project,
        )(fn)

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.info("▶ Node [%s] started", node_name)
            start = datetime.now(timezone.utc)
            try:
                result = traced_fn(*args, **kwargs)
                elapsed = (datetime.now(timezone.utc) - start).total_seconds()
                logger.info(
                    "✔ Node [%s] completed in %.2fs",
                    node_name,
                    elapsed,
                )
                return result
            except Exception:
                elapsed = (datetime.now(timezone.utc) - start).total_seconds()
                logger.exception(
                    "✘ Node [%s] raised after %.2fs",
                    node_name,
                    elapsed,
                )
                raise

        return wrapper

    return decorator
