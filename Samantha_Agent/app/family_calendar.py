"""Private family calendar registry and recurring-event calculations."""

from __future__ import annotations

import json
import re
import stat
import uuid
from collections.abc import Callable, Collection
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from app.file_persistence import lock_path_for, update_json_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FAMILY_CALENDAR_PATH = (
    PROJECT_ROOT / "data" / "private" / "family_calendar" / "people.json"
)
FAMILY_CALENDAR_SCHEMA_VERSION = 1
DEFAULT_LOOKAHEAD_DAYS = 30
NOTIFICATION_OFFSETS = frozenset({1, 2})
PERSON_ID_RE = re.compile(r"person-[a-z0-9]{8,40}")
NAME_DAY_RE = re.compile(r"(0[1-9]|1[0-2])-([0-2][0-9]|3[01])")
DEFAULT_FAMILY_CALENDAR_PREFILL: tuple[dict[str, str], ...] = (
    {"id": "person-prefill0001", "display_name": "Jana", "relation": "babička", "name_day": "05-24"},
    {"id": "person-prefill0002", "display_name": "Jana", "relation": "prababička", "name_day": "05-24"},
    {"id": "person-prefill0003", "display_name": "Miloslav", "relation": "děda", "name_day": "12-18"},
    {"id": "person-prefill0004", "display_name": "Karolina", "relation": "dcera", "name_day": "07-14"},
    {"id": "person-prefill0005", "display_name": "Kateřina", "relation": "dcera", "name_day": "11-25"},
    {"id": "person-prefill0006", "display_name": "Matěj", "relation": "vnuk", "name_day": "02-24"},
    {"id": "person-prefill0007", "display_name": "Tomík", "relation": "vnuk", "name_day": "03-07"},
    {"id": "person-prefill0008", "display_name": "Martinka", "relation": "vnučka", "name_day": "07-17"},
    {"id": "person-prefill0009", "display_name": "Renata", "relation": "prababička", "name_day": "10-13"},
    {"id": "person-prefill0010", "display_name": "Marie", "relation": "teta", "name_day": "09-12"},
    {"id": "person-prefill0011", "display_name": "Iva", "relation": "teta", "name_day": "12-01"},
    {"id": "person-prefill0012", "display_name": "Gisbert", "relation": "strejda", "name_day": "03-20"},
    {"id": "person-prefill0013", "display_name": "Adam", "relation": "bratranec", "name_day": "12-24"},
    {"id": "person-prefill0014", "display_name": "Marcela", "relation": "od Tomáše", "name_day": "04-20"},
    {"id": "person-prefill0015", "display_name": "Tomáš", "relation": "bratranec", "name_day": "03-07"},
)


@dataclass(frozen=True)
class FamilyPerson:
    person_id: str
    display_name: str
    relation: str
    birth_date: date | None
    name_day: tuple[int, int] | None
    reminders_enabled: bool
    active: bool
    created_at: str
    updated_at: str

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.person_id,
            "display_name": self.display_name,
            "relation": self.relation,
            "birth_date": self.birth_date.isoformat() if self.birth_date else "",
            "name_day": format_month_day(self.name_day),
            "reminders_enabled": self.reminders_enabled,
            "active": self.active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_summary(self, *, today: date) -> dict[str, Any]:
        age = age_on_date(self.birth_date, today) if self.birth_date else None
        return {
            **self.to_record(),
            "age": age,
        }


@dataclass(frozen=True)
class FamilyEvent:
    event_key: str
    person_id: str
    display_name: str
    relation: str
    event_type: str
    event_label: str
    event_date: date
    days_until: int
    age: int | None
    notification_due: bool
    catch_up: bool

    def to_summary(self) -> dict[str, Any]:
        return {
            "event_key": self.event_key,
            "person_id": self.person_id,
            "display_name": self.display_name,
            "relation": self.relation,
            "event_type": self.event_type,
            "event_label": self.event_label,
            "event_date": self.event_date.isoformat(),
            "days_until": self.days_until,
            "age": self.age,
            "notification_due": self.notification_due,
            "catch_up": self.catch_up,
        }


def load_family_people(
    path: Path = DEFAULT_FAMILY_CALENDAR_PATH,
    *,
    today: date | None = None,
) -> list[FamilyPerson]:
    target = Path(path)
    if not target.exists():
        return []
    raw = json.loads(target.read_text(encoding="utf-8"))
    return _people_from_store(raw, today=today or date.today())


def ensure_family_calendar_prefill(
    *,
    path: Path = DEFAULT_FAMILY_CALENDAR_PATH,
    records: Collection[dict[str, str]] = DEFAULT_FAMILY_CALENDAR_PREFILL,
    today: date | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Seed an empty private registry once without changing existing people."""

    today_date = today or date.today()
    timestamp = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
    prepared: list[FamilyPerson] = []
    seen_ids: set[str] = set()
    seen_people: set[tuple[str, str]] = set()
    for raw in records:
        if not isinstance(raw, dict):
            raise ValueError("Předvyplnění musí obsahovat strukturované osoby.")
        person_id = str(raw.get("id") or "").strip().casefold()
        if not PERSON_ID_RE.fullmatch(person_id) or person_id in seen_ids:
            raise ValueError("Předvyplnění obsahuje neplatnou nebo duplicitní identitu osoby.")
        display_name = _clean_text(
            raw.get("display_name", ""),
            field="Jméno",
            max_chars=120,
            required=True,
        )
        relation = _clean_text(raw.get("relation", ""), field="Vztah", max_chars=80)
        identity = (display_name.casefold(), relation.casefold())
        if identity in seen_people:
            raise ValueError("Předvyplnění obsahuje stejnou osobu vícekrát.")
        birth_date = parse_birth_date(str(raw.get("birth_date") or ""), today=today_date)
        name_day = parse_name_day(str(raw.get("name_day") or ""))
        if birth_date is None and name_day is None:
            raise ValueError("Předvyplněná osoba nemá datum narození ani svátku.")
        prepared.append(
            FamilyPerson(
                person_id=person_id,
                display_name=display_name,
                relation=relation,
                birth_date=birth_date,
                name_day=name_day,
                reminders_enabled=True,
                active=True,
                created_at=timestamp,
                updated_at=timestamp,
            )
        )
        seen_ids.add(person_id)
        seen_people.add(identity)
    if not prepared:
        raise ValueError("Předvyplnění neobsahuje žádné osoby.")

    target = Path(path)
    if target.exists():
        existing_people = load_family_people(target, today=today_date)
        if existing_people:
            return {"ok": True, "applied": False, "count": len(existing_people)}
    applied = False

    def update_store(current: Any) -> dict[str, Any]:
        nonlocal applied
        people = _people_from_store(current, today=today_date)
        if people:
            return _store_payload(people)
        applied = True
        return _store_payload(prepared)

    _prepare_private_target(target)
    update_json_file(
        target,
        update_store,
        default={"schema_version": FAMILY_CALENDAR_SCHEMA_VERSION, "people": []},
        sort_keys=True,
    )
    _harden_private_target(target)
    return {
        "ok": True,
        "applied": applied,
        "count": len(prepared) if applied else len(load_family_people(target, today=today_date)),
    }


def save_family_person(
    *,
    display_name: str,
    relation: str = "",
    birth_date: str = "",
    name_day: str = "",
    reminders_enabled: bool = True,
    active: bool = True,
    person_id: str = "",
    path: Path = DEFAULT_FAMILY_CALENDAR_PATH,
    today: date | None = None,
    now: datetime | None = None,
    person_id_factory: Callable[[], str] | None = None,
) -> FamilyPerson:
    """Create or update one private family-calendar person."""

    today_date = today or date.today()
    clean_name = _clean_text(display_name, field="Jméno", max_chars=120, required=True)
    clean_relation = _clean_text(relation, field="Vztah", max_chars=80)
    parsed_birth_date = parse_birth_date(birth_date, today=today_date)
    parsed_name_day = parse_name_day(name_day)
    if parsed_birth_date is None and parsed_name_day is None:
        raise ValueError("Doplň datum narození nebo datum svátku.")
    if not isinstance(reminders_enabled, bool) or not isinstance(active, bool):
        raise ValueError("Příznaky osoby musí být ano/ne.")

    target = Path(path)
    clean_person_id = str(person_id or "").strip().casefold()
    if clean_person_id and not PERSON_ID_RE.fullmatch(clean_person_id):
        raise ValueError("Identita osoby má neplatný formát.")
    timestamp = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
    created_or_updated: FamilyPerson | None = None

    def update_store(current: Any) -> dict[str, Any]:
        nonlocal created_or_updated
        people = _people_from_store(current, today=today_date)
        existing = next((person for person in people if person.person_id == clean_person_id), None)
        if clean_person_id and existing is None:
            raise ValueError("Osoba nebyla v rodinném kalendáři nalezena.")
        if existing is None:
            duplicate = next(
                (
                    person
                    for person in people
                    if person.active
                    and person.display_name.casefold() == clean_name.casefold()
                    and person.relation.casefold() == clean_relation.casefold()
                ),
                None,
            )
            if duplicate is not None:
                raise ValueError("Stejná osoba už v rodinném kalendáři existuje.")
            generated_id = (person_id_factory or _new_person_id)()
            if not PERSON_ID_RE.fullmatch(generated_id):
                raise ValueError("Nová identita osoby má neplatný formát.")
            if any(person.person_id == generated_id for person in people):
                raise ValueError("Nová identita osoby už existuje.")
            created_at = timestamp
            resolved_id = generated_id
        else:
            created_at = existing.created_at
            resolved_id = existing.person_id

        if active:
            duplicate = next(
                (
                    person
                    for person in people
                    if person.active
                    and person.person_id != resolved_id
                    and person.display_name.casefold() == clean_name.casefold()
                    and person.relation.casefold() == clean_relation.casefold()
                ),
                None,
            )
            if duplicate is not None:
                raise ValueError("Stejná osoba už v rodinném kalendáři existuje.")

        created_or_updated = FamilyPerson(
            person_id=resolved_id,
            display_name=clean_name,
            relation=clean_relation,
            birth_date=parsed_birth_date,
            name_day=parsed_name_day,
            reminders_enabled=reminders_enabled,
            active=active,
            created_at=created_at,
            updated_at=timestamp,
        )
        next_people = [person for person in people if person.person_id != resolved_id]
        next_people.append(created_or_updated)
        return _store_payload(next_people)

    _prepare_private_target(target)
    update_json_file(
        target,
        update_store,
        default={"schema_version": FAMILY_CALENDAR_SCHEMA_VERSION, "people": []},
        sort_keys=True,
    )
    _harden_private_target(target)
    if created_or_updated is None:  # pragma: no cover - defensive invariant.
        raise RuntimeError("Rodinný kalendář nevrátil uloženou osobu.")
    return created_or_updated


def set_family_person_active(
    person_id: str,
    *,
    active: bool,
    path: Path = DEFAULT_FAMILY_CALENDAR_PATH,
    today: date | None = None,
    now: datetime | None = None,
) -> FamilyPerson:
    if not isinstance(active, bool):
        raise ValueError("Příznak aktivity musí být ano/ne.")
    clean_person_id = str(person_id or "").strip().casefold()
    if not PERSON_ID_RE.fullmatch(clean_person_id):
        raise ValueError("Identita osoby má neplatný formát.")
    target = Path(path)
    timestamp = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
    updated_person: FamilyPerson | None = None

    def update_store(current: Any) -> dict[str, Any]:
        nonlocal updated_person
        people = _people_from_store(current, today=today or date.today())
        existing = next((person for person in people if person.person_id == clean_person_id), None)
        if existing is None:
            raise ValueError("Osoba nebyla v rodinném kalendáři nalezena.")
        updated_person = FamilyPerson(
            person_id=existing.person_id,
            display_name=existing.display_name,
            relation=existing.relation,
            birth_date=existing.birth_date,
            name_day=existing.name_day,
            reminders_enabled=existing.reminders_enabled,
            active=active,
            created_at=existing.created_at,
            updated_at=timestamp,
        )
        return _store_payload(
            [updated_person if person.person_id == clean_person_id else person for person in people]
        )

    _prepare_private_target(target)
    update_json_file(
        target,
        update_store,
        default={"schema_version": FAMILY_CALENDAR_SCHEMA_VERSION, "people": []},
        sort_keys=True,
    )
    _harden_private_target(target)
    if updated_person is None:  # pragma: no cover - defensive invariant.
        raise RuntimeError("Rodinný kalendář nevrátil upravenou osobu.")
    return updated_person


def family_calendar_status(
    *,
    path: Path = DEFAULT_FAMILY_CALENDAR_PATH,
    today: date | None = None,
    lookahead_days: int = DEFAULT_LOOKAHEAD_DAYS,
) -> dict[str, Any]:
    today_date = today or date.today()
    people = load_family_people(path, today=today_date)
    events = upcoming_family_events(people, today=today_date, lookahead_days=lookahead_days)
    return {
        "ok": True,
        "today": today_date.isoformat(),
        "lookahead_days": lookahead_days,
        "people": [person.to_summary(today=today_date) for person in people],
        "events": [event.to_summary() for event in events],
        "counts": {
            "people": len(people),
            "active_people": sum(person.active for person in people),
            "upcoming_events": len(events),
            "today": sum(event.days_until == 0 for event in events),
            "notification_due": sum(event.notification_due for event in events),
        },
    }


def upcoming_family_events(
    people: Collection[FamilyPerson],
    *,
    today: date,
    lookahead_days: int = DEFAULT_LOOKAHEAD_DAYS,
) -> list[FamilyEvent]:
    if lookahead_days < 0 or lookahead_days > 366:
        raise ValueError("Rozsah rodinného kalendáře musí být 0 až 366 dní.")
    events: list[FamilyEvent] = []
    for person in people:
        if not person.active:
            continue
        if person.birth_date is not None:
            event_date = next_annual_occurrence(person.birth_date.month, person.birth_date.day, today=today)
            days_until = (event_date - today).days
            if days_until <= lookahead_days:
                events.append(
                    _family_event(
                        person,
                        event_type="birthday",
                        event_label="narozeniny",
                        event_date=event_date,
                        days_until=days_until,
                        age=event_date.year - person.birth_date.year,
                    )
                )
        if person.name_day is not None:
            month, day = person.name_day
            event_date = next_annual_occurrence(month, day, today=today)
            days_until = (event_date - today).days
            if days_until <= lookahead_days:
                events.append(
                    _family_event(
                        person,
                        event_type="name_day",
                        event_label="svátek",
                        event_date=event_date,
                        days_until=days_until,
                        age=None,
                    )
                )
    return sorted(
        events,
        key=lambda event: (
            event.event_date,
            event.display_name.casefold(),
            event.relation.casefold(),
            event.event_type,
        ),
    )


def notification_candidates(
    events: Collection[FamilyEvent],
    *,
    sent_event_keys: Collection[str] = (),
) -> list[dict[str, Any]]:
    sent = {str(key).strip() for key in sent_event_keys if str(key).strip()}
    candidates = []
    for event in events:
        if not event.notification_due or event.event_key in sent:
            continue
        candidates.append(
            {
                **event.to_summary(),
                "delivery_kind": "catch_up" if event.catch_up else "scheduled",
            }
        )
    return candidates


def parse_birth_date(value: str, *, today: date) -> date | None:
    clean_value = str(value or "").strip()
    if not clean_value:
        return None
    try:
        parsed = date.fromisoformat(clean_value)
    except ValueError as exc:
        raise ValueError("Datum narození musí být ve formátu RRRR-MM-DD.") from exc
    if parsed > today:
        raise ValueError("Datum narození nemůže být v budoucnosti.")
    return parsed


def parse_name_day(value: str) -> tuple[int, int] | None:
    clean_value = str(value or "").strip()
    if not clean_value:
        return None
    if not NAME_DAY_RE.fullmatch(clean_value):
        raise ValueError("Datum svátku musí být ve formátu MM-DD.")
    month, day = (int(part) for part in clean_value.split("-", 1))
    try:
        date(2000, month, day)
    except ValueError as exc:
        raise ValueError("Datum svátku není platné.") from exc
    return month, day


def format_month_day(value: tuple[int, int] | None) -> str:
    if value is None:
        return ""
    month, day = value
    return f"{month:02d}-{day:02d}"


def next_annual_occurrence(month: int, day: int, *, today: date) -> date:
    occurrence = annual_occurrence(month, day, year=today.year)
    if occurrence < today:
        occurrence = annual_occurrence(month, day, year=today.year + 1)
    return occurrence


def annual_occurrence(month: int, day: int, *, year: int) -> date:
    try:
        return date(year, month, day)
    except ValueError:
        if month == 2 and day == 29:
            return date(year, 2, 28)
        raise ValueError("Opakované datum není platné.") from None


def age_on_date(birth_date: date, on_date: date) -> int:
    birthday = annual_occurrence(birth_date.month, birth_date.day, year=on_date.year)
    return on_date.year - birth_date.year - int(on_date < birthday)


def _family_event(
    person: FamilyPerson,
    *,
    event_type: str,
    event_label: str,
    event_date: date,
    days_until: int,
    age: int | None,
) -> FamilyEvent:
    notification_due = person.reminders_enabled and days_until in NOTIFICATION_OFFSETS
    return FamilyEvent(
        event_key=f"{person.person_id}:{event_type}:{event_date.isoformat()}",
        person_id=person.person_id,
        display_name=person.display_name,
        relation=person.relation,
        event_type=event_type,
        event_label=event_label,
        event_date=event_date,
        days_until=days_until,
        age=age,
        notification_due=notification_due,
        catch_up=notification_due and days_until == 1,
    )


def _people_from_store(raw: Any, *, today: date) -> list[FamilyPerson]:
    if not isinstance(raw, dict):
        raise ValueError("Rodinný kalendář musí být JSON objekt.")
    if raw.get("schema_version") != FAMILY_CALENDAR_SCHEMA_VERSION:
        raise ValueError("Rodinný kalendář má neznámé schéma.")
    records = raw.get("people")
    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        raise ValueError("Rodinný kalendář musí obsahovat seznam osob.")
    people = [_person_from_record(record, today=today) for record in records]
    identifiers = [person.person_id for person in people]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Rodinný kalendář obsahuje duplicitní identity osob.")
    return sorted(
        people,
        key=lambda person: (
            person.display_name.casefold(),
            person.relation.casefold(),
            person.person_id,
        ),
    )


def _person_from_record(raw: dict[str, Any], *, today: date) -> FamilyPerson:
    person_id = str(raw.get("id") or "").strip().casefold()
    if not PERSON_ID_RE.fullmatch(person_id):
        raise ValueError("Rodinný kalendář obsahuje neplatnou identitu osoby.")
    display_name = _clean_text(raw.get("display_name", ""), field="Jméno", max_chars=120, required=True)
    relation = _clean_text(raw.get("relation", ""), field="Vztah", max_chars=80)
    birth_date = parse_birth_date(str(raw.get("birth_date") or ""), today=today)
    name_day = parse_name_day(str(raw.get("name_day") or ""))
    if birth_date is None and name_day is None:
        raise ValueError("Osoba v rodinném kalendáři nemá žádné datum.")
    reminders_enabled = raw.get("reminders_enabled", True)
    active = raw.get("active", True)
    if not isinstance(reminders_enabled, bool) or not isinstance(active, bool):
        raise ValueError("Rodinný kalendář obsahuje neplatný příznak osoby.")
    return FamilyPerson(
        person_id=person_id,
        display_name=display_name,
        relation=relation,
        birth_date=birth_date,
        name_day=name_day,
        reminders_enabled=reminders_enabled,
        active=active,
        created_at=_clean_timestamp(raw.get("created_at")),
        updated_at=_clean_timestamp(raw.get("updated_at")),
    )


def _store_payload(people: Collection[FamilyPerson]) -> dict[str, Any]:
    ordered = sorted(
        people,
        key=lambda person: (
            person.display_name.casefold(),
            person.relation.casefold(),
            person.person_id,
        ),
    )
    return {
        "schema_version": FAMILY_CALENDAR_SCHEMA_VERSION,
        "people": [person.to_record() for person in ordered],
    }


def _clean_text(value: Any, *, field: str, max_chars: int, required: bool = False) -> str:
    cleaned = " ".join(str(value or "").split())
    if required and not cleaned:
        raise ValueError(f"{field} nesmí být prázdné.")
    if len(cleaned) > max_chars:
        raise ValueError(f"{field} je příliš dlouhé.")
    return cleaned


def _clean_timestamp(value: Any) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise ValueError("Rodinný kalendář neobsahuje čas změny osoby.")
    try:
        datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Rodinný kalendář obsahuje neplatný čas změny.") from exc
    return cleaned


def _new_person_id() -> str:
    return f"person-{uuid.uuid4().hex[:16]}"


def _prepare_private_target(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)


def _harden_private_target(path: Path) -> None:
    path.chmod(0o600)
    lock_path = lock_path_for(path)
    if lock_path.exists():
        lock_path.chmod(0o600)
    if stat.S_IMODE(path.stat().st_mode) != 0o600:  # pragma: no cover - defensive invariant.
        raise OSError("Soukromý rodinný kalendář nemá bezpečná oprávnění.")
