from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from app import cockpit
from app.shared_chat import SharedChat
from scripts.cockpit_quality_gate import node_binary
from tests.test_shared_chat import fixture_hub, ChatModel


class SharedChatHTTPTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)/'shared';self.tasks=[];ChatModel.instances=[];ChatModel.fail_send=False
        self.service=SharedChat(self.root,hub_factory=fixture_hub,launcher=self.tasks.append)
        patched=patch('app.cockpit_shared_chat.CHAT',self.service);patched.start();self.addCleanup(patched.stop)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),cockpit.CockpitServer().make_handler())
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.stop)
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        event_patch=patch('app.cockpit.log_cockpit_http_event')
        self.event_logger=event_patch.start();self.addCleanup(event_patch.stop)

    def stop(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)

    def request(self,path='/api/samantha-chat/action',body=None,token='',editor='http-editor-001',origin=None):
        conn=HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        headers={'X-Samantha-Client':token,'X-Samantha-Editor':editor}
        if body is not None:headers.update({'Content-Type':'application/json','Origin':origin or self.url})
        conn.request('POST' if body is not None else 'GET',path,body=json.dumps(body) if body is not None else None,headers=headers)
        response=conn.getresponse();data=response.read().decode();status=response.status;conn.close();return status,data

    def create(self):
        status,body=self.request(body={'action':'create','name':'Mint','request_id':'http-create-request','editor_id':'http-editor-001'})
        self.assertEqual(status,200);return json.loads(body)

    def test_page_and_unpaired_get_are_inert_and_device_tokens_are_not_in_urls(self):
        status,body=self.request('/samantha/');self.assertEqual(status,200);self.assertIn('Připojit telefon',body)
        status,body=self.request('/api/samantha-chat/state');self.assertTrue(json.loads(body)['needs_setup'])
        self.assertFalse(self.root.exists());self.assertEqual(self.tasks,[])
        self.assertEqual(self.request('/api/samantha-chat/state?client_token=secret')[0],400)

    def test_foreign_origin_cannot_create_or_pair_devices(self):
        status,_=self.request(body={'action':'create','name':'Mint','request_id':'bad-origin-request','editor_id':'http-editor-001'},origin='https://other.invalid')
        self.assertEqual(status,403);self.assertFalse(self.root.exists())
        self.assertEqual(self.event_logger.call_args.kwargs['event'],'origin_forbidden')

    def test_invalid_device_cannot_read_private_messages(self):
        host=self.create()
        status,body=self.request('/api/samantha-chat/state',token='0'*64)
        self.assertEqual(status,400);self.assertNotIn(host['client_token'],body)
        self.assertNotIn('thread_id',body)

    def test_concurrent_duplicate_send_submits_only_one_model_job(self):
        host=self.create();token=host['client_token'];editor='http-editor-001'
        state=self.service.execute({'action':'claim','client_token':token,'editor_id':editor,'expected_revision':0,'takeover':True})
        state=self.service.execute({'action':'draft','client_token':token,'editor_id':editor,'expected_revision':state['draft']['revision'],'text':'Souběžná otázka'})
        payload={'action':'send','client_token':token,'editor_id':editor,'expected_revision':state['draft']['revision'],'client_message_id':state['draft']['client_message_id']}
        with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda _:self.request(body=payload),range(2)))
        self.assertEqual([r[0] for r in responses],[200,200]);self.assertEqual(len(self.tasks),1)
        self.tasks.pop()();self.assertEqual(sum(c.sent for c in ChatModel.instances),1)

    def test_native_browser_timer_receivers_and_debounce(self):
        result=subprocess.run([node_binary(),str(Path(__file__).with_name('shared_chat_browser_timers.test.cjs'))],
            capture_output=True,text=True,timeout=15,check=False)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('PASS: native browser timer receiver',result.stdout)

    def test_real_frontend_two_clients_reconnect_conflict_and_lost_response(self):
        self.service.launcher=lambda fn:fn()
        result=subprocess.run([node_binary(),str(Path(__file__).with_name('shared_chat_frontend.test.cjs')),self.url],
            capture_output=True,text=True,timeout=30,check=False)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(sum(c.sent for c in ChatModel.instances),2)


if __name__=='__main__':unittest.main()
