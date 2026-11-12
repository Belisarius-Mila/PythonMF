"""Bounded public plan/comment projection for the scoped HA-04 observer.

The caller must validate the wire event and bind its exact thread/turn/
generation before persisting the projection. This module grants no ownership or delivery evidence.
No raw event, reasoning, command arguments or tool output is retained.
"""
from __future__ import annotations

from copy import deepcopy

MAX_STEPS = 32
MAX_STEP_TEXT = 1000
MAX_COMMENTS = 16
MAX_COMMENT_TEXT = 2000
SOURCE = "validated_public_progress"


def _text(value, limit):
    if not isinstance(value, str) or not value.strip():
        return None
    return value[:limit]


def _plan(value):
    if not isinstance(value, list) or len(value) > 128:
        return None
    result, truncated = [], len(value) > MAX_STEPS
    for step in value[:MAX_STEPS]:
        if (not isinstance(step, dict) or step.get("status") not in ("pending", "inProgress", "completed")
                or _text(step.get("step"), MAX_STEP_TEXT) is None):
            return None
        truncated |= len(step["step"]) > MAX_STEP_TEXT
        result.append({"step": step["step"][:MAX_STEP_TEXT], "status": step["status"]})
    return result, truncated


def public_event(method: str, params: dict) -> dict | None:
    """Only public plan steps and completed commentary-phase messages qualify."""
    if not isinstance(params, dict):
        return None
    if method == "turn/plan/updated":
        parsed = _plan(params.get("plan"))
        if parsed is not None:
            return {"kind": "plan", "plan": parsed[0], "truncated": parsed[1]}
    if method == "item/completed":
        item = params.get("item")
        if (isinstance(item, dict) and item.get("type") == "agentMessage"
                and item.get("phase") == "commentary"
                and isinstance(item.get("id"), str) and 0 < len(item["id"]) <= 256):
            text = _text(item.get("text"), MAX_COMMENT_TEXT)
            if text is not None:
                return {"kind": "comment", "comment": {"id": item["id"], "text": text},
                        "truncated": len(item["text"]) > MAX_COMMENT_TEXT}
    return None


def public_projection(value: dict | None) -> dict | None:
    """Rebuild a public value by whitelist; never expose extra stored fields."""
    if not isinstance(value, dict) or type(value.get("schema_version")) is not int or value.get("schema_version") != 1 or value.get("source") != SOURCE:
        return None
    plan = _plan(value.get("plan"))
    comments = value.get("comments")
    if plan is None or not isinstance(comments, list) or len(comments) > MAX_COMMENTS:
        return None
    safe_comments = []
    for item in comments:
        if (not isinstance(item, dict) or not isinstance(item.get("id"), str) or not 0 < len(item["id"]) <= 256
                or _text(item.get("text"), MAX_COMMENT_TEXT) is None):
            return None
        safe_comments.append({"id": item["id"], "text": item["text"][:MAX_COMMENT_TEXT]})
    return {"schema_version": 1, "source": SOURCE, "plan": plan[0], "comments": safe_comments,
            "plan_truncated": value.get("plan_truncated") is True or plan[1],
            "comments_truncated": value.get("comments_truncated") is True}


def merge_public_progress(previous: dict | None, update: dict | None) -> dict:
    value = public_projection(previous) or {"schema_version": 1, "source": SOURCE,
        "plan": [], "comments": [], "plan_truncated": False, "comments_truncated": False}
    if not isinstance(update, dict):
        return value
    if update.get("kind") == "plan":
        plan = _plan(update.get("plan"))
        if plan is not None:
            value["plan"] = plan[0]
            value["plan_truncated"] = plan[1] or update.get("truncated") is True
    if update.get("kind") == "comment":
        item = update.get("comment")
        if (isinstance(item, dict) and isinstance(item.get("id"), str) and 0 < len(item["id"]) <= 256
                and _text(item.get("text"), MAX_COMMENT_TEXT) is not None):
            comments = [old for old in value["comments"] if old["id"] != item["id"]]
            comments.append({"id": item["id"], "text": item["text"][:MAX_COMMENT_TEXT]})
            value["comments_truncated"] |= len(comments) > MAX_COMMENTS or update.get("truncated") is True
            value["comments"] = comments[-MAX_COMMENTS:]
    return deepcopy(value)
