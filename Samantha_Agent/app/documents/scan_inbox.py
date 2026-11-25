"""Confirmed local scan intake, independent from OCR and final vault classification."""
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import base64
import hashlib
import json
import re
import warnings
from app.documents.vault import DEFAULT_DOCUMENTS_DIR, safe_text
from app.file_persistence import atomic_create_bytes, atomic_create_text, exclusive_file_lock

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
MAX_SCAN_BYTES = 24 * 1024 * 1024
MAX_PAGES = 30
SCAN_ID = re.compile('[a-f0-9]{32}')

def scan_directory(scan_id, vault_dir):
    if not isinstance(scan_id, str) or not SCAN_ID.fullmatch(scan_id):
        raise ValueError('Neplatný identifikátor skenu.')
    path = Path(vault_dir) / 'scans' / scan_id
    if any((p.is_symlink() for p in (path, *path.parents))):
        raise ValueError('Úložiště skenů obsahuje nepovolený odkaz.')
    return path

def pdf_page_count(raw):
    import pdfplumber
    if not raw.startswith(b'%PDF-') or len(raw) > MAX_SCAN_BYTES:
        raise ValueError('Vyber PDF do 24 MB.')
    try:
        with pdfplumber.open(BytesIO(raw)) as document:
            count = len(document.pages)
    except Exception as exc:
        raise ValueError('PDF se nepodařilo přečíst. Vyber nešifrovaný dokument.') from exc
    if not 1 <= count <= MAX_PAGES:
        raise ValueError('Dokument musí obsahovat 1 až 30 stran.')
    return count

def images_pdf(pages):
    from PIL import Image, ImageOps
    if not isinstance(pages, list) or not 1 <= len(pages) <= MAX_PAGES:
        raise ValueError('Přidej 1 až 30 stran.')
    images = []
    total_bytes = total_pixels = 0
    try:
        for page in pages:
            if not isinstance(page, str):
                raise ValueError('Neplatná stránka.')
            raw = base64.b64decode(page, validate=True)
            total_bytes += len(raw)
            if total_bytes > MAX_SCAN_BYTES:
                raise ValueError('Stránky jsou příliš velké.')
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(BytesIO(raw)) as source:
                    if source.format not in {'JPEG', 'PNG', 'WEBP'} or source.width * source.height > 16000000:
                        raise ValueError('Použij fotografii JPG, PNG nebo WEBP do 16 megapixelů.')
                    total_pixels += source.width * source.height
                    if total_pixels > 60000000:
                        raise ValueError('Zmenši fotografie před uložením.')
                    images.append(ImageOps.exif_transpose(source).convert('RGB'))
        output = BytesIO()
        images[0].save(output, 'PDF', save_all=True, append_images=images[1:], resolution=200, creationDate=None, modDate=None)
        raw = output.getvalue()
        if len(raw) > MAX_SCAN_BYTES:
            raise ValueError('Výsledné PDF je větší než 24 MB.')
        return raw
    except (OSError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise ValueError('Některá fotografie není čitelná.') from exc
    finally:
        for image in images:
            image.close()

def save_scan(*, scan_id, title, raw, confirmed, vault_dir=DEFAULT_DOCUMENTS_DIR):
    if confirmed is not True:
        raise ValueError('Uložení skenu vyžaduje potvrzení.')
    name = safe_text(str(title or '')).strip()
    if not name or len(name) > 160:
        raise ValueError('Zadej název dokumentu do 160 znaků.')
    count = pdf_page_count(raw)
    directory = scan_directory(scan_id, vault_dir)
    directory.parent.mkdir(parents=True, exist_ok=True, mode=448)
    with exclusive_file_lock(directory.parent / (scan_id + '-save')):
        directory.mkdir(mode=448, exist_ok=True)
        pdf = directory / 'document.pdf'
        manifest = directory / 'scan.json'
        expected = digest(raw)
        if manifest.exists():
            record = json.loads(manifest.read_text())
            if record['sha256'] != expected or record['title'] != name:
                raise ValueError('Tento pokus už uložil jiný dokument. Otevři nový sken.')
            resolve_scan(scan_id, vault_dir=vault_dir)
            return public_scan(record)
        if pdf.exists():
            if pdf.is_symlink() or digest(pdf.read_bytes()) != expected:
                raise ValueError('Nedokončený přenos obsahuje jiná data.')
        else:
            atomic_create_bytes(pdf, raw)
        record = {'scan_id': scan_id, 'title': name, 'pages': count, 'sha256': expected, 'created_at': datetime.now(timezone.utc).isoformat()}
        atomic_create_text(manifest, canonical_json(record))
        return public_scan(record)

def public_scan(record):
    return {k: record[k] for k in ('scan_id', 'title', 'pages', 'created_at')}

def resolve_scan(scan_id, *, vault_dir=DEFAULT_DOCUMENTS_DIR):
    directory = scan_directory(scan_id, vault_dir)
    manifest = directory / 'scan.json'
    pdf = directory / 'document.pdf'
    if manifest.is_symlink() or pdf.is_symlink() or (not manifest.is_file()) or (not pdf.is_file()):
        raise ValueError('Uložený sken nebyl nalezen.')
    record = json.loads(manifest.read_text())
    if record['scan_id'] != scan_id or digest(pdf.read_bytes()) != record['sha256']:
        raise ValueError('Uložený sken neodpovídá záznamu.')
    return pdf

def list_scans(*, vault_dir=DEFAULT_DOCUMENTS_DIR):
    root = Path(vault_dir) / 'scans'
    if root.is_symlink():
        raise ValueError('Neplatné úložiště skenů.')
    rows = []
    for path in root.glob('*/scan.json'):
        if path.is_symlink():
            continue
        try:
            record = json.loads(path.read_text())
            if path.parent == scan_directory(record['scan_id'], vault_dir):
                rows.append(public_scan(record))
        except (ValueError, KeyError, OSError):
            continue
    return sorted(rows, key=lambda r: r['created_at'], reverse=True)[:100]

def save_scan_action(payload, *, vault_dir=DEFAULT_DOCUMENTS_DIR):
    try:
        if payload.get('confirmed') is not True:
            raise ValueError('Potvrď uložení dokumentu.')
        raw = images_pdf(payload.get('pages'))
        return {'ok': True, 'scan': save_scan(scan_id=payload.get('scan_id'), title=payload.get('title'), raw=raw, confirmed=True, vault_dir=vault_dir)}
    except (ValueError, OSError, TypeError) as exc:
        return {'ok': False, 'message': str(exc)}


def prepare_scan_for_scandocu(scan_id, *, vault_dir=DEFAULT_DOCUMENTS_DIR):
    from app.documents.scandocu import prepare_scandocu_candidate
    source = resolve_scan(scan_id, vault_dir=vault_dir)
    candidate = prepare_scandocu_candidate(source, vault_dir=vault_dir)
    result = candidate.to_api()
    result["title"] = json.loads((source.parent / "scan.json").read_text())["title"]
    return result
