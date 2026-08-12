"""Durable, fail-closed consent for non-sensitive external generation."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.file_persistence import atomic_write_json


CONSENT_SCHEMA_VERSION = 1
CONSENT_ID = "trusted_external_generation_v1"
GRANT_CONFIRMATION_TEXT = (
    "Schvaluji trvalé a odvolatelné oprávnění Human–Adam používat ve všech "
    "pracovních proudech registrované externí generativní služby pro veřejný, "
    "smyšlený a jiný necitlivý obsah, včetně generování obrázků, hlasu a dalších "
    "projektových materiálů, a ukládat výsledky zpět do aktivního projektu. "
    "Souhlas nezahrnuje soukromá data, tajemství, komunikaci s lidmi, publikování, "
    "nákupy, přihlašování, Git push, nasazení ani destruktivní operace."
)
REVOKE_CONFIRMATION_TEXT = "ODVOLÁVÁM TRVALÝ SOUHLAS S EXTERNÍM GENEROVÁNÍM"
CONSENT_SCOPES = ("public", "fictional", "nonsensitive")
CONSENT_OPERATIONS = (
    "generate_images",
    "generate_audio",
    "generate_music",
    "generate_project_materials",
)
CONSENT_EXCLUSIONS = (
    "private_data",
    "secrets",
    "human_communication",
    "publishing",
    "purchases",
    "authentication",
    "git_push",
    "deployment",
    "destructive_operations",
)
SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"\b(?:api[ _-]?key|password|heslo|access[ _-]?token|private[ _-]?key)\b", re.I),
    re.compile(r"(?:^|\b)data[/\\]private(?:[/\\]|$)", re.I),
    re.compile(r"(?:^|\s)\.env(?:\s|$|[/\\])", re.I),
    re.compile(r"\b(?:rodn\w*\s+čísl\w*|rodn\w*\s+cisl\w*|čísl\w*\s+účt\w*|cisl\w*\s+uct\w*|bank account)\b", re.I),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def trusted_external_generation_text_allowed(text: str) -> bool:
    """Reject empty or obviously sensitive text before durable consent is used."""
    clean = str(text or "").strip()
    return bool(clean) and not any(pattern.search(clean) for pattern in SENSITIVE_TEXT_PATTERNS)


class TrustedExternalGenerationConsentStore:
    """Persist one global consent without storing prompts or generated content."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def grant(self) -> dict[str, Any]:
        payload = {
            "schema_version": CONSENT_SCHEMA_VERSION,
            "consent_id": CONSENT_ID,
            "enabled": True,
            "revocable": True,
            "scopes": list(CONSENT_SCOPES),
            "operations": list(CONSENT_OPERATIONS),
            "exclusions": list(CONSENT_EXCLUSIONS),
            "approved_at": _now(),
            "revoked_at": "",
        }
        atomic_write_json(self.path, payload, ensure_ascii=False, indent=2)
        return self.status()

    def revoke(self) -> dict[str, Any]:
        payload = {
            "schema_version": CONSENT_SCHEMA_VERSION,
            "consent_id": CONSENT_ID,
            "enabled": False,
            "revocable": True,
            "scopes": list(CONSENT_SCOPES),
            "operations": list(CONSENT_OPERATIONS),
            "exclusions": list(CONSENT_EXCLUSIONS),
            "approved_at": "",
            "revoked_at": _now(),
        }
        atomic_write_json(self.path, payload, ensure_ascii=False, indent=2)
        return self.status()

    def _load_enabled(self) -> tuple[bool, str]:
        if not self.path.is_file():
            return False, "missing"
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False, "invalid"
        if not isinstance(payload, dict):
            return False, "invalid"
        expected = {
            "schema_version": CONSENT_SCHEMA_VERSION,
            "consent_id": CONSENT_ID,
            "revocable": True,
            "scopes": list(CONSENT_SCOPES),
            "operations": list(CONSENT_OPERATIONS),
            "exclusions": list(CONSENT_EXCLUSIONS),
        }
        if any(payload.get(key) != value for key, value in expected.items()):
            return False, "invalid"
        if payload.get("enabled") is not True:
            return False, "revoked" if payload.get("enabled") is False else "invalid"
        if not str(payload.get("approved_at") or "").strip():
            return False, "invalid"
        return True, "active"

    def status(self) -> dict[str, Any]:
        enabled, state = self._load_enabled()
        return {
            "schema_version": CONSENT_SCHEMA_VERSION,
            "consent_id": CONSENT_ID,
            "enabled": enabled,
            "state": state,
            "revocable": True,
            "scopes": list(CONSENT_SCOPES),
            "operations": list(CONSENT_OPERATIONS),
            "exclusions": list(CONSENT_EXCLUSIONS),
            "grant_confirmation_text": GRANT_CONFIRMATION_TEXT,
            "revoke_confirmation_text": REVOKE_CONFIRMATION_TEXT,
        }

    def development_control_lines(
        self,
        *,
        registered_capability_ids: tuple[str, ...] = (),
    ) -> tuple[str, ...]:
        status = self.status()
        clean_ids = tuple(
            capability_id
            for capability_id in registered_capability_ids
            if capability_id and capability_id.replace("_", "").isalnum()
        )
        if not status["enabled"] or not clean_ids:
            return (
                "trusted_external_generation=disabled",
                "trusted_external_generation_confirmation_required=explicit_durable_consent",
            )
        return (
            "trusted_external_generation=enabled",
            f"trusted_external_generation_consent_id={CONSENT_ID}",
            "trusted_external_generation_scope=" + ",".join(CONSENT_SCOPES),
            "trusted_external_generation_operations=" + ",".join(CONSENT_OPERATIONS),
            "trusted_external_generation_capabilities=" + ",".join(clean_ids),
            "trusted_external_generation_confirmation_required=none_within_scope",
            "trusted_external_generation_excludes=" + ",".join(CONSENT_EXCLUSIONS),
            "rule=Trusted external generation is allowed only through a registered "
            "external_generation capability and only for public, fictional or other "
            "non-sensitive input. Save results only to the active project or its "
            "approved private candidate area.",
            "rule=This consent never authorizes private data, secrets, messages to people, "
            "publishing, purchases, authentication, Git push, deployment or destructive work.",
        )
