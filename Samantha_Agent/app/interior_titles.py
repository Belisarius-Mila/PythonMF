"""Names for new proposals only; existing variants and media stay untouched."""
from __future__ import annotations

import re
import unicodedata

from app.interior_atelier import AtelierError, _text

TITLE_PROTOCOL = 'interior-title-v1'


def proposal_title(value, *, required=False):
    if not isinstance(value, str):
        raise AtelierError('Název návrhu musí být text.')
    return _text(' '.join(value.split()), 120, required=required)


def fallback_title(room, changes):
    """A reviewable local fallback when no named architect brief exists yet."""
    room_name = room['title'].strip() or 'Místnost'
    detail = ' '.join(changes.split()).strip()
    if not detail:
        return (room_name + ' – návrh')[:120]
    detail = re.split(r'[.!?\n]', detail, maxsplit=1)[0].strip() or detail
    prefix = room_name[:60] + ' – '
    return (prefix + detail[:120-len(prefix)]).rstrip()


def unique_proposal_title(room, value):
    title = proposal_title(value, required=True)
    key = lambda text: unicodedata.normalize('NFKC', ' '.join(text.split())).casefold()
    used = {key(v['title']) for v in room['variants'].values()}
    if key(title) not in used:
        return title
    stem = re.sub(r' · [0-9]+$', '', title)
    number = 2
    while True:
        suffix = f' · {number}'
        candidate = stem[:120-len(suffix)].rstrip() + suffix
        if key(candidate) not in used:
            return candidate
        number += 1
