from __future__ import annotations

import http.client
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from app import cockpit
from app.communication.session_hub import CanonicalSessionHub
from tests.test_communication_session_hub import FakeClient
from tests import test_human_adam_profiles as profile_fixtures


class SyntheticClient(FakeClient):
    instances = []
    block_started = None
    block_release = None
    fail_send = False
    fail_resume = False
    next_thread_ids = []
    generated_images = ()


class WorkHTTPTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.manager, _, _, _, _ = profile_fixtures.HumanAdamProfileManagerTests().make_manager(self.root)
        self.addCleanup(self.manager.close)
        self.addCleanup(self.join_workers)
        self.started, self.release = threading.Event(), threading.Event()
        SyntheticClient.instances = []
        SyntheticClient.block_started, SyntheticClient.block_release = self.started, self.release
        service = self.manager.profiles['human_adam']['service']
        service._hub = CanonicalSessionHub(state_path=service.state_path, workspace=self.root,
            client_factory=SyntheticClient, developer_instructions='Synthetic work fixture',
            sandbox='read-only', sandbox_policy={'type':'readOnly'}, approval_policy='never', reasoning_effort='low')
        self.manager.connect()
        patcher = patch('app.cockpit.HUMAN_ADAM', self.manager); patcher.start(); self.addCleanup(patcher.stop)
        self.server = ThreadingHTTPServer(('127.0.0.1',0), cockpit.CockpitServer().make_handler())
        self.server.handle_error = lambda *_: None
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.addCleanup(self.shutdown)
        self.addCleanup(self.release.set)
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        self.project = 'layer-human-adam-development'

    def join_workers(self):
        controller = self.manager._work_controller
        if controller:
            for handle in list(controller._handles.values()):
                if handle.thread: handle.thread.join(3)

    def shutdown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(3)

    def request(self,path,payload=None,origin=None):
        body = None if payload is None else json.dumps(payload).encode()
        headers={'Origin':origin or self.base,'Content-Type':'application/json'}
        try:r=urlopen(Request(self.base+path,data=body,headers=headers),timeout=3)
        except HTTPError as e:r=e
        with r:return r.status,json.loads(r.read()),dict(r.headers)

    def payload(self, **extra):
        return {'message':'PRIVATE accepted consultation','client_message_id':'http-work-0001',
                'workstream_id':self.project,'confirmed':True,**extra}

    def lookup(self,extra=''):
        return self.request('/api/human-adam/work?workstream_id='+self.project+extra)

    def wait_done(self,identity):
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            _,result,_=self.lookup('&operation_id='+identity)
            if result['operations'][0]['lifecycle_state']=='completed':return result
            time.sleep(.01)
        self.fail('Original work did not complete')

    def test_fast_acceptance_reload_and_two_clients_have_one_canonical_turn(self):
        began=time.monotonic()
        code,result,_=self.request('/api/human-adam/work/start',self.payload())
        self.assertEqual(code,202);self.assertLess(time.monotonic()-began,1)
        identity=result['operations'][0]['operation_id'];self.assertTrue(self.started.wait(2))
        code,second,_=self.request('/api/human-adam/work/start',self.payload())
        self.assertEqual(code,202);self.assertTrue(second['duplicate_prevented'])
        code,view,headers=self.lookup('&client_message_id=http-work-0001')
        self.assertEqual(code,200);self.assertIn('no-store',headers['Cache-Control'])
        self.assertEqual(view['operations'][0]['operation_id'],identity)
        self.assertNotIn('PRIVATE',json.dumps(view))
        self.assertNotIn(str(self.root),json.dumps(view))
        # Existing profile ownership also protects the accepted-to-start interval.
        code,switch,_=self.request('/api/human-adam/profile',{'workstream_id':'project-knowledge-library','confirmed':True})
        self.assertFalse(switch['ok'])
        self.release.set();done=self.wait_done(identity)
        self.assertEqual(done['operations'][0]['delivery_state'],'confirmed')
        self.assertEqual(SyntheticClient.instances[0].sent,1)
        self.assertIn('writable=false',SyntheticClient.instances[0].sent_texts[0])
        self.assertEqual(self.manager.active_workstream_id,self.project)

    def test_legacy_browser_disconnect_does_not_own_or_repeat_execution(self):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        wire={'message':'PRIVATE legacy task','client_message_id':'legacy-work-0001'}
        connection.request('POST','/api/human-adam/send',body=json.dumps(wire),
                           headers={'Origin':self.base,'Content-Type':'application/json'})
        self.assertTrue(self.started.wait(2));connection.close()
        code,view,_=self.lookup('&client_message_id=legacy-work-0001')
        self.assertEqual(code,200);identity=view['operations'][0]['operation_id']
        self.release.set();done=self.wait_done(identity)
        self.assertEqual(done['operations'][0]['client_request_id'],'legacy-work-0001')
        self.assertEqual(SyntheticClient.instances[0].sent,1)

    def test_read_validation_confirmation_and_foreign_origin_cannot_start_a_model(self):
        path='/api/human-adam/work/start'
        for payload in (self.payload(confirmed=False),self.payload(root='/tmp'),self.payload(write_intent='true')):
            self.assertEqual(self.request(path,payload)[0],400)
        self.assertEqual(self.request(path,self.payload(),origin='https://foreign.example')[0],403)
        for extra in ('&cursor=-1','&cursor=nan','&cursor=1&cursor=2','&root=/tmp'):
            self.assertEqual(self.lookup(extra)[0],400)
        self.assertEqual(self.lookup()[1]['operations'],[])
        self.assertEqual(SyntheticClient.instances[0].sent,0)
        self.assertFalse((self.root/'owned_work').exists())

    def test_wrong_project_and_request_fingerprint_are_conflicts_without_second_send(self):
        _,result,_=self.request('/api/human-adam/work/start',self.payload())
        self.assertTrue(self.started.wait(2));identity=result['operations'][0]['operation_id']
        for extra in ({'message':'different'},{'write_intent':True}):
            self.assertEqual(self.request('/api/human-adam/work/start',self.payload(**extra))[0],409)
        code,_,_=self.request('/api/human-adam/work?workstream_id=project-knowledge-library&operation_id='+identity)
        self.assertEqual(code,409)
        self.assertEqual(self.request('/api/human-adam/work/start',self.payload(workstream_id='project-knowledge-library'))[0],409)
        self.release.set();self.wait_done(identity)
        self.assertEqual(SyntheticClient.instances[0].sent,1)

    def test_capabilities_and_routes_are_registered_without_enabling_steer_or_stop(self):
        from app.capabilities import get_capability
        self.assertTrue(get_capability('human_adam_work_read').is_read_only)
        self.assertTrue(get_capability('human_adam_work_start').requires_confirmation)
        paths=[row['path'] for row in cockpit.COCKPIT_POST_ACTIONS]
        self.assertEqual(paths.count('/api/human-adam/work/start'),1)
        self.assertEqual(paths.count('/api/human-adam/work/recover'),1)

    def test_recover_is_explicit_metadata_reconciliation_without_a_model(self):
        from app.communication.human_adam_work import normalized_request
        controller=self.manager.work_controller
        session=self.manager.active_service.hub.snapshot()
        scope={'workstream_id':self.project,'profile_id':'human_adam','thread_id':session['thread_id'],
               'connection_generation':session['connection_generation']}
        record,_=controller.store.admit(normalized_request({'text':'PRIVATE accepted','client_message_id':'old-work-0001'}),
            scope,'old-backend',session_path=self.manager.active_service.hub.state_path)
        payload={'workstream_id':self.project,'operation_id':record['operation_id'],'confirmed':True}
        self.assertEqual(self.request('/api/human-adam/work/recover',{**payload,'confirmed':False})[0],400)
        code,result,_=self.request('/api/human-adam/work/recover',payload)
        self.assertEqual(code,200);self.assertTrue(result['writes_performed'])
        self.assertFalse(result['recovery']['redispatched'])
        self.assertEqual(result['operations'][0]['lifecycle_state'],'not_dispatched')
        self.assertFalse(self.request('/api/human-adam/work/recover',payload)[1]['writes_performed'])
        self.assertEqual(SyntheticClient.instances[0].sent,0)

    def test_corrupt_source_returns_unavailable_without_private_content(self):
        from app.communication.human_adam_work import normalized_request
        controller=self.manager.work_controller
        session=self.manager.active_service.hub.snapshot()
        record,_=controller.store.admit(normalized_request({'text':'PRIVATE accepted','client_message_id':'old-work-0001'}),
            {'workstream_id':self.project,'profile_id':'human_adam','thread_id':session['thread_id'],
             'connection_generation':session['connection_generation']},'old-backend',
            session_path=self.manager.active_service.hub.state_path)
        path=controller.store.repository(record['operation_id']).path
        value=json.loads(path.read_text());value['scope']['thread_id']={'raw':'PRIVATE secret'}
        path.write_text(json.dumps(value))
        code,result,_=self.lookup('&operation_id='+record['operation_id'])
        self.assertEqual(code,503);self.assertFalse(result['ok'])
        self.assertNotIn('PRIVATE',json.dumps(result));self.assertEqual(SyntheticClient.instances[0].sent,0)
