from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_EXPORT_PATH = Path(__file__).resolve().parents[1] / "data" / "conversations.json"


def load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Soubor neexistuje: {path}")

    if not path.is_file():
        raise ValueError(f"Cesta neni soubor: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def count_conversations(data: Any) -> int:
    if isinstance(data, list):
        return len(data)

    if isinstance(data, dict) and isinstance(data.get("conversations"), list):
        return len(data["conversations"])

    raise ValueError(
        "Nepodporovany format exportu. Ocekavam list konverzaci nebo objekt s klicem 'conversations'."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bezpecne nacte ChatGPT export conversations.json a vypise pocet konverzaci. "
            "Skript zatim nic nezapisuje ani neprepisuje."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=DEFAULT_EXPORT_PATH,
        help=f"Cesta k conversations.json. Vychozi: {DEFAULT_EXPORT_PATH}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export_path = args.path.expanduser().resolve()

    data = load_json(export_path)
    conversation_count = count_conversations(data)

    print(f"Nacteno: {export_path}")
    print(f"Pocet konverzaci: {conversation_count}")
    print("Hotovo. Skript zatim nic nezapisuje ani neprepisuje.")


if __name__ == "__main__":
    main()
