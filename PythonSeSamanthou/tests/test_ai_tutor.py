"""No network calls or personal data. Exercise API boundaries and worker isolation."""
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ai_tutor as tutor
import python_se_samanthou as app

CONTEXT = {'title': 'Test', 'source': 'print(2)', 'notes': 'Chci porozumět.', 'result': None}


class TutorTests(unittest.TestCase):
    def call(self, data):
        with patch('ai_tutor.request.build_opener') as build:
            build.return_value.open.return_value = io.BytesIO(json.dumps(data).encode())
            answer = tutor.ask_tutor('test-key', tutor.DEFAULT_MODEL, [tutor.context_message(CONTEXT, 'Proč?')])
            req = build.return_value.open.call_args.args[0]
            return answer, req

    def test_request_and_mixed_output(self):
        answer, req = self.call({'status': 'completed', 'output': [
            {'type': 'reasoning'}, {'type': 'message', 'content': [{'type': 'output_text', 'text': 'První'}]},
            {'type': 'message', 'content': [{'type': 'output_text', 'text': 'Druhý'}]}]})
        self.assertEqual(answer, 'První\n\nDruhý')
        self.assertEqual(req.full_url, tutor.ENDPOINT)
        payload = json.loads(req.data)
        self.assertFalse(payload['store'])
        self.assertNotIn('tools', payload)
        self.assertIn('print(2)', payload['input'][0]['content'])
        self.assertNotIn('test-key', req.data.decode())
        self.assertEqual(req.get_header('Authorization'), 'Bearer test-key')

    def test_partial_refusal_and_redaction(self):
        answer, _ = self.call({'status': 'incomplete', 'output': [{'type': 'message', 'content': [
            {'type': 'refusal', 'refusal': 'Odmítnuto test-key'}]}]})
        self.assertIn('před dokončením', answer)
        self.assertNotIn('test-key', answer)

    def test_empty_failed_and_malformed(self):
        for data in ({'status': 'completed', 'output': []}, {'status': 'failed'}, [],
                     {'status': 'completed', 'output': [None]}):
            with self.subTest(data=data), self.assertRaises(tutor.TutorError):
                self.call(data)

    def test_limits_and_settings(self):
        for key, model in (('', 'm'), ('bad\nkey', 'm'), ('key', '../../path')):
            with self.assertRaises(tutor.TutorError):
                tutor.validate_settings(key, model)
        for context, question in ((CONTEXT, ''), (CONTEXT, 'x'*4001),
                                   (dict(CONTEXT, source='x'*50001), 'proč')):
            with self.assertRaises(tutor.TutorError):
                tutor.context_message(context, question)

    def test_result_is_context_data(self):
        result = {'output': '2\n', 'error': None, 'variables': {}, 'commands': []}
        message = tutor.context_message(dict(CONTEXT, result=result), 'Vysvětli')
        self.assertIn('2\\n', message['content'])

    def test_http_errors_do_not_echo_body_and_do_not_retry(self):
        for code in (401, 403, 404, 429, 500):
            with patch('ai_tutor.request.build_opener') as build:
                build.return_value.open.side_effect = HTTPError(tutor.ENDPOINT, code, 'private test-key', {}, io.BytesIO(b'private test-key'))
                with self.assertRaises(tutor.TutorError) as caught:
                    tutor.ask_tutor('test-key', tutor.DEFAULT_MODEL, [])
                self.assertNotIn('test-key', str(caught.exception))
                self.assertEqual(build.return_value.open.call_count, 1)

    def test_network_timeout_invalid_json_and_size(self):
        for failure in (URLError('private test-key'), TimeoutError()):
            with patch('ai_tutor.request.build_opener') as build:
                build.return_value.open.side_effect = failure
                with self.assertRaises(tutor.TutorError):
                    tutor.ask_tutor('test-key', tutor.DEFAULT_MODEL, [])
        for raw in (b'{', b'x'*(tutor.MAX_REPLY_BYTES+1)):
            with patch('ai_tutor.request.build_opener') as build:
                build.return_value.open.return_value = io.BytesIO(raw)
                with self.assertRaises(tutor.TutorError):
                    tutor.ask_tutor('test-key', tutor.DEFAULT_MODEL, [])

    def test_redirect_never_forwards_key(self):
        with self.assertRaises(tutor.TutorError):
            tutor.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.com')

    def test_worker_does_not_inherit_api_keys(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic-secret', 'CODEX_API_KEY': 'synthetic-secret'}):
            result = app.run_code('import os\nprint("OPENAI_API_KEY" in os.environ)\nprint("CODEX_API_KEY" in os.environ)')
        self.assertIsNone(result['error'])
        self.assertEqual(result['output'], 'False\nFalse\n')


if __name__ == '__main__':
    unittest.main()
