from __future__ import annotations

import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from app.codex_appserver import AppServerTurnError, AppServerSteerRejected, CodexAppServerClient, CodexVersion, UnixSocketAppServerTransport
from app.communication.human_adam_work import WorkController, WorkReservation, WorkConflict, WorkUnavailable
from app.communication.session_hub import CanonicalSessionHub
from tests.test_human_adam_steer import SteerClient, wait_until


class InterruptClient(SteerClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stop_entered = threading.Event()
        self.stop_release = None

    def respond(self, message):
        if message['method'] != 'turn/interrupt':
            return super().respond(message)
        self.stop_entered.set()
        if self.stop_release:
            self.stop_release.wait(3)
        if self.mode == 'disconnect':
            self.transport.close()
        elif self.mode == 'crash':
            raise SystemExit('synthetic cancellation caller crash')
        elif self.mode == 'reject':
            self.transport.feed({'id': message['id'], 'error': {'code': -32600, 'message': 'PRIVATE_ERROR'}})
        else:
            if self.mode == 'completed_race':
                self.finish()
            self.transport.feed({'id': message['id'], 'result': {} if self.mode != 'bad_ack' else {'unexpected': True}})
            if self.mode == 'ok':
                self.finish_interrupted()

    def finish_interrupted(self, *, users=None):
        self.transport.feed({'method': 'turn/completed', 'params': {'threadId': self.thread,
            'turn': {'id': self.turn, 'status': 'interrupted', 'items': list(self.users if users is None else users)}}})


class WorkInterruptTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.client = InterruptClient()
        self.hub = CanonicalSessionHub(state_path=self.root/'session.json', workspace=self.root,
            client_factory=lambda: self.client, developer_instructions='Synthetic original permission',
            sandbox='read-only', sandbox_policy={'type': 'readOnly'}, approval_policy='never', reasoning_effort='low')
        self.hub.connect()
        self.project = 'project-current'
        self.controller = WorkController(self.root/'work', command_scope_guard=lambda v: v['scope']['workstream_id']==self.project)
        self.addCleanup(self.cleanup_work)
        scope = {'workstream_id':self.project, 'profile_id':'human-adam', 'thread_id':self.client.thread,
                 'connection_generation':self.hub.snapshot()['connection_generation']}
        self.request = {'text':'Original consultation', 'client_message_id':'original-stop-request-0001'}
        result = self.controller.submit(self.project, self.request,
            lambda: WorkReservation(scope,self.hub.state_path,lambda o:self.hub.send(**self.request,work_observer=o),lambda:None))
        self.identity = result['operations'][0]['operation_id']
        wait_until(lambda:self.view()['capabilities']['interrupt'])

    def cleanup_work(self):
        self.client.close(); self.controller.close()
        for h in self.controller._handles.values(): h.thread.join(3)
        self.hub.close()

    def view(self):
        return self.controller.view(self.project,identity=self.identity)['operations'][0]

    def payload(self, **change):
        return {'operation_id':self.identity, 'command_id':'ha07-'+self.identity,
                'expectedTurnId':self.client.turn, **change}

    def stop(self, **change):
        return self.controller.interrupt(self.project,self.payload(**change))

    def wait_end(self):
        self.assertTrue(self.controller._handles[self.identity].finished.wait(3))
        return self.view()

    def test_ack_is_not_stop_and_terminal_interruption_is_durable(self):
        self.client.mode='ack_only'
        stopped=self.stop()['operations'][0]
        self.assertEqual(stopped['interrupt']['state'],'accepted')
        self.assertEqual(stopped['interrupt']['outcome'],'waiting')
        self.assertEqual(stopped['lifecycle_state'],'running')
        self.assertFalse(stopped['capabilities']['interrupt']); self.assertFalse(stopped['capabilities']['steer'])
        self.client.finish_interrupted()
        end=self.wait_end()
        self.assertEqual(end['lifecycle_state'],'interrupted')
        self.assertEqual(end['interrupt']['outcome'],'interrupted')
        entry=self.hub.snapshot()['messages'][-1]
        self.assertEqual(entry['status'],'interrupted');self.assertTrue(entry['terminal_confirmed'])
        self.assertFalse(entry['delivery_confirmed']);self.assertFalse(entry['recovery_required'])
        self.assertTrue(self.hub.snapshot()['connected'])
        fresh=WorkController(self.root/'work')
        self.assertEqual(fresh.view(self.project,identity=self.identity)['operations'][0]['lifecycle_state'],'interrupted')
        self.assertEqual(self.client.count('turn/interrupt'),1);self.assertEqual(self.client.count('turn/start'),1)
        wire=next(m['params'] for m in self.client.transport.writes if m['method']=='turn/interrupt')
        self.assertEqual(wire,{'threadId':self.client.thread,'turnId':self.client.turn})

    def test_duplicate_and_concurrent_requests_dispatch_once(self):
        release=self.client.stop_release=threading.Event();self.addCleanup(release.set)
        thread=threading.Thread(target=self.stop);thread.start()
        self.assertTrue(self.client.stop_entered.wait(1))
        duplicate=self.stop();self.assertFalse(duplicate['dispatch_performed'])
        self.assertEqual(self.client.count('turn/interrupt'),1)
        release.set();thread.join(3);self.wait_end()
        self.stop();self.assertEqual(self.client.count('turn/interrupt'),1)

    def test_finish_winning_race_stays_completed(self):
        self.client.mode='completed_race';self.stop();end=self.wait_end()
        self.assertEqual(end['lifecycle_state'],'completed')
        self.assertEqual(end['interrupt']['outcome'],'completed')

    def test_rejection_and_bad_ack_never_claim_stopped(self):
        self.client.mode='reject';receipt=self.stop()['operations'][0]['interrupt']
        self.assertEqual(receipt['state'],'rejected');self.assertEqual(receipt['outcome'],'waiting')
        self.assertNotIn('PRIVATE_ERROR',json.dumps(receipt))
        self.stop();self.assertEqual(self.client.count('turn/interrupt'),1)
        self.client.finish();self.assertEqual(self.wait_end()['lifecycle_state'],'completed')

    def test_disconnect_preserves_unknown_and_restart_never_replays(self):
        self.client.mode='disconnect';self.stop();end=self.wait_end()
        self.assertEqual(end['lifecycle_state'],'unverified')
        self.assertEqual(end['interrupt']['state'],'unverified')
        self.assertEqual(self.hub.snapshot()['messages'][-1]['status'],'delivery_unknown')
        fresh=WorkController(self.root/'work',command_scope_guard=lambda _:True)
        fresh.interrupt(self.project,self.payload())
        fresh.recover(self.project,self.identity)
        self.assertEqual(self.client.count('turn/interrupt'),1);self.assertEqual(self.client.count('turn/start'),1)

    def test_wrong_scope_and_turn_do_not_interrupt_anything(self):
        with self.assertRaises(WorkConflict):self.controller.interrupt('project-other',self.payload())
        with self.assertRaises(WorkConflict):self.stop(expectedTurnId='turn-other')
        self.assertIsNone(self.view()['interrupt'])
        self.assertEqual(self.client.count('turn/interrupt'),0)
        self.client.finish();self.wait_end()

    def test_terminal_without_original_input_proof_remains_unknown(self):
        self.client.mode='ack_only';self.stop()
        # An invalid final input list cannot override the earlier correlation.
        self.client.finish_interrupted(users=[{'id':'foreign','type':'userMessage','clientId':'foreign-input'}])
        self.assertEqual(self.wait_end()['lifecycle_state'],'unverified')

    def test_missing_parent_stop_receipt_fails_closed(self):
        self.client.mode='ack_only';self.stop()
        repo=self.controller.store.repository(self.identity)
        from app.work_repository import RepositoryMutation
        repo.transact(lambda d:RepositoryMutation({k:v for k,v in d.items() if k!='_interrupt_request'},{}))
        with self.assertRaises(WorkUnavailable):self.stop()
        self.assertEqual(self.client.count('turn/interrupt'),1)
        self.client.finish_interrupted()

    def test_new_explicit_work_can_run_after_confirmed_stop(self):
        self.stop();self.wait_end()
        self.client.turn='turn-next';self.client.users=[]
        request={'text':'New explicitly submitted consultation','client_message_id':'next-stop-request-0002'}
        scope=self.controller.store.load(self.identity)['scope']
        result=self.controller.submit(self.project,request,
            lambda:WorkReservation(scope,self.hub.state_path,lambda o:self.hub.send(**request,work_observer=o),lambda:None))
        identity=result['operations'][0]['operation_id']
        wait_until(lambda:self.controller.view(self.project,identity=identity)['operations'][0]['capabilities']['interrupt'])
        self.client.finish();self.assertTrue(self.controller._handles[identity].finished.wait(3))
        self.assertEqual(self.controller.view(self.project,identity=identity)['operations'][0]['lifecycle_state'],'completed')
        self.assertEqual(self.client.count('turn/start'),2);self.assertEqual(self.client.count('turn/interrupt'),1)

    def test_uncertain_rpc_ack_is_not_replayed_even_if_parent_later_finishes(self):
        self.client.mode='bad_ack';self.stop()
        self.assertEqual(self.view()['interrupt']['state'],'unverified')
        self.stop();self.assertEqual(self.client.count('turn/interrupt'),1)
        self.client.finish_interrupted();self.assertEqual(self.wait_end()['lifecycle_state'],'interrupted')

    def test_caller_crash_leaves_nonreplayable_pending_identity(self):
        self.client.mode='crash'
        with self.assertRaises(SystemExit):self.stop()
        self.assertEqual(self.view()['interrupt']['state'],'unverified')
        fresh=WorkController(self.root/'work',command_scope_guard=lambda _:True)
        fresh.interrupt(self.project,self.payload());self.assertEqual(self.client.count('turn/interrupt'),1)
        self.client.finish_interrupted();self.wait_end()

    def test_scope_and_original_authorization_drift_reject_before_rpc(self):
        self.controller._command_scope_guard=lambda _:False
        with self.assertRaises(WorkConflict):self.stop()
        self.assertEqual(self.client.count('turn/interrupt'),0)
        self.assertIsNone(self.view()['interrupt'])
        self.controller._command_scope_guard=lambda _:True
        self.hub.model='changed-model'
        self.assertEqual(self.stop()['operations'][0]['interrupt']['state'],'rejected')
        self.assertEqual(self.client.count('turn/interrupt'),0)
        self.client.finish();self.wait_end()

    def test_explicit_recover_reads_canonical_interrupted_proof_only(self):
        self.stop();self.wait_end()
        from app.work_repository import RepositoryMutation
        def lagged(d):
            d['lifecycle_state']='unverified';d['delivery_state']='unknown'
            return RepositoryMutation(d,{})
        self.controller.store.repository(self.identity).transact(lagged)
        fresh=WorkController(self.root/'work')
        result=fresh.recover(self.project,self.identity)
        self.assertEqual(result['operations'][0]['lifecycle_state'],'interrupted')
        self.assertEqual(self.client.count('turn/interrupt'),1);self.assertEqual(self.client.count('turn/start'),1)


class ClientInterruptTests(unittest.TestCase):
    def test_real_unix_websocket_interrupt_uses_the_original_turn(self):
        from scripts.codex_sdk_socket_fixture import SyntheticSocket
        class Peer(SyntheticSocket):
            def _dispatch(self, message, send):
                method=message.get('method');params=message.get('params',{})
                self.calls.append((method,params))
                if method=='turn/start':
                    self.original=params['clientUserMessageId']
                    send({'id':message['id'],'result':{'turn':{'id':'fixture-turn'}}})
                    send({'method':'turn/started','params':{'threadId':'fixture-thread','turn':{'id':'fixture-turn'}}})
                    send({'method':'item/completed','params':{'threadId':'fixture-thread','turnId':'fixture-turn',
                        'item':{'id':'original','type':'userMessage','clientId':self.original}}})
                    self.started_turn.set()
                elif method=='turn/interrupt':
                    send({'id':message['id'],'result':{}})
                    send({'method':'turn/completed','params':{'threadId':'fixture-thread',
                        'turn':{'id':'fixture-turn','status':'interrupted','items':[
                            {'id':'original','type':'userMessage','clientId':self.original}]}}})
                return True
        with tempfile.TemporaryDirectory(prefix='ha07-',dir='/tmp') as directory:
            with Peer(Path(directory),websocket=True) as peer:
                client=CodexAppServerClient.__new__(CodexAppServerClient)
                client.server_version=CodexVersion.parse('codex-cli 0.169.0')
                client.transport=UnixSocketAppServerTransport(socket_path=peer.path,timeout=3)
                try:
                    with ThreadPoolExecutor(1) as executor:
                        future=executor.submit(client.send_text,thread_id='fixture-thread',text='Synthetic cancellation',
                            client_message_id='unix-stop-request-0001',allow_interrupt=True)
                        self.assertTrue(peer.started_turn.wait(1))
                        wait_until(lambda:client.can_interrupt_turn('fixture-thread','fixture-turn'))
                        client.interrupt_turn(thread_id='fixture-thread',expected_turn_id='fixture-turn')
                        with self.assertRaises(AppServerTurnError) as raised:future.result(3)
                        self.assertEqual(raised.exception.status,'interrupted')
                    self.assertEqual([m for m,_ in peer.calls],['turn/start','turn/interrupt'])
                    self.assertEqual(peer.calls[-1][1],{'threadId':'fixture-thread','turnId':'fixture-turn'})
                finally:client.close()

    def test_interrupt_has_independent_opt_in_and_peer_gate(self):
        for allowed,version in ((False,'0.167.0'),(True,'0.163.0'),(True,'0.167.0')):
            with self.subTest(allowed=allowed,version=version):
                client=InterruptClient(version=version)
                with ThreadPoolExecutor(1) as executor:
                    future=executor.submit(client.send_text,thread_id=client.thread,text='Original',
                        client_message_id='original-request-0001',allow_interrupt=allowed)
                    self.assertTrue(client.started.wait(1));wait_until(lambda:bool(client._inputs()._turns))
                    if allowed and version=='0.167.0':
                        # Exhausting append capacity cannot remove the ability to Stop.
                        state=next(iter(client._inputs()._turns.values()));state.commands={str(n) for n in range(64)}
                        self.assertTrue(client.can_interrupt_turn(client.thread,client.turn))
                        client.interrupt_turn(thread_id=client.thread,expected_turn_id=client.turn)
                        with self.assertRaises(AppServerTurnError):future.result(2)
                        self.assertEqual(client.count('turn/interrupt'),1)
                    else:
                        with self.assertRaises(AppServerSteerRejected):client.interrupt_turn(thread_id=client.thread,expected_turn_id=client.turn)
                        self.assertEqual(client.count('turn/interrupt'),0);client.finish();self.assertTrue(future.result(2).delivered)
                client.close()
