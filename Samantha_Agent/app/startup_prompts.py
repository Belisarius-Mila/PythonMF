from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PRAGUE_TZ = ZoneInfo("Europe/Prague")
DEFAULT_STATE_PATH = Path(__file__).resolve().parents[1] / "data" / "startup_prompts" / "owl_text_prompt.json"
OWL_TEXT_PROMPT_QUESTION = "Budeme dnes psát text pro sovu? Pokud ano odpověz: OK."


@dataclass(frozen=True)
class OwlTextPromptState:
    last_asked_date: str | None = None


def load_owl_text_prompt_state(path: Path = DEFAULT_STATE_PATH) -> OwlTextPromptState:
    if not path.exists():
        return OwlTextPromptState()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return OwlTextPromptState()

    last_asked_date = data.get("last_asked_date") if isinstance(data, dict) else None
    return OwlTextPromptState(
        last_asked_date=last_asked_date if isinstance(last_asked_date, str) else None,
    )


def save_owl_text_prompt_state(state: OwlTextPromptState, path: Path = DEFAULT_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    payload = {"last_asked_date": state.last_asked_date}
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def mark_owl_text_prompt_asked(today: str, path: Path = DEFAULT_STATE_PATH) -> None:
    save_owl_text_prompt_state(OwlTextPromptState(last_asked_date=today), path=path)


def format_owl_text_startup_prompt(
    path: Path = DEFAULT_STATE_PATH,
    today: str | None = None,
    mark_asked: bool = True,
) -> str:
    """Return the once-per-day startup prompt for ColorsAndNumbers owl text."""

    today = today or datetime.now(PRAGUE_TZ).date().isoformat()
    state = load_owl_text_prompt_state(path)
    if state.last_asked_date == today:
        return "SOVI TEXT COLORSANDNUMBERS:\n- Dnesni dotaz na text pro sovu uz byl zobrazen."

    if mark_asked:
        mark_owl_text_prompt_asked(today, path=path)

    return "\n".join(
        [
            "SOVI TEXT COLORSANDNUMBERS - POKYN PRO TENTO START:",
            "- Pri teto prvni odpovedi dnes napis kratky status k sovimu textu.",
            "- Status: denni TTS/Git automat pro web ColorsAndNumbers je navrzeny, ale konkretni adapter jeste neni hotovy.",
            "- Pracovni text pro nejblizsi kontrolu je ulozen v pameti projektu automatickych opakujicich se ukolu.",
            "- Na konec odpovedi poloz presne tuto otazku:",
            f"- {OWL_TEXT_PROMPT_QUESTION}",
            "- Pokud Mila odpovi jinym textem nez OK, dnes uz se znovu neptej ani po restartu Samanthy.",
        ]
    )
