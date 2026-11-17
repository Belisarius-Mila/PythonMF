"""Reuse verified Czech MP3s only. No network, credentials or generation."""
from __future__ import annotations

from pathlib import Path
import re
import unicodedata

from vocabulary_fr_catalog import encoded, load, safe_file, sha

VOICE = 'cs-CZ-VlastaNeural'
RATE = '-10%'


def text(value, kind):
    if kind not in {'words', 'sentences'} or not isinstance(value, str) or not value.strip():
        raise ValueError('Invalid spoken text.')
    value = unicodedata.normalize('NFC', ' '.join(value.split()))
    if kind == 'words':
        value = value.replace('(', '').replace(')', '')
        value = re.sub(r'\s*[,;/]\s*', '. ', value)
        value = re.sub(r'\s+([?.!])', r'\1', value)
        value = re.sub(r'\.{2,}', '.', value)
    return value.strip()


def reuse_index(docs):
    """Validate identity, voice, rate and bytes before considering IT audio."""
    items = {i['uid']: i for i in load(safe_file(docs, 'data/vocabulary-it-v2.json'))['items']}
    result = {}
    for kind, filename in [('words', 'vocabulary-it-audio.json'),
                           ('sentences', 'vocabulary-it-sentence-audio.json')]:
        manifest = load(safe_file(docs, 'data/' + filename))
        if (manifest.get('schemaVersion') != 1 or manifest.get('language') != 'it'
                or manifest.get('kind') != kind or manifest.get('voices', {}).get('cz') != VOICE
                or manifest.get('rate') != RATE):
            raise ValueError('Incompatible Czech reuse manifest.')
        for uid, record in manifest['items'].items():
            item = items.get(uid)
            if (not item or record.get('uid') != uid or record.get('sourceIt') != item['it']
                    or record.get('sourceCz') != item['cz']):
                raise ValueError('Stale reuse source identity.')
            if kind == 'sentences' and (record.get('sourceSentenceIt') != item['sentenceIt']
                                       or record.get('sourceSentenceCz') != item['sentenceCz']):
                raise ValueError('Stale reuse sentence identity.')
            spoken = text(item['cz' if kind == 'words' else 'sentenceCz'], kind)
            relative = record.get('cz')
            if record.get('spokenCz') != spoken or not isinstance(relative, str):
                raise ValueError('Inexact Czech speech identity.')
            prefix = 'assets/vocabulary-it-' + ('audio/' if kind == 'words' else 'sentences/')
            if not relative.startswith(prefix):
                raise ValueError('Unexpected reuse asset namespace.')
            expected = manifest.get('assetSha256', {}).get(relative)
            if not isinstance(expected, str) or len(expected) != 64:
                raise ValueError('Reuse asset has no byte proof.')
            # Hash selected assets when copied, rather than re-read all IT MP3s.
            result.setdefault((kind, spoken), (Path(docs), relative, expected))
    return result


def prepare(items, index, *, french_voice=None):
    if french_voice not in {None, 'fr-FR-DeniseNeural', 'fr-FR-HenriNeural'}:
        raise ValueError('Unapproved French voice profile.')
    manifests, assets, provenance, cached = {}, {}, {}, {}
    for kind in ('words', 'sentences'):
        records, hashes = {}, {}
        for item in items:
            uid = item['uid']
            record = {'uid': uid, 'sourceFr': item['fr'], 'sourceCz': item['cz']}
            if kind == 'sentences':
                record.update(sourceSentenceFr=item['sentenceFr'], sourceSentenceCz=item['sentenceCz'])
            for channel, field in [('fr', 'fr'), ('cz', 'cz')]:
                spoken = text(item[field if kind == 'words' else 'sentence' + field.title()], kind)
                record['spoken' + field.title()] = spoken
                record[channel] = None
                source = index.get((kind, spoken)) if channel == 'cz' else None
                if source:
                    root, relative, expected = source
                    if source not in cached:
                        data = safe_file(root, relative).read_bytes()
                        if sha(data) != expected:
                            raise ValueError('Reuse MP3 changed since its manifest.')
                        cached[source] = data
                    namespace = 'audio' if kind == 'words' else 'sentences'
                    target = f'assets/vocabulary-fr-{namespace}/cs-cz-vlasta-neural/{expected}.mp3'
                    assets[target] = cached[source]
                    hashes[target] = expected
                    provenance[target] = {'kind': kind, 'voice': VOICE, 'rate': RATE,
                                          'sourceProject': 'VocabularyIT', 'sourceAssetSha256': expected}
                    record[channel] = target
            records[uid] = record
        available = sum(r[c] is not None for r in records.values() for c in ('fr', 'cz'))
        status = 'not-generated' if not available else 'partial' if available < len(items) * 2 else 'complete'
        manifests[kind] = {'schemaVersion': 1, 'language': 'fr', 'kind': kind, 'status': status,
                           'provider': 'verified-existing-czech-mp3', 'voices': {'fr': french_voice, 'cz': VOICE},
                           'rate': RATE, 'items': records, 'sourceDigest': sha(encoded(records)),
                           'assetSha256': hashes}
    return manifests, assets, provenance
