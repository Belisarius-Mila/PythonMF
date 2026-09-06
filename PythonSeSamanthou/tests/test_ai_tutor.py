"""Codex transport tests: no live accounts/network or personal files."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ai_tutor as tutor
import python_se_samanthou as app

CONTEXT = {'title': 'Test', 'source': 'print(2)', 'notes': 'Chci porozumět.', 'result': None}


def events(text='Vysvětlení', completed=True):
    data = [{'type': 'thread.started', 'thread_id': 'synthetic'},
            {'type': 'item.completed', 'item': {'type': 'reasoning', 'text': 'internal'}},
            {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': text}}]
    if completed:
        data.append({'type': 'turn.completed'})
    return '\n'.join(json.dumps(x) for x in data)


class TutorTests(unittest.TestCase):
    def test_context_and_limits(self):
        m = tutor.context_message(CONTEXT, 'Proč?')
        self.assertIn('print(2)', m['content'])
        for context, question in ((CONTEXT, ''), (CONTEXT, 'x'*4001),
                                   (dict(CONTEXT, source='x'*50001), 'proč')):
            with self.assertRaises(tutor.TutorError):
                tutor.context_message(context, question)
        result = {'output': '2\n', 'error': None}
        self.assertIn('2\\n', tutor.context_message(dict(CONTEXT, result=result), 'Proč')['content'])

    def test_missing_binary(self):
        with patch('ai_tutor.shutil.which', return_value=None), patch('ai_tutor.Path.is_file', return_value=False):
            with self.assertRaisesRegex(tutor.TutorError, 'nainstalovaný'):
                tutor.find_codex()

    def test_saved_chatgpt_auth(self):
        with patch('ai_tutor.find_codex', return_value='/fake/codex'), patch('ai_tutor.run_process') as run:
            run.side_effect = [(0, 'codex-cli 0.153.0', ''), (0, '', 'Logged in using ChatGPT')]
            self.assertEqual(tutor.check_codex(), '/fake/codex')
            self.assertEqual(run.call_args.args[0], ['/fake/codex', 'login', 'status'])

    def test_api_unknown_and_logged_out_block_without_logout_or_exec(self):
        for code, message in ((0, 'Logged in using an API key: private'), (1, 'Not logged in'), (0, 'Unknown')):
            with self.subTest(message=message), patch('ai_tutor.find_codex', return_value='/fake/codex'), patch('ai_tutor.run_process') as run:
                run.side_effect = [(0, 'codex-cli 0.153.0', ''), (code, '', message)]
                with self.assertRaises(tutor.TutorError) as caught:
                    tutor.ask_tutor([])
                self.assertNotIn('private', str(caught.exception))
                self.assertEqual(run.call_count, 2)
                self.assertNotIn('forced_login_method', str(run.call_args))

    def test_old_or_unknown_version_blocks(self):
        for version in ('codex-cli 0.140.0', 'not-codex'):
            with patch('ai_tutor.find_codex', return_value='/fake/codex'), patch('ai_tutor.run_process', return_value=(0, version, '')) as run:
                with self.assertRaisesRegex(tutor.TutorError, 'Aktualizuj'):
                    tutor.check_codex()
                self.assertEqual(run.call_count, 1)

    def test_no_api_environment_or_parent_agent_configuration(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'secret', 'CODEX_API_KEY': 'secret',
                'OPENAI_BASE_URL': 'https://example.com', 'CODEX_THREAD_ID': 'parent',
                'CODEX_HOME': '/test/auth', 'PATH': '/bin', 'LC_ALL': 'C.UTF-8'}, clear=True):
            self.assertEqual(tutor.codex_environment(), {'CODEX_HOME': '/test/auth', 'PATH': '/bin', 'LC_ALL': 'C.UTF-8'})

    def test_request_uses_stdin_chatgpt_and_restricted_tools(self):
        m = tutor.context_message(CONTEXT, 'Proč?')
        with patch('ai_tutor.check_codex', return_value='/fake/codex'), patch('ai_tutor.run_process', return_value=(0, events(), '')) as run:
            self.assertEqual(tutor.ask_tutor([m]), 'Vysvětlení')
            args, prompt = run.call_args.args
            self.assertIn('forced_login_method="chatgpt"', args)
            self.assertIn('--ignore-user-config', args)
            self.assertIn('--ephemeral', args)
            self.assertIn('read-only', args)
            self.assertIn('shell_tool', args)
            self.assertIn('web_search="disabled"', args)
            self.assertNotIn('print(2)', str(args))
            self.assertIn('print(2)', prompt)
            self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', args)

    def test_error_limit_and_auth_are_redacted_no_partial_success(self):
        for detail, expected in (('usage_limit_reached private-token', 'limit'),
                                  ('401 unauthorized private-token', 'Přihlášení'),
                                  ('network error private-token', 'nedokončil')):
            with self.assertRaisesRegex(tutor.TutorError, expected) as caught:
                tutor.parse_answer(1, events(completed=False), detail)
            self.assertNotIn('private-token', str(caught.exception))
        with self.assertRaises(tutor.TutorError):
            tutor.parse_answer(0, events(completed=False), '')
        with self.assertRaises(tutor.TutorError):
            tutor.parse_answer(0, events()+'\n'+json.dumps({'type':'turn.failed'}), '')

    def test_malformed_and_empty(self):
        for out in ('', 'not-json', '[]', events(text='')):
            with self.assertRaises(tutor.TutorError):
                tutor.parse_answer(0, out, '')

    def test_login_is_explicit_and_rechecked(self):
        with patch('ai_tutor.find_codex', return_value='/fake/codex'), patch('ai_tutor.run_process', return_value=(0, '', '')), patch('ai_tutor.check_codex') as check:
            self.assertIn('Přihlášeno', tutor.login_codex())
            check.assert_called_once()

    def test_actual_process_unicode_no_shell_and_private_cwd(self):
        code = 'import sys,os; print(sys.stdin.read()); print(os.getcwd()); print("OPENAI_API_KEY" in os.environ)'
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'secret'}):
            status, out, err = tutor.run_process([sys.executable, '-c', code], 'Míla $(echo NO)')
        self.assertEqual(status, 0)
        self.assertIn('Míla $(echo NO)', out)
        self.assertIn('samantha-codex-', out)
        self.assertTrue(out.rstrip().endswith('False'))

    def test_timeout_cancel_and_output_limit(self):
        with self.assertRaises(tutor.TutorError):
            tutor.run_process([sys.executable, '-c', 'import time; time.sleep(30)'], timeout=.15)
        cancel = threading.Event()
        cancel.set()
        with self.assertRaisesRegex(tutor.TutorError, 'zastaven'):
            tutor.run_process([sys.executable, '-c', 'import time; time.sleep(30)'], cancel=cancel)
        with self.assertRaisesRegex(tutor.TutorError, 'mnoho dat'):
            tutor.run_process([sys.executable, '-c', 'print("x"*2000001)'])

    def test_cancellation_stops_descendants(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp)/'child-ran'
            child = 'import time; from pathlib import Path; time.sleep(1); Path('+repr(str(marker))+').write_text("bad")'
            parent = 'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",'+repr(child)+']); time.sleep(30)'
            with self.assertRaises(tutor.TutorError):
                tutor.run_process([sys.executable, '-c', parent], timeout=.4)
            time.sleep(1.2)
            self.assertFalse(marker.exists())

    def test_worker_does_not_inherit_api_keys(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic-secret', 'CODEX_API_KEY': 'synthetic-secret'}):
            result = app.run_code('import os\nprint("OPENAI_API_KEY" in os.environ)\nprint("CODEX_API_KEY" in os.environ)')
        self.assertIsNone(result['error'])
        self.assertEqual(result['output'], 'False\nFalse\n')


if __name__ == '__main__':
    unittest.main()
