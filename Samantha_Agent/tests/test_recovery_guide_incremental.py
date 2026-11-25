"""Sunday clock, real Git deltas, publication and idempotence without a provider."""
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
import json
import subprocess
import unittest
from unittest.mock import Mock, patch

from app import recovery_guide_incremental as delta
from app import recovery_guide_runtime_live as live
from app.file_persistence import atomic_write_json
from app.recovery_guide_scheduler import ANALYSIS_READY, ZONE
from tests import test_recovery_guide_runtime as existing
from tests.test_recovery_guide import CLOUD, USAGE
from tests.test_recovery_guide_quality import ORIGINAL


class IncrementalWeeks(unittest.TestCase):
    def setUp(self):
        fixture=existing.Configuration()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.project=fixture.project
        self.git('init','-q','-b','main')
        self.write_commit('docs/restore.md','Původní postup obnovy.')
        base=self.git('rev-parse','HEAD')
        cfg=fixture.save()
        fixture.value['publication_policy']={'mode':'validated_auto_v1','applications':['Samantha'],
                                            'macos_baseline':'test OS'}
        for path in cfg.destinations:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(ORIGINAL)
        fixture.value['bootstrap']={'path':str(cfg.destinations[0]),'sha256':delta.digest(ORIGINAL)}
        fixture.value['schedule']['not_before']='2026-11-29T08:00:00+00:00'
        self.cfg=fixture.save()
        atomic_write_json(cfg.root/'incremental.json',{'version':1,'base_head':base})
        self.runtime,self.counter=live.build(self.cfg,runtime_type=delta.IncrementalRuntime)
        self.addCleanup(self.counter.close)
        self.runtime.count=lambda text:max(1,len(text)//3)
        self.runtime.cloud_audit=lambda _:CLOUD
        self.runtime.delivery_readiness=lambda:{k:True for k in ANALYSIS_READY}
        self.runtime.readiness=Mock(return_value={k:True for k in ANALYSIS_READY})
        self.wire=Mock()
        @contextmanager
        def transport(directory,executor,*,assert_current):
            self.assertTrue(assert_current())
            yield self.wire
        self.runtime.call_factory=transport
        real=subprocess.check_output
        def stub(args,*a,**kw):
            return 'test OS\n' if args[0]=='/usr/bin/sw_vers' else real(args,*a,**kw)
        self.enterContext(patch.object(subprocess,'check_output',side_effect=stub))
        self.sunday=datetime(2026,11,29,9,tzinfo=ZONE)

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.project),*args],text=True).strip()

    def write_commit(self,name,text):
        path=self.project/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(text+'\n')
        self.git('add','--',name)
        self.git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture')

    def test_no_relevant_changes_without_model_and_replay(self):
        self.write_commit('docs/classroom.md','Procvičte obrázky zvířat.')
        self.write_commit('Samantha_Agent/data/private/install.md','Soukromé informace')
        self.write_commit('Samantha_Agent/memory/projects/interior_architect/MIGRATION.md','Migrace návrhů')
        self.assertEqual(self.runtime.tick(self.sunday-timedelta(seconds=1))['state'],'not_due')
        job=self.runtime.tick(self.sunday)
        self.assertEqual((job['state'],job['source_count'],job['reserved_credits']),('completed_no_change',0,0))
        self.assertEqual(job['source_head'],self.git('rev-parse','HEAD'))
        self.runtime.readiness.assert_not_called()
        self.wire.assert_not_called()
        self.assertEqual(self.runtime.tick(self.sunday)['action'],'replayed_receipt')
        self.assertTrue(all(p.read_text()==ORIGINAL for p in self.cfg.destinations))

    def test_only_changed_procedure_is_published_once_then_next_week_is_free(self):
        text='Po obnově ověř dostupnost místního úložiště.'
        self.write_commit('docs/restore.md',text)
        self.wire.return_value={'usage':USAGE,'answer':{'edits':[{'section':'c01','block':0,'action':'insert',
            'text':text,'status':'documented','evidence':[{'source':'docs/restore.md','quote':text}]}]}}
        job=self.runtime.tick(self.sunday)
        self.assertEqual(job['state'],'completed',job)
        self.assertEqual(self.wire.call_count,1)
        payload,kind=self.wire.call_args.args
        self.assertEqual(kind,'amend')
        self.assertEqual({s['path'] for s in payload['changes']},{'docs/restore.md','docs/restore.md (původní znění)'})
        for path in self.cfg.destinations:self.assertIn(text,path.read_text())
        self.assertEqual(self.cfg.destinations[0].read_bytes(),self.cfg.destinations[1].read_bytes())
        self.assertEqual(self.runtime.tick(self.sunday+timedelta(days=7))['state'],'completed_no_change')
        self.assertEqual(self.wire.call_count,1)

    def test_reviewed_diff_can_have_no_effect_on_guide(self):
        self.write_commit('docs/restore.md','Titulek pro obnovu.')
        self.wire.return_value={'usage':USAGE,'answer':{'edits':[]}}
        job=self.runtime.tick(self.sunday)
        self.assertEqual(job['state'],'completed_no_change',job)
        self.assertEqual(job['reported_model_turns'],1)
        self.assertTrue(all(p.read_text()==ORIGINAL for p in self.cfg.destinations))

    def test_failed_send_never_replayed(self):
        self.write_commit('docs/restore.md','Změněný instalační postup.')
        self.wire.side_effect=TimeoutError()
        self.assertEqual(self.runtime.tick(self.sunday)['state'],'attention')
        self.assertEqual(self.runtime.tick(self.sunday)['action'],'operator_attention')
        self.assertEqual(self.wire.call_count,1)

    def test_divergent_copies_do_not_advance_cursor(self):
        self.cfg.destinations[1].write_text('Jiná kopie')
        self.assertEqual(self.runtime.tick(self.sunday)['state'],'attention')
        self.assertFalse(list(self.runtime.scheduler.root.glob('recovery-*.json')))
        self.wire.assert_not_called()

    def test_explicit_supersession_keeps_before_image_and_next_sunday_can_run(self):
        from app import recovery_guide_known_result as repair
        from app.recovery_guide_sources import digest
        self.write_commit('docs/restore.md','Nový postup obnovy.')
        self.wire.side_effect=TimeoutError()
        job=self.runtime.tick(self.sunday)
        self.assertEqual(job['state'],'attention')
        scope=self.cfg.root
        path=scope/'schedule'/(job['request_id']+'.json')
        before=path.read_bytes()
        main=delta._git(repair.ROOT,'rev-parse','HEAD').decode().strip()
        # The legacy failed job preceded incremental activation.
        (scope/'incremental.json').rename(scope/'simulated-policy-before.json')
        with patch.object(repair,'owned_configuration',return_value=(self.cfg,'')), \
                patch.object(repair,'_install_committed') as install, \
                patch('app.recovery_guide_publish.icloud_metadata',return_value=CLOUD):
            args={'expected_main_head':main,'request_id':job['request_id'],'confirmed':True}
            with self.assertRaises(ValueError):
                repair.activate_incremental(**args,expected_job_sha256='0'*64)
            install.assert_not_called()
            approved=repair.activate_incremental(**args,expected_job_sha256=digest(before))
            self.assertEqual(approved,repair.activate_incremental(**args,expected_job_sha256=digest(before)))
            install.assert_called_once()
        retained=json.loads(path.read_text())
        self.assertEqual(retained['state'],'superseded')
        self.assertEqual(retained['reserved_credits'],job['reserved_credits'])
        original=scope/'incremental-migration'/job['request_id']/'previous-job.json'
        self.assertEqual(original.read_bytes(),before)
        self.assertEqual(self.runtime.tick(self.sunday)['action'],'replayed_receipt')
        self.assertEqual(self.runtime.tick(self.sunday+timedelta(days=7))['state'],'completed_no_change')
        self.assertEqual(self.wire.call_count,1)


class WireContract(unittest.TestCase):
    def test_live_adapter_uses_simple_edit_schema_and_standard_tier(self):
        fx=existing.TransportBinding()
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        with fx.binding() as send:
            send({'guide_layout':{},'changes':[]},'amend')
        turns=[params for name,params in fx.wire.calls if name=='turn/start']
        self.assertEqual(len(turns),1)
        self.assertEqual(turns[0]['outputSchema'],delta.EDIT_SCHEMA)
        self.assertEqual(turns[0]['serviceTierForTurn'],'default')
        self.assertEqual(turns[0]['sandboxPolicy'],{'type':'readOnly','networkAccess':False})
        self.assertNotIn('anyOf',json.dumps(turns[0]['outputSchema']))
