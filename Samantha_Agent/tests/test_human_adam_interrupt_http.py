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
