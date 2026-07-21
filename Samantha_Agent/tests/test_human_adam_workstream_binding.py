from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from app.communication.human_adam_workstream_binding import (
    canonical_workstream_binding,
)


class CanonicalWorkstreamBindingTests(unittest.TestCase):
    @staticmethod
    def profile(**workstream_overrides):
        tvbcp = "memory/tvbcp/architektura_komunikace_samantha.txt"
        workstream = {
            "id": "layer-human-adam-development",
            "type": "Layer",
            "name": "Human–Adam / vývojové prostředí",
            "handoff": "memory/handoffs/human_adam_layer_workstream_start_2026_07_20.md",
            "tvbcp": tvbcp,
            **workstream_overrides,
        }
        return {
            "workstream": workstream,
            "service": SimpleNamespace(
                work_profile_id="human_adam",
                tvbcp_relative_path=Path(tvbcp),
            ),
        }

    def test_legacy_alias_is_validated_against_canonical_catalog(self) -> None:
        binding = canonical_workstream_binding(
            profile_id="human_adam",
            profile=self.profile(),
        )

        self.assertIsNotNone(binding)
        self.assertEqual(binding.workstream_id, "layer-human-adam-development")
        self.assertEqual(binding.workstream_type, "Layer")

    def test_unknown_catalog_identity_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "mimo kanonický katalog"):
            canonical_workstream_binding(
                profile_id="human_adam",
                profile=self.profile(id="project-unknown"),
            )

    def test_noncanonical_name_or_type_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "neodpovídá kanonickému katalogu"):
            canonical_workstream_binding(
                profile_id="human_adam",
                profile=self.profile(type="Tool"),
            )

    def test_memory_path_and_service_identity_stay_profile_locked(self) -> None:
        with self.assertRaisesRegex(ValueError, "platnou cestu k handoff"):
            canonical_workstream_binding(
                profile_id="human_adam",
                profile=self.profile(handoff="../outside.md"),
            )

        profile = self.profile()
        profile["service"].work_profile_id = "knihovna"
        with self.assertRaisesRegex(ValueError, "bezpečný identifikátor"):
            canonical_workstream_binding(
                profile_id="human_adam",
                profile=profile,
            )


if __name__ == "__main__":
    unittest.main()
