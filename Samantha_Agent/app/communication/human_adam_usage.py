"""Read projection of one owned work and its explicitly bound helper receipts."""
from __future__ import annotations

from datetime import datetime, timezone
from app.codex_usage import label, measurement_projection
from app.release_usage import TOKEN_KEYS, normalize_usage


def helper_projection(value):
    if not isinstance(value, dict):
        return None
    executor = value.get("executor") if isinstance(value.get("executor"), dict) else {}
    duration = value.get("duration_ms")
    return {"model": label(executor.get("model")), "effort": label(executor.get("reasoning_effort")),
            "job_id": label(value.get("job_id")), "usage": normalize_usage(value.get("model_usage")),
            "duration_ms": duration if type(duration) is int and duration >= 0 else None}


def usage_projection(record):
    main = measurement_projection(record.get("_model_usage"))
    if main and (main["thread_id"] != record["thread_id"] or main["turn_id"] != record["turn_id"]):
        main = None
    components = [{"kind": "adam", "model": main["model"] if main else None,
                   "usage": main["usage"] if main else None, "complete": bool(main and main["complete"]),
                   "duration_ms": main["duration_ms"] if main else None,
                   "baseline": main["baseline"] if main else None,
                   "thread_total": main["thread_total"] if main else None,
                   "reason": main["reason"] if main else "telemetry_unavailable"}]
    helpers = record.get("_helper_usage")
    if isinstance(helpers, dict):
        for identity, raw in sorted(helpers.items())[:8]:
            safe = helper_projection(raw)
            if safe is not None:
                components.append({"kind": "helper", "helper_id": label(identity), **safe,
                                   "complete": safe["usage"] is not None and safe["model"] is not None})
    known = [c["usage"] for c in components if c["usage"] is not None]
    usage = {k: sum(c[k] for c in known) for k in TOKEN_KEYS} if known else None
    terminal = record["lifecycle_state"] in {"completed", "failed", "not_dispatched", "interrupted"}
    duration = None
    try:
        start = datetime.fromisoformat(record["created_at"])
        end = datetime.fromisoformat(record["updated_at"]) if terminal else datetime.now(timezone.utc)
        elapsed = (end - start).total_seconds()
        duration = round(elapsed * 1000) if elapsed >= 0 else None
    except (ValueError, TypeError):
        pass
    return {"schema_version": 1, "source": "owned_work_measurements",
            "coverage": "owned_turn_and_registered_portal_helpers", "components": components,
            "recorded_usage": usage, "complete": record.get("_usage_finalized") is True
                and all(c["complete"] for c in components),
            "elapsed_ms": duration, "elapsed_final": terminal,
            # No current, verified price table is configured for this projection.
            "price": {"amount": None, "currency": None, "price_version": None,
                      "reason": "not_configured"}}
