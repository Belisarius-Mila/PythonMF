from __future__ import annotations

import re
import subprocess
from typing import Any, Callable

from app.speech.voice_inbox import VoiceCommand, normalize_for_triage, voice_command_to_dict


MAX_TERMINAL_PROMPT_CHARS = 1200
PS_COMMAND = ["ps", "-axo", "pid=,ppid=,tty=,comm=,args="]

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


def normalize_tty(value: str) -> str:
    text = str(value or "").strip()
    if text.startswith("/dev/"):
        return text.removeprefix("/dev/")
    return text


def discover_codex_ttys(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[str]:
    try:
        completed = runner(
            PS_COMMAND,
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []

    tty_by_pid: dict[int, str] = {}
    parent_by_pid: dict[int, int] = {}
    codex_pids: set[int] = set()
    for line in completed.stdout.splitlines():
        parts = line.strip().split(None, 4)
        if len(parts) < 5:
            continue
        pid_text, ppid_text, tty, comm, args = parts
        try:
            pid = int(pid_text)
            ppid = int(ppid_text)
        except ValueError:
            continue
        tty_by_pid[pid] = normalize_tty(tty)
        parent_by_pid[pid] = ppid
        folded = f"{comm} {args}".casefold()
        if "codex" in folded and "app-server" not in folded:
            codex_pids.add(pid)

    result: list[str] = []
    seen: set[str] = set()
    for pid in sorted(codex_pids):
        current = pid
        for _ in range(20):
            tty = tty_by_pid.get(current, "")
            if tty and tty != "??" and tty not in seen:
                seen.add(tty)
                result.append(tty)
                break
            parent = parent_by_pid.get(current)
            if parent is None or parent == current:
                break
            current = parent
    return result


def terminal_applescript() -> str:
    return r'''
on run argv
  set promptText to item 1 of argv
  set shouldSubmit to item 2 of argv
  set targetTtys to {}
  if (count of argv) >= 3 then
    set AppleScript's text item delimiters to ","
    set targetTtys to text items of (item 3 of argv)
    set AppleScript's text item delimiters to ""
  end if
  tell application "Terminal"
    set foundTarget to false
    repeat with terminalWindow in windows
      repeat with terminalTab in tabs of terminalWindow
        set tabProcesses to processes of terminalTab
        set tabTty to tty of terminalTab
        if tabTty starts with "/dev/" then set tabTty to text 6 thru -1 of tabTty
        if (tabProcesses contains "codex") or (targetTtys contains tabTty) then
          set selected tab of terminalWindow to terminalTab
          set index of terminalWindow to 1
          set foundTarget to true
          exit repeat
        end if
      end repeat
      if foundTarget then exit repeat
    end repeat
    if not foundTarget then error "Nenalezen Terminal tab s procesem codex ani s odpovídajícím TTY."
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
    ps_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    script: str | None = None,
    timeout: float = 8.0,
) -> dict[str, Any]:
    safe_prompt = squash_terminal_text(prompt)
    codex_ttys = discover_codex_ttys(runner=ps_runner)
    completed = runner(
        [
            "/usr/bin/osascript",
            "-e",
            script or terminal_applescript(),
            safe_prompt,
            "1" if submit else "0",
            ",".join(codex_ttys),
        ],
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
            "target_ttys": codex_ttys,
        }
    return {
        "ok": True,
        "status": "delivered",
        "message": "Pokyn byl vložen do Codex terminálu.",
        "submitted": submit,
        "target_ttys": codex_ttys,
    }


def deliver_voice_command_to_terminal(
    command: VoiceCommand,
    *,
    submit: bool = True,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ps_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    decision = assess_terminal_bridge(command)
    if not decision.get("ok"):
        return {
            **decision,
            "command": voice_command_to_dict(command),
        }
    prompt = build_codex_terminal_prompt(command)
    delivery = deliver_prompt_to_terminal(prompt, submit=submit, runner=runner, ps_runner=ps_runner)
    return {
        **delivery,
        "prompt": prompt,
        "decision": decision,
        "command": voice_command_to_dict(command),
    }
