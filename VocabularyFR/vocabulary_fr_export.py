"""Build/verify a closed private FR bundle. Never publish or generate audio.

Explicit input: catalog.json, source.csv, images/, sentence-pictures.json.
Private outputs only, exclusive creation. Inspection never modifies the bundle.
"""
from __future__ import annotations

import argparse
from collections import Counter
import io
import json
from pathlib import Path
import re
import shutil
import subprocess

from PIL import Image, ImageOps

import vocabulary_fr_audio as audio
from vocabulary_fr_catalog import (digest, encoded, load, load_rows, private_output,
                                   resolve_rows, safe_file, sha, validate_catalog)

DATA_NAME = 'data/vocabulary-fr-v2.json'
QUIZ_NAME = 'data/vocabulary-fr-quiz.json'
PICTURES_NAME = 'data/vocabulary-fr-sentence-pictures.json'
AUDIO_NAMES = {'words': 'data/vocabulary-fr-audio.json',
               'sentences': 'data/vocabulary-fr-sentence-audio.json'}
EXPORTED_FIELDS = ('id', 'uid', 'active', 'primaryGroup', 'topicIds', 'partOfSpeech',
                   'teachingType', 'expressionType', 'difficultyBand', 'difficultyStatus',
                   'addedAt', 'legacyAddedAt', 'origin', 'lemma', 'formOfUid', 'related')


def webp(raw, edge):
    with Image.open(io.BytesIO(raw)) as source:
        image = ImageOps.exif_transpose(source)
        image = image.convert('RGBA' if 'A' in image.getbands() else 'RGB')
        image.thumbnail((edge, edge), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format='WEBP', quality=84, method=4)
        return output.getvalue()


def prepare_data(catalog, input_root):
    entries, hints = resolve_rows(load_rows(safe_file(input_root, 'source.csv')), catalog)
    assets, cache, items = {}, {}, []
    for entry in entries:
        raw = safe_file(input_root, entry['imageFile']).read_bytes()
        source_sha = sha(raw)
        if source_sha != entry['imageSha256']:
            raise ValueError('Pinned image changed: ' + entry['uid'])
        if source_sha not in cache:
            paths = []
            for kind, edge in [('images', 900), ('thumbs', 240)]:
                data = webp(raw, edge)
                relative = f'assets/vocabulary-fr-v2/{kind}/{sha(data)}.webp'
                assets[relative] = data
                paths.append(relative)
            cache[source_sha] = paths
        image, thumbnail = cache[source_sha]
        items.append({**{k: entry.get(k) for k in EXPORTED_FIELDS}, **entry['body'],
                      'image': image, 'thumbnail': thumbnail,
                      'imageReviewed': True, 'imageRole': entry['imageRole']})
    data = {'schemaVersion': 2, 'appName': 'VocabularyFR', 'language': 'fr',
            'translationLanguage': 'cs', 'mode': 'private-integration',
            'imageReviewComplete': True, 'audioStatus': 'not-generated',
            'itemCount': len(items), 'sourceRowCount': catalog['sourceRowCount'],
            'parents': catalog['parents'], 'groups': catalog['groups'], 'items': items,
            'stats': {'active': sum(i['active'] for i in items),
                      'groups': dict(Counter(i['primaryGroup'] for i in items))},
            'provenance': {'catalogSha256': sha(encoded(catalog)),
                           'sourceCsvSha256': digest(safe_file(input_root, 'source.csv'))}}
    return data, assets, hints


def practice(data, catalog):
    """Whole-word fallback: no unreviewed French syllabification."""
    entries = {}
    by_uid = {e['uid']: e for e in catalog['entries']}
    for item in data['items']:
        source = by_uid[item['uid']]
        conflicts = set(source.get('conflicts', []))
        conflicts.add('image:' + item['image'].rsplit('/', 1)[-1])
        conflicts.add('spelling:' + item['fr'].casefold())
        for uid in source.get('related', []):
            conflicts.add('related:' + ':'.join(sorted((item['uid'], uid))))
        entries[item['uid']] = {k: item[k] for k in ('uid', 'fr', 'cz', 'image', 'thumbnail')}
        entries[item['uid']].update(pieces=[item['fr']], reviewed=False, displayMode='whole-word',
                                   format='colors' if item['primaryGroup'] == 'topic-10' else 'objects',
                                   conflicts=sorted(conflicts))
    return {'schemaVersion': 1, 'language': 'fr', 'kind': 'spelling-pictures', 'entries': entries}


def sentence_pictures(source, data):
    if (source.get('schemaVersion') != 1 or source.get('language') != 'fr'
            or source.get('kind') != 'sentence-pictures' or source.get('maxPictures') != 5):
        raise ValueError('Invalid sentence picture source.')
    items = {i['uid']: i for i in data['items'] if i['active']}
    entries = {}
    for uid, record in source['entries'].items():
        target = items.get(uid)
        if not target or record.get('reviewed') is not True:
            raise ValueError('Unknown/unreviewed sentence.')
        identity = {key: target[field] for key, field in (
            ('sourceFr', 'fr'), ('sourceCz', 'cz'),
            ('sourceSentenceFr', 'sentenceFr'), ('sourceSentenceCz', 'sentenceCz'))}
        if any(record.get(k) != v for k, v in identity.items()):
            raise ValueError('Stale sentence meaning.')
        concepts = record.get('concepts')
        if not isinstance(concepts, list) or not 1 <= len(concepts) <= 5:
            raise ValueError('Require 1 to 5 sentence pictures.')
        seen, images, last_end, result = set(), set(), -1, []
        for ref in concepts:
            concept = items.get(ref.get('uid'))
            text, occurrence = ref.get('text'), ref.get('occurrence')
            if (not concept or concept['uid'] in seen or ref.get('sourceFr') != concept['fr']
                    or ref.get('sourceCz') != concept['cz'] or not isinstance(text, str) or not text.strip()
                    or type(occurrence) is not int or occurrence < 1):
                raise ValueError('Unknown/stale sentence concept.')
            # French elisions: l’arbre contains arbre; no matches inside letters.
            # Offsets refer to literal sentence text, never accent-folded matching.
            matches = list(re.finditer(r'(?<!\w)' + re.escape(text) + r'(?!\w)', target['sentenceFr']))
            if occurrence > len(matches):
                raise ValueError('Concept is absent from sentence.')
            match = matches[occurrence - 1]
            if match.start() < last_end or concept['image'] in images:
                raise ValueError('Overlapping/repeated sentence pictures.')
            last_end = match.end()
            start = len(target['sentenceFr'][:match.start()].encode('utf-16-le')) // 2
            end = start + len(text.encode('utf-16-le')) // 2
            if ('start' in ref and ref['start'] != start) or ('end' in ref and ref['end'] != end):
                raise ValueError('Incorrect UTF-16 sentence offsets.')
            result.append({**ref, 'start': start, 'end': end})
            seen.add(concept['uid']); images.add(concept['image'])
        entries[uid] = {**identity, 'reviewed': True, 'concepts': result}
    if set(entries) != set(items):
        raise ValueError('Sentence picture coverage is incomplete.')
    return {'schemaVersion': 1, 'language': 'fr', 'kind': 'sentence-pictures',
            'maxPictures': 5, 'entries': entries}


def validate_payload(root, catalog):
    """Check actual private data and every referenced asset, no private skips."""
    validate_catalog(catalog)
    data = load(safe_file(root, DATA_NAME))
    by_uid = {e['uid']: e for e in catalog['entries']}
    items = data.get('items', [])
    if (data.get('schemaVersion') != 2 or data.get('language') != 'fr'
            or data.get('translationLanguage') != 'cs' or data.get('appName') != 'VocabularyFR'
            or data.get('itemCount') != len(by_uid) or data.get('sourceRowCount') != catalog['sourceRowCount']
            or data.get('parents') != catalog['parents'] or data.get('groups') != catalog['groups']
            or data.get('provenance', {}).get('catalogSha256') != sha(encoded(catalog))
            or len(items) != len(by_uid) or {i['uid'] for i in items} != set(by_uid)):
        raise ValueError('Export does not match closed catalog.')
    referenced = set()
    for item in items:
        entry = by_uid[item['uid']]
        if any(item.get(k) != v for k, v in entry['body'].items()):
            raise ValueError('Exported source text changed.')
        if any(item.get(k) != entry.get(k) for k in EXPORTED_FIELDS):
            raise ValueError('Exported editorial metadata changed.')
        if item.get('imageReviewed') is not True or item.get('imageRole') != entry['imageRole']:
            raise ValueError('Image review state changed.')
        for field, edge in [('image', 900), ('thumbnail', 240)]:
            relative = item[field]
            if not re.fullmatch(r'assets/vocabulary-fr-v2/(images|thumbs)/[0-9a-f]{64}\.webp', relative):
                raise ValueError('Invalid image namespace.')
            path = safe_file(root, relative)
            if digest(path) != path.stem:
                raise ValueError('Image byte digest mismatch.')
            if relative not in referenced:
                with Image.open(path) as image:
                    image.load()
                    if image.format != 'WEBP' or max(image.size) > edge:
                        raise ValueError('Invalid image format/size.')
            referenced.add(relative)
    quiz = load(safe_file(root, QUIZ_NAME))
    if quiz != practice(data, catalog):
        raise ValueError('Practice metadata differs from catalog.')
    pictures = load(safe_file(root, PICTURES_NAME))
    if pictures != sentence_pictures(pictures, data):
        raise ValueError('Sentence picture offsets changed.')
    availability = {}
    for kind, filename in AUDIO_NAMES.items():
        manifest = load(safe_file(root, filename))
        if (manifest.get('schemaVersion') != 1 or manifest.get('language') != 'fr'
                or manifest.get('kind') != kind or manifest.get('rate') != audio.RATE
                or manifest.get('voices', {}).get('cz') != audio.VOICE
                or manifest.get('voices', {}).get('fr') not in {None, 'fr-FR-DeniseNeural', 'fr-FR-HenriNeural'}
                or set(manifest.get('items', {})) != set(by_uid)
                or manifest.get('sourceDigest') != sha(encoded(manifest['items']))):
            raise ValueError('Invalid audio manifest identity.')
        counts, hashes = {'fr': 0, 'cz': 0}, {}
        for item in items:
            record = manifest['items'][item['uid']]
            identity = {'uid': item['uid'], 'sourceFr': item['fr'], 'sourceCz': item['cz']}
            if kind == 'sentences':
                identity.update(sourceSentenceFr=item['sentenceFr'], sourceSentenceCz=item['sentenceCz'])
            if any(record.get(k) != v for k, v in identity.items()):
                raise ValueError('Stale audio source identity.')
            for channel in ('fr', 'cz'):
                field = channel if kind == 'words' else 'sentence' + channel.title()
                if record.get('spoken' + channel.title()) != audio.text(item[field], kind):
                    raise ValueError('Stale spoken text.')
                if channel not in record:
                    raise ValueError('Unavailable audio must be explicit null.')
                relative = record[channel]
                if relative is None:
                    continue
                namespace = 'audio' if kind == 'words' else 'sentences'
                if (not isinstance(relative, str) or not re.fullmatch(
                        'assets/vocabulary-fr-' + namespace + r'/[a-z0-9-]+/[0-9a-f]{64}\.mp3', relative)
                        or manifest['voices'][channel] is None):
                    raise ValueError('Invalid audio asset/voice.')
                voice_slug = re.sub(r'([a-z])([A-Z])', r'\1-\2', manifest['voices'][channel]).lower()
                if relative.split('/')[-2] != voice_slug:
                    raise ValueError('Audio path does not match channel voice.')
                actual = digest(safe_file(root, relative))
                if manifest.get('assetSha256', {}).get(relative) != actual:
                    raise ValueError('Audio byte digest mismatch.')
                hashes[relative] = actual
                counts[channel] += 1
                referenced.add(relative)
        n = sum(counts.values())
        status = 'not-generated' if not n else 'partial' if n < len(items) * 2 else 'complete'
        if manifest.get('status') != status or manifest.get('assetSha256') != hashes:
            raise ValueError('Audio availability is overstated.')
        availability[kind] = {**counts, 'status': status}
    statuses = {v['status'] for v in availability.values()}
    expected_status = ('complete' if statuses == {'complete'} else 'not-generated'
                       if statuses == {'not-generated'} else 'partial')
    if data.get('audioStatus') != expected_status or data.get('imageReviewComplete') is not True:
        raise ValueError('Dataset availability does not match actual media.')
    actual_assets = {p.relative_to(root).as_posix() for p in (Path(root) / 'assets').rglob('*') if p.is_file()}
    if referenced != actual_assets:
        raise ValueError('Missing or unreferenced media in payload.')
    return {'cards': len(items), 'sourceRows': catalog['sourceRowCount'],
            'images': len({i['image'] for i in items}), 'assets': len(referenced),
            'sentencePictures': sum(len(v['concepts']) for v in pictures['entries'].values()),
            'audio': availability}


def write_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('xb') as handle:
        handle.write(raw)
    path.chmod(0o600)


def build(input_root, output, reuse_docs, *, code_commit, bundle_id, french_voice=None):
    input_root = Path(input_root)
    output = private_output(output)
    if not re.fullmatch(r'[0-9a-f]{40}', code_commit) or not re.fullmatch(r'[a-z0-9-]{4,100}', bundle_id):
        raise ValueError('Exact code commit and stable bundle ID required.')
    if output.exists():
        raise ValueError('Never overwrite a closed/partial bundle; use a new version.')
    repo = Path(__file__).resolve().parents[1]
    code_files = {}
    for name in ('vocabulary_fr_catalog.py', 'vocabulary_fr_audio.py', 'vocabulary_fr_export.py'):
        relative = 'VocabularyFR/' + name
        frozen = subprocess.run(['git', '-C', str(repo), 'show', code_commit + ':' + relative],
                                capture_output=True, check=True).stdout
        if frozen != Path(__file__).with_name(name).read_bytes():
            raise ValueError('Running builder differs from pinned code commit.')
        code_files[relative] = sha(frozen)
    catalog_raw = safe_file(input_root, 'catalog.json').read_bytes()
    catalog = validate_catalog(json.loads(catalog_raw))
    if catalog_raw != encoded(catalog):
        raise ValueError('Catalog must have canonical byte serialization.')
    data, assets, _hints = prepare_data(catalog, input_root)
    manifests, sounds, provenance = audio.prepare(data['items'], audio.reuse_index(reuse_docs), french_voice=french_voice)
    assets.update(sounds)
    statuses = {m['status'] for m in manifests.values()}
    data['audioStatus'] = ('complete' if statuses == {'complete'} else 'not-generated'
                           if statuses == {'not-generated'} else 'partial')
    objects = {DATA_NAME: data, QUIZ_NAME: practice(data, catalog),
               PICTURES_NAME: sentence_pictures(load(safe_file(input_root, 'sentence-pictures.json')), data),
               **{AUDIO_NAMES[k]: v for k, v in manifests.items()}}
    if safe_file(input_root, 'catalog.json').read_bytes() != catalog_raw:
        raise ValueError('Catalog changed during build.')
    output.mkdir(parents=True, mode=0o700)
    for relative, raw in assets.items():
        write_new(output / 'payload' / relative, raw)
    for relative, obj in objects.items():
        write_new(output / 'payload' / relative, encoded(obj))
    write_new(output / 'catalog.json', catalog_raw)
    write_new(output / 'audio-provenance.json', encoded(provenance))
    proof = validate_payload(output / 'payload', catalog)
    files = {p.relative_to(output).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p)}
             for p in sorted(output.rglob('*')) if p.is_file()}
    manifest = {'schemaVersion': 1, 'project': 'VocabularyFR', 'bundleId': bundle_id,
                'state': 'closed-private', 'private': True, 'publicPromotionApproved': False,
                'itemCount': len(data['items']), 'sourceRowCount': catalog['sourceRowCount'],
                'catalogSha256': sha(catalog_raw), 'codeCommit': code_commit,
                'codeSourceSha256': code_files,
                'contentDigest': sha(encoded(files)), 'files': files, 'verification': proof}
    write_new(output / 'manifest.json', encoded(manifest))
    return verify(output)


def verify(bundle, *, decode_audio=False, expected_manifest_sha256=None):
    bundle = Path(bundle)
    manifest_path = safe_file(bundle, 'manifest.json')
    if expected_manifest_sha256 is not None and digest(manifest_path) != expected_manifest_sha256:
        raise ValueError('This is not the handed-over bundle manifest.')
    manifest = load(manifest_path)
    if (manifest.get('schemaVersion') != 1 or manifest.get('project') != 'VocabularyFR'
            or manifest.get('state') != 'closed-private' or manifest.get('private') is not True
            or manifest.get('publicPromotionApproved') is not False
            or not re.fullmatch(r'[0-9a-f]{40}', manifest.get('codeCommit', ''))
            or manifest.get('contentDigest') != sha(encoded(manifest.get('files')))):
        raise ValueError('Invalid closed private bundle manifest.')
    actual = set()
    for path in bundle.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink in closed bundle.')
        if path.is_file() and path != bundle / 'manifest.json':
            actual.add(path.relative_to(bundle).as_posix())
    if actual != set(manifest['files']):
        raise ValueError('Closed bundle file set changed.')
    for relative, proof in manifest['files'].items():
        path = safe_file(bundle, relative)
        if path.stat().st_size != proof['bytes'] or digest(path) != proof['sha256']:
            raise ValueError('Closed bundle bytes changed: ' + relative)
    catalog = load(safe_file(bundle, 'catalog.json'))
    if digest(bundle / 'catalog.json') != manifest['catalogSha256']:
        raise ValueError('Closed catalog changed.')
    for relative, expected in manifest.get('codeSourceSha256', {}).items():
        if (relative not in {'VocabularyFR/vocabulary_fr_catalog.py', 'VocabularyFR/vocabulary_fr_audio.py',
                             'VocabularyFR/vocabulary_fr_export.py'}
                or digest(Path(__file__).resolve().parents[1] / relative) != expected):
            raise ValueError('Verifier code differs from pinned bundle code.')
    if len(manifest.get('codeSourceSha256', {})) != 3:
        raise ValueError('Missing code source fingerprints.')
    proof = validate_payload(bundle / 'payload', catalog)
    if (proof != manifest['verification'] or proof['cards'] != manifest['itemCount']
            or proof['sourceRows'] != manifest['sourceRowCount']):
        raise ValueError('Closed content proof changed.')
    decoded = 0
    if decode_audio:
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg:
            raise RuntimeError('ffmpeg is required for full MP3 decoding.')
        for relative in manifest['files']:
            if relative.endswith('.mp3'):
                result = subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(bundle / relative),
                                         '-f', 'null', '-'], capture_output=True, timeout=30, check=False)
                if result.returncode or result.stderr:
                    raise ValueError('MP3 decode failed: ' + relative)
                decoded += 1
    return {'bundleId': manifest['bundleId'], 'manifestSha256': digest(bundle / 'manifest.json'),
            'catalogSha256': manifest['catalogSha256'], 'contentDigest': manifest['contentDigest'],
            'codeCommit': manifest['codeCommit'], **proof, 'decodedMp3': decoded,
            'publicPromotionApproved': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    inspect = commands.add_parser('verify')
    inspect.add_argument('--bundle', type=Path, required=True)
    inspect.add_argument('--decode-audio', action='store_true')
    inspect.add_argument('--expected-manifest-sha256', help='Pin the sender-provided handoff digest.')
    make = commands.add_parser('build')
    make.add_argument('--input', type=Path, required=True)
    make.add_argument('--output', type=Path, required=True)
    make.add_argument('--reuse-docs', type=Path, required=True)
    make.add_argument('--code-commit', required=True)
    make.add_argument('--bundle-id', required=True)
    make.add_argument('--french-voice', choices=['fr-FR-DeniseNeural', 'fr-FR-HenriNeural'])
    args = parser.parse_args()
    result = (verify(args.bundle, decode_audio=args.decode_audio,
                     expected_manifest_sha256=args.expected_manifest_sha256) if args.command == 'verify'
              else build(args.input, args.output, args.reuse_docs, code_commit=args.code_commit,
                         bundle_id=args.bundle_id, french_voice=args.french_voice))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
