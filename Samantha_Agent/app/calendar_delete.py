"""Explicit single-occurrence deletion; separate helper, immutable preview, no retry."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import time
from uuid import uuid4

from app.calendar_access_pilot import CalendarAccessPilot, CalendarPilotError, PROJECT, DEFAULT_ROOT
from app.calendar_overview import CalendarOverview, instant
from app.file_persistence import exclusive_file_lock, atomic_replace_text_under_external_lock

EVENT_KEYS = {'calendar_id', 'title', 'start', 'end', 'all_day'}
ID = re.compile(r'[a-f0-9]{32}')


def event_summary(value):
    if not isinstance(value, dict) or set(value) != EVENT_KEYS:
        raise ValueError('Neplatná událost ke smazání.')
    for key, limit in [('calendar_id', 512), ('title', 400), ('start', 40), ('end', 40)]:
        s = value[key]
        if (not isinstance(s, str) or not s.strip() or len(s) > limit
                or any(ord(c) < 32 and not (key=='title' and c in '\t\r\n') for c in s)):
            raise ValueError('Neplatná událost ke smazání.')
    if type(value['all_day']) is not bool or not 0 < (instant(value['end'])-instant(value['start'])).total_seconds() <= 31*86400:
        raise ValueError('Neplatné období události.')
    return dict(value)


class CalendarDeleteHelper(CalendarAccessPilot):
    source = PROJECT / 'scripts/calendar_delete.swift'
    bundle_id = 'com.samantha.calendar-delete'
    binary_name = 'CalendarDelete'
    app_name = 'SamanthaCalendarDelete.app'
    display_name = 'Samantha Calendar Delete'
    usage = 'Samantha smaže pouze konkrétní tebou potvrzený výskyt události bez účastníků.'
    self_test_checks = 7

    def __init__(self, root=DEFAULT_ROOT.with_name('SamanthaCalendarDelete'), **kwargs):
        super().__init__(root, **kwargs)

    def transact(self, operation, event, *, operation_id=None, identity=None):
        if operation not in {'inspect', 'delete', 'recover_delete'}:
            raise CalendarPilotError('Neplatná mazací operace.')
        event_summary(event)
        if operation != 'inspect' and (not isinstance(operation_id, str) or not ID.fullmatch(operation_id) or not isinstance(identity, dict)):
            raise CalendarPilotError('Chybí přesná identita smazání.')
        _, _, binary = self._build_info()
        request_id = str(uuid4()); directory = self._safe(self.root/'requests'/request_id)
        directory.mkdir(parents=True, mode=0o700)
        request = {'schema':1, 'operation':operation, 'request_id':request_id, 'event':event,
                   'operation_id':operation_id or '', 'identity':identity or {}}
        path = directory/'request.json'; self._write(path, request)
        label = 'com.samantha.calendar-delete.'+request_id
        self._run(['/bin/launchctl','submit','-l',label,'-o',directory/'stdout.log','-e',directory/'stderr.log','--',binary,path])
        response = self._safe(directory/'response.json'); deadline = time.monotonic()+25
        while not response.exists() and time.monotonic() < deadline: time.sleep(.2)
        if not response.exists(): raise CalendarPilotError('Výsledek není potvrzený. Ověř pouze původní smazání.')
        if response.stat().st_size > 16000: raise CalendarPilotError('Neplatná mazací účtenka.')
        result = json.loads(response.read_text()); self._run(['/bin/launchctl','remove',label])
        if (result.get('schema') != 1 or result.get('operation') != operation or result.get('request_id') != request_id
                or result.get('parent_pid') != 1 or result.get('bundle_identifier') != self.bundle_id
                or result.get('expected') != event or result.get('operation_id') != request['operation_id']
                or type(result.get('calendar_writes')) is not bool
                or result.get('status') not in {'preview','deleted_verified','delete_unknown','changed','unsupported','calendar_unavailable','authorization_required'}
                or (operation != 'delete' and result['calendar_writes'])
                or (result['status'] in {'changed','unsupported','calendar_unavailable','authorization_required'} and result['calendar_writes'])
                or (operation=='inspect' and result['status']=='deleted_verified')
                or (operation!='inspect' and result['status']=='preview')
                or (result.get('status') in {'preview','deleted_verified'} and result.get('authorization') != 'full_access')
                or (operation != 'inspect' and result.get('identity') != identity)):
            raise CalendarPilotError('Mazací účtenka neodpovídá potvrzené události.')
        if result['status'] == 'preview':
            native = result.get('identity', {})
            if (set(native) != {'event_id','item_id','fingerprint','recurring'}
                    or any(not isinstance(native.get(k),str) or not 0 < len(native[k]) <= 1024 for k in ('event_id','item_id'))
                    or not re.fullmatch('[a-f0-9]{64}',native.get('fingerprint','')) or type(native.get('recurring')) is not bool):
                raise CalendarPilotError('Událost nemá ověřenou identitu.')
        return result


class CalendarDeletion:
    def __init__(self, root=PROJECT/'data/private/calendar_deletions', *, calendar=None, helper=None, clock=None, on_deleted=None):
        self.root = Path(root).absolute(); self.calendar = calendar or CalendarOverview()
        self.helper = helper or CalendarDeleteHelper()
        self.clock = clock or (lambda:datetime.now(timezone.utc)); self.on_deleted = on_deleted or (lambda:None)

    def _path(self, request_id, create=False):
        if not isinstance(request_id,str) or not ID.fullmatch(request_id): raise ValueError('Neplatná identita smazání.')
        directory = self.root/request_id; path = directory/'state.json'
        for p in (self.root,directory,path,path.with_name('state.json.lock')):
            if p.is_symlink() or p.resolve() != p: raise ValueError('Soukromé smazání není dostupné.')
        if create:
            self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
            directory.mkdir(exist_ok=True,mode=0o700)
        return path

    def _scope(self, event):
        view = self.calendar.snapshot()
        writable = {c['id'] for c in view['calendars'] if c['writable']}
        allowed = set(view['read_calendar_ids']) | {view['target_calendar_id']}
        if event['calendar_id'] not in writable & allowed:
            raise ValueError('Kalendář není vybraný nebo neumožňuje změny.')
        return view['revision']

    def _save(self, path, value):
        atomic_replace_text_under_external_lock(path,json.dumps(value,ensure_ascii=False)+'\n')

    def _read(self, path):
        if not path.is_file() or path.stat().st_size > 16000: raise ValueError('Původní smazání nelze načíst.')
        value = json.loads(path.read_text())
        if value.get('request_id') != path.parent.name or value.get('schema') != 1: raise ValueError('Neplatný záznam smazání.')
        return value

    def _view(self, value):
        messages = {'prepared':'Potvrď smazání této události.', 'pending':'Výsledek není potvrzený. Ověř pouze původní smazání.',
                    'unknown':'Výsledek není potvrzený. Ověř pouze původní smazání.', 'deleted':'Smazáno z kalendáře.',
                    'changed':'Událost nebo výběr se změnily. Obnov přehled.', 'blocked':'Smazání neproběhlo. Obnov přehled.'}
        return {'ok':True,'request_id':value['request_id'],'state':value['state'],'event':value['event'],
                'recurring':value['identity']['recurring'],'calendar_title':value['calendar_title'],
                'start_day':value.get('start_day'),
                'message':messages[value['state']]}

    def prepare(self, event):
        event = event_summary(event); revision = self._scope(event)
        try: self.helper._build_info()
        except (OSError,ValueError,CalendarPilotError):
            return {'ok':True,'state':'setup_required','message':'Nejdřív jednou povol mazání na Macu.'}
        result = self.helper.transact('inspect',event)
        status = result['status']
        if status == 'authorization_required': return {'ok':True,'state':'setup_required','message':'Povol mazání na Macu.'}
        if status != 'preview':
            raise ValueError('Událost se změnila, je nejednoznačná nebo jde o pozvánku s účastníky. Obnov přehled; případně použij aplikaci Kalendář.')
        request_id = uuid4().hex; path = self._path(request_id,True)
        view = self.calendar.snapshot()
        value = {'schema':1,'request_id':request_id,'state':'prepared','event':event,'identity':result['identity'],
                 'selection_revision':revision,'expires_at':(self.clock()+timedelta(minutes=5)).isoformat(),
                 'start_day':result.get('start_day'),
                 'calendar_title':result.get('calendar_title') or next((c['title'] for c in view['calendars'] if c['id']==event['calendar_id']),'Kalendář')}
        with exclusive_file_lock(path,timeout=0): self._save(path,value)
        return self._view(value)

    def execute(self, payload):
        if not isinstance(payload,dict): raise ValueError('Neplatná mazací akce.')
        action = payload.get('action')
        if action == 'prepare' and set(payload)=={'action','event'}: return self.prepare(payload['event'])
        if action == 'authorize' and set(payload)=={'action','confirmed'} and payload['confirmed'] is True:
            self.helper.build(confirmed=True)
            result = self.helper.authorize_current(confirmed=True)
            return {'ok':True,'state':'setup','message':'Dokonči povolení na Macu a potom znovu zvol Smazat z kalendáře.', 'authorization':result.get('authorization')}
        if (action not in {'delete','status','recover'} or set(payload) != ({'action','request_id'} if action=='status' else {'action','request_id','confirmed'})
                or (action!='status' and payload.get('confirmed') is not True)):
            raise ValueError('Smazání vyžaduje potvrzení konkrétní události.')
        path = self._path(payload['request_id']); notify=False
        if action=='status': return self._view(self._read(path))
        with exclusive_file_lock(path,timeout=0):
            value = self._read(path)
            if action=='status' or value['state'] in {'deleted','changed','blocked'}: return self._view(value)
            if action=='delete' and value['state']!='prepared': return self._view(value)
            if action=='recover' and value['state'] not in {'pending','unknown'}: return self._view(value)
            if action=='delete':
                try: current = self._scope(value['event'])
                except ValueError: current = None
                if current != value['selection_revision'] or self.clock() > instant(value['expires_at']):
                    value['state']='changed';self._save(path,value);return self._view(value)
                # Durable claim before any native mutation; a replay never calls delete.
                value['state']='pending';self._save(path,value)
            try:
                result = self.helper.transact('delete' if action=='delete' else 'recover_delete',value['event'],
                                              operation_id=value['request_id'],identity=value['identity'])
                if action=='recover':
                    # Loss of access during a read-only audit cannot prove that
                    # an earlier mutation did not happen or close its receipt.
                    value['state']='deleted' if result['status']=='deleted_verified' else 'unknown'
                else:
                    value['state']={'deleted_verified':'deleted','changed':'changed','calendar_unavailable':'blocked',
                                    'authorization_required':'blocked','unsupported':'blocked'}.get(result['status'],'unknown')
            except Exception:
                value['state']='unknown'
            notify=value['state']=='deleted';self._save(path,value);view=self._view(value)
        if notify:
            try: self.on_deleted()
            except Exception: pass  # A failed refresh cannot turn a known delete into a retry.
        return view
