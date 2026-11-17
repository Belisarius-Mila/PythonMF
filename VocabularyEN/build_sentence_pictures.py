"""Export reviewed sentence-to-meaning links; no inference or media generation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_name('vocabulary_en_sentence_pictures.json')
DATA = ROOT / 'docs/data/vocabulary-en.json'
OUTPUT = ROOT / 'docs/data/vocabulary-en-sentence-pictures.json'


def build(source: dict, data: dict, *, asset_root: Path | None = None) -> dict:
    if (not isinstance(source, dict) or source.get('schemaVersion') != 1 or source.get('language') != 'en'
            or source.get('kind') != 'sentence-pictures' or source.get('maxPictures') != 5
            or not isinstance(source.get('entries'), dict)):
        raise ValueError('Neplatný podklad obrazových vět.')
    if not isinstance(data, dict) or not isinstance(data.get('items'), list):
        raise ValueError('Chybí slovníkový export.')
    items = {item['uid']: item for item in data['items'] if item.get('active', True)}
    entries = {}
    for uid, record in source['entries'].items():
        target = items.get(uid)
        if not isinstance(record, dict) or not target or record.get('reviewed') is not True:
            raise ValueError('Neznámá nebo neověřená věta: ' + uid)
        identity = {key: target[field] for key, field in (
            ('sourceEn', 'en'), ('sourceCz', 'cz'),
            ('sourceSentenceEn', 'sentenceEn'), ('sourceSentenceCz', 'sentenceCz'))}
        if any(record.get(key) != value or not isinstance(value, str) or not value.strip()
               for key, value in identity.items()):
            raise ValueError('Změněné znění nebo význam věty: ' + uid)
        concepts = record.get('concepts')
        if not isinstance(concepts, list) or not 1 <= len(concepts) <= 5:
            raise ValueError('Věta musí mít1 až5 obrazových pojmů: ' + uid)
        seen, pictures, result, last_end = set(), set(), [], -1
        for ref in concepts:
            if not isinstance(ref, dict):
                raise ValueError('Neplatná obrazová vazba: ' + uid)
            concept = items.get(ref.get('uid'))
            text, occurrence = ref.get('text'), ref.get('occurrence')
            if (not concept or concept['uid'] in seen or ref.get('sourceEn') != concept['en']
                    or ref.get('sourceCz') != concept['cz'] or not isinstance(text, str) or not text.strip()
                    or type(occurrence) is not int or occurrence < 1):
                raise ValueError('Neplatný nebo změněný význam pojmu: ' + uid)
            matches = list(re.finditer(r"(?<![\w’'])" + re.escape(text) + r"(?![\w’'])", target['sentenceEn']))
            if occurrence > len(matches):
                raise ValueError('Výraz není v aktuální větě: ' + uid)
            match = matches[occurrence - 1]
            if match.start() < last_end:
                raise ValueError('Pojmy nejsou v pořadí věty nebo se překrývají: ' + uid)
            last_end = match.end()
            image, thumbnail = concept.get('image'), concept.get('thumbnail')
            if not image or not thumbnail:
                raise ValueError('Pojem nemá úplnou obrazovou kartu: ' + uid)
            picture_identity = image
            if asset_root is not None:
                for relative in (image, thumbnail):
                    path = asset_root / relative
                    if (not relative.startswith('assets/vocabulary-en') or '..' in Path(relative).parts
                            or not path.resolve().is_relative_to(asset_root.resolve()) or path.is_symlink()
                            or not path.is_file() or path.name not in {p.name for p in path.parent.iterdir()}):
                        raise ValueError('Obraz není přesný místní asset: ' + str(relative))
                picture_identity = hashlib.sha256((asset_root / image).read_bytes()).hexdigest()
            if picture_identity in pictures:
                raise ValueError('Stejný obrázek se nemá ve větě opakovat: ' + uid)
            seen.add(concept['uid']); pictures.add(picture_identity)
            # JavaScript string offsets count UTF-16 units, not Python code points.
            start = len(target['sentenceEn'][:match.start()].encode('utf-16-le')) // 2
            end = start + len(text.encode('utf-16-le')) // 2
            result.append({**ref, 'start': start, 'end': end})
        entries[uid] = {**identity, 'reviewed': True, 'concepts': result}
    return {'schemaVersion': 1, 'language': 'en', 'kind': 'sentence-pictures',
            'maxPictures': 5, 'batch': source.get('batch'), 'entries': entries}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify the existing export without writes.')
    args = parser.parse_args()
    result = build(json.loads(SOURCE.read_text()), json.loads(DATA.read_text()), asset_root=ROOT / 'docs')
    raw = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if OUTPUT.read_text() != raw:
            raise ValueError('Obrazová metadata neodpovídají aktuálním zdrojům.')
    else:
        OUTPUT.write_text(raw)
    print(f"Sentence pictures: {len(result['entries'])} reviewed sentences, "
          f"{sum(len(r['concepts']) for r in result['entries'].values())} references.")


if __name__ == '__main__':
    main()
