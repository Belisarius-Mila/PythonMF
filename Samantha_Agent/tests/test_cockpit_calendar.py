from __future__ import annotations

from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError

from app import cockpit
from app.calendar_overview import CalendarOverview
from app.cockpit_frontend import CALENDAR_OVERVIEW_HTML
from tests.test_calendar_overview import FakePilot
from scripts.cockpit_quality_gate import node_binary


class CockpitCalendarTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()/'private'
        now=lambda:datetime(2026,11,7,12,tzinfo=timezone.utc)
        self.pilot=FakePilot(self.root,now); self.store=CalendarOverview(self.pilot,clock=now)
        self.patch=patch('app.cockpit_calendar.CalendarOverview',return_value=self.store)
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),cockpit.CockpitServer().make_handler())
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.addCleanup(self.shutdown); self.base=f'http://127.0.0.1:{self.server.server_port}'

    def shutdown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=3)

    def request(self,path,payload=None,origin=None):
        headers={'Origin':origin or self.base,'Content-Type':'application/json'}
        try: result=urlopen(Request(self.base+path,data=None if payload is None else json.dumps(payload).encode(),headers=headers),timeout=5)
        except HTTPError as exc: result=exc
        with result: return result.status,result.read(),dict(result.headers)

    def test_page_and_snapshot_are_readonly_private_and_reachable_from_cockpit(self):
        status,raw,headers=self.request('/calendar/')
        self.assertEqual(status,200); self.assertEqual(raw,CALENDAR_OVERVIEW_HTML.encode())
        self.assertIn('no-store',headers['Cache-Control']); self.assertIn('href="/calendar/"',cockpit.COCKPIT_HTML)
        status,raw,_=self.request('/api/calendar/overview')
        self.assertFalse(json.loads(raw)['ready']); self.assertFalse(self.root.exists()); self.assertEqual(self.pilot.calls,[])

    def test_real_http_inventory_selection_refresh_and_conflict(self):
        status,raw,_=self.request('/api/calendar/action',{'action':'refresh','confirmed':True})
        self.assertEqual(status,200); self.assertEqual(len(json.loads(raw)['calendars']),2)
        selection={'action':'save_selection','confirmed':True,'expected_revision':0,'read_calendar_ids':['a'],'target_calendar_id':'a'}
        self.assertEqual(self.request('/api/calendar/action',selection)[0],200)
        self.assertEqual(self.request('/api/calendar/action',selection)[0],409)
        _,raw,_=self.request('/api/calendar/action',{'action':'refresh','confirmed':True})
        state=json.loads(raw); self.assertTrue(state['ready']); self.assertEqual(len(state['events']),1)

    def test_foreign_origin_queries_and_unconfirmed_reads_are_rejected(self):
        self.assertEqual(self.request('/api/calendar/action',{'action':'refresh','confirmed':True},origin='https://other.invalid')[0],403)
        self.assertEqual(self.request('/api/calendar/action',{'action':'refresh'})[0],400)
        self.assertEqual(self.request('/api/calendar/overview?other=1')[0],400)
        self.assertEqual(self.request('/api/calendar/action?other=1',{'action':'refresh','confirmed':True})[0],400)
        self.assertEqual(self.pilot.calls,[])

    def test_browser_contract(self):
        result=subprocess.run([node_binary(),'tests/calendar_overview_frontend.test.cjs'],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
