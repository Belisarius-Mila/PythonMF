"""Serialize edit/delete and preserve uncertainty across both native helpers."""
from contextlib import contextmanager
from app.calendar_agenda import read_json
from app.file_persistence import exclusive_file_lock


@contextmanager
def mutation_guard(root, *, operation, recover=False):
    with exclusive_file_lock(root/'calendar_mutation.lock',timeout=0):
        if not recover:
            if operation=='delete':
                state = read_json(root/'calendar_edits/state.json', {'items':{}})
                rows = state['items'].values()
            else:
                rows = (read_json(path,{}) for path in (root/'calendar_deletions').glob('*/state.json'))
            if any(row.get('state') in {'pending','unknown'} for row in rows):
                raise ValueError('Nejdřív ověř původní nedokončenou úpravu nebo smazání kalendáře.')
        yield
