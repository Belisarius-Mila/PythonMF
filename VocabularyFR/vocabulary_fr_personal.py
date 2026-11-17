"""Build private hard-word imports independently of A–D profiles.

The full inventory is implicit, so future cards remain available automatically.
This is a private browser-import contract, never a public card-data field.
"""
from __future__ import annotations

from vocabulary_fr_catalog import resolve_rows


def prepare_hard_backup(rows, catalog):
    """Preserve source HT by permanent meaning UID, including omitted aliases.

    No browser state is changed here. The client must validate the import,
    show its effect and save it only after the user's explicit confirmation.
    """
    entries, hints = resolve_rows(rows, catalog)
    return {
        'schema': 1,
        'kind': 'vocabulary-fr.personal-hard-backup',
        'language': 'fr',
        'hard': sorted(entry['uid'] for entry in entries if hints[entry['uid']]['hard']),
    }
