"""ScienceNews inbox. One atomic state, durable decisions and replay-safe archive.

Importing or reading this module never creates data or calls a model/network.
"""
from __future__ import annotations

import hashlib
import json
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from app.file_persistence import atomic_create_text, atomic_replace_text_under_external_lock, exclusive_file_lock

ROOT = Path(__file__).resolve().parents[1] / "data/private/science_news"
AREAS = ("Astrofyzika", "Částicová fyzika", "Evoluce", "Paleontologie", "Antropologie", "Genetika", "Lékařské vědy", "AI")
ID = re.compile(r"[a-zA-Z0-9_-]{1,100}\Z")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def public_url(value):
    """Links only; fetching has its own fixed allowlist in science_news_sources."""
    parsed = urlsplit(str(value))
    host = parsed.hostname or ""
    if (parsed.scheme != "https" or not host or "." not in host or parsed.username
            or parsed.password or parsed.port not in (None, 443)
            or host.endswith((".local", ".localhost", ".internal"))
            or re.fullmatch(r"[\d.:]+", host)):
        raise ValueError("Zdroj musí mít veřejnou HTTPS adresu.")
    return urlunsplit(("https", parsed.netloc.lower(), parsed.path, parsed.query, ""))


def identity(item):
    doi = str(item.get("doi", "")).strip().lower()
    doi = re.sub(r"^https://(?:dx\.)?doi.org/", "", doi)
    if doi and not re.fullmatch(r"10\.\d{4,9}/\S{1,200}", doi):
        raise ValueError("Neplatné DOI.")
    base = "sn_" + digest(doi or public_url(item["source_url"]))[:32]
    revision = item.get("revision_digest")
    if revision:
        if not re.fullmatch(r"[a-f0-9]{64}", revision) or not item.get("topic_id"):
            raise ValueError("Nová revize nemá ověřenou vazbu na téma.")
        return base + "_u" + revision[:16]
    return base


def validate_item(raw):
    item = dict(raw)
    for key, limit in (("title", 400), ("abstract_cs", 6000), ("significance_cs", 2000), ("uncertainty_cs", 2000)):
        if not isinstance(item.get(key), str) or not 1 <= len(item[key].strip()) <= limit:
            raise ValueError("Zpráva nemá úplný český abstrakt, význam a omezení.")
    if item.get("area") not in AREAS or item.get("category") not in ("science", "health_info"):
        raise ValueError("Neplatný obor nebo kategorie.")
    item["source_url"] = public_url(item["source_url"])
    if item.get("study_url"):
        item["study_url"] = public_url(item["study_url"])
    datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
    item["id"] = identity(item)
    item["topic_id"] = item.get("topic_id") or item["id"]
    if not ID.fullmatch(item["topic_id"]):
        raise ValueError("Neplatná vazba sledování.")
    # Only trusted editorial import may attach reusable full source text. Model
    # output is projected onto an explicit smaller set of fields by the runner.
    if len(item.get("source_text", "")) > 120_000:
        raise ValueError("Plný text překročil limit.")
    return item


def _empty():
    return {"schema": 1, "items": {}, "issues": {}, "operations": {}, "follows": {}, "jobs": {}}


class ScienceNews:
    def __init__(self, root=ROOT, archive_root=None):
        if Path(root).is_symlink():
            raise ValueError("Úložiště ScienceNews nesmí být symlink.")
        # Canonicalize OS aliases such as macOS /var -> /private/var once;
        # subsequent checks still reject substitution of any canonical component.
        self.root = Path(root).resolve()
        self.path = self.root / "state.json"
        if archive_root is None:
            from app.article_archive import DEFAULT_ARCHIVE_ROOT
            archive_root = DEFAULT_ARCHIVE_ROOT
        if Path(archive_root).is_symlink():
            raise ValueError("Archiv nesmí být symlink.")
        self.archive_root = Path(archive_root).resolve()

    def _safe(self):
        for p in (self.root, *self.root.parents, self.path, self.root / "state.json.lock"):
            if p.is_symlink():
                raise ValueError("Úložiště ScienceNews nesmí být symlink.")

    def _read(self):
        self._safe()
        if not self.path.exists():
            return _empty()
        raw = json.loads(self.path.read_text())
        if raw.get("schema") != 1 or any(not isinstance(raw.get(k), dict) for k in _empty() if k != "schema"):
            raise ValueError("Stav ScienceNews je neplatný; fronta není označená za prázdnou.")
        return raw

    @contextmanager
    def transaction(self):
        self._safe()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        with exclusive_file_lock(self.path):
            state = self._read()
            yield state
            atomic_replace_text_under_external_lock(self.path, json.dumps(state, ensure_ascii=False) + "\n")

    def overview(self):
        state = self._read()
        items = []
        for item in state["items"].values():
            if item.get("decision") is None:
                visible = {k: v for k, v in item.items() if k not in ("source_text", "translation", "translation_permission")}
                visible["translation_available"] = bool(item.get("translation"))
                visible["translation_supported"] = bool(item.get("source_text") and item.get("translation_permission") in ("cc-by", "cc-by-sa", "cc0", "public-domain", "user-provided"))
                items.append(visible)
        items.sort(key=lambda i: (i["published_at"], i["id"]), reverse=True)
        return {"ok": True, "items": items, "pending_count": len(items),
                "follows": list(state["follows"].values()), "initialized": self.path.exists(),
                "issues": [{k: v for k, v in i.items() if k != "fingerprint"} for i in state["issues"].values()]}

    def publish(self, issue_id, items, *, available_at, source_health=None):
        if not ID.fullmatch(issue_id) or len(items) > 5:
            raise ValueError("Vydání smí mít nejvýše pět zpráv.")
        clean = [validate_item(i) for i in items]
        if len({i["id"] for i in clean}) != len(clean):
            raise ValueError("Duplicitní objev ve vydání.")
        fingerprint = digest({"items": clean, "available_at": available_at})
        with self.transaction() as state:
            if issue_id in state["issues"]:
                if state["issues"][issue_id]["fingerprint"] != fingerprint:
                    raise ValueError("Vydání již existuje s jiným obsahem.")
                return {"ok": True, "replayed": True}
            for item in clean:
                # Never resurrect a dismissed/saved/followed DOI or overwrite notes.
                if item["id"] not in state["items"]:
                    state["items"][item["id"]] = {**item, "issue_id": issue_id, "decision": None}
            state["issues"][issue_id] = {"id": issue_id, "available_at": available_at,
                "item_count": len(clean), "fingerprint": fingerprint, "source_health": source_health or []}
        return {"ok": True, "replayed": False}

    def decide(self, item_id, action, request_id):
        if action not in ("save", "follow", "dismiss") or not ID.fullmatch(str(request_id)):
            raise ValueError("Neplatná volba nebo identita požadavku.")
        command = {"item_id": item_id, "action": action}
        with self.transaction() as state:
            old = state["operations"].get(request_id)
            if old:
                if old["command"] != command:
                    raise ValueError("Identita požadavku patří jiné akci.")
                if old["state"] == "completed":
                    return {"ok": True, "replayed": True, "archive_id": old.get("archive_id")}
            item = state["items"].get(item_id)
            if not item:
                raise ValueError("Zpráva nebyla nalezena.")
            if item.get("decision"):
                if item["decision"] != action:
                    raise ValueError("Zpráva už byla vyřízena jinou volbou.")
                return {"ok": True, "replayed": True, "archive_id": item.get("archive_id")}
            if action == "save" and state["jobs"].get("translation_" + item_id, {}).get("state") == "running":
                raise ValueError("Nejprve vyčkej na dokončení překladu, aby se uložil celý výsledek.")
            active = item.get("operation")
            if active and active != request_id:
                raise ValueError("Nejprve ověř předchozí operaci této zprávy.")
            state["operations"][request_id] = {"command": command, "state": "started"}
            item["operation"] = request_id
        # The intention is durable before the archive write. A reconnect repeats
        # the SAME command; the deterministic archive reconciles partial writes.
        archive_id = archive_item(item, self.archive_root) if action == "save" else None
        with self.transaction() as state:
            item = state["items"][item_id]
            if action in ("save", "follow"):
                state["follows"][item["topic_id"]] = {"topic_id": item["topic_id"], "title": item["title"],
                    "source_url": item["source_url"], "abstract_cs": item["abstract_cs"],
                    "published_at": item["published_at"], "source_digest": item.get("source_digest", ""),
                    "active": True, "updated_at": utc_now()}
            item.update(decision=action, archive_id=archive_id)
            state["operations"][request_id].update(state="completed", archive_id=archive_id)
        return {"ok": True, "archive_id": archive_id, "replayed": False}

    def unfollow(self, topic_id):
        with self.transaction() as state:
            if topic_id not in state["follows"]:
                raise ValueError("Sledovaná položka nebyla nalezena.")
            state["follows"][topic_id].update(active=False, updated_at=utc_now())
        return {"ok": True}

    def item(self, item_id):
        item = self._read()["items"].get(item_id)
        if item is None:
            raise ValueError("Zpráva nebyla nalezena.")
        return item


def archive_item(item, root):
    """Create-only compatible article; shared archive lock, stable ID, no edits lost."""
    from app.article_archive import _serialized_archive_write, update_registry

    @_serialized_archive_write
    def write(*, archive_root):
        article_id = "science_" + item["id"][3:]
        directory = archive_root / "articles" / article_id
        for p in (archive_root, *archive_root.parents, archive_root / ".archive-write.lock", directory):
            if p.is_symlink():
                raise ValueError("Archiv nesmí být symlink.")
        meta_path = directory / "metadata.json"
        text_path = directory / "article.txt"
        if meta_path.is_symlink() or text_path.is_symlink():
            raise ValueError("Karta nesmí být symlink.")
        origin = digest({k: item[k] for k in ("id", "title", "source_url", "abstract_cs")})
        if meta_path.exists():
            metadata = json.loads(meta_path.read_text())
            if metadata.get("science_origin") != origin or not text_path.is_file():
                raise ValueError("Existující kartu nelze bezpečně přiřadit; nic nepřepisuji.")
        else:
            body = (f"{item['title']}\n\n{item['abstract_cs']}\n\nVýznam: {item['significance_cs']}\n\n"
                    f"Omezení: {item['uncertainty_cs']}\n\nZdroj: {item['source_url']}\n"
                    f"Publikováno: {item['published_at']}\n")
            if item.get("translation"):
                body += "\nČeský překlad zdrojové zprávy:\n" + item["translation"] + "\n"
            if text_path.exists():
                if text_path.read_text() != body:
                    raise ValueError("Neúplná karta obsahuje jiný text; vyžaduje kontrolu.")
            else:
                atomic_create_text(text_path, body)
            metadata = {"id": article_id, "title": item["title"], "one_line_title": item["title"],
                "category": item["category"], "source_type": "url", "source_label": "ScienceNews",
                "source_note": "Vlastní český abstrakt; uložení zapnulo sledování.",
                "source_url": item["source_url"], "canonical_url": item["source_url"],
                "archived_at": utc_now(), "text_file": str(text_path.relative_to(archive_root)),
                "html_file": "", "text_chars": len(body), "read_state": "normal", "attachments": [],
                "tags": ["science-news", item["area"]], "science_origin": origin}
            atomic_create_text(meta_path, json.dumps(metadata, ensure_ascii=False) + "\n")
        update_registry(archive_root / "registry.jsonl", metadata)
        return article_id

    return write(archive_root=Path(root))
