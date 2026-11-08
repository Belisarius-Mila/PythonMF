from dataclasses import asdict
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app import recovery_guide_activation as a
from app import recovery_guide_maintainer as m
from app.recovery_guide_sources import canonical_json,digest
from tests.test_recovery_guide_quality import ORIGINAL
from tests.test_recovery_guide import CLOUD


class Activation(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name).resolve()
        self.home=self.root/'home';self.home.mkdir();self.project=self.root/'project';self.project.mkdir()
        for name in ('config','.venv/bin','scripts','.venv/recovery_rec06_trial'):(self.project/name).mkdir(parents=True,exist_ok=True)
        (self.project/'config/agent_roles.json').write_text('{"schema":1,"roles":{}}')
        (self.project/'.venv/bin/python').write_text('#!/bin/sh\n');(self.project/'.venv/bin/python').chmod(0o755)
        (self.project/'scripts/recovery_guide.py').write_text('# fixture')
        (self.project/'.venv/recovery_rec06_trial/receipt.json').write_text('{"state":"trial_passed","accepted":true}')
        self.enterContext(patch.object(a,'ROOT',self.project));self.enterContext(patch.object(a,'STATE',self.project/'.venv/activation'))
        self.enterContext(patch.object(a,'_implementation',return_value={'fixture':'v1'}))
        self.enterContext(patch.object(a.live.subprocess,'check_output',return_value='Test OS\n'))
        self.seed=self.root/'seed.txt';self.seed.write_text(ORIGINAL)
        self.cost=self.root/'cost.json';self.cost.write_text(canonical_json({'source_head':'a'*40,'source_count':2,
            'seed_sha256':digest(ORIGINAL),'reserved_credits':3.0,'planned_calls':2,
            'provisional_limits_not_approved':asdict(m.Limits(40000,2000,8,10,100,60)),
            'tokenizer':{'package_version':'test','encoding':'o200k_base','margin':1.2,'reference_uncertainty_accepted':True}}))
        self.now=datetime(2026,11,8,12,tzinfo=timezone.utc);self.first=self.now+timedelta(days=7)
        for path in a.target_preview(self.home,self.home/'Desktop/PythonMF').values():
            if isinstance(path,str) and path.endswith('OBNOVA_SAMANTHY_NOVY_MAC.txt'):Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.loaded=False;self.launches=0;self.fail_launch=False

    def prepare(self):return a.prepare(cost_path=self.cost,seed=self.seed,run_credits=10,month_credits=100,
        first_due=self.first,applications=['Python','Codex'],runtime_evidence={'server_version':'test','protocol_sha256':'b'*64,
            'input_tokens':40000,'reference':'accepted fixture context'},macos_baseline='Test OS',home=self.home,now=self.now)

    def runner(self,args,**kwargs):
        if args[1]=='print':
            listing='\n'.join(a.launch_agent(self.project)['ProgramArguments']) if self.loaded else ''
            return SimpleNamespace(returncode=0 if self.loaded else 1,stdout=listing)
        self.assertEqual(args[1],'bootstrap');self.launches+=1;self.loaded=not self.fail_launch
        return SimpleNamespace(returncode=0 if self.loaded else 1,stdout='')

    def activate(self,card,**kwargs):
        args={'proposal_sha256':card['proposal_sha256'],'confirmation':a.CONFIRMATION,'runner':self.runner,
            'cloud_audit':lambda _:CLOUD,'now':self.now};args.update(kwargs)
        return a.activate(**args)

    def test_prepare_is_inert_and_leaves_actual_activation_role_and_launchagent_untouched(self):
        old=(self.project/'config/agent_roles.json').read_bytes();card=self.prepare()
        self.assertEqual(card['state'],'awaiting_safety_and_budget_confirmation')
        self.assertFalse((self.project/'data/private/recovery_guide_runtime/activation.json').exists())
        self.assertFalse((self.home/'Library/LaunchAgents/com.samantha.recovery-guide.plist').exists())
        self.assertEqual((self.project/'config/agent_roles.json').read_bytes(),old);self.assertEqual(self.launches,0)

    def test_wrong_safety_confirmation_never_changes_files_or_launches(self):
        card=self.prepare()
        with self.assertRaisesRegex(ValueError,'exact_safety_confirmation'):self.activate(card,confirmation='Aktivuj')
        self.assertFalse((self.project/'data').exists());self.assertEqual(self.launches,0)

    def test_exact_activation_publishes_two_copies_and_installs_only_once_without_model(self):
        card=self.prepare();result=self.activate(card);self.assertEqual(result['state'],'active')
        paths=card['targets'];self.assertEqual(Path(paths[0]).read_bytes(),Path(paths[1]).read_bytes())
        self.assertEqual(digest(Path(paths[0]).read_bytes()),card['candidate_sha256'])
        self.assertEqual(self.activate(card)['state'],'active');self.assertEqual(self.launches,1)
        self.assertEqual(result['paid_model_calls'],0)

    def test_pending_cloud_defers_launch_and_resumes_without_a_second_model(self):
        card=self.prepare();result=self.activate(card,cloud_audit=lambda _:{**CLOUD,'uploaded':False})
        self.assertEqual(result['state'],'baseline_pending_icloud');self.assertEqual(self.launches,0)
        self.assertEqual(self.activate(card)['state'],'active');self.assertEqual(self.launches,1)

    def test_launch_uncertainty_never_bootstraps_a_second_time(self):
        card=self.prepare();self.fail_launch=True
        self.assertEqual(self.activate(card)['state'],'launch_outcome_unknown_operator_required')
        self.assertEqual(self.activate(card)['state'],'launch_outcome_unknown_operator_required')
        self.assertEqual(self.launches,1)

    def test_foreign_target_or_role_edit_blocks_before_installation(self):
        card=self.prepare();Path(card['targets'][0]).write_text('User edit')
        with self.assertRaisesRegex(ValueError,'target_changed'):self.activate(card)
        self.assertEqual(self.launches,0);self.assertFalse((self.project/'data').exists())

    def test_other_role_edit_is_not_overwritten(self):
        card=self.prepare();role=self.project/'config/agent_roles.json';role.write_text('{"schema":1,"roles":{"other":{}}}')
        with self.assertRaisesRegex(ValueError,'other_roles_changed'):self.activate(card)
        self.assertEqual(self.launches,0)

    def test_changed_code_or_expired_first_slot_requires_new_preparation(self):
        card=self.prepare()
        with patch.object(a,'_implementation',return_value={'fixture':'changed'}):
            with self.assertRaisesRegex(ValueError,'proposal_changed'):self.activate(card)
        with self.assertRaisesRegex(ValueError,'first_slot_requires_refresh'):self.activate(card,now=self.first)


if __name__=='__main__':unittest.main()
