import json
import subprocess
import unittest
from unittest.mock import patch

from app import cockpit
from app.cockpit_frontend import load_frontend_page
from scripts.cockpit_quality_gate import node_binary
from tests import test_calendar_edit as backend
EVENT, CHANGES = backend.EVENT, backend.CHANGES
from tests.test_cockpit_http_security import running_cockpit_server


class CalendarEditHTTPTests(unittest.TestCase):
    def setUp(self):backend.CalendarEditTests.setUp(self)
    native=backend.CalendarEditTests.native
    def call(self,host,port,payload,path='/api/calendar/edit',origin=None):
        # Shared request helper preserves actual host/origin enforcement.
        import http.client
        connection=http.client.HTTPConnection(host,port,timeout=5)
        connection.request('POST',path,json.dumps(payload),{'Content-Type':'application/json','Origin':origin or f'http://{host}:{port}'})
        response=connection.getresponse();body=json.loads(response.read());status=response.status;headers=dict(response.getheaders());connection.close()
        return status,body,headers
    def test_edit_real_http_prepare_update_and_recovery_contract(self):
        with patch('app.cockpit_calendar_edit.EDITS',self.service),running_cockpit_server() as (host,port,_):
            code,p,headers=self.call(host,port,{'action':'prepare','event':EVENT})
            self.assertEqual(code,200);self.assertIn('no-store',headers['Cache-Control'])
            body={'action':'update','request_id':p['request_id'],'changes':CHANGES,'confirmed':True}
            self.assertEqual(self.call(host,port,body)[1]['state'],'verified')
            self.assertEqual(self.call(host,port,body)[1]['state'],'verified')
        self.assertEqual([c[0] for c in self.calls],['inspect','update'])
    def test_foreign_origin_query_and_unconfirmed_update_never_touch_helper(self):
        with patch('app.cockpit_calendar_edit.EDITS',self.service),running_cockpit_server() as (host,port,_):
            body={'action':'prepare','event':EVENT}
            self.assertEqual(self.call(host,port,body,origin='https://foreign.invalid')[0],403)
            self.assertEqual(self.call(host,port,body,path='/api/calendar/edit?x=1')[0],400)
            self.assertEqual(self.call(host,port,{'action':'update','confirmed':False})[0],400)
        self.assertEqual(self.calls,[])
    def test_frontend_module_and_browser_behavior(self):
        for page in ['cockpit','calendar_overview']:
            html=load_frontend_page(page)
            self.assertIn('Splněno',html);self.assertIn('Uložit změny',html);self.assertIn('/api/calendar/edit',html)
        result=subprocess.run([node_binary(),'tests/calendar_actions_frontend.test.cjs'],capture_output=True,text=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
