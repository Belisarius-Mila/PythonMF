"""Bounded read-only EventKit experiment, separate from live email/calendar writes."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.file_persistence import atomic_write_text, exclusive_file_lock

PROJECT = Path(__file__).resolve().parents[1]
# launchd must not depend on access to the protected Desktop checkout. Only
# owned application data/artifacts live here; no system configuration is edited.
DEFAULT_ROOT = Path.home() / "Library/Application Support/SamanthaCalendarPilot"
SOURCE = PROJECT / "scripts/calendar_access_pilot.swift"
BUNDLE_ID = "com.samantha.calendar-readonly-pilot"
AUTHORIZATIONS = {"not_determined", "restricted", "denied", "full_access", "write_only", "unknown"}


class CalendarPilotError(RuntimeError):
    pass


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CalendarAccessPilot:
    source = SOURCE
    bundle_id = BUNDLE_ID
    binary_name = "CalendarReadOnlyPilot"
    app_name = "SamanthaCalendarReadOnly.app"
    display_name = "Samantha Calendar Read Only"
    usage = "Samantha ověří čtení iCloud kalendářů. Tento pilot neumí události vytvářet, měnit ani mazat."
    self_test_checks = 4

    def __init__(self, root=DEFAULT_ROOT, *, runner=subprocess.run):
        if Path(root).is_symlink():
            raise CalendarPilotError("Kořen pilotu nesmí být symlink.")
        self.root = Path(root).resolve()
        self.runner = runner

    def _safe(self, path):
        path = Path(path).absolute()
        if not path.is_relative_to(self.root) or path.resolve() != path:
            raise CalendarPilotError("Pilot odmítl cizí cestu nebo symlink.")
        return path

    def _run(self, args, timeout=60):
        result = self.runner(list(map(str, args)), capture_output=True, text=True, timeout=timeout, check=False)
        if result.returncode:
            if self.root.is_dir():
                self._write(self.root / ("command_error_" + uuid4().hex + ".json"),
                            {"program": Path(args[0]).name, "returncode": result.returncode,
                             "stderr": result.stderr[-16000:]})
            raise CalendarPilotError("Příkaz kalendářového pilotu neprošel; neopakovat nejistý start.")
        return result.stdout

    def _write(self, path, value):
        path = self._safe(path)
        atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def _build_info(self):
        path = self._safe(self.root / "build.json")
        value = json.loads(path.read_text())
        app = self._safe(Path(value["app"]))
        binary = self._safe(app / ("Contents/MacOS/" + self.binary_name))
        info = self._safe(app / "Contents/Info.plist")
        if (_sha(binary) != value["binary_sha256"] or _sha(info) != value["info_sha256"]
                or _sha(self.source) != value["source_sha256"]):
            raise CalendarPilotError("Sestavený pilot nebo jeho zdroj se změnil.")
        return value, app, binary

    def build(self, *, confirmed=False):
        if confirmed is not True:
            raise CalendarPilotError("Sestavení vyžaduje potvrzený vývojový krok.")
        self._safe(self.root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        with exclusive_file_lock(self.root / "build", timeout=0):
            if (self.root / "build.json").exists():
                previous = json.loads((self.root / "build.json").read_text())
                if previous.get("source_sha256") == _sha(self.source):
                    self._build_info()
                    return {"ok": True, "built": True, "reused": True}
                history = self.root / "build_history"
                history.mkdir(exist_ok=True, mode=0o700)
                self._write(history / (uuid4().hex + ".json"), previous)
            app = self.root / "builds" / uuid4().hex / self.app_name
            binary = app / ("Contents/MacOS/" + self.binary_name)
            binary.parent.mkdir(parents=True, mode=0o700)
            info = app / "Contents/Info.plist"
            info.write_bytes(plistlib.dumps({
                "CFBundleIdentifier": self.bundle_id, "CFBundleName": self.display_name,
                "CFBundleExecutable": binary.name, "CFBundlePackageType": "APPL",
                "CFBundleVersion": "1", "LSUIElement": True, "LSMinimumSystemVersion": "14.0",
                "NSCalendarsFullAccessUsageDescription": self.usage,
                "SamanthaPilotRoot": str(self.root),
            }))
            self._run(["/usr/bin/xcrun", "swiftc", "-swift-version", "5", str(self.source),
                       "-framework", "AppKit", "-framework", "EventKit", "-o", str(binary)], timeout=180)
            self._run(["/usr/bin/codesign", "--sign", "-", str(app)])
            self._run(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app)])
            test = json.loads(self._run([str(binary), "--self-test"]))
            if test != {"self_test": True, "checks": self.self_test_checks, "calendar_accessed": False}:
                raise CalendarPilotError("Nativní syntetická zkouška neprošla.")
            self._write(self.root / "build.json", {"app": str(app), "source_sha256": _sha(self.source),
                "binary_sha256": _sha(binary), "info_sha256": _sha(info), "bundle_id": self.bundle_id})
            return {"ok": True, "built": True, "reused": False, "native_self_test_checks": self.self_test_checks}

    def status(self):
        if not (self.root / "build.json").exists():
            return {"ok": True, "built": False, "calendar_writes": False}
        _, _, binary = self._build_info()
        result = json.loads(self._run([binary, "--status-json"]))
        if (result.get("operation") != "status" or result.get("schema") != 1
                or result.get("calendar_writes") is not False or result.get("bundle_identifier") != self.bundle_id
                or result.get("authorization") not in AUTHORIZATIONS):
            raise CalendarPilotError("Nativní stav nemá platný protokol.")
        return {"ok": True, "built": True, "authorization": result["authorization"],
                "context": "direct_cli", "calendar_writes": False, "observed_at": result["observed_at"]}

    def _request(self, operation, *, calendar_ids=None, days=7):
        self._build_info()
        now = datetime.now(timezone.utc).replace(microsecond=0)
        request_id = str(uuid4())
        directory = self._safe(self.root / "requests" / request_id)
        directory.mkdir(parents=True, mode=0o700)
        request = {"schema": 1, "operation": operation, "request_id": request_id,
                   "start": now.isoformat().replace("+00:00", "Z"),
                   "end": (now + timedelta(days=days)).isoformat().replace("+00:00", "Z")}
        if operation == "overview":
            request["calendar_ids"] = calendar_ids
        path = directory / "request.json"
        self._write(path, request)
        return path

    def _response(self, request_path, *, wait_seconds=0):
        request = json.loads(self._safe(request_path).read_text())
        response_path = self._safe(request_path.parent / "response.json")
        deadline = time.monotonic() + wait_seconds
        while not response_path.exists() and time.monotonic() < deadline:
            time.sleep(0.2)
        if not response_path.exists():
            return {"ok": True, "status": "pending", "request_id": request["request_id"], "calendar_writes": False}
        limit = 4 * 1024 * 1024 if request["operation"] == "overview" else 1024 * 1024
        if response_path.stat().st_size > limit:
            raise CalendarPilotError("Výsledek překročil povolenou velikost.")
        result = json.loads(response_path.read_text())
        if (result.get("request_id") != request["request_id"] or result.get("operation") != request["operation"]
                or result.get("schema") != 1 or result.get("calendar_writes") is not False
                or result.get("bundle_identifier") != self.bundle_id or result.get("authorization") not in AUTHORIZATIONS):
            raise CalendarPilotError("Výsledek patří jiné operaci nebo nepovoluje čtecí režim.")
        if result.get("status") == "read_verified":
            for key in ("calendar_count", "icloud_calendar_count", "event_count"):
                if type(result.get(key)) is not int or result[key] < 0:
                    raise CalendarPilotError("Čtecí výsledek nemá platné agregované počty.")
            if result.get("start") != request["start"] or result.get("end") != request["end"]:
                raise CalendarPilotError("Čtecí výsledek patří jinému časovému úseku.")
        # Calendar titles/IDs stay only in the private native response.
        public = {key: result[key] for key in ("status", "authorization", "calendar_count", "icloud_calendar_count",
                    "event_count", "start", "end", "observed_at", "parent_pid", "bundle_identifier") if key in result}
        ok = result.get("authorization") == "full_access" and result.get("status") in {"read_verified", "authorization_checked"}
        return {"ok": ok, "request_id": request["request_id"], "calendar_writes": False, **public}

    def _permission_response(self, pointer):
        saved = json.loads(self._safe(pointer).read_text())
        info, _, _ = self._build_info()
        if (saved.get("binary_sha256", info["binary_sha256"]) != info["binary_sha256"]
                or ("binary_sha256" not in saved and
                    (self.root / "build.json").stat().st_mtime > pointer.stat().st_mtime)):
            raise CalendarPilotError("Původní žádost o oprávnění patří jinému sestavení; nelze ji přehrát.")
        return self._response(self._safe(Path(saved["request"])))

    def authorize(self, *, confirmed=False):
        return self.authorize_current(confirmed=confirmed)

    def authorize_current(self, *, confirmed=False):
        """One GUI request per exact binary; an older grant is never replayed."""
        if confirmed is not True:
            raise CalendarPilotError("Žádost o systémový přístup vyžaduje výslovný souhlas.")
        info, app, _ = self._build_info()
        pointer = self._safe(self.root / ("authorization_request_" + info["binary_sha256"] + ".json"))
        with exclusive_file_lock(self.root / "authorize", timeout=0):
            if pointer.exists():
                return self._permission_response(pointer)
            legacy = self._safe(self.root / "authorization_request.json")
            if legacy.exists():
                saved = json.loads(legacy.read_text())
                if (saved.get("binary_sha256") == info["binary_sha256"] or
                        ("binary_sha256" not in saved and legacy.stat().st_mtime >= (self.root / "build.json").stat().st_mtime)):
                    return self._permission_response(legacy)
            request = self._request("authorize")
            self._write(pointer, {"request": str(request), "binary_sha256": info["binary_sha256"]})
            self._run(["/usr/bin/open", "-n", "-a", app, "--args", request])
            return self._response(request, wait_seconds=3)

    def read_overview(self, calendar_ids, *, confirmed=False, start=None, end=None):
        """Private bounded inventory and selected events in the actual launchd context."""
        if confirmed is not True:
            raise CalendarPilotError("Načtení přehledu vyžaduje výslovný pokyn.")
        if (not isinstance(calendar_ids, list) or len(calendar_ids) > 512
                or any(not isinstance(value, str) or not 0 < len(value) <= 512 for value in calendar_ids)
                or len(set(calendar_ids)) != len(calendar_ids)):
            raise CalendarPilotError("Neplatný výběr kalendářů.")
        if start is not None or end is not None:
            if (not isinstance(start, datetime) or not isinstance(end, datetime)
                    or start.tzinfo is None or end.tzinfo is None
                    or not 0 < (end-start).total_seconds() <= 31*86400):
                raise CalendarPilotError("Neplatné omezené období kontroly.")
        _, _, binary = self._build_info()
        request = self._request("overview", calendar_ids=calendar_ids, days=30)
        if start is not None:
            value = json.loads(request.read_text())
            value.update(start=start.isoformat(), end=end.isoformat())
            self._write(request, value)
        label = "com.samantha.calendar-readonly-overview." + request.parent.name
        self._write(request.parent / "launchd_plan.json", {
            "label": label, "binary": str(binary), "request": str(request), "persistent_install": False})
        self._run(["/bin/launchctl", "submit", "-l", label, "-o", request.parent / "stdout.log",
                   "-e", request.parent / "stderr.log", "--", binary, request])
        public = self._response(request, wait_seconds=25)
        if public.get("status") == "pending":
            raise CalendarPilotError("Načtení zatím není potvrzené. Poslední přehled není aktuálně ověřený.")
        registered = self.runner(["/bin/launchctl", "print", f"gui/{os.getuid()}/{label}"],
                                 capture_output=True, text=True, timeout=10, check=False).returncode == 0
        self._run(["/bin/launchctl", "remove", label])
        if not registered or public.get("parent_pid") != 1:
            raise CalendarPilotError("Servisní kontext přehledu nebyl ověřený.")
        result = json.loads(self._safe(request.parent / "response.json").read_text())
        if result.get("start") != json.loads(request.read_text())["start"] or result.get("end") != json.loads(request.read_text())["end"] or result.get("calendar_ids") != calendar_ids:
            raise CalendarPilotError("Přehled patří jinému výběru nebo období.")
        return result

    def probe(self, *, confirmed=False, service=False):
        if confirmed is not True:
            raise CalendarPilotError("Čtení kalendáře vyžaduje výslovně potvrzený pilot.")
        authorization = self.status().get("authorization")
        pointer = self._safe(self.root / "authorization_request.json")
        info, _, _ = self._build_info()
        current = self._safe(self.root / ("authorization_request_" + info["binary_sha256"] + ".json"))
        if current.exists():
            pointer = current
        if authorization != "full_access" and pointer.exists():
            authorization = self._permission_response(pointer).get("authorization")
        if authorization != "full_access":
            return {"ok": False, "status": "authorization_required", "calendar_writes": False}
        _, _, binary = self._build_info()
        request = self._request("probe")
        if not service:
            self._run([binary, request])
            return self._response(request)
        label = "com.samantha.calendar-readonly-probe." + request.parent.name
        plan = {"label": label, "binary": str(binary), "request": str(request), "persistent_install": False}
        self._write(request.parent / "launchd_plan.json", plan)
        # One owned transient user job; no ~/Library/LaunchAgents file, KeepAlive,
        # other service, calendar mutation, TCC reset or system policy change.
        self._run(["/bin/launchctl", "submit", "-l", label, "-o", request.parent / "stdout.log",
                   "-e", request.parent / "stderr.log", "--", binary, request])
        result = self._response(request, wait_seconds=25)
        registered = self.runner(["/bin/launchctl", "print", f"gui/{os.getuid()}/{label}"],
                                 capture_output=True, text=True, timeout=10, check=False).returncode == 0
        if result.get("status") == "pending":
            return {**result, "service_registered": registered, "service_verification": "pending", "job_label": label}
        self._run(["/bin/launchctl", "remove", label])
        proof = {**result, "service_registered": registered,
                 "launchd_parent_verified": result.get("parent_pid") == 1, "temporary_job_removed": True}
        proof["ok"] = bool(registered and proof["launchd_parent_verified"]
                           and result.get("status") == "read_verified")
        self._write(request.parent / "service_verified.json", proof)
        return proof
