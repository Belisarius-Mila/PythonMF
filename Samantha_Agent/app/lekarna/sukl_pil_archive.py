from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .sukl_dlp import DEFAULT_SUKL_CACHE_DIR


@dataclass(frozen=True)
class SuklPilDocument:
    pil_name: str
    archive_path: Path
    member_name: str
    text: str
    extraction_method: str


def find_latest_pil_archive(cache_dir: Path = DEFAULT_SUKL_CACHE_DIR) -> Path | None:
    cache_dir = cache_dir.expanduser()
    if not cache_dir.exists():
        return None
    candidates = [
        path
        for path in cache_dir.glob("*.zip")
        if "pil" in path.name.casefold() and not path.name.casefold().startswith("dlp")
    ]
    candidates.sort(key=lambda path: (path.stat().st_mtime, path.name), reverse=True)
    return candidates[0] if candidates else None


def resolve_sukl_pil_document(
    pil_name: str,
    *,
    pil_archive_path: Path | None = None,
    cache_dir: Path = DEFAULT_SUKL_CACHE_DIR,
) -> SuklPilDocument | None:
    clean_name = Path(str(pil_name or "").strip()).name
    if not clean_name:
        return None
    archive_path = pil_archive_path or find_latest_pil_archive(cache_dir)
    if not archive_path or not archive_path.exists():
        return None
    member_name = _find_archive_member(archive_path, clean_name)
    if not member_name:
        return None
    with zipfile.ZipFile(archive_path) as archive:
        payload = archive.read(member_name)
    text, method = _extract_document_text(payload, member_name)
    if not text.strip():
        return None
    return SuklPilDocument(
        pil_name=clean_name,
        archive_path=archive_path,
        member_name=member_name,
        text=_normalize_text(text),
        extraction_method=method,
    )


def build_pil_short_from_text(product_name: str, text: str, *, limit: int = 700) -> str:
    normalized = _normalize_text(text)
    if not normalized:
        return ""
    product = " ".join(str(product_name or "").strip().split())
    section_one = _extract_section(normalized, "1.", "2.")
    section_two = _extract_section(normalized, "2.", "3.")
    use_sentences = _first_sentences(section_one, max_sentences=2)
    safety_sentences = _safety_sentences(section_two, max_sentences=2)
    pieces: list[str] = []
    if product:
        pieces.append(f"{product}:")
    if use_sentences:
        pieces.append(use_sentences)
    if safety_sentences:
        pieces.append(safety_sentences)
    pieces.append("Řiďte se aktuální příbalovou informací; text není osobní dávkovací doporučení.")
    return _truncate(" ".join(piece for piece in pieces if piece), limit)


def _find_archive_member(archive_path: Path, pil_name: str) -> str:
    target = Path(pil_name).name.casefold()
    with zipfile.ZipFile(archive_path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
    for name in names:
        if Path(name).name.casefold() == target:
            return name
    target_stem = Path(target).stem
    for name in names:
        if Path(name).stem.casefold() == target_stem:
            return name
    return ""


def _extract_document_text(payload: bytes, member_name: str) -> tuple[str, str]:
    suffix = Path(member_name).suffix.casefold()
    if suffix in {".txt", ".text"}:
        return _decode_text(payload), "text"
    if suffix == ".pdf":
        return _extract_pdf_text(payload)
    if suffix in {".doc", ".docx", ".rtf"}:
        return _extract_with_textutil(payload, suffix)
    return "", "unsupported"


def _extract_pdf_text(payload: bytes) -> tuple[str, str]:
    with tempfile.TemporaryDirectory(prefix="samantha_sukl_pil_") as temp_dir:
        pdf_path = Path(temp_dir) / "pil.pdf"
        pdf_path.write_bytes(payload)
        pdftotext = _resolve_pdftotext_binary()
        if pdftotext:
            try:
                completed = subprocess.run(
                    [pdftotext, "-layout", str(pdf_path), "-"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
            except (OSError, subprocess.SubprocessError):
                completed = None
            if completed and completed.returncode == 0 and completed.stdout.strip():
                return completed.stdout, "pdftotext"
        try:
            from pdfminer.high_level import extract_text  # type: ignore

            text = extract_text(str(pdf_path)) or ""
        except Exception:
            return "", "pdf-text-failed"
        return text, "pdfminer" if text.strip() else "pdf-empty"


def _extract_with_textutil(payload: bytes, suffix: str) -> tuple[str, str]:
    textutil = shutil.which("textutil") or "/usr/bin/textutil"
    if not Path(textutil).is_file():
        return "", "textutil-unavailable"
    with tempfile.TemporaryDirectory(prefix="samantha_sukl_pil_") as temp_dir:
        source_path = Path(temp_dir) / f"pil{suffix}"
        source_path.write_bytes(payload)
        try:
            completed = subprocess.run(
                [textutil, "-convert", "txt", "-stdout", str(source_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (OSError, subprocess.SubprocessError):
            return "", "textutil-failed"
    if completed.returncode == 0 and completed.stdout.strip():
        return completed.stdout, "textutil"
    return "", "textutil-empty"


def _resolve_pdftotext_binary() -> str:
    found = shutil.which("pdftotext")
    if found:
        return found
    for candidate in ("/usr/local/bin/pdftotext", "/opt/homebrew/bin/pdftotext", "/usr/bin/pdftotext"):
        if Path(candidate).is_file():
            return candidate
    return ""


def _decode_text(payload: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1250", "utf-8", "latin2"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="replace")


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").replace("\x00", " ")).strip()


def _extract_section(text: str, start_marker: str, end_marker: str) -> str:
    start = _find_section_marker(text, start_marker)
    if start < 0:
        return ""
    end = _find_section_marker(text, end_marker, start + len(start_marker))
    if end < 0:
        end = len(text)
    return text[start:end].strip()


def _find_section_marker(text: str, marker: str, start: int = 0) -> int:
    pattern = re.compile(rf"(?:^|\s){re.escape(marker)}\s+", re.IGNORECASE)
    match = pattern.search(text, start)
    return match.start() if match else -1


def _first_sentences(text: str, *, max_sentences: int) -> str:
    cleaned = _strip_section_heading(text)
    return " ".join(_sentence_split(cleaned)[:max_sentences])


def _safety_sentences(text: str, *, max_sentences: int) -> str:
    cleaned = _strip_section_heading(text)
    sentences = _sentence_split(cleaned)
    priority_terms = (
        "neužívejte",
        "neuzivejte",
        "upozornění",
        "upozorneni",
        "poraďte",
        "poradte",
        "lékař",
        "lekar",
        "alerg",
    )
    selected = [
        sentence
        for sentence in sentences
        if any(term in sentence.casefold() for term in priority_terms)
    ]
    return " ".join((selected or sentences)[:max_sentences])


def _strip_section_heading(text: str) -> str:
    return re.sub(r"^\s*\d+\.\s+[^.?!]{0,180}", "", text).strip()


def _sentence_split(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", _normalize_text(text))
    return [part.strip() for part in parts if len(part.strip()) >= 20]


def _truncate(text: str, limit: int) -> str:
    cleaned = _normalize_text(text)
    if len(cleaned) <= limit:
        return cleaned
    shortened = cleaned[: limit - 3].rstrip()
    last_sentence = max(shortened.rfind("."), shortened.rfind("!"), shortened.rfind("?"))
    if last_sentence >= 240:
        shortened = shortened[: last_sentence + 1]
    return shortened.rstrip() + "..."
