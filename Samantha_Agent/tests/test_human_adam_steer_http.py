import http.client
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from app import cockpit
from app.communication.session_hub import CanonicalSessionHub
from tests import test_human_adam_profiles as profile_fixtures
from tests import test_human_adam_work_http as work_http_helpers
from tests.test_human_adam_steer import SteerClient, wait_until


class SteerHTTPTests(unittest.TestCase):
    request = work_http_helpers.WorkHTTPTests.request
    shutdown = work_http_helpers.WorkHTTPTests.shutdown
    join_workers = work_http_helpers.WorkHTTPTests.join_workers

    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.manager, _, _, _, _ = profile_fixtures.HumanAdamProfileManagerTests().make_manager(self.root)
        self.addCleanup(self.manager.close)
        self.addCleanup(self.join_workers)
        self.client = SteerClient()
        self.addCleanup(self.client.close)
        service = self.manager.profiles['human_adam']['service']
        service._hub = CanonicalSessionHub(state_path=service.state_path, workspace=self.root,
            client_factory=lambda: self.client, developer_instructions='Synthetic original control',
            sandbox='read-only',sandbox_policy={'type':'readOnly','networkAccess':False},approval_policy='never',reasoning_effort='low')
        self.manager.connect()
        patcher=patch('app.cockpit.HUMAN_ADAM',self.manager);patcher.start();self.addCleanup(patcher.stop)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),cockpit.CockpitServer().make_handler())
        self.server.handle_error=lambda *_:None
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.shutdown)
        self.base=f'http://127.0.0.1:{self.server.server_port}'
        self.project='layer-human-adam-development'
        code,result,_=self.request('/api/human-adam/work/start',{'message':'Original private consultation','client_message_id':'original-request-0001',
            'workstream_id':self.project,'confirmed':True})
        self.assertEqual(code,202)
        self.identity=result['operations'][0]['operation_id']
        wait_until(lambda:self.manager.work_controller.view(self.project,identity=self.identity)['operations'][0]['capabilities']['steer'])

    def payload(self,index=1,**change):
        return {'workstream_id':self.project,'operation_id':self.identity,'command_id':f'ha06-{self.identity}-{index:032x}',
                'expectedTurnId':self.client.turn,'text':'Upřesnění stejné práce','confirmed':True,**change}

    def read_receipt(self,index=1):
        command=self.payload(index)['command_id']
        return self.request(f'/api/human-adam/work/command?workstream_id={self.project}&operation_id={self.identity}&command_id={command}')

    def test_ten_http_appends_stay_in_same_readonly_turn(self):
        for index in range(10):
            code,result,_=self.request('/api/human-adam/work/steer',self.payload(index))
            self.assertEqual(code,200);self.assertEqual(result['command']['state'],'accepted')
        self.assertEqual(self.client.count('turn/start'),1);self.assertEqual(self.client.count('turn/steer'),10)
        self.assertIn('writable=false',self.client.transport.writes[0]['params']['input'][0]['text'])
        self.assertTrue(all(set(m['params'])=={'threadId','expectedTurnId','clientUserMessageId','input'}
                            for m in self.client.transport.writes if m['method']=='turn/steer'))
        self.client.finish()
        self.assertTrue(self.manager.work_controller._handles[self.identity].finished.wait(2))
        self.assertTrue(self.manager.active_service.hub.snapshot()['messages'][-1]['delivery_confirmed'])

    def test_origin_confirmation_and_override_guards(self):
        for change in ({'confirmed':False},{'write_intent':True},{'model':'other'},{'expectedTurnId':None}):
            self.assertEqual(self.request('/api/human-adam/work/steer',self.payload(**change))[0],400)
        self.assertEqual(self.request('/api/human-adam/work/steer',self.payload(),origin='https://foreign.example')[0],403)
        self.assertEqual(self.client.count('turn/steer'),0)
        self.assertEqual(self.request('/api/human-adam/work/steer',self.payload(expectedTurnId='turn-other'))[1]['command']['state'],'rejected')
        self.assertEqual(self.client.count('turn/start'),1)

    def test_read_receipt_is_no_store_and_never_dispatches(self):
        self.assertEqual(self.read_receipt()[1]['found'],False)
        self.request('/api/human-adam/work/steer',self.payload())
        code,receipt,headers=self.read_receipt()
        self.assertEqual(code,200);self.assertTrue(receipt['read_only']);self.assertFalse(receipt['writes_performed'])
        self.assertIn('no-store',headers['Cache-Control'])
        self.assertEqual(receipt['command']['state'],'accepted')
        self.assertEqual(self.client.count('turn/steer'),1)

    def test_http_disconnect_does_not_cancel_or_repeat_original_command(self):
        release=self.client.steer_release=threading.Event();self.addCleanup(release.set)
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2)
        connection.request('POST','/api/human-adam/work/steer',body=json.dumps(self.payload()),headers={'Origin':self.base,'Content-Type':'application/json'})
        self.assertTrue(self.client.steer_entered.wait(1));connection.close()
        duplicate=self.request('/api/human-adam/work/steer',self.payload())[1]
        self.assertTrue(duplicate['duplicate_prevented']);self.assertEqual(duplicate['command']['state'],'pending')
        release.set();wait_until(lambda:self.read_receipt()[1]['command']['state']=='accepted')
        self.assertEqual(self.client.count('turn/steer'),1);self.assertEqual(self.client.count('turn/start'),1)
