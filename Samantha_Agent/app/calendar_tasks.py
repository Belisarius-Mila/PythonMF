"""One explicit task form submission -> one journalled calendar event.

The existing signed writer owns all native validation and recovery. This layer
never changes its binary, asks for permissions, or sends text to a model.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.calendar_overview import CalendarOverview
from app.calendar_writer import CalendarWriter
from app.email.calendar_proposal import resolve_local
from app.file_persistence import (FileLockTimeoutError, exclusive_file_lock,
                                  atomic_replace_text_under_external_lock)

DEFAULT_ROOT = Path(__file__).resolve().parents[1] / 'data/private/calendar_tasks'
ZONE = ZoneInfo('Europe/Prague')
REQUEST_ID = re.compile(r'[a-f0-9]{32}')


class CalendarTasks:
    def __init__(self, root=DEFAULT_ROOT, *, calendar=None, writer=None, clock=None, on_saved=None):
        self.root = Path(root).absolute()
        self.calendar = calendar or CalendarOverview()
        self.writer = writer or CalendarWriter()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.on_saved = on_saved or (lambda: None)

    def context(self):
        view = self.calendar.snapshot()
        target = next((row for row in view['calendars']
                       if row['id'] == view['target_calendar_id'] and row['writable']), None)
        return {'ok': True, 'ready': bool(target), 'target': target,
                'selection_revision': view['revision'],
                'today': self.clock().astimezone(ZONE).date().isoformat(),
                'default_time': '09:00', 'time_zone': 'Europe/Prague', 'reminders': [1440, 60]}

    def _path(self, request_id, *, create=False):
        if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
            raise ValueError('Zadání nemá platnou identitu.')
        directory = self.root / request_id
        path = directory / 'state.json'
        for candidate in (self.root, directory, path, path.with_name('state.json.lock')):
            if candidate.is_symlink() or candidate.resolve() != candidate:
                raise ValueError('Soukromé zadání není dostupné.')
        if create:
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            directory.mkdir(exist_ok=True, mode=0o700)
        return path

    def _read(self, path):
        if not path.exists():
            return None
        if path.stat().st_size > 32000:
            raise ValueError('Soukromé zadání nelze načíst.')
        record = json.loads(path.read_text())
        if (record.get('schema') != 1 or record.get('request_id') != path.parent.name
                or record.get('write', {}).get('state') not in {'pending', 'unknown', 'blocked', 'verified'}):
            raise ValueError('Soukromé zadání nelze načíst.')
        return record

    def _save(self, path, record):
        # All callers hold the stable state.json sidecar lock.
        atomic_replace_text_under_external_lock(path, json.dumps(record, ensure_ascii=False, indent=2)+'\n')

    def _view(self, request_id, record):
        if not record:
            return {'ok': True, 'request_id': request_id, 'state': 'not_found',
                    'message': 'Zadání zatím není evidované. Lze znovu odeslat jen toto stejné zadání.'}
        values = record['input']
        return {'ok': True, 'request_id': request_id, 'state': record['write']['state'],
                'message': record['write'].get('message', 'Zápis se ověřuje…'),
                'task': {key: values[key] for key in ('title', 'date', 'time')},
                'calendar_title': (record.get('target') or {}).get('title', '')}

    def status(self, request_id):
        return self._view(request_id, self._read(self._path(request_id)))

    def _input(self, payload):
        expected = {'action', 'request_id', 'title', 'date', 'time', 'expected_selection_revision',
                    'expected_target_calendar_id', 'confirmed'}
        if (set(payload) != expected or payload.get('confirmed') is not True
                or type(payload.get('expected_selection_revision')) is not int
                or not isinstance(payload.get('expected_target_calendar_id'), str)
                or len(payload['expected_target_calendar_id']) > 512
                or not isinstance(payload.get('title'), str) or not payload['title'].strip() or len(payload['title']) > 400
                or any(ord(c) < 32 and c not in '\n\r\t' for c in payload['title'])
                or not isinstance(payload.get('date'), str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', payload['date'])
                or not isinstance(payload.get('time'), str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', payload['time'])):
            raise ValueError('Vyplň text úkolu, datum a čas a potvrď Zapsat úkol.')
        return {key: payload[key] for key in expected if key != 'action'}

    def _event(self, values, target, previous):
        try:
            day = date.fromisoformat(values['date'])
        except ValueError as error:
            raise ValueError('Zkontroluj den, měsíc a rok.') from error
        if day.year > self.clock().astimezone(ZONE).year + 10:
            raise ValueError('Vyber rok v příštích deseti letech.')
        issues = []
        start = resolve_local(day, values['time'], ZONE, issues)
        if issues:
            raise ValueError(issues[0])
        if start <= self.clock():
            raise ValueError('Zvolený termín už uplynul. Posuň datum nebo čas.')
        return {'operation_id': (previous or {}).get('operation_id') or str(uuid4()),
                'calendar_id': target['id'], 'title': values['title'].strip(),
                'start': start.isoformat(), 'end': (start+timedelta(minutes=1)).isoformat(),
                'time_zone': 'Europe/Prague', 'all_day': False,
                'location': '', 'join_url': '', 'reminders': [1440, 60]}

    def create(self, payload):
        return self._notify(self._create(payload))

    def _create(self, payload):
        values = self._input(payload)
        request_id = values['request_id']
        path = self._path(request_id, create=True)
        try:
            with exclusive_file_lock(path, timeout=0):
                old = self._read(path)
                if old and old['input'] != values:
                    raise ValueError('Toto zadání už má jiný obsah. Ověř jeho původní zápis.')
                if old and old['write']['state'] != 'blocked':
                    return self._view(request_id, old)
                record = old or {'schema': 1, 'request_id': request_id, 'input': values,
                                  'created_at': self.clock().isoformat(), 'target': None,
                                  'write': {'state': 'blocked'}}
                try:
                    selection_lock = self.calendar._lock(timeout=5)
                    selection_lock.__enter__()
                except FileLockTimeoutError:
                    record['write'] = {'state': 'blocked', 'message': 'Kalendář právě pracuje. Zkus zápis za chvíli.'}
                    self._save(path, record)
                    return self._view(request_id, record)
                try:
                    # Cached labels choose the configured ID; the signed writer
                    # checks actual existence/write access immediately before save.
                    try:
                        context = self.context()
                        if not context['ready']:
                            raise ValueError('Nejdřív vyber cílový kalendář v nastavení Kalendáře.')
                        if (context['selection_revision'] != values['expected_selection_revision']
                                or context['target']['id'] != values['expected_target_calendar_id']):
                            raise ValueError('Cílový kalendář se změnil. Prohlédni nový cíl a stiskni Zapsat úkol znovu.')
                        event = self._event(values, context['target'], record['write'].get('event'))
                        self.writer.check_build()
                    except ValueError as error:
                        record['write'] = {'state': 'blocked', 'message': str(error)}
                        self._save(path, record)
                        return self._view(request_id, record)
                    record['target'] = context['target']
                    record['write'] = {'state': 'pending', 'event': event, 'message': 'Zapisuji úkol…'}
                    self._save(path, record)  # Durable identity BEFORE any native action.
                    return self._perform(path, record, recover=False)
                finally:
                    selection_lock.__exit__(None, None, None)
        except FileLockTimeoutError:
            return self.status(request_id)

    def _perform(self, path, record, *, recover):
        event = record['write']['event']
        # One create at most. One subsequent read-only recovery handles EventKit's
        # occasionally delayed eventIdentifier; unresolved results stay frozen.
        for read_only in ([True] if recover else [False, True]):
            state, result = 'unknown', None
            try:
                result = self.writer.execute_event(event, recover=read_only, confirmed=True)
                if result['status'] == 'saved_verified':
                    state = 'verified'
                elif (not read_only and result['status'] in {'authorization_required', 'calendar_unavailable'}
                      and result.get('calendar_writes') is False):
                    state = 'blocked'
            except Exception:
                pass
            messages = {'verified': 'Zapsáno.', 'blocked': 'Úkol nevznikl. Ověř zápis a cílový kalendář na Macu.',
                        'unknown': 'Výsledek zatím není potvrzený. Ověř pouze tento původní zápis.'}
            record['write'].update(state=state, message=messages[state], checked_at=self.clock().isoformat())
            if state == 'verified':
                record['write']['verified_event'] = deepcopy(result['event'])
            self._save(path, record)
            if state != 'unknown':
                break
        result = self._view(record['request_id'], record)
        result['_refresh'] = record['write']['state'] == 'verified'
        return result

    def recover(self, request_id):
        return self._notify(self._recover(request_id))

    def _notify(self, result):
        # Run after both selection and receipt locks are released.
        if result.pop('_refresh', False):
            try:
                self.on_saved()
            except Exception:
                pass  # A dashboard refresh failure cannot undo or repeat a save.
        return result

    def _recover(self, request_id):
        path = self._path(request_id)
        if not path.exists():
            return self._view(request_id, None)
        try:
            with exclusive_file_lock(path, timeout=0):
                record = self._read(path)
                if record['write']['state'] in {'blocked', 'verified'}:
                    return self._view(request_id, record)
                return self._perform(path, record, recover=True)
        except FileLockTimeoutError:
            return self.status(request_id)

    def execute(self, payload):
        if not isinstance(payload, dict):
            raise ValueError('Neplatný požadavek.')
        action = payload.get('action')
        if action == 'create':
            return self.create(payload)
        if action == 'status' and set(payload) == {'action', 'request_id'}:
            return self.status(payload['request_id'])
        if action == 'recover' and set(payload) == {'action', 'request_id', 'confirmed'} and payload['confirmed'] is True:
            return self.recover(payload['request_id'])
        raise ValueError('Neplatný požadavek na úkol.')
