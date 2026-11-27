"""Private calendar selection and bounded read snapshots; no event mutations."""
from __future__ import annotations

from datetime import datetime, timezone
from collections import defaultdict
import hashlib
import json
import subprocess
from pathlib import Path

from app.calendar_access_pilot import CalendarAccessPilot, CalendarPilotError
from app.calendar_event_time import event_zone, exclusive_all_day_end
from app.file_persistence import FilePersistenceError, exclusive_file_lock


class CalendarOverviewError(ValueError):
    pass


class CalendarSelectionConflict(CalendarOverviewError):
    pass


def instant(value):
    if not isinstance(value, str):
        raise CalendarOverviewError("Neplatný čas v přehledu.")
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise CalendarOverviewError("Čas nemá časové pásmo.")
    return date


def text(value, limit):
    if not isinstance(value, str) or len(value) > limit:
        raise CalendarOverviewError("Neplatný údaj v přehledu.")
    return value


def event_key(event):
    """One display identity shared by current and retained occurrences."""
    values = [event['calendar_id'], event['title'], instant(event['start']).astimezone(timezone.utc).isoformat(),
              instant(event['end']).astimezone(timezone.utc).isoformat(), event['all_day']]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()


def event_end(event):
    return exclusive_all_day_end(instant(event['end']), all_day=event['all_day'], time_zone=event['timezone'])


class CalendarOverview:
    def __init__(self, pilot=None, *, clock=None):
        self.pilot = pilot or CalendarAccessPilot()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.path = self.pilot._safe(self.pilot.root / "overview.json")

    def _load(self):
        if not self.path.exists():
            return {"revision": 0, "read_calendar_ids": [], "target_calendar_id": "",
                    "calendars": [], "events": [], "last_loaded_at": None,
                    "inventory_at": None, "inventory_verified": False, "last_error": None}
        value = json.loads(self.pilot._safe(self.path).read_text())
        if not isinstance(value, dict) or type(value.get("revision")) is not int:
            raise CalendarOverviewError("Uložený výběr kalendářů nelze přečíst.")
        return value

    def _fresh(self, stamp, seconds=900):
        return bool(stamp and 0 <= (self.clock() - instant(stamp)).total_seconds() <= seconds)

    def snapshot(self):
        value = self._load()
        selected = value["read_calendar_ids"]
        ready = bool(selected and value.get("loaded_revision") == value["revision"]
                     and self._fresh(value.get("last_loaded_at")) and not value.get("last_error")
                     and not value.get("missing_calendar_ids") and not value.get("truncated"))
        # Earlier content can be shown only for the same exact saved selection.
        events = value["events"] if value.get("loaded_revision") == value["revision"] else []
        reason = value.get("last_error") or ("selection_required" if not selected else
                 "ready" if ready else "refresh_required")
        return {"ok": True, "revision": value["revision"], "read_calendar_ids": selected,
                "target_calendar_id": value["target_calendar_id"], "calendars": value["calendars"],
                "events": events,
                "retained_events": [row for row in value.get("retained_events", [])
                                    if row["calendar_id"] in selected],
                "last_loaded_at": value.get("last_loaded_at"),
                "inventory_at": value.get("inventory_at"), "start": value.get("start"),
                "end": value.get("end"), "ready": ready, "status": reason,
                "missing_calendar_ids": value.get("missing_calendar_ids", []),
                "truncated": value.get("truncated", False), "calendar_writes": False,
                "can_select": value.get("inventory_verified", False) and self._fresh(value.get("inventory_at")),
                "authorization": value.get("authorization", "unknown")}

    def _lock(self, *, timeout=0):
        self.pilot.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        return exclusive_file_lock(self.pilot._safe(self.pilot.root / "overview_operation"), timeout=timeout)

    def save_selection(self, payload):
        if (set(payload) != {"action", "confirmed", "expected_revision", "read_calendar_ids", "target_calendar_id"}
                or payload.get("confirmed") is not True or type(payload.get("expected_revision")) is not int):
            raise CalendarOverviewError("Uložení vyžaduje potvrzený aktuální výběr.")
        ids, target = payload["read_calendar_ids"], payload["target_calendar_id"]
        if (not isinstance(ids, list) or len(ids) > 512
                or any(not isinstance(item, str) for item in ids) or len(set(ids)) != len(ids)
                or not isinstance(target, str)):
            raise CalendarOverviewError("Neplatný výběr kalendářů.")
        with self._lock():
            value = self._load()
            if value["revision"] != payload["expected_revision"]:
                raise CalendarSelectionConflict("Výběr se mezitím změnil. Načti přehled znovu.")
            if not value.get("inventory_verified") or not self._fresh(value.get("inventory_at")):
                raise CalendarOverviewError("Nejdřív obnov dostupné kalendáře.")
            inventory = {row["id"]: row for row in value["calendars"]}
            if any(item not in inventory for item in ids) or (target and (target not in inventory or not inventory[target]["writable"])):
                raise CalendarOverviewError("Kalendář chybí nebo není vhodný jako budoucí cíl zápisu.")
            self._remember_overdue(value)
            value.update(revision=value["revision"] + 1, read_calendar_ids=sorted(ids),
                         target_calendar_id=target, events=[], last_error=None)
            self.pilot._write(self.path, value)
        return self.snapshot()

    def _validated_read(self, result, ids):
        if result.get("calendar_writes") is not False or result.get("calendar_ids") != ids:
            raise CalendarOverviewError("Přehled neodpovídá čtecímu výběru.")
        start, end = instant(result["start"]), instant(result["end"])
        observed = instant(result["observed_at"])
        if not 0 < (end-start).total_seconds() <= 31*86400 or abs((self.clock()-observed).total_seconds()) > 120:
            raise CalendarOverviewError("Přehled má neplatné období nebo stáří.")
        calendars, events = result.get("calendars"), result.get("events")
        if not isinstance(calendars, list) or len(calendars) > 512 or not isinstance(events, list) or len(events) > 2000:
            raise CalendarOverviewError("Přehled překročil povolený rozsah.")
        inventory = []
        for row in calendars:
            if not isinstance(row, dict) or type(row.get("writable")) is not bool:
                raise CalendarOverviewError("Chybí oprávnění kalendáře.")
            inventory.append({"id": text(row.get("id"), 512), "title": text(row.get("title"), 200),
                              "source_title": text(row.get("source_title"), 200), "writable": row["writable"]})
        available = {row["id"] for row in inventory}
        if len(available) != len(inventory) or "" in available:
            raise CalendarOverviewError("Nejednoznačný seznam kalendářů.")
        missing = sorted(set(ids) - available)
        if sorted(result.get("missing_calendar_ids", [])) != missing or type(result.get("truncated")) is not bool:
            raise CalendarOverviewError("Neplatný stav úplnosti přehledu.")
        clean_events = []
        for row in events:
            if not isinstance(row, dict):
                raise CalendarOverviewError("Neplatná událost.")
            a, b = instant(row.get("start")), instant(row.get("end"))
            if (row.get("calendar_id") not in set(ids) & available or not a < b or a >= end or b <= start
                    or type(row.get("all_day")) is not bool):
                raise CalendarOverviewError("Událost nepatří do vybraného přehledu.")
            zone = text(row.get("timezone"), 100)
            # EventKit also returns fixed-offset names such as GMT+0100.
            # Instants carry explicit offsets; all-day dates are supplied by the
            # native calendar, so no Python IANA lookup/reinterpretation is needed.
            days = {key: text(row.get(key), 10) for key in ("start_day", "end_day")}
            for day in days.values():
                datetime.strptime(day, "%Y-%m-%d")
            if row['all_day']:
                normalized_end = exclusive_all_day_end(b, all_day=True, time_zone=zone)
                if normalized_end != b:
                    local_end = b.astimezone(event_zone(zone))
                    if days['end_day'] != local_end.date().isoformat():
                        raise CalendarOverviewError("Neplatný konec celodenního období.")
                    days['end_day'] = normalized_end.astimezone(event_zone(zone)).date().isoformat()
            if row["all_day"] and days["end_day"] <= days["start_day"]:
                raise CalendarOverviewError("Neplatné celodenní období.")
            clean_events.append({"calendar_id": row["calendar_id"], "title": text(row.get("title"), 400),
                                 "start": row["start"], "end": row["end"], "timezone": zone,
                                 "all_day": row["all_day"], **days})
        return inventory, sorted(clean_events, key=lambda row: instant(row["start"])), missing

    def _remember_overdue(self, value, current_events=()):
        # Keep duplicate occurrences ambiguous. A later authoritative group replaces
        # the previous group for the same exact display identity.
        groups = defaultdict(list)
        for row in value.get("retained_events", []):
            groups[event_key(row)].append(row)
        for rows in (value.get("events", []), current_events):
            expired = defaultdict(list)
            for row in rows:
                if event_end(row) <= self.clock():
                    expired[event_key(row)].append(row)
            groups.update(expired)
        value["retained_events"] = [row for rows in groups.values() for row in rows]

    def follow_retained_edit(self, before, after):
        with self._lock():
            value = self._load()
            old = event_key(before)
            retained = value.get("retained_events", [])
            if not any(event_key(row) == old for row in retained):
                return
            value["retained_events"] = [row for row in retained if event_key(row) != old]
            if event_end(after) <= self.clock():
                value["retained_events"].append(after)
            self.pilot._write(self.path, value)

    def refresh(self, *, confirmed=False):
        if confirmed is not True:
            raise CalendarOverviewError("Načtení vyžaduje výslovný pokyn.")
        with self._lock():
            value = self._load()
            try:
                result = self.pilot.read_overview(value["read_calendar_ids"], confirmed=True)
                value["authorization"] = result.get("authorization", "unknown")
                if result.get("authorization") != "full_access" or result.get("status") != "overview_read":
                    value.update(last_error="authorization_required", inventory_verified=False)
                else:
                    inventory, events, missing = self._validated_read(result, value["read_calendar_ids"])
                    self._remember_overdue(value, events)
                    value.update(calendars=inventory, events=events, missing_calendar_ids=missing,
                                 truncated=result["truncated"], start=result["start"], end=result["end"],
                                 inventory_at=result["observed_at"], inventory_verified=True,
                                 last_loaded_at=result["observed_at"], loaded_revision=value["revision"],
                                 last_error="missing_calendars" if missing else "limited" if result["truncated"] else None)
            except (OSError, ValueError, CalendarPilotError, FilePersistenceError,
                    subprocess.SubprocessError, KeyError, TypeError):
                value.update(last_error="source_unavailable", inventory_verified=False)
            self.pilot._write(self.path, value)
        return self.snapshot()

    def authorize(self, *, confirmed=False):
        return self.pilot.authorize_current(confirmed=confirmed)

    def review_interval(self, start, end, *, confirmed=False):
        """Fresh bounded read for an explicit proposal review, without changing the overview."""
        if confirmed is not True:
            raise CalendarOverviewError("Kontrola kolizí vyžaduje výslovný pokyn.")
        with self._lock():
            selection = self._load()
            ids, target = selection['read_calendar_ids'], selection['target_calendar_id']
            if not ids or not target:
                raise CalendarOverviewError("V Kalendáři vyber čtené kalendáře i cílový kalendář a ulož výběr.")
            result = self.pilot.read_overview(ids, confirmed=True, start=start, end=end)
            if result.get('authorization') != 'full_access' or result.get('status') != 'overview_read':
                raise CalendarOverviewError("Kalendáře nejsou dostupné; potvrzení není možné. Obnov přístup na Macu.")
            inventory, events, missing = self._validated_read(result, ids)
            if (instant(result['start']) != start or instant(result['end']) != end
                    or missing or result['truncated']):
                raise CalendarOverviewError("Kontrola nemá úplný výsledek pro přesné období a výběr kalendářů.")
            destination = next((row for row in inventory if row['id'] == target and row['writable']), None)
            if not destination:
                raise CalendarOverviewError("Cílový kalendář chybí nebo není zapisovatelný.")
            return {'selection_revision': selection['revision'], 'target': destination,
                    'read_calendars': [row for row in inventory if row['id'] in ids],
                    'events': events, 'observed_at': result['observed_at'], 'calendar_writes': False}

    def execute(self, payload):
        if not isinstance(payload, dict):
            raise CalendarOverviewError("Neplatný požadavek.")
        if payload.get("action") == "save_selection":
            return self.save_selection(payload)
        if set(payload) != {"action", "confirmed"} or payload.get("confirmed") is not True:
            raise CalendarOverviewError("Akce vyžaduje výslovné potvrzení.")
        if payload["action"] == "refresh":
            return self.refresh(confirmed=True)
        if payload["action"] == "authorize":
            result = self.authorize(confirmed=True)
            return {"ok": True, "authorization_status": result.get("status"), **self.snapshot()}
        raise CalendarOverviewError("Neznámá kalendářová akce.")
