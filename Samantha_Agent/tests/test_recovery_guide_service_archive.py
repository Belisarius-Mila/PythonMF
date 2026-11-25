from pathlib import Path
from tempfile import TemporaryDirectory
import json,unittest
from unittest.mock import patch
from app import recovery_guide_service_archive as a

class Archive(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.source=self.root/'source.json';self.source.write_text('{"private":"preserve"}')
        self.sources_function=a.sources
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
    def test_preserved_proof_names_survive_standard_recovery_exclusions(self):
        import plistlib
        from types import SimpleNamespace
        from app.backup.incremental import FilterRules,ALWAYS_FILTER
        home=self.root/'home';project=self.root/'owned-project';state=project/'state';state.mkdir(parents=True)
        bootstrap=self.root/'guide.txt';bootstrap.write_text('guide')
        names=('.venv/recovery_rec06_peer_schema/v2/TurnStartParams.json','.venv/recovery_rec06_peer_schema/v2/ThreadStartResponse.json','.venv/recovery_rec06_cli/node_modules/@openai/codex/package.json','.venv/recovery_rec06_disabled_features.txt')
        for name in names:path=project/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('proof')
        config=SimpleNamespace(project=project,root=state,payload={'bootstrap':{'path':str(bootstrap)}})
        # Use the real source selector; the outer fixture's generic source mock
        # is restored for the archive-copy tests.
        from app.recovery_guide_service_archive import sources
        original=self.sources_function
        with patch.object(a,'owned_configuration',return_value=(config,'agent')),patch('pathlib.Path.home',return_value=home):rows=original()
        rules=FilterRules.from_files([ALWAYS_FILTER])
        self.assertEqual(len(rows),5)
        self.assertTrue(all(not rules.is_excluded(Path(relative),False) for _,relative in rows))

    def test_no_silent_size_truncation(self):
        with patch.object(a,'MAX_BYTES',1):
            with self.assertRaises(ValueError):a.preserve(request_id='service-archive-fixture')
        self.assertEqual(self.source.read_text(),'{"private":"preserve"}')
