"""Bounded official RSS/Atom collection. No model and no arbitrary page scraping."""
from __future__ import annotations

import email.utils
import html
import re
import ssl
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from app.science_news import digest, public_url

# Explicit publishers, not URLs supplied by model output. Feed availability is
# reported per source; a failed feed is never silently substituted or called empty.
SOURCES = {
    "nature": "https://www.nature.com/nature.rss",
    "nature_evolution": "https://www.nature.com/natecolevol.rss",
    "nature_genetics": "https://www.nature.com/ng.rss",
    "nature_medicine": "https://www.nature.com/nm.rss",
    "nature_computational": "https://www.nature.com/natcomputsci.rss",
    "nasa": "https://www.nasa.gov/feed/",
    "nature_physics": "https://www.nature.com/nphys.rss",
    "nature_astronomy": "https://www.nature.com/natastron.rss",
}
HOSTS = {"www.nature.com", "www.nasa.gov", "home.cern", "www.nih.gov"}
MAX_BYTES = 2_000_000


class FeedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        from urllib.parse import urlsplit
        target = public_url(newurl)
        if urlsplit(target).hostname not in HOSTS:
            raise ValueError("Přesměrování mimo schválené zdroje.")
        return super().redirect_request(req, fp, code, msg, headers, target)


def fetch_feed(url):
    if url not in SOURCES.values():
        raise ValueError("Neznámý zdroj.")
    return fetch_public(url)


def fetch_public(url):
    from urllib.parse import urlsplit
    if urlsplit(public_url(url)).hostname not in HOSTS:
        raise ValueError("Zdroj není ve schváleném seznamu vydavatelů.")
    request = urllib.request.Request(url, headers={"User-Agent": "Samantha-ScienceNews/1.0 (weekly personal research)", "Accept": "application/rss+xml, application/atom+xml, application/xml"})
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    with urllib.request.build_opener(FeedRedirect(), urllib.request.HTTPSHandler(context=context)).open(request, timeout=20) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Zdroj překročil limit velikosti.")
    return data


def reusable_full_text(item, *, fetch=fetch_public):
    """Only explicit derivative-friendly page licences; model cannot grant one.

    No paywall/cookie bypass or automatic use of an abstract as full article.
    Editorial import can separately attach user-provided/reviewed source text.
    """
    from html.parser import HTMLParser
    from urllib.parse import urlsplit
    from app.article_archive import extract_article

    class LicenceParser(HTMLParser):
        licence = ""
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag != "link" or "license" not in attrs.get("rel", "").lower().split():
                return
            url = urlsplit(attrs.get("href", ""))
            if url.hostname not in ("creativecommons.org", "www.creativecommons.org"):
                return
            if re.fullmatch(r"/licenses/by/(?:3\.0|4\.0)/?", url.path): self.licence = "cc-by"
            if re.fullmatch(r"/licenses/by-sa/(?:3\.0|4\.0)/?", url.path): self.licence = "cc-by-sa"
            if re.fullmatch(r"/publicdomain/zero/1\.0/?", url.path): self.licence = "cc0"

    data = fetch(item["source_url"])
    if len(data) > MAX_BYTES:
        raise ValueError("Zdrojový text je příliš velký.")
    parser = LicenceParser()
    parser.feed(data.decode("utf-8", errors="replace"))
    if not parser.licence:
        raise ValueError("Plný text nemá ověřené oprávnění k překladu. Otevři zdroj nebo připrav oprávněný text pro import.")
    article = extract_article(data, item["source_url"])
    if not 200 <= len(article.text) <= 50_000:
        raise ValueError("Celou zprávu nelze v přijatelném rozsahu ověřit; nepoužiji místo ní abstrakt.")
    return article.text, parser.licence


def plain(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", value or ""))).strip()


def parse_feed(data, source_id):
    if len(data) > MAX_BYTES or re.search(br"<!\s*(DOCTYPE|ENTITY)", data, re.I):
        raise ValueError("Nepovolený nebo příliš velký XML zdroj.")
    root = ET.fromstring(data)
    if root.tag.split("}")[-1] not in ("rss", "RDF", "feed"):
        raise ValueError("Odpověď není RSS/Atom.")
    rows = []
    for entry in root.iter():
        if entry.tag.split("}")[-1] not in ("item", "entry"):
            continue
        fields = {}
        for child in entry:
            name = child.tag.split("}")[-1]
            value = "".join(child.itertext()).strip()
            if name == "link":
                if child.get("rel", "alternate") != "alternate":
                    continue
                value = child.get("href") or value
            fields.setdefault(name, value)
        url = public_url(fields.get("link", ""))
        raw_date = fields.get("published") or fields.get("pubDate") or fields.get("date") or fields.get("updated")
        try:
            when = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            when = email.utils.parsedate_to_datetime(raw_date)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        title = plain(fields.get("title"))[:400]
        abstract = plain(fields.get("description") or fields.get("summary") or fields.get("encoded") or fields.get("content"))[:3500]
        if not title:
            continue
        doi = fields.get("doi", "").strip()
        match = re.search(r"10\.\d{4,9}/[^\s<>\"?#]+", fields.get("doi", "") or url)
        if match:
            doi = match[0].rstrip(".,)")
        rows.append({"source_id": source_id, "source_url": url, "published_at": when.isoformat(),
            "title": title, "source_excerpt": abstract, "doi": doi,
            "candidate_id": "src_" + digest(doi.lower() or url)[:24]})
    return rows


def collect(now, *, fetch=fetch_feed, max_candidates=60):
    if now.tzinfo is None:
        raise ValueError("Čas sběru musí obsahovat časové pásmo.")
    found, health = {}, []
    for source_id, url in SOURCES.items():
        try:
            rows = parse_feed(fetch(url), source_id)
            current = [i for i in rows if now - timedelta(days=7) <= datetime.fromisoformat(i["published_at"]) <= now]
            for item in current:
                found.setdefault(item["candidate_id"], item)
            health.append({"source_id": source_id, "state": "ok", "entries": len(rows), "recent": len(current)})
        except (OSError, ValueError, TypeError, ET.ParseError, KeyError):
            health.append({"source_id": source_id, "state": "unavailable"})
    # Round-robin prevents prolific publishers excluding every other discipline.
    pools = {source: sorted((i for i in found.values() if i["source_id"] == source), key=lambda i: i["published_at"], reverse=True) for source in SOURCES}
    selected = []
    while len(selected) < max_candidates and any(pools.values()):
        for pool in pools.values():
            if pool and len(selected) < max_candidates:
                selected.append(pool.pop(0))
    return {"collected_at": now.isoformat(), "candidates": selected, "source_health": health,
            "complete": all(i["state"] == "ok" for i in health), "total_recent": len(found),
            "omitted_due_to_limit": max(0, len(found) - len(selected))}
