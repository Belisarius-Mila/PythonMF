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

    def test_italian_elsa_preserves_accents_and_exact_billable_text(self):
        text = "L'acqua è qui."
        xml, count = ssml_parts(text, 'it-IT-ElsaNeural')
        root = ElementTree.fromstring(xml)
        self.assertEqual(root.attrib['{http://www.w3.org/XML/1998/namespace}lang'], 'it-IT')
        self.assertEqual(''.join(root.itertext()), text)
        self.assertIn('it-IT-ElsaNeural', xml)
        self.assertEqual(count, len(text) + 31)

    def test_french_henri_ssml_preserves_exact_text_accents_and_escaping(self):
        text = " L’été & l'œuf < demain > aujourd’hui.\nÇa va ? "
        xml, count = ssml_parts(text, 'fr-FR-HenriNeural')
        root = ElementTree.fromstring(xml)
        ns = {'s': 'http://www.w3.org/2001/10/synthesis'}
        self.assertEqual(root.attrib['{http://www.w3.org/XML/1998/namespace}lang'], 'fr-FR')
        self.assertEqual(root.find('s:voice', ns).attrib['name'], 'fr-FR-HenriNeural')
        self.assertEqual(root.find('s:voice/s:prosody', ns).attrib['rate'], '-10%')
        self.assertEqual(''.join(root.itertext()), text)
        self.assertIn('&amp;', xml)
        self.assertIn('&lt; demain &gt;', xml)
        self.assertEqual(count, len(text) + 31 + 4 + 3 + 3)

    def test_henri_transport_reserves_before_single_post_and_keeps_failure_reserved(self):
        text = "L’été arrive."
        for outcome in (subprocess.CompletedProcess([], 0, b'ID3audio\n200', b''),
                        RuntimeError('synthetic transport failure')):
            with self.subTest(uncertain=isinstance(outcome, Exception)):
                budget = CharacterBudget()
                def run(argv, **kwargs):
                    self.assertEqual(budget.reserved, ssml_parts(text, 'fr-FR-HenriNeural')[1])
                    self.assertNotIn('--retry', argv)
                    self.assertNotIn('--location', argv)
                    self.assertNotIn(os.environ['AZURE_SPEECH_KEY'], ' '.join(argv))
                    self.assertIn('fr-FR-HenriNeural', kwargs['input'].decode())
                    if isinstance(outcome, Exception):
                        raise outcome
                    return outcome
                runner = Mock(side_effect=run)
                with patch('app.speech.azure_tts_mp3.dotenv_values', return_value={}):
                    if isinstance(outcome, Exception):
                        with self.assertRaisesRegex(AzureTtsError, 'bez opakování'):
                            synthesize_azure_tts_mp3_sync(text, voice='fr-FR-HenriNeural', budget=budget, runner=runner)
                    else:
                        self.assertEqual(synthesize_azure_tts_mp3_sync(text, voice='fr-FR-HenriNeural', budget=budget, runner=runner), b'ID3audio')
                runner.assert_called_once()
                self.assertGreater(budget.reserved, 0)

    def test_french_addition_keeps_unselected_voice_rate_and_budget_blocked(self):
        for voice, rate, limit in [('fr-FR-DeniseNeural', '-10%', 10000),
                                   ('fr-FR-HenriNeural', '0%', 10000),
                                   ('fr-FR-HenriNeural', '-10%', 1)]:
            with self.subTest(voice=voice, rate=rate, limit=limit):
                runner = Mock()
                with patch('app.speech.azure_tts_mp3.dotenv_values', return_value={}):
                    with self.assertRaises(AzureTtsError):
                        synthesize_azure_tts_mp3_sync('Bonjour !', voice=voice, rate=rate,
                                                     budget=CharacterBudget(limit), runner=runner)
                runner.assert_not_called()

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
