"""Validate the saved batch and build a local review; never call image generation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
MAX_BYTES = 300_000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    requests = json.loads((ROOT / 'requests.json').read_text())
    with (PROJECT / 'VocabularyEN/mmtx_dialogue_supplement.csv').open(newline='') as handle:
        words = {row['EN']: row for row in csv.DictReader(handle)}
    assert len(requests) == 49
    assert len({r['output_file'] for r in requests}) == 49
    for request in requests:
        path = ROOT / request['output_file']
        assert path.parent == ROOT and path.suffix == '.webp'
        assert request['word'] in words
        with Image.open(path) as im:
            im.verify()
        receipt = json.loads(path.with_suffix('.receipt.json').read_text())
        assert receipt['word'] == request['word'] and receipt['status'] == 'generated'
        if path.stat().st_size >= MAX_BYTES:
            print('Compress:', path.name, path.stat().st_size)
            if args.apply:
                original = ROOT / 'originals' / path.name
                original.parent.mkdir(exist_ok=True)
                if not original.exists():
                    shutil.copy2(path, original)
                source = Path(receipt['source'])
                assert source.is_file(), source
                subprocess.run(['/usr/local/bin/cwebp', '-quiet', '-size', '280000',
                                str(source), '-o', str(path)], check=True)
                assert path.stat().st_size < MAX_BYTES
    if not args.apply:
        print('Dry run: 49 decodable images; no API calls and no files written.')
        return
    results, cards = [], []
    for request in requests:
        path = ROOT / request['output_file']
        row = words[request['word']]
        with Image.open(path) as im:
            im.load()
            dimensions = list(im.size)
        assert dimensions[0] == dimensions[1]
        size = path.stat().st_size
        assert size < MAX_BYTES
        results.append(dict(word=request['word'], output_file=path.name, status='generated',
                            output_bytes=size, dimensions=dimensions,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            czech=row['CZ'], sentence=row['Sentence'], sentence_cz=row['SentenceT']))
        e = html.escape
        cards.append(f'<article><a href="{e(path.name)}"><img src="{e(path.name)}" alt="{e(row["CZ"])}"></a>'
                     f'<h2>{request["index"]}. {e(row["EN"])}</h2><p class="meaning">{e(row["CZ"])}</p>'
                     f'<p>{e(row["Sentence"])}</p><p class="translation">{e(row["SentenceT"])}</p></article>')
    report = dict(created_at=datetime.now(ZoneInfo('Europe/Prague')).isoformat(),
                  engine='built-in image_gen', requested=49, generated=49, max_size_bytes=MAX_BYTES,
                  largest_image_bytes=max(r['output_bytes'] for r in results),
                  review_status='awaiting_user_review', production_applied=False, results=results)
    (ROOT / 'generation_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    page = '''<!doctype html><html lang="cs"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>49 nových obrázků — angličtina</title>
<style>body{font:17px/1.45 system-ui,sans-serif;background:#f5f2eb;color:#26392e;margin:0;padding:28px}
header{max-width:900px;margin:0 auto 28px}h1{font-size:30px;margin:0 0 10px}header p{margin:7px 0}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,270px),1fr));gap:22px;max-width:1450px;margin:auto}
article{background:white;border-radius:14px;overflow:hidden;padding-bottom:16px;box-shadow:0 2px 9px #26392e12}
img{display:block;width:100%;aspect-ratio:1;object-fit:contain}h2,p{margin:10px 18px}h2{font-size:23px}
.meaning{font-weight:650}.translation{color:#56645b}a:focus-visible{outline:4px solid #32764c}
</style><header><h1>49 nových obrázků pro angličtinu</h1>
<p>Každý obrázek otevřeš kliknutím ve větším zobrazení. Pod ním je slovíčko, český význam a příkladová věta.</p>
<p>Členy, zájmena a abstraktní slova posuzuj společně s větou. Galerie čeká na tvoji kontrolu.</p>
</header><main>''' + '\n'.join(cards) + '</main></html>\n'
    (ROOT / 'review.html').write_text(page, encoding='utf-8')
    # Contact sheets are inspection artifacts only; the individual images are not edited here.
    for offset in range(0, len(requests), 16):
        group = requests[offset:offset + 16]
        sheet = Image.new('RGB', (1200, 4 * 340), '#f5f2eb')
        draw = ImageDraw.Draw(sheet)
        for i, request in enumerate(group):
            with Image.open(ROOT / request['output_file']) as im:
                preview = im.convert('RGB')
                preview.thumbnail((290, 290))
                x, y = (i % 4) * 300 + 5, (i // 4) * 340 + 5
                sheet.paste(preview, (x, y))
            draw.text((x + 4, y + 296), f'{request["index"]}. {request["word"]}', fill='#14271c', font_size=22)
        sheet.save(ROOT / f'contact_sheet_{offset // 16 + 1}.jpg', quality=90)
    print(json.dumps({key: report[key] for key in ('requested', 'generated', 'largest_image_bytes')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
