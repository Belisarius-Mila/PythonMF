import json
from pathlib import Path
import subprocess
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from app import cockpit
from app.cockpit_frontend import load_frontend_page
from scripts.cockpit_quality_gate import node_binary
from tests import test_calendar_delete as backend
EVENT=backend.EVENT


class CalendarDeleteHTTPTests(unittest.TestCase):
    def setUp(self):
        backend.CalendarDeleteTests.setUp(self)
        p=patch('app.cockpit_calendar_delete.DELETIONS',self.service);p.start();self.addCleanup(p.stop)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),cockpit.CockpitServer().make_handler())
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.shutdown)
        self.base=f'http://127.0.0.1:{self.server.server_port}'
    native=backend.CalendarDeleteTests.native
    def shutdown(self):self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)
    def request(self,payload,path='/api/calendar/delete',origin=None):
        headers={'Origin':origin or self.base,'Content-Type':'application/json'}
        try:r=urlopen(Request(self.base+path,data=json.dumps(payload).encode(),headers=headers),timeout=5)
        except HTTPError as exc:r=exc
        with r:return r.status,json.loads(r.read()),dict(r.headers)
    def test_calendar_delete_action_requires_exact_preview_and_confirmation_over_http(self):
        code,preview,headers=self.request({'action':'prepare','event':EVENT});self.assertEqual(code,200)
        self.assertIn('no-store',headers['Cache-Control']);self.assertEqual(preview['state'],'prepared')
        body={'action':'delete','request_id':preview['request_id'],'confirmed':True}
        self.assertEqual(self.request(body)[1]['state'],'deleted');self.assertEqual(self.request(body)[1]['state'],'deleted')
        self.assertEqual([r[0] for r in self.calls],['inspect','delete'])
    def test_foreign_origin_query_and_unconfirmed_delete_stop_before_helper(self):
        self.assertEqual(self.request({'action':'prepare','event':EVENT},origin='https://foreign.invalid')[0],403)
        self.assertEqual(self.request({'action':'prepare','event':EVENT},path='/api/calendar/delete?extra=1')[0],400)
        for payload in [{'action':'delete','confirmed':False},{'action':'delete_all','confirmed':True},{'action':'authorize','confirmed':False}]:
            self.assertEqual(self.request(payload)[0],400)
        self.assertEqual(self.calls,[]);self.helper.build.assert_not_called()
    def test_all_calendar_surfaces_deliver_the_same_confirmation_and_recovery_widget(self):
        for page in ['cockpit','calendar_overview','calendar_task','email_agent']:
            html=load_frontend_page(page)
            self.assertIn('/api/calendar/delete',html);self.assertIn('Ověřit původní smazání',html)
            self.assertIn('Smaže se pouze tento výskyt',html)
    def test_frontend_confirm_cancel_unknown_recovery_and_setup(self):
        result=subprocess.run([node_binary(),'tests/calendar_delete_frontend.test.cjs'],capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
