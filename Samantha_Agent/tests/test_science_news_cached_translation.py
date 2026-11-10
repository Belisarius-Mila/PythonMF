import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.science_news import ScienceNews, identity
from app.science_news_cached_translation import attach_and_save
from tests.test_science_news import item


class CachedTranslationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.store = ScienceNews(self.root / 'news', self.root / 'archive')
        self.store.publish('fixture', [item()], available_at='2026-11-09T09:00:00+00:00')
        self.source = 'A complete source paragraph. ' * 20
        self.translation = 'Úplný český překlad zdrojového odstavce. ' * 20
        self.args = dict(item_id=identity(item()), source_url=item()['source_url'], source_text=self.source,
            source_sha256=hashlib.sha256(self.source.encode()).hexdigest(), translation=self.translation,
            translation_sha256=hashlib.sha256(self.translation.encode()).hexdigest(), permission='public-domain',
            request_id='save-reviewed-fixture', confirmed=True)

    def test_save_contains_full_czech_translation_link_and_follow(self):
        before = self.store._read()
        result = attach_and_save(self.store, **self.args)
        body = (self.store.archive_root / 'articles' / result['archive_id'] / 'article.txt').read_text()
        self.assertIn(self.translation, body)
        self.assertIn(item()['source_url'], body)
        self.assertEqual(self.store.overview()['pending_count'], 0)
        self.assertTrue(self.store.overview()['follows'][0]['active'])
        self.assertEqual(self.store._read()['jobs'], before['jobs'])
        self.assertEqual(self.store._read()['issues'], before['issues'])

    def test_replay_after_lost_ack_does_not_create_another_card_or_overwrite_user_edit(self):
        original = self.store.decide
        def lost(*args):
            original(*args)
            raise TimeoutError('acknowledgement lost')
        with patch.object(self.store, 'decide', side_effect=lost), self.assertRaises(TimeoutError):
            attach_and_save(self.store, **self.args)
        card = next((self.store.archive_root / 'articles').iterdir()) / 'article.txt'
        card.write_text('Later user edit')
        result = attach_and_save(self.store, **self.args)
        self.assertTrue(result['replayed'])
        self.assertEqual(card.read_text(), 'Later user edit')
        self.assertEqual(len(list((self.store.archive_root / 'articles').iterdir())), 1)

    def test_wrong_digest_source_or_missing_confirmation_does_not_change_item(self):
        for change in ({'source_sha256':'0'*64}, {'translation_sha256':'0'*64}, {'confirmed':False},
                       {'source_url':'https://www.nature.com/other'}, {'permission':'unknown'}):
            with self.subTest(change=change):
                before = self.store.path.read_bytes()
                with self.assertRaises(ValueError):
                    attach_and_save(self.store, **{**self.args, **change})
                self.assertEqual(self.store.path.read_bytes(), before)
        self.assertFalse(self.store.archive_root.exists())

    def test_other_decision_or_unknown_operation_is_preserved(self):
        with self.store.transaction() as state:
            state['items'][self.args['item_id']]['operation'] = 'different-request'
        with self.assertRaises(ValueError):
            attach_and_save(self.store, **self.args)
        self.assertFalse(self.store.archive_root.exists())

    def test_dismissed_news_is_not_resurrected(self):
        self.store.decide(self.args['item_id'], 'dismiss', 'original-dismiss')
        before = self.store.path.read_bytes()
        with self.assertRaises(ValueError):
            attach_and_save(self.store, **self.args)
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_uncertain_paid_job_blocks_cached_replacement_without_resending(self):
        with self.store.transaction() as state:
            state['jobs']['model_translation_'+self.args['item_id']] = {'state':'delivery_unknown'}
        before = self.store.path.read_bytes()
        with self.assertRaises(ValueError):
            attach_and_save(self.store, **self.args)
        self.assertEqual(self.store.path.read_bytes(), before)

    def test_existing_different_translation_is_preserved(self):
        with self.store.transaction() as state:
            state['items'][self.args['item_id']]['translation'] = 'Other translation'
        with self.assertRaises(ValueError):
            attach_and_save(self.store, **self.args)
        self.assertEqual(self.store.item(self.args['item_id'])['translation'], 'Other translation')

    def test_existing_archive_without_translation_and_symlink_are_not_overwritten(self):
        directory = self.store.archive_root / 'articles' / ('science_'+self.args['item_id'][3:])
        directory.mkdir(parents=True)
        (directory / 'article.txt').write_text('Existing unrelated or partial content')
        with self.assertRaises(ValueError):
            attach_and_save(self.store, **self.args)
        self.assertEqual((directory / 'article.txt').read_text(), 'Existing unrelated or partial content')
