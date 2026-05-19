"""Simple JSON persistence for MultiLO progress."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path


PROGRESS_FILE = Path(__file__).resolve().parent / "progress.json"


def load_progress(path: Path = PROGRESS_FILE) -> dict:
    if not path.exists():
        return {"users": {}}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return {"users": {}}
    if not isinstance(data, dict):
        return {"users": {}}
    data.setdefault("users", {})
    return data


def save_progress(data: dict, path: Path = PROGRESS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def _apply_event(data: dict, *, user_id: str, item_id: int, mode: str, okruh: str, lang: str, correct: bool) -> None:
    """Mutate *data* in-place — no disk I/O."""
    users = data.setdefault("users", {})
    user_block = users.setdefault(user_id, {})
    items = user_block.setdefault("items", {})
    item_block = items.setdefault(str(item_id), {})
    mode_block = item_block.setdefault(mode, {})

    mode_block["okruh"] = okruh
    mode_block["last_lang"] = lang
    mode_block["seen_count"] = int(mode_block.get("seen_count", 0)) + 1
    mode_block["correct_count"] = int(mode_block.get("correct_count", 0)) + (1 if correct else 0)
    mode_block["wrong_count"] = int(mode_block.get("wrong_count", 0)) + (0 if correct else 1)
    mode_block["last_result"] = "correct" if correct else "wrong"
    mode_block["last_seen_at"] = datetime.now(timezone.utc).isoformat()


def _apply_seen(data: dict, *, user_id: str, item_id: int, mode: str, okruh: str, lang: str) -> None:
    """Mutate *data* in-place — no disk I/O."""
    users = data.setdefault("users", {})
    user_block = users.setdefault(user_id, {})
    items = user_block.setdefault("items", {})
    item_block = items.setdefault(str(item_id), {})
    mode_block = item_block.setdefault(mode, {})

    mode_block["okruh"] = okruh
    mode_block["last_lang"] = lang
    mode_block["seen_count"] = int(mode_block.get("seen_count", 0)) + 1
    mode_block.setdefault("correct_count", 0)
    mode_block.setdefault("wrong_count", 0)
    mode_block["last_result"] = "seen"
    mode_block["last_seen_at"] = datetime.now(timezone.utc).isoformat()


def update_progress_event_in_memory(
    data: dict,
    *,
    user_id: str,
    item_id: int,
    mode: str,
    okruh: str,
    lang: str,
    correct: bool,
) -> None:
    """Record a correct/wrong event into an already-loaded *data* dict (no I/O)."""
    _apply_event(data, user_id=user_id, item_id=item_id, mode=mode, okruh=okruh, lang=lang, correct=correct)


def update_progress_seen_in_memory(
    data: dict,
    *,
    user_id: str,
    item_id: int,
    mode: str,
    okruh: str,
    lang: str,
) -> None:
    """Record a seen event into an already-loaded *data* dict (no I/O)."""
    _apply_seen(data, user_id=user_id, item_id=item_id, mode=mode, okruh=okruh, lang=lang)


def reset_progress_for_okruh_in_memory(
    data: dict,
    *,
    user_id: str,
    okruh: str,
) -> None:
    """Remove all progress for *okruh* from an already-loaded *data* dict (no I/O)."""
    user_block = data.get("users", {}).get(user_id)
    if not isinstance(user_block, dict):
        return
    items = user_block.get("items")
    if not isinstance(items, dict):
        return
    empty: list[str] = []
    for item_id_str, modes in list(items.items()):
        if not isinstance(modes, dict):
            continue
        for mode_name in [k for k, v in modes.items() if isinstance(v, dict) and v.get("okruh") == okruh]:
            modes.pop(mode_name, None)
        if not modes:
            empty.append(item_id_str)
    for k in empty:
        items.pop(k, None)


def record_progress_event(
    *,
    user_id: str,
    item_id: int,
    mode: str,
    okruh: str,
    lang: str,
    correct: bool,
    path: Path = PROGRESS_FILE,
) -> None:
    data = load_progress(path)
    _apply_event(data, user_id=user_id, item_id=item_id, mode=mode, okruh=okruh, lang=lang, correct=correct)
    save_progress(data, path)


def record_progress_seen(
    *,
    user_id: str,
    item_id: int,
    mode: str,
    okruh: str,
    lang: str,
    path: Path = PROGRESS_FILE,
) -> None:
    data = load_progress(path)
    _apply_seen(data, user_id=user_id, item_id=item_id, mode=mode, okruh=okruh, lang=lang)
    save_progress(data, path)


def summarize_progress_by_okruh(
    *,
    user_id: str,
    item_okruh_map: dict[int, str],
    data: dict | None = None,
    path: Path = PROGRESS_FILE,
) -> dict[str, dict[str, int]]:
    if data is None:
        data = load_progress(path)

    summary: dict[str, dict[str, int]] = {}
    for okruh in set(item_okruh_map.values()):
        summary[okruh] = {
            "total_items": 0,
            "seen_items": 0,
            "correct_count": 0,
            "wrong_count": 0,
        }

    for item_id, okruh in item_okruh_map.items():
        block = summary.setdefault(
            okruh,
            {"total_items": 0, "seen_items": 0, "correct_count": 0, "wrong_count": 0},
        )
        block["total_items"] += 1

    items = (
        data.get("users", {})
        .get(user_id, {})
        .get("items", {})
    )

    for item_id_str, modes in items.items():
        try:
            item_id = int(item_id_str)
        except (TypeError, ValueError):
            continue
        okruh = item_okruh_map.get(item_id)
        if okruh is None:
            continue

        block = summary.setdefault(
            okruh,
            {"total_items": 0, "seen_items": 0, "correct_count": 0, "wrong_count": 0},
        )
        seen_for_item = False
        for mode_block in modes.values():
            if not isinstance(mode_block, dict):
                continue
            if int(mode_block.get("seen_count", 0)) > 0:
                seen_for_item = True
            block["correct_count"] += int(mode_block.get("correct_count", 0))
            block["wrong_count"] += int(mode_block.get("wrong_count", 0))
        if seen_for_item:
            block["seen_items"] += 1

    return summary


def rank_item_ids_by_weakness(
    *,
    user_id: str,
    item_ids: list[int],
    data: dict | None = None,
    path: Path = PROGRESS_FILE,
) -> list[int]:
    if data is None:
        data = load_progress(path)

    items = data.get("users", {}).get(user_id, {}).get("items", {})

    def weakness_key(item_id: int) -> tuple[int, float, int, int]:
        item_block = items.get(str(item_id), {})
        seen_count = 0
        correct_count = 0
        wrong_count = 0
        for mode_block in item_block.values():
            if not isinstance(mode_block, dict):
                continue
            seen_count += int(mode_block.get("seen_count", 0))
            correct_count += int(mode_block.get("correct_count", 0))
            wrong_count += int(mode_block.get("wrong_count", 0))

        attempts = correct_count + wrong_count
        success_ratio = (correct_count / attempts) if attempts else -1.0
        has_wrong = 1 if wrong_count > 0 else 0
        unseen = 1 if seen_count == 0 else 0

        return (
            -has_wrong,
            success_ratio,
            unseen,
            -seen_count,
        )

    return sorted(item_ids, key=weakness_key)


def reset_progress_for_okruh(
    *,
    user_id: str,
    okruh: str,
    path: Path = PROGRESS_FILE,
) -> None:
    data = load_progress(path)
    users = data.get("users", {})
    user_block = users.get(user_id)
    if not isinstance(user_block, dict):
        return

    items = user_block.get("items")
    if not isinstance(items, dict):
        return

    empty_item_ids: list[str] = []
    for item_id_str, modes in list(items.items()):
        if not isinstance(modes, dict):
            continue
        mode_names_to_delete: list[str] = []
        for mode_name, mode_block in modes.items():
            if not isinstance(mode_block, dict):
                continue
            if mode_block.get("okruh") == okruh:
                mode_names_to_delete.append(mode_name)
        for mode_name in mode_names_to_delete:
            modes.pop(mode_name, None)
        if not modes:
            empty_item_ids.append(item_id_str)

    for item_id_str in empty_item_ids:
        items.pop(item_id_str, None)

    save_progress(data, path)
