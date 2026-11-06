from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from app.calendar_access_pilot import BUNDLE_ID, CalendarAccessPilot, CalendarPilotError, SOURCE, _sha


class CalendarAccessPilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.calls = []
        self.authorization = "full_access"
        self.parent_pid = 1
        self.fail_open = False
        self.pilot = CalendarAccessPilot(self.root, runner=self.run_command)
        app = self.root / "Probe.app"
        binary = app / "Contents/MacOS/CalendarReadOnlyPilot"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"synthetic native binary")
        info = app / "Contents/Info.plist"
        info.write_bytes(b"synthetic info")
        (self.root / "build.json").write_text(json.dumps({"app": str(app),
            "binary_sha256": _sha(binary), "info_sha256": _sha(info), "source_sha256": _sha(SOURCE)}))

    def run_command(self, args, **kwargs):
        args = list(map(str, args)); self.calls.append(args)
        output = ""
        if args[-1] == "--status-json":
            output = json.dumps({"schema": 1, "operation": "status", "calendar_writes": False,
                                 "bundle_identifier": BUNDLE_ID,
                                 "authorization": self.authorization, "observed_at": "2026-11-06T00:00:00Z"})
        elif args[0] == "/usr/bin/open":
            if self.fail_open:
                return subprocess.CompletedProcess(args, 1, "", "synthetic GUI launch failure")
        elif args[0] == "/bin/launchctl" and args[1] in {"print", "remove"}:
            pass
        else:
            request_path = Path(args[-1]); value = json.loads(request_path.read_text())
            self.response(request_path, parent_pid=self.parent_pid)
        return subprocess.CompletedProcess(args, 0, output, "")

    def response(self, path, **overrides):
        request = json.loads(path.read_text())
        value = {"schema": 1, "operation": request["operation"], "request_id": request["request_id"],
                 "bundle_identifier": BUNDLE_ID, "start": request["start"], "end": request["end"],
                 "calendar_writes": False, "status": "read_verified", "authorization": "full_access",
                 "parent_pid": 1, "calendar_count": 2, "icloud_calendar_count": 1, "event_count": 3,
                 "calendars": [{"title": "PRIVATE TITLE", "id": "PRIVATE ID"}], **overrides}
        (path.parent / "response.json").write_text(json.dumps(value))

    def test_status_is_read_only_and_does_not_create_requests(self):
        before = set(self.root.rglob("*"))
        result = self.pilot.status()
        self.assertEqual(result["authorization"], "full_access")
        self.assertFalse(result["calendar_writes"])
        self.assertEqual(set(self.root.rglob("*")), before)

    def test_missing_build_status_does_not_initialize_storage(self):
        missing = self.root / "absent"
        result = CalendarAccessPilot(missing, runner=self.run_command).status()
        self.assertFalse(result["built"])
        self.assertFalse(missing.exists())

    def test_sensitive_operations_require_explicit_confirmation(self):
        for action in (self.pilot.build, self.pilot.authorize, self.pilot.probe):
            with self.subTest(action=action.__name__), self.assertRaises(CalendarPilotError):
                action()
        self.assertEqual(self.calls, [])

    def test_no_permission_stops_before_calendar_query_or_job_creation(self):
        self.authorization = "denied"
        result = self.pilot.probe(confirmed=True, service=True)
        self.assertEqual(result["status"], "authorization_required")
        self.assertEqual(len(self.calls), 1)
        self.assertFalse((self.root / "requests").exists())

    def test_binary_drift_prevents_execution(self):
        _, _, binary = self.pilot._build_info()
        binary.write_bytes(b"changed")
        with self.assertRaises(CalendarPilotError):
            self.pilot.status()
        self.assertEqual(self.calls, [])

    def test_symlink_manifest_is_refused(self):
        original = self.root / "build.json"
        target = self.root / "other.json"
        original.rename(target); original.symlink_to(target)
        with self.assertRaises(CalendarPilotError):
            self.pilot.status()
        self.assertEqual(self.calls, [])

    def test_probe_redacts_calendar_names_and_keeps_private_proof(self):
        result = self.pilot.probe(confirmed=True)
        self.assertEqual(result["status"], "read_verified")
        self.assertEqual(result["event_count"], 3)
        self.assertNotIn("PRIVATE", json.dumps(result))
        proof = self.root / "requests" / result["request_id"] / "response.json"
        self.assertIn("PRIVATE TITLE", proof.read_text())
        request = json.loads(proof.with_name("request.json").read_text())
        self.assertEqual(request["operation"], "probe")
        self.assertEqual(set(request), {"schema", "operation", "request_id", "start", "end"})

    def test_mismatched_or_writing_result_cannot_be_accepted(self):
        for overrides in ({"request_id": "foreign"}, {"calendar_writes": True}, {"operation": "authorize"},
                          {"schema": 2}, {"bundle_identifier": "foreign"}, {"start": "foreign"},
                          {"event_count": -1}):
            path = self.pilot._request("probe")
            self.response(path, **overrides)
            with self.subTest(overrides=overrides), self.assertRaises(CalendarPilotError):
                self.pilot._response(path)

    def test_failed_gui_start_keeps_claim_and_never_automatically_relaunches(self):
        self.fail_open = True
        with self.assertRaises(CalendarPilotError):
            self.pilot.authorize(confirmed=True)
        result = self.pilot.authorize(confirmed=True)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(sum(call[0] == "/usr/bin/open" for call in self.calls), 1)

    def test_service_probe_checks_real_parent_and_removes_only_its_own_job(self):
        result = self.pilot.probe(confirmed=True, service=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["launchd_parent_verified"])
        submit = next(c for c in self.calls if c[:2] == ["/bin/launchctl", "submit"])
        remove = next(c for c in self.calls if c[:2] == ["/bin/launchctl", "remove"])
        self.assertEqual(submit[3], remove[2])
        self.assertTrue(submit[3].startswith("com.samantha.calendar-readonly-probe."))
        self.assertNotIn("LaunchAgents", " ".join(submit))

    def test_shell_parent_is_not_service_acceptance(self):
        self.parent_pid = 123
        result = self.pilot.probe(confirmed=True, service=True)
        self.assertFalse(result["ok"])
        self.assertFalse(result["launchd_parent_verified"])

    def test_gui_permission_allows_native_service_probe_despite_shell_write_only_context(self):
        request = self.pilot._request("authorize")
        self.response(request, status="authorization_checked")
        info, _, _ = self.pilot._build_info()
        (self.root / "authorization_request.json").write_text(json.dumps({
            "request": str(request), "binary_sha256": info["binary_sha256"]}))
        self.authorization = "write_only"
        self.assertTrue(self.pilot.probe(confirmed=True, service=True)["ok"])

    def test_permission_receipt_from_another_binary_cannot_authorize_a_probe(self):
        (self.root / "authorization_request.json").write_text(json.dumps({
            "request": "unused", "binary_sha256": "foreign"}))
        self.authorization = "write_only"
        with self.assertRaises(CalendarPilotError):
            self.pilot.probe(confirmed=True, service=True)
        self.assertFalse(any("submit" in call for call in self.calls))

    def test_native_source_has_no_calendar_mutation_or_reset_entrypoint(self):
        source = SOURCE.read_text()
        for api in ("save(", "remove(", "reset(", "requestWriteOnlyAccessToEvents", "EKReminder("):
            self.assertNotIn(api, source)
        self.assertIn("end.timeIntervalSince(start) <= 31 * 86400", source)


if __name__ == "__main__":
    unittest.main()
