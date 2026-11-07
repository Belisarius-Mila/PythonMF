import json
from pathlib import Path
import subprocess
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request,urlopen
from unittest.mock import patch
from app import cockpit
from scripts.cockpit_quality_gate import node_binary
from tests import test_calendar_agenda as backend


class CalendarAgendaHTTPTests(unittest.TestCase):
    prepare=backend.CalendarAgendaTests.prepare
    def setUp(self):
        backend.CalendarAgendaTests.setUp(self)
        self.patcher=patch('app.cockpit_calendar_agenda.AGENDA',self.agenda);self.patcher.start();self.addCleanup(self.patcher.stop)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),cockpit.CockpitServer().make_handler())
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.shutdown)
        self.base=f'http://127.0.0.1:{self.server.server_port}'

    def shutdown(self):self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)
    def request(self,path='/api/calendar/agenda',body=None,origin=None):
        headers={'Origin':origin or self.base,'Content-Type':'application/json'}
        try:r=urlopen(Request(self.base+path,data=None if body is None else json.dumps(body).encode(),headers=headers),timeout=5)
        except HTTPError as exc:r=exc
        with r:return r.status,r.read(),dict(r.headers)

    def test_get_is_private_read_only_and_starts_no_native_read(self):
        code,raw,headers=self.request();self.assertEqual(code,200);self.assertFalse(json.loads(raw)['fresh'])
        self.assertIn('no-store',headers['Cache-Control']);self.assertEqual(self.pilot.calls,[]);self.assertFalse(self.pilot.root.exists())

    def test_background_refresh_and_local_type_assignment_over_real_http(self):
        self.prepare();calls=len(self.pilot.calls)
        code,raw,_=self.request(body={'action':'refresh'});self.assertEqual(code,200);view=json.loads(raw)
        self.assertTrue(view['refreshing']);self.assertEqual(len(self.pilot.calls),calls);self.assertEqual(len(self.callbacks),1)
        self.callbacks.pop()();_,raw,_=self.request();view=json.loads(raw)
        label={'action':'set_kind','key':view['meetings'][0]['key'],'kind':'task_deadline','expected_selection_revision':view['selection_revision'],
               'expected_labels_revision':view['labels_revision'],'confirmed':True}
        before=self.overview.path.read_bytes();code,raw,_=self.request(body=label)
        self.assertEqual(code,200);self.assertEqual(len(json.loads(raw)['deadlines']),1);self.assertEqual(self.overview.path.read_bytes(),before)
        self.assertEqual(self.request(body=label)[0],400)

    def test_foreign_origin_and_invalid_actions_stop_before_read_or_annotation(self):
        self.prepare();calls=len(self.pilot.calls)
        self.assertEqual(self.request(body={'action':'refresh'},origin='https://other.invalid')[0],403)
        for body in ({'action':'refresh','extra':True},{'action':'authorize'},{'action':'write'},{'action':'set_kind','confirmed':False}):
            self.assertEqual(self.request(body=body)[0],400)
        for path in ('/api/calendar/agenda?other=1','/api/calendar/agenda?id=x'):
            self.assertEqual(self.request(path)[0],400);self.assertEqual(self.request(path,body={'action':'refresh'})[0],400)
        self.assertEqual(len(self.pilot.calls),calls);self.assertEqual(self.callbacks,[])

    def test_frontend_contract(self):
        result=subprocess.run([node_binary(),'tests/calendar_agenda_frontend.test.cjs'],capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
