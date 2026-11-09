"""Independent signed helper for editing exactly one existing occurrence."""
from __future__ import annotations
import json
import re
import time
from uuid import uuid4
from app.calendar_access_pilot import CalendarAccessPilot, CalendarPilotError, PROJECT, DEFAULT_ROOT
from app.calendar_delete import event_summary, ID

class CalendarEditHelper(CalendarAccessPilot):
    source = PROJECT / 'scripts/calendar_edit.swift'
    bundle_id = 'com.samantha.calendar-edit'
    binary_name = 'CalendarEdit'
    app_name = 'SamanthaCalendarEdit.app'
    display_name = 'Samantha Calendar Edit'
    usage = 'Samantha upraví pouze název a čas tebou potvrzené události bez účastníků.'
    self_test_checks = 7

    def __init__(self, root=DEFAULT_ROOT.with_name('SamanthaCalendarEdit'), **kwargs):
        super().__init__(root, **kwargs)

    def transact(self, operation, event, *, operation_id=None, identity=None, replacement=None):
        if operation not in {'inspect', 'update', 'recover_update'}:
            raise CalendarPilotError('Neplatná editační operace.')
        event_summary(event)
        if operation != 'inspect' and (not isinstance(operation_id, str) or not ID.fullmatch(operation_id) or not isinstance(identity, dict)):
            raise CalendarPilotError('Chybí přesná identita úpravy.')
        if operation!='inspect': event_summary(replacement)
        _, _, binary = self._build_info()
        request_id = str(uuid4()); directory = self._safe(self.root/'requests'/request_id)
        directory.mkdir(parents=True, mode=0o700)
        request = {'schema':1, 'operation':operation, 'request_id':request_id, 'event':event,
                   'operation_id':operation_id or '', 'identity':identity or {}, 'replacement':replacement or {}}
        path = directory/'request.json'; self._write(path, request)
        label = 'com.samantha.calendar-edit.'+request_id
        self._run(['/bin/launchctl','submit','-l',label,'-o',directory/'stdout.log','-e',directory/'stderr.log','--',binary,path])
        response = self._safe(directory/'response.json'); deadline = time.monotonic()+25
        while not response.exists() and time.monotonic() < deadline: time.sleep(.2)
        if not response.exists(): raise CalendarPilotError('Výsledek není potvrzený. Ověř pouze původní úpravy.')
        if response.stat().st_size > 16000: raise CalendarPilotError('Neplatná editační účtenka.')
        result = json.loads(response.read_text()); self._run(['/bin/launchctl','remove',label])
        if (result.get('schema') != 1 or result.get('operation') != operation or result.get('request_id') != request_id
                or result.get('parent_pid') != 1 or result.get('bundle_identifier') != self.bundle_id
                or result.get('replacement') != (replacement or {})
                or result.get('expected') != event or result.get('operation_id') != request['operation_id']
                or type(result.get('calendar_writes')) is not bool
                or result.get('status') not in {'preview','edited_verified','edit_unknown','changed','unsupported','calendar_unavailable','authorization_required'}
                or (operation != 'update' and result['calendar_writes'])
                or (result['status'] in {'changed','unsupported','calendar_unavailable','authorization_required'} and result['calendar_writes'])
                or (operation=='inspect' and result['status']=='edited_verified')
                or (operation!='inspect' and result['status']=='preview')
                or (result.get('status') in {'preview','edited_verified'} and result.get('authorization') != 'full_access')
                or (operation != 'inspect' and result.get('identity') != identity)):
            raise CalendarPilotError('Editační účtenka neodpovídá potvrzené události.')
        if result['status'] == 'preview':
            native = result.get('identity', {})
            if (set(native) != {'event_id','item_id','fingerprint','recurring'}
                    or any(not isinstance(native.get(k),str) or not 0 < len(native[k]) <= 1024 for k in ('event_id','item_id'))
                    or not re.fullmatch('[a-f0-9]{64}',native.get('fingerprint','')) or type(native.get('recurring')) is not bool):
                raise CalendarPilotError('Událost nemá ověřenou identitu.')
        if result['status']=='edited_verified' and result.get('event')!=replacement:
            raise CalendarPilotError('Upravená událost neodpovídá potvrzení.')
        return result
