from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from app.cockpit_status_service import (
    CockpitStatusLoaders,
    build_cockpit_live_status,
    build_cockpit_status,
    build_server_health_status,
)
from scripts.cockpit_smoke_check import check_endpoint


class CockpitStatusServiceTests(unittest.TestCase):
    def test_server_health_contract_is_lightweight_and_deterministic(self) -> None:
        status = build_server_health_status(
            code_stamp="stamp-123",
            host="127.0.0.1",
            port=8770,
            timestamp_loader=lambda: "2026-07-10T12:00:00+00:00",
            pid_loader=lambda: 4321,
        )

        self.assertEqual(
            status,
            {
                "ok": True,
                "generated_at": "2026-07-10T12:00:00+00:00",
                "server": {
                    "code_stamp": "stamp-123",
                    "pid": 4321,
                    "host": "127.0.0.1",
                    "port": 8770,
                },
            },
        )

    def test_full_status_preserves_section_dependencies_and_payload_contract(self) -> None:
        calls: list[str] = []
        downloads = {"items": ["download"]}
        document_work = {"items": ["work"]}
        reminders = {"items": ["reminder"]}
        urgent = {"items": ["urgent"]}

        def simple_loader(name: str, value: object):
            def load() -> object:
                calls.append(name)
                return value

            return load

        def load_document_work(received_downloads: object) -> object:
            self.assertIs(received_downloads, downloads)
            calls.append("document_work")
            return document_work

        def load_document_intake(received_downloads: object) -> object:
            self.assertIs(received_downloads, downloads)
            calls.append("document_intake")
            return {"items": ["intake"]}

        def load_action_queue(received_work: object, received_reminders: object, received_urgent: object) -> object:
            self.assertIs(received_work, document_work)
            self.assertIs(received_reminders, reminders)
            self.assertIs(received_urgent, urgent)
            calls.append("action_queue")
            return {"items": ["action"]}

        clock_value = 0.0

        def performance_clock() -> float:
            nonlocal clock_value
            clock_value += 0.001
            return clock_value

        loaders = CockpitStatusLoaders(
            downloads=simple_loader("downloads", downloads),
            document_work=load_document_work,
            document_intake=load_document_intake,
            document_cases=simple_loader("document_cases", {"items": ["case"]}),
            document_classification=simple_loader("document_classification", {"items": ["classification"]}),
            document_due_candidates=simple_loader("document_due_candidates", {"items": ["due"]}),
            reminders=simple_loader("reminders", reminders),
            urgent_reminders=simple_loader("urgent_reminders", urgent),
            backup_status=simple_loader("backup_status", {"message": "backup ok"}),
            action_queue=load_action_queue,
            vault=simple_loader("vault", "vault ok"),
            scandocu=simple_loader("scandocu", {"running": False}),
            codex_approval=simple_loader("codex_approval", {"active": False}),
            git=simple_loader("git", {"clean": True}),
        )

        status = build_cockpit_status(
            loaders=loaders,
            code_stamp="stamp-456",
            performance_clock=performance_clock,
            timestamp_loader=lambda: "2026-07-10T13:00:00+00:00",
            pid_loader=lambda: 9876,
        )

        self.assertEqual(
            calls,
            [
                "downloads",
                "document_work",
                "document_intake",
                "document_cases",
                "document_classification",
                "document_due_candidates",
                "reminders",
                "urgent_reminders",
                "backup_status",
                "action_queue",
                "vault",
                "scandocu",
                "codex_approval",
                "git",
            ],
        )
        self.assertEqual(status["generated_at"], "2026-07-10T13:00:00+00:00")
        self.assertEqual(status["server"], {"code_stamp": "stamp-456", "pid": 9876})
        self.assertIs(status["downloads"], downloads)
        self.assertIs(status["document_work"], document_work)
        self.assertEqual(status["backup"], "backup ok")
        self.assertEqual(len(status["status_timing"]["sections_ms"]), 14)
        self.assertEqual(status["codex_approval"], {"active": False})
        self.assertNotIn("voice_mode", status)
        self.assertNotIn("voice_bridge", status)
        self.assertNotIn("voice_mode", status["status_timing"]["sections_ms"])
        self.assertNotIn("voice_bridge", status["status_timing"]["sections_ms"])
        self.assertLessEqual(len(status["status_timing"]["slowest_sections"]), 3)

    def test_live_status_contains_only_codex_approval_and_timing(self) -> None:
        clock_values = iter((1.0, 1.001, 1.002, 1.003))
        status = build_cockpit_live_status(
            codex_approval_loader=lambda: {"active": False},
            performance_clock=lambda: next(clock_values),
            timestamp_loader=lambda: "2026-07-26T20:00:00+00:00",
        )

        self.assertEqual(
            status,
            {
                "generated_at": "2026-07-26T20:00:00+00:00",
                "codex_approval": {"active": False},
                "live_status_timing": {
                    "total_ms": 3.0,
                    "codex_approval_ms": 1.0,
                },
            },
        )
        self.assertNotIn("voice_mode", status)
        self.assertNotIn("voice_bridge", status)

    def test_smoke_contract_accepts_status_payloads_without_voice_sections(self) -> None:
        headers = {
            "x-content-type-options": "nosniff",
            "x-frame-options": "SAMEORIGIN",
            "referrer-policy": "no-referrer",
            "content-security-policy": "default-src 'self'",
        }
        payloads = {
            "/api/status": {
                "generated_at": "2026-07-26T20:00:00+00:00",
                "backup_status": {"status": "ok"},
            },
            "/api/live-status": {
                "generated_at": "2026-07-26T20:00:00+00:00",
                "codex_approval": {"active": False},
                "live_status_timing": {"total_ms": 1.0},
            },
        }

        for path, payload in payloads.items():
            with (
                self.subTest(path=path),
                patch(
                    "scripts.cockpit_smoke_check.fetch_url",
                    return_value=(200, json.dumps(payload).encode("utf-8"), headers),
                ),
            ):
                result = check_endpoint("http://127.0.0.1:8770", "status", path, timeout=1.0)
                self.assertTrue(result.ok)

    def test_smoke_contract_rejects_retired_voice_status_sections(self) -> None:
        headers = {
            "x-content-type-options": "nosniff",
            "x-frame-options": "SAMEORIGIN",
            "referrer-policy": "no-referrer",
            "content-security-policy": "default-src 'self'",
        }
        payloads = {
            "/api/status": {
                "generated_at": "2026-07-26T20:00:00+00:00",
                "backup_status": {"status": "ok"},
                "voice_bridge": {},
            },
            "/api/live-status": {
                "generated_at": "2026-07-26T20:00:00+00:00",
                "codex_approval": {"active": False},
                "live_status_timing": {"total_ms": 1.0},
                "voice_mode": {},
            },
        }

        for path, payload in payloads.items():
            with (
                self.subTest(path=path),
                patch(
                    "scripts.cockpit_smoke_check.fetch_url",
                    return_value=(200, json.dumps(payload).encode("utf-8"), headers),
                ),
            ):
                result = check_endpoint("http://127.0.0.1:8770", "status", path, timeout=1.0)
                self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
