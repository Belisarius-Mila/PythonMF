from __future__ import annotations

import hashlib
import html
import json
import re
import ssl
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE_ROOT = PROJECT_ROOT / "data" / "private" / "article_archive"

CATEGORY_LABELS = {
    "recipes": "Recepty",
    "science": "Vědecké články",
    "other": "Ostatní",
}


@dataclass(frozen=True)
class ArticleArchiveItem:
    id: str
    title: str
    one_line_title: str
    category: str
    category_label: str
    archived_at: str
    source_url: str
    canonical_url: str
    text_file: str
    html_file: str
    text_chars: int
    tags: tuple[str, ...]

    def to_summary(self, snippet: str = "") -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "one_line_title": self.one_line_title,
            "category": self.category,
            "category_label": self.category_label,
            "archived_at": self.archived_at,
            "source_url": self.source_url,
            "canonical_url": self.canonical_url,
            "text_chars": self.text_chars,
            "tags": list(self.tags),
            "snippet": snippet,
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
    title = str(raw.get("title", "")).strip()
    one_line_title = str(raw.get("one_line_title", "")).strip() or compact_title(title)
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
        source_url=str(raw.get("source_url", "")).strip(),
        canonical_url=str(raw.get("canonical_url", "")).strip(),
        text_file=str(raw.get("text_file", "")).strip(),
        html_file=str(raw.get("html_file", "")).strip(),
        text_chars=text_chars,
        tags=tags_tuple,
    )


def compact_title(title: str) -> str:
    head = title.split("|", 1)[0].strip()
    return head or title.strip() or "Bez názvu"


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
        "item": item.to_summary(),
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


def make_snippet(text: str, terms: list[str], radius: int = 180) -> str:
    folded = text.casefold()
    positions = [folded.find(term) for term in terms if folded.find(term) >= 0]
    if not positions:
        return " ".join(text[: radius * 2].split())
    center = min(positions)
    start = max(0, center - radius)
    end = min(len(text), center + radius)
    return " ".join(text[start:end].split())
