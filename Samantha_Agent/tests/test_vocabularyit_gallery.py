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

    def test_all_1096_cards_have_accepted_complete_italian_data(self):
        data=self.data
        self.assertEqual((data['schemaVersion'],data['language'],data['appName']),(2,'it','VocabularyIT'))
        self.assertEqual((data['itemCount'],data['sourceRowCount']),(1096,471))
        self.assertEqual(len({item['uid'] for item in data['items']}),1096)
        self.assertTrue(data['imageReviewComplete']);self.assertEqual(data['mode'],'release')
        self.assertEqual(data['stats']['pendingImageReview'],0)
        self.assertTrue(all(item['active'] and item['imageReviewed'] and item['sentenceIt'] and item['sentenceCz'] for item in data['items']))
        self.assertEqual(data['stats']['teachingTypes'],{'word':1062,'interaction':30,'idiom':4})
        for item in data['items']:
            self.assertNotIn('en',item);self.assertNotIn('L',item);self.assertNotIn('HT',item)

    def test_all_1314_visual_assets_decode_and_match_case_hash_and_dimensions(self):
        refs={}
        for item in self.data['items']:
            refs[item['image']]=900;refs[item['thumbnail']]=240
        self.assertEqual(len(refs),1314)
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
            self.assertEqual(len(manifest['items']),1096)
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
        self.assertEqual(len(expected['entries']),1096)
        self.assertEqual(sum(e['reviewed'] for e in expected['entries'].values()),1094)
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



class ItalianSentencePictureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec=importlib.util.spec_from_file_location('italian_sentence_builder',ROOT/'VocabularyIT/build_sentence_pictures.py')
        cls.builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.builder)
        cls.source=json.loads((ROOT/'VocabularyIT/vocabulary_it_sentence_pictures.json').read_text())
        cls.data=json.loads((DOCS/'data/vocabulary-it-v2.json').read_text())
        cls.export=json.loads((DOCS/'data/vocabulary-it-sentence-pictures.json').read_text())

    def test_complete_exact_reviewed_export_and_all_image_references(self):
        actual=self.builder.build(self.source,self.data,asset_root=DOCS)
        self.assertEqual(actual,self.export)
        self.assertEqual(len(actual['entries']),1096)
        self.assertEqual(sum(len(r['concepts']) for r in actual['entries'].values()),1963)
        self.assertEqual(max(len(r['concepts']) for r in actual['entries'].values()),5)
        self.assertTrue(all(r['reviewed'] and 1<=len(r['concepts'])<=5 for r in actual['entries'].values()))

    def test_changed_sentence_translation_meaning_missing_or_retired_uid_are_rejected(self):
        for mode in ['sentence','translation','word','meaning','unknown','retired','coverage','too-many','duplicate','order','substring','shape']:
            source=copy.deepcopy(self.source);data=copy.deepcopy(self.data);record=source['entries']['vit-0083']
            if mode=='sentence':record['sourceSentenceIt']+='x'
            if mode=='translation':record['sourceSentenceCz']+='x'
            if mode=='word':record['sourceIt']+='x'
            if mode=='meaning':record['concepts'][0]['sourceCz']+='x'
            if mode=='unknown':record['concepts'][0]['uid']='vit-9999'
            if mode=='retired':next(i for i in data['items'] if i['uid']=='vit-0083')['active']=False
            if mode=='coverage':source['entries'].pop('vit-0001')
            if mode=='too-many':record['concepts']*=2
            if mode=='duplicate':record['concepts'][1]=record['concepts'][0]
            if mode=='order':record['concepts'].reverse()
            if mode=='substring':record['concepts'][1]['text']='ner'
            if mode=='shape':record['concepts']=None
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.builder.build(source,data)

    def test_reviewed_homographs_idioms_inflections_and_elisions_have_correct_meanings(self):
        def ids(uid):return {r['uid'] for r in self.export['entries'][uid]['concepts']}
        self.assertIn('vit-0682',ids('vit-0443'));self.assertNotIn('vit-0583',ids('vit-0443'))
        self.assertIn('vit-0525',ids('vit-0065'));self.assertNotIn('vit-0130',ids('vit-0065'))
        self.assertIn('vit-0107',ids('vit-0106'));self.assertIn('vit-0106',ids('vit-0106'))
        self.assertIn('vit-1008',ids('vit-1089'));self.assertNotIn('vit-0580',ids('vit-1089'))
        self.assertIn('vit-0491',ids('vit-0491'));self.assertNotIn('vit-0353',ids('vit-0491'))
        self.assertIn('vit-1091',ids('vit-0166'));self.assertNotIn('vit-0166',ids('vit-0166'))
        self.assertIn('vit-1050',ids('vit-1050'));self.assertNotIn('vit-0322',ids('vit-1050'))
        self.assertIn('vit-0320',ids('vit-1074'));self.assertNotIn('vit-0319',ids('vit-1074'))
        ref=self.export['entries']['vit-0617']['concepts'][0];self.assertEqual(ref['text'],'acqua')

    def test_utf16_offsets_and_order_independence(self):
        source=copy.deepcopy(self.source);data=copy.deepcopy(self.data)
        item=next(i for i in data['items'] if i['uid']=='vit-0617')
        item['sentenceIt']='💧 '+item['sentenceIt'];source['entries'][item['uid']]['sourceSentenceIt']=item['sentenceIt']
        result=self.builder.build(source,data);ref=result['entries'][item['uid']]['concepts'][0]
        expected=len(item['sentenceIt'][:item['sentenceIt'].index('acqua')].encode('utf-16-le'))//2
        self.assertEqual(ref['start'],expected)
        data['items'].reverse();self.assertEqual(self.builder.build(source,data),result)

    def test_unsafe_missing_and_repeated_image_assets_are_rejected(self):
        for mode in ['unsafe','missing','same-image']:
            data=copy.deepcopy(self.data);items={i['uid']:i for i in data['items']}
            if mode=='unsafe':items['vit-0083']['thumbnail']='../private.webp'
            if mode=='missing':items['vit-0083']['thumbnail']='assets/vocabulary-it-v2/thumbs/missing.webp'
            if mode=='same-image':items['vit-0512']['image']=items['vit-0083']['image']
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.builder.build(self.source,data,asset_root=DOCS)

if __name__=='__main__':unittest.main()
