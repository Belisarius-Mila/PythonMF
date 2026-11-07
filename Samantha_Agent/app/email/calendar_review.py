"""Fresh calendar conflict previews and revocable human approval; no event writes."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta
import hashlib
import json
from uuid import uuid4
from zoneinfo import ZoneInfo
from app.file_persistence import exclusive_file_lock

from .calendar_proposal import derive_fields, validate_fields, validate_reminders


def instant(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None: raise ValueError('Kontrola nemá časové pásmo.')
    return result


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class CalendarReview:
    def __init__(self, service):
        self.service = service

    def status(self, entry):
        if not entry or not entry.get('review'): return {'review': None, 'confirmation': None}
        review = copy.deepcopy(entry['review'])
        valid = (not review.get('invalidated') and review['revision'] == entry['draft']['revision']
                 and instant(review['expires_at']) > self.service.clock())
        selection = self.service.calendar.snapshot()
        valid = bool(valid and selection['revision'] == review['selection_revision']
                     and selection['target_calendar_id'] == review['target']['id']
                     and sorted(selection['read_calendar_ids']) == sorted(row['id'] for row in review['read_calendars']))
        review['valid'] = valid
        confirmation = copy.deepcopy(entry.get('confirmation')) if valid else None
        return {'review': review, 'confirmation': confirmation}

    def _entry(self, item_id, revision):
        card = self.service._card(item_id)
        entry = self.service.repository.read()['items'].get(item_id)
        if (not entry or not entry.get('draft') or entry['content_digest'] != card['content_digest']
                or entry['draft']['revision'] != revision):
            raise ValueError('Návrh nebo zdroj se změnil. Ulož aktuální návrh a zkontroluj jej znovu.')
        return entry

    def _preview(self, entry):
        draft = entry['draft']
        fields, _ = derive_fields(draft['fields'])
        issues, normalized = validate_fields(fields)
        if issues: raise ValueError('Před kontrolou doplň návrh: ' + ' '.join(issues))
        if not normalized:
            raise ValueError('Pro kontrolu termínu a upozornění doplň konkrétní čas termínu.')
        point = normalized.get('deadline')
        start = instant(point or normalized['start'])
        end = start + timedelta(seconds=1) if point else instant(normalized['end'])
        # Native read accepts a bounded interval and returns only selected calendars.
        read = self.service.calendar.review_interval(start, end, confirmed=True)
        names = {row['id']: row['title'] for row in read['read_calendars']}
        conflicts = []
        for event in read['events']:
            a, b = instant(event['start']), instant(event['end'])
            overlap = a <= start < b if point else a < end and b > start
            if overlap:
                conflicts.append({key: event[key] for key in ('calendar_id', 'title', 'start', 'end', 'all_day')}
                                 | {'calendar_title': names[event['calendar_id']]})
        conflicts.sort(key=lambda row: (row['start'], row['end'], row['calendar_id'], row['title']))
        reminders = validate_reminders(draft.get('reminders', [1440, 60]))
        zone = ZoneInfo(fields['time_zone'])
        capsule = {'revision': draft['revision'], 'source_digest': entry['content_digest'], 'fields': fields,
                   'normalized': normalized, 'reminders': reminders,
                   'alerts': [{'minutes_before': minutes, 'at': (start-timedelta(minutes=minutes)).astimezone(zone).isoformat(),
                               'past': start-timedelta(minutes=minutes) < self.service.clock()}
                              for minutes in reminders],
                   'warnings': draft['issues'], 'selection_revision': read['selection_revision'],
                   'target': read['target'], 'read_calendars': sorted(read['read_calendars'], key=lambda row: row['id']),
                   'conflicts': conflicts, 'deadline_is_point': bool(point)}
        return {**capsule, 'fingerprint': fingerprint(capsule), 'review_id': uuid4().hex,
                'observed_at': read['observed_at'], 'expires_at': (self.service.clock()+timedelta(minutes=5)).isoformat(),
                'calendar_writes': False}

    def _store(self, item_id, revision, preview, *, original_review=None, confirmation=None):
        self.service._card(item_id, preview['source_digest'])
        def save(document):
            entry = document['items'][item_id]
            if (entry['content_digest'] != preview['source_digest'] or entry['draft']['revision'] != revision
                    or (original_review is not None and entry.get('review', {}).get('review_id') != original_review)):
                raise ValueError('Návrh nebo kontrola se během čtení změnily; ověř aktuální stav.')
            selection = self.service.calendar.snapshot()
            if (selection['revision'] != preview['selection_revision']
                    or selection['target_calendar_id'] != preview['target']['id']
                    or sorted(selection['read_calendar_ids']) != sorted(row['id'] for row in preview['read_calendars'])):
                raise ValueError('Výběr kalendářů se během kontroly změnil. Zkontroluj návrh znovu.')
            entry['review'] = preview
            entry['confirmation'] = confirmation
        self.service._mutate(save)

    def execute(self, payload):
        self.service._card(payload.get('id'))
        with exclusive_file_lock(self.service.root/('review-'+payload['id']), timeout=0):
            return self._execute(payload)

    def _execute(self, payload):
        common = {'action', 'id', 'expected_revision'}
        confirming = payload['action'] == 'confirm'
        expected = common | ({'review_id', 'acknowledged', 'accept_conflicts'} if confirming else {'confirmed'})
        if set(payload) != expected or type(payload.get('expected_revision')) is not int:
            raise ValueError('Kontrola vyžaduje přesný návrh a jeho revizi.')
        if confirming:
            if (payload['acknowledged'] is not True or type(payload['accept_conflicts']) is not bool
                    or not isinstance(payload['review_id'], str)):
                raise ValueError('Potvrď kontrolu údajů, citací a nejasností.')
        elif payload['confirmed'] is not True:
            raise ValueError('Čtení kalendářů vyžaduje výslovný pokyn.')
        item_id, revision = payload['id'], payload['expected_revision']
        entry = self._entry(item_id, revision)
        old = entry.get('review')
        if confirming:
            state = self.status(entry)
            if not old or not state['review']['valid'] or old['review_id'] != payload['review_id']:
                raise ValueError('Náhled není aktuální. Zkontroluj kolize a zobraz náhled znovu.')
            if old['conflicts'] and not payload['accept_conflicts']:
                raise ValueError('Potvrď také přijetí zobrazených kolizí.')
        try:
            preview = self._preview(entry)  # Re-read even when an old preview was recently clear.
        except Exception:
            def invalidate(document):
                current = document['items'].get(item_id, {})
                if (current.get('draft', {}).get('revision') == revision and old
                        and current.get('review', {}).get('review_id') == old['review_id']):
                    current['review']['invalidated'] = True
                    current['confirmation'] = None
            self.service._mutate(invalidate)
            raise
        changed = bool(confirming and (preview['fingerprint'] != old['fingerprint']
                                      or instant(old['expires_at']) <= self.service.clock()))
        confirmation = None
        if confirming and not changed:
            confirmation = {'fingerprint': preview['fingerprint'], 'review_id': preview['review_id'],
                            'confirmed_at': self.service.clock().isoformat(), 'expires_at': preview['expires_at'],
                            'accepted_conflicts': payload['accept_conflicts'], 'calendar_writes': False}
        self._store(item_id, revision, preview, original_review=old['review_id'] if confirming else None,
                    confirmation=confirmation)
        result = self.service.status(item_id)
        if changed:
            result['message'] = 'Náhled vypršel nebo se kolize či cílový kalendář změnily. Prohlédni nový náhled a potvrď jej znovu.'
        return result
