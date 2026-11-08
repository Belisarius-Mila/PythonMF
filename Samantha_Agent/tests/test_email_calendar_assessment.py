from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from app.cockpit_email_agent import email_agent_edit_action, email_agent_overview
from app.email.calendar_assessment import calendar_suggestion
from app.email.calendar_draft import CalendarDraftService
from app.email.calendar_proposal import Candidate, Claim
from app.email.codex_proposer import CodexEmailProposer
from app.email.continuous_agent import ContinuousEmailAgent, EmailAssessment
from app.email.hourly_agent import HourlyEmailScheduler
from app.email.service import ServiceSettings, service_tick
from tests.test_continuous_email_agent import FakeSource, proposal
from tests.test_email_calendar_draft import candidate, message


class CalendarAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.worker = ContinuousEmailAgent(Path(self.temp.name) / 'private')
        self.mail = message()
        self.source = FakeSource([self.mail])
        self.reader = Mock(side_effect=AssertionError('Unexpected second email read'))
        self.driver = Mock(side_effect=AssertionError('Unexpected second model turn'))
        self.callbacks = []
        self.service = CalendarDraftService(self.worker, source_factory=self.reader,
            driver=self.driver, launcher=self.callbacks.append)
        self.payload = {'action': 'prepare', 'id': self.mail.item_id,
            'request_id': 'assessment-import-1', 'expected_content_digest': self.mail.content_digest, 'confirmed': True}

    def assess(self, raw=None):
        suggestion = calendar_suggestion(self.mail, candidate() if raw is None else raw, model='synthetic')
        self.worker.cycle(self.source, lambda _: EmailAssessment(proposal(), suggestion))
        return suggestion

    def test_existing_proposal_and_digest_contract_are_unchanged(self):
        self.assess()
        item = self.worker.status()['items'][self.mail.item_id]
        self.assertEqual(item['proposal'], proposal().model_dump())
        result = email_agent_edit_action({'id': self.mail.item_id, 'expected_digest': item['proposal_digest'],
            'proposal': {**item['proposal'], 'reply_draft': 'Moje rozepsaná odpověď.'}}, worker=self.worker)
        self.assertTrue(result['ok'])
        self.assertEqual(self.worker.status()['items'][self.mail.item_id]['calendar_suggestion'], item['calendar_suggestion'])

    def test_get_and_overview_only_advertise_prepared_suggestion_without_import(self):
        self.assess()
        before = self.worker.status()
        self.assertIsNone(self.service.status(self.mail.item_id)['job'])
        view = email_agent_overview(worker=self.worker)
        self.assertEqual(view['cards'][0]['calendar_suggestion'], {'status': 'ready'})
        self.assertFalse(self.service.root.exists())
        self.assertEqual(before, self.worker.status())
        self.reader.assert_not_called()
        self.driver.assert_not_called()

    def test_import_is_atomic_and_uses_existing_defaults_without_model_or_imap(self):
        self.assess()
        before = self.worker.status()
        view = self.service.execute(self.payload)
        self.assertEqual(view['job']['status'], 'completed')
        self.assertEqual(view['draft']['fields']['date'], '2026-11-11')
        self.assertEqual(view['draft']['reminders'], [1440, 60])
        self.assertEqual(view['draft']['issues'], [])
        self.assertEqual(view['draft']['normalized']['start'], '2026-11-11T09:00:00+00:00')
        self.assertFalse(view['calendar_writes'])
        self.assertIsNone(view['write'])
        self.assertIsNone(view['review'])
        self.assertEqual(self.callbacks, [])
        self.reader.assert_not_called()
        self.driver.assert_not_called()
        self.assertEqual(before, self.worker.status())

    def test_import_does_not_replace_edits_or_write_marker_on_reopen_and_restart(self):
        self.assess()
        view = self.service.execute(self.payload)
        view = self.service.execute({'action': 'save', 'id': self.mail.item_id, 'expected_revision': 0,
            'fields': {**view['draft']['fields'], 'location': 'Moje místo'}})
        self.service._mutate(lambda d: d['items'][self.mail.item_id].update(write={'state': 'unknown'}))
        before = self.service.repository.read()
        restarted = CalendarDraftService(self.worker, source_factory=self.reader, driver=self.driver)
        restarted.execute({**self.payload, 'request_id': 'assessment-reopen-2'})
        self.assertEqual(before, self.service.repository.read())
        self.assertEqual(restarted.status(self.mail.item_id)['draft']['fields']['location'], 'Moje místo')
        self.assertEqual(restarted.status(self.mail.item_id)['write']['state'], 'unknown')

    def test_different_concurrent_request_ids_preserve_a_single_draft(self):
        self.assess()
        def prepare(index):
            try:
                self.service.execute({**self.payload, 'request_id': 'concurrent-import-' + str(index)})
            except Exception as exc:
                # A lock denial is allowed; no alternate operation is started.
                from app.file_persistence import FileLockTimeoutError
                if not isinstance(exc, FileLockTimeoutError):
                    raise
        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(prepare, range(3)))
        self.assertEqual(len(self.service.repository.read()['items']), 1)
        self.assertEqual(self.callbacks, [])
        self.driver.assert_not_called()

    def test_wrong_source_or_bad_confirmation_cannot_import_or_start_fallback(self):
        self.assess()
        for update in ({'confirmed': False}, {'expected_content_digest': '0'*64}):
            with self.assertRaises(ValueError):
                self.service.execute({**self.payload, **update})
        self.worker._update(lambda d: d['items'][self.mail.item_id]['calendar_suggestion'].update(source_digest='0'*64))
        with self.assertRaises(ValueError):
            self.service.execute(self.payload)
        self.assertEqual(self.service.repository.read(), {'items': {}})
        self.reader.assert_not_called()

    def test_existing_queued_or_uncertain_manual_attempt_is_never_replaced(self):
        self.assess()
        for status in ('queued', 'delivery_unknown'):
            entry = {'content_digest': self.mail.content_digest,
                     'job': {'id': 'original', 'status': status, 'nonce': self.service.nonce}}
            self.service._mutate(lambda d: d['items'].__setitem__(self.mail.item_id, entry))
            self.service.execute(self.payload)
            self.assertEqual(self.service.repository.read()['items'][self.mail.item_id], entry)
        self.reader.assert_not_called()

    def test_invalid_calendar_quote_does_not_discard_or_change_email_proposal(self):
        bad = candidate(); bad['location']['quote'] = 'Not in original email'
        suggestion = self.assess(bad)
        self.assertEqual(suggestion['status'], 'invalid')
        item = self.worker.status()['items'][self.mail.item_id]
        self.assertEqual(item['proposal'], proposal().model_dump())
        self.assertEqual(item['status'], 'awaiting_confirmation')
        self.assertEqual(email_agent_overview(worker=self.worker)['calendar_suggestion_errors'], 1)
        self.assertNotIn('input', suggestion)

    def test_invalid_saved_quote_fails_again_at_import_without_partial_draft(self):
        self.assess()
        self.worker._update(lambda d: d['items'][self.mail.item_id]['calendar_suggestion']['candidate']['date'].update(quote='forged'))
        with self.assertRaises(ValueError):
            self.service.execute(self.payload)
        self.assertEqual(self.service.repository.read(), {'items': {}})
        self.reader.assert_not_called()

    def test_formal_invitation_and_recurrence_remain_manual_even_if_model_says_meeting(self):
        for mail in (message(formal=True), message('Schůzka každé pondělí od 10:00.')):
            result = calendar_suggestion(mail, candidate(), model='synthetic')
            self.assertEqual(result['status'], 'ready')
            self.assertEqual(result['candidate']['kind'], 'manual_required')
            self.assertTrue(result['input']['manual_reason'])

    def test_ambiguous_deadline_preserves_missing_date_and_cannot_pass_review(self):
        self.mail = message('Pošlete podklady do pátku.'); self.source = FakeSource([self.mail])
        raw = Candidate(kind='task_deadline', all_day=True, date=Claim(value='', source='body', quote='do pátku')).model_dump()
        self.assess(raw)
        view = self.service.execute({**self.payload, 'id': self.mail.item_id, 'expected_content_digest': self.mail.content_digest})
        self.assertTrue(view['draft']['issues'])
        self.assertIsNone(view['draft']['normalized'])
        with self.assertRaises(ValueError):
            self.service.execute({'action': 'review', 'id': self.mail.item_id, 'expected_revision': 0, 'confirmed': True})

    def test_restart_scan_and_reopening_never_repeat_assessment(self):
        calls = Mock(return_value=EmailAssessment(proposal(), calendar_suggestion(self.mail, candidate(), model='synthetic')))
        self.worker.cycle(self.source, calls)
        ContinuousEmailAgent(self.worker.root).cycle(self.source, calls)
        self.service.execute(self.payload)
        self.service.execute({**self.payload, 'request_id': 'new-click-same-source'})
        self.assertEqual(calls.call_count, 1)

    def test_irrelevant_mail_retains_classification_and_no_candidate(self):
        result = calendar_suggestion(self.mail, None, model='synthetic')
        self.assertEqual(result['status'], 'not_applicable')
        low = proposal().model_copy(update={'important': False, 'reply_draft': ''})
        self.worker.cycle(self.source, lambda _: EmailAssessment(low, result))
        self.assertEqual(self.worker.status()['items'][self.mail.item_id]['status'], 'hourly_summary')

    def test_real_candidate_is_visible_even_if_model_mistakenly_marks_mail_unimportant(self):
        result = calendar_suggestion(self.mail, candidate(), model='synthetic')
        low = proposal().model_copy(update={'important': False, 'reply_draft': ''})
        self.worker.cycle(self.source, lambda _: EmailAssessment(low, result))
        self.assertEqual(self.worker.status()['items'][self.mail.item_id]['status'], 'awaiting_confirmation')

    def test_import_uses_the_existing_fresh_review_and_confirmed_single_write(self):
        from app.calendar_overview import CalendarOverview
        from tests.test_email_calendar_review import BoundedPilot
        from tests.test_email_calendar_write import FakeWriter
        now = datetime.fromisoformat('2026-11-08T10:00:00+01:00')
        calendar = CalendarOverview(BoundedPilot(Path(self.temp.name) / 'calendar', lambda: now), clock=lambda: now)
        calendar.refresh(confirmed=True)
        calendar.save_selection({'action': 'save_selection', 'confirmed': True, 'expected_revision': 0,
                                 'read_calendar_ids': ['a'], 'target_calendar_id': 'a'})
        writer = FakeWriter(Path(self.temp.name) / 'writer')
        self.service.calendar = calendar
        self.service.writer = writer
        self.service.clock = lambda: now
        self.assess(); self.service.execute(self.payload)
        self.assertEqual(writer.calls, [])
        view = self.service.execute({'action': 'review', 'id': self.mail.item_id, 'expected_revision': 0, 'confirmed': True})
        payload = {'action': 'write', 'id': self.mail.item_id, 'expected_revision': 0,
                   'review_fingerprint': view['review']['fingerprint'], 'confirmed': True}
        with self.assertRaises(ValueError):
            self.service.execute({**payload, 'confirmed': False})
        self.assertEqual(writer.calls, [])
        self.assertEqual(self.service.execute(payload)['write']['state'], 'verified')
        self.service.execute(payload)
        self.assertEqual(len(writer.calls), 1)
        self.assertEqual(writer.calls[0][0]['reminders'], [1440, 60])
        self.reader.assert_not_called()
        self.driver.assert_not_called()

    def test_enabling_later_never_reassesses_or_rewrites_historical_cards(self):
        self.worker.cycle(self.source, lambda _: proposal())
        before = self.worker.status()['items']
        self.worker.cycle(self.source, lambda _: self.fail('Old email must not be reassessed'))
        self.assertEqual(self.worker.status()['items'], before)
        self.assertNotIn('calendar_suggestion', before[self.mail.item_id])


class CalendarAssessmentAdapterTests(unittest.TestCase):
    def adapter(self, raw, *, enabled=True):
        self.calls = []
        calls = self.calls
        class Client:
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def start_thread(self, **kwargs): calls.append(kwargs); return 'synthetic'
            def send_text(self, **kwargs):
                calls.append(kwargs)
                return SimpleNamespace(delivered=True, answer=json.dumps(raw),
                    thread_token_usage={'input_tokens': 1000, 'output_tokens': 200}, duration_ms=150)
        return CodexEmailProposer('synthetic', reply_name='', client_factory=Client, calendar_suggestions=enabled)

    def test_enabled_adds_strict_candidate_schema_to_a_single_turn_and_retains_email_fields(self):
        raw = {**proposal().model_dump(), 'calendar_candidate': candidate()}
        result = self.adapter(raw)(message())
        self.assertIsInstance(result, EmailAssessment)
        self.assertEqual(result.proposal, proposal())
        self.assertEqual(result.calendar_suggestion['status'], 'ready')
        self.assertEqual(result.calendar_suggestion['assessment_usage']['input_tokens'], 1000)
        self.assertEqual(len(self.calls), 2)  # One start_thread and one send_text.
        schema = self.calls[1]['output_schema']
        def strict(node):
            if isinstance(node, dict):
                if node.get('type') == 'object':
                    self.assertEqual(set(node['properties']), set(node['required']))
                    self.assertIs(node['additionalProperties'], False)
                for value in node.values(): strict(value)
            elif isinstance(node, list):
                for value in node: strict(value)
        strict(schema)
        self.assertIn('calendar_candidate', schema['required'])
        payload = json.loads(self.calls[1]['text'])
        self.assertEqual(payload['body_text'], message().source.body_text)
        self.assertNotIn('original_eml', payload)

    def test_disabled_keeps_original_result_schema_instructions_and_full_body(self):
        result = self.adapter(proposal().model_dump(), enabled=False)(message())
        self.assertEqual(result, proposal())
        self.assertNotIn('calendar_candidate', self.calls[1]['output_schema']['properties'])
        self.assertNotIn('calendar_candidate', self.calls[0]['developer_instructions'])

    def test_invalid_optional_candidate_preserves_successful_email_assessment(self):
        result = self.adapter({**proposal().model_dump(), 'calendar_candidate': {'kind': 'bogus'}})(message())
        self.assertEqual(result.proposal, proposal())
        self.assertEqual(result.calendar_suggestion['status'], 'invalid')

    def test_old_settings_default_off_and_opt_in_reuses_one_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); worker = ContinuousEmailAgent(root / 'private')
            path = root / 'service.json'; source = FakeSource([message()])
            source.baseline_cursor = lambda: {'uidvalidity': '10', 'after_uid': 0}
            HourlyEmailScheduler(worker).initialize_from_now([source])
            self.assertFalse(ServiceSettings.model_validate({'enabled': True}).calendar_suggestions)
            path.write_text(json.dumps({'enabled': True, 'providers': ['icloud'], 'calendar_suggestions': True}))
            adapter = self.adapter({**proposal().model_dump(), 'calendar_candidate': candidate()})
            factory = Mock(return_value=adapter)
            tick = lambda: service_tick(settings_path=path, worker=worker,
                now=datetime.fromisoformat('2026-11-08T10:00:00+01:00'), source_factory=lambda _: source,
                select_model=lambda: {'model': 'synthetic', 'reasoning_effort': 'high'},
                selection_validator=lambda *args, **kwargs: None, proposer_factory=factory)
            self.assertEqual(tick()['proposals'], 1)
            self.assertEqual(tick()['status'], 'already_completed')
            factory.assert_called_once_with('synthetic', effort='high', calendar_suggestions=True)
            self.assertEqual(len(self.calls), 2)
            self.assertEqual(worker.status()['service']['daily_attempts']['2026-11-08'], 1)
            self.assertEqual(worker.status()['sources'][source.key]['after_uid'], 1)


if __name__ == '__main__':
    unittest.main()
