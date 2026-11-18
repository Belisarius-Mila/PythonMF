from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from app.article_archive import archive_book_entry, archive_text_entry, update_article
from app.shared_chat import SharedChat, ChatError
from app.shared_chat_library import LibraryReader, PAGE_CHARS, save_reference
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

    def test_place_state_defaults_to_unknown_and_refuses_stale_or_non_place_updates(self):
        item_id = self.place['id']
        self.assertEqual(self.reader.detail(item_id)['item']['visit_state'], 'unknown')
        self.reader.set_visit_state(item_id, 'visited', 'unknown')
        self.assertEqual(self.reader.detail(item_id)['item']['visit_state'], 'visited')
        update_article(article_id=item_id, title='Salcburk', text='Nová poznámka',
                       category='travel_places', archive_root=self.root)
        self.assertEqual(self.reader.detail(item_id)['item']['visit_state'], 'visited')
        self.assertEqual(self.reader.prepare('Doporuč mi místo v Rakousku', {})['count'], 0)
        with self.assertRaises(ValueError):
            self.reader.set_visit_state(item_id, 'tip', 'unknown')
        with self.assertRaises(ValueError):
            self.reader.set_visit_state(self.recipe['id'], 'visited', 'unknown')
        self.assertEqual(self.reader.detail(item_id)['item']['visit_state'], 'visited')

    def test_save_request_uses_one_confirmed_answer_and_refuses_ambiguous_reference(self):
        answer = {'status':'completed', 'delivery_confirmed':True,
                  'answer':'[První](https://example.test/1) [Druhý](https://example.test/2)'}
        self.assertIn('notice', save_reference('Ulož tento článek', [answer]))
        self.assertEqual(save_reference('Ulož druhý recept', [answer]),
                         {'url':'https://example.test/2', 'category':'recipes'})
        mixed = {**answer, 'answer':'[První](https://example.test/1) a https://example.test/2.'}
        self.assertIn('notice', save_reference('Ulož tento článek', [mixed]))
        self.assertEqual(save_reference('Ulož druhý recept', [mixed]),
                         {'url':'https://example.test/2', 'category':'recipes'})
        self.assertEqual(save_reference('Ulož první místo, kam chceme jet', [answer]),
                         {'url':'https://example.test/1', 'category':'travel_places', 'visit_state':'want_to_visit'})
        self.assertIn('notice', save_reference('Ulož první', [{**answer, 'delivery_confirmed':False}]))
        self.assertIsNone(save_reference('Neukládej tento recept', [answer]))
        text_answer = {'status':'completed', 'delivery_confirmed':True, 'answer':'Syntetický text receptu.'}
        self.assertEqual(save_reference('Ulož recept', [text_answer]),
                         {'text':'Syntetický text receptu.', 'title':'', 'category':'recipes'})
        self.assertIn('notice', save_reference('Ulož druhý recept', [text_answer]))
        self.assertIn('notice', save_reference('Ulož recept', [{**text_answer, 'answer':'1. První\n2. Druhý'}]))

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

    def test_place_state_requires_selected_room_item_and_preserves_newer_state(self):
        found = self.action('library_search', self.token, query='Salcburk', expected_library_revision=0)
        revision = found['library']['revision']
        with self.assertRaises(ChatError):
            self.action('library_visit_state', self.token, item_id=self.place['id'], visit_state='visited',
                        expected_state='unknown', expected_library_revision=revision)
        opened = self.action('library_open', self.token, item_id=self.place['id'], expected_library_revision=revision)
        revision = opened['library']['revision']
        saved = self.action('library_visit_state', self.token, item_id=self.place['id'], visit_state='visited',
                            expected_state='unknown', expected_library_revision=revision)
        self.assertEqual(saved['library']['items'][0]['visit_state'], 'visited')
        with self.assertRaises(ChatError):
            self.action('library_visit_state', self.token, item_id=self.place['id'], visit_state='tip',
                        expected_state='unknown', expected_library_revision=revision)
        self.assertEqual(self.service.library_reader.detail(self.place['id'])['item']['visit_state'], 'visited')
        self.assertEqual(self.tasks, [])

    def test_confirmed_source_is_saved_once_and_duplicate_is_reported(self):
        url = 'https://example.test/nova-stranka'
        state = self.action('library_save_prepare', self.token, url=url, category='recipes')
        save_id = state['library_save']['id']
        page = b'<html><head><title>Testovaci recept</title></head><body><main>Suroviny a postup pro synteticky recept.</main></body></html>'
        with patch('app.article_archive.fetch_url', return_value=page) as fetch:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: self.action('library_save_confirm', self.token, save_id=save_id), range(2)))
        self.assertEqual(fetch.call_count, 1)
        final = self.service.status(self.token, 'library-editor-001')['library_save']
        self.assertEqual(final['state'], 'saved')
        self.assertTrue(any(result['library_save']['state'] == 'saved' for result in results))
        item = final['item']
        self.assertEqual(item['source_url'], url)
        self.assertEqual(item['category'], 'recipes')
        self.assertIn('Suroviny', self.service.library_reader.detail(item['id'])['text'])
        duplicate = self.action('library_save_prepare', self.token, url=url, category='recipes')
        self.assertEqual(duplicate['library_save']['state'], 'duplicate')
        self.assertEqual(duplicate['library_save']['duplicates'][0]['id'], item['id'])
        self.assertEqual(self.tasks, [])

    def test_interrupted_save_recovers_only_original_operation(self):
        url = 'https://example.test/vylet'
        state = self.action('library_save_prepare', self.token, url=url, category='travel_places')
        save_id = state['library_save']['id']
        page = b'<html><head><title>Vylet</title></head><body><main>Synteticke misto pro vylet.</main></body></html>'
        original = self.service.library_reader.save_source
        def save_then_lose_reply(*args):
            original(*args)
            raise OSError('synthetic lost result')
        with patch('app.article_archive.fetch_url', return_value=page), patch.object(self.service.library_reader, 'save_source', side_effect=save_then_lose_reply):
            result = self.action('library_save_confirm', self.token, save_id=save_id)
        self.assertEqual(result['library_save']['state'], 'unknown')
        with self.assertRaises(ChatError):
            self.action('library_save_prepare', self.token, url='https://example.test/jine', category='other')
        restored = SharedChat(self.root/'chat', library_reader=LibraryReader(self.root/'archive'))
        result = restored.execute({'action':'library_save_verify','editor_id':'library-editor-001',
                                   'client_token':self.token,'save_id':save_id})
        self.assertEqual(result['library_save']['state'], 'saved')
        self.assertEqual(result['library_save']['item']['source_url'], url)
        self.assertEqual(len([item for item in restored.library_reader.search('vylet')['items'] if item['source_url'] == url]), 1)

    def test_save_request_prepares_source_without_writing_archive_or_starting_an_extra_turn(self):
        url = 'https://example.test/recept-z-webu'
        state = self.action('claim', self.token, expected_revision=0, takeover=True)
        state = self.action('draft', self.token, text='Ulož tento recept ' + url,
                            expected_revision=state['draft']['revision'])
        before = (self.root/'archive'/'registry.jsonl').read_bytes()
        self.action('send', self.token, expected_revision=state['draft']['revision'],
                    client_message_id=state['draft']['client_message_id'])
        self.tasks.pop()()
        result = self.service.status(self.token, 'library-editor-001')
        self.assertEqual(result['library_save']['state'], 'draft')
        self.assertEqual(result['library_save']['url'], url)
        self.assertEqual(result['library_save']['category'], 'recipes')
        self.assertEqual((self.root/'archive'/'registry.jsonl').read_bytes(), before)
        self.assertEqual(sum(model.sent for model in ChatModel.instances), 1)

    def test_stale_save_preparation_cannot_overwrite_other_devices_draft(self):
        first = self.action('library_save_prepare', self.token, url='https://example.test/prvni',
                            category='other', expected_save_id='')
        with self.assertRaises(ChatError):
            self.action('library_save_prepare', self.token, url='https://example.test/druhy',
                        category='other', expected_save_id='')
        current = self.service.status(self.token, 'library-editor-001')['library_save']
        self.assertEqual(current['id'], first['library_save']['id'])
        self.assertEqual(current['url'], 'https://example.test/prvni')

    def test_natural_save_does_not_replace_a_newer_manual_proposal(self):
        state = self.action('claim', self.token, expected_revision=0, takeover=True)
        state = self.action('draft', self.token, text='Ulož https://example.test/predchozi',
                            expected_revision=state['draft']['revision'])
        self.action('send', self.token, expected_revision=state['draft']['revision'],
                    client_message_id=state['draft']['client_message_id'])
        reader = self.service.library_reader
        original = reader.source_duplicates
        def race(url):
            result = original(url)
            if url.endswith('/predchozi'):
                self.action('library_save_prepare', self.token, url='https://example.test/rucni', category='other')
            return result
        with patch.object(reader, 'source_duplicates', side_effect=race):
            self.tasks.pop()()
        current = self.service.status(self.token, 'library-editor-001')['library_save']
        self.assertEqual(current['url'], 'https://example.test/rucni')
        self.assertIn('jiný návrh', ChatModel.instances[0].sent_texts[0].casefold())

    def test_text_save_preserves_text_and_explicit_visit_status_and_detects_duplicate(self):
        text = 'Syntetický popis místa.\nDruhý odstavec.'
        draft = self.action('library_save_prepare', self.token, url='', title='Výlet', text=text,
                            category='travel_places', visit_state='want_to_visit')
        saved = self.action('library_save_confirm', self.token, save_id=draft['library_save']['id'])
        item = saved['library_save']['item']
        self.assertEqual(item['visit_state'], 'want_to_visit')
        self.assertEqual(self.service.library_reader.detail(item['id'])['text'], text)
        again = self.action('library_save_prepare', self.token, url='', title='Jiný název', text=text,
                            category='travel_places', visit_state='unknown')
        self.assertEqual(again['library_save']['state'], 'duplicate')
        self.assertEqual(again['library_save']['duplicates'][0]['id'], item['id'])

    def test_selected_text_and_url_are_both_preserved_without_downloading_page(self):
        url = 'https://example.test/vybrany-clanek'
        text = 'Přesně vybraný odstavec.\nDalší řádek.'
        draft = self.action('library_save_prepare', self.token, url=url, title='Úryvek', text=text,
                            category='other')
        self.assertEqual(draft['library_save']['text'], text)
        with patch('app.article_archive.fetch_url') as fetch:
            saved = self.action('library_save_confirm', self.token, save_id=draft['library_save']['id'])
        fetch.assert_not_called()
        item = saved['library_save']['item']
        self.assertEqual(item['source_url'], url)
        self.assertEqual(self.service.library_reader.detail(item['id'])['text'], text)
        duplicate = self.action('library_save_prepare', self.token, url=url, title='', text='', category='other')
        self.assertEqual(duplicate['library_save']['state'], 'duplicate')

    def test_followup_turn_receives_confirmed_save_state(self):
        draft = self.action('library_save_prepare', self.token, url='', title='Testovací zápis',
                            text='Syntetický text.', category='other')
        self.action('library_save_confirm', self.token, save_id=draft['library_save']['id'])
        state = self.action('claim', self.token, expected_revision=0, takeover=True)
        state = self.action('draft', self.token, text='Uložil jsi to?', expected_revision=state['draft']['revision'])
        self.action('send', self.token, expected_revision=state['draft']['revision'],
                    client_message_id=state['draft']['client_message_id'])
        self.tasks.pop()()
        self.assertIn('"state": "saved"', ChatModel.instances[0].sent_texts[0])
        self.assertIn('Testovací zápis', ChatModel.instances[0].sent_texts[0])
        self.assertEqual(sum(model.sent for model in ChatModel.instances), 1)

    def test_failure_before_writing_is_known_and_failure_after_reservation_blocks_other_rooms(self):
        url = 'https://example.test/ztraceno'
        draft = self.action('library_save_prepare', self.token, url=url, category='other')
        with patch('app.article_archive.fetch_url', side_effect=OSError('offline')):
            failed = self.action('library_save_confirm', self.token, save_id=draft['library_save']['id'])
        self.assertEqual(failed['library_save']['state'], 'not_saved')
        draft = self.action('library_save_prepare', self.token, url=url, category='other')
        page = b'<html><head><title>Ukazka</title></head><body><main>Synteticky text stranky.</main></body></html>'
        with patch('app.article_archive.fetch_url', return_value=page), patch('app.article_archive.write_article_archive', side_effect=OSError('disk')) as writer:
            failed = self.action('library_save_confirm', self.token, save_id=draft['library_save']['id'])
            self.assertEqual(failed['library_save']['state'], 'unknown')
            other = self.action('create', name='Druhá místnost', request_id='other-save-room')
            second = self.action('library_save_prepare', other['client_token'], url=url, category='other')
            blocked = self.action('library_save_confirm', other['client_token'], save_id=second['library_save']['id'])
            self.assertEqual(blocked['library_save']['state'], 'unknown')
            self.assertEqual(writer.call_count, 1)

    def test_canonical_source_duplicate_is_detected_after_fetch_and_other_room_cannot_confirm(self):
        first = 'https://example.test/clanek'
        second = 'https://example.test/jiny-odkaz'
        page = (b'<html><head><title>Ukazka</title><link rel="canonical" '
                b'href="https://example.test/original"></head><body><main>Synteticky text.</main></body></html>')
        draft = self.action('library_save_prepare', self.token, url=first, category='other')
        other = self.action('create', name='Jiná místnost', request_id='other-unique-room')
        with self.assertRaises(ChatError):
            self.action('library_save_confirm', other['client_token'], save_id=draft['library_save']['id'])
        with patch('app.article_archive.fetch_url', return_value=page):
            saved = self.action('library_save_confirm', self.token, save_id=draft['library_save']['id'])
            next_draft = self.action('library_save_prepare', self.token, url=second, category='other')
            duplicate = self.action('library_save_confirm', self.token, save_id=next_draft['library_save']['id'])
        self.assertEqual(saved['library_save']['state'], 'saved')
        self.assertEqual(duplicate['library_save']['state'], 'duplicate')
        self.assertEqual(duplicate['library_save']['item']['id'], saved['library_save']['item']['id'])

    def test_url_query_identifies_distinct_articles_but_tracking_does_not(self):
        page = b'<html><head><title>Clanek</title></head><body><main>Obsah testovaci stranky.</main></body></html>'
        with patch('app.article_archive.fetch_url', return_value=page):
            first = self.action('library_save_prepare', self.token, url='https://example.test/view?id=1', category='other')
            saved = self.action('library_save_confirm', self.token, save_id=first['library_save']['id'])
            second = self.action('library_save_prepare', self.token, url='https://example.test/view?id=2', category='other')
            self.assertEqual(second['library_save']['state'], 'draft')
            saved_second = self.action('library_save_confirm', self.token, save_id=second['library_save']['id'])
        self.assertEqual(saved_second['library_save']['state'], 'saved')
        self.assertNotEqual(saved['library_save']['item']['id'], saved_second['library_save']['item']['id'])
        tracked = self.action('library_save_prepare', self.token, url='https://example.test/view?id=1&utm_source=test', category='other')
        self.assertEqual(tracked['library_save']['state'], 'duplicate')
        self.assertEqual(tracked['library_save']['duplicates'][0]['id'], saved['library_save']['item']['id'])

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
