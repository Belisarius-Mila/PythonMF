from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.communication.trusted_external_generation import (
    CONSENT_EXCLUSIONS,
    CONSENT_ID,
    GRANT_CONFIRMATION_TEXT,
    REVOKE_CONFIRMATION_TEXT,
    TrustedExternalGenerationConsentStore,
    trusted_external_generation_text_allowed,
)


class TrustedExternalGenerationConsentTests(unittest.TestCase):
    def test_missing_or_invalid_consent_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "consent.json"
            store = TrustedExternalGenerationConsentStore(path)
            self.assertFalse(store.status()["enabled"])
            self.assertIn("trusted_external_generation=disabled", store.development_control_lines())

            path.write_text('{"enabled": true}', encoding="utf-8")
            self.assertEqual(store.status()["state"], "invalid")
            self.assertFalse(store.status()["enabled"])

    def test_grant_is_durable_bounded_and_revocable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "consent.json"
            store = TrustedExternalGenerationConsentStore(path)

            granted = store.grant()
            restarted = TrustedExternalGenerationConsentStore(path)
            lines = restarted.development_control_lines(
                registered_capability_ids=(
                    "generate_human_adam_image_candidate",
                    "generate_project_audio_asset",
                )
            )

            self.assertTrue(granted["enabled"])
            self.assertTrue(restarted.status()["enabled"])
            self.assertIn("trusted_external_generation=enabled", lines)
            self.assertIn(
                f"trusted_external_generation_consent_id={CONSENT_ID}",
                lines,
            )
            self.assertIn("trusted_external_generation_confirmation_required=none_within_scope", lines)
            self.assertIn(
                "trusted_external_generation_capabilities="
                "generate_human_adam_image_candidate,generate_project_audio_asset",
                lines,
            )
            serialized = json.dumps(restarted.status())
            for exclusion in CONSENT_EXCLUSIONS:
                self.assertIn(exclusion, serialized)

            revoked = restarted.revoke()
            self.assertFalse(revoked["enabled"])
            self.assertEqual(revoked["state"], "revoked")

        self.assertTrue(GRANT_CONFIRMATION_TEXT.startswith("Schvaluji trvalé"))
        self.assertTrue(REVOKE_CONFIRMATION_TEXT.startswith("ODVOLÁVÁM"))

    def test_obviously_sensitive_text_cannot_use_durable_consent(self) -> None:
        self.assertTrue(
            trusted_external_generation_text_allowed(
                "Vygeneruj obrázek smyšlené modré sovy v lese."
            )
        )
        for text in (
            "Vygeneruj ilustraci podle data/private/dokument.txt.",
            "Nakresli kartu s API key abc.",
            "Vytvoř obrázek pro osoba@example.com.",
            "Vygeneruj plakát s rodným číslem.",
        ):
            self.assertFalse(trusted_external_generation_text_allowed(text), text)


if __name__ == "__main__":
    unittest.main()
