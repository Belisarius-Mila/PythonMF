"""Reviewed model-role bindings; catalog upgrade hints never grant approval."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from app.codex_appserver import AppServerError


ROLE = "release_executor"
ROUTINE_ROLE = "routine_reviewer"
KNOWN_ROLES = frozenset({ROLE, ROUTINE_ROLE})
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config/agent_roles.json"
MODEL_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._:-]{0,95}")
EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max", "ultra"})


class AgentRoleError(AppServerError):
    """Missing approval or compatibility blocks a role before publication."""


def _review(value: Any) -> bool:
    return isinstance(value, str) and 8 <= len(value) <= 240 and not any(ord(c) < 32 for c in value)


def load_role(path: Path = CONFIG_PATH, *, role: str = ROLE) -> dict[str, Any]:
    try:
        raw = Path(path).read_bytes()
        if len(raw) > 32_000:
            raise ValueError("oversized")
        document = json.loads(raw)
        if set(document) != {"schema", "roles"} or document["schema"] != 1:
            raise ValueError("schema")
        if (role not in KNOWN_ROLES or role not in document["roles"]
                or not set(document["roles"]).issubset(KNOWN_ROLES)):
            raise ValueError("roles")
        binding = document["roles"][role]
        if set(binding) != {"label", "preferred_model", "approved_models"}:
            raise ValueError("role")
        candidates = binding["approved_models"]
        if not isinstance(candidates, list) or not 1 <= len(candidates) <= 8 or not _review(binding["label"]):
            raise ValueError("candidates")
        seen = set()
        for item in candidates:
            if (set(item) != {"model", "reasoning_effort", "cost_review", "dry_run_evidence"}
                    or not isinstance(item["model"], str) or not MODEL_ID.fullmatch(item["model"])
                    or item["reasoning_effort"] not in EFFORTS
                    or not _review(item["cost_review"]) or not _review(item["dry_run_evidence"])
                    or item["model"] in seen):
                raise ValueError("approval")
            seen.add(item["model"])
        if binding["preferred_model"] not in seen:
            raise ValueError("preferred")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise AgentRoleError("Nastavení vykonavatele nemá platné schválení ceny a zkoušky.") from exc
    digest = hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {**binding, "role": role, "policy_digest": digest}


def validate_selection(selection: Any, *, role: str = ROLE) -> dict[str, str]:
    if (role not in KNOWN_ROLES or not isinstance(selection, dict) or selection.get("role") != role
            or not isinstance(selection.get("model"), str) or not MODEL_ID.fullmatch(selection["model"])
            or not isinstance(selection.get("reasoning_effort"), str) or selection["reasoning_effort"] not in EFFORTS
            or not re.fullmatch(r"[0-9a-f]{64}", str(selection.get("policy_digest", "")))):
        raise AgentRoleError("Účtenka nemá platný zmrazený model vykonavatele.")
    return {key: selection[key] for key in ("role", "model", "reasoning_effort", "policy_digest")}


def assert_current(selection: dict[str, Any], *, path: Path = CONFIG_PATH, role: str = ROLE) -> dict[str, str]:
    selected = validate_selection(selection, role=role)
    policy = load_role(path, role=role)
    if (policy["policy_digest"] != selected["policy_digest"]
            or not any(item["model"] == selected["model"] and item["reasoning_effort"] == selected["reasoning_effort"]
                       for item in policy["approved_models"])):
        raise AgentRoleError("Nastavení vykonavatele se od potvrzení změnilo. Je potřeba nové předání.")
    return selected


def compatible(entry: dict[str, Any], candidate: dict[str, Any]) -> bool:
    if not isinstance(entry, dict):
        return False
    efforts = entry.get("supportedReasoningEfforts") or []
    modalities = entry.get("inputModalities", ["text", "image"])
    return (entry.get("model") == candidate["model"]
            and isinstance(modalities, list) and "text" in modalities
            and isinstance(efforts, list)
            and any(isinstance(item, dict) and item.get("reasoningEffort") == candidate["reasoning_effort"]
                    for item in efforts))


def resolve_role(catalog: list[dict[str, Any]], *, path: Path = CONFIG_PATH, role: str = ROLE) -> dict[str, Any]:
    policy = load_role(path, role=role)
    preferred = policy["preferred_model"]
    candidates = sorted(policy["approved_models"], key=lambda item: item["model"] != preferred)
    for candidate in candidates:
        if any(compatible(entry, candidate) for entry in catalog):
            return {"role": role, "model": candidate["model"], "reasoning_effort": candidate["reasoning_effort"],
                    "policy_digest": policy["policy_digest"], "fallback": candidate["model"] != preferred}
    upgrade = next((entry.get("upgrade") for entry in catalog if entry.get("model") == preferred), None)
    hint = (f" Doporučený nástupce {upgrade} vyžaduje posouzení ceny a zkoušku."
            if isinstance(upgrade, str) and MODEL_ID.fullmatch(upgrade) else "")
    raise AgentRoleError("V katalogu není dostupný kompatibilní schválený vykonavatel." + hint)
