from pathlib import Path
from tempfile import TemporaryDirectory
import json,unittest
from unittest.mock import patch
from app import recovery_guide_service_archive as a

class Archive(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.source=self.root/'source.json';self.source.write_text('{"private":"preserve"}')
        self.enterContext(patch.object(a,'ROOT',self.root));self.enterContext(patch.object(a,'sources',return_value=[(self.source,'runtime/activation.json')]))
    def test_owned_files_are_preserved_with_manifest_and_never_replaced_on_replay(self):
        result=a.preserve(request_id='service-archive-fixture');self.assertEqual(result['state'],'complete')
        target=self.root/'data/private/recovery-service-archives/service-archive-fixture/runtime/activation.json'
        self.assertEqual(target.read_bytes(),self.source.read_bytes());self.assertEqual(target.stat().st_mode&0o777,0o600)
        self.source.write_text('new live state');self.assertEqual(a.preserve(request_id='service-archive-fixture'),result)
    def test_source_alias_and_destination_alias_refused(self):
        alias=self.root/'alias';alias.symlink_to(self.source)
        with patch.object(a,'sources',return_value=[(alias,'alias.json')]):
            with self.assertRaises(ValueError):a.preserve(request_id='service-source-alias')
        root=self.root/'elsewhere';root.mkdir();(self.root/'data/private/recovery-service-archives/alias-target-fixture').symlink_to(root,target_is_directory=True)
        with self.assertRaises(ValueError):a.preserve(request_id='alias-target-fixture')
    def test_mutated_archive_and_path_escape_do_not_verify(self):
        a.preserve(request_id='service-archive-fixture');path=self.root/'data/private/recovery-service-archives/service-archive-fixture'
        (path/'runtime/activation.json').write_text('corrupted')
        with self.assertRaises(ValueError):a.verify(path)
        manifest=json.loads((path/'manifest.json').read_text());manifest['files'][0]['relative']='../outside';(path/'manifest.json').write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):a.verify(path)
    def test_no_silent_size_truncation(self):
        with patch.object(a,'MAX_BYTES',1):
            with self.assertRaises(ValueError):a.preserve(request_id='service-archive-fixture')
        self.assertEqual(self.source.read_text(),'{"private":"preserve"}')
