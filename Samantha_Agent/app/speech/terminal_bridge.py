from __future__ import annotations

import re
import subprocess
from typing import Any, Callable

from app.speech.voice_inbox import VoiceCommand, normalize_for_triage, voice_command_to_dict


MAX_TERMINAL_PROMPT_CHARS = 1200

TERMINAL_MANUAL_TERMS = (
    "smaz",
    "smaž",
    "vymaz",
    "vymaž",
    "uprav",
    "oprav",
    "zmen",
    "změň",
    "prepis",
    "přepiš",
    "vytvor soubor",
    "vytvoř soubor",
    "uloz",
    "ulož",
    "commit",
    "push",
    "odesli",
    "odešli",
    "posli",
    "pošli",
    "zaplat",
    "platbu",
    "token",
    "heslo",
    "api key",
)


def squash_terminal_text(text: str) -> str:
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", str(text or ""))
    return " ".join(cleaned.split())


def assess_terminal_bridge(command: VoiceCommand) -> dict[str, Any]:
    text = squash_terminal_text(command.text)
    folded = normalize_for_triage(text)
    if not command.ok or not text:
        return {
            "ok": False,
            "status": "empty_command",
            "reason": "Hlasový pokyn nemá použitelný text.",
        }
    if command.triage.requires_confirmation or command.triage.risk in {"blocked", "needs_confirmation"}:
        return {
            "ok": False,
            "status": "manual_required",
            "reason": "Triage hlasového pokynu vyžaduje ruční potvrzení.",
            "risk": command.triage.risk,
        }
    if any(term in folded for term in TERMINAL_MANUAL_TERMS):
        return {
            "ok": False,
            "status": "manual_required",
            "reason": "Pokyn obsahuje změnovou nebo citlivou formulaci, proto se nevkládá automaticky do terminálu.",
            "risk": command.triage.risk,
        }
    if len(text) > MAX_TERMINAL_PROMPT_CHARS:
        return {
            "ok": False,
            "status": "manual_required",
            "reason": "Pokyn je příliš dlouhý pro bezpečné automatické vložení do terminálu.",
            "risk": command.triage.risk,
        }
    return {
        "ok": True,
        "status": "allowed",
        "reason": "Pokyn je vhodný pro bezpečné vložení do Codex terminálu.",
        "risk": command.triage.risk,
        "text": text,
    }


def build_codex_terminal_prompt(command: VoiceCommand) -> str:
    text = squash_terminal_text(command.text)
    return (
        "Hlasový pokyn od Míly z Cockpitu: "
        f"{text} "
        "Zpracuj ho jako běžný uživatelský pokyn; pokud zjistíš riziko změny dat, "
        "odesílání, mazání, commitu, platby nebo tajemství, vyžádej si ruční potvrzení."
    )


def terminal_applescript() -> str:
    return r'''
on run argv
  set promptText to item 1 of argv
  set shouldSubmit to item 2 of argv
  tell application "Terminal"
    set foundTarget to false
    repeat with terminalWindow in windows
      repeat with terminalTab in tabs of terminalWindow
        set tabProcesses to processes of terminalTab
        if tabProcesses contains "codex" then
          set selected tab of terminalWindow to terminalTab
          set index of terminalWindow to 1
          set foundTarget to true
          exit repeat
        end if
      end repeat
      if foundTarget then exit repeat
    end repeat
    if not foundTarget then error "Nenalezen Terminal tab s procesem codex."
    activate
  end tell
  delay 0.2
  tell application "System Events"
    set the clipboard to promptText
    keystroke "v" using command down
    if shouldSubmit is "1" then key code 36
  end tell
  return "delivered"
end run
'''.strip()


def deliver_prompt_to_terminal(
    prompt: str,
    *,
    submit: bool = True,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    script: str | None = None,
    timeout: float = 8.0,
) -> dict[str, Any]:
    safe_prompt = squash_terminal_text(prompt)
    completed = runner(
        ["/usr/bin/osascript", "-e", script or terminal_applescript(), safe_prompt, "1" if submit else "0"],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "ok": False,
            "status": "terminal_delivery_failed",
            "message": (completed.stderr or completed.stdout or "Terminálový bridge selhal.").strip(),
            "returncode": completed.returncode,
        }
    return {
        "ok": True,
        "status": "delivered",
        "message": "Pokyn byl vložen do Codex terminálu.",
        "submitted": submit,
    }


def deliver_voice_command_to_terminal(
    command: VoiceCommand,
    *,
    submit: bool = True,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    decision = assess_terminal_bridge(command)
    if not decision.get("ok"):
        return {
            **decision,
            "command": voice_command_to_dict(command),
        }
    prompt = build_codex_terminal_prompt(command)
    delivery = deliver_prompt_to_terminal(prompt, submit=submit, runner=runner)
    return {
        **delivery,
        "prompt": prompt,
        "decision": decision,
        "command": voice_command_to_dict(command),
    }
