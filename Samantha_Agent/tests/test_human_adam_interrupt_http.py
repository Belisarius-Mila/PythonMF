import unittest
from unittest.mock import patch

from tests.test_human_adam_interrupt import InterruptClient
from tests import test_human_adam_steer_http as steer_http


class InterruptHTTPTests(unittest.TestCase):
    request = steer_http.SteerHTTPTests.request
    shutdown = steer_http.SteerHTTPTests.shutdown
    join_workers = steer_http.SteerHTTPTests.join_workers

    def setUp(self):
        with patch('tests.test_human_adam_steer_http.SteerClient', InterruptClient):
            steer_http.SteerHTTPTests.setUp(self)

    def payload(self, **change):
        return {'workstream_id': self.project, 'operation_id': self.identity, 'command_id': 'ha07-'+self.identity,
                'expectedTurnId': self.client.turn, 'confirmed': True, **change}

    def test_stop_http_origin_confirmation_and_exact_target(self):
        path='/api/human-adam/work/interrupt'
        for change in ({'confirmed':False},{'model':'other'},{'expectedTurnId':None},{'write_intent':True}):
            self.assertEqual(self.request(path,self.payload(**change))[0],400)
        self.assertEqual(self.request(path,self.payload(),origin='https://foreign.example')[0],403)
        self.assertEqual(self.client.count('turn/interrupt'),0)
        code,result,_=self.request(path,self.payload())
        self.assertEqual(code,200);self.assertTrue(result['ok'])
        self.assertTrue(self.manager.work_controller._handles[self.identity].finished.wait(3))
        code,result,headers=self.request(f'/api/human-adam/work?workstream_id={self.project}&operation_id={self.identity}')
        self.assertEqual(result['operations'][0]['lifecycle_state'],'interrupted')
        self.assertIn('no-store',headers['Cache-Control'])
        duplicate=self.request(path,self.payload())[1]
        self.assertFalse(duplicate['dispatch_performed']);self.assertEqual(self.client.count('turn/interrupt'),1)
        self.assertEqual(self.client.count('turn/start'),1)

    def test_interrupted_result_never_enters_automatic_completion(self):
        with patch.object(self.manager,'_complete_successful_turn',side_effect=AssertionError('Partial result must not be completed')):
            self.request('/api/human-adam/work/interrupt',self.payload())
            self.assertTrue(self.manager.work_controller._handles[self.identity].finished.wait(3))
        result=self.manager.work_controller._handles[self.identity].response
        self.assertEqual(result['automatic_completion'],{'state':'interrupted','attempted':False})
        self.assertEqual(result['automatic_operation'],{'state':'interrupted','attempted':False})
        self.assertIsNone(self.manager.completion_job_store.load())

    def test_writable_interruption_keeps_changes_and_owned_wip(self):
        # Finish the read-only setup turn, then explicitly admit a writable one.
        self.client.finish()
        self.assertTrue(self.manager.work_controller._handles[self.identity].finished.wait(3))
        service=self.manager.profiles['human_adam']['service']
        workspace=service.workspace
        self.client.turn='turn-writable';self.client.users=[]
        code,result,_=self.request('/api/human-adam/work/start',{'message':'Synthetic authorized development',
            'client_message_id':'writable-stop-request-0002','workstream_id':self.project,'write_intent':True,'confirmed':True})
        self.assertEqual(code,202)
        identity=result['operations'][0]['operation_id']
        from tests.test_human_adam_steer import wait_until
        wait_until(lambda:self.manager.work_controller.view(self.project,identity=identity)['operations'][0]['capabilities']['interrupt'])
        workspace.dirty=True
        self.assertTrue(self.manager.deferred_integration_store.path.exists())
        with patch.object(self.manager,'_complete_successful_turn',side_effect=AssertionError('No partial checkpoint')):
            code,result,_=self.request('/api/human-adam/work/interrupt',{'workstream_id':self.project,'operation_id':identity,
                'command_id':'ha07-'+identity,'expectedTurnId':self.client.turn,'confirmed':True})
            self.assertEqual(code,200)
            self.assertTrue(self.manager.work_controller._handles[identity].finished.wait(3))
        self.assertTrue(workspace.dirty)
        self.assertTrue(self.manager.deferred_integration_store.path.exists())
        self.assertEqual(self.manager.work_controller.view(self.project,identity=identity)['operations'][0]['lifecycle_state'],'interrupted')
        self.assertIsNone(self.manager.completion_job_store.load())

    def stopped_writable(self):
        self.client.finish()
        self.assertTrue(self.manager.work_controller._handles[self.identity].finished.wait(3))
        workspace=self.manager.profiles['human_adam']['service'].workspace
        self.client.turn='resume-parent-turn';self.client.users=[]
        parent_client='resume-parent-request-0001'
        code,result,_=self.request('/api/human-adam/work/start',{'message':'Synthetic development',
            'client_message_id':parent_client,'workstream_id':self.project,'write_intent':True,'confirmed':True})
        self.assertEqual(code,202);identity=result['operations'][0]['operation_id']
        from tests.test_human_adam_steer import wait_until
        wait_until(lambda:self.manager.work_controller.view(self.project,identity=identity)['operations'][0]['capabilities']['interrupt'])
        workspace.dirty=True
        self.request('/api/human-adam/work/interrupt',{'workstream_id':self.project,'operation_id':identity,
            'command_id':'ha07-'+identity,'expectedTurnId':self.client.turn,'confirmed':True})
        self.assertTrue(self.manager.work_controller._handles[identity].finished.wait(3))
        return workspace,identity,parent_client

    def continue_work(self,parent_client,client_id='resume-child-request-0002',**changes):
        self.client.turn='turn-'+client_id;self.client.users=[]
        payload={'message':'Continue the same synthetic work','client_message_id':client_id,
            'workstream_id':self.project,'write_intent':True,'confirmed':True,
            'continue_from_client_message_id':parent_client,**changes}
        code,result,_=self.request('/api/human-adam/work/start',payload)
        return code,result,payload

    def test_writable_stop_continue_stop_is_explicit_and_preserves_parent_chain(self):
        workspace,parent,parent_client=self.stopped_writable()
        self.assertEqual(self.manager.status()['interrupted_work_continuation']['client_message_id'],parent_client)
        audit=self.manager.pending_integration_status()
        self.assertTrue(audit['can_continue']);self.assertFalse(audit['can_recover'])
        code,result,payload=self.continue_work(parent_client)
        self.assertEqual(code,202);child=result['operations'][0]['operation_id']
        from tests.test_human_adam_steer import wait_until
        wait_until(lambda:self.manager.work_controller.view(self.project,identity=child)['operations'][0]['capabilities']['interrupt'])
        self.assertEqual(self.manager.work_controller.store.load(child)['continuation_of'],parent)
        self.assertEqual(self.manager.deferred_integration_store.load().client_message_id,payload['client_message_id'])
        before=self.client.count('turn/start')
        code,duplicate,_=self.request('/api/human-adam/work/start',payload)
        self.assertTrue(duplicate['duplicate_prevented']);self.assertEqual(self.client.count('turn/start'),before)
        self.request('/api/human-adam/work/interrupt',{'workstream_id':self.project,'operation_id':child,
            'command_id':'ha07-'+child,'expectedTurnId':self.client.turn,'confirmed':True})
        self.assertTrue(self.manager.work_controller._handles[child].finished.wait(3))
        self.assertTrue(workspace.dirty)
        self.assertEqual(self.manager.status()['interrupted_work_continuation']['client_message_id'],payload['client_message_id'])
        self.assertEqual(self.manager.work_controller.store.load(parent)['lifecycle_state'],'interrupted')
        self.assertIsNone(self.manager.completion_job_store.load())

    def test_resume_rejects_foreign_parent_missing_authorization_and_changed_wip(self):
        workspace,parent,parent_client=self.stopped_writable()
        before=self.client.count('turn/start')
        for i,kwargs in enumerate(({'continue_from_client_message_id':'foreign-parent-0001'},
                                    {'write_intent':False})):
            code,result,_=self.continue_work(parent_client,'bad-resume-request-000'+str(i),**kwargs)
            if code==202:
                identity=result['operations'][0]['operation_id']
                self.assertTrue(self.manager.work_controller._handles[identity].finished.wait(3))
                self.assertEqual(self.manager.work_controller.store.load(identity)['lifecycle_state'],'not_dispatched')
            else:self.assertEqual(code,400)
        original=workspace.status
        with patch.object(workspace,'status',side_effect=lambda:{**original(),'changes':[{'path':'foreign.py','status':' M'}]}):
            self.assertIsNone(self.manager.status()['interrupted_work_continuation'])
            code,result,_=self.continue_work(parent_client,'changed-wip-request-0003')
            identity=result['operations'][0]['operation_id']
            self.assertTrue(self.manager.work_controller._handles[identity].finished.wait(3))
        self.assertEqual(self.client.count('turn/start'),before)
        self.assertEqual(self.manager.deferred_integration_store.load().client_message_id,parent_client)

    def test_failure_before_dispatch_restores_stopped_owner(self):
        workspace,parent,parent_client=self.stopped_writable()
        service=self.manager.profiles['human_adam']['service']
        from app.codex_appserver import AppServerError
        before=self.manager.deferred_integration_store.path.read_bytes()
        with patch.object(service,'send',side_effect=AppServerError('Synthetic pre-dispatch failure')):
            code,result,_=self.continue_work(parent_client)
            child=result['operations'][0]['operation_id']
            self.assertTrue(self.manager.work_controller._handles[child].finished.wait(3))
        self.assertEqual(self.manager.work_controller.store.load(child)['lifecycle_state'],'not_dispatched')
        self.assertEqual(self.manager.deferred_integration_store.path.read_bytes(),before)
        self.assertTrue(workspace.dirty)
        self.assertEqual(self.manager.status()['interrupted_work_continuation']['client_message_id'],parent_client)

    def test_resume_keeps_old_workspace_when_main_advanced_and_defers_integration(self):
        workspace,parent,parent_client=self.stopped_writable();workspace.source_ahead=True
        self.assertTrue(self.manager.status()['interrupted_work_continuation']['integration_deferred'])
        previous_sync=workspace.sync_count
        code,result,_=self.continue_work(parent_client)
        child=result['operations'][0]['operation_id']
        from tests.test_human_adam_steer import wait_until
        wait_until(lambda:self.manager.work_controller.view(self.project,identity=child)['operations'][0]['capabilities']['interrupt'])
        self.assertEqual(workspace.sync_count,previous_sync)
        self.assertTrue(self.manager.deferred_integration_store.load().integration_deferred)
        self.request('/api/human-adam/work/interrupt',{'workstream_id':self.project,'operation_id':child,
            'command_id':'ha07-'+child,'expectedTurnId':self.client.turn,'confirmed':True})
        self.assertTrue(self.manager.work_controller._handles[child].finished.wait(3))

    def test_reconnect_stopped_dirty_workspace_without_sync_or_new_model_turn(self):
        workspace,parent,parent_client=self.stopped_writable();workspace.source_ahead=True
        service=self.manager.profiles['human_adam']['service']
        service.hub.close()
        self.assertFalse(service.hub.snapshot()['connected'])
        self.client=InterruptClient();self.addCleanup(self.client.close)
        previous_sync=workspace.sync_count
        result=self.manager.connect()
        self.assertTrue(result['ok']);self.assertFalse(result['workspace_synced'])
        self.assertEqual(workspace.sync_count,previous_sync);self.assertTrue(workspace.dirty)
        self.assertEqual(self.client.count('turn/start'),0)
        self.assertEqual(self.manager.status()['interrupted_work_continuation']['client_message_id'],parent_client)

    def test_uncertain_parent_is_not_eligible_for_continuation(self):
        workspace,parent,parent_client=self.stopped_writable()
        hub=self.manager.profiles['human_adam']['service'].hub
        with hub._state_lock:
            hub._state['messages'][-1]['recovery_required']=True
            hub._save_locked()
        self.assertIsNone(self.manager.status()['interrupted_work_continuation'])
        before=self.client.count('turn/start')
        code,result,_=self.continue_work(parent_client)
        self.assertEqual(code,409);self.assertEqual(self.client.count('turn/start'),before)
        self.assertEqual(self.manager.deferred_integration_store.load().client_message_id,parent_client)
