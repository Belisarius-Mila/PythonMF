"""Selection safety and CI contracts; no model, live service or publication."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from app.communication import validation_policy as policy
from app.communication.validation_domains import BOUNDARY_TESTS, CORE_TESTS, SOURCES, modules_for_scopes
from app.communication.validation_policy import select_validation_plan
from scripts.cockpit_quality_gate import PROJECT_ROOT, TEST_MODULES
from scripts.validation_ci import ci_plan, event_base


class ValidationDomainsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)

    def write(self, relative, text):
        path = self.repo / 'Samantha_Agent' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def plan(self, *paths):
        return select_validation_plan(['Samantha_Agent/'+p for p in paths], repo=self.repo)

    def test_catalog_domains_and_boundary_contracts_are_in_the_full_suite(self):
        self.assertEqual(len(TEST_MODULES),len(set(TEST_MODULES)))
        contracts = set(CORE_TESTS)
        for domain in SOURCES:
            group = modules_for_scopes({domain},TEST_MODULES)
            self.assertTrue(group,domain)
            contracts.update(group)
        for group in BOUNDARY_TESTS.values():
            contracts.update(group)
        self.assertTrue(contracts.issubset(TEST_MODULES))
        for name in contracts:
            self.assertTrue((PROJECT_ROOT/(name.replace('.','/')+'.py')).is_file(),name)
        with self.assertRaises(policy.ValidationPolicyError):
            select_validation_plan(['Samantha_Agent/tests/test_new_unregistered.py'])

    def test_calendar_is_scoped_and_keeps_downstream_write_recovery_tests(self):
        plan=select_validation_plan(['Samantha_Agent/app/calendar_writer.py'])
        self.assertEqual(plan.mode,'targeted')
        for name in ('tests.test_calendar_writer','tests.test_calendar_tasks','tests.test_email_calendar_write',
                     'tests.test_calendar_edit','tests.test_calendar_delete','tests.test_cockpit_http_security'):
            self.assertIn(name,plan.modules)
        self.assertNotIn('tests.test_camino_film_editor',plan.modules)

    def test_french_online_game_always_keeps_server_and_original_client_regressions(self):
        for path in ('Samantha_Agent/app/vocabulary_fr_multiplayer.py',
                     'docs/vocabulary-fr/online.js', 'docs/vocabulary-fr/online.html',
                     'Samantha_Agent/tests/test_vocabularyfr_online.js'):
            with self.subTest(path=path):
                plan=select_validation_plan([path])
                self.assertEqual(plan.mode,'targeted')
                self.assertIn('tests.test_vocabularyfr_multiplayer',plan.modules)
                self.assertIn('tests.test_vocabularyfr_web_gallery',plan.modules)
                self.assertNotIn('tests.test_camino_film_editor',plan.modules)

    def test_shared_calendar_editor_keeps_native_and_dashboard_regressions(self):
        plan=self.plan('app/frontend/shared/calendar_actions.js')
        for name in ('tests.test_cockpit_calendar_edit','tests.test_calendar_edit',
                     'tests.test_cockpit_calendar_agenda','tests.test_cockpit_http_security'):
            self.assertIn(name,plan.modules)
        self.assertNotIn('tests.test_camino_film_editor',plan.modules)

    def test_shared_and_unknown_changes_use_contracts_without_automatic_full(self):
        for path in ('app/file_persistence.py','app/work_repository.py','app/documents/transactions.py',
                     'app/unknown.py','requirements.txt','config/agent_roles.json','AGENTS.md',
                     'app/calendar_unknown/nested.py', 'unknown/app/calendar_writer.py',
                     'app/communication/validation_domains.py','scripts/cockpit_quality_gate.py'):
            with self.subTest(path=path):
                result=select_validation_plan(['Samantha_Agent/'+path])
                self.assertEqual(result.mode,'targeted')
                self.assertTrue(result.modules)

    def test_shared_chat_frontend_and_node_fixture_keep_the_real_two_client_test(self):
        for path in ('app/frontend/samantha_chat/app.js', 'app/frontend/samantha_chat/page.html',
                     'app/frontend/samantha_chat/styles.css', 'tests/shared_chat_frontend.test.cjs',
                     'tests/shared_chat_browser_timers.test.cjs', 'app/shared_chat_library.py',
                     'app/frontend/samantha_chat/library.js', 'tests/shared_chat_library.test.cjs'):
            with self.subTest(path=path):
                result = self.plan(path)
                self.assertEqual(result.mode, 'targeted')
                self.assertIn('tests.test_shared_chat_http', result.modules)
                self.assertIn('tests.test_shared_chat_runtime', result.modules)
                self.assertIn('tests.test_shared_chat_library', result.modules)
                self.assertIn('tests.test_cockpit_http_security', result.modules)
                self.assertNotIn('tests.test_calendar_writer', result.modules)

    def test_reverse_relative_imports_expand_other_domains_and_direct_test_consumers(self):
        self.write('app/calendar_writer.py','VALUE = 1\n')
        self.write('app/interior_titles.py','from .calendar_writer import VALUE\n')
        self.write('tests/test_agent_reply.py','from app import interior_titles\n')
        result = self.plan('app/calendar_writer.py')
        self.assertEqual(result.mode,'targeted')
        self.assertIn('interior',result.domains)
        self.assertIn('tests.test_interior_titles',result.modules)
        self.assertIn('tests.test_agent_reply',result.modules)

    def test_unknown_production_or_unregistered_test_consumer_adds_contract_checks(self):
        for path in ('app/unknown_adapter.py','tests/unregistered_consumer.py'):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temp:
                previous=self.repo
                self.repo=Path(temp)
                self.write(path,'from app.calendar_writer import VALUE\n')
                result=self.plan('app/calendar_writer.py')
                self.assertEqual(result.mode,'targeted')
                self.assertIn('tests.test_cockpit_quality_gate',result.modules)
                self.repo=previous

    def test_running_a_test_does_not_expand_its_unchanged_fixture_users(self):
        self.write('tests/test_calendar_writer.py','import app.calendar_writer\n')
        self.write('tests/test_simple_main_checkpoint.py','from tests.test_calendar_writer import Fixture\n')
        production=self.plan('app/calendar_writer.py')
        fixture=self.plan('tests/test_calendar_writer.py')
        self.assertNotIn('tests.test_simple_main_checkpoint',production.modules)
        self.assertIn('tests.test_simple_main_checkpoint',fixture.modules)

    def test_reviewed_composition_boundary_keeps_its_contract_without_graph_flood(self):
        self.write('app/email/codex_proposer.py','from .calendar_assessment import assess\n')
        self.write('app/unassigned_caller.py','from app.email.codex_proposer import propose\n')
        result=self.plan('app/email/calendar_assessment.py')
        self.assertEqual(result.mode,'targeted')
        self.assertIn('tests.test_agent_reply',result.modules)
        self.assertEqual(self.plan('app/email/codex_proposer.py').mode,'targeted')

    def test_dynamic_dependencies_expand_contracts_and_invalid_python_stops_without_full(self):
        for text in ("__import__('app.calendar_writer')\n",
                     "from importlib import import_module as load\nload('app.calendar_tasks')\n",
                     "from builtins import __import__ as load\nload('app.calendar_tasks')\n"):
            self.write('app/calendar_writer.py',text)
            result=self.plan('app/calendar_writer.py','requirements.txt')
            self.assertEqual(result.mode,'targeted')
            self.assertIn('tests.test_cockpit_quality_gate',result.modules)
        self.write('app/calendar_writer.py','def invalid(\n')
        with self.assertRaises(policy.ValidationPolicyError):
            self.plan('app/calendar_writer.py')

    def test_import_cache_tracks_content_even_if_timestamps_are_restored(self):
        import os
        path=self.write('app/interior_titles.py','from app.calendar_tasks import VALUE\n')
        original=path.stat()
        self.assertNotIn('interior',self.plan('app/calendar_writer.py').domains)
        path.write_text('from app.calendar_writer import VALUE\n')
        os.utime(path,ns=(original.st_atime_ns,original.st_mtime_ns))
        self.assertIn('interior',self.plan('app/calendar_writer.py').domains)

    def test_new_and_deleted_sources_expand_consumers_without_full_bootstrap(self):
        self.write('app/interior_titles.py','import app.calendar_writer\n')
        with patch.object(policy,'git',return_value=b'Samantha_Agent/app/calendar_tasks.py\0'):
            result=select_validation_plan(['Samantha_Agent/app/calendar_writer.py'],repo=self.repo,base='a'*40)
        self.assertEqual(result.mode,'targeted')
        # Source is absent, but a surviving import still defines its consumer.
        self.assertIn('interior',self.plan('app/calendar_writer.py').domains)

    def test_stale_domain_or_registry_in_a_long_running_process_requires_reload(self):
        for target in ('_LOADED_DOMAIN_SOURCE',):
            with patch.object(policy,target,'old-loaded-content'):
                self.assertEqual(self.plan('app/calendar_writer.py').reason,'policy_runtime_requires_reload')
        with patch('scripts.cockpit_quality_gate.LOADED_SOURCE_HASH','old-loaded-content'):
            self.assertEqual(self.plan('app/calendar_writer.py').reason,'policy_runtime_requires_reload')

    def test_ci_schedule_manual_and_unknown_events_cannot_choose_a_subset(self):
        for name in ('schedule','workflow_dispatch','unknown'):
            self.assertIsNone(event_base(name,{'before':'a'*40}))
        self.assertEqual(event_base('push',{'before':'a'*40}),'a'*40)
        self.assertEqual(event_base('pull_request',{'pull_request':{'base':{'sha':'b'*40}}}),'b'*40)
        for base in ('0'*40,'--unsafe','main',None):
            self.assertIsNone(event_base('push',{'before':base}))
        for event in (None,[],{'pull_request':None},{'pull_request':{'base':None}}):
            self.assertIsNone(event_base('pull_request',event))

    def test_ci_full_is_only_scheduled_or_manual_unknown_base_uses_contracts(self):
        with patch('scripts.validation_ci.git',side_effect=policy.ValidationPolicyError('unavailable')) as git:
            plan,base=ci_plan(self.repo,'schedule',{})
            self.assertEqual(plan.mode,'full')
            self.assertIsNone(base)
            git.assert_not_called()
            plan,base=ci_plan(self.repo,'push',{'before':'a'*40})
            self.assertEqual(plan.mode,'targeted')
            self.assertIsNone(base)

    def test_ci_uses_complete_event_diff_and_fetches_missing_shallow_base(self):
        base='b'*40
        diff=b'Samantha_Agent/app/calendar_writer.py\0Samantha_Agent/requirements.txt\0'
        with patch('scripts.validation_ci.git',side_effect=[policy.ValidationPolicyError('shallow'),b'',diff]) as git:
            result,observed=ci_plan(self.repo,'push',{'before':base})
        self.assertEqual(observed,base)
        self.assertEqual(result.mode,'targeted')
        self.assertIn('tests.test_calendar_writer',result.modules)
        self.assertEqual(git.call_args_list[1].args[1:],('fetch','--no-tags','--depth=1','origin',base))
        self.assertEqual(git.call_args_list[2].args[1:],('diff','--no-renames','--name-only','-z',base,'HEAD','--'))

    def test_vocabulary_content_paths_include_new_media_and_inventory_tests_without_authoring(self):
        paths=('VocabularyEN/VocabularyEN.csv','VocabularyEN/vocabulary_en_catalog.json',
               'VocabularyEN/Pict/new.png','docs/assets/vocabulary-en/new.webp',
               'docs/assets/vocabulary-en-thumbs/new.webp',
               'docs/assets/vocabulary-en-audio/en-us-aria-neural/new.mp3',
               'docs/assets/vocabulary-en-sentences/cs-cz-vlasta-neural/new.mp3',
               'docs/data/vocabulary-en.json','docs/data/vocabulary-en-audio.json',
               'Samantha_Agent/tests/test_vocabularyen_selection.js',
               'Samantha_Agent/tests/test_vocabularyen_audio_library.py',
               'Samantha_Agent/tests/test_vocabularyen_gallery.py')
        result=select_validation_plan(paths)
        self.assertEqual(result.domains,('vocabulary_content',))
        self.assertIn('tests.test_vocabularyen_audio_library',result.modules)
        self.assertIn('tests.test_vocabularyen_gallery',result.modules)
        self.assertNotIn('tests.test_vocabulary_authoring',result.modules)
        self.assertNotIn('tests.test_calendar_writer',result.modules)
        code=select_validation_plan([*paths,'Samantha_Agent/app/vocabulary_authoring.py'])
        self.assertIn('tests.test_vocabulary_authoring',code.modules)

    def test_french_client_and_synthetic_fixtures_select_only_the_existing_fr_contract(self):
        for path in ('docs/vocabulary-fr/gallery.js',
                     'Samantha_Agent/tests/fixtures/vocabulary_fr_dom.js',
                     'Samantha_Agent/tests/fixtures/vocabulary_fr_client.js'):
            with self.subTest(path=path):
                result=select_validation_plan([path])
                self.assertEqual(result.mode,'targeted')
                self.assertEqual(result.domains,('vocabulary_fr',))
                self.assertIn('tests.test_vocabularyfr_web_gallery',result.modules)
                self.assertIn('tests.test_cockpit_http_security',result.modules)
                self.assertNotIn('tests.test_vocabularyit_gallery',result.modules)
                self.assertNotIn('tests.test_vocabularyfr_catalog',result.modules)

    def test_italian_foundation_has_its_own_inventory_and_identity_checks(self):
        result=select_validation_plan([
            'VocabularyIT/vocabulary_it_catalog.py', 'VocabularyIT/vocabulary_it_catalog.json',
            'VocabularyIT/vocabulary_it_input_manifest.json', 'VocabularyIT/VocabularyIT.csv',
            'VocabularyIT/vocabulary_it_export.py',
            'VocabularyIT/vocabulary_it_audio.py',
            'docs/assets/vocabulary-it-audio/it-it-elsa-neural/fixture.mp3',
            'docs/assets/vocabulary-it-sentences/cs-cz-vlasta-neural/fixture.mp3',
            'PictNew/generated/20261115_it_web_review/vit-0013.webp',
            'docs/data/vocabulary-it-v2.json',
            'docs/data/vocabulary-it-quiz.json',
            'docs/vocabulary-it/gallery.js', 'Pict/it_web_vit_0136.webp',
            'Samantha_Agent/tests/test_vocabularyit_selection.js',
            'Samantha_Agent/tests/test_vocabularyit_catalog.py'])
        self.assertEqual(result.domains, ('vocabulary_it',))
        self.assertIn('tests.test_vocabularyit_catalog', result.modules)
        self.assertIn('tests.test_vocabularyit_export', result.modules)
        self.assertIn('tests.test_vocabularyit_gallery', result.modules)
        self.assertIn('tests.test_vocabularyit_audio', result.modules)
        self.assertIn('tests.test_cockpit_http_security', result.modules)
        self.assertNotIn('tests.test_calendar_writer', result.modules)
        self.assertNotIn('tests.test_vocabulary_authoring', result.modules)
