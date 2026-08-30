#!/usr/bin/env python3
"""Build the secret-free source plist for Samantha's GitHub-backed Quick Note Shortcut."""

from __future__ import annotations

import plistlib
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "generated_shortcuts" / "Samantha_Quick_Note_GitHub.xml"
WORKFLOW_NAME = "Samantha – Quick Note"
PLACEHOLDER = "\ufffc"

UUIDS = {
    "ask-note": "362958E5-15CC-44A0-AE16-97B3DD45BDB6",
    "delivery-id": "4E23217E-294D-4C7F-B2B7-35E436B5BEBB",
    "github-token": "28047218-DAF3-4528-B609-2FC97CBF9717",
    "github-url": "471367B1-9FDF-4221-9B5A-A0B6EE6671F0",
    "issue-body": "91320806-C44B-4E69-9A47-7D5C329E849C",
    "issue-title": "17298DF3-DC56-416E-81BC-BDF3323871A3",
    "issue-response": "4EC64D37-367A-4A76-919F-7810AF7D848D",
    "issue-number": "9A7A5668-2603-4D1A-A123-9100987EFD4C",
    "cockpit-url": "E48B5399-EE1A-4BAC-BD51-A37A80AD3C73",
    "cockpit-response": "58266BB5-9CB9-4D05-9295-BE1A20018E7B",
    "receipt-id": "4ADE883E-390E-41F2-B42D-BE5CC0681196",
    "receipt-text": "6A31E006-A8D7-4862-8064-3C3594E4267D",
    "issue-if": "B5F9DEA9-F3A7-4085-AE15-A19D4AB4BF0E",
    "receipt-if": "A5DF26C0-118C-4664-8E5B-8B944C8E49DB",
}


def action(identifier: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "WFWorkflowActionIdentifier": identifier,
        "WFWorkflowActionParameters": parameters or {},
    }


def output_reference(output_uuid: str, output_name: str) -> dict[str, str]:
    return {
        "OutputName": output_name,
        "OutputUUID": output_uuid,
        "Type": "ActionOutput",
    }


def token_attachment(output_uuid: str, output_name: str) -> dict[str, Any]:
    return {
        "Value": output_reference(output_uuid, output_name),
        "WFSerializationType": "WFTextTokenAttachment",
    }


def token_string(*parts: str | tuple[str, str]) -> dict[str, Any]:
    text_parts: list[str] = []
    attachments: dict[str, dict[str, str]] = {}
    position = 0
    for part in parts:
        if isinstance(part, str):
            text_parts.append(part)
            position += len(part)
            continue
        output_uuid, output_name = part
        text_parts.append(PLACEHOLDER)
        attachments[f"{{{position}, 1}}"] = output_reference(output_uuid, output_name)
        position += 1
    value: dict[str, Any] = {"string": "".join(text_parts)}
    if attachments:
        value["attachmentsByRange"] = attachments
    return {"Value": value, "WFSerializationType": "WFTextTokenString"}


def current_date_token_string(prefix: str, *, date_format: str) -> dict[str, Any]:
    return {
        "Value": {
            "string": f"{prefix}{PLACEHOLDER}",
            "attachmentsByRange": {
                f"{{{len(prefix)}, 1}}": {
                    "Aggrandizements": [
                        {
                            "Type": "WFDateFormatVariableAggrandizement",
                            "WFDateFormat": date_format,
                            "WFDateFormatStyle": "Custom",
                            "WFISO8601IncludeTime": False,
                        }
                    ],
                    "Type": "CurrentDate",
                }
            },
        },
        "WFSerializationType": "WFTextTokenString",
    }


def dictionary_items(entries: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    items = [
        {
            "WFItemType": 0,
            "WFKey": token_string(key),
            "WFValue": value,
        }
        for key, value in entries
    ]
    return {
        "Value": {"WFDictionaryFieldValueItems": items},
        "WFSerializationType": "WFDictionaryFieldValue",
    }


def condition_input(output_uuid: str, output_name: str) -> dict[str, Any]:
    return {
        "Type": "Variable",
        "Variable": token_attachment(output_uuid, output_name),
    }


def comment(text: str) -> dict[str, Any]:
    return action("is.workflow.actions.comment", {"WFCommentActionText": text})


def show_result(*parts: str | tuple[str, str]) -> dict[str, Any]:
    return action("is.workflow.actions.showresult", {"Text": token_string(*parts)})


def build_actions() -> list[dict[str, Any]]:
    ask_id = UUIDS["ask-note"]
    delivery_id = UUIDS["delivery-id"]
    token_id = UUIDS["github-token"]
    github_url_id = UUIDS["github-url"]
    issue_body_id = UUIDS["issue-body"]
    issue_title_id = UUIDS["issue-title"]
    issue_response_id = UUIDS["issue-response"]
    issue_number_id = UUIDS["issue-number"]
    cockpit_url_id = UUIDS["cockpit-url"]
    cockpit_response_id = UUIDS["cockpit-response"]
    receipt_id = UUIDS["receipt-id"]
    receipt_text_id = UUIDS["receipt-text"]
    issue_if_group = UUIDS["issue-if"]
    receipt_if_group = UUIDS["receipt-if"]

    return [
        comment(
            "Samantha – Quick Note.\n\n"
            "Nejprve uloží delší technickou poznámku do soukromého GitHub Issues inboxu. "
            "Potom zkusí přímé doručení do Cockpitu přes Tailscale. Mac uzavře GitHub "
            "Issue až po lokálním převzetí stejného delivery_id."
        ),
        comment(
            "Shortcuts generated by Shortcuts Playground. May contain mistakes. Always check "
            "the shortcut's actions first.\n\n"
            "This shortcut was created via the following user prompt:\n\n"
            "> Vytvoř iPhone zkratku Samantha Quick Notes: nejprve ulož delší technický "
            "nápad do soukromého GitHub Issues inboxu, potom zkus přímé doručení do "
            "Cockpitu přes Tailscale a potvrď jen přesnou shodu delivery_id."
        ),
        comment("1. Zeptej se na text Quick Note a vytvoř jedinečné delivery_id."),
        action(
            "is.workflow.actions.ask",
            {
                "CustomOutputName": "Quick Note",
                "UUID": ask_id,
                "WFAskActionPrompt": "Co chceš uložit do Quick Notes?",
                "WFInputType": "Text",
            },
        ),
        action(
            "is.workflow.actions.gettext",
            {
                "CustomOutputName": "Delivery ID",
                "UUID": delivery_id,
                "WFTextActionText": current_date_token_string(
                    "samantha-qn-",
                    date_format="yyyyMMddHHmmssSSS",
                ),
            },
        ),
        comment(
            "2. GitHub token musí být fine-grained a omezený jen na soukromý QN "
            "repozitář s oprávněním Issues: Read and write. Vytvoření tokenu: "
            "https://github.com/settings/personal-access-tokens/new"
        ),
        action(
            "is.workflow.actions.gettext",
            {
                "CustomOutputName": "GitHub token",
                "UUID": token_id,
                "WFTextActionText": "github_pat_REPLACE_ME",
            },
        ),
        action(
            "is.workflow.actions.url",
            {
                "CustomOutputName": "GitHub Issues URL",
                "UUID": github_url_id,
                "WFURLActionURL": "https://api.github.com/repos/OWNER/REPOSITORY/issues",
            },
        ),
        action(
            "is.workflow.actions.gettext",
            {
                "CustomOutputName": "GitHub Issue body",
                "UUID": issue_body_id,
                "WFTextActionText": token_string(
                    "Samantha quick note v1\ndelivery_id: ",
                    (delivery_id, "Delivery ID"),
                    "\ncreated_at:\n\n",
                    (ask_id, "Quick Note"),
                ),
            },
        ),
        action(
            "is.workflow.actions.gettext",
            {
                "CustomOutputName": "GitHub Issue title",
                "UUID": issue_title_id,
                "WFTextActionText": token_string(
                    "[Samantha QN] ",
                    (delivery_id, "Delivery ID"),
                ),
            },
        ),
        action(
            "is.workflow.actions.downloadurl",
            {
                "CustomOutputName": "GitHub Issue response",
                "UUID": issue_response_id,
                "WFHTTPBodyType": "JSON",
                "WFHTTPHeaders": dictionary_items(
                    [
                        ("Accept", token_string("application/vnd.github+json")),
                        ("Authorization", token_string("Bearer ", (token_id, "GitHub token"))),
                        ("X-GitHub-Api-Version", token_string("2026-03-10")),
                    ]
                ),
                "WFHTTPMethod": "POST",
                "WFJSONValues": dictionary_items(
                    [
                        ("title", token_string((issue_title_id, "GitHub Issue title"))),
                        ("body", token_string((issue_body_id, "GitHub Issue body"))),
                    ]
                ),
                "WFURL": token_string((github_url_id, "GitHub Issues URL")),
            },
        ),
        action(
            "is.workflow.actions.getvalueforkey",
            {
                "CustomOutputName": "GitHub Issue number",
                "UUID": issue_number_id,
                "WFDictionaryKey": "number",
                "WFGetDictionaryValueType": "Value",
                "WFInput": token_attachment(issue_response_id, "GitHub Issue response"),
            },
        ),
        comment(
            "3. Pokračuj k přímému doručení jen tehdy, když GitHub vrátil číslo Issue.\n"
            "• Když Mac spí, Cockpit požadavek může vypršet a Issue zůstane otevřená.\n"
            "• Quick Note neposílej automaticky žádnou třetí cestou."
        ),
        action(
            "is.workflow.actions.conditional",
            {
                "GroupingIdentifier": issue_if_group,
                "WFCondition": 100,
                "WFControlFlowMode": 0,
                "WFInput": condition_input(issue_number_id, "GitHub Issue number"),
            },
        ),
        comment("4. Zkus přímé doručení stejného textu a stejného delivery_id přes Tailscale."),
        action(
            "is.workflow.actions.url",
            {
                "CustomOutputName": "Cockpit delivery URL",
                "UUID": cockpit_url_id,
                "WFURLActionURL": "https://cockpit-host.tailnet-name.ts.net/api/quick-notes/deliver",
            },
        ),
        action(
            "is.workflow.actions.downloadurl",
            {
                "CustomOutputName": "Odpověď Cockpitu",
                "UUID": cockpit_response_id,
                "WFHTTPBodyType": "JSON",
                "WFHTTPMethod": "POST",
                "WFJSONValues": dictionary_items(
                    [
                        ("text", token_string((ask_id, "Quick Note"))),
                        ("delivery_id", token_string((delivery_id, "Delivery ID"))),
                    ]
                ),
                "WFURL": token_string((cockpit_url_id, "Cockpit delivery URL")),
            },
        ),
        action(
            "is.workflow.actions.getvalueforkey",
            {
                "CustomOutputName": "Potvrzené delivery_id",
                "UUID": receipt_id,
                "WFDictionaryKey": "delivery_id",
                "WFGetDictionaryValueType": "Value",
                "WFInput": token_attachment(cockpit_response_id, "Odpověď Cockpitu"),
            },
        ),
        action(
            "is.workflow.actions.gettext",
            {
                "CustomOutputName": "Potvrzené delivery_id jako text",
                "UUID": receipt_text_id,
                "WFTextActionText": token_string((receipt_id, "Potvrzené delivery_id")),
            },
        ),
        comment(
            "5. Přímé doručení potvrď jen při přesné shodě delivery_id.\n"
            "• Shoda: Cockpit Quick Note převzal.\n"
            "• Neshoda: stav je nejistý a GitHub Issue zůstává bezpečně otevřená."
        ),
        action(
            "is.workflow.actions.conditional",
            {
                "GroupingIdentifier": receipt_if_group,
                "WFCondition": 4,
                "WFConditionalActionString": token_string((delivery_id, "Delivery ID")),
                "WFControlFlowMode": 0,
                "WFInput": condition_input(receipt_text_id, "Potvrzené delivery_id jako text"),
            },
        ),
        show_result(
            "Quick Note doručena přímo do Cockpitu. GitHub záloha #",
            (issue_number_id, "GitHub Issue number"),
            " se po převzetí na Macu automaticky uzavře.",
        ),
        action(
            "is.workflow.actions.conditional",
            {"GroupingIdentifier": receipt_if_group, "WFControlFlowMode": 1},
        ),
        show_result(
            "Doručení je nejisté. GitHub QN záloha #",
            (issue_number_id, "GitHub Issue number"),
            " zůstává otevřená.",
        ),
        action(
            "is.workflow.actions.conditional",
            {"GroupingIdentifier": receipt_if_group, "WFControlFlowMode": 2},
        ),
        action(
            "is.workflow.actions.conditional",
            {"GroupingIdentifier": issue_if_group, "WFControlFlowMode": 1},
        ),
        show_result(
            "GitHub nepotvrdil vytvoření QN zálohy. Quick Note neposílám dál. Stav je "
            "nejistý; před případným novým pokusem zkontroluj soukromý inbox."
        ),
        action(
            "is.workflow.actions.conditional",
            {"GroupingIdentifier": issue_if_group, "WFControlFlowMode": 2},
        ),
    ]


def build_workflow() -> dict[str, Any]:
    return {
        "WFWorkflowActions": build_actions(),
        "WFWorkflowClientVersion": "2700.0.4",
        "WFWorkflowHasOutputFallback": False,
        "WFWorkflowIcon": {
            "WFWorkflowIconGlyphNumber": 61464,
            "WFWorkflowIconStartColor": 3031607807,
        },
        "WFWorkflowImportQuestions": [
            {
                "ActionIndex": 6,
                "Category": "Parameter",
                "DefaultValue": "github_pat_REPLACE_ME",
                "ParameterKey": "WFTextActionText",
                "Text": (
                    "Vlož fine-grained GitHub token omezený jen na soukromý QN inbox "
                    "s oprávněním Issues: Read and write"
                ),
            },
            {
                "ActionIndex": 7,
                "Category": "Parameter",
                "DefaultValue": "https://api.github.com/repos/OWNER/REPOSITORY/issues",
                "ParameterKey": "WFURLActionURL",
                "Text": "Vlož GitHub API URL soukromého QN inboxu zakončenou /issues",
            },
            {
                "ActionIndex": 15,
                "Category": "Parameter",
                "DefaultValue": (
                    "https://cockpit-host.tailnet-name.ts.net/api/quick-notes/deliver"
                ),
                "ParameterKey": "WFURLActionURL",
                "Text": (
                    "Vlož celou Tailscale HTTPS adresu Cockpitu zakončenou "
                    "/api/quick-notes/deliver"
                ),
            },
        ],
        "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowName": WORKFLOW_NAME,
        "WFWorkflowOutputContentItemClasses": [],
        "WFWorkflowTypes": [],
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("wb") as handle:
        plistlib.dump(build_workflow(), handle, fmt=plistlib.FMT_XML, sort_keys=False)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
