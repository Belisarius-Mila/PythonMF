#!/usr/bin/env python3
"""Preview or create a separate-account VocabularyFR installation on macOS."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import pwd
import re
import shlex
import shutil
import stat
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, TextIO


INSTALL_CONFIRMATION = "INSTALL_VOCABULARYFR_FOR_JANA"
CSV_FILENAME = "VocabularyFR.csv"
VERBE_FILENAME = "VerbeFR.csv"
PICT_CSV_FILENAME = "FR_Pict.csv"
LAUNCHER_FILENAME = "VocabularyFR.command"
SHARED_ROOT = Path("/Users/Shared/VocabularyFR")
DEFAULT_PYTHON = Path("/usr/local/bin/python3.12")
REQUIRED_VOCABULARY_COLUMNS = {
    "FR",
    "CZ",
    "Order",
    "Sentence",
    "SentenceT",
    "L",
    "HT",
    "gender_fr",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


class VocabularyFRInstallError(RuntimeError):
    """Raised when the installation cannot be planned or applied safely."""


@dataclass(frozen=True, repr=False)
class InstallSources:
    trainer: Path
    vocabulary_csv: Path
    verbe_csv: Path
    pict_csv: Path
    male_fox: Path
    female_fox: Path
    pict_dir: Path


@dataclass(frozen=True, repr=False)
class VocabularyFRInstallPlan:
    account_name: str
    account_uid: int
    account_gid: int
    jana_home: Path
    shared_root: Path
    python_path: Path
    sources: InstallSources
    vocabulary_rows: int
    sentence_pairs: int
    picture_files: int
    mapping_missing_images: int
    source_manifest: tuple[tuple[str, str, int], ...]
    fingerprint: str

    @property
    def data_dir(self) -> Path:
        return self.jana_home / "Library" / "Application Support" / "VocabularyFR"

    @property
    def launcher_path(self) -> Path:
        return self.jana_home / "Desktop" / LAUNCHER_FILENAME

    def __repr__(self) -> str:
        return (
            "VocabularyFRInstallPlan("
            f"status='preview', fingerprint={self.fingerprint[:12]!r}, "
            "redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "preview",
            "target_account_validated": True,
            "source_csv_validated": True,
            "vocabulary_rows": self.vocabulary_rows,
            "complete_sentence_pairs": self.sentence_pairs,
            "picture_files": self.picture_files,
            "picture_mapping_missing_images": self.mapping_missing_images,
            "layout": {
                "shared_program": "/Users/Shared/VocabularyFR/app",
                "shared_pictures": "/Users/Shared/VocabularyFR/Pict",
                "user_data": "~/Library/Application Support/VocabularyFR",
                "launcher": "~/Desktop/VocabularyFR.command",
            },
            "create_only": True,
            "confirmation_required": True,
            "required_confirmation": INSTALL_CONFIRMATION,
            "plan_fingerprint": self.fingerprint,
            "writes_performed": False,
            "install_called": False,
            "private_paths_redacted": True,
        }


@dataclass(frozen=True, repr=False)
class VocabularyFRInstallResult:
    fingerprint: str
    vocabulary_rows: int
    picture_files: int
    mapping_missing_images: int

    def __repr__(self) -> str:
        return (
            "VocabularyFRInstallResult("
            f"status='installed', fingerprint={self.fingerprint[:12]!r}, "
            "redacted=True)"
        )

    def safe_document(self) -> dict[str, object]:
        return {
            "status": "installed",
            "vocabulary_rows": self.vocabulary_rows,
            "picture_files": self.picture_files,
            "picture_mapping_missing_images": self.mapping_missing_images,
            "create_only": True,
            "plan_fingerprint": self.fingerprint,
            "writes_performed": True,
            "install_called": True,
            "private_paths_redacted": True,
        }


def _regular_file(path: Path, label: str) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_symlink() or not candidate.is_file():
        raise VocabularyFRInstallError(f"Required {label} is not a regular file.")
    return candidate.resolve()


def _regular_directory(path: Path, label: str) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_symlink() or not candidate.is_dir():
        raise VocabularyFRInstallError(f"Required {label} is not a regular directory.")
    return Path(os.path.abspath(candidate))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_stem(value: str) -> str:
    folded = "".join(
        character
        for character in unicodedata.normalize("NFD", (value or "").strip().casefold())
        if unicodedata.category(character) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "", folded)


def _validate_vocabulary_csv(path: Path) -> tuple[int, int]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = set(reader.fieldnames or ())
            if not REQUIRED_VOCABULARY_COLUMNS.issubset(columns):
                raise VocabularyFRInstallError(
                    "Vocabulary CSV does not have the required schema."
                )
            rows = [row for row in reader if (row.get("FR") or row.get("CZ") or "").strip()]
    except VocabularyFRInstallError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VocabularyFRInstallError("Vocabulary CSV cannot be read safely.") from exc
    if not rows:
        raise VocabularyFRInstallError("Vocabulary CSV contains no vocabulary rows.")
    incomplete = [
        row
        for row in rows
        if not (row.get("Sentence") or "").strip()
        or not (row.get("SentenceT") or "").strip()
    ]
    if incomplete:
        raise VocabularyFRInstallError(
            "Vocabulary CSV has incomplete Sentence/SentenceT pairs."
        )
    return len(rows), len(rows)


def _validate_auxiliary_csv(path: Path, required_columns: set[str], label: str) -> None:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not required_columns.issubset(set(reader.fieldnames or ())):
                raise VocabularyFRInstallError(f"{label} does not have the required schema.")
            if next(reader, None) is None:
                raise VocabularyFRInstallError(f"{label} contains no data rows.")
    except VocabularyFRInstallError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VocabularyFRInstallError(f"{label} cannot be read safely.") from exc


def _picture_inventory(pict_dir: Path) -> tuple[tuple[Path, ...], int]:
    source_dir = _regular_directory(pict_dir, "picture source")
    mapping_path = _regular_file(source_dir / "mapping.json", "picture mapping")
    image_paths = []
    for path in sorted(source_dir.iterdir(), key=lambda item: item.name.casefold()):
        if path.name == "mapping.json":
            continue
        if path.suffix.casefold() not in IMAGE_EXTENSIONS:
            continue
        image_paths.append(_regular_file(path, "picture"))
    if not image_paths:
        raise VocabularyFRInstallError("Picture source contains no supported images.")
    try:
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VocabularyFRInstallError("Picture mapping cannot be read safely.") from exc
    if not isinstance(mapping, dict) or not mapping:
        raise VocabularyFRInstallError("Picture mapping is empty or invalid.")
    stems = {_normalized_stem(path.stem) for path in image_paths}
    missing = {
        value
        for value in mapping.values()
        if not isinstance(value, str) or _normalized_stem(value) not in stems
    }
    return (mapping_path, *image_paths), len(missing)


def _assert_safe_targets(jana_home: Path, shared_root: Path) -> tuple[Path, Path]:
    home = Path(jana_home).expanduser()
    shared = Path(shared_root).expanduser()
    if home.is_symlink() or not home.is_dir():
        raise VocabularyFRInstallError("Target account home is unavailable.")
    if shared.name != "VocabularyFR" or not shared.parent.is_dir():
        raise VocabularyFRInstallError("Shared target is outside the supported layout.")
    data_dir = home / "Library" / "Application Support" / "VocabularyFR"
    launcher = home / "Desktop" / LAUNCHER_FILENAME
    for target in (shared, data_dir, launcher):
        if target.exists() or target.is_symlink():
            raise VocabularyFRInstallError("A create-only installation target already exists.")
    return data_dir, launcher


def _manifest_entry(label: str, source: Path) -> tuple[str, str, int]:
    return label, _sha256(source), source.stat().st_size


def plan_vocabularyfr_install(
    *,
    account_name: str,
    account_uid: int,
    account_gid: int,
    jana_home: Path,
    shared_root: Path,
    python_path: Path,
    sources: InstallSources,
) -> VocabularyFRInstallPlan:
    """Build an exact, redacted and write-free installation plan."""

    if not account_name or account_uid <= 0 or account_gid < 0:
        raise VocabularyFRInstallError("A non-system target account is required.")
    python = _regular_file(python_path, "Python interpreter")
    if not os.access(python, os.X_OK):
        raise VocabularyFRInstallError("Python interpreter is not executable.")
    try:
        runtime_check = subprocess.run(
            [str(python), "-c", "import tkinter; import PIL"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise VocabularyFRInstallError("Python GUI runtime cannot be verified.") from exc
    if runtime_check.returncode != 0:
        raise VocabularyFRInstallError("Python GUI runtime is missing tkinter or Pillow.")
    checked_sources = InstallSources(
        trainer=_regular_file(sources.trainer, "trainer source"),
        vocabulary_csv=_regular_file(sources.vocabulary_csv, "vocabulary source"),
        verbe_csv=_regular_file(sources.verbe_csv, "verbs source"),
        pict_csv=_regular_file(sources.pict_csv, "picture table source"),
        male_fox=_regular_file(sources.male_fox, "male fox image"),
        female_fox=_regular_file(sources.female_fox, "female fox image"),
        pict_dir=_regular_directory(sources.pict_dir, "picture source"),
    )
    data_dir, launcher = _assert_safe_targets(jana_home, shared_root)
    vocabulary_rows, sentence_pairs = _validate_vocabulary_csv(
        checked_sources.vocabulary_csv
    )
    _validate_auxiliary_csv(checked_sources.verbe_csv, {"InfFR", "InfCZ"}, VERBE_FILENAME)
    _validate_auxiliary_csv(checked_sources.pict_csv, {"FRP", "CZP", "ENP"}, PICT_CSV_FILENAME)
    pictures, mapping_missing_images = _picture_inventory(checked_sources.pict_dir)

    labelled_sources = [
        ("shared/app/vocab_trainer_fr.py", checked_sources.trainer),
        ("shared/app/MaleFox.PNG", checked_sources.male_fox),
        ("shared/app/FemaleFox.PNG", checked_sources.female_fox),
        (f"data/{CSV_FILENAME}", checked_sources.vocabulary_csv),
        (f"data/{VERBE_FILENAME}", checked_sources.verbe_csv),
        (f"data/{PICT_CSV_FILENAME}", checked_sources.pict_csv),
    ]
    labelled_sources.extend((f"shared/Pict/{path.name}", path) for path in pictures)
    manifest = tuple(_manifest_entry(label, source) for label, source in labelled_sources)
    fingerprint_payload = {
        "account_name": account_name,
        "account_uid": account_uid,
        "account_gid": account_gid,
        "jana_home": str(Path(jana_home).resolve()),
        "shared_root": str(Path(shared_root).resolve()),
        "python_path": str(python),
        "data_dir": str(data_dir),
        "launcher": str(launcher),
        "manifest": manifest,
    }
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return VocabularyFRInstallPlan(
        account_name=account_name,
        account_uid=account_uid,
        account_gid=account_gid,
        jana_home=Path(jana_home).resolve(),
        shared_root=Path(shared_root).resolve(),
        python_path=python,
        sources=checked_sources,
        vocabulary_rows=vocabulary_rows,
        sentence_pairs=sentence_pairs,
        picture_files=len(pictures) - 1,
        mapping_missing_images=mapping_missing_images,
        source_manifest=manifest,
        fingerprint=fingerprint,
    )


def _copy_file(source: Path, target: Path, mode: int) -> None:
    if target.exists() or target.is_symlink():
        raise VocabularyFRInstallError("A create-only target changed after preview.")
    shutil.copyfile(source, target)
    target.chmod(mode)


def _chown_tree(path: Path, uid: int, gid: int) -> None:
    os.chown(path, uid, gid)
    if path.is_dir():
        for child in path.rglob("*"):
            os.chown(child, uid, gid)


def _ensure_account_directory(path: Path, home: Path, uid: int, gid: int) -> None:
    missing = []
    candidate = path
    while candidate != home and not candidate.exists():
        missing.append(candidate)
        candidate = candidate.parent
    if candidate.is_symlink() or not candidate.is_dir():
        raise VocabularyFRInstallError("A target account directory is unsafe.")
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        os.chown(directory, uid, gid)


def _verify_created_install(plan: VocabularyFRInstallPlan) -> None:
    shared_app = plan.shared_root / "app"
    shared_pict = plan.shared_root / "Pict"
    pairs = [
        (plan.sources.trainer, shared_app / "vocab_trainer_fr.py", 0o644),
        (plan.sources.male_fox, shared_app / "MaleFox.PNG", 0o644),
        (plan.sources.female_fox, shared_app / "FemaleFox.PNG", 0o644),
        (plan.sources.vocabulary_csv, plan.data_dir / CSV_FILENAME, 0o600),
        (plan.sources.verbe_csv, plan.data_dir / VERBE_FILENAME, 0o600),
        (plan.sources.pict_csv, plan.data_dir / PICT_CSV_FILENAME, 0o600),
    ]
    pairs.extend(
        (source, shared_pict / source.name, 0o644)
        for source in _picture_inventory(plan.sources.pict_dir)[0]
    )
    for source, target, mode in pairs:
        if (
            target.is_symlink()
            or not target.is_file()
            or _sha256(target) != _sha256(source)
            or stat.S_IMODE(target.stat().st_mode) != mode
        ):
            raise VocabularyFRInstallError("Created installation did not verify.")
    if (
        plan.launcher_path.is_symlink()
        or not plan.launcher_path.is_file()
        or plan.launcher_path.read_text(encoding="utf-8") != _launcher_text(plan)
        or stat.S_IMODE(plan.launcher_path.stat().st_mode) != 0o700
    ):
        raise VocabularyFRInstallError("Created launcher did not verify.")
    for directory, mode in (
        (plan.shared_root, 0o755),
        (shared_app, 0o755),
        (shared_pict, 0o755),
        (plan.data_dir, 0o700),
    ):
        if stat.S_IMODE(directory.stat().st_mode) != mode:
            raise VocabularyFRInstallError("Created directory permissions did not verify.")


def _launcher_text(plan: VocabularyFRInstallPlan) -> str:
    trainer = plan.shared_root / "app" / "vocab_trainer_fr.py"
    command = " ".join(
        shlex.quote(str(part))
        for part in (
            plan.python_path,
            trainer,
            "--data-dir",
            plan.data_dir,
            "--pict-dir",
            plan.shared_root / "Pict",
        )
    )
    return f"#!/bin/zsh\nexec {command}\n"


def apply_vocabularyfr_install(
    plan: VocabularyFRInstallPlan,
    *,
    confirmation: str,
    expected_fingerprint: str,
) -> VocabularyFRInstallResult:
    """Create the validated installation after exact confirmation."""

    if not isinstance(plan, VocabularyFRInstallPlan):
        raise VocabularyFRInstallError("A validated installation plan is required.")
    if confirmation != INSTALL_CONFIRMATION:
        raise VocabularyFRInstallError("Exact installation confirmation is required.")
    if expected_fingerprint != plan.fingerprint:
        raise VocabularyFRInstallError("Installation fingerprint does not match preview.")
    current = plan_vocabularyfr_install(
        account_name=plan.account_name,
        account_uid=plan.account_uid,
        account_gid=plan.account_gid,
        jana_home=plan.jana_home,
        shared_root=plan.shared_root,
        python_path=plan.python_path,
        sources=plan.sources,
    )
    if current.fingerprint != plan.fingerprint:
        raise VocabularyFRInstallError("Installation inputs changed after preview.")

    shared_created = False
    data_created = False
    launcher_created = False
    try:
        current.shared_root.mkdir(mode=0o755)
        shared_created = True
        shared_app = current.shared_root / "app"
        shared_pict = current.shared_root / "Pict"
        shared_app.mkdir(mode=0o755)
        shared_pict.mkdir(mode=0o755)
        for directory in (current.shared_root, shared_app, shared_pict):
            directory.chmod(0o755)

        _copy_file(current.sources.trainer, shared_app / "vocab_trainer_fr.py", 0o644)
        _copy_file(current.sources.male_fox, shared_app / "MaleFox.PNG", 0o644)
        _copy_file(current.sources.female_fox, shared_app / "FemaleFox.PNG", 0o644)
        for source in _picture_inventory(current.sources.pict_dir)[0]:
            _copy_file(source, shared_pict / source.name, 0o644)

        _ensure_account_directory(
            current.data_dir.parent,
            current.jana_home,
            current.account_uid,
            current.account_gid,
        )
        current.data_dir.mkdir(mode=0o700)
        data_created = True
        for source, filename in (
            (current.sources.vocabulary_csv, CSV_FILENAME),
            (current.sources.verbe_csv, VERBE_FILENAME),
            (current.sources.pict_csv, PICT_CSV_FILENAME),
        ):
            _copy_file(source, current.data_dir / filename, 0o600)

        _ensure_account_directory(
            current.launcher_path.parent,
            current.jana_home,
            current.account_uid,
            current.account_gid,
        )
        current.launcher_path.write_text(_launcher_text(current), encoding="utf-8")
        current.launcher_path.chmod(0o700)
        launcher_created = True
        _chown_tree(current.data_dir, current.account_uid, current.account_gid)
        _chown_tree(current.launcher_path, current.account_uid, current.account_gid)
        _verify_created_install(current)
    except (OSError, UnicodeError, shutil.Error, VocabularyFRInstallError) as exc:
        if launcher_created and current.launcher_path.is_file():
            current.launcher_path.unlink()
        if data_created and current.data_dir.is_dir():
            shutil.rmtree(current.data_dir)
        if shared_created and current.shared_root.is_dir():
            shutil.rmtree(current.shared_root)
        raise VocabularyFRInstallError("Installation failed safely and was rolled back.") from exc

    return VocabularyFRInstallResult(
        fingerprint=current.fingerprint,
        vocabulary_rows=current.vocabulary_rows,
        picture_files=current.picture_files,
        mapping_missing_images=current.mapping_missing_images,
    )


def _default_sources(source_csv: Path) -> InstallSources:
    project_dir = Path(__file__).resolve().parent
    return InstallSources(
        trainer=project_dir / "vocab_trainer_fr.py",
        vocabulary_csv=source_csv,
        verbe_csv=project_dir / VERBE_FILENAME,
        pict_csv=project_dir / PICT_CSV_FILENAME,
        male_fox=project_dir / "MaleFox.PNG",
        female_fox=project_dir / "FemaleFox.PNG",
        pict_dir=project_dir.parent / "Pict",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or create Jana's separate-account VocabularyFR setup.",
    )
    parser.add_argument("--jana-user", required=True, help="Jana's macOS short user name.")
    parser.add_argument("--source-csv", required=True, type=Path)
    parser.add_argument("--python-path", type=Path, default=DEFAULT_PYTHON)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirmation", default="")
    parser.add_argument("--expected-fingerprint", default="")
    return parser


def main(argv: Sequence[str] | None = None, *, output: TextIO | None = None) -> int:
    stream = sys.stdout if output is None else output
    arguments = build_parser().parse_args(argv)
    plan = None
    try:
        account = pwd.getpwnam(arguments.jana_user)
        if account.pw_uid < 500 or Path(account.pw_dir).parent != Path("/Users"):
            raise VocabularyFRInstallError("Target account is not a standard macOS user.")
        plan = plan_vocabularyfr_install(
            account_name=account.pw_name,
            account_uid=account.pw_uid,
            account_gid=account.pw_gid,
            jana_home=Path(account.pw_dir),
            shared_root=SHARED_ROOT,
            python_path=arguments.python_path,
            sources=_default_sources(arguments.source_csv),
        )
        if not arguments.apply:
            print(json.dumps(plan.safe_document(), sort_keys=True), file=stream)
            return 0
        result = apply_vocabularyfr_install(
            plan,
            confirmation=arguments.confirmation,
            expected_fingerprint=arguments.expected_fingerprint,
        )
    except Exception:  # noqa: BLE001 - redact private paths and OS details.
        writes_performed = bool(
            arguments.apply
            and plan is not None
            and (
                plan.shared_root.exists()
                or plan.data_dir.exists()
                or plan.launcher_path.exists()
            )
        )
        print(
            json.dumps(
                {
                    "status": "failed",
                    "writes_performed": writes_performed,
                    "install_called": bool(arguments.apply),
                    "private_paths_redacted": True,
                },
                sort_keys=True,
            ),
            file=stream,
        )
        return 1
    print(json.dumps(result.safe_document(), sort_keys=True), file=stream)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
