"""Italian TTS plan, exact reuse and crash-safe requests; no online synthesis."""
from __future__ import annotations
import copy
import importlib.util
import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'VocabularyIT'))
import vocabulary_it_audio as a

ITEMS=[{'uid':'vit-0353','it':'tempo','cz':'čas','sentenceIt':'Non ho tempo.','sentenceCz':'Nemám čas.'},
       {'uid':'vit-0491','it':'tempo','cz':'počasí','sentenceIt':'Oggi il tempo è bello.','sentenceCz':'Dnes je pěkné počasí.'}]


class VocabularyItalianAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ffmpeg=shutil.which('ffmpeg')
        if not ffmpeg or not shutil.which('ffprobe'):raise unittest.SkipTest('Audio fixtures require FFmpeg/ffprobe.')
        cls.scratch=tempfile.TemporaryDirectory();cls.fixture=Path(cls.scratch.name)/'fixture.mp3'
        subprocess.run([ffmpeg,'-v','error','-f','lavfi','-i','sine=frequency=440:duration=0.4','-ac','1','-ar','24000','-b:a','48k',str(cls.fixture)],check=True)
        cls.audio=cls.fixture.read_bytes()
    @classmethod
    def tearDownClass(cls):cls.scratch.cleanup()

    def test_complete_plan_keeps_all_four_references_and_reuses_only_exact_pronunciation(self):
        p=a.plan(ITEMS)
        self.assertEqual((p['stats']['references'],p['stats']['uniqueAssets']),(8,7))
        w=p['manifests']['words']['items'];self.assertEqual(w['vit-0353']['it'],w['vit-0491']['it'])
        self.assertNotEqual(w['vit-0353']['cz'],w['vit-0491']['cz'])
        self.assertNotEqual(a.asset_path('it','words','tempo'),a.asset_path('it','sentences','tempo'))
        self.assertNotEqual(a.asset_path('it','words','tempo'),a.asset_path('it','words','témpo'))
        self.assertNotEqual(a.asset_path('it','words','tempo'),a.asset_path('it','words','tempo',{'it':'it-IT-DiegoNeural','cz':a.VOICES['cz']}))
        self.assertEqual(a.text('Dov’è il bagno?','sentences'),'Dov’è il bagno?')
        self.assertEqual(a.text('příliš / moc','words'),'příliš. moc')
        for value in ['',None,'x'*1501]:
            with self.assertRaises(ValueError):a.text(value,'words')

    def test_explicit_provider_changes_metadata_without_replacing_any_existing_asset(self):
        edge=a.plan(ITEMS)
        mixed=a.plan(ITEMS,provider='registered-edge-tts+azure-neural')
        self.assertEqual(edge['jobs'],mixed['jobs'])
        self.assertEqual(edge['stats'],mixed['stats'])
        self.assertNotEqual(edge['digest'],mixed['digest'])
        self.assertEqual(mixed['manifests']['words']['provider'],'registered-edge-tts+azure-neural')
        with self.assertRaises(ValueError):a.plan(ITEMS,provider='unknown-service')

    def test_requested_receipt_precedes_transport_and_completed_jobs_resume_without_calls(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);receipt=root/'private/receipt.json';p=a.plan(ITEMS);calls=[]
            def synth(text,**kwargs):
                ledger=json.loads(receipt.read_text());self.assertTrue(any(v['state']=='requested' for v in ledger['jobs'].values()));calls.append((text,kwargs));return self.audio
            result=a.build(p,root/'web',receipt,synthesize=synth,workers=1)
            self.assertTrue(result['complete']);self.assertEqual(len(calls),7)
            for kind,name in [('words','vocabulary-it-audio.json'),('sentences','vocabulary-it-sentence-audio.json')]:
                manifest=json.loads((root/'web/data'/name).read_text());self.assertEqual(manifest['kind'],kind);self.assertEqual(len(manifest['assetSha256']),len({r[l] for r in manifest['items'].values() for l in ('it','cz')}))
            again=a.build(p,root/'web',receipt,synthesize=lambda *args,**kwargs:self.fail('must not resynthesize'),workers=1)
            self.assertEqual(again['generated'],0);self.assertEqual(again['verifiedExisting'],7)

    def test_uncertain_request_stops_whole_resume_before_any_new_external_call(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);receipt=root/'receipt.json';p=a.plan(ITEMS);calls=[]
            def broken(*args,**kwargs):calls.append(args);raise RuntimeError('transport lost')
            with self.assertRaises(RuntimeError):a.build(p,root/'web',receipt,synthesize=broken,workers=1)
            self.assertEqual(len(calls),1);ledger=json.loads(receipt.read_text());self.assertEqual(list(ledger['jobs'].values())[0]['state'],'uncertain')
            with self.assertRaisesRegex(ValueError,'Nejistý'):a.build(p,root/'web',receipt,synthesize=broken,workers=1)
            self.assertEqual(len(calls),1);self.assertFalse((root/'web/data/vocabulary-it-audio.json').exists())

    def test_partial_subset_never_replaces_public_complete_manifests(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);receipt=root/'receipt.json';p=a.plan(ITEMS)
            result=a.build(p,root/'web',receipt,synthesize=lambda *args,**kwargs:self.audio,uids=['vit-0353'],limit=1,workers=1)
            self.assertFalse(result['complete']);self.assertEqual(result['missing'],6)
            self.assertFalse((root/'web/data/vocabulary-it-audio.json').exists())
            changed=a.plan([{**ITEMS[0],'cz':'jiný význam'},ITEMS[1]])
            with self.assertRaisesRegex(ValueError,'jinému zdroji'):a.build(changed,root/'web',receipt,synthesize=lambda *args,**kwargs:self.fail('must not call'))

    def test_exact_existing_czech_record_is_copied_without_transport(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);p=a.plan(ITEMS);job=next(j for j in p['jobs'].values() if j['language']=='it')
            reuse={(job['voice'],job['rate'],job['text']):self.fixture}
            result=a.build(p,root/'web',root/'receipt.json',synthesize=lambda *args,**kwargs:self.audio,reuse=reuse,workers=1)
            self.assertEqual(result['reused'],1);self.assertTrue(result['complete'])

    def test_completed_hash_or_missing_file_cannot_be_silently_replaced(self):
        for mode in ('hash','missing'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as name:
                root=Path(name);p=a.plan(ITEMS);receipt=root/'receipt.json'
                a.build(p,root/'web',receipt,synthesize=lambda *args,**kwargs:self.audio,limit=1,workers=1)
                relative=next(iter(json.loads(receipt.read_text())['jobs']));target=root/'web'/relative
                if mode=='hash':target.write_bytes(b'changed')
                else:target.rename(target.with_suffix('.saved'))
                with self.assertRaises(ValueError):a.build(p,root/'web',receipt,synthesize=lambda *args,**kwargs:self.fail('must not call'),workers=1)

    def test_file_lock_and_source_guard_prevent_duplicate_or_stale_requests(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);p=a.plan(ITEMS);receipt=root/'receipt.json';calls=[]
            def synth(*args,**kwargs):
                calls.append(args)
                with self.assertRaisesRegex(ValueError,'už pracuje'):a.build(p,root/'web',receipt,synthesize=lambda *a,**k:self.fail('second transport'))
                return self.audio
            a.build(p,root/'web',receipt,synthesize=synth,limit=1,workers=1);self.assertEqual(len(calls),1)
            with self.assertRaisesRegex(ValueError,'Zdroj se změnil'):a.build(p,root/'web',receipt,synthesize=lambda *a,**k:self.fail('stale transport'),source_guard=lambda:False,workers=1)

    def test_registered_endpoint_is_restored_even_after_error(self):
        import edge_tts.communicate as communicate
        previous=communicate.WSS_URL
        with self.assertRaises(RuntimeError):
            with a.registered_generator():
                self.assertEqual(communicate.WSS_URL,previous);raise RuntimeError('probe')
        self.assertEqual(communicate.WSS_URL,previous)
        with a.registered_generator(alternate_endpoint=True):self.assertTrue(communicate.WSS_URL.startswith(a.ENDPOINT+'?'))
        self.assertEqual(communicate.WSS_URL,previous)

    def test_sources_validate_against_current_catalog_before_planning(self):
        items=a.load_items(ROOT,ROOT/'docs');self.assertEqual(len(items),497)
        with tempfile.TemporaryDirectory() as name:
            out=Path(name);(out/'data').mkdir();data=json.loads((ROOT/'docs/data/vocabulary-it-v2.json').read_text());data['items'][0]['sentenceIt']='Different sentence';(out/'data/vocabulary-it-v2.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'význam nebo věty'):a.load_items(ROOT,out)

    def test_complete_production_library_matches_all_current_texts_voices_and_hashes(self):
        items=a.load_items(ROOT,ROOT/'docs');expected=a.plan(items);all_paths=set()
        self.assertEqual(expected['stats']['references'],1988)
        self.assertEqual(expected['stats']['uniqueAssets'],1907)
        for kind,name in [('words','vocabulary-it-audio.json'),('sentences','vocabulary-it-sentence-audio.json')]:
            manifest=json.loads((ROOT/'docs/data'/name).read_text())
            self.assertEqual(manifest['status'],'complete')
            for field in ('schemaVersion','language','kind','rate','voices','items','sourceDigest'):
                self.assertEqual(manifest[field],expected['manifests'][kind][field])
            for path,sha in manifest['assetSha256'].items():
                full=ROOT/'docs'/path
                self.assertTrue(full.is_file());self.assertGreater(full.stat().st_size,1000)
                self.assertEqual(a.digest(full),sha);all_paths.add(path)
        self.assertEqual(all_paths,set(expected['jobs']))
        self.assertEqual(len(all_paths),1907)
        for kind in ('words','sentences'):
            for lang in ('it','cz'):
                path=next(iter(expected['manifests'][kind]['items'].values()))[lang]
                self.assertTrue(a.valid_audio(ROOT/'docs'/path))


if __name__=='__main__':unittest.main()
