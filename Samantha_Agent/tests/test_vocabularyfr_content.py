"""Synthetic FR contract tests; these do not attest to private learner data."""
from __future__ import annotations

from copy import deepcopy
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'VocabularyFR'))
import vocabulary_fr_catalog as catalog
import vocabulary_fr_audio as audio
import vocabulary_fr_export as export


def fixture():
    # Invented editorial inventory, deliberately unrelated to a real input CSV.
    rows = [dict(zip(catalog.COLUMNS, values)) for values in [
        ('œuvre-test', 'syntetický význam', '8', '😀 Voici l’œuvre-test.', 'Syntetická věta.', 'ne', 'ne', 'f'),
        ('œuvre-test', 'jiný syntetický význam', '3', 'Autre œuvre-test.', 'Jiná testovací věta.', 'ne', 'ano', 'm'),
        ('œuvre-test', 'syntetický význam', '15', 'Ancienne œuvre-test.', 'Starší testovací věta.', 'ano', 'ne', 'f'),
    ]]
    image = Image.new('RGB', (32, 25), '#aabbdd')
    buf = io.BytesIO(); image.save(buf, format='PNG'); raw = buf.getvalue()
    entries = []
    for index, row in enumerate(rows[:2], 1):
        entries.append({'id': index, 'uid': f'vfr-{index:04d}', 'sourceIdentity': catalog.body(row),
                        'omittedSources': [catalog.body(rows[2])] if index == 1 else [],
                        'body': {**catalog.body(row), 'genderFr': row['gender_fr']},
                        'active': True, 'primaryGroup': 'topic-01', 'topicIds': ['topic-01'],
                        'partOfSpeech': ['noun'], 'teachingType': 'word', 'expressionType': 'word',
                        'difficultyBand': 1, 'difficultyStatus': 'proposed', 'addedAt': None,
                        'legacyAddedAt': None, 'origin': 'legacy', 'lemma': None, 'formOfUid': None,
                        'related': [], 'imageFile': 'images/test.png', 'imageSha256': catalog.sha(raw),
                        'imageRole': 'mnemonic', 'imageReviewed': True, 'conflicts': ['synthetic-conflict']})
    doc = {'schemaVersion': 1, 'language': 'fr', 'itemCount': 2, 'sourceRowCount': 3,
           'parents': [{'id': 'synthetic', 'label': 'synthetic'}],
           'groups': [{'id': f'topic-{i:02d}', 'label': f'test {i}', 'parentId': 'synthetic'} for i in range(1, 19)],
           'entries': entries}
    return rows, doc, raw


def sentence_source(data):
    entries = {}
    for item in data['items']:
        match = 'œuvre-test'
        entries[item['uid']] = {'sourceFr': item['fr'], 'sourceCz': item['cz'],
                               'sourceSentenceFr': item['sentenceFr'], 'sourceSentenceCz': item['sentenceCz'],
                               'reviewed': True, 'concepts': [{'uid': item['uid'], 'sourceFr': item['fr'],
                                                            'sourceCz': item['cz'], 'text': match, 'occurrence': 1}]}
    return {'schemaVersion': 1, 'language': 'fr', 'kind': 'sentence-pictures', 'maxPictures': 5, 'entries': entries}


class CatalogTests(unittest.TestCase):
    def test_reorder_and_order_renumber_do_not_reassign_uids(self):
        rows, doc, _ = fixture()
        first, hints = catalog.resolve_rows(rows, doc)
        for i, row in enumerate(rows):
            row['Order'] = str(100 + i)
        second, changed_hints = catalog.resolve_rows(rows[::-1], doc)
        self.assertEqual(first, second)
        self.assertEqual(hints, changed_hints)
        self.assertEqual(hints['vfr-0001'], {'learned': True, 'hard': False})
        self.assertEqual(hints['vfr-0002'], {'learned': False, 'hard': True})

    def test_learner_hints_change_without_identity_change(self):
        rows, doc, _ = fixture(); rows[0]['HT'] = 'ano'
        entries, hints = catalog.resolve_rows(rows, doc)
        self.assertEqual(entries[0]['uid'], 'vfr-0001'); self.assertTrue(hints['vfr-0001']['hard'])

    def test_unknown_changed_sentence_or_meaning_fails(self):
        for field in ('FR', 'CZ', 'Sentence', 'SentenceT'):
            rows, doc, _ = fixture(); rows[0][field] += '!'
            with self.subTest(field=field), self.assertRaises(ValueError): catalog.resolve_rows(rows, doc)

    def test_missing_and_duplicate_source_fail(self):
        rows, doc, _ = fixture()
        for changed in (rows[:2], rows + [rows[0]]):
            with self.assertRaises(ValueError): catalog.resolve_rows(changed, doc)

    def test_case_and_accents_distinguish_meanings(self):
        rows, doc, _ = fixture(); rows[0]['FR'] = 'oeuvre-test'
        with self.assertRaises(ValueError): catalog.resolve_rows(rows, doc)
        rows, doc, _ = fixture(); rows[0]['FR'] = rows[0]['FR'].upper()
        with self.assertRaises(ValueError): catalog.resolve_rows(rows, doc)

    def test_web_correction_preserves_original_lookup(self):
        rows, doc, _ = fixture(); doc['entries'][0]['body']['cz'] = 'explicit corrected synthetic meaning'
        entries, _ = catalog.resolve_rows(rows, doc)
        self.assertEqual(entries[0]['body']['cz'], 'explicit corrected synthetic meaning')

    def test_duplicate_uid_and_source_alias_fail(self):
        _, doc, _ = fixture(); doc['entries'][1]['uid'] = 'vfr-0001'
        with self.assertRaises(ValueError): catalog.validate_catalog(doc)
        _, doc, _ = fixture(); doc['entries'][1]['omittedSources'] = [doc['entries'][0]['sourceIdentity']]
        with self.assertRaises(ValueError): catalog.validate_catalog(doc)

    def test_unsafe_inputs_case_traversal_and_symlink_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); (root / 'Exact.txt').write_text('test')
            (root / 'linked.txt').symlink_to(root / 'Exact.txt')
            for name in ('exact.txt', '../Exact.txt', '/Exact.txt', 'a/../Exact.txt', 'linked.txt', 'a\\x'):
                with self.subTest(name=name), self.assertRaises(ValueError): catalog.safe_file(root, name)

    def test_git_private_guard_rejects_public_and_tracked_destinations(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / '.gitignore').write_text('private/\ndocs/\n')
            self.assertEqual(catalog.private_output(root / 'private/bundle'), root / 'private/bundle')
            for name in ('docs/bundle', 'public/bundle', '.git/bundle'):
                with self.subTest(name=name), self.assertRaises(ValueError): catalog.private_output(root / name)
            (root / 'private').mkdir(); (root / 'private/tracked').write_text('test')
            subprocess.run(['git', '-C', str(root), 'add', '-f', 'private/tracked'], check=True)
            with self.assertRaises(ValueError): catalog.private_output(root / 'private')


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.rows, self.catalog, raw = fixture()
        (self.root / 'images').mkdir(); (self.root / 'images/test.png').write_bytes(raw)
        with (self.root / 'source.csv').open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=catalog.COLUMNS); writer.writeheader(); writer.writerows(self.rows)
        self.data, self.assets, _ = export.prepare_data(self.catalog, self.root)

    def test_no_private_state_or_source_paths_in_export(self):
        keys = set(self.data['items'][0])
        self.assertFalse(keys & {'L', 'HT', 'sourceIdentity', 'sourceRow', 'imageFile', 'PIN', 'learned', 'hard'})
        self.assertNotIn(str(self.root), json.dumps(self.data))

    def test_pinned_image_mismatch_fails(self):
        (self.root / 'images/test.png').write_bytes(b'changed')
        with self.assertRaises(ValueError): export.prepare_data(self.catalog, self.root)

    def test_whole_word_fallback_and_conflicts(self):
        result = export.practice(self.data, self.catalog)
        entry = result['entries']['vfr-0001']
        self.assertEqual(entry['pieces'], ['œuvre-test']); self.assertFalse(entry['reviewed'])
        self.assertEqual(entry['displayMode'], 'whole-word')
        self.assertEqual(entry['conflicts'], result['entries']['vfr-0002']['conflicts'])

    def test_elision_and_utf16_offsets(self):
        source = sentence_source(self.data); result = export.sentence_pictures(source, self.data)
        ref = result['entries']['vfr-0001']['concepts'][0]
        self.assertEqual(ref['start'], 11)  # emoji occupies two UTF-16 units
        self.assertEqual(ref['end'], 21)

    def test_wrong_meaning_offset_missing_coverage_and_substrings_fail(self):
        for change in ('meaning', 'offset', 'missing', 'substring'):
            source = sentence_source(self.data)
            ref = source['entries']['vfr-0001']['concepts'][0]
            if change == 'meaning': ref['sourceCz'] = 'wrong'
            if change == 'offset': ref['start'] = 10
            if change == 'missing': del source['entries']['vfr-0002']
            if change == 'substring': ref['text'] = 'œuvre'
            # Hyphen is a boundary, so use an inside-letters substring instead.
            if change == 'substring': ref['text'] = 'uvre'
            with self.subTest(change=change), self.assertRaises(ValueError): export.sentence_pictures(source, self.data)

    def test_more_than_five_and_repeated_picture_fail(self):
        for n in (2, 6):
            source = sentence_source(self.data); source['entries']['vfr-0001']['concepts'] *= n
            with self.assertRaises(ValueError): export.sentence_pictures(source, self.data)

    def make_payload(self):
        manifests, sounds, _ = audio.prepare(self.data['items'], {})
        objects = {export.DATA_NAME: self.data, export.QUIZ_NAME: export.practice(self.data, self.catalog),
                   export.PICTURES_NAME: export.sentence_pictures(sentence_source(self.data), self.data),
                   **{export.AUDIO_NAMES[k]: v for k, v in manifests.items()}}
        for path, raw in {**self.assets, **sounds}.items(): export.write_new(self.root / 'payload' / path, raw)
        for path, value in objects.items(): export.write_new(self.root / 'payload' / path, catalog.encoded(value))
        return self.root / 'payload'

    def test_actual_payload_validation_is_required(self):
        root = self.make_payload(); proof = export.validate_payload(root, self.catalog)
        self.assertEqual(proof['cards'], 2); self.assertEqual(proof['audio']['words']['status'], 'not-generated')
        (root / export.QUIZ_NAME).write_text('{}')
        with self.assertRaises(ValueError): export.validate_payload(root, self.catalog)

    def test_missing_and_extra_asset_fail(self):
        root = self.make_payload()
        (root / 'assets/extra.txt').write_text('extra')
        with self.assertRaises(ValueError): export.validate_payload(root, self.catalog)

    def test_overstated_or_implicit_audio_availability_fails(self):
        root = self.make_payload()
        original = catalog.load(root / export.AUDIO_NAMES['words'])
        for change in ('complete', 'missing-channel', 'empty-path', 'wrong-identity', 'wrong-language'):
            value = deepcopy(original); first = value['items']['vfr-0001']
            if change == 'complete': value['status'] = 'complete'
            if change == 'missing-channel': del first['fr']
            if change == 'empty-path': first['fr'] = ''
            if change == 'wrong-identity': first['sourceCz'] = 'different'
            if change == 'wrong-language': value['language'] = 'it'
            value['sourceDigest'] = catalog.sha(catalog.encoded(value['items']))
            (root / export.AUDIO_NAMES['words']).write_bytes(catalog.encoded(value))
            with self.subTest(change=change), self.assertRaises(ValueError): export.validate_payload(root, self.catalog)

    def closed_bundle(self):
        self.make_payload()
        export.write_new(self.root / 'catalog.json', catalog.encoded(self.catalog))
        code = {'VocabularyFR/' + n: catalog.digest(ROOT / 'VocabularyFR' / n) for n in
                ('vocabulary_fr_catalog.py', 'vocabulary_fr_audio.py', 'vocabulary_fr_export.py')}
        files = {p.relative_to(self.root).as_posix(): {'bytes': p.stat().st_size, 'sha256': catalog.digest(p)}
                 for p in self.root.rglob('*') if p.is_file()}
        manifest = {'schemaVersion': 1, 'project': 'VocabularyFR', 'bundleId': 'synthetic',
                    'state': 'closed-private', 'private': True, 'publicPromotionApproved': False,
                    'itemCount': 2, 'sourceRowCount': 3, 'codeCommit': 'a' * 40,
                    'codeSourceSha256': code, 'catalogSha256': catalog.sha(catalog.encoded(self.catalog)),
                    'files': files, 'contentDigest': catalog.sha(catalog.encoded(files)),
                    'verification': export.validate_payload(self.root / 'payload', self.catalog)}
        export.write_new(self.root / 'manifest.json', catalog.encoded(manifest))
        return self.root

    def test_closed_bundle_verification_and_external_digest(self):
        root = self.closed_bundle()
        result = export.verify(root, expected_manifest_sha256=catalog.digest(root / 'manifest.json'))
        self.assertEqual(result['cards'], 2); self.assertFalse(result['publicPromotionApproved'])
        with self.assertRaises(ValueError): export.verify(root, expected_manifest_sha256='0' * 64)

    def test_closed_bundle_rejects_changed_bytes(self):
        root = self.closed_bundle(); (root / export.QUIZ_NAME).parent.mkdir(exist_ok=True)
        (root / 'payload' / export.QUIZ_NAME).write_text('{}')
        with self.assertRaises(ValueError): export.verify(root)

    def test_closed_bundle_rejects_extra_nested_manifest(self):
        root = self.closed_bundle(); (root / 'payload/manifest.json').write_text('{}')
        with self.assertRaises(ValueError): export.verify(root)

    def test_closed_bundle_rejects_symlinks(self):
        root = self.closed_bundle(); (root / 'link').symlink_to(root / 'catalog.json')
        with self.assertRaises(ValueError): export.verify(root)

    def test_build_never_overwrites_existing_destination(self):
        with self.assertRaises(ValueError):
            export.build(self.root, self.root, self.root, code_commit='a' * 40, bundle_id='synthetic')


class AudioTests(unittest.TestCase):
    def test_partial_czech_without_french(self):
        rows, doc, _ = fixture(); items = [{'uid': e['uid'], **e['body']} for e in doc['entries']]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); raw = b'synthetic bytes only, not real media'
            (root / 'test.mp3').write_bytes(raw)
            index = {('words', audio.text(items[0]['cz'], 'words')): (root, 'test.mp3', catalog.sha(raw))}
            manifests, assets, _ = audio.prepare(items, index)
            words = manifests['words']; record = words['items']['vfr-0001']
            self.assertEqual(words['status'], 'partial'); self.assertIsNone(record['fr'])
            self.assertTrue(record['cz'].startswith('assets/vocabulary-fr-audio/'))
            self.assertEqual(list(assets.values()), [raw]); self.assertEqual(manifests['sentences']['status'], 'not-generated')

    def test_changed_reused_bytes_fail(self):
        _, doc, _ = fixture(); items = [{'uid': e['uid'], **e['body']} for e in doc['entries']]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); (root / 'test.mp3').write_bytes(b'changed')
            index = {('words', audio.text(items[0]['cz'], 'words')): (root, 'test.mp3', '0' * 64)}
            with self.assertRaises(ValueError): audio.prepare(items, index)

    def test_no_italian_syllabification_or_accent_folding(self):
        self.assertNotEqual(audio.text('sur', 'words'), audio.text('sûr', 'words'))
        self.assertEqual(audio.text("  l’œuvre  ", 'words'), 'l’œuvre')
        self.assertEqual(audio.text('test; autre (sens)', 'words'), 'test. autre sens')

    def test_unknown_voice_rejected(self):
        with self.assertRaises(ValueError): audio.prepare([], {}, french_voice='it-IT-ElsaNeural')


if __name__ == '__main__':
    unittest.main()
