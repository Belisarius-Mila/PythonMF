from pathlib import Path
import json
import tempfile
import unittest

from app.article_archive import archive_book_entry, archive_text_entry
from app.shared_chat import SharedChat, ChatError
from app.shared_chat_library import LibraryReader, PAGE_CHARS
from tests.test_shared_chat import fixture_hub, ChatModel


def library_fixture(root):
    from app.book_taxonomy import GROUP_OPTIONS
    group = next(g for g in GROUP_OPTIONS if 'istor' in g['label'])
    book = archive_book_entry(title='Dějiny Evropy', author='Syntetická autorka',
        summary='Historie Rakouska a střední Evropy. Pouze anotace.', location='Police B',
        book_subjects_manual=[group['subject']], book_groups_manual=[group['code']], archive_root=root)['item']
    recipe = archive_text_entry(title='Jablečný koláč', text='Syntetický recept. Jablka, mouka a pečení.',
        category='recipes', archive_root=root)['item']
    place = archive_text_entry(title='Salcburk', text='Rakousko. Místo se syntetickou fotografií.',
        category='travel_places', archive_root=root)['item']
    study = archive_text_entry(title='Syntetická studie', text='Výzkum.\n' + 'Dlouhý uložený text.\n' * 3000,
        category='science', archive_root=root)['item']
    return book, recipe, place, study


class LibraryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)/'archive'
        self.book, self.recipe, self.place, self.study = library_fixture(self.root)
        self.reader = LibraryReader(self.root)

    def test_searches_whole_catalog_accent_tolerantly_by_text_author_location_and_topic(self):
        self.assertEqual([r['id'] for r in self.reader.search('Doporuč mi něco z našich knih o historii')['items']], [self.book['id']])
        self.assertEqual(self.reader.search('synteticka autorka')['items'][0]['id'], self.book['id'])
        self.assertEqual(self.reader.search('police b')['items'][0]['book_location'], 'Police B')
        found = self.reader.prepare('Co máme uloženého o Rakousku?', {})
        self.assertEqual({r['id'] for r in found['items']}, {self.book['id'], self.place['id']})
        self.assertEqual(found['catalog_count'], 4)
        all_types = self.reader.prepare('Co máme v knihovně o Rakousku?', {})
        self.assertEqual({r['id'] for r in all_types['items']}, {self.book['id'], self.place['id']})
        self.assertEqual(self.reader.search('recepty v knihovně')['count'], 1)
        self.assertEqual(self.reader.search('knihy o neexistujicimtematu')['count'], 0)

    def test_new_items_and_text_edits_invalidate_cache_without_writing_archive(self):
        first = self.reader.search('recepty'); self.assertEqual(first['count'], 1)
        archive_text_entry(title='Hruškový koláč', text='Hrušky.', category='recipes', archive_root=self.root)
        self.assertEqual(self.reader.search('recepty')['count'], 2)
        registry = [json.loads(s) for s in (self.root/'registry.jsonl').read_text().splitlines()]
        item = next(r for r in registry if r['id'] == self.recipe['id'])
        (self.root/item['text_file']).write_text('Nový jedinečný citronový text.')
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(self.reader.search('citronovy')['count'], 1)
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_full_stored_study_pages_and_digest_guard(self):
        first = self.reader.detail(self.study['id']); self.assertTrue(first['more'])
        self.assertEqual(len(first['text']), PAGE_CHARS)
        text = first['text']; page = first
        while page['more']:
            page = self.reader.detail(self.study['id'], page['next_offset'], page['sha256']); text += page['text']
        self.assertEqual(len(text), first['total_chars'])
        self.assertIn('Dlouhý uložený text.', text)
        with self.assertRaises(ValueError): self.reader.detail(self.study['id'], PAGE_CHARS)
        with self.assertRaises(ValueError): self.reader.detail(self.study['id'], PAGE_CHARS, '0'*64)
        with self.assertRaises(ValueError): self.reader.detail(self.study['id'], -1)

    def test_natural_open_uses_previous_result_ids_and_admits_ambiguity(self):
        previous = self.reader.prepare('Co máme uloženého o Rakousku?', {})
        opened = self.reader.prepare('Otevři druhý', previous)
        self.assertEqual(opened['selected_id'], previous['items'][1]['id'])
        self.assertEqual(self.reader.prepare('Otevři to', previous)['selected_id'], '')
        recipes = self.reader.prepare('Najdi recepty', {})
        self.assertEqual(self.reader.prepare('Otevři ten recept', recipes)['selected_id'], self.recipe['id'])
        science = self.reader.prepare('Otevři syntetickou studii', {})
        self.assertEqual(science['selected_id'], self.study['id'])
        source = science['model_context']['sources'][0]
        self.assertFalse(source['text_truncated']); self.assertEqual(len(source['text']), source['text_chars'])
        self.assertIsNone(self.reader.prepare('Ahoj Samanto', previous))

    def test_corrupt_registry_duplicate_ids_and_escaping_paths_are_not_empty_success(self):
        registry = self.root/'registry.jsonl'; original = registry.read_text()
        entry = json.loads(original.splitlines()[0])
        bad = [original+'\n{broken', original+'\n'+json.dumps(entry)]
        for path in ('../../outside.txt', '/tmp/outside.txt'):
            value = dict(entry, text_file=path); bad.append(json.dumps(value))
        external = self.root.parent/'outside.txt'; external.write_text('PRIVATE OUTSIDE')
        link = self.root/'escaped.txt'; link.symlink_to(external)
        bad.append(json.dumps(dict(entry, text_file='escaped.txt')))
        for raw in bad:
            registry.write_text(raw)
            with self.assertRaises((ValueError, OSError)): self.reader.search('knihy')
        self.assertEqual(external.read_text(), 'PRIVATE OUTSIDE')


class SharedLibraryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.book, self.recipe, self.place, self.study = library_fixture(self.root/'archive')
        self.tasks = []; ChatModel.instances = []; ChatModel.fail_send = False
        self.service = SharedChat(self.root/'chat', library_reader=LibraryReader(self.root/'archive'), hub_factory=fixture_hub, launcher=self.tasks.append)
        self.host = self.action('create', name='Mint', request_id='library-create-001')
        self.token = self.host['client_token']

    def action(self, action, token=None, **payload):
        return self.service.execute({'action': action, 'editor_id': 'library-editor-001',
            **({'client_token': token} if token else {}), **payload})

    def test_phone_open_is_shared_persisted_and_never_calls_model_or_mutates_draft(self):
        paired = self.action('pair', self.token)
        phone = self.action('join', name='iPhone', code=paired['pair_code'], request_id='library-join-001')
        found = self.action('library_search', self.token, query='recepty', expected_library_revision=0)
        opened = self.action('library_open', phone['client_token'], item_id=self.recipe['id'], expected_library_revision=found['library']['revision'])
        self.assertEqual(opened['library'], self.service.status(self.token, 'library-editor-001')['library'])
        self.assertEqual(opened['draft'], found['draft'])
        self.assertEqual(self.tasks, []); self.assertEqual(ChatModel.instances, [])
        with self.assertRaises(ChatError): self.action('library_open', self.token, item_id=self.book['id'], expected_library_revision=opened['library']['revision'])
        with self.assertRaises(ChatError): self.action('library_open', self.token, item_id=self.recipe['id'], expected_library_revision=0)
        reload = SharedChat(self.root/'chat', library_reader=self.service.library_reader)
        self.assertEqual(reload.status(self.token, 'library-editor-001')['library']['selected_id'], self.recipe['id'])

    def test_authenticated_room_result_scope_and_no_raw_paths_or_model_context_in_status(self):
        self.action('library_search', self.token, query='recepty', expected_library_revision=0)
        other = self.action('create', name='Other', request_id='library-other-001')
        for token, item in [(other['client_token'], self.recipe['id']), (self.token, self.study['id']), ('0'*64, self.recipe['id'])]:
            with self.assertRaises(ChatError): self.service.library_detail(token, 'library-editor-001', item)
        result = self.service.library_detail(self.token, 'library-editor-001', self.recipe['id'])
        self.assertIn('Syntetický recept.', result['text'])
        raw = json.dumps(self.service.status(self.token, 'library-editor-001'))
        self.assertNotIn('model_context', raw); self.assertNotIn('text_file', raw); self.assertNotIn(str(self.root), raw)

    def test_library_context_enriches_exactly_one_original_turn_and_keeps_user_text(self):
        state = self.action('claim', self.token, expected_revision=0, takeover=True)
        text = 'Doporuč mi knihu o historii'
        state = self.action('draft', self.token, text=text, expected_revision=state['draft']['revision'])
        args = {'expected_revision': state['draft']['revision'], 'client_message_id': state['draft']['client_message_id']}
        self.action('send', self.token, **args); self.action('send', self.token, **args)
        self.assertEqual(len(self.tasks), 1); self.tasks.pop()()
        self.assertEqual(sum(m.sent for m in ChatModel.instances), 1)
        self.assertIn('Historie Rakouska', ChatModel.instances[0].sent_texts[0])
        status = self.service.status(self.token, 'library-editor-001')
        self.assertEqual(status['messages'][0]['user_text'], text)
        self.assertEqual(status['messages'][0]['status'], 'completed')
        self.assertEqual(status['library']['items'][0]['id'], self.book['id'])


if __name__ == '__main__': unittest.main()
