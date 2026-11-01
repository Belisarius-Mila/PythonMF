import os
import subprocess
import unittest
from unittest.mock import Mock, patch
from xml.etree import ElementTree

from app.speech.azure_tts_mp3 import AzureTtsError, CharacterBudget, ssml_parts, synthesize_azure_tts_mp3_sync


class AzureSpeechTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'AZURE_SPEECH_KEY': 'fake-test-key-' + 'a'*32,
                                          'AZURE_SPEECH_REGION': 'germanywestcentral'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def call(self, runner, budget=None, text='A & B < C'):
        with patch('app.speech.azure_tts_mp3.dotenv_values', return_value={}):
            return synthesize_azure_tts_mp3_sync(text, voice='en-US-AndrewNeural',
                                                budget=budget or CharacterBudget(), runner=runner)

    def test_exact_text_escape_and_billable_body(self):
        text = ' A & B < C!\nŽluťoučký '
        xml, count = ssml_parts(text, 'cs-CZ-VlastaNeural')
        root = ElementTree.fromstring(xml)
        self.assertEqual(''.join(root.itertext()), text)
        self.assertEqual(count, len(text) + 31 + 4 + 3)
        self.assertIn('rate="-10%"', xml)

    def test_success_keeps_credentials_out_of_argv_and_uses_one_post(self):
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, b'ID3audio\n200', b''))
        budget = CharacterBudget()
        self.assertEqual(self.call(runner, budget), b'ID3audio')
        runner.assert_called_once()
        argv = runner.call_args.args[0]
        self.assertNotIn(os.environ['AZURE_SPEECH_KEY'], ' '.join(argv))
        self.assertNotIn('--location', argv)
        self.assertNotIn('--retry', argv)
        config = runner.call_args.kwargs['input'].decode()
        self.assertIn(os.environ['AZURE_SPEECH_KEY'], config)
        self.assertIn('A &amp; B &lt; C', config)
        self.assertIn('audio-24khz-48kbitrate-mono-mp3', config)
        self.assertEqual(budget.reserved, ssml_parts('A & B < C', 'en-US-AndrewNeural')[1])

    def test_http_failure_is_redacted_never_retried_and_not_refunded(self):
        runner = Mock(return_value=subprocess.CompletedProcess([], 0,
                      os.environ['AZURE_SPEECH_KEY'].encode()+b'\n429', b''))
        budget = CharacterBudget()
        with self.assertRaisesRegex(AzureTtsError, 'HTTP 429') as error:
            self.call(runner, budget)
        self.assertNotIn(os.environ['AZURE_SPEECH_KEY'], str(error.exception))
        self.assertGreater(budget.reserved, 0)
        runner.assert_called_once()

    def test_uncertain_transport_never_retries_or_leaks_exception(self):
        runner = Mock(side_effect=RuntimeError(os.environ['AZURE_SPEECH_KEY']))
        budget = CharacterBudget()
        with self.assertRaises(AzureTtsError) as error:
            self.call(runner, budget)
        self.assertNotIn(os.environ['AZURE_SPEECH_KEY'], str(error.exception))
        self.assertGreater(budget.reserved, 0)
        runner.assert_called_once()

    def test_budget_exhaustion_blocks_transport(self):
        runner = Mock()
        with self.assertRaisesRegex(AzureTtsError, 'Limit'):
            self.call(runner, CharacterBudget(1))
        runner.assert_not_called()
        with self.assertRaises(AzureTtsError):
            CharacterBudget(10001)

    def test_invalid_region_or_header_injection_blocks_transport(self):
        for key, value in [('AZURE_SPEECH_REGION', 'invalid.example/'),
                           ('AZURE_SPEECH_KEY', 'test\nInjected: secret')]:
            with self.subTest(key=key), patch.dict(os.environ, {key:value}):
                runner = Mock()
                with self.assertRaises(AzureTtsError):self.call(runner)
                runner.assert_not_called()

    def test_sensitive_or_oversized_text_is_rejected_without_truncation(self):
        for text in ('', 'api key: example', 'a'*1501):
            with self.subTest(length=len(text)):
                runner = Mock()
                with self.assertRaises(AzureTtsError):self.call(runner, text=text)
                runner.assert_not_called()


if __name__ == '__main__': unittest.main()
