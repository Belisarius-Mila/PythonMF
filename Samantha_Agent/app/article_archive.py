from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE_ROOT = PROJECT_ROOT / "data" / "private" / "article_archive"

CATEGORY_LABELS = {
    "recipes": "Recepty",
    "science": "Vědecké články",
    "ai_tools": "Samantha / AI nástroje",
    "other": "Ostatní",
}

SUPPORTED_ATTACHMENT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
ATTACHMENT_CONFIRMATION_PHRASE = "Potvrzuji připojení obrázku"
DELETE_CONFIRMATION_PHRASE = "Potvrzuji vyřazení z knihovny"


@dataclass(frozen=True)
class ArticleAttachment:
    id: str
    label: str
    kind: str
    role: str
    mime_type: str
    original_file: str
    readable_file: str
    thumb_file: str
    size_bytes: int
    note: str
    created_at: str

    def to_summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "role": self.role,
            "mime_type": self.mime_type,
            "has_original": bool(self.original_file),
            "has_readable": bool(self.readable_file),
            "has_thumb": bool(self.thumb_file),
            "size_bytes": self.size_bytes,
            "note": self.note,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ArticleArchiveItem:
    id: str
    title: str
    one_line_title: str
    category: str
    category_label: str
    archived_at: str
    source_type: str
    source_label: str
    source_note: str
    source_url: str
    canonical_url: str
    text_file: str
    html_file: str
    text_chars: int
    tags: tuple[str, ...]
    attachments: tuple[ArticleAttachment, ...] = ()

    def to_summary(self, snippet: str = "", include_attachments: bool = False) -> dict[str, Any]:
        attachment_types = sorted({attachment.kind for attachment in self.attachments if attachment.kind})
        attachment_roles = sorted({attachment.role for attachment in self.attachments if attachment.role})
        return {
            "id": self.id,
            "title": self.title,
            "one_line_title": self.one_line_title,
            "category": self.category,
            "category_label": self.category_label,
            "archived_at": self.archived_at,
            "source_type": self.source_type,
            "source_label": self.source_label,
            "source_note": self.source_note,
            "source_url": self.source_url,
            "canonical_url": self.canonical_url,
            "text_chars": self.text_chars,
            "tags": list(self.tags),
            "snippet": snippet,
            "attachment_count": len(self.attachments),
            "attachment_types": attachment_types,
            "attachment_roles": attachment_roles,
            **(
                {"attachments": [attachment.to_summary() for attachment in self.attachments]}
                if include_attachments
                else {}
            ),
        }


@dataclass(frozen=True)
class ExtractedArticle:
    title: str
    text: str
    canonical_url: str


class ReadableTextParser(HTMLParser):
    BLOCK_TAGS = {
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dt",
        "figcaption",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "ol",
        "p",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
    SKIP_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = html.unescape(data)
        if text.strip():
            self.parts.append(text)

    def text(self) -> str:
        raw = "".join(self.parts)
        lines = []
        for line in raw.splitlines():
            cleaned = " ".join(line.split())
            if cleaned:
                lines.append(cleaned)
        return "\n".join(collapse_repeated_lines(lines))


def collapse_repeated_lines(lines: list[str]) -> list[str]:
    result: list[str] = []
    previous = ""
    repeated = 0
    for line in lines:
        if line == previous:
            repeated += 1
            if repeated > 1:
                continue
        else:
            repeated = 0
        result.append(line)
        previous = line
    return result


def normalize_category(value: str) -> str:
    category = str(value or "").strip().casefold()
    aliases = {
        "recipe": "recipes",
        "recept": "recipes",
        "recepty": "recipes",
        "science": "science",
        "scientific": "science",
        "věda": "science",
        "veda": "science",
        "vědecké články": "science",
        "vedecke clanky": "science",
        "ai": "ai_tools",
        "ai tools": "ai_tools",
        "ai_tools": "ai_tools",
        "samantha": "ai_tools",
        "samantha ai": "ai_tools",
        "samantha / ai nástroje": "ai_tools",
        "samantha / ai nastroje": "ai_tools",
        "ai nástroje": "ai_tools",
        "ai nastroje": "ai_tools",
        "openai": "ai_tools",
        "codex": "ai_tools",
        "agents sdk": "ai_tools",
        "other": "other",
        "ostatní": "other",
        "ostatni": "other",
    }
    return aliases.get(category, category if category in CATEGORY_LABELS else "other")


def archive_url(
    *,
    url: str,
    category: str = "other",
    tags: list[str] | None = None,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    timeout: float = 25.0,
) -> dict[str, Any]:
    normalized_url = validate_archive_url(url)
    html_bytes = fetch_url(normalized_url, timeout=timeout)
    article = extract_article(html_bytes, normalized_url)
    metadata = write_article_archive(
        source_url=normalized_url,
        html_bytes=html_bytes,
        article=article,
        archive_root=archive_root,
        now=datetime.now(timezone.utc).replace(microsecond=0),
        category=category,
        tags=tags or [],
    )
    return {
        "ok": True,
        "message": "Článek uložen do soukromé knihovny.",
        "item": article_item_from_raw(metadata).to_summary(),
    }


def archive_text_entry(
    *,
    title: str,
    text: str,
    category: str = "other",
    tags: list[str] | None = None,
    source_label: str = "Vložený text",
    source_note: str = "",
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    clean_title = compact_title(str(title or ""))
    clean_text = normalize_manual_text(text)
    if not clean_text:
        raise ValueError("Vlož text, který mám uložit.")
    if clean_title == "Bez názvu":
        clean_title = first_text_line(clean_text) or "Vložený text"
    metadata = write_text_archive(
        title=clean_title,
        text=clean_text,
        archive_root=archive_root,
        now=datetime.now(timezone.utc).replace(microsecond=0),
        category=category,
        tags=tags or [],
        source_label=source_label,
        source_note=source_note,
    )
    return {
        "ok": True,
        "message": "Text uložen do znalostní databáze.",
        "item": article_item_from_raw(metadata).to_summary(),
    }


def attach_article_image(
    *,
    article_id: str,
    image_path: Path | str | None = None,
    image_bytes: bytes | None = None,
    filename: str = "",
    label: str = "",
    role: str = "handwritten_recipe_scan",
    note: str = "",
    mime_type: str = "",
    tags: list[str] | None = None,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> dict[str, Any]:
    if not user_confirmed or ATTACHMENT_CONFIRMATION_PHRASE.casefold() not in str(confirmation_text).casefold():
        raise ValueError(f"Připojení obrázku vyžaduje potvrzení: {ATTACHMENT_CONFIRMATION_PHRASE}")
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        raise ValueError("Článek nebyl nalezen.")
    raw_bytes, source_name = read_attachment_input(image_path=image_path, image_bytes=image_bytes, filename=filename)
    extension = normalized_image_extension(source_name, mime_type=mime_type)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    attachment_id = unique_attachment_id(item, label or Path(source_name).stem or "obrazek", now)
    item_dir = archive_root / "articles" / item.id
    original_dir = item_dir / "attachments" / "original"
    readable_dir = item_dir / "attachments" / "readable"
    thumb_dir = item_dir / "attachments" / "thumbs"
    original_dir.mkdir(parents=True, exist_ok=True)
    readable_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir.mkdir(parents=True, exist_ok=True)
    original_path = original_dir / f"{attachment_id}{extension}"
    readable_path = readable_dir / f"{attachment_id}.jpg"
    thumb_path = thumb_dir / f"{attachment_id}.jpg"
    original_path.write_bytes(raw_bytes)
    readable_bytes, thumb_bytes = build_readable_image_versions(raw_bytes)
    readable_path.write_bytes(readable_bytes)
    thumb_path.write_bytes(thumb_bytes)
    attachment = {
        "id": attachment_id,
        "label": str(label or "Doprovodný obrázek").strip()[:160] or "Doprovodný obrázek",
        "kind": "image",
        "role": str(role or "supporting_image").strip()[:80] or "supporting_image",
        "mime_type": mime_type_for_extension(extension),
        "original_file": str(original_path.relative_to(archive_root)),
        "readable_file": str(readable_path.relative_to(archive_root)),
        "thumb_file": str(thumb_path.relative_to(archive_root)),
        "size_bytes": len(raw_bytes),
        "readable_size_bytes": len(readable_bytes),
        "thumb_size_bytes": len(thumb_bytes),
        "note": str(note or "").strip()[:1000],
        "created_at": now.isoformat(),
    }
    metadata = append_attachment_metadata(
        archive_root=archive_root,
        item_id=item.id,
        attachment=attachment,
        tags=tags or [],
    )
    return {
        "ok": True,
        "message": "Obrázek připojen ke znalostní kartě.",
        "item": article_item_from_raw(metadata).to_summary(include_attachments=True),
        "attachment": ArticleAttachment(**{  # type: ignore[arg-type]
            "id": str(attachment["id"]),
            "label": str(attachment["label"]),
            "kind": str(attachment["kind"]),
            "role": str(attachment["role"]),
            "mime_type": str(attachment["mime_type"]),
            "original_file": str(attachment["original_file"]),
            "readable_file": str(attachment["readable_file"]),
            "thumb_file": str(attachment["thumb_file"]),
            "size_bytes": int(attachment["size_bytes"]),
            "note": str(attachment["note"]),
            "created_at": str(attachment["created_at"]),
        }).to_summary(),
    }


def read_attachment_input(
    *,
    image_path: Path | str | None,
    image_bytes: bytes | None,
    filename: str,
) -> tuple[bytes, str]:
    if image_bytes is not None:
        if not image_bytes:
            raise ValueError("Obrázek je prázdný.")
        return image_bytes, filename or "attachment.jpg"
    if image_path is None:
        raise ValueError("Zadej cestu k obrázku nebo image_bytes.")
    path = Path(image_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise ValueError(f"Obrázek neexistuje: {path}")
    if path.suffix.casefold() not in SUPPORTED_ATTACHMENT_EXTENSIONS:
        raise ValueError("Podporované přílohy jsou JPG, PNG, WEBP, HEIC/HEIF.")
    return path.read_bytes(), path.name


def normalized_image_extension(filename: str, *, mime_type: str = "") -> str:
    suffix = Path(filename or "").suffix.casefold()
    if suffix in SUPPORTED_ATTACHMENT_EXTENSIONS:
        return ".jpg" if suffix == ".jpeg" else suffix
    normalized_mime = str(mime_type or "").casefold()
    if normalized_mime == "image/png":
        return ".png"
    if normalized_mime == "image/webp":
        return ".webp"
    if normalized_mime in {"image/heic", "image/heif"}:
        return ".heic"
    return ".jpg"


def mime_type_for_extension(extension: str) -> str:
    suffix = extension.casefold()
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    if suffix in {".heic", ".heif"}:
        return "image/heic"
    return "image/jpeg"


def unique_attachment_id(item: ArticleArchiveItem, label: str, now: datetime) -> str:
    base = slugify(label or "obrazek", max_length=44)
    existing = {attachment.id for attachment in item.attachments}
    suffix = hashlib.sha256(f"{item.id}\n{label}\n{now.isoformat()}".encode("utf-8")).hexdigest()[:6]
    candidate = slugify(f"{base}-{suffix}", max_length=52)
    counter = 2
    while candidate in existing:
        candidate = slugify(f"{base}-{suffix}-{counter}", max_length=56)
        counter += 1
    return candidate


def build_readable_image_versions(raw_bytes: bytes) -> tuple[bytes, bytes]:
    try:
        from PIL import Image, ImageOps
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on local environment setup
        raise ValueError("Pillow není nainstalovaný, nejde vytvořit čitelnou kopii obrázku.") from exc
    image = Image.open(BytesIO(raw_bytes))
    image = ImageOps.exif_transpose(image)
    readable = prepare_image_for_jpeg(image)
    readable.thumbnail((2600, 2600), Image.Resampling.LANCZOS)
    thumb = prepare_image_for_jpeg(image.copy())
    thumb.thumbnail((520, 520), Image.Resampling.LANCZOS)
    return encode_jpeg(readable, quality=88), encode_jpeg(thumb, quality=78)


def prepare_image_for_jpeg(image: Any) -> Any:
    if image.mode in {"RGBA", "LA", "P"}:
        rgba = image.convert("RGBA")
        try:
            from PIL import Image
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise ValueError("Pillow není nainstalovaný.") from exc
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def encode_jpeg(image: Any, *, quality: int) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=True)
    return buffer.getvalue()


def append_attachment_metadata(
    *,
    archive_root: Path,
    item_id: str,
    attachment: dict[str, Any],
    tags: list[str],
) -> dict[str, Any]:
    metadata_path = archive_root / "articles" / item_id / "metadata.json"
    if not metadata_path.exists():
        raise ValueError("Metadata článku nebyla nalezena.")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError("Metadata článku mají neplatný formát.")
    attachments = metadata.get("attachments", [])
    if not isinstance(attachments, list):
        attachments = []
    attachments.append(attachment)
    metadata["attachments"] = attachments
    existing_tags = [str(tag).strip() for tag in metadata.get("tags", []) if str(tag).strip()] if isinstance(metadata.get("tags"), list) else []
    for tag in tags:
        clean = str(tag).strip()
        if clean and clean not in existing_tags:
            existing_tags.append(clean)
    if attachments and "ma-obrazek" not in existing_tags:
        existing_tags.append("ma-obrazek")
    metadata["tags"] = existing_tags
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_registry(archive_root / "registry.jsonl", metadata)
    return metadata


def validate_archive_url(url: str) -> str:
    value = str(url or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Zadej platnou http/https URL.")
    return value


def fetch_url(url: str, timeout: float = 25.0) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SamanthaAgentArticleArchive/1.0 (+local personal archive)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.URLError as exc:
        if not is_certificate_verify_failure(exc):
            raise
        return fetch_url_with_curl(url, timeout=timeout)


def is_certificate_verify_failure(exc: urllib.error.URLError) -> bool:
    reason = getattr(exc, "reason", None)
    return isinstance(reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(exc)


def fetch_url_with_curl(url: str, timeout: float = 25.0) -> bytes:
    completed = subprocess.run(
        [
            "curl",
            "--fail",
            "--location",
            "--silent",
            "--show-error",
            "--max-time",
            str(max(1, int(timeout))),
            url,
        ],
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise urllib.error.URLError(message or f"curl failed with exit {completed.returncode}")
    return completed.stdout


def extract_article(html_bytes: bytes, source_url: str) -> ExtractedArticle:
    html_text = html_bytes.decode("utf-8", errors="replace")
    title = extract_title(html_text) or urlparse(source_url).netloc or "article"
    canonical = extract_canonical_url(html_text) or strip_tracking_query(source_url)
    parser = ReadableTextParser()
    parser.feed(html_text)
    text = trim_to_article_body(parser.text(), title)
    return ExtractedArticle(title=title, text=text, canonical_url=canonical)


def extract_title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.I | re.S)
    if not match:
        return ""
    title = html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    return title


def extract_canonical_url(html_text: str) -> str:
    match = re.search(
        r"<link[^>]+rel=[\"']canonical[\"'][^>]+href=[\"']([^\"']+)[\"']",
        html_text,
        flags=re.I,
    )
    if not match:
        return ""
    return html.unescape(match.group(1)).strip()


def strip_tracking_query(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def trim_to_article_body(text: str, title: str) -> str:
    lines = text.splitlines()
    if not lines:
        return ""
    start = detect_article_start(lines, title)
    stop_markers = (
        "Související produkty",
        "Diskuze",
        "Přidat komentář",
        "Newsletter",
        "Naposledy navštívené",
        "Hlídací pes",
        "Podobné produkty",
        "Mohlo by se vám hodit",
        "Související články",
        "Předchozí článek",
        "Zápatí",
        "Sector 31",
        "Vytvořil Shoptet",
        "Copyright",
    )
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if any(marker.casefold() in lines[index].casefold() for marker in stop_markers):
            end = index
            break
    body_lines = clean_article_lines(lines[start:end])
    return "\n".join(body_lines).strip()


def clean_article_lines(lines: list[str]) -> list[str]:
    ignored_lines = {"postranní panel", "postranni panel", "."}
    cleaned = [line for line in lines if line.strip().casefold() not in ignored_lines]
    while cleaned and cleaned[0].strip().casefold() in ignored_lines:
        cleaned.pop(0)
    return cleaned


def detect_article_start(lines: list[str], title: str) -> int:
    title_head = title.split("|", 1)[0].strip()
    title_words = significant_words(title_head)
    candidates: list[tuple[int, int]] = []

    for index, line in enumerate(lines):
        folded = line.casefold()
        if index > 10 and "domů/" in folded and title_words:
            score = matching_word_count(folded, title_words)
            if score >= min(2, len(title_words)):
                candidates.append((95 + score, min(index + 1, len(lines) - 1)))
        if index > 10 and title_words:
            score = matching_word_count(folded, title_words)
            if score >= min(3, len(title_words)) and len(line) <= 180:
                candidates.append((80 + score, index))
        if index > 10 and title_head and title_head.casefold() in folded:
            candidates.append((70, index))

    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    for index, line in enumerate(lines):
        if index > 10 and title_head and title_head.casefold() in line.casefold():
            return index
    return 0


def significant_words(value: str) -> list[str]:
    words = re.findall(r"[0-9A-Za-zÁ-ž]{4,}", value.casefold())
    ignored = {"postup", "postupy", "navody", "návody", "praha", "naradi", "nářadí"}
    return [word for word in words if word not in ignored]


def matching_word_count(folded_line: str, words: list[str]) -> int:
    return sum(1 for word in words if word in folded_line)


def slugify(value: str, max_length: int = 72) -> str:
    table = str.maketrans(
        "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ",
        "acdeeinorstuuyzACDEEINORSTUUYZ",
    )
    ascii_text = value.translate(table)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_text).strip("-").lower()
    return (slug or "article")[:max_length].strip("-") or "article"


def article_id(title: str, canonical_url: str, now: datetime) -> str:
    digest = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()[:8]
    return f"{now.date().isoformat()}_{slugify(title)}_{digest}"


def text_entry_id(title: str, text: str, now: datetime) -> str:
    digest_source = f"{title}\n{text}\n{now.isoformat()}"
    digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:8]
    return f"{now.date().isoformat()}_{slugify(title)}_{digest}"


def write_article_archive(
    *,
    source_url: str,
    html_bytes: bytes,
    article: ExtractedArticle,
    archive_root: Path,
    now: datetime,
    category: str,
    tags: list[str],
) -> dict[str, Any]:
    item_id = article_id(article.title, article.canonical_url or source_url, now)
    item_dir = archive_root / "articles" / item_id
    item_dir.mkdir(parents=True, exist_ok=True)
    html_path = item_dir / "source.html"
    text_path = item_dir / "article.txt"
    metadata_path = item_dir / "metadata.json"
    html_path.write_bytes(html_bytes)
    text_path.write_text(article.text + "\n", encoding="utf-8")
    metadata: dict[str, Any] = {
        "id": item_id,
        "title": article.title,
        "one_line_title": compact_title(article.title),
        "category": normalize_category(category),
        "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
        "source_url": source_url,
        "canonical_url": article.canonical_url,
        "archived_at": now.isoformat(),
        "text_file": str(text_path.relative_to(archive_root)),
        "html_file": str(html_path.relative_to(archive_root)),
        "text_chars": str(len(article.text)),
        "attachments": [],
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_registry(archive_root / "registry.jsonl", metadata)
    return metadata


def write_text_archive(
    *,
    title: str,
    text: str,
    archive_root: Path,
    now: datetime,
    category: str,
    tags: list[str],
    source_label: str,
    source_note: str,
) -> dict[str, Any]:
    clean_text = normalize_manual_text(text)
    item_id = text_entry_id(title, clean_text, now)
    item_dir = archive_root / "articles" / item_id
    item_dir.mkdir(parents=True, exist_ok=True)
    text_path = item_dir / "article.txt"
    metadata_path = item_dir / "metadata.json"
    text_path.write_text(clean_text + "\n", encoding="utf-8")
    metadata: dict[str, Any] = {
        "id": item_id,
        "title": title,
        "one_line_title": compact_title(title),
        "category": normalize_category(category),
        "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
        "source_type": "manual_text",
        "source_label": str(source_label or "Vložený text").strip()[:160] or "Vložený text",
        "source_note": str(source_note or "").strip()[:1000],
        "source_url": "",
        "canonical_url": "",
        "archived_at": now.isoformat(),
        "text_file": str(text_path.relative_to(archive_root)),
        "html_file": "",
        "text_chars": str(len(clean_text)),
        "attachments": [],
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_registry(archive_root / "registry.jsonl", metadata)
    return metadata


def update_registry(path: Path, metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    replaced = False
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(item.get("id", "")) == metadata["id"]:
                rows.append(metadata)
                replaced = True
            elif isinstance(item, dict):
                rows.append(item)
    if not replaced:
        rows.append(metadata)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def remove_from_registry(path: Path, item_id: str) -> dict[str, Any] | None:
    wanted = str(item_id or "").strip()
    if not wanted or not path.exists():
        return None
    rows: list[dict[str, Any]] = []
    removed: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        if str(item.get("id", "")).strip() == wanted:
            removed = item
            continue
        rows.append(item)
    if removed is not None:
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
    return removed


def load_article_registry(archive_root: Path = DEFAULT_ARCHIVE_ROOT) -> list[ArticleArchiveItem]:
    path = archive_root / "registry.jsonl"
    if not path.exists():
        return []
    items: list[ArticleArchiveItem] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(raw, dict):
            continue
        item = article_item_from_raw(raw)
        if item.id and item.text_file:
            items.append(item)
    items.sort(key=article_sort_key, reverse=True)
    return items


def article_item_from_raw(raw: dict[str, Any]) -> ArticleArchiveItem:
    category = normalize_category(str(raw.get("category", "")))
    tags = raw.get("tags", [])
    if isinstance(tags, str):
        tags_tuple = tuple(part.strip() for part in tags.split(",") if part.strip())
    elif isinstance(tags, list):
        tags_tuple = tuple(str(part).strip() for part in tags if str(part).strip())
    else:
        tags_tuple = ()
    attachments = normalize_attachments(raw.get("attachments", []))
    title = str(raw.get("title", "")).strip()
    one_line_title = str(raw.get("one_line_title", "")).strip() or compact_title(title)
    source_url = str(raw.get("source_url", "")).strip()
    canonical_url = str(raw.get("canonical_url", "")).strip()
    source_type = str(raw.get("source_type", "")).strip() or ("url" if source_url or canonical_url else "manual_text")
    source_label = str(raw.get("source_label", "")).strip()
    if not source_label:
        source_label = "URL článek" if source_type == "url" else "Vložený text"
    try:
        text_chars = int(raw.get("text_chars", 0) or 0)
    except (TypeError, ValueError):
        text_chars = 0
    return ArticleArchiveItem(
        id=str(raw.get("id", "")).strip(),
        title=title,
        one_line_title=one_line_title,
        category=category,
        category_label=CATEGORY_LABELS[category],
        archived_at=str(raw.get("archived_at", "")).strip(),
        source_type=source_type,
        source_label=source_label,
        source_note=str(raw.get("source_note", "")).strip(),
        source_url=source_url,
        canonical_url=canonical_url,
        text_file=str(raw.get("text_file", "")).strip(),
        html_file=str(raw.get("html_file", "")).strip(),
        text_chars=text_chars,
        tags=tags_tuple,
        attachments=attachments,
    )


def normalize_attachments(raw: Any) -> tuple[ArticleAttachment, ...]:
    if not isinstance(raw, list):
        return ()
    attachments: list[ArticleAttachment] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            continue
        attachment_id = slugify(str(item.get("id", "")).strip() or f"attachment-{index}", max_length=48)
        try:
            size_bytes = int(item.get("size_bytes", 0) or 0)
        except (TypeError, ValueError):
            size_bytes = 0
        attachments.append(
            ArticleAttachment(
                id=attachment_id,
                label=str(item.get("label", "")).strip()[:160] or f"Příloha {index}",
                kind=str(item.get("kind", "")).strip()[:80] or "image",
                role=str(item.get("role", "")).strip()[:80] or "supporting",
                mime_type=str(item.get("mime_type", "")).strip()[:120] or "application/octet-stream",
                original_file=str(item.get("original_file", "")).strip(),
                readable_file=str(item.get("readable_file", "")).strip(),
                thumb_file=str(item.get("thumb_file", "")).strip(),
                size_bytes=max(0, size_bytes),
                note=str(item.get("note", "")).strip()[:1000],
                created_at=str(item.get("created_at", "")).strip(),
            )
        )
    return tuple(attachments)


def compact_title(title: str) -> str:
    head = title.split("|", 1)[0].strip()
    return head or title.strip() or "Bez názvu"


def normalize_manual_text(text: str) -> str:
    lines = []
    for line in str(text or "").replace("\r\n", "\n").replace("\r", "\n").splitlines():
        lines.append(line.rstrip())
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()


def first_text_line(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if clean:
            return compact_title(clean[:120])
    return ""


def article_sort_key(item: ArticleArchiveItem) -> tuple[str, str]:
    return (normalized_datetime(item.archived_at), item.id)


def normalized_datetime(value: str) -> str:
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return value


def list_articles(
    *,
    category: str = "other",
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    limit: int = 200,
) -> dict[str, Any]:
    wanted = normalize_category(category)
    items = [
        item.to_summary()
        for item in load_article_registry(archive_root)
        if item.category == wanted
    ]
    return {
        "ok": True,
        "category": wanted,
        "category_label": CATEGORY_LABELS[wanted],
        "items": items[: max(1, min(limit, 500))],
        "count": len(items),
    }


def search_articles(
    *,
    query: str,
    category: str = "all",
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    limit: int = 50,
) -> dict[str, Any]:
    terms = [term.casefold() for term in query.split() if term.strip()]
    if not terms:
        return {"ok": True, "query": query, "items": [], "count": 0}
    wanted = normalize_category(category) if category != "all" else "all"
    results: list[tuple[int, ArticleArchiveItem, str]] = []
    for item in load_article_registry(archive_root):
        if wanted != "all" and item.category != wanted:
            continue
        text = read_article_text(item.id, archive_root=archive_root, max_chars=0)
        folded = text.casefold()
        score = sum(folded.count(term) for term in terms)
        title_score = sum(item.one_line_title.casefold().count(term) for term in terms) * 3
        total_score = score + title_score
        if total_score <= 0:
            continue
        results.append((total_score, item, make_snippet(text, terms)))
    results.sort(key=lambda row: row[0], reverse=True)
    limited = results[: max(1, min(limit, 200))]
    return {
        "ok": True,
        "query": query,
        "category": wanted,
        "items": [
            {
                **item.to_summary(snippet=snippet),
                "score": score,
            }
            for score, item, snippet in limited
        ],
        "count": len(results),
    }


def get_article(
    *,
    article_id: str,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    max_chars: int = 40000,
) -> dict[str, Any]:
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        return {"ok": False, "error": "not_found", "message": "Článek nebyl nalezen."}
    text = read_article_text(item.id, archive_root=archive_root, max_chars=max_chars)
    return {
        "ok": True,
        "item": item.to_summary(include_attachments=True),
        "text": text,
        "truncated": max_chars > 0 and len(text) >= max_chars,
    }


def find_article(article_id: str, archive_root: Path = DEFAULT_ARCHIVE_ROOT) -> ArticleArchiveItem | None:
    wanted = str(article_id or "").strip()
    if not wanted:
        return None
    for item in load_article_registry(archive_root):
        if item.id == wanted:
            return item
    return None


def delete_article(
    *,
    article_id: str,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> dict[str, Any]:
    if not user_confirmed or DELETE_CONFIRMATION_PHRASE.casefold() not in str(confirmation_text).casefold():
        raise ValueError(f"Vyřazení položky vyžaduje potvrzení: {DELETE_CONFIRMATION_PHRASE}")
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        raise ValueError("Článek nebyl nalezen.")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    trash_root = archive_root / "trash" / "articles"
    trash_root.mkdir(parents=True, exist_ok=True)
    source_dir = archive_root / "articles" / item.id
    trash_dir = next_trash_path(trash_root / f"{now.strftime('%Y%m%d_%H%M%S')}_{item.id}")
    moved_to = ""
    if source_dir.exists():
        shutil.move(str(source_dir), str(trash_dir))
        moved_to = str(trash_dir.relative_to(archive_root))

    registry_path = archive_root / "registry.jsonl"
    removed = remove_from_registry(registry_path, item.id)
    if removed is None:
        if moved_to:
            shutil.move(str(trash_dir), str(source_dir))
        raise ValueError("Článek nebyl nalezen v registru.")

    manifest = {
        "id": item.id,
        "title": item.title,
        "category": item.category,
        "removed_at": now.isoformat(),
        "moved_to": moved_to,
        "registry_entry": removed,
    }
    manifest_path = trash_dir / "removed_from_registry.json" if moved_to else trash_root / f"{item.id}_removed_from_registry.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "message": "Položka byla vyřazena z knihovny a přesunuta do soukromého koše.",
        "item_id": item.id,
        "title": item.one_line_title,
        "trash_path": moved_to,
    }


def next_trash_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.name}_{index}")
        if not candidate.exists():
            return candidate
    raise OSError("Nepodařilo se najít volný název v koši archivu.")


def read_article_text(article_id: str, archive_root: Path = DEFAULT_ARCHIVE_ROOT, max_chars: int = 0) -> str:
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        return ""
    text_path = archive_root / item.text_file
    if not text_path.exists():
        return ""
    text = text_path.read_text(encoding="utf-8", errors="replace").strip()
    if max_chars > 0 and len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text


def get_article_attachment(
    *,
    article_id: str,
    attachment_id: str,
    variant: str = "readable",
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
) -> dict[str, Any]:
    item = find_article(article_id, archive_root=archive_root)
    if item is None:
        return {"ok": False, "error": "not_found", "message": "Článek nebyl nalezen."}
    wanted = slugify(str(attachment_id or "").strip(), max_length=48)
    attachment = next((entry for entry in item.attachments if entry.id == wanted), None)
    if attachment is None:
        return {"ok": False, "error": "not_found", "message": "Příloha nebyla nalezena."}
    variant_key = str(variant or "readable").strip().casefold()
    candidates = {
        "thumb": [attachment.thumb_file, attachment.readable_file, attachment.original_file],
        "thumbnail": [attachment.thumb_file, attachment.readable_file, attachment.original_file],
        "readable": [attachment.readable_file, attachment.original_file],
        "original": [attachment.original_file],
    }.get(variant_key, [attachment.readable_file, attachment.original_file])
    for relative_path in candidates:
        resolved = resolve_archive_relative_file(archive_root, relative_path)
        if resolved is not None and resolved.is_file():
            return {
                "ok": True,
                "path": resolved,
                "attachment": attachment.to_summary(),
                "mime_type": mime_type_for_extension(resolved.suffix),
                "filename": resolved.name,
            }
    return {"ok": False, "error": "not_found", "message": "Soubor přílohy nebyl nalezen."}


def resolve_archive_relative_file(archive_root: Path, relative_path: str) -> Path | None:
    value = str(relative_path or "").strip()
    if not value:
        return None
    if Path(value).is_absolute():
        return None
    try:
        root = archive_root.resolve(strict=True)
        target = (archive_root / value).resolve(strict=True)
    except FileNotFoundError:
        return None
    if root != target and root not in target.parents:
        return None
    return target


def make_snippet(text: str, terms: list[str], radius: int = 180) -> str:
    folded = text.casefold()
    positions = [folded.find(term) for term in terms if folded.find(term) >= 0]
    if not positions:
        return " ".join(text[: radius * 2].split())
    center = min(positions)
    start = max(0, center - radius)
    end = min(len(text), center + radius)
    return " ".join(text[start:end].split())
