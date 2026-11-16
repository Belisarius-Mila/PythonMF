"""Bounded official RSS/Atom collection. No model and no arbitrary page scraping."""
from __future__ import annotations

import email.utils
import html
import http.cookiejar
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


class NatureIdentityRedirect(FeedRedirect):
    """Public publisher cookie handshake, without login or persisted cookies."""
    max_redirections = 6

    def __init__(self, original):
        self.original = public_url(original)

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        from urllib.parse import parse_qs, urlsplit
        target = urlsplit(public_url(newurl))
        previous = urlsplit(req.full_url)
        if target.hostname == 'idp.nature.com':
            authorize = (previous.hostname == 'www.nature.com' and target.path == '/authorize'
                and parse_qs(target.query).get('redirect_uri') == [self.original]
                and parse_qs(target.query).get('response_type') == ['cookie'])
            transit = previous.hostname == 'idp.nature.com' and previous.path == '/authorize' and target.path == '/transit'
            if not (authorize or transit):
                raise ValueError('Nepovolené přesměrování vydavatele.')
            return urllib.request.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)
        if previous.hostname == 'idp.nature.com' and public_url(newurl) != self.original:
            raise ValueError('Vydavatel se nevrátil k původnímu veřejnému zdroji.')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


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
    handlers = [FeedRedirect(), urllib.request.HTTPSHandler(context=context)]
    if urlsplit(url).hostname == 'www.nature.com':
        handlers[0] = NatureIdentityRedirect(url)
        handlers.append(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    with urllib.request.build_opener(*handlers).open(request, timeout=20) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Zdroj překročil limit velikosti.")
    return data


class SourcePreparationError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def nature_article_text(data):
    """Read the full study body, including Methods, references and extended data."""
    from app.article_archive import ReadableTextParser

    class Body(ReadableTextParser):
        def __init__(self):
            super().__init__()
            self.body = 0
            self.excluded = 0
            self.finished = False
            self.sections = set()

        def handle_starttag(self, tag, attrs):
            values = dict(attrs)
            if tag == 'div' and 'c-article-body' in values.get('class', '').split() and not self.body:
                self.body = 1
                return
            if not self.body:
                return
            if tag == 'div':
                self.body += 1
            if self.finished:
                return
            if tag == 'section':
                title = values.get('data-title', '')
                if self.excluded:
                    self.excluded += 1
                elif title == 'References':
                    self.sections.add(title)
                elif title in ('Rights and permissions', 'About this article'):
                    self.finished = True
                elif title == 'Inline Recommendations' or values.get('aria-labelledby') == 'content-related-subjects':
                    self.excluded = 1
                else:
                    self.sections.add(title)
            if not self.excluded and not self.finished:
                super().handle_starttag(tag, attrs)

        def handle_endtag(self, tag):
            if not self.body:
                return
            if tag == 'div':
                self.body -= 1
            if self.excluded:
                if tag == 'section':
                    self.excluded -= 1
                return
            if not self.finished:
                super().handle_endtag(tag)

        def handle_data(self, value):
            if self.body and not self.excluded and not self.finished:
                super().handle_data(value)

    parser = Body()
    parser.feed(data.decode('utf-8', errors='replace'))
    if not {'Main', 'References'} <= parser.sections or not parser.finished:
        raise SourcePreparationError('source_incomplete', 'Úplné tělo studie se nepodařilo ověřit. Samotný abstrakt nepřeložím jako celou zprávu.')
    return parser.text()


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
            if tag not in ('link', 'a') or "license" not in attrs.get("rel", "").lower().split():
                return
            url = urlsplit(attrs.get("href", ""))
            if url.hostname not in ("creativecommons.org", "www.creativecommons.org"):
                return
            if re.fullmatch(r"/licenses/by/(?:3\.0|4\.0)/?", url.path): self.licence = "cc-by"
            if re.fullmatch(r"/licenses/by-sa/(?:3\.0|4\.0)/?", url.path): self.licence = "cc-by-sa"
            if re.fullmatch(r"/publicdomain/zero/1\.0/?", url.path): self.licence = "cc0"

    try:
        data = fetch(item["source_url"])
    except (OSError, ValueError) as error:
        raise SourcePreparationError('source_unavailable', 'Plný text se nepodařilo načíst od vydavatele. Překlad nebyl spuštěný ani účtovaný. Zkus jej později nebo otevři původní zprávu.') from error
    if len(data) > MAX_BYTES:
        raise ValueError("Zdrojový text je příliš velký.")
    parser = LicenceParser()
    parser.feed(data.decode("utf-8", errors="replace"))
    if not parser.licence:
        raise SourcePreparationError('permission_unverified', "Plný text nemá ověřené oprávnění k překladu. Otevři zdroj nebo připrav oprávněný text pro import.")
    is_nature_study = urlsplit(item['source_url']).hostname == 'www.nature.com' and urlsplit(item['source_url']).path.startswith('/articles/s')
    text = nature_article_text(data) if is_nature_study else extract_article(data, item['source_url']).text
    if len(text) > 300_000:
        raise SourcePreparationError('source_too_large', f'Úplná studie má {len(text):,} znaků a překračuje limit 300 000 znaků. Překlad nebyl spuštěný ani účtovaný. Text nezkracuji.')
    if len(text) < 200:
        raise SourcePreparationError('source_incomplete', "Celou zprávu nelze ověřit; nepoužiji místo ní abstrakt.")
    return text, parser.licence


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
