"""Identity, compatibility and real export checks for the Vocabulary EN gallery."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.cockpit_quality_gate import node_binary

ROOT=Path(__file__).resolve().parents[2]
VOCAB=ROOT/'VocabularyEN'
SPEC=importlib.util.spec_from_file_location('vocabulary_gallery_sync',VOCAB/'sync_vocabulary_en_to_docs.py')
sync=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)

class VocabularyGalleryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=sync.load_rows(VOCAB/'VocabularyEN.csv')
        cls.catalog=sync.load_catalog(VOCAB/'VocabularyEN.csv')
        cls.manifest=json.loads((ROOT/'docs/data/vocabulary-en.json').read_text())

    def test_approved_retirements_preserve_records_and_active_teaching_types(self):
        inactive={item['uid'] for item in self.manifest['items'] if not item['active']}
        self.assertEqual(inactive,{'ven-0195','ven-0197','ven-0199','ven-0200','ven-0203',
                                   'ven-0257','ven-0258','ven-0259','ven-0260','ven-0271'})
        self.assertEqual(len(self.manifest['items']),541)
        active=[item for item in self.manifest['items'] if item['active']]
        self.assertEqual(len(active),531)
        self.assertEqual(sum(i['teachingType']=='interaction' for i in active),20)
        self.assertEqual(sum(i['teachingType']=='word' for i in active),511)
        self.assertFalse(any(i['teachingType']=='idiom' for i in active))
        for entry in self.catalog['entries']:
            if entry.get('retirementReason')=='regular_plural_duplicate':
                target=next(e for e in self.catalog['entries'] if e['uid']==entry['singularUid'])
                self.assertTrue(target['active']);self.assertNotEqual(entry['uid'],target['uid'])
        # Singular-only irregular lemmas and unpaired plurals must not disappear.
        for en in ['goose','mouse','eyes','parents','potatoes','pants','boots','nuts']:
            self.assertTrue(next(i for i in active if i['en']==en)['active'])

    def test_word_and_sentence_corrections_keep_I_identity_and_picture(self):
        item=next(i for i in self.manifest['items'] if i['uid']=='ven-0062')
        self.assertEqual((item['id'],item['en'],item['cz'],item['partOfSpeech']),(62,'I','já',['pronoun']))
        self.assertEqual(item['image'],'assets/vocabulary-en/iam.png')
        old=sync.resolve_catalog_rows([{'EN':'I (am)','CZ':'já (jsem)'}],self.catalog)
        self.assertEqual(old[0]['uid'],item['uid'])
        self.assertEqual(item['sentenceEn'],'I am ready now—let’s start.')
        sure=next(i for i in self.manifest['items'] if i['uid']=='ven-0148')
        self.assertEqual(sure['sentenceEn'],'Sure, I can help you.')
        please=next(i for i in self.manifest['items'] if i['uid']=='ven-0139')
        self.assertEqual(please['sentenceEn'],'Please speak slowly; I want to understand.')

    def test_meaning_variants_keep_legacy_aliases_and_have_real_pinned_illustrations(self):
        by_uid={i['uid']:i for i in self.manifest['items']}
        for number in range(1,426):
            uid=f'ven-{number:04d}'
            self.assertEqual(by_uid[uid]['id'],number)
        old=sync.resolve_catalog_rows([{'EN':'second','CZ':'sekunda; druhý'},
                                      {'EN':'help','CZ':'pomoc'},
                                      {'EN':'free','CZ':'volný; zdarma'}],self.catalog)
        self.assertEqual([e['uid'] for e in old],['ven-0385','ven-0058','ven-0044'])
        for uid,cz,pos in [('ven-0385','sekunda','noun'),('ven-0440','druhý','number'),
                          ('ven-0058','pomoc','noun'),('ven-0430','pomoci; pomáhat','verb'),
                          ('ven-0428','zdarma','adjective'),('ven-0435','opatrně','adverb')]:
            self.assertEqual((by_uid[uid]['cz'],by_uid[uid]['partOfSpeech']),(cz,[pos]))
        for entry in self.catalog['entries']:
            if entry.get('imageStemOverride','').startswith('sense'):
                item=by_uid[entry['uid']]
                self.assertEqual(item['imageSource'],'catalog')
                self.assertEqual(item['imageStem'],entry['imageStemOverride'])
                self.assertNotIn('others',item['image'])
        for uid,stem in [('ven-0275','warning'),('ven-0030','drink'),('ven-0119','chicken'),
                         ('ven-0144','right'),('ven-0398','that')]:
            self.assertEqual((by_uid[uid]['imageStem'],by_uid[uid]['imageSource']),(stem,'catalog'))
        self.assertFalse(any(i['editorialStatus']=='needs-review' for i in by_uid.values() if i['active']))

    def test_benji_apply_never_tags_later_meanings_with_the_same_english_spelling(self):
        from tests import test_vocabularyen_mmtx_import as legacy
        module=legacy.load_benji_module()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'VocabularyEN.csv'
            raw=(VOCAB/'VocabularyEN.csv').read_bytes()
            rows=list(__import__('csv').DictReader(__import__('io').StringIO(raw.decode())))
            target=next(row for row in rows if row['Order']=='385');target['WS']=''
            with path.open('w',newline='') as handle:
                writer=__import__('csv').DictWriter(handle,fieldnames=list(rows[0]),lineterminator='\r\n')
                writer.writeheader();writer.writerows(rows)
            self.assertEqual(module.apply(path),['second'])
            updated=module.load_rows(path)
            self.assertIn('Benji',next(row for row in updated if row['Order']=='385')['WS'])
            self.assertEqual([row['WS'] for row in updated if int(row['Order'])>425],['']*116)
            self.assertEqual(module.apply(path),[])

    def test_body_batch_adds_ten_complete_nouns_and_keeps_original_body_cards(self):
        by_uid={i['uid']:i for i in self.manifest['items']}
        body=[by_uid[f'ven-{number:04d}'] for number in range(443,453)]
        self.assertEqual([i['en'] for i in body],['head','face','ear','nose','mouth','neck','arm','hand','leg','foot'])
        self.assertEqual([i['cz'] for i in body],['hlava','obličej','ucho','nos','ústa','krk','paže','ruka','noha','chodidlo'])
        for item in body:
            self.assertEqual((item['primaryGroup'],item['partOfSpeech'],item['teachingType'],item['imageSource']),('topic-02',['noun'],'word','catalog'))
            self.assertTrue(item['active']);self.assertFalse(item['selected']);self.assertFalse(item['hardTraining'])
            self.assertEqual(item['sourceIds'],[]);self.assertTrue(item['sentenceEn']);self.assertTrue(item['sentenceCz'])
        self.assertEqual((by_uid['ven-0036']['en'],by_uid['ven-0054']['en']),('eyes','hair'))
        self.assertEqual(sum(i['en']=='eyes' for i in self.manifest['items']),1)

    def test_invalid_activity_type_image_override_and_plural_reference_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            csv=Path(directory)/'VocabularyEN.csv';csv.write_text('EN,CZ\n')
            path=csv.with_name('vocabulary_en_catalog.json')
            for field,value in [('active',1),('teachingType','unknown'),('imageStemOverride','../other'),
                                ('imageStemOverride',123),('singularUid','ven-missing')]:
                catalog=copy.deepcopy(self.catalog);catalog['entries'][0][field]=value
                path.write_text(json.dumps(catalog))
                with self.subTest(field=field,value=value),self.assertRaises(ValueError):sync.load_catalog(csv)

    def test_reexport_carries_teaching_metadata_and_pins_the_renamed_picture(self):
        dirs=sync.build_picture_base_dirs(ROOT,VOCAB/'VocabularyEN.csv')
        mapping=sync.load_external_mapping(dirs,VOCAB/'VocabularyEN.csv')
        payload,_=sync.build_export_payload(self.rows,dirs,mapping,sync.discover_picture_stems(dirs),
            ROOT/'docs','vocabulary-en','VocabularyEN/VocabularyEN.csv',self.catalog)
        expected={i['uid']:(i['active'],i['teachingType'],i['image']) for i in self.manifest['items']}
        actual={i['uid']:(i['active'],i['teachingType'],i['image']) for i in payload['items']}
        self.assertEqual(actual,expected)

    def test_catalog_covers_all_meanings_once_and_does_not_merge_orange(self):
        entries=sync.resolve_catalog_rows(self.rows,self.catalog)
        self.assertEqual(len(entries),541)
        self.assertEqual(len({e['uid'] for e in entries}),541)
        self.assertEqual(len(self.catalog['groups']),18)
        orange=[entry for row,entry in zip(self.rows,entries) if row['EN']=='orange']
        self.assertEqual([e['uid'] for e in orange],['ven-0118','ven-0170'])
        self.assertNotEqual(orange[0]['primaryGroup'],orange[1]['primaryGroup'])

    def test_reordering_and_inserting_rows_do_not_change_existing_ids_or_audio_identity(self):
        original=sync.resolve_catalog_rows(self.rows,self.catalog)
        reversed_rows=list(reversed(self.rows))
        resolved=sync.resolve_catalog_rows(reversed_rows,self.catalog)
        self.assertEqual([e['uid'] for e in resolved],list(reversed([e['uid'] for e in original])))
        catalog=copy.deepcopy(self.catalog)
        entry=copy.deepcopy(catalog['entries'][0]);entry.update(id=max(e['id'] for e in catalog['entries'])+1,uid='ven-new-card',matches=[{'en':'test addition','cz':'zkouška'}])
        catalog['entries'].append(entry)
        rows=[{'EN':'test addition','CZ':'zkouška'},*self.rows]
        after=sync.resolve_catalog_rows(rows,catalog)
        self.assertEqual([e['id'] for e in after[1:]],[e['id'] for e in original])

    def test_unknown_or_duplicated_meaning_requires_an_explicit_catalog_edit(self):
        with self.assertRaisesRegex(ValueError,'katalog'):
            sync.resolve_catalog_rows([{'EN':'new text','CZ':'nový význam'}],self.catalog)
        with self.assertRaisesRegex(ValueError,'katalog'):
            sync.resolve_catalog_rows([self.rows[0],self.rows[0]],self.catalog)
        catalog=copy.deepcopy(self.catalog)
        catalog['entries'][0]['matches'].append({'en':'edited wording','cz':'upravený význam'})
        self.assertEqual(sync.resolve_catalog_rows([{'EN':'edited wording','CZ':'upravený význam'}],catalog)[0]['uid'],'ven-0001')

    def test_invalid_catalog_cannot_silently_rebind_an_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            csv=Path(directory)/'VocabularyEN.csv';csv.write_text('EN,CZ\n')
            path=csv.with_name('vocabulary_en_catalog.json')
            for field,value in [('id',self.catalog['entries'][1]['id']),('uid',self.catalog['entries'][1]['uid']),('primaryGroup','missing')]:
                catalog=copy.deepcopy(self.catalog);catalog['entries'][0][field]=value
                path.write_text(json.dumps(catalog))
                with self.subTest(field=field),self.assertRaises(ValueError):sync.load_catalog(csv)

    def test_export_and_audio_builder_agree_after_csv_reordering(self):
        sys.path.insert(0,str(VOCAB))
        try:
            import build_vocabulary_en_audio as audio
            with tempfile.TemporaryDirectory() as directory:
                csv=Path(directory)/'VocabularyEN.csv'
                import csv as csv_module
                with csv.open('w',newline='') as handle:
                    writer=csv_module.DictWriter(handle,fieldnames=list(self.rows[0]))
                    writer.writeheader();writer.writerows(reversed(self.rows))
                csv.with_name('vocabulary_en_catalog.json').write_text(json.dumps(self.catalog))
                resolved=sync.resolve_catalog_rows(sync.load_rows(csv),sync.load_catalog(csv))
                audio_rows=audio.load_csv_rows(csv)
                self.assertEqual([e['id'] for e in resolved],[r['id'] for r in audio_rows])
                self.assertEqual(audio_rows[-20]['en'],'cat')
                self.assertEqual(audio_rows[-20]['id'],20)
        finally:sys.path.remove(str(VOCAB))

    def test_all_current_image_and_audio_links_keep_their_meanings(self):
        audio=json.loads((ROOT/'docs/data/vocabulary-en-audio.json').read_text())
        for item in self.manifest['items']:
            with self.subTest(uid=item['uid']):
                self.assertTrue((ROOT/'docs'/item['image']).is_file())
                self.assertTrue((ROOT/'docs'/item['thumbnail']).is_file())
                record=audio['items'][str(item['id'])]
                self.assertEqual((record['sourceEn'],record['sourceCz']),(item['en'],item['cz']))
        yard=next(i for i in self.manifest['items'] if i['uid']=='ven-0300')
        self.assertEqual(yard['image'],'assets/vocabulary-en/courtyard.webp')
        see=next(i for i in self.manifest['items'] if i['uid']=='ven-0533')
        self.assertEqual(see['image'],'assets/vocabulary-en/see-verb.webp')
        self.assertEqual(self.manifest['stats']['uniqueImageFiles'],491)

    def test_every_sentence_and_translation_stays_with_its_source_meaning(self):
        source={(row['EN'],row['CZ']):row for row in self.rows}
        self.assertEqual(len(self.manifest['items']),541)
        for item in self.manifest['items']:
            with self.subTest(uid=item['uid']):
                row=source[(item['en'],item['cz'])]
                self.assertTrue(item['sentenceEn'])
                self.assertTrue(item['sentenceCz'])
                self.assertEqual(item['sentenceEn'],row['Sentence'])
                self.assertEqual(item['sentenceCz'],row['SentenceT'])

    def test_thumbnails_preserve_originals_and_repeat_export_without_changing_content(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);original=root/'source.png'
            Image.new('RGB',(800,400),'red').save(original)
            original_hash=hashlib.sha256(original.read_bytes()).hexdigest()
            payload={'catalog':{},'items':[{'image':'assets/vocabulary-en/red.png'}]}
            for attempt in range(2):
                candidate=copy.deepcopy(payload)
                sync.write_output(root,candidate,{original:'red.png'},'test.json','vocabulary-en',preserve_extra_assets=True)
                target=root/candidate['items'][0]['thumbnail']
                with Image.open(target) as thumb:self.assertEqual(thumb.size,(384,192))
                content=target.read_bytes()
                if attempt:self.assertEqual(content,first)
                first=content
            self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),original_hash)

    def test_controller_and_selection_regressions_execute_with_node(self):
        result=subprocess.run([node_binary(),'--test',str(Path(__file__).with_name('test_vocabularyen_selection.js')),str(Path(__file__).with_name('test_vocabularyen_learners.js'))],cwd=Path(__file__).parents[1],capture_output=True,text=True,timeout=120)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)

    def test_picture_quiz_catalog_pins_only_existing_active_meanings_and_exported_images(self):
        catalog=json.loads((ROOT/'docs/data/vocabulary-en-quiz.json').read_text())
        self.assertEqual(catalog['schemaVersion'],1)
        self.assertGreaterEqual(len(catalog['entries']),4)
        by_uid={item['uid']:item for item in self.manifest['items']}
        for uid,entry in catalog['entries'].items():
            item=by_uid[uid]
            self.assertTrue(item['active'],uid)
            self.assertEqual(item['teachingType'],'word',uid)
            self.assertEqual((entry['en'],entry['cz'],entry['image']),
                             (item['en'],item['cz'],item['image']),uid)
            self.assertIsInstance(entry['conflicts'],list)
            self.assertIn(entry['format'],('objects','colors','numbers'))
            self.assertTrue((ROOT/'docs'/entry['image']).is_file(),uid)

    def test_legacy_export_and_image_rules_still_hold(self):
        import inspect
        from tests import test_vocabularyen_mmtx_import as legacy
        # These checks cover the export/image/Benji contracts used by the gallery.
        # The five separate historical whole-MMTX/receipt snapshot audits remain
        # in their original module; they predate newer story and mapping changes.
        names = {
            'test_czech_tokenization_keeps_letters_with_diacritics_together',
            'test_benji_tag_transform_changes_only_selected_crlf_rows',
            'test_current_mmtx_rows_are_all_in_benji_word_set',
            'test_web_export_offers_exactly_the_mmtx_rows_in_benji_word_set',
            'test_exact_mapping_beats_accent_stripped_czech_filename_collision',
            'test_exact_english_filename_stays_authoritative',
            'test_czech_meaning_beats_short_english_function_word',
            'test_web_asset_sync_can_preserve_unreferenced_files',
            'test_mapping_byte_append_preserves_existing_values',
            'test_picture_plan_covers_every_imported_row_without_overwrite',
        }
        for name in sorted(names):
            function = getattr(legacy, name)
            with self.subTest(legacy_check=name):
                parameters=inspect.signature(function).parameters
                if parameters:
                    self.assertEqual(set(parameters),{'tmp_path'})
                    with tempfile.TemporaryDirectory() as directory:
                        function(tmp_path=Path(directory))
                else:
                    function()

    def test_en83_keeps_its_existing_shared_trainer(self):
        html=(ROOT/'docs/vocabulary-en83/index.html').read_text()
        self.assertIn('../vocabulary-en/app.js',html)
        self.assertIn('../vocabulary-en/styles.css',html)
        legacy=(ROOT/'docs/vocabulary-en/app.js').read_text()
        self.assertNotIn('VocabularyModel',legacy)
        gallery=(ROOT/'docs/vocabulary-en/index.html').read_text()
        self.assertIn('src="gallery.js"',gallery)

class SentencePictureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('sentence_picture_builder',VOCAB/'build_sentence_pictures.py')
        cls.builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.builder)
        cls.source=json.loads((VOCAB/'vocabulary_en_sentence_pictures.json').read_text())
        cls.data=json.loads((ROOT/'docs/data/vocabulary-en.json').read_text())
        cls.export=json.loads((ROOT/'docs/data/vocabulary-en-sentence-pictures.json').read_text())

    def test_all_active_sentences_export_one_to_five_real_image_links(self):
        from PIL import Image
        expected=self.builder.build(self.source,self.data,asset_root=ROOT/'docs')
        self.assertEqual(expected,self.export)
        active={i['uid'] for i in self.data['items'] if i.get('active',True)}
        self.assertEqual(set(expected['entries']),active)
        self.assertEqual(len(active),531)
        self.assertTrue(all(1<=len(r['concepts'])<=5 for r in expected['entries'].values()))
        self.assertEqual(max(len(r['concepts']) for r in expected['entries'].values()),5)
        items={i['uid']:i for i in self.data['items']};seen=set()
        for record in expected['entries'].values():
            for ref in record['concepts']:
                item=items[ref['uid']];self.assertTrue(item['active'])
                for key in ('image','thumbnail'):
                    path=ROOT/'docs'/item[key]
                    if path in seen:continue
                    with Image.open(path) as image:image.load()
                    seen.add(path)

    def test_authoring_rejects_a_missing_active_sentence(self):
        source=copy.deepcopy(self.source);source['entries'].pop('ven-0020')
        with self.assertRaises(ValueError):self.builder.build(source,self.data)

    def test_unedited_pilot_records_are_unchanged(self):
        import hashlib
        pilot=['ven-0020','ven-0027','ven-0211','ven-0384','ven-0117','ven-0074','ven-0111',
               'ven-0233','ven-0224','ven-0008','ven-0222','ven-0226','ven-0207','ven-0208',
               'ven-0217','ven-0234','ven-0450','ven-0477','ven-0262','ven-0430']
        approved_changes={'ven-0222','ven-0208','ven-0450','ven-0430','ven-0224'}
        records={uid:self.source['entries'][uid] for uid in pilot if uid not in approved_changes}
        raw=json.dumps(records,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'231d09042e2bdf9837b9adac3c3b7d27ba8f1ab87d55563cdfaec1ae0d4aaf8a')

    def test_full_review_keeps_homographs_grammatical_roles_and_fixed_expressions(self):
        cases={
            1:({30},{426}),35:({17},{44,428,429}),116:({30,118},{170,426}),
            170:({170},{118}),192:({118},{170}),243:({519},{204}),
            277:({431},{119}),300:({431},{119}),433:({433},{144,432}),
            447:({376},{439}),413:({436},{332}),434:({434,430},{159,58}),
            504:({159},{434}),510:({510,445},{263,67}),514:({514},{487,5}),
            86:(set(),{299}),98:(set(),{97}),269:(set(),{86}),
            405:(set(),{279}),406:(set(),{400}),153:({136},{160}),
        }
        for number,(required,forbidden) in cases.items():
            uid=f'ven-{number:04}';actual={int(r['uid'][4:]) for r in self.source['entries'][uid]['concepts']}
            with self.subTest(uid=uid):
                self.assertTrue(required<=actual);self.assertTrue(forbidden.isdisjoint(actual))
        record=self.export['entries']['ven-0325'];ref=next(r for r in record['concepts'] if r['uid']=='ven-0325')
        self.assertEqual(ref['occurrence'],2)
        self.assertEqual(ref['start'],record['sourceSentenceEn'].rindex('do'))

    def test_sentence_texts_and_concept_meanings_cannot_drift_silently(self):
        for field in ('sourceEn','sourceCz','sourceSentenceEn','sourceSentenceCz'):
            source=copy.deepcopy(self.source);source['entries']['ven-0020'][field]+=' changed'
            with self.subTest(field=field),self.assertRaises(ValueError):self.builder.build(source,self.data)
        for field in ('sourceEn','sourceCz'):
            source=copy.deepcopy(self.source);source['entries']['ven-0020']['concepts'][1][field]+=' changed'
            with self.subTest(field=field),self.assertRaises(ValueError):self.builder.build(source,self.data)

    def test_bad_references_order_duplicates_and_overlong_rows_are_rejected(self):
        for mode in ('unknown','duplicate','too-many','order','missing-word','inside-word','occurrence','review','shape','retired'):
            source=copy.deepcopy(self.source);data=copy.deepcopy(self.data);r=source['entries']['ven-0020'];refs=r['concepts']
            if mode=='unknown':refs[0]['uid']='ven-9999'
            if mode=='duplicate':refs.insert(1,copy.deepcopy(refs[0]))
            if mode=='too-many':r['concepts']=refs*2
            if mode=='order':refs.reverse()
            if mode=='missing-word':refs[0]['text']='kitten'
            if mode=='inside-word':refs[1]['text']='sleep'
            if mode=='occurrence':refs[0]['occurrence']=True
            if mode=='review':r['reviewed']=False
            if mode=='shape':r['concepts']=None
            if mode=='retired':next(i for i in data['items'] if i['uid']=='ven-0477')['active']=False
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.builder.build(source,data)

    def test_inflections_keep_the_exact_meaning_instead_of_spelling_homographs(self):
        records=self.export['entries']
        self.assertEqual([(r['uid'],r['text']) for r in records['ven-0020']['concepts']],
                         [('ven-0020','cat'),('ven-0477','sleeps'),('ven-0222','chair')])
        self.assertIn(('ven-0477','sleeping'),[(r['uid'],r['text']) for r in records['ven-0226']['concepts']])
        self.assertIn(('ven-0376','opens'),[(r['uid'],r['text']) for r in records['ven-0234']['concepts']])
        self.assertNotIn('ven-0439',[r['uid'] for r in records['ven-0234']['concepts']])
        self.assertEqual([r['uid'] for r in records['ven-0430']['concepts']],['ven-0430','ven-0287','ven-0344','ven-0012'])
        self.assertNotIn('ven-0058',[r['uid'] for r in records['ven-0430']['concepts']])
        self.assertNotIn('ven-0097',[r['uid'] for r in records['ven-0027']['concepts']])
        self.assertNotIn('ven-0081',[r['uid'] for r in records['ven-0207']['concepts']])

    def test_offsets_use_javascript_utf16_and_do_not_depend_on_catalog_order(self):
        source=copy.deepcopy(self.source);r=source['entries']['ven-0020']
        data=copy.deepcopy(self.data);target=next(i for i in data['items'] if i['uid']=='ven-0020')
        target['sentenceEn']='🐈 '+target['sentenceEn'];r['sourceSentenceEn']=target['sentenceEn']
        result=self.builder.build(source,data);ref=result['entries']['ven-0020']['concepts'][0]
        expected=len(target['sentenceEn'][:target['sentenceEn'].index('cat')].encode('utf-16-le'))//2
        self.assertEqual(ref['start'],expected)
        data['items'].reverse();self.assertEqual(self.builder.build(source,data),result)

    def test_asset_traversal_missing_thumbnail_and_duplicate_image_are_rejected(self):
        for mode in ('traversal','missing','duplicate-image'):
            data=copy.deepcopy(self.data);items={i['uid']:i for i in data['items']}
            if mode=='traversal':items['ven-0477']['thumbnail']='../private.png'
            if mode=='missing':items['ven-0477']['thumbnail']='assets/vocabulary-en-thumbs/missing.webp'
            if mode=='duplicate-image':items['ven-0477']['image']=items['ven-0020']['image']
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.builder.build(self.source,data,asset_root=ROOT/'docs')


if __name__=='__main__':unittest.main()
