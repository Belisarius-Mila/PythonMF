from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.lekarna.search_tags import apply_search_tags_to_csv


def main() -> int:
    result = apply_search_tags_to_csv()
    print(f"csv={result.csv_path}")
    print(f"backup={result.backup_path}")
    print(f"rows={result.total_rows}")
    print(f"updated={result.updated_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
