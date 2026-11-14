import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import article_archive as archive, book_inventory as inventory, book_legacy_cleanup as cleanup


class LegacyBookCleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        result = inventory.save_inventory_book({'request_id':'category_cleanup_fixture','isbn':'9788024932460','title':'Book','book_subjects_manual':['Beletrie']},archive_root=self.root)
        self.item = archive.find_article(result['item']['id'],archive_root=self.root)
        self.meta = archive.article_metadata_path(self.item,archive_root=self.root)
        raw=json.loads(self.meta.read_text());raw['tags']=['fantasy','obalka','ma-obrazek'];raw['attachments']=[{'id':'photo','note':'keep'}]
        self.meta.write_text(json.dumps(raw)+'\n');archive.update_registry(self.root/'registry.jsonl',raw)
        (self.root/archive.BOOK_OPTIONS_FILENAME).write_text(json.dumps({'locations':['půda'],'categories':['fantasy','román'],'other':'keep'}))
        self.before={p.relative_to(self.root).as_posix():p.read_bytes() for p in (self.meta,self.root/'registry.jsonl',self.root/archive.BOOK_OPTIONS_FILENAME,self.root/'inventory_operations.json')}

    def test_preview_only_then_exact_cleanup_preserves_every_other_value(self):
        p=cleanup.preview_cleanup(archive_root=self.root)
        self.assertEqual(p['changed_books'],1);self.assertEqual(p['removed_labels'],['fantasy']);self.assertEqual(p['removed_option_count'],2)
        self.assertEqual(self.before,{name:(self.root/name).read_bytes() for name in self.before})
        with self.assertRaises(ValueError):cleanup.apply_cleanup(plan_id=p['plan_id'],confirmation='ano',archive_root=self.root)
        self.assertEqual(self.before,{name:(self.root/name).read_bytes() for name in self.before})
        result=cleanup.apply_cleanup(plan_id=p['plan_id'],confirmation=cleanup.CONFIRMATION,archive_root=self.root)
        raw=json.loads(self.meta.read_text());old=json.loads(self.before[str(self.meta.relative_to(self.root))]);old['tags']=['obalka','ma-obrazek']
        self.assertEqual(raw,old);self.assertEqual(raw['book_subjects_manual'],['Beletrie'])
        self.assertEqual(json.loads((self.root/archive.BOOK_OPTIONS_FILENAME).read_text()),{'locations':['půda'],'other':'keep'})
        self.assertEqual((self.root/'inventory_operations.json').read_bytes(),self.before['inventory_operations.json'])
        backed=[p.read_bytes() for p in Path(result['backup_directory']).glob('*.bin')]
        self.assertCountEqual(backed,[self.before[name] for name in self.before if name!='inventory_operations.json'])
        self.assertTrue(cleanup.apply_cleanup(plan_id=p['plan_id'],confirmation=cleanup.CONFIRMATION,archive_root=self.root)['already_done'])

    def test_other_categories_and_actual_photo_bytes_are_untouched(self):
        from datetime import datetime, timezone
        raw=archive.write_text_archive(title="Science fixture",text="Science content",archive_root=self.root,now=datetime.now(timezone.utc),category="science",tags=["fantasy"],source_label="fixture",source_note="keep")
        item=archive.article_item_from_raw(raw)
        path=archive.article_metadata_path(item,archive_root=self.root)
        before=path.read_bytes()
        photo=self.meta.parent/"photo.jpg"; photo.write_bytes(b"private-photo-exact-bytes")
        p=cleanup.preview_cleanup(archive_root=self.root)
        cleanup.apply_cleanup(plan_id=p["plan_id"],confirmation=cleanup.CONFIRMATION,archive_root=self.root)
        self.assertEqual(path.read_bytes(),before)
        self.assertEqual(photo.read_bytes(),b"private-photo-exact-bytes")
        self.assertEqual(archive.find_article(item.id,archive_root=self.root).tags,("fantasy",))

    def test_intervening_edit_and_tampered_plan_block_without_changes(self):
        p=cleanup.preview_cleanup(archive_root=self.root)
        original=self.meta.read_bytes();self.meta.write_bytes(original+b' ')
        with self.assertRaisesRegex(ValueError,'změnila'):cleanup.apply_cleanup(plan_id=p['plan_id'],confirmation=cleanup.CONFIRMATION,archive_root=self.root)
        self.assertEqual(self.meta.read_bytes(),original+b' ')
        self.assertFalse(list((self.root/'maintenance').glob('*backup')))
        self.meta.write_bytes(original)
        path=self.root/'maintenance'/f"categories_{p['plan_id']}.json";plan=json.loads(path.read_text());plan['changed_books']=999;path.write_text(json.dumps(plan))
        with self.assertRaises(ValueError):cleanup.apply_cleanup(plan_id=p['plan_id'],confirmation=cleanup.CONFIRMATION,archive_root=self.root)

    def test_crash_resume_uses_only_original_plan_and_backups(self):
        p=cleanup.preview_cleanup(archive_root=self.root);original=cleanup.atomic_write_text;calls=[]
        def fail(path,text):
            calls.append(path)
            if len(calls)==2:raise OSError('disk interrupted')
            original(path,text)
        with patch.object(cleanup,'atomic_write_text',side_effect=fail):
            with self.assertRaises(OSError):cleanup.apply_cleanup(plan_id=p['plan_id'],confirmation=cleanup.CONFIRMATION,archive_root=self.root)
        result=cleanup.apply_cleanup(plan_id=p['plan_id'],confirmation=cleanup.CONFIRMATION,archive_root=self.root)
        self.assertEqual(result['state'],'done');self.assertEqual(json.loads(self.meta.read_text())['tags'],['obalka','ma-obrazek'])

    def test_pending_inventory_request_blocks_cleanup(self):
        path=self.root/'inventory_operations.json';data=json.loads(path.read_text());next(iter(data['operations'].values()))['state']='prepared';path.write_text(json.dumps(data))
        p=cleanup.preview_cleanup(archive_root=self.root);self.assertFalse(p['ready'])
        with self.assertRaises(ValueError):cleanup.apply_cleanup(plan_id=p['plan_id'],confirmation=cleanup.CONFIRMATION,archive_root=self.root)
