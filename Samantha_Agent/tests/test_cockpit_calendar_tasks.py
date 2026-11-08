import json
from pathlib import Path
import struct
import subprocess
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from app import cockpit
from scripts.cockpit_quality_gate import node_binary
from tests import test_calendar_tasks as backend


class CalendarTaskHTTPTests(unittest.TestCase):
    prepare = backend.CalendarTaskTests.prepare
    payload = backend.CalendarTaskTests.payload

    def setUp(self):
        backend.CalendarTaskTests.setUp(self)
        self.patcher=patch('app.cockpit_calendar_tasks.TASKS',self.service)
        self.patcher.start();self.addCleanup(self.patcher.stop)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),cockpit.CockpitServer().make_handler())
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.shutdown);self.base=f'http://127.0.0.1:{self.server.server_port}'

    def shutdown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(3)

    def request(self,path='/api/calendar/tasks',body=None,origin=None,host=None):
        headers={'Origin':origin or self.base,'Content-Type':'application/json'}
        if host:headers['Host']=host
        request=Request(self.base+path,data=None if body is None else json.dumps(body).encode(),headers=headers)
        try:r=urlopen(request,timeout=10)
        except HTTPError as error:r=error
        with r:return r.status,r.headers,r.read()

    def test_context_and_standalone_page_are_read_only(self):
        status,headers,body=self.request();self.assertEqual(status,200)
        self.assertFalse(json.loads(body)['ready']);self.assertIn('no-store',headers['Cache-Control'])
        status,_,body=self.request('/calendar/task/');self.assertEqual(status,200)
        self.assertIn('Zadání úkolu',body.decode());self.assertIn('type="time" value="09:00"',body.decode())
        self.assertEqual(self.writer.calls,[]);self.assertEqual(self.pilot.calls,[])
        self.assertFalse(self.service.root.exists())

    def test_home_screen_manifest_pins_the_task_route_and_real_icon(self):
        status,headers,body=self.request('/calendar/task/manifest.webmanifest')
        self.assertEqual(status,200);self.assertEqual(headers['Content-Type'],'application/manifest+json')
        manifest=json.loads(body)
        self.assertEqual(manifest['start_url'],'/calendar/task/');self.assertEqual(manifest['id'],'/calendar/task/')
        status,headers,body=self.request('/calendar/task/icon-180.png');self.assertEqual(status,200)
        self.assertEqual(headers['Content-Type'],'image/png');self.assertEqual(body[:8],b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('>II',body[16:24]),(180,180))
        self.assertEqual(self.request('/calendar/task/icon.svg')[0],200)
        self.assertEqual(self.request('/calendar/task/manifest.webmanifest?start=other')[0],400)
        self.assertIn('/calendar/task/',self.request('/calendar/')[2].decode())

    def test_actual_http_create_and_same_id_status_are_idempotent(self):
        self.prepare()
        for _ in range(2):
            status,_,body=self.request(body=self.payload());self.assertEqual(status,200)
            self.assertEqual(json.loads(body)['state'],'verified')
        status,_,body=self.request(body={'action':'status','request_id':'a'*32})
        self.assertEqual(status,200);self.assertEqual(json.loads(body)['task']['time'],'09:00')
        self.assertEqual(len(self.writer.calls),1)

    def test_foreign_origin_host_queries_and_bad_consent_cannot_write(self):
        self.prepare()
        self.assertEqual(self.request(body=self.payload(),origin='https://foreign.invalid')[0],403)
        self.assertEqual(self.request('/calendar/task/',host='foreign.invalid')[0],400)
        self.assertEqual(self.request('/api/calendar/tasks?title=private',self.payload())[0],400)
        self.assertEqual(self.request(body=self.payload(confirmed=False))[0],400)
        self.assertEqual(self.request(body={'action':'recover','request_id':'a'*32,'confirmed':False})[0],400)
        self.assertEqual(self.writer.calls,[]);self.assertFalse(self.service.root.exists())

    def test_frontend_contract_in_node(self):
        result=subprocess.run([node_binary(),str(Path(__file__).with_name('calendar_task_frontend.test.cjs'))],
                              cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
