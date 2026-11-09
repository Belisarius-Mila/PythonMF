"""Journalled edit of one existing event; uncertain results permit read-back only."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
import re
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.calendar_agenda import event_key, read_json, save_locked
from app.calendar_delete import event_summary, ID
from app.calendar_edit_helper import CalendarEditHelper
from app.calendar_access_pilot import CalendarPilotError
from app.calendar_overview import CalendarOverview, instant
from app.email.calendar_proposal import resolve_local
from app.file_persistence import exclusive_file_lock

PROJECT = Path(__file__).resolve().parents[1]
PRAGUE = ZoneInfo('Europe/Prague')


class CalendarEditing:
    def __init__(self, root=PROJECT/'data/private/calendar_edits', *, calendar=None, helper=None, clock=None, on_saved=None):
        self.root = Path(root).absolute()
        self.path = self.root/'state.json'
        self.calendar = calendar or CalendarOverview()
        self.helper = helper or CalendarEditHelper()
        self.clock = clock or (lambda:datetime.now(timezone.utc))
        self.on_saved = on_saved or (lambda before, after:None)

    def _read(self):
        for path in (self.root,self.path,self.path.with_name('state.json.lock')):
            if path.is_symlink() or path.resolve()!=path: raise ValueError('Soukromé úpravy nyní nejsou dostupné.')
        value = read_json(self.path, {'schema':1,'items':{}})
        if (not isinstance(value,dict) or value.get('schema')!=1 or not isinstance(value.get('items'),dict)
                or any(not ID.fullmatch(k) or r.get('request_id')!=k for k,r in value['items'].items())):
            raise ValueError('Původní úpravu nelze bezpečně načíst.')
        return value

    def _scope(self, event):
        view = self.calendar.snapshot()
        allowed = set(view['read_calendar_ids']) | {view['target_calendar_id']}
        writable = {c['id'] for c in view['calendars'] if c['writable']}
        rows = [r for r in view['events'] if event_key(r)==event_key(event)]
        if not view['ready'] or event['calendar_id'] not in allowed & writable or len(rows)!=1:
            raise ValueError('Událost není v aktuálním vybraném přehledu nebo kalendář neumožňuje změny.')
        return view['revision']

    def _pending(self, data):
        return next((r for r in data['items'].values() if r['state'] in {'pending','unknown'}),None)

    def _view(self, row):
        if row is None: return {'ok':True,'state':'idle'}
        messages = {'prepared':'Uprav název, datum nebo čas a potvrď Uložit změny.',
                    'pending':'Výsledek není potvrzený. Ověř pouze původní úpravu.',
                    'unknown':'Výsledek není potvrzený. Ověř pouze původní úpravu.',
                    'verified':'Změny uloženy do původní události.',
                    'changed':'Událost nebo výběr se změnily. Obnov přehled.',
                    'blocked':'Úprava neproběhla. Obnov přehled nebo povol úpravy na Macu.'}
        return {'ok':True,'state':row['state'],'request_id':row['request_id'],
                'event':row.get('replacement',row['event']), 'original':row['event'], 'form':row['form'],
                'calendar_title':row['calendar_title'],'recurring':row['identity']['recurring'],
                'message':messages[row['state']]}

    def _replacement(self, row, values):
        if (not isinstance(values,dict) or set(values)!={'title','date','time'}
                or not isinstance(values['title'],str) or not values['title'].strip() or len(values['title'])>400
                or any(ord(c)<32 and c not in '\n\r\t' for c in values['title'])
                or not isinstance(values['date'],str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',values['date'])
                or not isinstance(values['time'],str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',values['time'])):
            raise ValueError('Vyplň název, platné datum a čas.')
        try: day = date.fromisoformat(values['date'])
        except ValueError as exc: raise ValueError('Vyber platné datum.') from exc
        source = row['event']
        if source['all_day']:
            try: zone = ZoneInfo(row['timezone'])
            except ZoneInfoNotFoundError:
                fixed = re.fullmatch(r'GMT([+-])(\d{2}):?(\d{2})',row['timezone'])
                if not fixed: raise ValueError('Časové pásmo této celodenní události nelze bezpečně upravit.')
                zone = timezone(timedelta(minutes=(int(fixed[2])*60+int(fixed[3]))*(1 if fixed[1]=='+' else -1)))
            length = (date.fromisoformat(row['end_day'])-date.fromisoformat(row['start_day'])).days
            if not 1<=length<=31: raise ValueError('Neplatné celodenní období.')
            start = datetime.combine(day,time(),zone)
            end = datetime.combine(day+timedelta(days=length),time(),zone)
        else:
            issues = []
            start = resolve_local(day,values['time'],PRAGUE,issues)
            if issues or start is None: raise ValueError('Čas při změně letního času neexistuje nebo je dvojznačný. Vyber jiný čas.')
            start = start.astimezone(timezone.utc)
            end = start+(instant(source['end'])-instant(source['start']))
        return event_summary({**source,'title':values['title'],'start':start.isoformat(),'end':end.isoformat()})

    def prepare(self, event):
        event = event_summary(event); revision = self._scope(event)
        pending = self._pending(self._read())
        if pending: return self._view(pending)
        try: self.helper._build_info()
        except (OSError,ValueError,CalendarPilotError):
            return {'ok':True,'state':'setup_required','message':'Nejdřív jednou povol úpravy kalendáře na Macu.'}
        result = self.helper.transact('inspect',event)
        if result['status']=='authorization_required':
            return {'ok':True,'state':'setup_required','message':'Povol úpravy kalendáře na Macu.'}
        if result['status']!='preview':
            raise ValueError('Událost se změnila, je nejednoznačná nebo má účastníky. Obnov přehled; případně použij aplikaci Kalendář.')
        start = instant(event['start']).astimezone(PRAGUE)
        row = {'request_id':uuid4().hex,'state':'prepared','event':event,'identity':result['identity'],
               'selection_revision':revision,'expires_at':(self.clock()+timedelta(minutes=10)).isoformat(),
               'calendar_title':result['calendar_title'],'timezone':result['timezone'],
               'start_day':result['start_day'],'end_day':result['end_day'],
               'form':{'title':event['title'],'date':result['start_day'] if event['all_day'] else start.date().isoformat(),
                       'time':'00:00' if event['all_day'] else start.strftime('%H:%M')}}
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        with exclusive_file_lock(self.path,timeout=0):
            data = self._read(); pending = self._pending(data)
            if pending: return self._view(pending)
            data['items'][row['request_id']] = row; save_locked(self.path,data)
        return self._view(row)

    def execute(self, payload):
        if isinstance(payload,dict) and payload.get('action') in {'prepare','update','recover'}:
            from app.calendar_mutation_guard import mutation_guard
            with mutation_guard(self.root.parent,operation='edit',recover=payload.get('action')=='recover'):
                return self._execute(payload)
        return self._execute(payload)

    def _execute(self, payload):
        if not isinstance(payload,dict): raise ValueError('Neplatná úprava kalendáře.')
        action = payload.get('action')
        if action=='current' and set(payload)=={'action'}: return self._view(self._pending(self._read()))
        if action=='prepare' and set(payload)=={'action','event'}: return self.prepare(payload['event'])
        if action=='authorize' and set(payload)=={'action','confirmed'} and payload['confirmed'] is True:
            self.helper.build(confirmed=True); self.helper.authorize_current(confirmed=True)
            return {'ok':True,'state':'setup','message':'Dokonči povolení na Macu a potom znovu zvol Editovat.'}
        keys = {'action','request_id'} | ({'confirmed'} if action in {'update','recover'} else set()) | ({'changes'} if action=='update' else set())
        if (action not in {'status','recover','update'} or set(payload)!=keys or not isinstance(payload.get('request_id'),str)
                or not ID.fullmatch(payload['request_id']) or (action!='status' and payload['confirmed'] is not True)):
            raise ValueError('Potvrď úpravu konkrétní události.')
        notify = False
        with exclusive_file_lock(self.path,timeout=0):
            data = self._read(); row = data['items'].get(payload['request_id'])
            if row is None: raise ValueError('Původní úprava nebyla nalezena.')
            if action=='status' or row['state'] in {'verified','changed','blocked'}: return self._view(row)
            if action=='update' and row['state']!='prepared': return self._view(row)
            if action=='recover' and row['state'] not in {'pending','unknown'}: return self._view(row)
            if action=='update':
                pending = self._pending(data)
                if pending: return self._view(pending)
                try: replacement = self._replacement(row,payload['changes'])
                except ValueError as exc: return {**self._view(row),'validation_error':str(exc)}
                try: revision = self._scope(row['event'])
                except ValueError: revision = None
                if revision!=row['selection_revision'] or self.clock()>instant(row['expires_at']):
                    row['state']='changed';save_locked(self.path,data);return self._view(row)
                row.update(state='pending',replacement=replacement)
                save_locked(self.path,data)  # Durable original identity before any native update.
            try:
                result = self.helper.transact('update' if action=='update' else 'recover_update',row['event'],
                    operation_id=row['request_id'],identity=row['identity'],replacement=row['replacement'])
                if result['status']=='edited_verified': row['state']='verified';notify=True
                elif action=='update' and result['status'] in {'changed','unsupported','calendar_unavailable','authorization_required'}:
                    row['state']='changed' if result['status']=='changed' else 'blocked'
                else: row['state']='unknown'
            except Exception: row['state']='unknown'
            save_locked(self.path,data); view = self._view(row)
        if notify:
            try: self.on_saved(row['event'],row['replacement'])
            except Exception: pass  # A refresh/annotation failure can never trigger another native update.
        return view
