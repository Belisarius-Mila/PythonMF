from __future__ import annotations

import json
import re
import subprocess
import termios
import fcntl
import time
from pathlib import Path
from typing import Any, Callable

from app.speech.voice_inbox import VoiceCommand, normalize_for_triage, voice_command_to_dict


MAX_TERMINAL_PROMPT_CHARS = 1200
PS_COMMAND = ["ps", "-axo", "pid=,ppid=,tty=,stat=,etime=,comm=,args="]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRENT_CODEX_TTY_PATH = PROJECT_ROOT / "data/private/voice_inbox/current_codex_tty.json"
DEFAULT_STALE_CODEX_SECONDS = 36 * 60 * 60
DEFAULT_CODEX_SCREEN_SESSION = "samantha_codex"
SCREEN_CLEAR_INPUT = "\x15"
SCREEN_SUBMIT_INPUT = "\r"

TERMINAL_MANUAL_TERMS = (
    "smaz",
    "smaž",
    "vymaz",
    "vymaž",
    "commit",
    "push",
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
    if (
        command.triage.risk != "outbound_confirmation"
        and (command.triage.requires_confirmation or command.triage.risk in {"blocked", "needs_confirmation"})
    ):
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
        "odesílání, mazání, commitu, platby nebo tajemství, vyžádej si ruční potvrzení. "
        "U odchozího e-mailu nebo SMS smíš připravit návrh/draft, ale skutečné "
        "odeslání proveď až po samostatné přesné potvrzovací větě od Míly. "
        "Nejdřív bez čtení nahlas zapiš textový mezistav do Cockpitu přes "
        "`.venv/bin/python scripts/adam_voice_reply.py --processing-started`. "
        "Po dokončení napiš výsledek do chatu a zapiš stejný stručný výsledek do Cockpitu přes "
        "`.venv/bin/python scripts/adam_voice_reply.py --latest-command \"STRUČNÝ VÝSLEDEK\"`. "
        "Nespouštěj zároveň Mac TTS přes `scripts/speak_edge_open.py`, protože otevřený "
        "Cockpit audiokanál odpověď přehraje v prohlížeči; Mac TTS použij jen při výslovném "
        "požadavku nebo jako fallback, když Cockpit audio není k dispozici. "
        "Nečti nahlas tajemství, celé osobní údaje ani dlouhé citlivé texty. "
        "Pokud je aktivní TVBCP a pokyn souvisí s probíhajícím brainstormingem, udrž odpověď "
        "ve VoiceBridge stručnou, ale přes `scripts/tvbcp.py append --mila ... --adam ...` zapiš "
        "plné věcné znění podstatných návrhů a myšlenek obou stran. TVBCP není kopie chatu: "
        "vynech technické mezistavy, testy, příkazy a provozní hlášky. Neukládej tajemství, "
        "osobní údaje ani identifikující citlivý krizový příběh."
    )


def normalize_tty(value: str) -> str:
    text = str(value or "").strip()
    if text.startswith("/dev/"):
        text = text.removeprefix("/dev/")
    match = re.match(r"^(.*?)(\d+)$", text)
    if match:
        prefix, digits = match.groups()
        if len(digits) < 3:
            return f"{prefix}{digits.zfill(3)}"
    return text


def is_codex_cli_process(comm: str, args: str) -> bool:
    folded = f"{comm} {args}".casefold()
    if "app-server" in folded:
        return False
    tokens = [comm, *str(args or "").split()]
    return any(Path(token).name == "codex" for token in tokens if token)


def parse_ps_etime_seconds(value: str) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    days = 0
    if "-" in text:
        day_text, text = text.split("-", 1)
        try:
            days = int(day_text)
        except ValueError:
            days = 0
    parts = text.split(":")
    try:
        if len(parts) == 3:
            hours, minutes, seconds = [int(part) for part in parts]
        elif len(parts) == 2:
            hours = 0
            minutes, seconds = [int(part) for part in parts]
        elif len(parts) == 1:
            hours = 0
            minutes = 0
            seconds = int(parts[0])
        else:
            return 0
    except ValueError:
        return 0
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def looks_like_ps_etime(value: str) -> bool:
    return bool(re.fullmatch(r"(?:\d+-)?\d+(?::\d+){0,2}", str(value or "").strip()))


def looks_like_ps_stat(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z+<NsS]+", str(value or "").strip()))


def discover_codex_ttys(
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    stale_after_seconds: int = DEFAULT_STALE_CODEX_SECONDS,
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
    stat_by_pid: dict[int, str] = {}
    elapsed_by_pid: dict[int, int] = {}
    codex_pids: set[int] = set()
    for line in completed.stdout.splitlines():
        parts = line.strip().split(None, 6)
        if len(parts) < 5:
            continue
        elapsed_seconds = 0
        stat = ""
        if len(parts) >= 7 and looks_like_ps_stat(parts[3]) and looks_like_ps_etime(parts[4]):
            pid_text, ppid_text, tty, stat, etime, comm, args = parts
            elapsed_seconds = parse_ps_etime_seconds(etime)
        elif len(parts) >= 6 and looks_like_ps_etime(parts[3]):
            parts = line.strip().split(None, 5)
            pid_text, ppid_text, tty, etime, comm, args = parts
            elapsed_seconds = parse_ps_etime_seconds(etime)
        else:
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
        stat_by_pid[pid] = stat
        elapsed_by_pid[pid] = elapsed_seconds
        if is_codex_cli_process(comm, args):
            codex_pids.add(pid)

    fresh_result: list[str] = []
    foreground_stale_result: list[str] = []
    fresh_seen: set[str] = set()
    stale_seen: set[str] = set()
    for pid in sorted(codex_pids):
        current = pid
        foreground_terminal = False
        for _ in range(20):
            if "+" in stat_by_pid.get(current, ""):
                foreground_terminal = True
            tty = tty_by_pid.get(current, "")
            if tty and tty != "??":
                elapsed_seconds = elapsed_by_pid.get(pid, 0)
                is_fresh = stale_after_seconds <= 0 or elapsed_seconds <= stale_after_seconds
                if is_fresh:
                    if tty not in fresh_seen:
                        fresh_seen.add(tty)
                        fresh_result.append(tty)
                elif foreground_terminal and tty not in stale_seen:
                    stale_seen.add(tty)
                    foreground_stale_result.append(tty)
                break
            parent = parent_by_pid.get(current)
            if parent is None or parent == current:
                break
            current = parent
    return fresh_result or foreground_stale_result


def load_marked_codex_tty(path: Path = CURRENT_CODEX_TTY_PATH) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    tty = normalize_tty(str(payload.get("tty") or ""))
    if not tty or tty == "??":
        return ""
    return tty


def deliver_prompt_to_tty(
    tty: str,
    prompt: str,
    *,
    submit: bool = True,
    ioctl_func: Callable[..., Any] = fcntl.ioctl,
) -> dict[str, Any]:
    target_tty = normalize_tty(tty)
    if not target_tty or target_tty == "??":
        return {"ok": False, "status": "tty_delivery_failed", "message": "Chybí cílové TTY."}
    tty_path = Path("/dev") / target_tty
    payload = squash_terminal_text(prompt) + ("\n" if submit else "")
    try:
      with tty_path.open("wb", buffering=0) as handle:
          for char in payload:
              ioctl_func(handle.fileno(), termios.TIOCSTI, char.encode("utf-8"))
    except (OSError, ValueError) as exc:
        return {
            "ok": False,
            "status": "tty_delivery_failed",
            "message": str(exc),
            "target_tty": target_tty,
        }
    return {
        "ok": True,
        "status": "delivered_tty",
        "message": f"Pokyn byl vložen do cílového Codex TTY {target_tty}.",
        "submitted": submit,
        "target_tty": target_tty,
        "verified": False,
    }


def screen_session_exists(
    session_name: str = DEFAULT_CODEX_SCREEN_SESSION,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> bool:
    try:
        completed = runner(["screen", "-ls"], capture_output=True, text=True, timeout=4, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    output = f"{completed.stdout}\n{completed.stderr}"
    return f".{session_name}" in output


def deliver_prompt_to_screen_session(
    prompt: str,
    *,
    submit: bool = True,
    session_name: str = DEFAULT_CODEX_SCREEN_SESSION,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    if not screen_session_exists(session_name=session_name, runner=runner):
        return {
            "ok": False,
            "status": "screen_not_running",
            "message": f"Screen relace {session_name} neběží.",
            "session_name": session_name,
            "delivery_method": "screen_stuff",
        }
    payload = SCREEN_CLEAR_INPUT + squash_terminal_text(prompt)
    try:
        insert_completed = runner(
            ["screen", "-S", session_name, "-p", "0", "-X", "stuff", payload],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        completed = insert_completed
        if submit and insert_completed.returncode == 0:
            sleeper(0.2)
            completed = runner(
                ["screen", "-S", session_name, "-p", "0", "-X", "stuff", SCREEN_SUBMIT_INPUT],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "status": "screen_delivery_failed",
            "message": f"Pokyn se nepodařilo vložit do screen relace: {exc}",
            "session_name": session_name,
            "delivery_method": "screen_stuff",
        }
    if completed.returncode != 0:
        return {
            "ok": False,
            "status": "screen_delivery_failed",
            "message": (completed.stderr or completed.stdout or "Vložení pokynu do screen relace selhalo.").strip(),
            "returncode": completed.returncode,
            "session_name": session_name,
            "delivery_method": "screen_stuff",
        }
    return {
        "ok": True,
        "status": "screen_delivery_unverified",
        "message": (
            f"Screen relace {session_name} přijala příkaz `stuff`, ale doručení do Codex chatu "
            "nejde ověřit. Nepovažuji to za jisté vložení."
        ),
        "submitted": submit,
        "session_name": session_name,
        "delivery_method": "screen_stuff",
        "verified": False,
    }


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
    if (count of targetTtys) > 0 then
      repeat with terminalWindow in windows
        repeat with terminalTab in tabs of terminalWindow
          set tabTty to tty of terminalTab
          if tabTty starts with "/dev/" then set tabTty to text 6 thru -1 of tabTty
          if targetTtys contains tabTty then
            set selected tab of terminalWindow to terminalTab
            set index of terminalWindow to 1
            set foundTarget to true
            exit repeat
          end if
        end repeat
        if foundTarget then exit repeat
      end repeat
    end if
    if not foundTarget then
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
    end if
    if not foundTarget then error "Nenalezen Terminal tab s procesem codex ani s odpovídajícím TTY."
    activate
  end tell
  delay 0.2
  tell application "System Events"
    set the clipboard to promptText
    keystroke "v" using command down
    delay 0.25
    if shouldSubmit is "1" then key code 36
  end tell
  return "delivered"
end run
'''.strip()


def vscode_applescript() -> str:
    return r'''
on run argv
  set promptText to item 1 of argv
  set shouldSubmit to item 2 of argv
  tell application "System Events"
    set frontAppName to name of first application process whose frontmost is true
  end tell
  tell application "Visual Studio Code"
    activate
  end tell
  delay 0.2
  tell application "System Events"
    keystroke "u" using control down
    delay 0.1
    set the clipboard to promptText
    keystroke "v" using command down
    delay 0.25
    if shouldSubmit is "1" then key code 36
  end tell
  if frontAppName is not "Visual Studio Code" and frontAppName is not "Code" then
    delay 0.2
    tell application frontAppName to activate
  end if
  return "delivered_vscode"
end run
'''.strip()


def deliver_prompt_to_vscode(
    prompt: str,
    *,
    submit: bool = True,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    script: str | None = None,
    timeout: float = 8.0,
) -> dict[str, Any]:
    safe_prompt = squash_terminal_text(prompt)
    completed = runner(
        [
            "/usr/bin/osascript",
            "-e",
            script or vscode_applescript(),
            safe_prompt,
            "1" if submit else "0",
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "ok": False,
            "status": "vscode_delivery_failed",
            "message": (completed.stderr or completed.stdout or "VS Code bridge selhal.").strip(),
            "returncode": completed.returncode,
        }
    return {
        "ok": True,
        "status": "vscode_delivery_unverified",
        "message": (
            "VS Code AppleScript proběhl, ale neumím ověřit, že se text dostal "
            "do aktivního Codex chatu. Nepovažuji to za jisté doručení."
        ),
        "submitted": submit,
        "verified": False,
        "delivery_method": "local_gui_vscode",
    }


def deliver_prompt_to_terminal(
    prompt: str,
    *,
    submit: bool = True,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ps_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    script: str | None = None,
    vscode_script: str | None = None,
    vscode_fallback: bool = True,
    marked_tty_path: Path = CURRENT_CODEX_TTY_PATH,
    tty_deliverer: Callable[..., dict[str, Any]] = deliver_prompt_to_tty,
    screen_session_name: str = DEFAULT_CODEX_SCREEN_SESSION,
    screen_deliverer: Callable[..., dict[str, Any]] = deliver_prompt_to_screen_session,
    timeout: float = 8.0,
) -> dict[str, Any]:
    safe_prompt = squash_terminal_text(prompt)
    marked_tty = load_marked_codex_tty(marked_tty_path)
    codex_ttys = discover_codex_ttys(runner=ps_runner)
    codex_session_seen = bool(codex_ttys)
    effective_marked_tty = marked_tty if marked_tty and (marked_tty in codex_ttys or not codex_ttys) else ""
    auto_target_tty = ""
    stale_marked_tty = marked_tty if marked_tty and codex_ttys and marked_tty not in codex_ttys else ""
    if stale_marked_tty and len(codex_ttys) == 1:
        auto_target_tty = codex_ttys[0]
    marked_tty_error: dict[str, Any] | None = None
    screen_unverified_status: dict[str, Any] | None = None
    if effective_marked_tty or auto_target_tty:
        target_tty = effective_marked_tty or auto_target_tty
        tty_result = tty_deliverer(target_tty, safe_prompt, submit=submit)
        if auto_target_tty:
            tty_result = {
                **tty_result,
                "marked_tty_status": {
                    "ok": False,
                    "status": "stale_marked_tty",
                    "message": f"Označené TTY {marked_tty} už nepatří aktivní Codex relaci.",
                    "target_tty": marked_tty,
                },
                "auto_target_tty": auto_target_tty,
            }
        if tty_result.get("ok") and tty_result.get("verified"):
            return tty_result
        if tty_result.get("ok"):
            return {
                **tty_result,
                "message": (
                    f"{tty_result.get('message') or 'Pokyn byl vložen do cílového TTY.'} "
                    "Doručení do označené relace neumím ověřit, proto nespouštím GUI fallback."
                ),
                "delivery_method": "auto_single_codex_tty" if auto_target_tty else "marked_tty",
            }
        marked_tty_error = tty_result
    elif stale_marked_tty:
        marked_tty_error = {
            "ok": False,
            "status": "stale_marked_tty",
            "message": f"Označené TTY {marked_tty} už nepatří aktivní Codex relaci.",
            "target_tty": marked_tty,
        }

    if screen_session_name and (marked_tty or codex_ttys):
        screen_result = screen_deliverer(safe_prompt, submit=submit, session_name=screen_session_name, runner=runner)
        if screen_result.get("ok") and screen_result.get("verified"):
            if marked_tty_error:
                screen_result["marked_tty_status"] = marked_tty_error
            if auto_target_tty:
                screen_result["auto_target_tty"] = auto_target_tty
            return {
                **screen_result,
                "target_ttys": codex_ttys,
            }
        if screen_result.get("ok"):
            screen_unverified_status = {
                **screen_result,
                "target_ttys": codex_ttys,
            }
            if marked_tty_error:
                screen_unverified_status["marked_tty_status"] = marked_tty_error
            if auto_target_tty:
                screen_unverified_status["auto_target_tty"] = auto_target_tty

    if effective_marked_tty:
        target_ttys = [effective_marked_tty]
    elif auto_target_tty:
        target_ttys = [auto_target_tty]
    else:
        target_ttys = codex_ttys
    completed = runner(
        [
            "/usr/bin/osascript",
            "-e",
            script or terminal_applescript(),
            safe_prompt,
            "1" if submit else "0",
            ",".join(target_ttys),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        fallback_blocked_message = (
            "Nebyla nalezena aktivní Codex CLI relace, proto VS Code fallback nehlásím jako doručení."
        )
        terminal_error = {
            "ok": False,
            "status": "no_active_codex_session" if not codex_session_seen else "terminal_delivery_failed",
            "message": (
                f"{(completed.stderr or completed.stdout or 'Terminálový bridge selhal.').strip()} "
                f"{fallback_blocked_message if not codex_session_seen else ''}"
            ).strip(),
            "returncode": completed.returncode,
            "target_ttys": codex_ttys,
        }
        if screen_unverified_status:
            terminal_error["screen_status"] = screen_unverified_status
        if marked_tty_error:
            terminal_error["marked_tty_status"] = marked_tty_error
        if vscode_fallback and codex_session_seen:
            vscode_result = deliver_prompt_to_vscode(
                safe_prompt,
                submit=submit,
                runner=runner,
                script=vscode_script,
                timeout=timeout,
            )
            if vscode_result.get("ok"):
                return {
                    **vscode_result,
                    "terminal_status": terminal_error,
                    "target_ttys": codex_ttys,
                }
            detail_parts = [terminal_error["message"]]
            if marked_tty_error:
                detail_parts.append(f"TTY {marked_tty_error.get('target_tty')}: {marked_tty_error.get('message')}")
            detail_parts.append(f"VS Code fallback: {vscode_result.get('message')}")
            terminal_error["message"] = " | ".join(part for part in detail_parts if part)
            return {
                **terminal_error,
                "vscode_status": vscode_result,
            }
        return terminal_error
    if not codex_session_seen:
        return {
            "ok": True,
            "status": "terminal_delivery_unverified",
            "message": (
                "Pokyn byl vložen do terminálu, ale nebyla nalezena aktivní Codex CLI relace. "
                "Doručení proto neoznačuji jako ověřené."
            ),
            "submitted": submit,
            "target_ttys": codex_ttys,
            "verified": False,
            "delivery_method": "local_gui_terminal",
            "marked_tty_status": marked_tty_error,
        }
    return {
        "ok": True,
        "status": "terminal_delivery_unverified",
        "message": (
            "Terminálový AppleScript proběhl, ale neumím ověřit, že se text dostal "
            "do aktivního Codex chatu. Nepovažuji to za jisté doručení."
        ),
        "submitted": submit,
        "target_ttys": codex_ttys,
        "verified": False,
        "delivery_method": "local_gui_terminal",
        "marked_tty_status": marked_tty_error,
        "screen_status": screen_unverified_status,
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
