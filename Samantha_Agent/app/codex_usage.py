"""Numeric per-turn measurement from cumulative counters; no billing assumptions."""
from __future__ import annotations

import re
from app.release_usage import TOKEN_KEYS, normalize_usage


def label(value):
    return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9._:/-]{1,128}", value) else None


class UsageMeter:
    def __init__(self, thread_id, *, model=None, effort=None, service_tier=None, anchor=None):
        self.thread_id, self.turn_id = thread_id, ""
        self.context = (label(model), label(effort), label(service_tier))
        self.baseline, self.total = None, None
        self.reason = "baseline_unavailable"
        self.fault = False
        if isinstance(anchor, dict):
            if anchor.get("fresh") is True or anchor.get("context") == self.context:
                self.baseline = normalize_usage(anchor.get("total"))
            else:
                self.reason = "context_changed"

    def observe(self, total):
        checked = normalize_usage(total)
        previous = self.total if self.total is not None else self.baseline
        if checked is None:
            self.fault, self.reason = True, "telemetry_unavailable"
        elif previous is not None and any(checked[k] < previous[k] for k in TOKEN_KEYS):
            self.fault, self.reason = True, "counter_reset"
        self.total = checked

    def snapshot(self, *, terminal=False, duration_ms=None):
        delta = None
        if not self.fault and self.baseline is not None and self.total is not None:
            delta = normalize_usage({k: self.total[k] - self.baseline[k] for k in TOKEN_KEYS})
        complete = bool(terminal and delta is not None and self.context[0])
        reason = ("complete" if complete else self.reason if self.fault or self.baseline is None
                  else "model_unknown" if not self.context[0] else "in_progress" if not terminal
                  else "telemetry_unavailable")
        return {"schema_version": 1, "source": "app_server_cumulative_delta",
                "thread_id": self.thread_id, "turn_id": self.turn_id,
                **dict(zip(("model", "effort", "service_tier"), self.context)),
                "baseline": self.baseline, "thread_total": self.total, "usage": delta,
                "complete": complete, "terminal": terminal, "reason": reason,
                "duration_ms": duration_ms if type(duration_ms) is int and duration_ms >= 0 else None}

    def anchor(self, *, terminal):
        if terminal and not self.fault and self.total is not None:
            return {"context": self.context, "total": self.total}
        return None


def measurement_projection(value):
    """Recompute the delta and expose only a bounded, numeric protocol receipt."""
    if (not isinstance(value, dict) or value.get("schema_version") != 1
            or value.get("source") != "app_server_cumulative_delta"
            or not label(value.get("thread_id")) or not label(value.get("turn_id"))
            or type(value.get("terminal")) is not bool or type(value.get("complete")) is not bool):
        return None
    allowed = {"complete", "baseline_unavailable", "context_changed", "counter_reset",
               "telemetry_unavailable", "model_unknown", "in_progress"}
    if value.get("reason") not in allowed:
        return None
    baseline, total = normalize_usage(value.get("baseline")), normalize_usage(value.get("thread_total"))
    meter = UsageMeter(value["thread_id"], model=value.get("model"), effort=value.get("effort"),
                       service_tier=value.get("service_tier"))
    meter.turn_id, meter.baseline, meter.total = value["turn_id"], baseline, total
    meter.reason = value["reason"]
    meter.fault = value["reason"] in {"counter_reset", "telemetry_unavailable"}
    result = meter.snapshot(terminal=value["terminal"], duration_ms=value.get("duration_ms"))
    if result["complete"] != value["complete"] or result["usage"] != value.get("usage"):
        return None
    return result
