from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from app import science_news_activation as activation


class ActivationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.runtime = self.root / 'runtime'
        self.home = self.root / 'home'
        for name in activation.CODE:
            dest = self.runtime / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((activation.ROOT / name).read_bytes())
        python = self.runtime / '.venv/bin/python'
        python.parent.mkdir(parents=True)
        python.write_text('fixture; never executed')
        patcher = patch.object(activation, 'STATE', self.root / 'activation')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.now = datetime(2026, 11, 10, 8, tzinfo=timezone.utc)
        self.probe = lambda runtime: {'known': True, 'policy_digest': activation.expected_role()}
        self.serving = lambda runtime: True
        self.prepared = activation.prepare(runtime_root=self.runtime, home=self.home, now=self.now,
            role_probe=self.probe, serving_probe=self.serving)
        self.config = self.runtime / 'data/private/science_news/activation.json'
        self.agent = self.home / 'Library/LaunchAgents/com.samantha.science-news.plist'
        self.receipt = activation.STATE / ('receipt_'+self.prepared['proposal_sha256']+'.json')
        self.args = {'proposal_sha256':self.prepared['proposal_sha256'], 'confirmation':activation.CONFIRMATION,
                     'role_probe':self.probe, 'serving_probe':self.serving, 'now':self.now}
        self.calls = []
        self.present = False

    def runner(self, args, **kwargs):
        self.calls.append(args)
        if args[1] == 'bootstrap':
            self.assertTrue(json.loads(self.receipt.read_text())['launch_attempted'])
            self.present = True
        listing = '\n'.join([str(self.runtime / '.venv/bin/python'),str(self.runtime / 'scripts/science_news.py'),'tick'])
        return SimpleNamespace(returncode=0 if self.present else 1, stdout=listing if self.present else '')

    def test_prepare_only_writes_private_proposal_and_targets_future_friday(self):
        self.assertEqual(self.prepared['first_due'],'2026-11-13T09:00:00+01:00')
        self.assertTrue(self.prepared['role_ready'] and self.prepared['code_ready'])
        self.assertEqual(self.prepared['paid_model_calls'],0)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.agent.exists())

    def test_missing_safety_phrase_does_not_write_or_launch(self):
        with self.assertRaises(ValueError):
            activation.activate(**{**self.args,'confirmation':'ano'},runner=self.runner)
        self.assertFalse(self.calls)
        self.assertFalse(self.config.exists())

    def test_activate_and_replay_bootstrap_once_and_do_not_touch_other_roles(self):
        roles = self.runtime / 'config/agent_roles.json'
        roles.parent.mkdir()
        roles.write_text('unrelated runtime roles, read by fixture probe')
        result = activation.activate(**self.args, runner=self.runner)
        self.assertEqual(result['state'],'active')
        self.assertEqual(activation.activate(**self.args,runner=self.runner)['state'],'active')
        self.assertEqual(sum(args[1]=='bootstrap' for args in self.calls),1)
        self.assertEqual(roles.read_text(),'unrelated runtime roles, read by fixture probe')
        config = json.loads(self.config.read_text())
        self.assertEqual(config['max_job_credits'],15)
        self.assertEqual(config['max_month_credits'],100)

    def test_missing_deployment_blocks_before_activation_files(self):
        (self.runtime / 'app/science_news_model.py').write_text('old deployed code')
        with self.assertRaises(ValueError):
            activation.activate(**self.args,runner=self.runner)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.calls)

    def test_role_policy_change_blocks_before_write(self):
        probe = lambda runtime: {'known':True,'policy_digest':'0'*64}
        with self.assertRaises(ValueError):
            activation.activate(**{**self.args,'role_probe':probe},runner=self.runner)
        self.assertFalse(self.config.exists())

    def test_files_without_restarted_cockpit_are_insufficient(self):
        with self.assertRaises(ValueError):
            activation.activate(**{**self.args,'serving_probe':lambda runtime:False},runner=self.runner)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.calls)

    def test_uncertain_bootstrap_is_reconciled_without_second_launch(self):
        def uncertain(args, **kwargs):
            result = self.runner(args, **kwargs)
            if args[1]=='bootstrap':
                raise TimeoutError('reply lost after actual launch')
            return result
        with self.assertRaises(TimeoutError):
            activation.activate(**self.args,runner=uncertain)
        self.assertEqual(json.loads(self.receipt.read_text())['state'],'launch_unknown')
        self.assertEqual(activation.activate(**self.args,runner=self.runner)['state'],'active')
        self.assertEqual(sum(args[1]=='bootstrap' for args in self.calls),1)

    def test_failed_bootstrap_is_not_retried(self):
        def failed(args, **kwargs):
            self.calls.append(args)
            return SimpleNamespace(returncode=1,stdout='')
        with self.assertRaises(ValueError):
            activation.activate(**self.args,runner=failed)
        with self.assertRaises(ValueError):
            activation.activate(**self.args,runner=failed)
        self.assertEqual(sum(args[1]=='bootstrap' for args in self.calls),1)

    def test_foreign_agent_is_preserved(self):
        self.agent.parent.mkdir(parents=True)
        self.agent.write_text('foreign configuration')
        with self.assertRaises(ValueError):
            activation.activate(**self.args,runner=self.runner)
        self.assertEqual(self.agent.read_text(),'foreign configuration')
        self.assertFalse(self.config.exists())

    def test_expired_first_slot_requires_new_free_proposal(self):
        with self.assertRaises(ValueError):
            activation.activate(**{**self.args,'now':datetime(2026,11,14,tzinfo=timezone.utc)},runner=self.runner)
        self.assertFalse(self.config.exists())

    def test_existing_different_activation_is_preserved(self):
        self.config.parent.mkdir(parents=True)
        self.config.write_text('{"enabled":false}')
        with self.assertRaises(ValueError):
            activation.activate(**self.args,runner=self.runner)
        self.assertEqual(self.config.read_text(),'{"enabled":false}')
