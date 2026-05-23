from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemReport:
    name: str
    when_to_use: str
    output: str
    command: str
    samantha_tool: str
    saves_data: str


SYSTEM_REPORTS = (
    SystemReport(
        name="Health check",
        when_to_use="rychla kontrola rozpracovanosti, git stavu, pending bodu a varovani",
        output="kratky operacni status; `--mode full` ukaze detailnejsi audit",
        command=".venv/bin/python scripts/samantha_health_check.py --mode quick",
        samantha_tool="samantha_health_check(mode='quick')",
        saves_data="ne",
    ),
    SystemReport(
        name="Kvantitativni status",
        when_to_use="objemovy rust Samanthy: soubory, radky, lokalni stav vs git tracked",
        output="tabulky podle typu souboru a souhrn lokalni/git tracked",
        command=".venv/bin/python scripts/samantha_quantitative_status.py",
        samantha_tool="samantha_quantitative_status(save=False)",
        saves_data="jen s `--save` jako agregovana JSONL datova veta",
    ),
    SystemReport(
        name="Capability audit",
        when_to_use="prehled registrovanych schopnosti, toolu, workflow a hlavních rezerv",
        output="tabulka oblasti schopnosti, uroven, bezpecnostni rozsah a nejblizsi mezera",
        command=".venv/bin/python scripts/samantha_capability_audit.py",
        samantha_tool="samantha_capability_audit()",
        saves_data="ne",
    ),
    SystemReport(
        name="Knowledge inbox inventory",
        when_to_use="bezpecny inventar velkych podkladu ve private knowledge inboxu",
        output="nazvy souboru, typy, velikosti a cas zmeny; necte obsah",
        command=".venv/bin/python scripts/samantha_knowledge_inbox.py",
        samantha_tool="samantha_knowledge_inbox_inventory()",
        saves_data="ne",
    ),
    SystemReport(
        name="Memory status",
        when_to_use="stav lokalni pameti, startup kontextu, priorit a pripomenuti",
        output="bezpecna diagnostika memory store bez e-mailu a tajemstvi",
        command=".venv/bin/python -m app.samantha_agent \"Ukaz stav lokalni pameti Samanthy.\"",
        samantha_tool="memory_status()",
        saves_data="ne",
    ),
)


def format_system_reports_overview() -> str:
    lines = [
        "Samantha System Reports",
        "",
        "| Report | Kdy pouzit | Vystup | Uklada data |",
        "| --- | --- | --- | --- |",
    ]
    for report in SYSTEM_REPORTS:
        lines.append(
            f"| {report.name} | {report.when_to_use} | {report.output} | {report.saves_data} |"
        )

    lines.extend(
        [
            "",
            "Prikazy:",
        ]
    )
    for report in SYSTEM_REPORTS:
        lines.append(f"- {report.name}: `{report.command}`")

    lines.extend(
        [
            "",
            "Samantha tools:",
        ]
    )
    for report in SYSTEM_REPORTS:
        lines.append(f"- {report.name}: `{report.samantha_tool}`")

    return "\n".join(lines)
