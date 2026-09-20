"""Strict JSON v1 encoding for the C03a reference objects.

The wire contract requires every field, including nullable ones. This prevents
a newer client field from being silently dropped by an older server.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from .model import (
    Asset, CaptureTime, ChapterChange, ContractError, HiddenChange, JourneyDay,
    LocationFix, Moment, MomentKind, Privacy, PrivacyChange, TextRevision,
    TimeSource, Trip,
)


def exact_object(value: Any, fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ContractError("JSON object has missing or unknown fields")
    return value


def wire(value: Any) -> dict[str, Any]:
    """Produce JSON-compatible, deterministic object fields from a dataclass."""
    return json.loads(json.dumps(asdict(value), sort_keys=True, separators=(",", ":")))


def decode_trip(value: Any) -> Trip:
    data = exact_object(value, {"id", "name", "language", "active", "viewer_enabled", "start_date"})
    return Trip(**data)


def decode_day(value: Any) -> JourneyDay:
    return JourneyDay(**exact_object(value, {"id", "trip_id", "local_date"}))


def decode_capture(value: Any) -> CaptureTime:
    data = exact_object(value, {
        "utc_ms", "local_wall", "utc_offset_minutes", "time_zone_id", "source", "uncertain",
    })
    if not isinstance(data["uncertain"], bool):
        raise ContractError("capture uncertainty must be boolean")
    try:
        source = TimeSource(data["source"])
    except (TypeError, ValueError) as error:
        raise ContractError("unknown capture time source") from error
    return CaptureTime(
        data["utc_ms"], data["local_wall"], data["utc_offset_minutes"],
        data["time_zone_id"], source, data["uncertain"],
    )


def decode_location(value: Any) -> LocationFix | None:
    if value is None:
        return None
    data = exact_object(value, {
        "latitude", "longitude", "measured_at_utc_ms", "horizontal_accuracy_m",
    })
    if any(isinstance(data[key], bool) or not isinstance(data[key], (int, float))
           for key in ("latitude", "longitude", "horizontal_accuracy_m")):
        raise ContractError("location values must be numeric")
    return LocationFix(**data)


def decode_moment(value: Any) -> Moment:
    data = exact_object(value, {
        "id", "trip_id", "day_id", "chapter_date", "kind", "captured", "privacy",
        "revision", "hidden", "important", "related_moment_id", "location",
    })
    try:
        kind = MomentKind(data["kind"])
    except (TypeError, ValueError) as error:
        raise ContractError("unknown Moment kind") from error
    return Moment(
        id=data["id"], trip_id=data["trip_id"], day_id=data["day_id"],
        chapter_date=data["chapter_date"], kind=kind,
        captured=decode_capture(data["captured"]), privacy=data["privacy"],
        revision=data["revision"], hidden=data["hidden"], important=data["important"],
        related_moment_id=data["related_moment_id"],
        location=decode_location(data["location"]),
    )


def decode_asset(value: Any) -> Asset:
    return Asset(**exact_object(value, {
        "id", "moment_id", "media_kind", "origin", "byte_count", "sha256", "duration_ms",
    }))


def decode_text(value: Any) -> TextRevision:
    data = exact_object(value, {
        "id", "moment_id", "role", "content", "source_ids", "parent_revision_id",
        "created_at_utc_ms",
    })
    if not isinstance(data["source_ids"], list):
        raise ContractError("source IDs must be a JSON array")
    return TextRevision(
        data["id"], data["moment_id"], data["role"], data["content"],
        tuple(data["source_ids"]), data["parent_revision_id"], data["created_at_utc_ms"],
    )


def encode_change(value: PrivacyChange | HiddenChange | ChapterChange) -> dict[str, Any]:
    result = wire(value)
    result["type"] = (
        "privacy" if isinstance(value, PrivacyChange)
        else "hidden" if isinstance(value, HiddenChange) else "chapter"
    )
    return result


def decode_change(value: Any) -> PrivacyChange | HiddenChange | ChapterChange:
    if not isinstance(value, dict):
        raise ContractError("metadata change must be an object")
    kind = value.get("type")
    common = {"type", "id", "moment_id", "device_sequence", "expected_revision"}
    if kind == "privacy":
        data = exact_object(value, common | {"new_privacy", "user_action"})
        try:
            privacy = Privacy(data["new_privacy"])
        except (TypeError, ValueError) as error:
            raise ContractError("unknown privacy change") from error
        return PrivacyChange(
            data["id"], data["moment_id"], data["device_sequence"],
            data["expected_revision"], privacy, data["user_action"],
        )
    if kind == "hidden":
        data = exact_object(value, common | {"hidden"})
        return HiddenChange(
            data["id"], data["moment_id"], data["device_sequence"],
            data["expected_revision"], data["hidden"],
        )
    if kind == "chapter":
        data = exact_object(value, common | {"day"})
        return ChapterChange(
            data["id"], data["moment_id"], data["device_sequence"],
            data["expected_revision"], decode_day(data["day"]),
        )
    raise ContractError("unknown metadata change type")
