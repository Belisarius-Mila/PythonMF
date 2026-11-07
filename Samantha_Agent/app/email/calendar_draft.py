"""One selected email -> editable suggestion and explicitly confirmed calendar create."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from functools import partial
import hashlib
import json
from pathlib import Path
import re
import threading
from uuid import uuid4

from app.codex_appserver import CodexAppServerClient, UnixSocketAppServerTransport
from app.communication import agent_roles
from app.communication.local_runtime import DEFAULT_SOCKET_PATH
from app.file_persistence import exclusive_file_lock, atomic_write_json
from app.routine_tasks import start_data_only_thread
from app.work_repository import JsonWorkRepository, RepositoryMutation
from app.calendar_overview import CalendarOverview
from .continuous_agent import ContinuousEmailAgent
from .continuous_source import IMAPAgentSource
from .icloud_provider import _html_to_text
from .calendar_proposal import (Candidate, Claim, FIELD_NAMES, INSTRUCTIONS,
    derive_fields, simple_defaults, edit_simple, evidence_issues, materialize, strict_schema, validate_fields, validate_reminders)
from .calendar_review import CalendarReview
from .calendar_write import CalendarWrite
from app.calendar_writer import CalendarWriter

ID = re.compile(r'[0-9a-f]{64}')
REQUEST = re.compile(r'[A-Za-z0-9_-]{8,96}')
DISABLED_FEATURES=('image_generation','plugins','remote_plugin','view_image','sleep_tool','tool_suggest',
    'in_app_browser','browser_use','browser_use_external','browser_annotation_api','browser_use_full_cdp_access',
    'computer_use','search_tool','tool_search','request_permissions_tool','plugin_hooks','multi_agent_v2_dynamic_tools')


def now(): return datetime.now(timezone.utc).isoformat()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def source_context(observed):
    source = observed.source
    if not source.original_eml or len(source.original_eml) > 8*1024*1024:
        raise ValueError('Zdrojový e-mail chybí nebo překročil limit návrhového pilotu.')
    context = {'subject':source.subject, 'date':source.date, 'body':source.body_text, 'html':source.body_html}
    if sum(len(value.encode()) for value in context.values()) > 256000:
        raise ValueError('Text zprávy chybí nebo překročil limit; model nebyl spuštěn.')
    mime = BytesParser(policy=policy.default).parsebytes(source.original_eml)
    formal = any(part.get_content_type()=='text/calendar' or (part.get_filename() or '').lower().endswith('.ics') for part in mime.walk())
    recurring = bool(re.search(r'\b(každ[ýéou]\s+(pondělí|úterý|střed[au]|čtvrtek|pátek|sobot[au]|neděli|týden|měsíc)|every\s+(monday|tuesday|wednesday|thursday|friday|week|month)|RRULE\s*:)',source.body_text+' '+_html_to_text(source.body_html),re.I))
    context['manual_reason'] = 'Formální kalendářová pozvánka vyžaduje ruční zpracování.' if formal else 'Opakování vyžaduje ruční zpracování.' if recurring else ''
    if not context['manual_reason'] and not (source.body_text or source.body_html):
        raise ValueError('Text zprávy chybí; model nebyl spuštěn.')
    return context


class CalendarDraftDriver:
    def __init__(self, client_factory=None):
        self.client_factory = client_factory or partial(CodexAppServerClient, timeout=180,experimental_api=True,
            transport_factory=partial(UnixSocketAppServerTransport,socket_path=DEFAULT_SOCKET_PATH))

    def selection(self):
        agent_roles.load_role(role=agent_roles.EMAIL_ROLE)
        with self.client_factory() as client:
            selected=agent_roles.resolve_role(client.list_models(),role=agent_roles.EMAIL_ROLE)
        if selected.get('fallback'):raise ValueError('E-mailový model se nesmí automaticky změnit.')
        return selected

    def __call__(self, job, home, on_thread, before_send):
        selected=agent_roles.assert_current(job['selection'],role=agent_roles.EMAIL_ROLE)
        with self.client_factory() as client:
            current=agent_roles.resolve_role(client.list_models(),role=agent_roles.EMAIL_ROLE)
            if current.get('fallback') or any(current[key]!=selected[key] for key in ('role','model','reasoning_effort','policy_digest')):
                raise ValueError('Schválené nastavení e-mailového modelu se změnilo.')
            isolated=start_data_only_thread(client,home/'empty_context',selected['model'],INSTRUCTIONS,
                disabled_features=DISABLED_FEATURES,restrict_read_access=True)
            thread=isolated['thread_id'];on_thread(thread);before_send()
            receipt=client.send_text(thread_id=thread,text=json.dumps(job['input'],ensure_ascii=False),
                client_message_id='calendar-draft-'+job['id'],model=selected['model'],effort=selected['reasoning_effort'],
                approval_policy='never',permission_profile=isolated['permission_profile'],output_schema=strict_schema(),
                service_tier_for_turn='default')
        if not receipt.delivered or len(receipt.answer.encode()) > 128000:
            raise ValueError('Návrh nemá ověřenou konečnou odpověď.')
        return {'candidate':json.loads(receipt.answer),'receipt':receipt.as_dict()}


class CalendarDraftService:
    def __init__(self, worker=None, *, source_factory=IMAPAgentSource, driver=None, launcher=None, calendar=None, clock=None, writer=None):
        self.worker=worker or ContinuousEmailAgent()
        self.root=self.worker.root/'calendar_drafts'
        self.repository=JsonWorkRepository(self.root/'state.json',default={'items':{}})
        self.source_factory,self.driver=source_factory,driver or CalendarDraftDriver()
        self.launcher=launcher or self._launch
        self.nonce=uuid4().hex
        self.calendar=calendar or CalendarOverview()
        self.clock=clock or (lambda: datetime.now(timezone.utc))
        self.review=CalendarReview(self)
        self.writer=writer or CalendarWriter()
        self.write=CalendarWrite(self)

    @staticmethod
    def _launch(callback):
        threading.Thread(target=callback,daemon=True,name='calendar-email-proposal').start()

    def _card(self,item_id,expected=None):
        if not isinstance(item_id,str) or not ID.fullmatch(item_id): raise ValueError('Neplatná zpráva.')
        item=self.worker.status()['items'].get(item_id)
        if not item or item['status'] not in {'awaiting_confirmation','archived'}:
            raise ValueError('Vybraná zpráva není dostupná pro návrh.')
        if expected is not None and (not isinstance(expected,str) or not ID.fullmatch(expected) or item['content_digest']!=expected):
            raise ValueError('Zdroj zprávy se změnil; obnov kartu.')
        return item

    def _mutate(self,callback):
        def update(document):
            callback(document)
            return RepositoryMutation(document)
        return self.repository.transact(update)

    def status(self,item_id):
        card=self._card(item_id)
        entry=self.repository.read()['items'].get(item_id)
        if entry and entry['content_digest']!=card['content_digest']:
            raise ValueError('Uložený návrh patří jinému obsahu zprávy.')
        job=copy.deepcopy(entry['job']) if entry else None
        if job:
            if job['status'] in {'queued','running'} and job.get('nonce')!=self.nonce:
                job['status']='delivery_unknown'
            job={key:job.get(key) for key in ('status','request_id','message')}
        draft=copy.deepcopy(entry.get('draft')) if entry else None
        if draft: draft.setdefault('reminders', [1440, 60])  # Side-effect-free compatibility for existing concepts.
        return {'ok':True,'source':{'id':item_id,'subject':card['header']['subject'],'date':card['header']['date']},
            'model':entry['job'].get('selection',{}).get('model','') if entry else agent_roles.load_role(role=agent_roles.EMAIL_ROLE)['preferred_model'],
            'job':job,'draft':draft,**self.review.status(entry),
            'write':copy.deepcopy(entry.get('write')) if entry else None,
            'writer_built':(self.writer.root/'build.json').exists(),
            'calendar_writes':bool(entry and entry.get('write',{}).get('state')=='verified')}

    def prepare(self,payload):
        if (set(payload)!={'action','id','request_id','expected_content_digest','confirmed'} or payload.get('confirmed') is not True
                or not isinstance(payload.get('request_id'),str) or not REQUEST.fullmatch(payload['request_id'])):
            raise ValueError('Příprava vyžaduje explicitně vybranou zprávu a potvrzený požadavek.')
        item_id=payload['id'];card=self._card(item_id,payload['expected_content_digest'])
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        with exclusive_file_lock(self.root/('prepare-'+item_id),timeout=0):
            if item_id in self.repository.read()['items']:
                return self.status(item_id)  # One model attempt per exact source, even with a different request ID.
            observed=self.source_factory(card['provider'],card['folder']).read_item(card)
            if observed.item_id!=item_id or observed.content_digest!=card['content_digest']:
                raise ValueError('Původní zpráva neodpovídá kartě; model nebyl spuštěn.')
            context=source_context(observed)
            selection={} if context['manual_reason'] else self.driver.selection()  # Catalog only; no paid turn.
            job_id=digest([item_id,card['content_digest'],payload['request_id']])[:32]
            job={'id':job_id,'request_id':payload['request_id'],'status':'queued','nonce':self.nonce,
                 'created_at':now(),'selection':selection,'input':context,'send_started':False}
            self._card(item_id,card['content_digest'])
            def reserve(document):
                if item_id in document['items']: raise ValueError('Návrh již má evidovaný pokus.')
                document['items'][item_id]={'content_digest':card['content_digest'],'job':job}
            self._mutate(reserve)
            try: self.launcher(lambda:self._run(item_id,job_id))
            except Exception:
                self._job_update(item_id,job_id,status='failed',message='Přípravu se nepodařilo spustit. Neopakuj ji; ověř původní požadavek.')
        return self.status(item_id)

    def _job_update(self,item_id,job_id,**fields):
        def update(document):
            job=document['items'][item_id]['job']
            if job['id']!=job_id: raise ValueError('Požadavek se změnil.')
            job.update(fields)
        self._mutate(update)

    def _run(self,item_id,job_id):
        try:
            with exclusive_file_lock(self.root/('run-'+job_id),timeout=0):
                entry=self.repository.read()['items'][item_id];job=entry['job']
                if job['id']!=job_id or job['status']!='queued' or job['nonce']!=self.nonce: return
                self._job_update(item_id,job_id,status='running')
                home=self.root/'requests'/job_id;home.mkdir(parents=True,exist_ok=True,mode=0o700)
                if job['input']['manual_reason']:
                    candidate=Candidate(kind='manual_required',title=Claim(value=job['input']['subject'],source='subject' if job['input']['subject'] else 'none',quote=job['input']['subject']),uncertainties=[job['input']['manual_reason']]).model_dump()
                    result={'candidate':candidate,'receipt':{'model_turns':0,'local_rule':True}}
                else:
                    result=self.driver(job,home,lambda thread:self._job_update(item_id,job_id,thread_id=thread),
                        lambda:self._job_update(item_id,job_id,send_started=True))
                atomic_write_json(home/'result.json',{'job_id':job_id,'content_digest':entry['content_digest'],**result})
                self._complete(item_id,job_id,result['candidate'])
        except Exception as exc:
            entry=self.repository.read()['items'][item_id];sent=entry['job'].get('send_started',False)
            self._job_update(item_id,job_id,status='delivery_unknown' if sent else 'failed',error_type=type(exc).__name__,
                message='Výsledek návrhu vyžaduje ověření. Nový modelový pokus se automaticky nespouští.')

    def _complete(self,item_id,job_id,candidate):
        entry=self.repository.read()['items'][item_id]
        self._card(item_id,entry['content_digest'])
        fields,evidence,warnings=materialize(candidate,entry['job']['input'])
        fields,calculated=simple_defaults(fields)
        for name in calculated:
            evidence[name]={'source':'calculation','quote':'','origin':'calculated'}
        if any(len(warning)>1000 for warning in warnings):raise ValueError('Upozornění překročilo limit.')
        issues,normalized=validate_fields(fields)
        issues=list(dict.fromkeys([*warnings,*issues,*evidence_issues(fields,evidence)]))
        if issues: normalized=None
        draft={'revision':0,'fields':fields,'evidence':evidence,'issues':issues,'normalized':normalized,
               'reminders':[1440,60],
               'source_item_id':item_id,'source_digest':entry['content_digest'],'calendar_writes':False}
        def complete(document):
            current=document['items'][item_id]
            if current['job']['id']!=job_id or current['job']['status']!='running':raise ValueError('Požadavek se změnil.')
            current.update(draft=draft,original_fields=fields,original_evidence=evidence,warnings=warnings)
            current['job'].update(status='completed',completed_at=now(),message='Návrh je připravený k lidskému posouzení.')
        self._mutate(complete)

    def save(self,payload):
        if (set(payload) not in ({'action','id','expected_revision','fields'}, {'action','id','expected_revision','fields','reminders'})
                or type(payload.get('expected_revision')) is not int):
            raise ValueError('Uložení potřebuje aktuální revizi návrhu.')
        item_id=payload['id'];card=self._card(item_id)
        validate_fields(payload['fields'])  # Validate untrusted shape before entering a transaction.
        if 'reminders' in payload: validate_reminders(payload['reminders'])
        def save(document):
            entry=document['items'].get(item_id)
            if not entry or not entry.get('draft') or entry['content_digest']!=card['content_digest']:
                raise ValueError('Původní návrh není dostupný.')
            if entry.get('write',{}).get('state','blocked') != 'blocked':
                raise ValueError('Událost už má evidovaný zápis; úpravy další zápis nepovolí.')
            draft=entry['draft']
            if draft['revision']!=payload['expected_revision']:raise ValueError('Návrh se mezitím změnil. Tvoje úpravy zůstávají v editoru; obnov stav.')
            fields,calculated=derive_fields(payload['fields'],draft['fields'],draft['evidence'])
            issues,normalized=validate_fields(fields)
            evidence=copy.deepcopy(entry['original_evidence'])
            for name in FIELD_NAMES:
                if fields[name]!=entry['original_fields'][name]:
                    evidence[name]['origin']='user' if fields[name] else 'missing'
                if name in calculated: evidence[name]={'source':'calculation','quote':'','origin':'calculated'}
            warnings=list(entry['warnings'])
            if entry['job']['input']['manual_reason']:warnings.append(entry['job']['input']['manual_reason'])
            current_issues=list(dict.fromkeys([*warnings,*issues,*evidence_issues(fields,evidence)]))
            draft.update(revision=draft['revision']+1,fields=fields,evidence=evidence,
                reminders=validate_reminders(payload.get('reminders',draft.get('reminders',[1440,60]))),
                issues=current_issues,normalized=None if current_issues else normalized,updated_at=now())
            entry.pop('review',None);entry.pop('confirmation',None)
        self._mutate(save)
        return self.status(item_id)

    def execute(self,payload):
        if not isinstance(payload,dict):raise ValueError('Neplatný požadavek.')
        if payload.get('action')=='prepare':return self.prepare(payload)
        if payload.get('action')=='save':return self.save(payload)
        if payload.get('action')=='save_simple':
            if set(payload)!={'action','id','expected_revision','values'}:raise ValueError('Neplatná úprava karty.')
            entry=self.review._entry(payload['id'],payload['expected_revision'])
            return self.save({'action':'save','id':payload['id'],'expected_revision':payload['expected_revision'],
                             'fields':edit_simple(entry['draft'],payload['values']),'reminders':[1440,60]})
        if payload.get('action')=='write':return self.write.execute(payload)
        if payload.get('action')=='authorize_writer':
            if set(payload)!={'action','id','confirmed'} or payload['confirmed'] is not True:
                raise ValueError('Povolení zápisu vyžaduje výslovný pokyn.')
            self._card(payload['id'])
            self.writer.build(confirmed=True)
            self.writer.authorize_current(confirmed=True)
            result=self.status(payload['id'])
            result['message']='Na Macu potvrď přístup aplikace Samantha Calendar Writer. Potom znovu potvrď zápis.'
            return result
        if payload.get('action') in {'review','confirm'}:return self.review.execute(payload)
        raise ValueError('Neznámá akce návrhu.')
