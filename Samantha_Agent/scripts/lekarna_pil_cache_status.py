from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.lekarna.sukl_pil_archive import (
    DEFAULT_PIL_DOC_CACHE_DIR,
    download_sukl_pil_document,
    find_latest_pil_archive,
    resolve_sukl_pil_document,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Zkontroluje lokalni cache SUKL PIL archivu pro Lekarnu.")
    parser.add_argument("--pil", default="", help="Volitelny PIL soubor k overeni, napr. PI229834.pdf.")
    parser.add_argument("--download", action="store_true", help="Kdyz PIL chybi, zkusit stahnout konkretni dokument online.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive = find_latest_pil_archive()
    if args.pil:
        document = resolve_sukl_pil_document(args.pil)
        if document:
            print(f"PIL soubor OK: {document.member_name}")
            print(f"Zdroj: {document.source_kind} ({document.source_path})")
            print(f"Extrakce: {document.extraction_method}")
            print(f"Znaku textu: {len(document.text)}")
            return 0
        if args.download:
            downloaded = download_sukl_pil_document(args.pil)
            if downloaded:
                print(f"PIL dokument stazen do cache: {downloaded}")
                document = resolve_sukl_pil_document(args.pil)
                if document:
                    print(f"Extrakce: {document.extraction_method}")
                    print(f"Znaku textu: {len(document.text)}")
                    return 0
            print(f"PIL soubor se nepodarilo stahnout nebo precist: {args.pil}")
            print(f"Cache jednotlivych dokumentu: {DEFAULT_PIL_DOC_CACHE_DIR}")
            return 2

    if not archive:
        print("PIL archiv v cache nenalezen.")
        print("Ocekavana slozka: data/lekarna/sukl_cache")
        print("Ocekavany soubor: ZIP s PIL v nazvu, napr. PIL20260701.zip")
        if args.pil:
            print(f"Jednotlivy PIL dokument take nenalezen: {args.pil}")
            print("Pro online pokus pouzij --download.")
        return 1

    print(f"PIL archiv v cache: {archive}")
    if args.pil:
        document = resolve_sukl_pil_document(args.pil, pil_archive_path=archive)
        if not document:
            print(f"PIL soubor nenalezen nebo nejde precist: {args.pil}")
            return 2
        print(f"PIL soubor OK: {document.member_name}")
        print(f"Extrakce: {document.extraction_method}")
        print(f"Znaku textu: {len(document.text)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
