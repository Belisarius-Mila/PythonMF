from __future__ import annotations

import re
import shutil
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = PROJECT_ROOT / "data" / "private" / "iphone_shortcuts"
REQUESTS_DIR = PRIVATE_ROOT / "requests"
SHORTCUTS_PLAYGROUND_OUTPUT_DIR = Path.home() / "Documents" / "Shortcuts Playground"
REQUEST_CONFIRMATION_PHRASE = "Potvrzuji pripravu iPhone zkratky"
SHORTCUTS_PLAYGROUND_REPO = "https://github.com/viticci/shortcuts-playground-plugin"


@dataclass(frozen=True)
class IPhoneShortcutsStatus:
    shortcuts_cli: str | None
    codex_cli: str | None
    playground_paths: tuple[Path, ...]
    output_dir_exists: bool
    requests_dir_exists: bool


def format_iphone_shortcuts_status(
    *,
    output_dir: Path = SHORTCUTS_PLAYGROUND_OUTPUT_DIR,
    requests_dir: Path = REQUESTS_DIR,
    shortcuts_cli: str | None = None,
    codex_cli: str | None = None,
    playground_paths: tuple[Path, ...] | None = None,
) -> str:
    status = iphone_shortcuts_status(
        output_dir=output_dir,
        requests_dir=requests_dir,
        shortcuts_cli=shortcuts_cli,
        codex_cli=codex_cli,
        playground_paths=playground_paths,
    )
    lines = [
        "iPhone Shortcuts Playground Status",
        f"- Apple shortcuts CLI: {_present(status.shortcuts_cli)}",
        f"- Codex CLI: {_present(status.codex_cli)}",
        f"- Shortcuts Playground plugin detected: {'yes' if status.playground_paths else 'no'}",
        f"- Playground output folder exists: {'yes' if status.output_dir_exists else 'no'}",
        f"- Local request folder exists: {'yes' if status.requests_dir_exists else 'no'}",
        f"- Plugin source: {SHORTCUTS_PLAYGROUND_REPO}",
        "",
        "Safety:",
        "- Status is read-only.",
        "- Shortcut request preparation writes only to private ignored data after confirmation.",
        "- Generated shortcuts must be opened and checked manually in Apple Shortcuts before use.",
    ]
    if status.playground_paths:
        lines.extend(["", "Detected plugin paths:"])
        lines.extend(f"- `{path}`" for path in status.playground_paths[:5])
    else:
        lines.extend(
            [
                "",
                "Next step:",
                "- Install or enable Shortcuts Playground for Codex, then create a request from Samantha.",
            ]
        )
    return "\n".join(lines)


def iphone_shortcuts_status(
    *,
    output_dir: Path = SHORTCUTS_PLAYGROUND_OUTPUT_DIR,
    requests_dir: Path = REQUESTS_DIR,
    shortcuts_cli: str | None = None,
    codex_cli: str | None = None,
    playground_paths: tuple[Path, ...] | None = None,
) -> IPhoneShortcutsStatus:
    return IPhoneShortcutsStatus(
        shortcuts_cli=shortcuts_cli if shortcuts_cli is not None else shutil.which("shortcuts"),
        codex_cli=codex_cli if codex_cli is not None else shutil.which("codex"),
        playground_paths=playground_paths if playground_paths is not None else _find_playground_paths(),
        output_dir_exists=output_dir.exists(),
        requests_dir_exists=requests_dir.exists(),
    )


def prepare_iphone_shortcut_request(
    *,
    name: str,
    purpose: str,
    details: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    requests_dir: Path = REQUESTS_DIR,
) -> str:
    cleaned_name = name.strip()
    cleaned_purpose = purpose.strip()
    cleaned_details = details.strip()
    if not cleaned_name or not cleaned_purpose:
        return (
            "iPhone Shortcut Request\n"
            "- Status: blocked\n"
            "- Reason: name and purpose are required."
        )

    prompt = _shortcut_prompt(cleaned_name, cleaned_purpose, cleaned_details)
    lines = [
        "iPhone Shortcut Request",
        f"- Name: {cleaned_name}",
        "- Destination: private request draft",
        "",
        "Prompt for Shortcuts Playground:",
        "```text",
        prompt,
        "```",
    ]

    if not user_confirmed or not _has_request_confirmation(confirmation_text):
        lines.extend(
            [
                "",
                "- Status: preview only; no request file written",
                f"- Required confirmation: `{REQUEST_CONFIRMATION_PHRASE}`",
            ]
        )
        return "\n".join(lines)

    requests_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{_slugify(cleaned_name)}.md"
    request_path = requests_dir / filename
    request_path.write_text(_request_document(cleaned_name, cleaned_purpose, cleaned_details, prompt), encoding="utf-8")

    lines.extend(
        [
            "",
            "- Status: request saved",
            f"- Request file: `{request_path}`",
            "",
            "Manual build step after plugin install:",
            "- Open Codex with Shortcuts Playground enabled and use the prompt above with `/shortcuts-playground:build`.",
        ]
    )
    return "\n".join(lines)


def _shortcut_prompt(name: str, purpose: str, details: str) -> str:
    sections = [
        f"Create an Apple Shortcut named: {name}",
        "",
        "Goal:",
        purpose,
        "",
        "Requirements:",
        "- Prefer built-in Apple Shortcuts actions where possible.",
        "- Use Czech user-facing labels if the shortcut shows prompts or menus.",
        "- Avoid destructive actions unless they are explicitly requested.",
        "- Do not require API keys, accounts, paid services, or private credentials unless explicitly requested.",
        "- Add clear comments or visible prompts where the user must review behavior.",
        "- After generating, validate and sign the .shortcut file.",
    ]
    if details:
        sections.extend(["", "Additional details:", details])
    sections.extend(
        [
            "",
            "After generation, summarize:",
            "- what the shortcut does",
            "- which permissions it may request",
            "- what Mila should manually verify before installing it on iPhone",
        ]
    )
    return "\n".join(sections)


def _request_document(name: str, purpose: str, details: str, prompt: str) -> str:
    created = datetime.now().isoformat(timespec="seconds")
    return "\n".join(
        [
            "# iPhone Shortcut Request",
            "",
            f"Created: {created}",
            f"Name: {name}",
            "",
            "## Purpose",
            "",
            purpose,
            "",
            "## Details",
            "",
            details or "-",
            "",
            "## Shortcuts Playground Prompt",
            "",
            "```text",
            prompt,
            "```",
            "",
            "## Safety",
            "",
            "- Private local draft; do not commit.",
            "- Generated .shortcut must be reviewed manually in Apple Shortcuts before use.",
        ]
    )


def _find_playground_paths() -> tuple[Path, ...]:
    roots = [
        Path.home() / ".codex" / "plugins",
        Path.home() / ".codex" / "plugins" / "cache",
        Path.home() / ".codex" / "skills",
    ]
    matches: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if len(matches) >= 10:
                break
            normalized = path.name.casefold()
            if "shortcuts" in normalized and "playground" in normalized:
                matches.append(path)
    return tuple(matches)


def _present(path: str | None) -> str:
    return f"yes (`{path}`)" if path else "no"


def _has_request_confirmation(text: str) -> bool:
    normalized = _normalize(text)
    return all(token in normalized for token in ("potvrzuji", "pripravu", "iphone", "zkratky"))


def _slugify(text: str) -> str:
    normalized = _normalize(text)
    slug = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return slug[:60] or "shortcut"


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))
