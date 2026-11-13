"""Local, opt-in supervision. Never starts, repairs or replays a watched agent."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.file_persistence import exclusive_file_lock, FileLockTimeoutError
from app.work_repository import JsonWorkRepository, RepositoryMutation, WorkRepositoryError

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / "data/private/agent_supervisor"
PRAGUE = ZoneInfo("Europe/Prague")
LABELS = {"email": "Poštovní agent", "cockpit": "Cockpit", "appserver": "App Server",
          "autosave": "Autosave", "storage": "Místo na SSD"}
BAD = {"warning", "error", "unknown"}
GOOD = {"ok", "working"}
CONFIG = {"version": 1, "enabled": False, "notifications_enabled": False,
          "failure_url": "", "recovery_url": ""}
MESSAGES = {
    "ok": "Kontrola v pořádku.", "disabled": "Vědomě vypnuto.",
    "unavailable": "Stav nelze ověřit.", "outside_hours": "Mimo provozní okno 07–22.",
    "service_missing": "Zapnutá služba není ověřeně načtená.",
    "heartbeat_missing": "Chybí čerstvý heartbeat služby (více než 5 minut).",
    "worker_failed": "Poslední běh služby skončil chybou.",
    "working": "Probíhá ověřený běh; dokončení zatím není potvrzené.",
    "working_long": "Ověřený běh trvá déle než 45 minut.",
    "scan_due": "Čekám na dokončení nového hodinového scanu.",
    "scan_missing": "Po termínu chybí úplný scan všech sledovaných schránek.",
    "source_error": "Některý sledovaný poštovní zdroj hlásí chybu.",
    "clock_invalid": "Časový důkaz chybí nebo je v budoucnosti.",
    "autosave_missing": "Neběží právě jeden autosave watcher.",
    "autosave_old": "Poslední autosave je starší než 20 minut.",
    "autosave_failed": "Poslední pokus o autosave selhal.",
    "storage_low": "Na SSD zbývá méně než 30 GiB.",
    "storage_critical": "Na SSD zbývá méně než 15 GiB.",
    "snapshot_stale": "Dohled nemá čerstvý snímek; poslední známý stav není živý důkaz.",
}


def instant(value):
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def age(value, now):
    stamp = instant(value)
    return (now - stamp).total_seconds() if stamp and stamp <= now else None


def row(identity, state, code, *, last_success_at="", next_due_at="", checked_at=""):
    if identity not in LABELS or state not in BAD | GOOD | {"disabled", "outside_hours"}:
        raise ValueError("Neplatný stav dohledu.")
    return {"id": identity, "label": LABELS[identity], "state": state, "code": code,
            "message": MESSAGES[code], "last_success_at": last_success_at,
            "next_due_at": next_due_at, "checked_at": checked_at}


def email_row(evidence, now):
    """Heartbeat, active work and complete source scans are different proofs."""
    identity = "email"
    if type(evidence.get("enabled")) is not bool:
        return row(identity, "unknown", "unavailable")
    if not evidence["enabled"]:
        return row(identity, "disabled", "disabled")
    if not all(evidence.get(k) is True for k in ("installed", "owned", "loaded")):
        return row(identity, "error", "service_missing")
    health = evidence.get("health", {})
    started_age = age(health.get("started_at"), now)
    if health.get("status") == "running" and evidence.get("worker_running") is True:
        if started_age is None:
            return row(identity, "unknown", "clock_invalid")
        return row(identity, "working" if started_age <= 2700 else "warning",
                   "working" if started_age <= 2700 else "working_long")
    heartbeat_age = age(health.get("finished_at"), now)
    if heartbeat_age is None:
        return row(identity, "unknown", "clock_invalid")
    if heartbeat_age > 300:
        return row(identity, "error", "heartbeat_missing")
    if health.get("status") not in {"completed", "already_completed", "outside_hours", "incomplete"}:
        return row(identity, "error", "worker_failed")
    local = now.astimezone(PRAGUE)
    if not 7 <= local.hour <= 22:
        next_day = local + timedelta(days=local.hour > 22)
        due = next_day.replace(hour=7, minute=0, second=0, microsecond=0)
        return row(identity, "outside_hours", "outside_hours", next_due_at=due.isoformat())
    slot = local.replace(minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    next_due = slot + timedelta(hours=1) if local.hour < 22 else (
        local + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
    sources = evidence.get("sources", [])
    if not sources:
        return row(identity, "unknown", "unavailable", next_due_at=next_due.isoformat())
    if any(s.get("error") or s.get("health") != "ok" for s in sources):
        return row(identity, "error", "source_error", next_due_at=next_due.isoformat())
    verified = []
    for source in sources:
        scan = source.get("followup_scan", {})
        at, finished = instant(scan.get("as_of")), instant(scan.get("verified_at"))
        if (scan.get("status") == "complete" and at and finished and at <= finished <= now
                and scan.get("uidvalidity") == source.get("uidvalidity")):
            verified.append(at)
    complete = len(verified) == len(sources)
    last = min(verified).isoformat() if complete else ""
    if complete and min(verified) >= slot:
        return row(identity, "ok", "ok", last_success_at=last, next_due_at=next_due.isoformat())
    waiting = (now - slot).total_seconds() <= 900
    return row(identity, "working" if waiting else "error", "scan_due" if waiting else "scan_missing",
               last_success_at=last, next_due_at=slot.isoformat())


def evaluate(evidence, now):
    if now.tzinfo is None:
        raise ValueError("Dohled vyžaduje časové pásmo.")
    now = now.astimezone(timezone.utc)
    result = []
    for identity in LABELS:
        item = evidence.get(identity, {})
        try:
            if item.get("probe_failed"):
                value = row(identity, "unknown", "unavailable")
            elif identity == "email":
                value = email_row(item, now)
            elif identity in {"cockpit", "appserver"}:
                good = item.get("reachable") is True
                value = row(identity, "ok" if good else "error", "ok" if good else "unavailable",
                            last_success_at=now.isoformat() if good else "")
            elif identity == "autosave":
                last = item.get("latest_modified_at", "")
                elapsed = age(last, now)
                if item.get("watcher_count") != 1:
                    value = row(identity, "error", "autosave_missing", last_success_at=last)
                elif item.get("last_error"):
                    value = row(identity, "error", "autosave_failed", last_success_at=last)
                elif elapsed is None:
                    value = row(identity, "unknown", "clock_invalid")
                else:
                    value = row(identity, "ok" if elapsed <= 1200 else "warning",
                                "ok" if elapsed <= 1200 else "autosave_old", last_success_at=last,
                                next_due_at=(instant(last) + timedelta(minutes=20)).isoformat())
            else:
                free = item.get("free_gib")
                if type(free) not in (float, int) or not math.isfinite(free) or free < 0:
                    value = row(identity, "unknown", "unavailable")
                else:
                    state, code = ("error", "storage_critical") if free < 15 else (
                        ("warning", "storage_low") if free < 30 else ("ok", "ok"))
                    value = row(identity, state, code)
        except (ValueError, TypeError, KeyError, AttributeError):
            value = row(identity, "unknown", "unavailable")
        value["checked_at"] = now.isoformat()
        if not value["next_due_at"]:
            value["next_due_at"] = (now + timedelta(seconds=120)).isoformat()
        result.append(value)
    return result


class AgentSupervisor:
    def __init__(self, root=ROOT, *, collector=None, sender=None, clock=None):
        self.root = Path(root)
        self.config_repo = JsonWorkRepository(self.root / "config.json", default=CONFIG)
        self.repository = JsonWorkRepository(self.root / "state.json", default={"version": 1,
            "rows": [], "incidents": {}, "events": {}, "last_run_at": ""})
        self.collector, self.sender = collector, sender
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def config(self):
        config = self.config_repo.read()
        if (type(config.get("version")) is not int or config.get("version") != 1 or any(type(config.get(k)) is not bool
                for k in ("enabled", "notifications_enabled"))
                or any(not isinstance(config.get(k), str) for k in ("failure_url", "recovery_url"))):
            raise WorkRepositoryError("Neplatná konfigurace dohledu.")
        if config["notifications_enabled"]:
            from app.email.pushcut import _validate_url
            for key in ("failure_url", "recovery_url"):
                _validate_url(config[key], webhook=True)
            if config["failure_url"] == config["recovery_url"]:
                raise ValueError("Výpadek a obnova potřebují dvě různá Pushcut oznámení.")
        return config

    def configure(self, *, enabled, notifications_enabled=False, failure_url="", recovery_url="", confirmed=False):
        if confirmed is not True or type(enabled) is not bool or type(notifications_enabled) is not bool:
            raise ValueError("Konfigurace dohledu vyžaduje výslovné potvrzení.")
        if not isinstance(failure_url, str) or not isinstance(recovery_url, str):
            raise ValueError("Neplatná konfigurace oznámení.")
        candidate = {**CONFIG, "enabled": enabled, "notifications_enabled": notifications_enabled,
                     "failure_url": failure_url, "recovery_url": recovery_url}
        if notifications_enabled:
            from app.email.pushcut import _validate_url
            for key in ("failure_url", "recovery_url"):
                _validate_url(candidate[key], webhook=True)
            if failure_url == recovery_url:
                raise ValueError("Výpadek a obnova potřebují různá oznámení.")
        elif failure_url or recovery_url:
            raise ValueError("Vypnutá oznámení neukládají webhooky.")
        with exclusive_file_lock(self.root / "worker", timeout=0):
            self.config_repo.transact(lambda _: RepositoryMutation(candidate))
        return self.status()

    def status(self):
        config, document = self.config(), self.repository.read()
        if document.get("version") != 1:
            raise WorkRepositoryError("Neznámá verze dohledu.")
        elapsed = age(document.get("last_run_at"), self.clock().astimezone(timezone.utc))
        recent = elapsed is not None and elapsed <= 300
        rows = []
        if recent:
            stored = document.get("rows", [])
            if (not isinstance(stored, list) or len(stored) != len(LABELS)
                    or {v.get("id") for v in stored if isinstance(v, dict)} != set(LABELS)):
                raise WorkRepositoryError("Poškozený snímek dohledu.")
            for value in stored:
                if value.get("code") not in MESSAGES:
                    raise WorkRepositoryError("Poškozený stav dohledu.")
                times = {key: value.get(key) if instant(value.get(key)) else ""
                         for key in ("last_success_at", "next_due_at", "checked_at")}
                rows.append(row(value["id"], value["state"], value["code"], **times))
        if not recent:
            rows = [row(key, "unknown", "snapshot_stale") for key in LABELS]
        return {"ok": True, "version": 1, "configured": config["enabled"],
                "notifications_enabled": config["notifications_enabled"], "snapshot_recent": recent,
                "worker_recent": recent and config["enabled"] and document.get("origin") == "scheduled",
                "last_run_at": document.get("last_run_at", ""), "origin": document.get("origin", ""),
                "rows": rows, "external_watchdog": "not_configured", "read_only": True,
                "notification_counts": {state: len({e.get("delivery_id", key) for key, e in document.get("events", {}).items()
                    if e.get("status") == state})
                    for state in ("pending", "accepted", "rejected", "delivery_unknown", "superseded")}}

    def check(self, *, confirmed=False, scheduled=False):
        """Manual sampling never sends. Scheduled sampling needs prior opt-in."""
        if type(scheduled) is not bool or type(confirmed) is not bool:
            raise ValueError("Neplatný režim dohledu.")
        if not scheduled and confirmed is not True:
            raise ValueError("Ruční kontrola vyžaduje potvrzení.")
        if scheduled and not self.config()["enabled"]:
            return {"ok": True, "status": "disabled"}
        try:
            with exclusive_file_lock(self.root / "worker", timeout=0):
                config = self.config()
                if scheduled and not config["enabled"]:
                    return {"ok": True, "status": "disabled"}
                collector = self.collector
                if collector is None:
                    from app.agent_supervisor_probes import collect
                    collector = collect
                evidence = collector()
                now = self.clock().astimezone(timezone.utc)
                rows = evaluate(evidence, now)
                at = now.isoformat()
                def save(document):
                    if document.get("version") != 1:
                        raise WorkRepositoryError("Neznámá verze dohledu.")
                    if not scheduled:
                        document.update(rows=rows, last_run_at=at, origin="manual")
                        return RepositoryMutation(document)
                    incidents, events = document["incidents"], document["events"]
                    for event in events.values():
                        if event["status"] == "sending":
                            event["status"] = "delivery_unknown"
                    def queue(kind, incident):
                        key = incident["id"] + ":" + kind
                        if key not in events and scheduled and config["notifications_enabled"]:
                            events[key] = {"kind": kind, "incident_id": incident["id"],
                                "agent_id": incident["agent_id"], "status": "pending", "at": at}
                    for value in rows:
                        identity = value["id"]
                        current = incidents.get(identity)
                        if value["state"] in BAD:
                            if not current or current.get("closed_at"):
                                current = {"id": uuid4().hex, "agent_id": identity, "opened_at": at,
                                           "closed_at": ""}
                                incidents[identity] = current
                            current.update(code=value["code"], state=value["state"])
                            queue("failure", current)
                        elif value["state"] == "working":
                            # Starting work is not proof that the missing scan has recovered.
                            continue
                        elif current and not current.get("closed_at"):
                            current["closed_at"] = at
                            failure = events.get(current["id"] + ":failure", {})
                            if failure.get("status") == "pending":
                                failure["status"] = "superseded"
                            if value["state"] == "ok" and failure.get("status") == "accepted":
                                queue("recovery", current)
                    states = {v["id"]: v["state"] for v in rows}
                    for event in events.values():
                        current = incidents.get(event["agent_id"], {})
                        relevant = (event["incident_id"] == current.get("id") and (
                            (event["kind"] == "failure" and not current.get("closed_at")
                             and states[event["agent_id"]] in BAD | {"working"}) or
                            (event["kind"] == "recovery" and current.get("closed_at")
                             and states[event["agent_id"]] in GOOD)))
                        if event["status"] == "pending" and not relevant:
                            event["status"] = "superseded"
                    document.update(rows=rows, last_run_at=at, origin="scheduled" if scheduled else "manual")
                    return RepositoryMutation(document)
                self.repository.transact(save)
                if scheduled and config["notifications_enabled"]:
                    self._dispatch(config)
                return self.status()
        except FileLockTimeoutError:
            return {"ok": True, "status": "busy"}

    def _dispatch(self, config):
        from app.email.pushcut import trigger_pushcut
        sender = self.sender or trigger_pushcut
        document = self.repository.read()
        states = {value["id"]: value["state"] for value in document["rows"]}
        for kind in ("failure", "recovery"):
            identities = [key for key, event in document["events"].items()
                          if event["status"] == "pending" and event["kind"] == kind
                          and (states[event["agent_id"]] in BAD if kind == "failure"
                               else states[event["agent_id"]] == "ok")]
            if not identities:
                continue
            delivery_id = uuid4().hex
            # The worker lock serializes config, reservations and network calls.
            def reserve(current):
                for identity in identities:
                    current["events"][identity].update(status="sending", delivery_id=delivery_id)
                return RepositoryMutation(current)
            self.repository.transact(reserve)
            try:
                result = sender(config[kind + "_url"])
                state = result.get("status", "delivery_unknown")
            except Exception:
                state = "delivery_unknown"
            if state not in {"accepted", "rejected", "delivery_unknown"}:
                state = "delivery_unknown"
            def finish(current):
                for identity in identities:
                    current["events"][identity]["status"] = state
                return RepositoryMutation(current)
            self.repository.transact(finish)
