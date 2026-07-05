from __future__ import annotations

import getpass
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.lekarna.web_bundle import KEYCHAIN_SERVICE


def main() -> int:
    first = getpass.getpass("Heslo webove Lekarny pro ulozeni do macOS Keychain: ")
    second = getpass.getpass("Zopakovat heslo: ")
    if not first:
        print("Heslo nesmi byt prazdne.")
        return 2
    if first != second:
        print("Hesla se neshoduji.")
        return 2
    completed = subprocess.run(
        [
            "security",
            "add-generic-password",
            "-U",
            "-s",
            KEYCHAIN_SERVICE,
            "-a",
            getpass.getuser(),
            "-w",
            first,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        print((completed.stderr or completed.stdout or "Ulozeni do Keychain selhalo.").strip())
        return completed.returncode or 1
    print(f"Heslo je ulozene v macOS Keychain jako `{KEYCHAIN_SERVICE}`.")
    print("Heslo ani hash hesla nebyly ulozeny do projektu ani gitu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
