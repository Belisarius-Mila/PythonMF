"""One human click -> fresh check -> one durable create, never retry an uncertain save."""
from __future__ import annotations

import copy
from datetime import timedelta
from uuid import uuid4

from app.file_persistence import exclusive_file_lock
from .calendar_review import instant


class CalendarWrite:
    def __init__(self, service): self.service = service

    def execute(self, payload):
        service = self.service
        if (set(payload) != {'action', 'id', 'expected_revision', 'review_fingerprint', 'confirmed'}
                or payload['confirmed'] is not True or type(payload['expected_revision']) is not int
                or not isinstance(payload['review_fingerprint'], str)):
            raise ValueError('Potvrď konkrétní událost z aktuální karty.')
        service._card(payload['id'])
        with exclusive_file_lock(service.root / ('review-' + payload['id']), timeout=0):
            entry = service.repository.read()['items'].get(payload['id'], {})
            old_write = entry.get('write')
            if old_write and old_write['state'] == 'verified': return service.status(payload['id'])
            if old_write and old_write['state'] != 'blocked':
                # Read only. A restart/lost response cannot lead to another create.
                return self._perform(payload['id'], old_write, recover=True)
            entry = service.review._entry(payload['id'], payload['expected_revision'])
            if entry['job']['input']['manual_reason']:
                raise ValueError(entry['job']['input']['manual_reason'])
            preview = service.review._preview(entry)
            old = entry.get('review')
            service.review._store(payload['id'], payload['expected_revision'], preview)
            if (not old or payload['review_fingerprint'] != old['fingerprint']
                    or preview['fingerprint'] != old['fingerprint']):
                result = service.status(payload['id'])
                result['message'] = 'Údaje nebo kolize se změnily. Prohlédni kartu a potvrď zápis znovu.'
                return result
            normalized = preview['normalized']
            start = instant(normalized.get('deadline') or normalized['start'])
            end = start + timedelta(minutes=1) if 'deadline' in normalized else instant(normalized['end'])
            fields = preview['fields']
            service.writer.check_build()  # Missing build is a known preflight failure, not an uncertain save.
            event = {'operation_id': str(uuid4()), 'calendar_id': preview['target']['id'],
                     'title': fields['title'], 'start': start.isoformat(), 'end': end.isoformat(),
                     'time_zone': fields['time_zone'], 'all_day': fields['all_day'],
                     'location': fields['location'], 'join_url': fields['join_url'], 'reminders': preview['reminders']}
            write = {'state': 'pending', 'event': event, 'revision': payload['expected_revision'],
                     'review_fingerprint': preview['fingerprint'], 'created_at': service.clock().isoformat()}
            # Keep the configured destination stable through reservation and native write.
            with service.calendar._lock():
                service._card(payload['id'], entry['content_digest'])
                selection = service.calendar.snapshot()
                if (selection['revision'] != preview['selection_revision']
                        or selection['target_calendar_id'] != event['calendar_id']):
                    raise ValueError('Cílový kalendář se změnil; zkontroluj kartu znovu.')
                def reserve(document):
                    current = document['items'][payload['id']]
                    if (current['draft']['revision'] != write['revision']
                            or current['content_digest'] != entry['content_digest']
                            or current.get('write', {}).get('state', 'blocked') != 'blocked'):
                        raise ValueError('Návrh se změnil nebo už má evidovaný zápis.')
                    current['write'] = write
                service._mutate(reserve)
                return self._perform(payload['id'], write, recover=False)

    def _perform(self, item_id, write, *, recover):
        service = self.service
        result = None
        try:
            result = service.writer.execute_event(write['event'], recover=recover, confirmed=True)
            state = 'verified' if result['status'] == 'saved_verified' else (
                'blocked' if result['status'] in {'authorization_required', 'calendar_unavailable'} and not recover else 'unknown')
        except Exception:
            state = 'unknown'
        messages = {'verified': 'Zapsáno.', 'blocked': 'Povol zápis na Macu a ověř cílový kalendář. Událost nevznikla.',
                    'unknown': 'Výsledek zápisu není potvrzený. Obnov pouze původní zápis; další událost se nevytvoří.'}
        def finish(document):
            current = document['items'][item_id]['write']
            if current['event']['operation_id'] != write['event']['operation_id']:
                raise ValueError('Identita zápisu se změnila.')
            current.update(state=state, message=messages[state], checked_at=service.clock().isoformat())
            if result and state == 'verified': current['verified_event'] = copy.deepcopy(result['event'])
        service._mutate(finish)
        return service.status(item_id)
