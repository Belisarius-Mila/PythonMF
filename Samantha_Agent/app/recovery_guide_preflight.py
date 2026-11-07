"""Nonpaid REC-02 diagnostics. Reference BPE is NEVER a model fallback.

Optional tiktoken belongs to the isolated operator environment, not the
project dependencies. Unknown exact model mappings keep the real pilot shut.
"""
from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
import importlib
from importlib.metadata import version
from datetime import datetime, timezone
from pathlib import Path

from app.recovery_guide_maintainer import MODEL, Limits, plan
from app.recovery_guide_sources import Snapshot, canonical_json, digest

REFERENCE_ENCODING = "o200k_base"
PROPOSED_LIMITS = Limits(input_tokens=250_000, output_tokens=32_000, max_calls=20,
                       run_credits=500, month_credits=2500, seconds=1800,
                       inspection_output_tokens=8_000)


class TokenizerUnavailable(ValueError):
    pass


def runtime_observation(client_factory=None) -> dict:
    """Connect ONLY to the existing shared socket. No process/thread/turn start.

    Strict projection avoids prompt templates and credential-bearing config.
    Catalog availability is not a paid invocation or an isolation proof.
    """
    if client_factory is None:
        from app.communication.luna_release import new_luna_client
        client_factory = new_luna_client
    result = {"observed_at": datetime.now(timezone.utc).isoformat(), "model": MODEL,
              "model_calls": 0, "thread_starts": 0, "starts_service": False,
              "live_isolation_proven": False, "authentication_pricing_basis": "not_verified",
              "ready_for_paid_pilot": False}
    try:
        with client_factory() as client:
            catalog = client.list_models(include_hidden=True)
            config = client.read_effective_config(cwd=Path(__file__).resolve().parents[1])
            row = next((r for r in catalog if r.get("model") == MODEL), {})
            medium = any(e.get("reasoningEffort") == "medium" for e in row.get("supportedReasoningEfforts", [])
                         if isinstance(e, dict))
            tier = config.get("service_tier")
            return {**result, "state": "observed", "server_version": client.server_version.raw,
                    "local_cli_version": client.version.raw, "model_medium_available": medium,
                    "standard_preference_compatible": tier in {None, "default"},
                    "runtime_context_tokens": None}
    except Exception:
        return {**result, "state": "unavailable", "automatic_retry": False}


def tokenizer_probe(module=None) -> dict:
    """Inspect the installed upstream model map; never map a model ourselves."""
    if module is None:
        try:
            module = importlib.import_module("tiktoken")
        except ImportError:
            return {"state": "unavailable", "exact_model_mapping": False, "model": MODEL}
    try:
        package_version = version("tiktoken")
    except Exception:
        package_version = "unknown"
    result = {"model": MODEL, "package": "tiktoken", "version": package_version,
              "exact_model_mapping": False, "fallback": False}
    try:
        encoding = module.encoding_for_model(MODEL)
    except KeyError:
        return {**result, "state": "model_mapping_unknown"}
    return {**result, "state": "mapped", "encoding": encoding.name, "exact_model_mapping": True,
            "full_appserver_prompt_exact": False}


def exact_text_counter(module=None):
    module = module or importlib.import_module("tiktoken")
    probe = tokenizer_probe(module)
    if not probe["exact_model_mapping"]:
        raise TokenizerUnavailable("Model nemá upstream mapování; bez automatické náhrady.")
    encoding = module.encoding_for_model(MODEL)
    return lambda text: len(encoding.encode_ordinary(text))


def reference_preflight(snapshot: Snapshot, *, limits: Limits = PROPOSED_LIMITS, module=None) -> dict:
    """Exact counts FOR a named reference encoding, not for the requested model.

    Returns no runnable prompts or approval token. Estimates include repeated
    originals, fixed instructions/schema framing, inspection and synthesis.
    Output limits are acceptance allowances, not transport-enforced billing caps.
    """
    module = module or importlib.import_module("tiktoken")
    probe = tokenizer_probe(module)
    encoding = module.get_encoding(REFERENCE_ENCODING)

    @lru_cache(maxsize=8)
    def count(text: str) -> int:
        return len(encoding.encode_ordinary(text))

    prepared = plan(snapshot, count, limits)
    rows = []
    all_paths = []
    for index, payload in enumerate(prepared["shards"]):
        rows.append({"batch": index, "source_count": len(payload["sources"]),
                     "source_paths": [s["path"] for s in payload["sources"]],
                     "payload_sha256": digest(canonical_json(payload)),
                     "payload_reference_tokens": count(canonical_json(payload))})
        all_paths.extend(rows[-1]["source_paths"])
    expected = [s.path for s in snapshot.sources]
    if all_paths != expected or len(set(all_paths)) != len(expected):
        raise ValueError("Dávky nepokrývají úplný zmrazený manifest.")
    result = {"state": "blocked_for_live_pilot", "task": "recovery_guide_preflight",
              "model": MODEL, "tokenizer": probe, "reference_encoding": REFERENCE_ENCODING,
              "reference_is_model_mapping": False, "model_calls": 0, "publication": False,
              "snapshot": snapshot.receipt(), "proposed_limits_not_approved": asdict(limits),
              "batches": rows, "planned_calls_including_synthesis": prepared["calls"],
              "coverage_planned": {"source_count": len(all_paths), "ratio": 1.0},
              "original_reference_tokens": count(snapshot.original.text),
              "source_reference_tokens": sum(count(s.text) for s in snapshot.sources),
              "estimated_input_reference_tokens": prepared["input_bound"],
              "reserved_output_reference_tokens": prepared["output_bound"],
              "estimated_standard_credits_reference_only": prepared["reserved_credits"],
              "cache_assumed": False, "billing_hard_cap": False,
              "blockers": ["approved_complete_corpus", "verified_model_tokenization_and_runtime_context",
                           "explicit_cost_trial_approval", "live_isolation_and_standard_tier_proof"],
              "rates": {"input": 50, "cached_input": 2.5, "output": 250,
                        "unit": "Standard credits per 1M tokens",
                        "source": "https://learn.chatgpt.com/docs/pricing#token-rates",
                        "checked": "2026-11-07"}}
    result["plan_sha256"] = digest(canonical_json(result))
    return result
