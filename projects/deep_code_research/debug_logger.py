"""
Lightweight debug logger that writes NDJSON lines to the shared debug log.

Designed for quick instrumentation without external dependencies.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Log path provided by system reminder
DEBUG_LOG_PATH = Path(__file__).resolve().parents[2] / ".cursor" / "debug.log"


def log_event(
    *,
    location: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    session_id: str = "debug-session",
    run_id: Optional[str] = None,
    hypothesis_id: str = "H0",
) -> None:
    """
    Append a single NDJSON log line.

    Keeps failures silent to avoid breaking the main flow.
    """
    payload = {
        "sessionId": session_id,
        "runId": run_id or os.environ.get("DEBUG_RUN_ID") or "run1",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": _safe_data(data),
        "timestamp": int(time.time() * 1000),
    }

    try:
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        # Fail silently; logging must never break execution
        pass


def _safe_data(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Ensure data is JSON-serializable; fall back to string repr."""
    if data is None:
        return {}

    safe = {}
    for k, v in data.items():
        try:
            json.dumps(v)
            safe[k] = v
        except TypeError:
            safe[k] = repr(v)
    return safe

