"""Separate signed create-only EventKit helper, with read-only uncertain recovery."""
from __future__ import annotations

from datetime import datetime
import json
import time
from uuid import uuid4

from app.calendar_access_pilot import CalendarAccessPilot, CalendarPilotError, PROJECT, DEFAULT_ROOT


class CalendarWriter(CalendarAccessPilot):
    source = PROJECT / 'scripts/calendar_writer.swift'
    bundle_id = 'com.samantha.calendar-writer'
    binary_name = 'CalendarWriter'
    app_name = 'SamanthaCalendarWriter.app'
    display_name = 'Samantha Calendar Writer'
    usage = 'Samantha zapíše pouze tebou potvrzenou novou událost s upozorněními a ověří její uložení.'
    self_test_checks = 6

    def __init__(self, root=DEFAULT_ROOT.with_name('SamanthaCalendarWriter'), **kwargs):
        super().__init__(root, **kwargs)

    def check_build(self):
        try: self._build_info()
        except (OSError, ValueError, CalendarPilotError) as exc:
            raise ValueError('Nejdřív povol zápis na Macu.') from exc

    def execute_event(self, event, *, recover=False, confirmed=False):
        if confirmed is not True:
            raise CalendarPilotError('Zápis vyžaduje potvrzení konkrétní události.')
        _, _, binary = self._build_info()
        request_id = str(uuid4())
        directory = self._safe(self.root / 'requests' / request_id)
        directory.mkdir(parents=True, mode=0o700)
        operation = 'recover' if recover else 'create'
        request = directory / 'request.json'
        self._write(request, {'schema': 1, 'operation': operation, 'request_id': request_id, 'event': event})
        label = 'com.samantha.calendar-writer.' + request_id
        self._run(['/bin/launchctl', 'submit', '-l', label, '-o', directory/'stdout.log',
                   '-e', directory/'stderr.log', '--', binary, request])
        # Never re-submit a timed-out process. Recovery is a separate read-only operation.
        response = self._safe(directory / 'response.json')
        deadline = time.monotonic() + 25
        while not response.exists() and time.monotonic() < deadline:
            time.sleep(.2)
        if not response.exists():
            raise CalendarPilotError('Výsledek zápisu není potvrzený; ověř pouze původní zápis.')
        if response.stat().st_size > 64000:
            raise CalendarPilotError('Neplatný výsledek zápisu.')
        result = json.loads(response.read_text())
        self._run(['/bin/launchctl', 'remove', label])
        if (result.get('schema') != 1 or result.get('operation') != operation or result.get('request_id') != request_id
                or result.get('bundle_identifier') != self.bundle_id or result.get('parent_pid') != 1
                or result.get('operation_id') != event['operation_id'] or result.get('expected') != event
                or type(result.get('calendar_writes')) is not bool
                or result.get('status') not in {'saved_verified', 'write_unknown', 'authorization_required', 'calendar_unavailable'}
                or (recover and result['calendar_writes'])):
            raise CalendarPilotError('Výsledek neodpovídá potvrzené události nebo servisnímu kontextu.')
        if ((result['status'] in {'authorization_required', 'calendar_unavailable'} and result['calendar_writes'])
                or (result['status'] == 'saved_verified' and result.get('authorization') != 'full_access')):
            raise CalendarPilotError('Výsledek nedokládá bezpečný stav kalendáře.')
        if result['status'] == 'saved_verified':
            actual = result.get('event', {})
            for key in ('calendar_id', 'title', 'time_zone', 'all_day', 'location', 'join_url'):
                if actual.get(key) != event[key]: raise CalendarPilotError('Zapsané údaje neodpovídají návrhu.')
            for key in ('start', 'end'):
                if datetime.fromisoformat(actual[key].replace('Z', '+00:00')) != datetime.fromisoformat(event[key]):
                    raise CalendarPilotError('Zapsaný čas neodpovídá návrhu.')
            if (not isinstance(actual.get('event_id'), str) or not actual['event_id']
                    or actual.get('marker') != 'Samantha event: ' + event['operation_id']
                    or sorted(actual.get('reminders', [])) != sorted(event['reminders'])):
                raise CalendarPilotError('Uložení nebo upozornění nebyla ověřena.')
        return result
