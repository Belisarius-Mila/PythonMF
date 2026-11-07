from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from email.message import EmailMessage
from pathlib import Path
import json
import tempfile
import unittest

from app.email.calendar_proposal import Candidate,Claim,empty_fields,materialize,validate_fields,strict_schema
from app.email.calendar_draft import CalendarDraftService,source_context
from app.email.continuous_agent import ContinuousEmailAgent
from app.email.continuous_source import ObservedEmail
from app.email.icloud_provider import _message_data_to_archive_source
from tests.test_continuous_email_agent import FakeSource,proposal

BODY='Schůzka dne 11.11.2026 od 10:00 do 11:00. Pásmo Europe/Prague. Místo Praha. https://meet.example.test/room'


def message(body=BODY, *, formal=False):
    mail=EmailMessage();mail['From']='sender@example.test';mail['To']='recipient@example.test'
    mail['Subject']='Schůzka';mail['Date']='Sat, 07 Nov 2026 08:00:00 +0100'
    mail.set_content(body)
    if formal:mail.add_attachment('BEGIN:VCALENDAR\nMETHOD:REQUEST\nEND:VCALENDAR',subtype='calendar',filename='invite.ics')
    raw=mail.as_bytes()
    source=_message_data_to_archive_source('1',[(b'RFC822.SIZE '+str(len(raw)).encode(),raw)],None,max_message_bytes=len(raw))
    return ObservedEmail('account-a','10',source)


def candidate():
    def body(value,quote=None):return Claim(value=value,source='body',quote=quote or value)
    return Candidate(kind='meeting',title=Claim(value='Schůzka',source='subject',quote='Schůzka'),
        date=body('2026-11-11','11.11.2026'),start_time=body('10:00'),end_time=body('11:00'),
        time_zone=body('Europe/Prague'),location=body('Praha'),join_url=body('https://meet.example.test/room')).model_dump()


class Driver:
    def __init__(self):self.calls=0;self.fail=False;self.result=candidate()
    def selection(self):return {'role':'continuous_email','model':'synthetic','reasoning_effort':'high','policy_digest':'0'*64,'fallback':False}
    def __call__(self,job,home,on_thread,before_send):
        self.calls+=1;on_thread('synthetic-thread');before_send()
        if self.fail:raise TimeoutError('synthetic uncertainty')
        return {'candidate':deepcopy(self.result),'receipt':{'delivered':True,'synthetic':True}}


class EmailCalendarDraftTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.worker=ContinuousEmailAgent(Path(self.temp.name)/'private')
        self.observed=message();self.worker.cycle(FakeSource([self.observed]),lambda _:proposal())
        self.driver=Driver();self.source_reads=0;self.callbacks=[]
        class Source:
            def read_item(inner,item):
                self.source_reads+=1;return self.observed
        self.factory=lambda *_:Source()
        self.service=CalendarDraftService(self.worker,source_factory=self.factory,driver=self.driver,launcher=self.callbacks.append)
        self.payload={'action':'prepare','id':self.observed.item_id,'expected_content_digest':self.observed.content_digest,
                      'request_id':'synthetic-calendar-request-1','confirmed':True}

    def prepare(self):return self.service.execute(self.payload)
    def complete(self):self.prepare();self.callbacks.pop(0)();return self.service.status(self.observed.item_id)
    def save(self,fields,revision=0):return self.service.execute({'action':'save','id':self.observed.item_id,'expected_revision':revision,'fields':fields})

    def test_status_is_side_effect_free_and_starts_no_model_or_provider(self):
        before=self.worker.status();view=self.service.status(self.observed.item_id)
        self.assertIsNone(view['draft']);self.assertIsNone(view['job']);self.assertFalse(self.service.root.exists())
        self.assertEqual(self.driver.calls,0);self.assertEqual(self.source_reads,0);self.assertEqual(self.worker.status(),before)

    def test_selected_source_is_read_once_and_mail_business_state_is_preserved(self):
        before=self.worker.status();view=self.prepare();self.assertEqual(view['job']['status'],'queued')
        self.assertEqual(self.driver.calls,0);self.assertEqual(self.source_reads,1)
        self.callbacks.pop(0)();view=self.service.status(self.observed.item_id)
        self.assertEqual(view['job']['status'],'completed');self.assertFalse(view['calendar_writes'])
        self.assertEqual(view['draft']['fields']['date'],'2026-11-11');self.assertEqual(view['draft']['issues'],[])
        self.assertEqual(view['draft']['normalized']['start'],'2026-11-11T09:00:00+00:00')
        self.assertEqual(view['draft']['source_digest'],self.observed.content_digest)
        self.assertEqual(self.worker.status(),before)

    def test_different_request_ids_double_click_and_restart_never_repeat_model(self):
        self.prepare();self.service.execute({**self.payload,'request_id':'a-different-id'})
        self.assertEqual(len(self.callbacks),1);self.callbacks.pop(0)()
        self.service.execute({**self.payload,'request_id':'yet-another-id'})
        restarted=CalendarDraftService(self.worker,driver=self.driver)
        restarted.execute({**self.payload,'request_id':'request-after-restart'})
        self.assertEqual(self.driver.calls,1);self.assertEqual(self.source_reads,1)
        self.assertEqual(restarted.status(self.observed.item_id)['job']['status'],'completed')

    def test_uncertain_model_result_cannot_cause_second_attempt(self):
        self.driver.fail=True;view=self.complete()
        self.assertEqual(view['job']['status'],'delivery_unknown');self.assertIsNone(view['draft'])
        self.service.execute({**self.payload,'request_id':'no-repeat-after-timeout'})
        self.assertEqual(self.driver.calls,1);self.assertEqual(len(self.callbacks),0)

    def test_interrupted_queued_or_running_request_is_unknown_after_restart(self):
        self.prepare();restarted=CalendarDraftService(self.worker,driver=self.driver)
        self.assertEqual(restarted.status(self.observed.item_id)['job']['status'],'delivery_unknown')
        restarted.execute({**self.payload,'request_id':'restart-must-not-retry'})
        self.assertEqual(self.driver.calls,0)

    def test_source_drift_wrong_item_and_confirmation_fail_before_model(self):
        for patch in ({'confirmed':False},{'expected_content_digest':'0'*64},{'id':'../other'},{'request_id':'bad'}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):self.service.execute({**self.payload,**patch})
        original=self.observed;self.observed=replace(original,uidvalidity='different')
        with self.assertRaises(ValueError):self.prepare()
        self.assertEqual(self.driver.calls,0);self.assertEqual(len(self.callbacks),0)

    def test_formal_invitation_and_recurrence_have_manual_draft_without_model(self):
        for observed in (message(formal=True),message('Schůzka každé pondělí od 10:00.')):
            with self.subTest(body=observed.source.body_text):
                worker=ContinuousEmailAgent(Path(self.temp.name)/('manual-'+observed.content_digest[:8]))
                worker.cycle(FakeSource([observed]),lambda _:proposal())
                class Source:
                    def read_item(self,item):return observed
                service=CalendarDraftService(worker,source_factory=lambda *_:Source(),driver=self.driver,launcher=lambda callback:callback())
                view=service.execute({**self.payload,'id':observed.item_id,'expected_content_digest':observed.content_digest})
                self.assertEqual(view['draft']['fields']['kind'],'manual_required');self.assertTrue(view['draft']['issues'])
        self.assertEqual(self.driver.calls,0)

    def test_edit_survives_restart_uses_revision_and_marks_user_data(self):
        view=self.complete();fields={**view['draft']['fields'],'location':'Upravené místo','duration_minutes':'60'}
        view=self.save(fields);self.assertEqual(view['draft']['revision'],1)
        self.assertEqual(view['draft']['evidence']['location']['origin'],'user')
        before=self.service.repository.read()
        with self.assertRaises(ValueError):self.save({**fields,'location':'Stale overwrite'})
        self.assertEqual(self.service.repository.read(),before)
        restarted=CalendarDraftService(self.worker)
        self.assertEqual(restarted.status(self.observed.item_id)['draft']['fields']['location'],'Upravené místo')
        self.assertEqual(self.driver.calls,1)

    def test_incomplete_edit_is_saved_with_missing_duration_no_assumption(self):
        fields=self.complete()['draft']['fields'];fields.update(end_time='',duration_minutes='')
        view=self.save(fields)
        self.assertTrue(any('délku' in issue for issue in view['draft']['issues']))
        self.assertIsNone(view['draft']['normalized'])

    def test_unverified_quote_is_rejected_and_retained_result_never_retried(self):
        self.driver.result['location']['quote']='NOT IN ORIGINAL MAIL'
        view=self.complete();self.assertEqual(view['job']['status'],'delivery_unknown');self.assertIsNone(view['draft'])
        self.assertEqual(len(list(self.service.root.glob('requests/*/result.json'))),1)
        self.prepare();self.assertEqual(self.driver.calls,1)

    def test_unknown_actions_and_dismissed_cards_are_rejected(self):
        with self.assertRaises(ValueError):self.service.execute({'action':'write'})
        self.worker.dismiss([self.observed.item_id],action='dismiss')
        with self.assertRaises(ValueError):self.prepare()
        self.assertEqual(self.source_reads,0)

    def test_deadline_proposal_preserves_missing_time_and_requires_date_review(self):
        self.observed=message('Pošlete podklady do pátku.')
        self.worker=ContinuousEmailAgent(Path(self.temp.name)/'deadline')
        self.worker.cycle(FakeSource([self.observed]),lambda _:proposal())
        self.service=CalendarDraftService(self.worker,source_factory=self.factory,driver=self.driver,launcher=self.callbacks.append)
        self.payload.update(expected_content_digest=self.observed.content_digest,id=self.observed.item_id)
        self.driver.result=Candidate(kind='task_deadline',date=Claim(value='2026-11-13',source='body',quote='do pátku'),all_day=True).model_dump()
        draft=self.complete()['draft']
        self.assertEqual(draft['fields']['kind'],'task_deadline')
        self.assertEqual(draft['fields']['start_time'],'');self.assertEqual(draft['fields']['duration_minutes'],'')
        self.assertTrue(any('interpretace' in issue for issue in draft['issues']))
        self.assertIsNone(draft['normalized'])

    def test_schema_is_strict_and_requires_all_structured_properties(self):
        schema=strict_schema()
        self.assertEqual(set(schema['required']),set(schema['properties']))
        claim=schema['$defs']['Claim'];self.assertEqual(set(claim['required']),set(claim['properties']))
        self.assertFalse(claim['additionalProperties'])


class CalendarProposalTimeTests(unittest.TestCase):
    def fields(self,**changes):
        return {**empty_fields(),'title':'Schůzka','date':'2026-11-11','start_time':'10:00','end_time':'11:00','time_zone':'Europe/Prague',**changes}

    def test_absolute_date_and_time_citations_cannot_claim_different_values(self):
        from app.email.calendar_proposal import evidence_issues
        source=source_context(message());model=candidate();model['date']['value']='2026-11-12';model['start_time']['value']='09:00'
        fields,evidence,_=materialize(model,source)
        issues=evidence_issues(fields,evidence)
        self.assertTrue(any('Datum neodpovídá' in issue for issue in issues));self.assertTrue(any('Začátek neodpovídá' in issue for issue in issues))

    def test_missing_zone_date_time_duration_and_invalid_values_are_visible(self):
        for patch in ({'time_zone':''},{'date':''},{'date':'2026-02-30'},{'date':'9999-12-31'},
                      {'start_time':'25:00'},{'duration_minutes':'0'},{'end_time':''},{'time_zone':'not/a/zone'},
                      {'join_url':'javascript:alert(1)'},{'end_time':'09:00'}):
            with self.subTest(patch=patch):self.assertTrue(validate_fields(self.fields(**patch))[0])

    def test_ambiguous_and_nonexistent_dst_times_are_never_normalized(self):
        for date in ('2026-03-29','2026-10-25'):
            issues,normalized=validate_fields(self.fields(date=date,start_time='02:30',end_time='',duration_minutes='60'))
            self.assertTrue(issues);self.assertIsNone(normalized)

    def test_cross_midnight_and_conflicting_duration(self):
        fields=self.fields(start_time='23:30',end_time='00:30',end_date='2026-11-12')
        self.assertEqual(validate_fields(fields)[0],[])
        self.assertTrue(validate_fields({**fields,'end_date':''})[0])
        self.assertTrue(validate_fields({**fields,'duration_minutes':'30'})[0])

    def test_deadline_is_not_a_meeting_and_all_day_bounds_are_explicit(self):
        fields=self.fields(kind='task_deadline',all_day=True,start_time='',end_time='')
        self.assertEqual(validate_fields(fields)[0],[])
        self.assertTrue(validate_fields({**fields,'duration_minutes':'60'})[0])
        self.assertTrue(validate_fields({**fields,'kind':'meeting'})[0])
        self.assertEqual(validate_fields({**fields,'kind':'meeting','end_date':'2026-11-12'})[0],[])
        issues,normalized=validate_fields({**fields,'all_day':False,'start_time':'15:00'})
        self.assertEqual(issues,[]);self.assertEqual(normalized,{'deadline':'2026-11-11T14:00:00+00:00'})


class CalendarDraftDriverTests(unittest.TestCase):
    def test_isolated_role_schema_and_durable_callback_precede_single_model_turn(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from app.email.calendar_draft import CalendarDraftDriver
        selected={'role':'continuous_email','model':'synthetic','reasoning_effort':'high','policy_digest':'0'*64}
        events=[]
        class Client:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def list_models(self):return []
            def read_effective_config(self,**kwargs):return {'mcp_servers':{'example':{'enabled':True}}}
            transport=SimpleNamespace(request=lambda *args:{'data':[]})
            def start_thread(self,**kwargs):
                self.options=kwargs;events.append('thread');return 'original-thread'
            def send_text(self,**kwargs):
                self.sent=kwargs;events.append('turn')
                return SimpleNamespace(delivered=True,answer=json.dumps(candidate()),as_dict=lambda:{'delivered':True})
        client=Client();driver=CalendarDraftDriver(client_factory=lambda:client)
        with tempfile.TemporaryDirectory() as directory,patch('app.email.calendar_draft.agent_roles.assert_current',return_value=selected),patch('app.email.calendar_draft.agent_roles.resolve_role',return_value=selected):
            driver({'selection':selected,'id':'f'*32,'input':source_context(message())},Path(directory),lambda thread:events.append('thread_saved'),lambda:events.append('send_claimed'))
        self.assertEqual(events,['thread','thread_saved','send_claimed','turn'])
        profile=client.sent['permission_profile']
        self.assertEqual(profile,client.options['permission_profile'])
        self.assertIs(client.options['config_overrides']['permissions'][profile]['network']['enabled'],False)
        self.assertEqual(client.options['config_overrides']['permissions'][profile]['filesystem'][':minimal'],'read')
        overrides=client.options['config_overrides']
        for feature in ('apps','shell_tool','image_generation','remote_plugin','memories','plugins','computer_use','browser_use'):
            self.assertIs(overrides['features.'+feature],False)
        self.assertIs(overrides['mcp_servers.example.enabled'],False)
        self.assertEqual(client.sent['client_message_id'],'calendar-draft-'+'f'*32)
        self.assertEqual(client.sent['service_tier_for_turn'],'default')
        self.assertEqual(set(json.loads(client.sent['text'])),{'subject','date','body','html','manual_reason'})
