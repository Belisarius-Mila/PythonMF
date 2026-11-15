from __future__ import annotations
import copy,csv,json,os,subprocess,sys,tempfile,unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from app import vocabulary_authoring as author
from app.vocabulary_authoring import VocabularyAuthoring,AuthoringError,parse_input


class AuthoringTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.repo=(Path(self.temp.name)/'repo').resolve();self.repo.mkdir();self.calls=[]
        sync,word,sentence,_=author._tools()
        real=author.PROJECT.parent
        catalog=json.loads((real/author.CATALOG).read_text())
        wanted={20,58,257,385};catalog['entries']=[e for e in catalog['entries'] if e['id'] in wanted]
        with (real/author.CSV).open(newline='') as handle: source=list(csv.DictReader(handle))
        rows=[row for row in source if int(row['Order']) in wanted]
        path=self.repo/author.CSV;path.parent.mkdir()
        with path.open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(rows[0]),lineterminator='\r\n');writer.writeheader();writer.writerows(rows)
        (self.repo/author.CATALOG).write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
        pict=self.repo/'Pict';pict.mkdir()
        for entry,row in zip(catalog['entries'],rows):
            # Resolve each image explicitly in this small isolated source fixture.
            stem=entry.get('imageStemOverride') or sync.normalize_word(row['EN'])
            Image.new('RGB',(96,96),'green').save(pict/(stem+'.png'))
        bases=sync.build_picture_base_dirs(self.repo,path)
        payload,assets=sync.build_export_payload(sync.load_rows(path),bases,{},sync.discover_picture_stems(bases),self.repo/'docs','vocabulary-en',author.CSV,catalog)
        sync.write_output(self.repo/'docs',payload,assets,'vocabulary-en.json','vocabulary-en',True)
        wm=word.build_manifest(payload['items']);sm=sentence.build_manifest(payload['items'])
        for relative in {*word._asset_jobs(wm),*sentence.jobs(sm)}:
            file=self.repo/'docs'/relative;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(b'ID3'+b'x'*1600)
        author._save(self.repo/author.DATA[1],wm);author._save(self.repo/author.DATA[2],sm)
        subprocess.run(['git','init','-q',str(self.repo)],check=True)
        subprocess.run(['git','-C',str(self.repo),'add','VocabularyEN','docs','Pict'],check=True)
        subprocess.run(['git','-C',str(self.repo),'-c','user.name=Synthetic','-c','user.email=synthetic@example.test','commit','-qm','fixture'],check=True)
        self.image=Path(self.temp.name)/'image.png';Image.new('RGB',(100,80),'blue').save(self.image)
        self.worker=VocabularyAuthoring(self.repo,store_root=self.repo/'jobs',synthesize=self.synth)

    def synth(self,text,*,voice,rate):
        self.calls.append((text,voice,rate));return b'ID3'+(text.encode()*1600)[:1600]

    def item(self,en='head',cz='hlava'):
        return {'en':en,'cz':cz,'sentenceEn':'This is my '+en+'.','sentenceCz':'Tohle je '+cz+'.',
                'partOfSpeech':['noun'],'primaryGroup':'topic-02'}

    def prepare(self,items=None,request='test-authoring-0001',worker=None):
        worker=worker or self.worker;items=items or self.item();preview=worker.preview(items)
        images={p['key']:str(self.image) for p in preview['items'] if p['status']=='new'}
        return worker.prepare(request,items,images=images,expected_preview=preview['digest'],confirmed=True)

    def apply(self,receipt,worker=None):
        return (worker or self.worker).apply(receipt['request_id'],expected_digest=receipt['digest'],confirmed=True)

    def test_csv_single_and_list_share_schema_and_preserve_quoted_punctuation(self):
        a=parse_input('EN;CZ;Sentence;SentenceT\nhead;hlava;"A, B; C.";"Věta; druhá."')
        self.assertEqual(a[0]['sentenceEn'],'A, B; C.')
        self.assertEqual(a[0]['sentenceCz'],'Věta; druhá.')
        self.assertEqual(parse_input(self.item()),parse_input([self.item()]))
        for bad in [{'en':'x','cz':'y','id':20},'EN,CZ;Sentence\nhead,hlava;Hi']:
            with self.assertRaises(AuthoringError):parse_input(bad)

    def test_preview_is_read_only_recognizes_alias_retired_and_distinct_meaning(self):
        before=self.worker._snapshot()
        p=self.worker.preview([{'en':'second','cz':'sekunda; druhý'}, {'en':'I have','cz':'mám'},self.item('second','druhý')])
        self.assertEqual([x['status'] for x in p['items']],['existing','retired','new'])
        self.assertEqual(p['items'][0]['existingUid'],'ven-0385')
        self.assertEqual(p['items'][2]['otherMeanings'],['ven-0385'])
        self.assertFalse(self.worker.store.exists());self.assertEqual(before,self.worker._snapshot());self.assertFalse(self.calls)

    def test_incomplete_duplicate_and_conflicting_pos_are_explicit(self):
        p=self.worker.preview([{'en':'new','cz':'nové'},self.item(),self.item(),self.item('second','sekunda')|{'partOfSpeech':['verb']}])
        self.assertEqual([x['status'] for x in p['items']],['incomplete','new','duplicate-in-batch','needs-review'])
        self.assertFalse(p['ready'])

    def test_single_prepare_and_apply_preserve_source_until_complete_and_replay(self):
        before=(self.repo/author.CSV).read_bytes();snapshot=self.worker._snapshot()
        receipt=self.prepare();self.assertEqual(receipt['state'],'prepared');self.assertEqual(receipt['generatedAudio'],4)
        self.assertEqual(snapshot,self.worker._snapshot())
        self.assertEqual(self.apply(receipt)['state'],'applied')
        self.assertTrue((self.repo/author.CSV).read_bytes().startswith(before))
        current=json.loads((self.repo/author.DATA[0]).read_text())['items'];self.assertEqual(len(current),5)
        added=current[-1];self.assertEqual(added['en'],'head');self.assertFalse(added['selected']);self.assertEqual(added['sourceIds'],[])
        self.assertEqual(added['imageSource'],'catalog');self.assertEqual(added['partOfSpeech'],['noun'])
        changed=(self.repo/author.CSV).read_bytes()+b'foreign edit'
        (self.repo/author.CSV).write_bytes(changed);self.apply(receipt)
        self.assertEqual((self.repo/author.CSV).read_bytes(),changed);self.assertEqual(len(self.calls),4)

    def test_existing_only_is_a_true_noop_and_no_generation(self):
        before=self.worker._snapshot();receipt=self.prepare({'en':'cat','cz':'kočka'})
        self.assertEqual((receipt['newCount'],receipt['changedFiles']),(0,0))
        self.apply(receipt);self.assertEqual(self.worker._snapshot(),before);self.assertFalse(self.calls)

    def test_same_english_has_separate_uid_and_czech_audio_with_reused_english(self):
        receipt=self.prepare(self.item('second','druhý'));self.assertEqual(receipt['generatedAudio'],3)
        self.apply(receipt);items=json.loads((self.repo/author.DATA[0]).read_text())['items']
        meanings=[i for i in items if i['en']=='second'];self.assertEqual([i['cz'] for i in meanings],['sekunda','druhý'])
        self.assertNotEqual(meanings[0]['uid'],meanings[1]['uid'])
        self.assertEqual(meanings[0]['wordSets'],['Benji']);self.assertEqual(meanings[1]['wordSets'],[])

    def test_stale_preview_and_changed_source_fail_without_generation_or_overwrite(self):
        item=self.item();p=self.worker.preview(item)
        (self.repo/author.CSV).write_bytes((self.repo/author.CSV).read_bytes()+b'\r\n')
        with self.assertRaises(AuthoringError):self.worker.prepare('test-stale-preview',item,images={p['items'][0]['key']:str(self.image)},expected_preview=p['digest'],confirmed=True)
        self.assertFalse(self.calls)

    def test_uncertain_external_request_is_not_repeated(self):
        def fail(*args,**kwargs):self.calls.append('uncertain');raise RuntimeError('disconnected')
        worker=VocabularyAuthoring(self.repo,store_root=self.worker.store,synthesize=fail)
        with self.assertRaises(RuntimeError):self.prepare(worker=worker)
        with self.assertRaisesRegex(AuthoringError,'Nejistý'):self.prepare(worker=worker)
        self.assertEqual(self.calls,['uncertain'])

    def test_tampered_prepared_asset_blocks_all_source_writes(self):
        receipt=self.prepare();before=self.worker._snapshot()
        job=json.loads(self.worker._job_path(receipt['request_id']).read_text())
        asset=next(p for p in job['changes'] if p.endswith('.mp3'))
        (self.worker._job_path(receipt['request_id']).parent/'stage'/asset).write_bytes(b'bad')
        with self.assertRaises(AuthoringError):self.apply(receipt)
        self.assertEqual(before,self.worker._snapshot())

    def test_partial_apply_recovers_original_batch_without_more_synthesis(self):
        receipt=self.prepare();real=author._atomic;once=[]
        def fail_after_write(path,data,**kwargs):
            real(path,data,**kwargs)
            if path==self.repo/author.CSV and not once:once.append(True);raise OSError('simulated crash')
        with patch.object(author,'_atomic',fail_after_write):
            with self.assertRaises(OSError):self.apply(receipt)
        self.assertEqual(self.apply(receipt)['state'],'applied');self.assertEqual(len(self.calls),4)

    def test_real_process_exit_after_first_source_write_recovers(self):
        receipt=self.prepare()
        code=f'''import os\nfrom pathlib import Path\nfrom app import vocabulary_authoring as a\nr=Path({str(self.repo)!r});real=a._atomic\ndef crash(path,data,**kwargs):\n real(path,data,**kwargs)\n if path==r/a.CSV:os._exit(17)\na._atomic=crash\na.VocabularyAuthoring(r,store_root=r/'jobs').apply({receipt['request_id']!r},expected_digest={receipt['digest']!r},confirmed=True)\n'''
        result=subprocess.run([sys.executable,'-c',code],env={**os.environ,'PYTHONPATH':str(author.PROJECT)},capture_output=True)
        self.assertEqual(result.returncode,17,result.stderr.decode());self.assertEqual(self.apply(receipt)['state'],'applied')
        self.assertEqual(len(self.calls),4)

    def test_foreign_edit_and_deleted_original_file_are_never_overwritten(self):
        receipt=self.prepare();path=self.repo/author.CSV;original=path.read_bytes();foreign=original+b'\r\n';path.write_bytes(foreign)
        with self.assertRaises(AuthoringError):self.apply(receipt)
        self.assertEqual(path.read_bytes(),foreign)
        # A missing original is not equivalent to an unspecified after-value.
        source=json.loads(self.worker._job_path(receipt['request_id']).read_text())['source']
        path.write_bytes(original);path.rename(self.repo/'preserved-source.csv')
        with self.assertRaises(AuthoringError):self.worker._check_source(source)

    def test_parallel_preparations_reserve_distinct_ids_and_stale_second_apply_stops(self):
        worker2=VocabularyAuthoring(self.repo,store_root=self.worker.store,synthesize=self.synth)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(self.prepare,self.item(), 'test-parallel-head',self.worker),
                     pool.submit(self.prepare,self.item('face','obličej'),'test-parallel-face',worker2)]
            receipts=[f.result() for f in futures]
        self.assertEqual(len({r['items'][0]['uid'] for r in receipts}),2)
        self.apply(receipts[0])
        with self.assertRaises(AuthoringError):self.apply(receipts[1],worker2)

    def test_mid_apply_stage_change_stops_before_copying_changed_bytes(self):
        receipt=self.prepare();path=self.worker._job_path(receipt['request_id'])
        stage=path.parent/'stage'/author.CATALOG;original=stage.read_bytes();before=(self.repo/author.CATALOG).read_bytes()
        real=author._atomic
        def change_later_file(target,data,**kwargs):
            real(target,data,**kwargs)
            if target==self.repo/author.CSV:stage.write_bytes(b'{}')
        with patch.object(author,'_atomic',change_later_file):
            with self.assertRaises(AuthoringError):self.apply(receipt)
        self.assertEqual((self.repo/author.CATALOG).read_bytes(),before)
        stage.write_bytes(original);self.assertEqual(self.apply(receipt)['state'],'applied')
        self.assertEqual(len(self.calls),4)

    def test_changed_request_identity_and_missing_consent_are_rejected(self):
        receipt=self.prepare()
        with self.assertRaises(AuthoringError):self.prepare(self.item('face','obličej'))
        with self.assertRaises(AuthoringError):self.worker.apply(receipt['request_id'],expected_digest=receipt['digest'],confirmed=False)
        with self.assertRaises(AuthoringError):self.worker.apply('../escape',expected_digest=receipt['digest'],confirmed=True)

if __name__=='__main__':unittest.main()
