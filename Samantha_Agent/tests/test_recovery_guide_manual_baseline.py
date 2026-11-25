from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import json,unittest
from app import recovery_guide_runtime_config as c
from app.recovery_guide_sources import canonical_json,digest
from app.file_persistence import atomic_write_json

class ManualBaseline(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.configpath=self.root/'activation.json'
        self.before={'enabled':True,'bootstrap':{'path':'old','sha256':'a'*64},'limits':{'run_credits':200},'runtime_evidence':{'server_version':'old'},'unchanged':'keep'}
        self.configpath.write_text(canonical_json(self.before));self.configpath.chmod(0o600)
        self.home=self.root/'home';cfg=self.owned()[0]
        for path in cfg.destinations:path.parent.mkdir(parents=True,exist_ok=True);path.write_text('manual guide')
        self.status={'state':'uploaded','candidate_sha256':digest('manual guide'),'approval_sha256':'b'*64}
        self.enterContext(patch('app.recovery_guide_revalidation.owned_configuration',side_effect=self.owned))
        self.enterContext(patch.object(c,'validate_payload',side_effect=lambda value:value))
        self.enterContext(patch('app.recovery_guide_publication.PublicationStore',side_effect=lambda *a,**k:SimpleNamespace(status=lambda request:self.status)))
        self.cloud={'available':True,'ubiquitous':True,'uploaded':True,'uploading':False,'upload_error':False}
    def owned(self):return c.RuntimeConfig(self.configpath,canonical_json(json.loads(self.configpath.read_text())),self.root,self.home),'agent'
    def adopt(self,**extra):
        options={'request_id':'manual-fixture','expected_activation_sha256':digest(canonical_json(self.before)),'confirmed':True,'cloud_audit':lambda path:self.cloud};options.update(extra);return c.adopt_manual_guide(**options)
    def test_only_bootstrap_changes_and_replay_does_not_write_again(self):
        result=self.adopt();self.assertEqual(result['state'],'completed');after=json.loads(self.configpath.read_text())
        self.assertEqual({k:v for k,v in after.items() if k!='bootstrap'},{k:v for k,v in self.before.items() if k!='bootstrap'})
        self.assertEqual(after['bootstrap']['sha256'],digest('manual guide'));self.assertEqual(self.adopt(),result)
    def test_no_current_confirmation_or_changed_config(self):
        for options in ({'confirmed':False},{'expected_activation_sha256':'f'*64}):
            with self.assertRaises(ValueError):self.adopt(**options)
        self.assertEqual(json.loads(self.configpath.read_text()),self.before)
    def test_existing_weekly_history_never_reset(self):
        directory=self.root/'schedule';directory.mkdir();record=directory/'recovery-2026-W47.json';record.write_text('preserve')
        with self.assertRaises(ValueError):self.adopt()
        self.assertEqual(record.read_text(),'preserve');self.assertEqual(json.loads(self.configpath.read_text()),self.before)
    def test_not_uploaded_or_foreign_copy_refused(self):
        self.status['state']='pending_icloud'
        with self.assertRaises(ValueError):self.adopt()
        self.status['state']='uploaded';self.owned()[0].destinations[0].write_text('foreign edit')
        with self.assertRaises(ValueError):self.adopt()
        self.assertEqual(json.loads(self.configpath.read_text()),self.before)
    def test_cloud_not_confirmed_refused(self):
        self.cloud['uploaded']=False
        with self.assertRaises(ValueError):self.adopt()
        self.assertEqual(json.loads(self.configpath.read_text()),self.before)
    def test_lost_final_receipt_is_resolved_by_current_config_without_reapplying(self):
        writes=[]
        def writer(path,value,*args,**kwargs):
            writes.append(Path(path))
            if Path(path).name=='manual-fixture.json' and value.get('state')=='completed':raise OSError('receipt lost')
            return atomic_write_json(path,value,*args,**kwargs)
        with patch('app.file_persistence.atomic_write_json',side_effect=writer):
            with self.assertRaises(OSError):self.adopt()
        self.assertEqual(writes.count(self.configpath),1)
        self.assertEqual(self.adopt()['state'],'completed')
        self.assertEqual(writes.count(self.configpath),1)
