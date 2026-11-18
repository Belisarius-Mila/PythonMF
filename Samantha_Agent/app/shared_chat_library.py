"""Read-only library retrieval for the paired operating conversation.

The server owns the archive root. Neither the model nor a browser supplies paths.
Retrieval enriches the original turn; it never starts another model request.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import threading
import unicodedata
from urllib.parse import urlsplit

from app.article_archive import DEFAULT_ARCHIVE_ROOT, article_item_from_raw, resolve_archive_relative_file

ITEM_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,180}')
MAX_RESULTS = 12
PAGE_CHARS = 20000
CONTEXT_CHARS = 120000
STOP = set('a aby aj ale ano asi az bez bych bys co do doporuc doporucit hledam hledej i jak jaka jake jakou je jen jeste jeho ji jim kde ke knihu knihy knih knihovne knihovny knihovna ktera ktere ktery ma mam mame me mi moje mu na nase nasi nas neco nebo nejake o od otevri prosim pro recept receptu recepty se si s ten tento toho tu ty u ulozene ulozeno ulozeneho ulozenych v ve vlastni vse vsech z za ze zobraz ukaz prvni druhy druha treti ctvrty paty posledni tom teto'.split())


def fold(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(text).casefold()) if not unicodedata.combining(c))


def terms(text):
    return list(dict.fromkeys(w[:5] if len(w) > 5 else w for w in re.findall(r'[a-z0-9]+', fold(text)) if w not in STOP and len(w) > 1))[:20]


def categories(text):
    value = fold(text)
    groups = [('books', r'\b(?:knih(?:a|y|u|ou|ach|ami|am)?|knize|knizni)\b'), ('recipes', r'\brecept\w*'),
              ('travel_places', r'\b(?:mist\w*|cestov\w*|vylet\w*|jedeme|pojedeme)'),
              ('science', r'\b(?:vedeck\w*|studii|studie)')]
    return [category for category, pattern in groups if re.search(pattern, value)]


def safe_url(value):
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in ('http', 'https') and parsed.hostname and not parsed.username and not parsed.password and not any(ord(c) < 32 for c in value) else ''
    except ValueError:
        return ''


class LibraryReader:
    def __init__(self, archive_root=DEFAULT_ARCHIVE_ROOT):
        self.root = Path(archive_root)
        self.lock = threading.RLock()
        self.signature = None
        self.records = []

    def _records(self):
        registry = self.root / 'registry.jsonl'
        if not registry.exists():
            if self.root.exists() and not self.root.is_dir():
                raise ValueError('Knihovnu nelze načíst.')
            return []
        if registry.is_symlink() or registry.stat().st_size > 16000000:
            raise ValueError('Katalog knihovny nelze ověřit.')
        raw = registry.read_text(encoding='utf-8')
        entries = [json.loads(line) for line in raw.splitlines() if line.strip()]
        if any(not isinstance(entry, dict) for entry in entries):
            raise ValueError('Katalog knihovny nelze ověřit.')
        paths = []
        ids = set()
        for entry in entries:
            item = article_item_from_raw(entry)
            if not ITEM_ID.fullmatch(item.id) or item.id in ids:
                raise ValueError('Identitu položek knihovny nelze ověřit.')
            ids.add(item.id)
            path = resolve_archive_relative_file(self.root, item.text_file)
            if path is None:
                # A missing file is honest unavailable content; an escaping path is rejected.
                relative = Path(item.text_file)
                if relative.is_absolute() or '..' in relative.parts or not item.text_file:
                    raise ValueError('Soubor položky není v knihovně.')
                candidate = (self.root / relative).resolve()
                if not candidate.is_relative_to(self.root.resolve()):
                    raise ValueError('Soubor položky není v knihovně.')
            elif not path.is_file() or path.stat().st_size > 4000000:
                raise ValueError('Text položky nelze načíst.')
            paths.append((item, path))
        signature = (hashlib.sha256(raw.encode()).hexdigest(), tuple(
            (item.id, str(path), path.stat().st_mtime_ns, path.stat().st_size) if path else (item.id, '')
            for item, path in paths))
        if signature == self.signature:
            return self.records
        records = []
        size = 0
        for item, path in paths:
            text = path.read_text(encoding='utf-8').strip() if path else ''
            size += len(text)
            if size > 64000000:
                raise ValueError('Knihovna překračuje kapacitu tohoto čtecího pilotu.')
            summary = item.to_summary()
            record = {k: summary.get(k, '') for k in ('id', 'title', 'category', 'category_label', 'book_author', 'book_location', 'book_publication_year')}
            record.update(source_url=safe_url(item.canonical_url or item.source_url),
                          text_available=path is not None, text_chars=len(text),
                          content_kind='Uložená anotace / poznámky ke knize' if item.category == 'books' else 'Uložený text',
                          preview=text[:300], image=None)
            if item.category == 'travel_places':
                record.update(visit_state=item.visit_state, visit_state_label=summary['visit_state_label'])
            image = next((a for a in item.attachments if a.mime_type.startswith('image/') and (a.thumb_file or a.readable_file or a.original_file)), None)
            if image:
                record['image'] = {'attachment_id': image.id, 'variant': 'thumb' if image.thumb_file else 'readable' if image.readable_file else 'original'}
            group_labels = [' '.join(str(g.get(k, '')) for k in ('code', 'label', 'subject')) for g in summary.get('book_groups', [])]
            metadata = ' '.join([item.title, item.book_author, item.book_location, *item.tags, *summary.get('book_subjects', []), *group_labels])
            records.append((record, text, fold(metadata), fold(text)))
        self.signature, self.records = signature, records
        return records

    def search(self, query, *, exclude_visited=False):
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            raise ValueError('Napiš hledanou knihu, článek, recept nebo místo (nejvýše 2000 znaků).')
        wanted, needles = categories(query), terms(query)
        # Category words and conversational commands are not content search terms.
        needles = [n for n in needles if n not in ('clane', 'clank', 'mist', 'misto', 'cesto', 'vedec', 'studi', 'kniha')]
        with self.lock:
            records = self._records()
            ranked = []
            for record, text, metadata, body in records:
                if exclude_visited and record.get('visit_state') == 'visited':
                    continue
                if wanted and record['category'] not in wanted:
                    continue
                score = sum(5 * metadata.count(n) + min(20, body.count(n)) for n in needles)
                if needles and not score:
                    continue
                ranked.append((score, record, text))
            ranked.sort(key=lambda row: -row[0])
            return {'query': query, 'catalog_count': len(records), 'count': len(ranked),
                    'items': [dict(row[1]) for row in ranked[:MAX_RESULTS]]}

    def detail(self, item_id, offset=0, digest=''):
        if not isinstance(item_id, str) or not ITEM_ID.fullmatch(item_id) or type(offset) is not int or offset < 0:
            raise ValueError('Neplatná položka nebo část textu.')
        with self.lock:
            record = next((r for r in self._records() if r[0]['id'] == item_id), None)
            if record is None:
                raise ValueError('Položka už v knihovně není.')
            item, text, _, _ = record
            sha = hashlib.sha256(text.encode()).hexdigest()
            if (offset and not digest) or (digest and digest != sha) or offset > len(text):
                raise ValueError('Text se změnil. Otevři položku znovu od začátku.')
            end = min(len(text), offset + PAGE_CHARS)
            return {'ok': True, 'item': dict(item), 'text': text[offset:end], 'offset': offset,
                    'next_offset': end, 'more': end < len(text), 'total_chars': len(text), 'sha256': sha}

    def set_visit_state(self, item_id, visit_state, expected_state):
        from app.article_archive import set_place_visit_state
        return set_place_visit_state(article_id=item_id, visit_state=visit_state,
                                     expected_state=expected_state, archive_root=self.root)

    def prepare(self, text, previous):
        value = fold(text)
        follow = bool(previous.get('items')) and bool(re.search(r'\b(?:otevri|ukaz|zobraz|tom|toho|autor\w*|anotac\w*|shrn\w*|vysvet\w*|pokrac\w*)\b', value))
        active = bool(categories(text) or re.search(r'\b(?:knihovn\w*|clan\w*|ulozen\w*|doporuc\w*|najdi|vyhledej|hledam)\b', value) or follow)
        if not active:
            return None
        opening = bool(re.match(r'\s*(?:prosim\s+)?(?:otevri|ukaz|zobraz)\b', value))
        references = previous.get('items', []) if follow else []
        ordinal = re.search(r'\b(prvni|druhy|druhou|druha|treti|ctvrty|paty|posledni|[1-9][0-9]?)\b', value)
        wanted = categories(text)
        candidates = [item for item in references if not wanted or item['category'] in wanted]
        selected = ''
        if opening and ordinal and references:
            word = ordinal.group(1)
            index = {'prvni': 0, 'druhy': 1, 'druhou': 1, 'druha': 1, 'treti': 2, 'ctvrty': 3, 'paty': 4, 'posledni': len(references)-1}.get(word, int(word)-1 if word.isdigit() else -1)
            if 0 <= index < len(references):
                if not wanted or references[index]['category'] in wanted:
                    selected = references[index]['id']
            result = {k: previous[k] for k in ('query', 'catalog_count', 'count', 'items')}
        elif follow and (not terms(text) or previous.get('selected_id') and not wanted and not opening):
            result = {k: previous[k] for k in ('query', 'catalog_count', 'count', 'items')}
            selected = previous.get('selected_id', '')
            if opening and len(candidates) == 1:
                selected = candidates[0]['id']
        else:
            recommend_places = bool(re.search(r'\b(?:doporuc\w*|tip\w*)\b', value) and 'travel_places' in wanted)
            result = self.search(text, exclude_visited=recommend_places)
            if opening and len(result['items']) == 1:
                selected = result['items'][0]['id']
        result.update(selected_id=selected, notice='')
        if opening and not selected:
            result['notice'] = 'Vyber konkrétní položku nebo její číslo; nejasný odkaz nic neotevřel.'
        context = []
        with self.lock:
            records = {r[0]['id']: r for r in self._records()}
            if selected and selected not in records:
                selected = ''
                result.update(selected_id='', notice='Položka už v knihovně není. Vyhledej ji znovu.')
            for number, item in enumerate(result['items'], 1):
                record = records.get(item['id'])
                if record is None:
                    continue
                stored = record[1]
                limit = CONTEXT_CHARS if selected == item['id'] else 3500
                context.append({**item, 'reference': number, 'text': stored[:limit],
                                'text_truncated': len(stored) > limit})
        result['model_context'] = {'catalog_count': result['catalog_count'], 'match_count': result['count'],
                                   'selected_id': selected, 'notice': result['notice'], 'sources': context}
        return result


READER = LibraryReader()
