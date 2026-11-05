"""Audio role approval, deliberately separate from App Server reasoning models."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.communication.agent_roles import CONFIG_PATH, KNOWN_ROLES, AgentRoleError, _review

VOICE_ROLE = "read_only_voice"
ROOT = Path(__file__).resolve().parents[2]


def load_voice_role(path: Path = CONFIG_PATH, *, root: Path = ROOT) -> dict:
    try:
        raw = Path(path).read_bytes()
        if len(raw) > 32000:
            raise ValueError()
        document = json.loads(raw)
        if (set(document) != {"schema", "roles"} or document["schema"] != 1
                or not set(document["roles"]).issubset(KNOWN_ROLES)):
            raise ValueError()
        role = document["roles"][VOICE_ROLE]
        if (set(role) != {"label", "preferred_model", "approved_models"}
                or not _review(role["label"]) or role["preferred_model"] != "gpt-live-1"
                or not isinstance(role["approved_models"], list) or len(role["approved_models"]) != 1):
            raise ValueError()
        model = role["approved_models"][0]
        if (set(model) != {"model", "cost_review", "dry_run_evidence"}
                or model["model"] != "gpt-live-1" or not _review(model["cost_review"])
                or model["dry_run_evidence"] != "memory/reports/voice_conversation_probe_20261105.json"):
            raise ValueError()
        proof = json.loads((root / model["dry_run_evidence"]).read_text())
        result = proof["result"]
        if (proof["schema"] != 1 or result["model"] != model["model"]
                or any(result.get(key) is not True for key in
                       ("probe_pass", "session_started", "session_closed", "final_usage_confirmed", "non_silent_audio"))
                or not 0 < result["seconds"] <= 60 or proof["audit"]["model_start_attempts"] != 1):
            raise ValueError()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise AgentRoleError("Čtecí hlas nemá platnou centrální roli a důkaz zkoušky.") from exc
    digest = hashlib.sha256(json.dumps(role, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"role": VOICE_ROLE, "model": model["model"], "policy_digest": digest}
