from __future__ import annotations

import unittest
from types import SimpleNamespace

from app.codex_appserver import AppServerError
from app.communication.human_adam_workstream_backends import (
    COMPATIBILITY_ADAPTER_BACKEND,
    LAZY_PRIVATE_THREAD_BACKEND,
    CompatibilityWorkstreamAdapter,
    WorkstreamBackendRegistry,
)


class WorkstreamBackendRegistryTests(unittest.TestCase):
    def adapter(self, workstream_id: str, profile_id: str):
        service = SimpleNamespace(work_profile_id=profile_id)
        return CompatibilityWorkstreamAdapter(workstream_id, profile_id, service)

    def test_compatibility_adapter_preserves_original_service_identity(self) -> None:
        adapter = self.adapter("layer-human-adam-development", "human_adam")
        registry = WorkstreamBackendRegistry(compatibility_adapters=(adapter,))
        lazy_calls: list[str] = []

        resolved = registry.service(
            "layer-human-adam-development",
            lazy_service_factory=lambda workstream_id: lazy_calls.append(workstream_id),
        )
        binding = registry.binding("layer-human-adam-development")

        self.assertIs(resolved, adapter.service)
        self.assertEqual(lazy_calls, [])
        self.assertEqual(binding.backend, COMPATIBILITY_ADAPTER_BACKEND)
        self.assertEqual(binding.profile_id, "human_adam")
        self.assertEqual(
            registry.compatibility_workstream_id("human_adam"),
            "layer-human-adam-development",
        )

    def test_lazy_backend_resolves_only_requested_canonical_service(self) -> None:
        registry = WorkstreamBackendRegistry()
        lazy_calls: list[str] = []

        def lazy_service(workstream_id: str):
            lazy_calls.append(workstream_id)
            return SimpleNamespace(work_profile_id=workstream_id)

        resolved = registry.service(
            "project-mmtx",
            lazy_service_factory=lazy_service,
        )

        self.assertEqual(resolved.work_profile_id, "project-mmtx")
        self.assertEqual(lazy_calls, ["project-mmtx"])
        self.assertEqual(
            registry.binding("project-mmtx").backend,
            LAZY_PRIVATE_THREAD_BACKEND,
        )

    def test_adapter_rejects_service_from_different_profile(self) -> None:
        adapter = CompatibilityWorkstreamAdapter(
            "project-knowledge-library",
            "knihovna",
            SimpleNamespace(work_profile_id="human_adam"),
        )

        with self.assertRaisesRegex(ValueError, "původní službu"):
            WorkstreamBackendRegistry(compatibility_adapters=(adapter,))

    def test_one_profile_cannot_own_two_compatibility_adapters(self) -> None:
        with self.assertRaisesRegex(ValueError, "jedinečný"):
            WorkstreamBackendRegistry(
                compatibility_adapters=(
                    self.adapter("layer-human-adam-development", "human_adam"),
                    self.adapter("project-knowledge-library", "human_adam"),
                )
            )

    def test_lazy_service_identity_mismatch_fails_closed(self) -> None:
        registry = WorkstreamBackendRegistry()

        with self.assertRaisesRegex(AppServerError, "nevrátil službu"):
            registry.service(
                "project-mmtx",
                lazy_service_factory=lambda _workstream_id: SimpleNamespace(
                    work_profile_id="project-lekarna"
                ),
            )


if __name__ == "__main__":
    unittest.main()
