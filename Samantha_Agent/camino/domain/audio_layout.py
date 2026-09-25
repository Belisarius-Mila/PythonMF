"""Immutable playback metadata, separate from immutable media manifests."""

from __future__ import annotations

from uuid import UUID

from .codec import exact_object
from .model import ContractError


def decode_audio_layout(value: object) -> dict:
    data = exact_object(value, {"clip_id", "moment_id", "session_id", "previous_clip_id",
                                "gap_before_ms", "missing_tail", "parts"})
    for key in ("clip_id", "moment_id", "session_id", "previous_clip_id"):
        if key == "previous_clip_id" and data[key] is None:
            continue
        try:
            if not isinstance(data[key], str) or str(UUID(data[key])) != data[key]:
                raise ValueError
        except ValueError as error:
            raise ContractError("audio layout IDs must be canonical UUIDs") from error
    previous = data["previous_clip_id"]
    if previous == data["clip_id"] or (previous is None) != (data["clip_id"] == data["session_id"]):
        raise ContractError("audio continuation must identify its original session and predecessor")
    gap = data["gap_before_ms"]
    if gap is not None and (type(gap) is not int or not 0 <= gap <= 9_007_199_254_740_991):
        raise ContractError("audio gap must be nonnegative milliseconds or unknown")
    if previous is None and gap is not None:
        raise ContractError("first audio clip cannot have a preceding pause")
    if type(data["missing_tail"]) is not bool:
        raise ContractError("audio tail flag must be explicit")
    parts = data["parts"]
    if not isinstance(parts, list) or not 1 <= len(parts) <= 4096:
        raise ContractError("audio layout must have 1 to 4096 parts")
    seen, last = set(), -1
    for part in parts:
        exact_object(part, {"asset_id", "index", "discontinuity_before"})
        try:
            if not isinstance(part["asset_id"], str) or str(UUID(part["asset_id"])) != part["asset_id"]:
                raise ValueError
        except ValueError as error:
            raise ContractError("audio part ID must be a canonical UUID") from error
        index = part["index"]
        if type(index) is not int or not last < index <= 2_147_483_647 or part["asset_id"] in seen:
            raise ContractError("audio parts must have unique assets and increasing indices")
        if type(part["discontinuity_before"]) is not bool:
            raise ContractError("audio discontinuity must be explicit")
        if index != last + 1 and not part["discontinuity_before"]:
            raise ContractError("missing audio indices must be marked as a discontinuity")
        seen.add(part["asset_id"])
        last = index
    return data


def ordered_audio_groups(assets: list[dict], layouts: list[dict]) -> tuple[list[dict], set[str]]:
    """Order by predecessor links, never UUID or wall clock; mark missing links."""
    by_asset = {asset["id"]: asset for asset in assets if asset["media_kind"] == "audio"}
    valid = [decode_audio_layout(layout) for layout in layouts]
    valid = [layout for layout in valid if all(part["asset_id"] in by_asset for part in layout["parts"])]
    groups, used = [], set()
    # Session ordering is only display ordering; no claimed timeline between sessions.
    for session_id in dict.fromkeys(layout["session_id"] for layout in valid):
        remaining = {layout["clip_id"]: layout for layout in valid if layout["session_id"] == session_id}
        clips = []
        previous = None
        while remaining:
            candidates = [layout for layout in remaining.values() if layout["previous_clip_id"] == previous]
            linked = len(candidates) == 1
            layout = candidates[0] if linked else next(
                (item for item in remaining.values() if item["previous_clip_id"] not in remaining),
                next(iter(remaining.values())),
            )
            del remaining[layout["clip_id"]]
            clips.append({**layout, "order_known": linked})
            used.update(part["asset_id"] for part in layout["parts"])
            previous = layout["clip_id"]
        groups.append({"clips": clips, "assets": by_asset})
    return groups, used
