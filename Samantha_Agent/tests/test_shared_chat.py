from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4
from unittest.mock import patch, Mock

from app.shared_chat import SharedChat, ChatError
from app.communication.session_hub import CanonicalSessionHub
from tests.test_communication_session_hub import FakeClient


class ChatModel(FakeClient):
    instances = []
    def start_thread(self, **kwargs):
        self.started_kwargs = kwargs
        return uuid4().hex


def fixture_hub(root):
    return CanonicalSessionHub(state_path=root/'session.json', workspace=root/'workspace',
        client_factory=ChatModel, developer_instructions='synthetic conversation',
        sandbox='read-only', sandbox_policy={'type':'readOnly','networkAccess':False},
        approval_policy='never', reasoning_effort='high', model='fixture-model')


class SharedChatTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)/'chat';self.now=1000
        self.tasks=[];ChatModel.instances=[];ChatModel.fail_send=False
        self.service=SharedChat(self.root,hub_factory=fixture_hub,launcher=self.tasks.append,clock=lambda:self.now)
        self.host=self.action('create',name='Mint',request_id='create-request-001')
        self.token=self.host['client_token'];self.editor='mint-editor-001'

    def action(self, action, token=None, editor='mint-editor-001', **payload):
        return self.service.execute({'action':action,'editor_id':editor,
            **({'client_token':token} if token else {}),**payload})

    def pair(self):
        state=self.action('pair',self.token)
        return self.action('join',name='iPhone',code=state['pair_code'],request_id='join-request-001',editor='phone-editor-001')

    def draft(self, text='Otázka pro Samanthu', token=None, editor=None):
        token=token or self.token;editor=editor or self.editor
        state=self.service.status(token,editor)
        state=self.action('claim',token,editor,expected_revision=state['draft']['revision'],takeover=True)
        return self.action('draft',token,editor,expected_revision=state['draft']['revision'],text=text)

    def test_get_pairing_and_drafts_never_start_a_model(self):
        phone=self.pair();self.draft(token=phone['client_token'],editor='phone-editor-001')
        self.assertEqual(self.service.status(self.token,self.editor)['draft']['text'],'Otázka pro Samanthu')
        self.assertEqual(self.tasks,[]);self.assertEqual(ChatModel.instances,[])
        self.assertEqual(list(self.root.glob('*/session.json')),[])

    def test_registration_response_can_be_recovered_with_same_request(self):
        duplicate=self.action('create',name='Mint',request_id='create-request-001')
        self.assertEqual(duplicate['client_token'],self.token)
        self.assertEqual(len(self.service._read()['rooms']),1)

    def test_join_code_is_single_use_expires_and_failed_attempts_are_bounded(self):
        state=self.action('pair',self.token);code=state['pair_code']
        self.now+=601
        self.assertFalse(self.action('join',name='iPhone',code=code,request_id='expired-request-001')['ok'])
        phone=self.pair()
        self.assertEqual(phone['room_id'],self.host['room_id'])
        self.assertFalse(self.action('join',name='Other',code=code,request_id='used-request-001')['ok'])
        for n in range(8):self.action('join',name='Other',code=code,request_id=f'bad-request-{n:03}')
        with self.assertRaises(ChatError):self.action('join',name='Other',code=code,request_id='limited-request-001')

    def test_nonhost_cannot_share_pair_code_or_generate_one(self):
        phone=self.pair();self.assertEqual(phone['pair_code'],'')
        with self.assertRaises(ChatError):self.action('pair',phone['client_token'])

    def test_other_room_and_invalid_device_cannot_read_or_edit_conversation(self):
        self.draft('Soukromá syntetická otázka')
        other=self.action('create',name='Mac',request_id='create-another-001')
        self.assertNotEqual(other['room_id'],self.host['room_id'])
        self.assertEqual(other['draft']['text'],'')
        with self.assertRaises(ChatError):self.service.status('0'*64,self.editor)
        with self.assertRaises(ChatError):self.action('draft','0'*64,expected_revision=0,text='overwrite')

    def test_stale_phone_cannot_overwrite_a_manual_mint_edit(self):
        phone=self.pair();token=phone['client_token'];editor='phone-editor-001'
        original=self.draft('Nadiktovaný text',token,editor)
        self.draft('Ručně opravený text na Mintu')
        with self.assertRaises(ChatError):self.action('draft',token,editor,expected_revision=original['draft']['revision'],text='Opožděný diktát')
        self.assertEqual(self.service.status(token,editor)['draft']['text'],'Ručně opravený text na Mintu')

    def test_lease_expiry_does_not_discard_text(self):
        before=self.draft();self.now+=121
        state=self.service.status(self.token,self.editor);self.assertFalse(state['draft']['can_edit'])
        self.assertEqual(state['draft']['text'],before['draft']['text'])
        with self.assertRaises(ChatError):self.action('draft',self.token,expected_revision=state['draft']['revision'],text='Late')

    def test_monitor_send_keeps_phone_as_writer_and_next_draft_survives_finish(self):
        phone=self.pair();token=phone['client_token'];editor='phone-editor-001'
        state=self.draft('Phone draft',token,editor)
        sent=self.action('send',self.token,expected_revision=state['draft']['revision'],client_message_id=state['draft']['client_message_id'])
        self.assertFalse(sent['draft']['can_edit'])
        state=self.service.status(token,editor)
        self.assertTrue(state['draft']['is_writer']);self.assertTrue(state['draft']['can_edit'])
        state=self.action('draft',token,editor,expected_revision=state['draft']['revision'],text='Next phone draft')
        self.tasks.pop()()
        state=self.service.status(token,editor)
        self.assertEqual(state['draft']['text'],'Next phone draft')
        self.assertEqual(state['messages'][0]['user_text'],'Phone draft')
        self.assertTrue(state['draft']['can_edit'])
        self.assertEqual(ChatModel.instances[0].sent,1)

    def test_active_writer_renewal_never_takes_over_another_device(self):
        phone=self.pair();token=phone['client_token'];editor='phone-editor-001'
        state=self.draft('Phone draft',token,editor)
        self.now+=60
        state=self.service.status(token,editor)
        self.assertEqual(state['draft']['lease_remaining_ms'],60000)
        renewed=self.action('claim',token,editor,expected_revision=state['draft']['revision'],takeover=False)
        self.assertEqual(renewed['draft']['lease_remaining_ms'],120000)
        self.now+=70
        self.assertTrue(self.service.status(token,editor)['draft']['can_edit'])
        self.draft('Monitor correction')
        foreign=self.service.status(token,editor)
        self.assertFalse(foreign['draft']['is_writer'])
        before=self.root.joinpath('rooms.json').read_bytes()
        with self.assertRaises(ChatError):
            self.action('claim',token,editor,expected_revision=foreign['draft']['revision'],takeover=False)
        self.assertEqual(before,self.root.joinpath('rooms.json').read_bytes())
        self.assertEqual(self.service.status(token,editor)['draft']['text'],'Monitor correction')

    def test_same_send_from_two_devices_has_one_turn_and_one_shared_answer(self):
        phone=self.pair();state=self.draft();draft=state['draft']
        payload={'expected_revision':draft['revision'],'client_message_id':draft['client_message_id']}
        self.action('send',self.token,**payload)
        self.action('send',phone['client_token'],'phone-editor-001',**payload)
        self.assertEqual(len(self.tasks),1)
        self.tasks.pop()()
        self.action('send',self.token,**payload)
        host=self.service.status(self.token,self.editor);mobile=self.service.status(phone['client_token'],'phone-editor-001')
        self.assertEqual(host['messages'],mobile['messages']);self.assertFalse(host['busy'])
        self.assertEqual(host['messages'][0]['answer'],'Hotovo')
        self.assertEqual(ChatModel.instances[0].sent,1)
        self.assertEqual(ChatModel.instances[0].sent_texts,['Otázka pro Samanthu'])

    def test_restart_keeps_completed_history_and_next_turn_resumes_original_thread(self):
        state=self.draft();self.action('send',self.token,expected_revision=state['draft']['revision'],client_message_id=state['draft']['client_message_id']);self.tasks.pop()()
        first=json.loads(next(self.root.glob('*/session.json')).read_text())['thread_id']
        self.service=SharedChat(self.root,hub_factory=fixture_hub,launcher=self.tasks.append,clock=lambda:self.now)
        before=self.root.joinpath('rooms.json').read_bytes()
        self.assertEqual(self.service.status(self.token,self.editor)['messages'][0]['answer'],'Hotovo')
        self.assertEqual(before,self.root.joinpath('rooms.json').read_bytes())
        state=self.draft('Další otázka');self.action('send',self.token,expected_revision=state['draft']['revision'],client_message_id=state['draft']['client_message_id']);self.tasks.pop()()
        self.assertEqual(ChatModel.instances[-1].resumed_thread_id,first)

    def test_restart_during_uncertain_delivery_never_replays_or_starts_new_turn(self):
        state=self.draft();payload={'expected_revision':state['draft']['revision'],'client_message_id':state['draft']['client_message_id']}
        self.action('send',self.token,**payload)
        service=SharedChat(self.root,hub_factory=Mock(side_effect=AssertionError('no retry')))
        self.assertEqual(service.status(self.token,self.editor)['submission']['status'],'delivery_unknown')
        service.execute({'action':'send','client_token':self.token,'editor_id':self.editor,**payload})
        self.assertEqual(len(self.tasks),1)
        self.service=service
        newer=self.draft('Další otázka')
        with self.assertRaises(ChatError):self.action('send',self.token,expected_revision=newer['draft']['revision'],client_message_id=newer['draft']['client_message_id'])

    def test_provider_error_is_redacted_and_cannot_be_resent(self):
        ChatModel.fail_send=True
        state=self.draft();payload={'expected_revision':state['draft']['revision'],'client_message_id':state['draft']['client_message_id']}
        self.action('send',self.token,**payload);self.tasks.pop()()
        result=self.action('send',self.token,**payload)
        self.assertEqual(result['submission']['status'],'delivery_unknown');self.assertEqual(ChatModel.instances[0].sent,1)
        self.assertNotIn('ambiguous',json.dumps(result))

    def test_failed_preflight_restores_draft_without_any_model_turn(self):
        self.service.hub_factory=Mock(side_effect=ValueError('PRIVATE provider credential'))
        state=self.draft();self.action('send',self.token,expected_revision=state['draft']['revision'],client_message_id=state['draft']['client_message_id']);self.tasks.pop()()
        state=self.service.status(self.token,self.editor)
        self.assertEqual(state['submission']['status'],'not_sent');self.assertEqual(state['draft']['text'],'Otázka pro Samanthu')
        self.assertNotIn('PRIVATE',json.dumps(state));self.assertEqual(ChatModel.instances,[])

    def test_unsupported_actions_or_payload_paths_do_not_mutate_any_state(self):
        before=self.root.joinpath('rooms.json').read_bytes()
        for payload in ({'action':'delete','editor_id':self.editor},
                        {'action':'pair','editor_id':self.editor,'client_token':self.token,'root':'/other'}):
            with self.assertRaises(ChatError):self.service.execute(payload)
        self.assertEqual(before,self.root.joinpath('rooms.json').read_bytes())


if __name__=='__main__':unittest.main()
