"""Thirty-day dashboard agenda, background reads and private display classifications."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import threading
from uuid import uuid4

from app.calendar_overview import CalendarOverview, instant
from app.email.continuous_agent import DEFAULT_ROOT as EMAIL_ROOT
from app.file_persistence import atomic_replace_text_under_external_lock, exclusive_file_lock, FileLockTimeoutError

PROJECT = Path(__file__).resolve().parents[1]
KINDS = {'meeting', 'task_deadline'}


def event_key(event):
    # A display annotation follows this exact content, never an unverified native ID.
    values = [event['calendar_id'], event['title'], instant(event['start']).astimezone(timezone.utc).isoformat(),
              instant(event['end']).astimezone(timezone.utc).isoformat(), event['all_day']]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()


def read_json(path, default=None):
    path = Path(path)
    if not path.exists(): return default
    if path.is_symlink() or path.stat().st_size > 32*1024*1024: raise ValueError('Neplatný soukromý přehled.')
    return json.loads(path.read_text())


def save_locked(path,value):
    """The caller already holds this file's stable transaction lock."""
    atomic_replace_text_under_external_lock(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')


class WrittenKinds:
    """Hints from verified Samantha receipts, matched only to unique exact content."""
    def __init__(self, email_path=EMAIL_ROOT/'calendar_drafts/state.json',
                 manual_root=PROJECT/'data/private/calendar_manual_requests'):
        self.email_path, self.manual_root = Path(email_path), Path(manual_root)

    def __call__(self):
        found = defaultdict(set); partial = False
        def add(write, kind):
            if kind in KINDS and write.get('state') == 'verified' and write.get('verified_event'):
                found[event_key(write['verified_event'])].add(kind)
        try:
            document = read_json(self.email_path, {'items':{}})
            for entry in document['items'].values():
                add(entry.get('write', {}), entry.get('draft', {}).get('fields', {}).get('kind'))
        except (OSError, ValueError, KeyError, TypeError, AttributeError): partial = True
        paths = sorted(self.manual_root.glob('*/write.json')) if self.manual_root.is_dir() else []
        if len(paths) > 2000: partial = True
        for path in paths[:2000]:
            try:
                proposal = read_json(path.with_name('proposal.json'), {})
                add(read_json(path, {}), proposal.get('fields', {}).get('kind'))
            except (OSError, ValueError, KeyError, TypeError, AttributeError): partial = True
        return {key:next(iter(kinds)) for key,kinds in found.items() if len(kinds)==1}, partial


class CalendarAgenda:
    def __init__(self, overview=None, *, clock=None, launcher=None, written_kinds=None, cooldown=60):
        self.overview = overview or CalendarOverview()
        self.clock = clock or self.overview.clock
        self.root = self.overview.pilot.root
        self.attempt_path = self.root/'agenda_refresh.json'
        self.labels_path = self.root/'agenda_types.json'
        self.written_kinds = written_kinds or WrittenKinds()
        self.launcher = launcher or (lambda fn:threading.Thread(target=fn, daemon=True, name='calendar-agenda-read').start())
        self.cooldown = cooldown
        self.guard = threading.Lock()
        self.running = False

    def _scope(self, selection):
        return hashlib.sha256(json.dumps([selection['revision'],sorted(selection['read_calendar_ids'])]).encode()).hexdigest()

    def _labels(self):
        value = read_json(self.labels_path, {'revision':0,'items':{}})
        if (not isinstance(value,dict) or type(value.get('revision')) is not int or not isinstance(value.get('items'),dict)
                or any(not isinstance(k,str) or len(k)!=64 or v not in KINDS for k,v in value['items'].items())):
            raise ValueError('Označení typů nyní nelze načíst.')
        return value

    def _attempt(self):
        try: return read_json(self.attempt_path, {})
        except (OSError,ValueError): return {}

    def snapshot(self):
        source = self.overview.snapshot(); now = self.clock(); end = now+timedelta(days=30)
        attempt = self._attempt(); scope = self._scope(source)
        same_attempt = attempt.get('scope') == scope
        age = (now-instant(attempt['started_at'])).total_seconds() if same_attempt and attempt.get('started_at') else None
        running = bool(same_attempt and attempt.get('state')=='running' and age is not None and 0 <= age < 90)
        last_failed = bool(same_attempt and attempt.get('state')=='failed' and
                           (not source['last_loaded_at'] or instant(attempt['completed_at']) >= instant(source['last_loaded_at'])))
        partial = False
        try: labels = self._labels()
        except (OSError,ValueError): labels={'revision':0,'items':{}};partial=True
        try: known, missing_types = self.written_kinds(); partial |= missing_types
        except (OSError,ValueError,KeyError,TypeError): known={};partial=True
        events = [row for row in source['events'] if instant(row['end'])>now and instant(row['start'])<end]
        counts = Counter(event_key(row) for row in events)
        deadlines, meetings = [], []
        for row in sorted(events,key=lambda e:(instant(e['start']),e['title'],e['calendar_id'])):
            key = event_key(row); unique = counts[key]==1
            manual = labels['items'].get(key) if unique else None
            suggested = known.get(key) if unique else None
            kind = manual or suggested or 'event'
            item = {**row,'key':key,'kind':kind,'type_source':'display' if manual else 'samantha' if suggested else 'calendar',
                    'display_kind':manual or 'auto','can_classify':unique and source['ready'] and not last_failed and not partial}
            (deadlines if kind=='task_deadline' else meetings).append(item)
        fresh = bool(source['ready'] and not last_failed)
        status = 'source_unavailable' if last_failed else source['status']
        return {'ok':True,'status':status,'fresh':fresh,'refreshing':running,'loaded_at':source['last_loaded_at'],
                'selection_revision':source['revision'],'labels_revision':labels['revision'],'selected_count':len(source['read_calendar_ids']),
                'classification_partial':partial,'deadlines':deadlines,'meetings':meetings,
                'start':now.isoformat(),'end':end.isoformat(),'calendar_writes':False}

    def request_refresh(self):
        with self.guard:
            selection = self.overview.snapshot()
            if self.running or not selection['read_calendar_ids']: return self.snapshot()
            self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
            try:
                with exclusive_file_lock(self.attempt_path,timeout=0):
                    previous = self._attempt(); now = self.clock(); scope = self._scope(selection)
                    age = (now-instant(previous['started_at'])).total_seconds() if previous.get('started_at') else None
                    if (age is not None and 0 <= age < 90 and previous.get('state')=='running') or (previous.get('scope')==scope and age is not None and 0 <= age < self.cooldown):
                        return self.snapshot()
                    attempt = {'id':uuid4().hex,'scope':scope,'started_at':now.isoformat(),'state':'running'}
                    save_locked(self.attempt_path,attempt)
            except FileLockTimeoutError: return self.snapshot()
            self.running = True
            try: self.launcher(lambda:self._refresh(attempt))
            except Exception:
                self.running = False; self._finish(attempt,False)
        return self.snapshot()

    def _finish(self, attempt, ready):
        with exclusive_file_lock(self.attempt_path,timeout=2):
            current = self._attempt()
            if current.get('id')==attempt['id']:
                save_locked(self.attempt_path,{**attempt,'state':'completed' if ready else 'failed',
                                  'completed_at':self.clock().isoformat()})

    def _refresh(self, attempt):
        ready = False
        try:
            result = self.overview.refresh(confirmed=True)
            ready = bool(result['ready'] and self._scope(result)==attempt['scope'])
        except Exception: pass
        finally:
            try: self._finish(attempt,ready)
            finally: self.running = False

    def set_kind(self, payload):
        expected = {'action','key','kind','expected_selection_revision','expected_labels_revision','confirmed'}
        if (set(payload)!=expected or payload['confirmed'] is not True or payload['kind'] not in KINDS|{'auto'}
                or type(payload['expected_selection_revision']) is not int or type(payload['expected_labels_revision']) is not int):
            raise ValueError('Označ typ aktuální události v přehledu.')
        with exclusive_file_lock(self.labels_path,timeout=0):
            view = self.snapshot(); labels = self._labels()
            rows = [row for row in view['deadlines']+view['meetings'] if row['key']==payload['key']]
            if (not view['fresh'] or len(rows)!=1 or not rows[0]['can_classify']
                    or view['selection_revision']!=payload['expected_selection_revision']
                    or labels['revision']!=payload['expected_labels_revision']):
                raise ValueError('Přehled se změnil nebo není aktuální. Obnov jej a označ typ znovu.')
            if payload['kind']=='auto': labels['items'].pop(payload['key'],None)
            else: labels['items'][payload['key']]=payload['kind']
            labels['revision']+=1
            save_locked(self.labels_path,labels)
        return self.snapshot()

    def execute(self,payload):
        if not isinstance(payload,dict): raise ValueError('Neplatný požadavek.')
        if payload=={'action':'refresh'}: return self.request_refresh()
        if payload.get('action')=='set_kind': return self.set_kind(payload)
        raise ValueError('Neznámá akce přehledu.')
