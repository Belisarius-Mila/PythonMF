"""Read-only, redacted housekeeping card; slow audits run off the HTTP thread."""
from __future__ import annotations

import copy
import os
import re
import subprocess
import threading
import time

from app.worktree_cleanup import GRACE_SECONDS, Housekeeping, LABEL

REASONS = {
    "Commits are not integrated into main": "Práce ještě není začleněná do main.",
    "Workspace has staged, modified or untracked files": "Obsahuje rozpracované změny nebo nové soubory.",
    "Unknown ignored data must be preserved first": "Lokální data ještě potřebují ověřenou kopii.",
    "Workspace is in use": "Pracovní kopie se právě používá.",
    "Workspace is locked, missing or prunable": "Kopie je zamčená nebo její stav vyžaduje kontrolu.",
    "Cannot verify open files": "Používání pracovní kopie nelze ověřit.",
}


def scheduler_status():
    try:
        result = subprocess.run(["/bin/launchctl", "print", f"gui/{os.getuid()}/{LABEL}"],
                                capture_output=True, text=True, timeout=2, check=False)
        match = re.search(r"^\s*last exit code = (-?\d+)\s*$", result.stdout, re.M)
        return {"loaded": result.returncode == 0, "last_exit_code": int(match[1]) if match else None}
    except (OSError, subprocess.SubprocessError):
        return {"loaded": None, "last_exit_code": None}


class HousekeepingOverview:
    def __init__(self, service=None, *, probe=scheduler_status, clock=time.time, start=None):
        self.service = service or Housekeeping()
        self.probe, self.clock = probe, clock
        self.start = start or (lambda callback: threading.Thread(target=callback, daemon=True).start())
        self.lock = threading.Lock()
        self.snapshot = None
        self.pending = False
        self.failed = False
        self.next_audit = 0

    def _audit(self):
        try:
            value = {"rows": self.service.preview()["worktrees"], "scheduler": self.probe(),
                     "checked_at": self.clock()}
            failed = False
        except Exception:
            value, failed = None, True
        with self.lock:
            if value is not None:
                self.snapshot = value
            self.failed, self.pending = failed, False
            self.next_audit = self.clock() + (60 if failed else 300)

    def overview(self, *, refresh=False):
        now = self.clock()
        with self.lock:
            launch = not self.pending and (refresh or now >= self.next_audit)
            if launch:
                self.pending = True
            cached, pending, failed = copy.deepcopy(self.snapshot), self.pending, self.failed
        if launch:
            try:
                self.start(self._audit)
            except Exception:
                with self.lock:
                    self.pending, self.failed, self.next_audit = False, True, now + 60
                pending, failed = False, True
        activation = self.service._read("activation.json", {})
        latest = self.service._read("latest.json", {})
        entries = self.service._read("state.json", {"entries": {}})["entries"]
        rows = []
        if cached:
            known = {row["name"]: row for row in cached["rows"]}
            for name, entry in entries.items():
                if name not in known and entry.get("state") in {"retired", "removing", "attention"}:
                    known[name] = {"name": name, "eligible": False}
            for name, row in sorted(known.items()):
                if not re.fullmatch(r"data-[a-z0-9][a-z0-9-]*", name):
                    continue
                entry = entries.get(name, {})
                retirement = entry.get("state")
                ready_after = entry.get("marked_at", 0) + GRACE_SECONDS if retirement == "retired" else None
                if retirement in {"removing", "attention"}:
                    state, reason = "blocked", "Předchozí odstranění vyžaduje ruční ověření."
                elif not row.get("eligible"):
                    state, reason = "blocked", REASONS.get(row.get("reason"), "Stav kopie nelze ověřit.")
                elif retirement == "retired":
                    state = "pending"
                    reason = "Běží ochranná lhůta." if ready_after > now else "Čeká na ověření při hodinovém úklidu."
                else:
                    state, reason = "unclosed", "Čeká na označení dokončené práce."
                rows.append({"name": name, "state": state, "reason": reason, "ready_after": ready_after})
        counts = {state: sum(r["state"] == state for r in rows) if cached else None
                  for state in ("pending", "blocked", "unclosed")}
        run_at = latest.get("time")
        recent = isinstance(run_at, (float, int)) and not isinstance(run_at, bool) and -60 <= now - run_at <= 4500
        change = latest.get("free_change_bytes")
        if not isinstance(change, (int, float)) or isinstance(change, bool):
            change = None
        return {"ok": True, "enabled": activation.get("enabled") is True, "interval_seconds": 3600,
                "scheduler": cached["scheduler"] if cached else {"loaded": None, "last_exit_code": None},
                "audit": {"pending": pending, "failed": failed, "checked_at": cached["checked_at"] if cached else None,
                          "stale": not cached or failed or now - cached["checked_at"] > 300},
                "last_run": {"at": run_at, "state": latest.get("state"), "recent": recent,
                             "worktrees_removed": len(latest.get("removed", [])),
                             "autosave_removed": latest.get("autosave", {}).get("removed"),
                             "free_change_bytes": change}, "counts": counts, "rows": rows}


_OVERVIEW = HousekeepingOverview()


def housekeeping_overview(*, refresh=False, service=None):
    try:
        return (service or _OVERVIEW).overview(refresh=refresh)
    except Exception:
        return {"ok": False, "message": "Stav úklidu nelze ověřit."}
