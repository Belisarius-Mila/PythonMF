"""Step 1: Data loading and validation for MultiLO.

Usage:
    from pathlib import Path
    from data_layer import load_data, summarize

    bundle = load_data(Path("MultiLO"))
    print(summarize(bundle))
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import unicodedata


VOCAB_FILE = "vocab_master.csv"
USERS_FILE = "users.csv"
PREFS_FILE = "user_item_prefs.csv"


@dataclass(frozen=True)
class VocabItem:
    item_id: int
    okruh: str
    cz: str
    fr: str
    it: str
    es: str
    en: str
    latin: str


@dataclass(frozen=True)
class UserProfile:
    user_id: str
    display_name: str
    role: str
    active: bool
    ui_language: str
    learn_language: str
    daily_goal: int


@dataclass(frozen=True)
class UserItemPreference:
    user_id: str
    item_id: int
    enabled: bool
    priority: int
    assoc_color_hex: str
    assoc_note: str


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class DataBundle:
    vocab: tuple[VocabItem, ...]
    users: tuple[UserProfile, ...]
    prefs: tuple[UserItemPreference, ...]
    validation: ValidationResult


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def _normalize_for_duplicate_check(value: str) -> str:
    txt = _normalize_text(value).casefold()
    txt = "".join(
        ch for ch in unicodedata.normalize("NFD", txt) if unicodedata.category(ch) != "Mn"
    )
    return txt


def _read_csv(
    path: Path,
    required_cols: list[str],
    optional_cols: list[str] | None = None,
) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        missing = [c for c in required_cols if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"Missing columns in {path.name}: {', '.join(missing)}")
        rows = [{k: _normalize_text(v) for k, v in row.items()} for row in reader]
        for row in rows:
            for col in optional_cols or []:
                row.setdefault(col, "")
        return rows


def load_data(base_dir: str | Path) -> DataBundle:
    base = Path(base_dir)
    vocab_rows = _read_csv(
        base / VOCAB_FILE,
        ["item_id", "OKRUH", "CZ", "FR", "IT", "ES", "EN"],
        optional_cols=["LATIN"],
    )
    user_rows = _read_csv(
        base / USERS_FILE,
        ["user_id", "display_name", "role", "active", "ui_language", "learn_language", "daily_goal"],
    )
    pref_rows = _read_csv(
        base / PREFS_FILE,
        ["user_id", "item_id", "enabled", "priority", "assoc_color_hex", "assoc_note"],
    )

    errors: list[str] = []
    warnings: list[str] = []

    vocab: list[VocabItem] = []
    item_ids: set[int] = set()
    cz_keys: set[str] = set()
    okruhy: set[str] = set()

    for i, row in enumerate(vocab_rows, start=2):
        try:
            item_id = int(row["item_id"])
        except ValueError:
            errors.append(f"{VOCAB_FILE}:{i} invalid item_id '{row['item_id']}'")
            continue
        if item_id <= 0:
            errors.append(f"{VOCAB_FILE}:{i} item_id must be > 0")
        if item_id in item_ids:
            errors.append(f"{VOCAB_FILE}:{i} duplicate item_id {item_id}")
        item_ids.add(item_id)

        okruh = row["OKRUH"]
        if not okruh:
            errors.append(f"{VOCAB_FILE}:{i} empty OKRUH")
        okruhy.add(okruh)

        required_text = ["CZ", "FR", "IT", "ES", "EN"]
        for col in required_text:
            if not row[col]:
                errors.append(f"{VOCAB_FILE}:{i} empty {col}")

        cz_key = _normalize_for_duplicate_check(row["CZ"])
        if cz_key in cz_keys:
            warnings.append(f"{VOCAB_FILE}:{i} possibly duplicate CZ '{row['CZ']}'")
        cz_keys.add(cz_key)

        vocab.append(
            VocabItem(
                item_id=item_id,
                okruh=okruh,
                cz=row["CZ"],
                fr=row["FR"],
                it=row["IT"],
                es=row["ES"],
                en=row["EN"],
                latin=row.get("LATIN", ""),
            )
        )

    users: list[UserProfile] = []
    user_ids: set[str] = set()
    for i, row in enumerate(user_rows, start=2):
        user_id = row["user_id"]
        if not user_id:
            errors.append(f"{USERS_FILE}:{i} empty user_id")
            continue
        if user_id in user_ids:
            errors.append(f"{USERS_FILE}:{i} duplicate user_id '{user_id}'")
        user_ids.add(user_id)

        try:
            daily_goal = int(row["daily_goal"])
        except ValueError:
            errors.append(f"{USERS_FILE}:{i} invalid daily_goal '{row['daily_goal']}'")
            daily_goal = 0

        active = row["active"] in {"1", "true", "True", "yes", "YES"}
        users.append(
            UserProfile(
                user_id=user_id,
                display_name=row["display_name"],
                role=row["role"],
                active=active,
                ui_language=row["ui_language"],
                learn_language=row["learn_language"],
                daily_goal=daily_goal,
            )
        )

    prefs: list[UserItemPreference] = []
    seen_pref_pairs: set[tuple[str, int]] = set()
    for i, row in enumerate(pref_rows, start=2):
        user_id = row["user_id"]
        if user_id not in user_ids:
            errors.append(f"{PREFS_FILE}:{i} unknown user_id '{user_id}'")
            continue

        try:
            item_id = int(row["item_id"])
        except ValueError:
            errors.append(f"{PREFS_FILE}:{i} invalid item_id '{row['item_id']}'")
            continue
        if item_id not in item_ids:
            errors.append(f"{PREFS_FILE}:{i} unknown item_id '{item_id}'")

        try:
            priority = int(row["priority"])
        except ValueError:
            errors.append(f"{PREFS_FILE}:{i} invalid priority '{row['priority']}'")
            priority = 1

        enabled = row["enabled"] in {"1", "true", "True", "yes", "YES"}
        pair = (user_id, item_id)
        if pair in seen_pref_pairs:
            warnings.append(f"{PREFS_FILE}:{i} duplicate preference pair {pair}")
        seen_pref_pairs.add(pair)

        prefs.append(
            UserItemPreference(
                user_id=user_id,
                item_id=item_id,
                enabled=enabled,
                priority=priority,
                assoc_color_hex=row["assoc_color_hex"],
                assoc_note=row["assoc_note"],
            )
        )

    expected_users = {"me", "wife", "guest"}
    missing = sorted(expected_users - user_ids)
    if missing:
        warnings.append(f"Missing default users: {', '.join(missing)}")

    if len(okruhy) < 5:
        warnings.append("Unexpectedly low number of OKRUH categories")

    validation = ValidationResult(errors=tuple(errors), warnings=tuple(warnings))
    return DataBundle(
        vocab=tuple(vocab),
        users=tuple(users),
        prefs=tuple(prefs),
        validation=validation,
    )


def summarize(bundle: DataBundle) -> str:
    okruh_counts: dict[str, int] = {}
    for item in bundle.vocab:
        okruh_counts[item.okruh] = okruh_counts.get(item.okruh, 0) + 1

    lines = [
        f"Vocab items: {len(bundle.vocab)}",
        f"Users: {len(bundle.users)}",
        f"Preferences: {len(bundle.prefs)}",
        f"OKRUH categories: {len(okruh_counts)}",
    ]
    for key in sorted(okruh_counts):
        lines.append(f"  - {key}: {okruh_counts[key]}")

    lines.append(f"Warnings: {len(bundle.validation.warnings)}")
    lines.append(f"Errors: {len(bundle.validation.errors)}")
    return "\n".join(lines)
