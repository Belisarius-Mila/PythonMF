from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path

from app.codex_appserver import AppServerError
from app.communication.development_semaphore import DevelopmentSemaphore


class DevelopmentSemaphoreTests(unittest.TestCase):
    def make_store(self, root: Path) -> DevelopmentSemaphore:
        return DevelopmentSemaphore(root / "development-semaphore.json")

    def acquire(
        self,
        store: DevelopmentSemaphore,
        *,
        owner_id: str = "knihovna",
        project_binding: dict[str, str] | None = None,
    ) -> dict[str, object]:
        return store.acquire(
            owner_id=owner_id,
            owner_label="Knihovna" if owner_id == "knihovna" else "Terminálový Adam",
            workspace_label="Profil Knihovna" if owner_id == "knihovna" else "Hlavní terminál",
            base_head="a" * 40,
            topic="Bezpečný souběh vývoje",
            project_binding=project_binding,
            expected_revision=0,
            confirmed=True,
        )

    def test_missing_state_is_free_and_acquire_persists_private_lease(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = self.make_store(root)
            before = store.status()
            acquired = self.acquire(store)
            persisted = json.loads((root / "development-semaphore.json").read_text(encoding="utf-8"))

        self.assertTrue(before["ok"])
        self.assertFalse(before["active"])
        self.assertTrue(acquired["active"])
        self.assertEqual(acquired["owner_id"], "knihovna")
        self.assertEqual(acquired["base_head_short"], "a" * 12)
        self.assertEqual(persisted["base_head"], "a" * 40)
        self.assertNotIn("path", persisted)

    def test_project_binding_persists_and_survives_pause_resume(self) -> None:
        binding = {
            "project_id": "test-project-12345678",
            "project_label": "Testovací projekt",
            "handoff_path": "memory/handoffs/test_project.md",
            "tvbcp_path": "memory/tvbcp/test_project.txt",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self.make_store(Path(temp_dir))
            acquired = self.acquire(store, project_binding=binding)
            paused = store.set_mode(
                owner_id="knihovna",
                mode="paused",
                expected_revision=int(acquired["revision"]),
                confirmed=True,
            )
            resumed = store.set_mode(
                owner_id="knihovna",
                mode="active",
                expected_revision=int(paused["revision"]),
                confirmed=True,
            )

        for key, value in binding.items():
            self.assertEqual(acquired[key], value)
            self.assertEqual(paused[key], value)
            self.assertEqual(resumed[key], value)

    def test_owned_bootstrap_lease_can_be_bound_once_to_valid_project(self) -> None:
        binding = {
            "project_id": "new-project-12345678",
            "project_label": "Nový projekt",
            "handoff_path": "memory/handoffs/new_project_start.md",
            "tvbcp_path": "",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self.make_store(Path(temp_dir))
            temporary = self.acquire(store)
            bound = store.bind_project(
                owner_id="knihovna",
                project_binding=binding,
                expected_revision=int(temporary["revision"]),
                confirmed=True,
            )
            repeated = store.bind_project(
                owner_id="knihovna",
                project_binding=binding,
                expected_revision=int(bound["revision"]),
                confirmed=True,
            )

        self.assertEqual(bound["project_id"], binding["project_id"])
        self.assertEqual(bound["handoff_path"], binding["handoff_path"])
        self.assertEqual(bound["revision"], 2)
        self.assertFalse(repeated["changed"])

    def test_invalid_project_binding_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self.make_store(Path(temp_dir))
            with self.assertRaisesRegex(AppServerError, "Projektová vazba"):
                self.acquire(
                    store,
                    project_binding={
                        "project_id": "test-project-12345678",
                        "project_label": "Testovací projekt",
                        "handoff_path": "../private/secret.md",
                    },
                )

    def test_foreign_owner_and_stale_revision_cannot_overwrite_lease(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self.make_store(Path(temp_dir))
            acquired = self.acquire(store)
            with self.assertRaisesRegex(AppServerError, "cizí lease"):
                store.acquire(
                    owner_id="terminal",
                    owner_label="Terminálový Adam",
                    workspace_label="Hlavní terminál",
                    base_head="a" * 40,
                    topic="Jiná změna",
                    expected_revision=int(acquired["revision"]),
                    confirmed=True,
                )
            with self.assertRaisesRegex(AppServerError, "mezitím změnil"):
                store.set_mode(
                    owner_id="knihovna",
                    mode="paused",
                    expected_revision=0,
                    confirmed=True,
                )

    def test_pause_resume_and_clean_release_keep_owner_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = self.make_store(Path(temp_dir))
            acquired = self.acquire(store)
            paused = store.set_mode(
                owner_id="knihovna",
                mode="paused",
                expected_revision=int(acquired["revision"]),
                confirmed=True,
            )
            with self.assertRaisesRegex(AppServerError, "pozastavený"):
                store.assert_owner("knihovna")
            resumed = store.set_mode(
                owner_id="knihovna",
                mode="active",
                expected_revision=int(paused["revision"]),
                confirmed=True,
            )
            self.assertEqual(store.assert_owner("knihovna")["owner_id"], "knihovna")
            with self.assertRaisesRegex(AppServerError, "neuzavřený WIP"):
                store.release(
                    owner_id="knihovna",
                    expected_revision=int(resumed["revision"]),
                    confirmed=True,
                    safe_to_release=False,
                )
            released = store.release(
                owner_id="knihovna",
                expected_revision=int(resumed["revision"]),
                confirmed=True,
                safe_to_release=True,
            )

        self.assertEqual(paused["mode"], "paused")
        self.assertFalse(released["active"])
        self.assertEqual(released["revision"], 4)

    def test_corrupt_state_is_visible_and_all_writes_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "development-semaphore.json"
            path.write_text("{broken", encoding="utf-8")
            store = DevelopmentSemaphore(path)
            status = store.status()
            with self.assertRaisesRegex(AppServerError, "nelze bezpečně načíst"):
                self.acquire(store)

        self.assertFalse(status["ok"])
        self.assertTrue(status["active"])
        self.assertEqual(status["mode"], "invalid")

    def test_two_process_equivalent_stores_cannot_both_acquire_revision_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            stores = [self.make_store(root), self.make_store(root)]
            barrier = threading.Barrier(2)
            successes: list[str] = []
            failures: list[str] = []

            def attempt(store: DevelopmentSemaphore, owner_id: str) -> None:
                barrier.wait()
                try:
                    result = store.acquire(
                        owner_id=owner_id,
                        owner_label=owner_id,
                        workspace_label=f"Workspace {owner_id}",
                        base_head="a" * 40,
                        topic="Souběžný pokus",
                        expected_revision=0,
                        confirmed=True,
                    )
                    successes.append(str(result["owner_id"]))
                except AppServerError as exc:
                    failures.append(str(exc))

            threads = [
                threading.Thread(target=attempt, args=(stores[0], "knihovna")),
                threading.Thread(target=attempt, args=(stores[1], "terminal")),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=5)
            final = stores[0].status()

        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        self.assertEqual(final["owner_id"], successes[0])
        self.assertEqual(final["revision"], 1)


if __name__ == "__main__":
    unittest.main()
