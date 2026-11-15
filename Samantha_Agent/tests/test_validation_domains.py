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

    def test_calendar_is_scoped_and_keeps_downstream_write_recovery_tests(self):
        plan=select_validation_plan(['Samantha_Agent/app/calendar_writer.py'])
        self.assertEqual(plan.mode,'targeted')
        for name in ('tests.test_calendar_writer','tests.test_calendar_tasks','tests.test_email_calendar_write',
                     'tests.test_calendar_edit','tests.test_calendar_delete','tests.test_cockpit_http_security'):
            self.assertIn(name,plan.modules)
        self.assertNotIn('tests.test_camino_film_editor',plan.modules)

    def test_global_and_unknown_changes_keep_the_full_gate(self):
        for path in ('app/file_persistence.py','app/work_repository.py','app/documents/transactions.py',
                     'app/unknown.py','requirements.txt','config/agent_roles.json','AGENTS.md',
                     'app/calendar_unknown/nested.py', 'unknown/app/calendar_writer.py',
                     'app/communication/validation_domains.py','scripts/cockpit_quality_gate.py'):
            with self.subTest(path=path):
                self.assertEqual(select_validation_plan(['Samantha_Agent/'+path]).mode,'full')

    def test_reverse_relative_imports_expand_other_domains_and_direct_test_consumers(self):
        self.write('app/calendar_writer.py','VALUE = 1\n')
        self.write('app/interior_titles.py','from .calendar_writer import VALUE\n')
        self.write('tests/test_agent_reply.py','from app import interior_titles\n')
        result = self.plan('app/calendar_writer.py')
        self.assertEqual(result.mode,'targeted')
        self.assertIn('interior',result.domains)
        self.assertIn('tests.test_interior_titles',result.modules)
        self.assertIn('tests.test_agent_reply',result.modules)

    def test_unknown_production_or_unregistered_test_consumer_forces_full(self):
        for path in ('app/unknown_adapter.py','tests/unregistered_consumer.py'):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temp:
                previous=self.repo
                self.repo=Path(temp)
                self.write(path,'from app.calendar_writer import VALUE\n')
                self.assertEqual(self.plan('app/calendar_writer.py').mode,'full')
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
        self.assertEqual(self.plan('app/email/codex_proposer.py').mode,'full')

    def test_dynamic_import_parse_failure_and_mixed_unknown_scope_fail_closed(self):
        for text in ("__import__('app.calendar_writer')\n",'def invalid(\n',
                     "from importlib import import_module as load\nload('app.calendar_tasks')\n",
                     "from builtins import __import__ as load\nload('app.calendar_tasks')\n"):
            self.write('app/calendar_writer.py',text)
            self.assertEqual(self.plan('app/calendar_writer.py').mode,'full')
        self.assertEqual(self.plan('app/calendar_writer.py','requirements.txt').mode,'full')

    def test_import_cache_tracks_content_even_if_timestamps_are_restored(self):
        import os
        path=self.write('app/interior_titles.py','from app.calendar_tasks import VALUE\n')
        original=path.stat()
        self.assertNotIn('interior',self.plan('app/calendar_writer.py').domains)
        path.write_text('from app.calendar_writer import VALUE\n')
        os.utime(path,ns=(original.st_atime_ns,original.st_mtime_ns))
        self.assertIn('interior',self.plan('app/calendar_writer.py').domains)

    def test_new_executable_code_requires_full_and_deleted_source_still_expands_consumers(self):
        self.write('app/interior_titles.py','import app.calendar_writer\n')
        with patch.object(policy,'git',return_value=b'Samantha_Agent/app/calendar_tasks.py\0'):
            result=select_validation_plan(['Samantha_Agent/app/calendar_writer.py'],repo=self.repo,base='a'*40)
        self.assertEqual(result.reason,'new_code_requires_full_baseline')
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

    def test_ci_unavailable_base_uses_full_and_schedule_never_needs_a_cache(self):
        with patch('scripts.validation_ci.git',side_effect=policy.ValidationPolicyError('unavailable')) as git:
            plan,base=ci_plan(self.repo,'schedule',{})
            self.assertEqual(plan.mode,'full')
            self.assertIsNone(base)
            git.assert_not_called()
            plan,base=ci_plan(self.repo,'push',{'before':'a'*40})
            self.assertEqual(plan.mode,'full')
            self.assertIsNone(base)

    def test_ci_uses_complete_event_diff_and_fetches_missing_shallow_base(self):
        base='b'*40
        diff=b'Samantha_Agent/app/calendar_writer.py\0Samantha_Agent/requirements.txt\0'
        with patch('scripts.validation_ci.git',side_effect=[policy.ValidationPolicyError('shallow'),b'',diff]) as git:
            result,observed=ci_plan(self.repo,'push',{'before':base})
        self.assertEqual(observed,base)
        self.assertEqual(result.mode,'full')
        self.assertEqual(git.call_args_list[1].args[1:],('fetch','--no-tags','--depth=1','origin',base))
        self.assertEqual(git.call_args_list[2].args[1:],('diff','--no-renames','--name-only','-z',base,'HEAD','--'))
