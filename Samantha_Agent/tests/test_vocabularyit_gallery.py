"""Italian web assets and real gallery/learner code through the DOM harness."""
from __future__ import annotations
import hashlib
import json
import copy
import sys
from pathlib import Path
import subprocess
import unittest
from PIL import Image
from scripts.cockpit_quality_gate import node_binary

ROOT=Path(__file__).resolve().parents[2]
DOCS=ROOT/'docs'
sys.path.insert(0,str(ROOT/'VocabularyIT'))
import vocabulary_it_practice as practice


class VocabularyItalianGalleryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((DOCS/'data/vocabulary-it-v2.json').read_text())

    def test_all_497_cards_have_accepted_complete_italian_data(self):
        data=self.data
        self.assertEqual((data['schemaVersion'],data['language'],data['appName']),(2,'it','VocabularyIT'))
        self.assertEqual((data['itemCount'],data['sourceRowCount']),(497,471))
        self.assertEqual(len({item['uid'] for item in data['items']}),497)
        self.assertTrue(data['imageReviewComplete']);self.assertEqual(data['mode'],'release')
        self.assertEqual(data['stats']['pendingImageReview'],0)
        self.assertTrue(all(item['active'] and item['imageReviewed'] and item['sentenceIt'] and item['sentenceCz'] for item in data['items']))
        self.assertEqual(data['stats']['teachingTypes'],{'word':482,'interaction':15})
        for item in data['items']:
            self.assertNotIn('en',item);self.assertNotIn('L',item);self.assertNotIn('HT',item)

    def test_all_814_visual_assets_decode_and_match_case_hash_and_dimensions(self):
        refs={}
        for item in self.data['items']:
            refs[item['image']]=900;refs[item['thumbnail']]=240
        self.assertEqual(len(refs),814)
        for relative,limit in refs.items():
            path=DOCS/relative
            self.assertTrue(relative.startswith('assets/vocabulary-it-v2/'))
            self.assertIn(path.name,{p.name for p in path.parent.iterdir()})
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),path.stem)
            with Image.open(path) as im:
                im.load();self.assertLessEqual(max(im.size),limit)

    def test_page_modules_are_local_and_both_audio_kinds_are_ready(self):
        html=(DOCS/'vocabulary-it/index.html').read_text()
        for name in ('model.js','learners.js','learner-ui.js','practice.js','gallery.js','gallery.css'):
            self.assertIn(name,html)
            self.assertTrue((DOCS/'vocabulary-it'/name).is_file())
        for kind,name in [('words','vocabulary-it-audio.json'),('sentences','vocabulary-it-sentence-audio.json')]:
            manifest=json.loads((DOCS/'data'/name).read_text())
            self.assertEqual((manifest['language'],manifest['kind'],manifest['status']),('it',kind,'complete'))
            self.assertEqual(len(manifest['items']),497)
        self.assertEqual(self.data['audioStatus'],'complete')
        self.assertIn('lang="it"',html)
        self.assertNotIn('vocabulary-en',html)
        css=(DOCS/'vocabulary-it/gallery.css').read_text()
        self.assertIn('repeat(2,minmax(0,1fr))',css)
        self.assertIn('repeat(8,minmax(0,1fr))',css)

    def test_practice_data_exactly_matches_all_words_images_and_reviewed_spelling(self):
        spelling=json.loads((ROOT/'VocabularyIT/vocabulary_it_spelling.json').read_text())
        self.assertEqual(spelling['sourceDataSha256'],hashlib.sha256((DOCS/'data/vocabulary-it-v2.json').read_bytes()).hexdigest())
        expected=practice.build(self.data,spelling)
        self.assertEqual(json.loads((DOCS/'data/vocabulary-it-quiz.json').read_text()),expected)
        self.assertEqual(len(expected['entries']),497)
        self.assertEqual(sum(e['reviewed'] for e in expected['entries'].values()),495)
        self.assertEqual({e['it'] for e in expected['entries'].values() if not e['reviewed']},{'éclair','brioche'})
        self.assertEqual(expected['entries']['vit-0320']['pieces'],['la','var','si'])
        self.assertEqual(expected['entries']['vit-0285']['pieces'],['caf','fè'])
        self.assertEqual(expected['entries']['vit-0400']['pieces'],['li','bre','ri','a'])

    def test_practice_builder_rejects_stale_text_missing_uid_or_unreviewed_segmentation(self):
        original=json.loads((ROOT/'VocabularyIT/vocabulary_it_spelling.json').read_text())
        for kind in ('missing','text','pieces','unreviewed','homograph'):
            with self.subTest(kind=kind):
                changed=copy.deepcopy(original)
                if kind=='missing':changed['entries'].pop('vit-0001')
                elif kind=='text':changed['entries']['vit-0001']['cz']='jiný význam'
                elif kind=='pieces':changed['entries']['vit-0320']['pieces']=['lavarsi!']
                elif kind=='unreviewed':changed['entries']['vit-0320']['reviewed']=False
                else:changed['entries']['vit-0479']['pieces']=['macchina']
                with self.assertRaises(ValueError):practice.build(self.data,changed)

    def test_real_gallery_and_learner_javascript_scenarios(self):
        completed=subprocess.run([node_binary(),'--test','tests/test_vocabularyit_selection.js'],
                                 cwd=ROOT/'Samantha_Agent',capture_output=True,text=True,timeout=45)
        self.assertEqual(completed.returncode,0,completed.stdout+'\n'+completed.stderr)


if __name__=='__main__':unittest.main()
