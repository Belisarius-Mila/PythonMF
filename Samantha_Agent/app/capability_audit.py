from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from app.capabilities import all_capabilities, validate_registry
from app.capabilities.models import STRICT_CONFIRMATION_RISKS
from app.workflows.commands import WORKFLOW_COMMANDS


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMANTHA_AGENT_PATH = PROJECT_ROOT / "app" / "samantha_agent.py"


@dataclass(frozen=True)
class CapabilityArea:
    name: str
    level: str
    safety: str
    tools: tuple[str, ...]
    next_gap: str


CAPABILITY_AREAS = (
    CapabilityArea(
        name="Memory and system reports",
        level="L3",
        safety="read-only; quantitative snapshot writes only aggregate JSONL on request",
        tools=(
            "search_memory",
            "memory_status",
            "samantha_health_check",
            "samantha_quantitative_status",
            "samantha_system_reports",
            "samantha_capability_audit",
            "samantha_project_audit",
        ),
        next_gap="Keep new repeated audits registered as system reports.",
    ),
    CapabilityArea(
        name="Knowledge inbox",
        level="L3/L4",
        safety="inbox and Downloads inventory read-only; selected Downloads copies require explicit confirmation",
        tools=(
            "samantha_knowledge_inbox_inventory",
            "samantha_downloads_inventory",
            "copy_downloads_files_to_knowledge_inbox",
        ),
        next_gap="Add scoped summarization/import only after explicit file selection and redacted memory diff.",
    ),
    CapabilityArea(
        name="iPhone shortcuts",
        level="L3/L4",
        safety="read-only readiness check; private shortcut request drafts require explicit confirmation",
        tools=(
            "iphone_shortcuts_playground_status",
            "prepare_iphone_shortcut",
        ),
        next_gap="Manually import and test Najit auto v3 before broader shortcut generation.",
    ),
    CapabilityArea(
        name="Quick notes",
        level="L3",
        safety="read-only local notes overview/detail",
        tools=(
            "list_quick_notes",
            "show_quick_note_detail",
            "quick_notes_action_status",
        ),
        next_gap="Convert selected quick notes to explicit confirmed actions only after Mila chooses them.",
    ),
    CapabilityArea(
        name="Email read-only and cases",
        level="L3/L4",
        safety="headers read-only; body, archive, links, sends and case saves require explicit confirmation",
        tools=(
            "list_recent_email_headers",
            "search_email_headers",
            "list_recent_seznam_email_headers",
            "search_seznam_email_headers",
            "show_new_email_overview",
            "list_unified_email_headers",
            "search_email_text_year",
            "read_email_body_by_uid",
            "read_seznam_email_body_by_uid",
            "run_email_triage_session",
            "run_unified_email_triage_session",
            "build_email_case_from_uid",
            "build_email_action_case_from_uid",
            "save_selected_email_cases_from_uids",
            "archive_email_by_uid",
            "prepare_forward_email_by_uid",
            "send_prepared_email_draft",
            "list_email_archives",
            "show_email_archive_summary",
            "show_email_archive_links",
            "build_rixo_insurance_case_from_uids",
            "show_email_case_links",
        ),
        next_gap="Use saved local full triage reports for longer human reviews.",
    ),
    CapabilityArea(
        name="Messages outbound",
        level="L4",
        safety="SMS/RCS send requires explicit confirmation and post-send is_sent/is_delivered/error verification",
        tools=(
            "send_confirmed_sms_rcs",
        ),
        next_gap="Run the next real family SMS/RCS through the confirmed tool and compare Messages DB status.",
    ),
    CapabilityArea(
        name="Reminders and payment cases",
        level="L3",
        safety="read-only listing/details; writes require explicit confirmation",
        tools=(
            "inspect_payment_page_for_reminder",
            "save_email_action_case_reminder",
            "save_payment_case_document",
            "save_payment_sms_reminder",
            "list_open_reminders",
            "show_reminder_detail",
            "mark_reminder_done",
        ),
        next_gap="Verify the next real payment SMS end to end.",
    ),
    CapabilityArea(
        name="Backup, restore and shell workflows",
        level="L2/L3",
        safety="registered argv only; restore first preview, then explicit confirmation",
        tools=(
            "list_backup_snapshots",
            "preview_backup_restore",
            "restore_path_from_backup",
            "list_workflow_commands",
            "preview_workflow_command",
            "run_workflow_command",
        ),
        next_gap="Do a small backup/restore drill when the external container is available.",
    ),
    CapabilityArea(
        name="Document vault",
        level="L3/L4",
        safety="private vault; import, cleanup, reminders and print actions require confirmation",
        tools=(
            "scan_document_inbox",
            "scan_downloaded_pdfs",
            "preview_document_reindex",
            "scan_mobile_document_inbox",
            "document_vault_status",
            "prepare_document_import",
            "apply_document_reindex",
            "prepare_mobile_document_batch",
            "prepare_next_scandocu_document",
            "process_mobile_document_inbox",
            "prepare_mobile_document_final_import",
            "apply_mobile_document_final_import",
            "inspect_document_text",
            "apply_document_import",
            "search_private_documents",
            "save_document_due_reminder",
            "prepare_document_print_job",
            "run_document_print_job",
            "propose_document_inbox_cleanup",
            "resolve_document_inbox_item",
        ),
        next_gap="Before more development, physically verify at least one printed document.",
    ),
    CapabilityArea(
        name="Lekarna",
        level="L3/L4",
        safety="read-only search/audit; retire and photo import are gated write flows",
        tools=(
            "search_domaci_leky",
            "audit_domaci_lekarna",
            "preview_vyrazeni_leku",
            "apply_vyrazeni_leku",
            "stage_lekarna_photo_import",
            "prepare_lekarna_photo_import",
            "apply_lekarna_photo_import",
            "validate_lekarna_photo_sources",
        ),
        next_gap="Add Silymarin photo only when a real source photo arrives.",
    ),
    CapabilityArea(
        name="Media utilities",
        level="L3",
        safety="preview first; apply resizes only after confirmation and backup rules",
        tools=("preview_zmenseni_obrazku", "apply_zmenseni_obrazku"),
        next_gap="Use as shared utility for future vocabulary image batches.",
    ),
)


def format_samantha_capability_audit() -> str:
    tool_names = _agent_tool_names(SAMANTHA_AGENT_PATH)
    mapped_tools = _mapped_tool_names()
    unmapped_tools = tuple(tool for tool in tool_names if tool not in mapped_tools)
    missing_registered_tools = tuple(tool for tool in mapped_tools if tool not in tool_names)
    registry_records = all_capabilities()
    registry_errors = validate_registry()
    high_risk_capabilities = tuple(record for record in registry_records if record.risk in STRICT_CONFIRMATION_RISKS)
    registry_tool_names = _registry_tool_names()
    registry_covered_tools = tuple(tool for tool in tool_names if tool in registry_tool_names)
    missing_registry_tools = tuple(tool for tool in tool_names if tool not in registry_tool_names)
    priority_missing_registry_tools = _priority_missing_registry_tools(missing_registry_tools)

    lines = [
        "Samantha Capability Audit",
        f"- Agent tools: {len(tool_names)}",
        f"- Mapped tools: {len(tool_names) - len(unmapped_tools)}",
        f"- Unmapped tools: {len(unmapped_tools)}",
        f"- Registered shell workflows: {len(WORKFLOW_COMMANDS)}",
        f"- Capability registry records: {len(registry_records)}",
        f"- High-risk capability records: {len(high_risk_capabilities)}",
        f"- Registry-covered agent tools: {len(registry_covered_tools)}/{len(tool_names)}",
        f"- Capability registry: {'OK' if not registry_errors else 'WARN'}",
        "",
        "Capability areas:",
        "| Area | Level | Tools present | Safety | Next gap |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for area in CAPABILITY_AREAS:
        present = len([tool for tool in area.tools if tool in tool_names])
        lines.append(
            f"| {area.name} | {area.level} | {present}/{len(area.tools)} | {area.safety} | {area.next_gap} |"
        )

    lines.extend(["", "Registry gaps:"])
    if unmapped_tools:
        lines.extend(f"- Unmapped agent tool: `{tool}`" for tool in unmapped_tools)
    else:
        lines.append("- No unmapped agent tools.")

    if missing_registered_tools:
        lines.extend(f"- Mapped but missing from agent tools: `{tool}`" for tool in missing_registered_tools)

    lines.extend(["", "Capability registry validation:"])
    if registry_errors:
        lines.extend(f"- {error}" for error in registry_errors)
    else:
        lines.append("- OK")

    lines.extend(["", "Priority missing capability records:"])
    if priority_missing_registry_tools:
        preview_limit = 15
        lines.extend(f"- `{tool}`" for tool in priority_missing_registry_tools[:preview_limit])
        remaining = len(priority_missing_registry_tools) - preview_limit
        if remaining > 0:
            lines.append(f"- ... and {remaining} more.")
    else:
        lines.append("- None.")

    lines.extend(["", "Agent tools missing capability records:"])
    if missing_registry_tools:
        preview_limit = 25
        lines.extend(f"- `{tool}`" for tool in missing_registry_tools[:preview_limit])
        remaining = len(missing_registry_tools) - preview_limit
        if remaining > 0:
            lines.append(f"- ... and {remaining} more.")
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "Priority reserves:",
            "- Reduce active `[PRIPOMENOUT]` noise when it starts hiding true next actions.",
            "- Register PictNew and VocabularyEN workflows before routing human requests to shell.",
            "- Keep network/T-Mobile retest pending until 2026-06-01 unless the connection worsens.",
        ]
    )
    return "\n".join(lines)


def _agent_tool_names(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Name) and node.func.id == "Agent"):
            continue
        for keyword in node.keywords:
            if keyword.arg != "tools" or not isinstance(keyword.value, ast.List):
                continue
            return tuple(
                element.id
                for element in keyword.value.elts
                if isinstance(element, ast.Name)
            )
    return ()


def _mapped_tool_names() -> set[str]:
    return {tool for area in CAPABILITY_AREAS for tool in area.tools}


def _registry_tool_names() -> set[str]:
    names: set[str] = set()
    for record in all_capabilities():
        names.add(record.capability_id)
        if record.tool and record.tool.replace("_", "").isalnum():
            names.add(record.tool)
    return names


def _priority_missing_registry_tools(missing_tools: tuple[str, ...]) -> tuple[str, ...]:
    priority_prefixes = (
        "apply_",
        "archive_",
        "copy_",
        "mark_",
        "prepare_forward",
        "process_",
        "resolve_",
        "restore_",
        "run_",
        "save_",
        "send_",
    )
    return tuple(tool for tool in missing_tools if tool.startswith(priority_prefixes))
