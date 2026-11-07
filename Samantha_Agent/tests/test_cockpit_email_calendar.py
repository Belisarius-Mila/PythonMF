from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request,urlopen

from app import cockpit
from app.email.calendar_draft import CalendarDraftService
from app.email.continuous_agent import ContinuousEmailAgent
from app.cockpit_email_calendar import email_calendar_draft_action,email_calendar_draft_status
from tests.test_continuous_email_agent import FakeSource,proposal
from tests.test_email_calendar_draft import message,Driver
from scripts.cockpit_quality_gate import node_binary


class EmailCalendarHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.worker=ContinuousEmailAgent(Path(self.temp.name)/'private')
        self.mail=message();self.worker.cycle(FakeSource([self.mail]),lambda _:proposal())
        self.driver=Driver();self.callbacks=[]
        class Source:
            def read_item(inner,item):return self.mail
        self.service=CalendarDraftService(self.worker,source_factory=lambda *_:Source(),driver=self.driver,launcher=self.callbacks.append)
        self.patches=[patch('app.cockpit.email_calendar_draft_action',side_effect=lambda payload:email_calendar_draft_action(payload,service=self.service)),
                      patch('app.cockpit.email_calendar_draft_status',side_effect=lambda id:email_calendar_draft_status(id,service=self.service))]
        for p in self.patches:p.start();self.addCleanup(p.stop)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),cockpit.CockpitServer().make_handler())
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.shutdown)
        self.base=f'http://127.0.0.1:{self.server.server_port}'

    def shutdown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)

    def request(self,path,payload=None,origin=None):
        headers={'Origin':origin or self.base,'Content-Type':'application/json'}
        try:r=urlopen(Request(self.base+path,data=None if payload is None else json.dumps(payload).encode(),headers=headers),timeout=5)
        except HTTPError as exc:r=exc
        with r:return r.status,r.read(),dict(r.headers)

    def test_get_does_not_contact_mail_model_or_initialize_store(self):
        code,raw,headers=self.request('/api/email-agent/calendar-draft?id='+self.mail.item_id)
        self.assertEqual(code,200);self.assertIsNone(json.loads(raw)['draft']);self.assertIn('no-store',headers['Cache-Control'])
        self.assertFalse(self.service.root.exists());self.assertEqual(self.driver.calls,0)
        code,raw,_=self.request('/emails-to-resolve/')
        self.assertEqual(code,200);self.assertIn('Navrhnout událost',raw.decode());self.assertIn('calendarDraftEditor',raw.decode())

    def test_explicit_prepare_save_and_read_current_draft_over_http(self):
        body={'action':'prepare','confirmed':True,'id':self.mail.item_id,'expected_content_digest':self.mail.content_digest,'request_id':'http-calendar-draft-001'}
        code,raw,_=self.request('/api/email-agent/calendar-draft',body)
        self.assertEqual(code,200);self.assertEqual(json.loads(raw)['job']['status'],'queued')
        self.callbacks.pop(0)()
        _,raw,_=self.request('/api/email-agent/calendar-draft?id='+self.mail.item_id);view=json.loads(raw)
        fields={**view['draft']['fields'],'location':'Upraveno přes HTTP'}
        code,raw,_=self.request('/api/email-agent/calendar-draft',{'action':'save','id':self.mail.item_id,'expected_revision':0,'fields':fields})
        self.assertEqual(code,200);self.assertEqual(json.loads(raw)['draft']['revision'],1)
        self.assertEqual(self.driver.calls,1)

    def test_other_origins_bad_queries_and_unconfirmed_prepare_fail_before_model(self):
        body={'action':'prepare','id':self.mail.item_id}
        self.assertEqual(self.request('/api/email-agent/calendar-draft',body,origin='https://other.invalid')[0],403)
        self.assertEqual(self.request('/api/email-agent/calendar-draft',body)[0],400)
        for query in ('','?id=../other','?id=a&id=b','?id=a&extra=b'):
            self.assertEqual(self.request('/api/email-agent/calendar-draft'+query)[0],400)
        self.assertEqual(self.driver.calls,0);self.assertEqual(self.callbacks,[])

    def test_editor_browser_contract(self):
        result=subprocess.run([node_binary(),'tests/email_calendar_draft_frontend.test.cjs'],capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_explicit_calendar_review_and_confirmation_over_http_preserve_mail_state(self):
        from app.calendar_overview import CalendarOverview
        from tests.test_email_calendar_review import BoundedPilot
        clock=lambda:datetime(2026,11,7,12,tzinfo=timezone.utc)
        pilot=BoundedPilot(Path(self.temp.name)/'calendar',clock)
        self.service.calendar=CalendarOverview(pilot,clock=clock);self.service.clock=clock
        self.service.calendar.refresh(confirmed=True)
        self.service.calendar.save_selection({'action':'save_selection','confirmed':True,'expected_revision':0,'read_calendar_ids':['a'],'target_calendar_id':'a'})
        self.request('/api/email-agent/calendar-draft',{'action':'prepare','confirmed':True,'id':self.mail.item_id,'expected_content_digest':self.mail.content_digest,'request_id':'http-calendar-review-01'})
        self.callbacks.pop(0)();before=self.worker.status()
        payload={'action':'review','id':self.mail.item_id,'expected_revision':0,'confirmed':True}
        reads=len(pilot.intervals)
        self.assertEqual(self.request('/api/email-agent/calendar-draft',payload,origin='https://other.invalid')[0],403)
        self.assertEqual(self.request('/api/email-agent/calendar-draft',{**payload,'confirmed':False})[0],400)
        self.assertEqual(len(pilot.intervals),reads)
        code,body,_=self.request('/api/email-agent/calendar-draft',payload)
        self.assertEqual(code,200);view=json.loads(body)
        self.assertEqual(view['draft']['reminders'],[1440,60]);self.assertEqual(len(view['review']['alerts']),2)
        confirmation={'action':'confirm','id':self.mail.item_id,'expected_revision':0,'review_id':view['review']['review_id'],'acknowledged':True,'accept_conflicts':False}
        self.assertEqual(self.request('/api/email-agent/calendar-draft',{**confirmation,'acknowledged':False})[0],400)
        code,body,_=self.request('/api/email-agent/calendar-draft',confirmation)
        self.assertEqual(code,200);self.assertIsNotNone(json.loads(body)['confirmation'])
        self.assertEqual(self.worker.status(),before);self.assertEqual(self.driver.calls,1)
