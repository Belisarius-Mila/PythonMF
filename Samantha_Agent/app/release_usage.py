"""Numeric-only release measurements; no prompts, answers or credentials."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


TOKEN_KEYS = ("input_tokens", "cached_input_tokens", "output_tokens",
              "reasoning_output_tokens", "total_tokens")
# Standard Codex credits / 1M tokens, checked 2026-10-17. Not a billing receipt.
STANDARD_RATES = {
    "gpt-6-astra": (250, 25, 1250),
    "gpt-6.1-sol": (50, 2.5, 250),
    "gpt-6-sol": (50, 5, 250),
    "gpt-6-luna": (2.5, .25, 12.5),
}


def normalize_usage(value: Any, *, camel_case: bool = False) -> dict[str, int] | None:
    """Missing/invalid telemetry stays unknown and cannot affect delivery."""
    if not isinstance(value, dict):
        return None
    aliases = ("inputTokens", "cachedInputTokens", "outputTokens",
               "reasoningOutputTokens", "totalTokens") if camel_case else TOKEN_KEYS
    result = {key: value.get(alias) for key, alias in zip(TOKEN_KEYS, aliases)}
    if any(type(number) is not int or number < 0 for number in result.values()):
        return None
    if (result["cached_input_tokens"] > result["input_tokens"]
            or result["reasoning_output_tokens"] > result["output_tokens"]
            or result["total_tokens"] != result["input_tokens"] + result["output_tokens"]):
        return None
    return result


def estimate_standard_credits(model: str, usage: Any) -> float | None:
    """Cached input and reasoning are subsets, never counted twice."""
    checked = normalize_usage(usage)
    rates = STANDARD_RATES.get(model)
    if checked is None or rates is None:
        return None
    fresh, cached, output = rates
    return round(((checked["input_tokens"] - checked["cached_input_tokens"]) * fresh
                  + checked["cached_input_tokens"] * cached
                  + checked["output_tokens"] * output) / 1_000_000, 8)


def native_usage_snapshot(thread_id: str, *, sessions_root: Path | None = None) -> dict[str, Any]:
    """Registered read-only projection for one explicitly selected native thread.

    Only turn configuration and token_count metadata leave the private log.
    It is never an account-wide or all-conversation scan.
    """
    if not re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", thread_id):
        raise ValueError("Neplatná identita měřené relace.")
    root = sessions_root or Path.home() / ".codex/sessions"
    paths = list(root.glob(f"*/*/*/*{thread_id}.jsonl"))
    if len(paths) != 1:
        raise ValueError("Měřená relace nemá právě jeden místní záznam.")
    context: dict[str, Any] = {}
    snapshot: dict[str, Any] = {}
    with paths[0].open() as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except ValueError:
                continue  # A concurrently appended final line may be incomplete.
            if not isinstance(event, dict) or not isinstance(event.get("payload"), dict):
                continue
            payload = event["payload"]
            if event.get("type") == "turn_context":
                context = {key: payload.get(key) for key in ("model", "effort", "service_tier")}
            if (event.get("type") == "event_msg" and payload.get("type") == "token_count"
                    and isinstance(payload.get("info"), dict)):
                usage = normalize_usage(payload["info"].get("total_token_usage"))
                if usage is not None:
                    snapshot = {"thread_id": thread_id, **context,
                                "observed_at": event.get("timestamp"), "usage": usage}
    if not snapshot:
        raise ValueError("Spotřeba měřené relace není dostupná.")
    return snapshot


def usage_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    for key in ("thread_id", "model", "effort", "service_tier"):
        if before.get(key) != after.get(key):
            raise ValueError("Během měření se změnila relace nebo nastavení modelu.")
    start, end = normalize_usage(before.get("usage")), normalize_usage(after.get("usage"))
    if start is None or end is None:
        raise ValueError("Chybí důkaz spotřeby.")
    delta = normalize_usage({key: end[key] - start[key] for key in TOKEN_KEYS})
    if delta is None:
        raise ValueError("Počítadlo spotřeby se vynulovalo nebo není srovnatelné.")
    return {"model": after["model"], "usage": delta,
            "estimated_standard_credits": estimate_standard_credits(after["model"], delta)}
