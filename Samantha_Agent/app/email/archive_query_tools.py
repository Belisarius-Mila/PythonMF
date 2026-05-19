from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from agents import function_tool

from .archive_service import DEFAULT_EMAIL_ARCHIVE_DIR
from .redaction import EMAIL_PATTERN, redact_email_addresses


URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
SAFE_ARCHIVE_ID_PATTERN = re.compile(r"[A-Za-z0-9_.-]+")
CONFIRMATION_WORDS = ("potvrzuji", "souhlasim", "souhlasím", "ano")
LINK_WORDS = ("url", "odkaz", "odkazy", "linky", "links")


@function_tool
def list_email_archives() -> str:
    """List local EmailArchiveVault archives without reading email provider."""
    return list_email_archives_text()


@function_tool
def show_email_archive_summary(archive_id_or_uid: str) -> str:
    """Show safe local EmailArchiveVault metadata for one archive."""
    return show_email_archive_summary_text(archive_id_or_uid=archive_id_or_uid)


@function_tool
def show_email_archive_links(
    archive_id_or_uid: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Show full links from a local archive after explicit confirmation."""
    return show_email_archive_links_text(
        archive_id_or_uid=archive_id_or_uid,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


def list_email_archives_text(directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR) -> str:
    archives = _load_archive_entries(directory)
    if not archives:
        return "V EmailArchiveVault nejsou ulozene zadne archivy."

    lines = ["EmailArchiveVault archivy:"]
    for entry in archives:
        metadata = entry["metadata"]
        lines.extend(
            [
                f"- Archive ID: {_safe_text(metadata.get('archive_id'))}",
                f"  UID: {_safe_text(metadata.get('uid'))}",
                f"  Datum: {_safe_text(metadata.get('date'))}",
                f"  Odesilatel: {_safe_text(metadata.get('from'))}",
                f"  Predmet: {_safe_text(metadata.get('subject'))}",
                f"  Odkazy: {_safe_text(metadata.get('links_count', 0))}",
                f"  Prilohy: {_safe_text(metadata.get('attachments_count', 0))}",
            ]
        )
    return _sanitize_safe_output("\n".join(lines))


def show_email_archive_summary_text(
    archive_id_or_uid: str,
    directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
) -> str:
    resolved = _resolve_archive(archive_id_or_uid, directory)
    if isinstance(resolved, str):
        return resolved

    archive_dir, metadata = resolved
    links = _read_links(archive_dir)
    attachments = _read_attachments(archive_dir)
    domain_counts = Counter(_safe_domain(link.get("domain")) for link in links)
    domain_counts.pop("", None)

    lines = [
        f"Archive ID: {_safe_text(metadata.get('archive_id'))}",
        f"UID: {_safe_text(metadata.get('uid'))}",
        f"Datum: {_safe_text(metadata.get('date'))}",
        f"Odesilatel: {_safe_text(metadata.get('from'))}",
        f"Predmet: {_safe_text(metadata.get('subject'))}",
        f"Archivovano: {_safe_text(metadata.get('archived_at'))}",
        f"Text ulozen: {_yes_no(metadata.get('body_text_saved'))}",
        f"HTML ulozeno: {_yes_no(metadata.get('body_html_saved'))}",
        f"Original EML ulozen: {_yes_no(metadata.get('original_eml_saved'))}",
        "",
        "Soubory:",
    ]
    files = _relative_files(archive_dir)
    lines.extend(f"- {_safe_text(path)}" for path in files) if files else lines.append("- Nenalezeny")

    lines.extend(["", "Odkazy domeny:"])
    if domain_counts:
        for domain, count in sorted(domain_counts.items()):
            lines.append(f"- {_safe_text(domain)}: {count}")
        lines.append("Plne URL zobrazi jen samostatne potvrzeny show_email_archive_links.")
    else:
        lines.append("- Nenalezeny")

    lines.extend(["", "Prilohy metadata:"])
    if attachments:
        for attachment in attachments:
            size = _safe_text(attachment.get("size_bytes")) or "neznamy"
            lines.append(
                "- "
                f"{_safe_text(attachment.get('filename'))} | "
                f"{_safe_text(attachment.get('content_type'))} | "
                f"{size} B | saved={_yes_no(attachment.get('saved'))}"
            )
    else:
        lines.append("- Nenalezeny")

    lines.append("")
    lines.append(
        "Bezpecnost: tento souhrn necte iCloud, neukazuje telo e-mailu, plne URL "
        "ani neredigovane e-mailove adresy."
    )
    return _sanitize_safe_output("\n".join(lines))


def show_email_archive_links_text(
    archive_id_or_uid: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    directory: Path = DEFAULT_EMAIL_ARCHIVE_DIR,
) -> str:
    resolved = _resolve_archive(archive_id_or_uid, directory)
    if isinstance(resolved, str):
        return resolved

    archive_dir, metadata = resolved
    if not user_confirmed or not has_explicit_archive_link_confirmation(
        archive_id=str(metadata.get("archive_id", "")),
        uid=str(metadata.get("uid", "")),
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji samostatne potvrzeni od Mily v aktualni zprave. "
            "Potvrzeni musi obsahovat archive id nebo UID a jasny souhlas se "
            "zobrazenim plnych odkazu z archivu. Bez toho links.json nevypisuji."
        )

    links = _read_links(archive_dir)
    lines = [
        f"Plne odkazy z archivu: {_safe_text(metadata.get('archive_id'))}",
    ]
    if links:
        for index, link in enumerate(links, start=1):
            lines.append(f"{index}. {link.get('url', '')}")
    else:
        lines.append("- Nenalezeny")
    lines.append("")
    lines.append("Bezpecnost: odkazy byly pouze vypsany z lokalniho archivu; nebyly otevreny.")
    return "\n".join(lines)


def has_explicit_archive_link_confirmation(
    archive_id: str,
    uid: str,
    confirmation_text: str,
) -> bool:
    normalized = _normalize_confirmation_text(confirmation_text)
    identifiers = [identifier.casefold() for identifier in (archive_id, uid) if identifier]
    return (
        any(identifier in confirmation_text.casefold() for identifier in identifiers)
        and any(word in normalized for word in CONFIRMATION_WORDS)
        and any(word in normalized for word in LINK_WORDS)
    )


def _load_archive_entries(directory: Path) -> list[dict[str, Any]]:
    if not directory.exists():
        return []
    entries: list[dict[str, Any]] = []
    for metadata_path in sorted(directory.glob("*/metadata.json")):
        try:
            metadata = _read_json(metadata_path)
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(metadata, dict):
            entries.append({"path": metadata_path.parent, "metadata": metadata})
    return entries


def _resolve_archive(
    archive_id_or_uid: str,
    directory: Path,
) -> tuple[Path, dict[str, Any]] | str:
    identifier = archive_id_or_uid.strip()
    if not identifier:
        return "Chybi archive id nebo UID archivu."

    candidates: list[tuple[Path, dict[str, Any]]] = []
    if SAFE_ARCHIVE_ID_PATTERN.fullmatch(identifier):
        exact_path = directory / identifier / "metadata.json"
        if exact_path.exists():
            metadata = _read_json(exact_path)
            if isinstance(metadata, dict):
                return exact_path.parent, metadata

    identifier_folded = identifier.casefold()
    for entry in _load_archive_entries(directory):
        metadata = entry["metadata"]
        archive_id = str(metadata.get("archive_id", ""))
        uid = str(metadata.get("uid", ""))
        subject = str(metadata.get("subject", ""))
        if (
            identifier in {archive_id, uid}
            or identifier_folded in archive_id.casefold()
            or identifier_folded in subject.casefold()
        ):
            candidates.append((entry["path"], metadata))

    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        ids = ", ".join(_safe_text(item[1].get("archive_id")) for item in candidates)
        return f"Nalezeno vice archivu, upresni archive id nebo UID: {ids}"
    return "Archiv nebyl nalezen."


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_links(archive_dir: Path) -> list[dict[str, Any]]:
    links_path = archive_dir / "links.json"
    if not links_path.exists():
        return []
    data = _read_json(links_path)
    links = data.get("links") if isinstance(data, dict) else None
    return links if isinstance(links, list) else []


def _read_attachments(archive_dir: Path) -> list[dict[str, Any]]:
    attachments_path = archive_dir / "attachments" / "attachments.json"
    if not attachments_path.exists():
        return []
    data = _read_json(attachments_path)
    attachments = data.get("attachments") if isinstance(data, dict) else None
    return attachments if isinstance(attachments, list) else []


def _relative_files(directory: Path) -> list[str]:
    return sorted(str(path.relative_to(directory)) for path in directory.rglob("*") if path.is_file())


def _safe_text(value: Any) -> str:
    text = str(value) if value is not None else ""
    text = URL_PATTERN.sub("[URL redigovano]", text)
    text = redact_email_addresses(text)
    return " ".join(text.split())


def _safe_domain(value: Any) -> str:
    domain = str(value) if value is not None else ""
    if "/" in domain or "@" in domain:
        return ""
    return domain


def _yes_no(value: Any) -> str:
    return "ano" if bool(value) else "ne"


def _sanitize_safe_output(text: str) -> str:
    text = URL_PATTERN.sub("[URL redigovano]", text)
    text = redact_email_addresses(text)
    if URL_PATTERN.search(text) or EMAIL_PATTERN.search(text):
        return "Archivni vystup byl odmitnut, protoze obsahuje citliva data."
    return text


def _normalize_confirmation_text(text: str) -> str:
    normalized = _strip_accents(text.casefold())
    return " ".join(normalized.split())


def _strip_accents(text: str) -> str:
    replacements = str.maketrans(
        {
            "á": "a",
            "č": "c",
            "ď": "d",
            "é": "e",
            "ě": "e",
            "í": "i",
            "ň": "n",
            "ó": "o",
            "ř": "r",
            "š": "s",
            "ť": "t",
            "ú": "u",
            "ů": "u",
            "ý": "y",
            "ž": "z",
        }
    )
    return text.translate(replacements)
