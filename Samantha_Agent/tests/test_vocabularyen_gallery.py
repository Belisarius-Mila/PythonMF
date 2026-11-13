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

    def test_catalog_covers_all_meanings_once_and_does_not_merge_orange(self):
        entries=sync.resolve_catalog_rows(self.rows,self.catalog)
        self.assertEqual(len(entries),425)
        self.assertEqual(len({e['uid'] for e in entries}),425)
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
        entry=copy.deepcopy(catalog['entries'][0]);entry.update(id=426,uid='ven-new-card',matches=[{'en':'test addition','cz':'zkouška'}])
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
        self.assertEqual(self.manifest['stats']['uniqueImageFiles'],384)

    def test_every_sentence_and_translation_stays_with_its_source_meaning(self):
        source={(row['EN'],row['CZ']):row for row in self.rows}
        self.assertEqual(len(self.manifest['items']),425)
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
        result=subprocess.run([node_binary(),'--test',str(Path(__file__).with_name('test_vocabularyen_selection.js'))],cwd=Path(__file__).parents[1],capture_output=True,text=True,timeout=90)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)

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

if __name__=='__main__':unittest.main()
