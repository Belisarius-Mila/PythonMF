"""C03a reference model for stable identity, provenance, revisions, and privacy.

This is pure domain logic. C03b owns the versioned API encoding; C04/C05/C08
must integrate and verify it on the phone, server, and Viewer separately.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from enum import StrEnum
from typing import Iterable, TypeAlias
from uuid import UUID


class ContractError(ValueError):
    """Invalid C03a data must not be silently repaired or published."""


class RevisionConflict(ContractError):
    """An operation targeted a different metadata revision."""


class OperationConflict(ContractError):
    """One operation ID was reused with different content."""


class Privacy(StrEnum):
    OWNER_ONLY = "owner_only"
    DIARY = "diary"


class MomentKind(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"
    COMMENT = "comment"
    REFLECTION = "reflection"
    MARKER = "marker"


class TimeSource(StrEnum):
    DEVICE_CAPTURE = "device_capture"
    IMPORT_METADATA = "import_metadata"
    IMPORT_ASSIGNMENT = "import_assignment"


def _uuid(value: str) -> None:
    try:
        if str(UUID(value)) != value:
            raise ValueError
    except (TypeError, ValueError, AttributeError) as error:
        raise ContractError("ID must be a canonical lowercase UUID") from error


def _day(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
        return parsed
    except (TypeError, ValueError, AttributeError) as error:
        raise ContractError("chapter date must be YYYY-MM-DD") from error


def _wall(value: str) -> datetime:
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", value) is None:
        raise ContractError("local wall time must have seconds and no inferred offset")
    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise ContractError("invalid local wall time") from error


def _instant(milliseconds: int) -> datetime:
    if isinstance(milliseconds, bool) or not isinstance(milliseconds, int):
        raise ContractError("UTC milliseconds must be an integer")
    try:
        return datetime.fromtimestamp(milliseconds / 1000, timezone.utc)
    except (OverflowError, OSError, ValueError) as error:
        raise ContractError("UTC milliseconds are outside the supported date range") from error


def _operation_fields(id: str, moment_id: str, device_sequence: int, expected_revision: int) -> None:
    _uuid(id)
    _uuid(moment_id)
    if (isinstance(device_sequence, bool) or not isinstance(device_sequence, int)
            or device_sequence < 1):
        raise ContractError("device sequence must be positive")
    if (isinstance(expected_revision, bool) or not isinstance(expected_revision, int)
            or expected_revision < 1):
        raise ContractError("expected revision must be positive")


@dataclass(frozen=True, slots=True)
class CaptureTime:
    utc_ms: int | None
    local_wall: str | None
    utc_offset_minutes: int | None
    time_zone_id: str | None
    source: TimeSource
    uncertain: bool = False

    def __post_init__(self) -> None:
        utc = _instant(self.utc_ms) if self.utc_ms is not None else None
        local = _wall(self.local_wall) if self.local_wall is not None else None
        offset = self.utc_offset_minutes
        if offset is not None and (isinstance(offset, bool) or not isinstance(offset, int) or not -840 <= offset <= 840):
            raise ContractError("UTC offset is invalid")
        if self.time_zone_id is not None and (not isinstance(self.time_zone_id, str) or not self.time_zone_id.strip()):
            raise ContractError("time zone ID is invalid")
        if self.source is TimeSource.DEVICE_CAPTURE:
            if utc is None or local is None or offset is None or self.uncertain:
                raise ContractError("device capture requires known UTC, local time, and offset")
        elif self.source is TimeSource.IMPORT_ASSIGNMENT:
            if utc is not None or local is not None or offset is not None or not self.uncertain:
                raise ContractError("assigned import day cannot invent capture time")
        elif self.source is TimeSource.IMPORT_METADATA:
            if (utc is None or local is None or offset is None) and not self.uncertain:
                raise ContractError("incomplete import metadata must be marked uncertain")
        else:
            raise ContractError("unknown time provenance")
        if utc is not None and local is not None and offset is not None:
            observed = (utc + timedelta(minutes=offset)).replace(tzinfo=None)
            if observed.replace(microsecond=0) != local:
                raise ContractError("UTC, local wall time, and recorded offset disagree")

    @property
    def initial_chapter_date(self) -> str | None:
        return self.local_wall[:10] if self.local_wall is not None else None


@dataclass(frozen=True, slots=True)
class LocationFix:
    latitude: float
    longitude: float
    measured_at_utc_ms: int
    horizontal_accuracy_m: float

    def __post_init__(self) -> None:
        from math import isfinite

        if not all(isfinite(value) for value in (self.latitude, self.longitude, self.horizontal_accuracy_m)):
            raise ContractError("location values must be finite")
        if not -90 <= self.latitude <= 90 or not -180 <= self.longitude <= 180:
            raise ContractError("location coordinates are invalid")
        if self.horizontal_accuracy_m < 0:
            raise ContractError("location accuracy is invalid")
        _instant(self.measured_at_utc_ms)

    def usable_at(self, capture_utc_ms: int | None) -> bool:
        return capture_utc_ms is not None and 0 <= capture_utc_ms - self.measured_at_utc_ms <= 120_000

    @property
    def approximate(self) -> bool:
        return self.horizontal_accuracy_m > 100


@dataclass(frozen=True, slots=True)
class Trip:
    id: str
    name: str
    language: str
    active: bool
    viewer_enabled: bool = False
    start_date: str | None = None

    def __post_init__(self) -> None:
        _uuid(self.id)
        if not isinstance(self.name, str) or not isinstance(self.language, str) or not self.name.strip() or not self.language.strip():
            raise ContractError("trip name and language are required")
        if not isinstance(self.active, bool) or not isinstance(self.viewer_enabled, bool):
            raise ContractError("trip flags must be explicit")
        if self.start_date is not None:
            _day(self.start_date)


@dataclass(frozen=True, slots=True)
class JourneyDay:
    id: str
    trip_id: str
    local_date: str

    def __post_init__(self) -> None:
        _uuid(self.id)
        _uuid(self.trip_id)
        _day(self.local_date)


@dataclass(frozen=True, slots=True)
class Moment:
    id: str
    trip_id: str
    day_id: str
    chapter_date: str
    kind: MomentKind
    captured: CaptureTime
    privacy: str
    revision: int = 1
    hidden: bool = False
    important: bool = False
    related_moment_id: str | None = None
    location: LocationFix | None = None

    def __post_init__(self) -> None:
        for value in (self.id, self.trip_id, self.day_id):
            _uuid(value)
        _day(self.chapter_date)
        if not isinstance(self.kind, MomentKind) or not isinstance(self.captured, CaptureTime):
            raise ContractError("Moment kind and capture provenance are required")
        if self.related_moment_id is not None:
            _uuid(self.related_moment_id)
            if self.related_moment_id == self.id:
                raise ContractError("a Moment cannot link to itself")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 1:
            raise ContractError("Moment revision must be positive")
        if not isinstance(self.privacy, str):
            raise ContractError("privacy must be an explicit string")
        if self.kind is MomentKind.REFLECTION and self.revision == 1 and self.privacy != Privacy.OWNER_ONLY.value:
            raise ContractError("a new standalone reflection must start owner-only")
        if not isinstance(self.hidden, bool) or not isinstance(self.important, bool):
            raise ContractError("Moment flags must be explicit")


@dataclass(frozen=True, slots=True)
class Asset:
    id: str
    moment_id: str
    media_kind: str
    origin: str
    byte_count: int
    sha256: str | None = None
    duration_ms: int | None = None

    def __post_init__(self) -> None:
        _uuid(self.id)
        _uuid(self.moment_id)
        if not isinstance(self.media_kind, str) or self.media_kind not in {"photo", "video", "audio"}:
            raise ContractError("unknown media kind")
        if not isinstance(self.origin, str) or self.origin not in {"camera", "recording", "photo_picker", "file_import"}:
            raise ContractError("asset origin is invalid")
        if isinstance(self.byte_count, bool) or not isinstance(self.byte_count, int) or self.byte_count < 0:
            raise ContractError("asset byte count is invalid")
        if self.sha256 is not None and (not isinstance(self.sha256, str)
                                        or re.fullmatch(r"[0-9a-f]{64}", self.sha256) is None):
            raise ContractError("asset SHA-256 is invalid")
        if self.duration_ms is not None and (
            isinstance(self.duration_ms, bool) or not isinstance(self.duration_ms, int)
            or self.media_kind == "photo" or self.duration_ms < 0
        ):
            raise ContractError("duration must come from an audio or video media timeline")


def create_moment(
    *, id: str, trip: Trip, day: JourneyDay, kind: MomentKind,
    captured: CaptureTime, new_moment_privacy: Privacy,
    related_moment_id: str | None = None, location: LocationFix | None = None,
) -> Moment:
    """Create one explicit offline identity; never infer a merge from nearby time."""
    if day.trip_id != trip.id:
        raise ContractError("chapter belongs to another trip")
    if captured.initial_chapter_date is not None and day.local_date != captured.initial_chapter_date:
        raise ContractError("initial chapter must use the recorded local start date")
    if not isinstance(kind, MomentKind):
        raise ContractError("unknown Moment kind")
    if kind is MomentKind.REFLECTION:
        privacy = Privacy.OWNER_ONLY
    else:
        try:
            privacy = Privacy(new_moment_privacy)
        except ValueError as error:
            raise ContractError("new Moment privacy must be known") from error
    if location is not None and not location.usable_at(captured.utc_ms):
        location = None  # stale/unknown location cannot masquerade as current
    return Moment(
        id=id, trip_id=trip.id, day_id=day.id, chapter_date=day.local_date,
        kind=kind, captured=captured, privacy=privacy.value,
        related_moment_id=related_moment_id, location=location,
    )


def create_private_addendum(
    *, id: str, trip: Trip, parent: Moment, day: JourneyDay, captured: CaptureTime,
) -> Moment:
    """A private reflection links to, but never changes, the original Moment."""
    if parent.trip_id != trip.id:
        raise ContractError("private addendum belongs to another trip")
    return create_moment(
        id=id, trip=trip, day=day, kind=MomentKind.REFLECTION,
        captured=captured, new_moment_privacy=Privacy.OWNER_ONLY,
        related_moment_id=parent.id,
    )


@dataclass(frozen=True, slots=True)
class PrivacyChange:
    id: str
    moment_id: str
    device_sequence: int
    expected_revision: int
    new_privacy: Privacy
    user_action: str

    def __post_init__(self) -> None:
        _operation_fields(self.id, self.moment_id, self.device_sequence, self.expected_revision)
        if not isinstance(self.new_privacy, Privacy):
            raise ContractError("unknown privacy cannot be chosen for a local change")
        if self.user_action not in {"lock", "unlock", "insert_reflection_into_diary"}:
            raise ContractError("privacy change needs an explicit user action")

    @property
    def queue_priority(self) -> int:
        return 0  # privacy metadata is ahead of media work


@dataclass(frozen=True, slots=True)
class HiddenChange:
    id: str
    moment_id: str
    device_sequence: int
    expected_revision: int
    hidden: bool

    def __post_init__(self) -> None:
        _operation_fields(self.id, self.moment_id, self.device_sequence, self.expected_revision)
        if not isinstance(self.hidden, bool):
            raise ContractError("hidden must be explicit")

    @property
    def queue_priority(self) -> int:
        return 0  # hiding is also access-affecting metadata


@dataclass(frozen=True, slots=True)
class ChapterChange:
    id: str
    moment_id: str
    device_sequence: int
    expected_revision: int
    day: JourneyDay

    def __post_init__(self) -> None:
        _operation_fields(self.id, self.moment_id, self.device_sequence, self.expected_revision)


MetadataOperation: TypeAlias = PrivacyChange | HiddenChange | ChapterChange


@dataclass(frozen=True, slots=True)
class MomentHistory:
    versions: tuple[Moment, ...]
    operations: tuple[MetadataOperation, ...] = ()

    def __post_init__(self) -> None:
        if not self.versions or self.versions[0].revision != 1:
            raise ContractError("history needs its original revision")
        if len(self.operations) != len(self.versions) - 1:
            raise ContractError("each later revision needs one operation")
        if any(value.id != self.versions[0].id or value.revision != index + 1
               for index, value in enumerate(self.versions)):
            raise ContractError("Moment history is not consecutive and immutable")
        if any(operation.moment_id != self.versions[0].id
               or operation.expected_revision != index + 1
               or (index > 0 and operation.device_sequence <= self.operations[index - 1].device_sequence)
               for index, operation in enumerate(self.operations)):
            raise ContractError("Moment operation history is inconsistent")

    @property
    def current(self) -> Moment:
        return self.versions[-1]

    def apply(self, operation: MetadataOperation) -> MomentHistory:
        for prior in self.operations:
            if prior.id == operation.id:
                if prior == operation:
                    return self  # exact retry has the same effect
                raise OperationConflict("operation ID was reused with other content")
        current = self.current
        if operation.moment_id != current.id:
            raise ContractError("operation targets another Moment")
        if operation.expected_revision != current.revision:
            raise RevisionConflict("expected metadata revision does not match")
        if self.operations and operation.device_sequence <= self.operations[-1].device_sequence:
            raise ContractError("device operation sequence cannot move backward")
        if isinstance(operation, PrivacyChange):
            if operation.new_privacy.value == current.privacy:
                raise ContractError("privacy is already at the requested value")
            if operation.new_privacy is Privacy.OWNER_ONLY:
                if operation.user_action != "lock":
                    raise ContractError("locking requires the lock action")
            elif current.privacy == Privacy.OWNER_ONLY:
                required = ("insert_reflection_into_diary" if current.kind is MomentKind.REFLECTION
                            else "unlock")
                if operation.user_action != required:
                    raise ContractError("release requires the matching explicit action")
            else:
                raise ContractError("unknown privacy cannot be released")
            updated = replace(current, privacy=operation.new_privacy.value, revision=current.revision + 1)
        elif isinstance(operation, HiddenChange):
            if operation.hidden == current.hidden:
                raise ContractError("hidden state is already at the requested value")
            updated = replace(current, hidden=operation.hidden, revision=current.revision + 1)
        elif isinstance(operation, ChapterChange):
            if operation.day.trip_id != current.trip_id:
                raise ContractError("new chapter belongs to another trip")
            if operation.day.id == current.day_id:
                raise ContractError("Moment is already in this chapter")
            updated = replace(
                current, day_id=operation.day.id,
                chapter_date=operation.day.local_date, revision=current.revision + 1,
            )
        else:
            raise ContractError("unsupported metadata operation")
        return MomentHistory(self.versions + (updated,), self.operations + (operation,))


@dataclass(frozen=True, slots=True)
class ServerMoment:
    """Only a server-accepted revision may enter a future Viewer projection."""

    id: str
    trip_id: str
    accepted_revision: int
    privacy: str
    hidden: bool
    received_at_utc_ms: int

    def __post_init__(self) -> None:
        _uuid(self.id)
        _uuid(self.trip_id)
        if (isinstance(self.accepted_revision, bool) or not isinstance(self.accepted_revision, int)
                or self.accepted_revision < 1):
            raise ContractError("server revision is invalid")
        if not isinstance(self.privacy, str) or not isinstance(self.hidden, bool):
            raise ContractError("server privacy and hidden state must be explicit")
        _instant(self.received_at_utc_ms)


def server_revision_pending(local: Moment, accepted: ServerMoment | None) -> bool:
    """Local metadata is pending until that exact state is accepted by the server."""
    if accepted is None:
        return True
    if local.id != accepted.id or local.trip_id != accepted.trip_id:
        raise ContractError("server snapshot belongs to another Moment")
    return (local.revision != accepted.accepted_revision
            or local.privacy != accepted.privacy or local.hidden != accepted.hidden)


def select_viewer_candidates(trip: Trip, accepted: Iterable[ServerMoment]) -> tuple[str, ...]:
    """Return only allowed IDs; do not return excluded counts or local drafts."""
    if not trip.viewer_enabled:
        return ()
    latest: dict[str, ServerMoment] = {}
    disputed: set[str] = set()
    for item in accepted:
        if item.trip_id != trip.id:
            continue
        prior = latest.get(item.id)
        if prior is None or item.accepted_revision > prior.accepted_revision:
            latest[item.id] = item
            disputed.discard(item.id)
        elif item.accepted_revision == prior.accepted_revision and item != prior:
            disputed.add(item.id)  # inconsistent server evidence fails closed
    return tuple(sorted(
        item.id for item in latest.values()
        if item.id not in disputed and item.privacy == Privacy.DIARY.value and not item.hidden
    ))


@dataclass(frozen=True, slots=True)
class TextDraft:
    moment_id: str
    base_revision_id: str | None
    content: str
    updated_at_utc_ms: int

    def __post_init__(self) -> None:
        _uuid(self.moment_id)
        if self.base_revision_id is not None:
            _uuid(self.base_revision_id)
        if not isinstance(self.content, str):
            raise ContractError("draft content must be text")
        _instant(self.updated_at_utc_ms)


@dataclass(frozen=True, slots=True)
class TextRevision:
    id: str
    moment_id: str
    role: str
    content: str
    source_ids: tuple[str, ...]
    parent_revision_id: str | None
    created_at_utc_ms: int

    def __post_init__(self) -> None:
        _uuid(self.id)
        _uuid(self.moment_id)
        if not isinstance(self.content, str) or not isinstance(self.source_ids, tuple):
            raise ContractError("text content and source IDs are invalid")
        for source_id in self.source_ids:
            _uuid(source_id)
        if self.parent_revision_id is not None:
            _uuid(self.parent_revision_id)
        if self.role not in {"typed_source", "transcript_raw", "transcript_clean", "human_revision"}:
            raise ContractError("text role is invalid")
        _instant(self.created_at_utc_ms)


@dataclass(frozen=True, slots=True)
class TextHistory:
    revisions: tuple[TextRevision, ...] = ()
    draft: TextDraft | None = None

    def add(self, revision: TextRevision) -> TextHistory:
        if any(prior.id == revision.id for prior in self.revisions):
            raise OperationConflict("text revision ID already exists")
        if self.revisions and revision.moment_id != self.revisions[0].moment_id:
            raise ContractError("text belongs to another Moment")
        if revision.parent_revision_id is not None and not any(
            prior.id == revision.parent_revision_id for prior in self.revisions
        ):
            raise ContractError("parent text revision is missing")
        return TextHistory(self.revisions + (revision,), self.draft)

    def save_draft(self, draft: TextDraft) -> TextHistory:
        if self.revisions and draft.moment_id != self.revisions[0].moment_id:
            raise ContractError("draft belongs to another Moment")
        return TextHistory(self.revisions, draft)

    @property
    def reader_revision(self) -> TextRevision | None:
        for role in ("human_revision", "transcript_clean", "typed_source", "transcript_raw"):
            for item in reversed(self.revisions):
                if item.role == role:
                    return item
        return None
