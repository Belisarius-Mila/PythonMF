#!/usr/bin/env python3
"""Registered one-shot P2-A synthetic experiment; no server, real media or upload."""

from __future__ import annotations

import argparse
import html
import json
import os
import tempfile
import time
from pathlib import Path

from camino.film.media import binary, run
from camino.film.project import FilmError, load_project, validate, write_json
from camino.film.render import DiskMeter, directory_bytes, render
from camino.film.synthetic import create_fixture


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'data' / 'private' / 'camino' / 'p2a'


def experiment(root: Path) -> dict:
    started = time.monotonic()
    with DiskMeter(root) as meter:
        project_path = create_fixture(root)
        project = load_project(project_path)  # Prove disk reopen, not an in-memory-only project.
        preview = render(project_path, 'preview')
        final = render(project_path, 'final')
        if preview['project_fingerprint'] != final['project_fingerprint']:
            raise FilmError('Náhled a finále mají jiné zadání.')
        validate(project, root)
    receipt = {'scope': 'synthetic-p2a', 'status': 'machine_verified',
               'ffmpeg': run([binary('ffmpeg'), '-version']).stdout.decode().splitlines()[0],
               'timeline_ms': final['timeline_ms'], 'preview': preview, 'final': final,
               'total_seconds': round(time.monotonic() - started, 3),
               'peak_run_logical_bytes': meter.peak[0], 'peak_run_allocated_bytes': meter.peak[1],
               'peak_sampling_ms': 50, 'retained_bytes': directory_bytes(root)[0],
               'manual_acceptance': 'PENDING_MAC_AND_IPHONE'}
    write_json(root / 'experiment.json', receipt)
    sections = ''
    for title, item in [('Pracovní náhled · 720p', preview), ('Finální export · 1080p', final)]:
        url = html.escape(item['output'], quote=True)
        sections += f'<section><h2>{title}</h2><video controls playsinline preload="metadata" src="{url}"></video><p><a href="{url}" download>Stáhnout MP4</a></p></section>'
    page = '''<!doctype html><html lang="cs"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Camino · P2-A</title><style>body{max-width:1000px;margin:40px auto;padding:0 20px;background:#102b33;color:#f6f0df;font:18px/1.6 system-ui}h1,h2{line-height:1.2}video{width:100%;background:black;border-radius:10px}section{margin:35px 0}a{color:#f0d091}.note{border-left:3px solid #f0d091;padding:12px 18px}</style><h1>Camino · zkouška filmové dílny</h1><p class="note">Pouze syntetické obrazy a místní testovací hlas. Žádná skutečná data Camina. Toto je přehrávač výsledků, nikoli editor.</p>'''
    page += sections + '<p>Kontrola: česká diakritika, celý žlutý rám videí, správné otočení, komentář přes střihy a celá závěrečná věta „šťastnou cestu“.</p></html>'
    (root / 'review.html').write_text(page, encoding='utf-8')
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        print('P2-A: --execute vytvoří nový zachovaný syntetický běh, MP4 720p/1080p a měření v data/private/camino/p2a. Bez sítě, skutečných médií a mazání.')
        return 0
    os.umask(0o077)
    os.nice(5)  # This one-shot process and its media children yield to normal services.
    RUNS.mkdir(parents=True, exist_ok=True, mode=0o700)
    root = Path(tempfile.mkdtemp(prefix='run-', dir=RUNS))
    print(f'P2-A run: {root.relative_to(ROOT)}', flush=True)
    try:
        result = experiment(root)
    except (FilmError, OSError, ValueError) as exc:
        write_json(root / 'failure.json', {'status': 'failed', 'message': str(exc)})
        print(f'P2-A FAILED: {exc}', flush=True)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
