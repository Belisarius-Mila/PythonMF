"""One approved candidate translation; private receipt, no role or queue writes.

preview() is free. run() consumes one fixed durable slot before connecting.
The candidate manifest replaces no central role and enables no recurring task.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.communication import agent_roles
from app.communication.luna_release import new_luna_client
from app.file_persistence import atomic_write_json, exclusive_file_lock
from app.release_usage import estimate_standard_credits, normalize_usage
from app.routine_tasks import start_data_only_thread
from app.science_news_model import OneTurn, ROLE, TRANSLATION_INSTRUCTIONS, TRANSLATION_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "memory/reports/science_news_translation_preflight_20261109.json"
PACKET = ROOT / "data/private/science_news_preflight/crispr_translation_packet_20261109.json"
SOURCE = ROOT / "data/private/science_news_preflight/crispr_source_20261109.txt"
STATE = ROOT / "data/private/science_news_trial_20261109"
REQUEST = "science-news-crispr-translation-20261109-01"
DEPENDENCIES = ("app/science_news_model.py", "app/routine_tasks.py", "app/codex_appserver.py",
    "app/communication/agent_roles.py", "app/communication/luna_release.py",
    "app/release_usage.py", "app/file_persistence.py")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_read(path, limit):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Pilot nesmí číst ani zapisovat přes symlink.")
    raw = path.read_bytes()
    if len(raw) > limit:
        raise ValueError("Podklady pilotu překročily limit.")
    return raw


def preview():
    report_raw = checked_read(REPORT, 32000)
    packet_raw = checked_read(PACKET, 180000)
    source_raw = checked_read(SOURCE, 50000)
    report, packet = json.loads(report_raw), json.loads(packet_raw)
    if (report["request_id"] != REQUEST or report["candidate_model"] != "gpt-6.1-sol"
            or report["reasoning_effort"] != "medium" or report["speed"] != "Standard"
            or report["proposed_acceptance_credits"] != 5 or report["accepted_output_tokens"] != 16000
            or report["packet_sha256"] != sha(packet_raw) or report["source_sha256"] != sha(source_raw)
            or report["trial_code_sha256"] != sha(Path(__file__).read_bytes())
            or report["trial_dependency_sha256"] != {name: sha(checked_read(ROOT / name, 2000000)) for name in DEPENDENCIES}
            or set(packet) != {"payload", "instructions", "schema"}
            or packet["payload"] != {"source_text": source_raw.decode()}
            or packet["instructions"] != TRANSLATION_INSTRUCTIONS or packet["schema"] != TRANSLATION_SCHEMA):
        raise ValueError("Zmrazený překladový pilot se změnil.")
    payload = json.dumps(packet["payload"], ensure_ascii=False, sort_keys=True)
    proxy = len(payload.encode()) + len(TRANSLATION_INSTRUCTIONS.encode()) + len(json.dumps(TRANSLATION_SCHEMA).encode())
    cost = estimate_standard_credits("gpt-6.1-sol", {"input_tokens": proxy, "cached_input_tokens": 0,
        "output_tokens": 16000, "reasoning_output_tokens": 0, "total_tokens": proxy + 16000})
    if cost is None or cost > 5 or abs(cost - report["body_proxy_credits"]) > 1e-8:
        raise ValueError("Cena pilotu se změnila.")
    return {"request_id": REQUEST, "report_sha256": sha(report_raw), "packet_sha256": sha(packet_raw),
        "model": "gpt-6.1-sol", "reasoning_effort": "medium", "speed": "Standard",
        "body_proxy_credits": cost, "acceptance_credits": 5, "paid_turns": 1,
        "payload": payload, "source_characters": len(source_raw.decode())}


def run(*, confirmed=False, approved_report_sha256="", approved_packet_sha256="", approval_ref="",
        client_factory=new_luna_client):
    if confirmed is not True or not isinstance(approval_ref, str) or not 8 <= len(approval_ref) <= 240:
        raise ValueError("Jediný placený tah vyžaduje konkrétní souhlas.")
    frozen = preview()
    if frozen["report_sha256"] != approved_report_sha256 or frozen["packet_sha256"] != approved_packet_sha256:
        raise ValueError("Souhlas nepatří tomuto přesnému pilotu.")
    if any(p.is_symlink() for p in (STATE, *STATE.parents)):
        raise ValueError("Pilot nesmí zapisovat přes symlink.")
    STATE.mkdir(parents=True, exist_ok=True)
    receipt_path = STATE / "receipt.json"
    if (STATE / "trial.lock.lock").is_symlink():
        raise ValueError("Zámek pilotu nesmí být symlink.")
    with exclusive_file_lock(STATE / "trial.lock"):
        if receipt_path.exists() or receipt_path.is_symlink():
            old = json.loads(checked_read(receipt_path, 500000))
            if old.get("state") == "review" and old.get("report_sha256") == approved_report_sha256:
                return old
            raise ValueError("Pokus již existuje; nic neopakuji. Nejprve ověř účtenku.")
        receipt = {k: v for k, v in frozen.items() if k != "payload"}
        receipt.update(state="delivery_unknown", approval_ref=approval_ref, attempts=1)
        atomic_write_json(receipt_path, receipt)
        try:
            selected = agent_roles.validate_selection({"role": ROLE, "model": frozen["model"],
                "reasoning_effort": frozen["reasoning_effort"], "policy_digest": approved_report_sha256}, role=ROLE)
            with client_factory() as client:
                account = client.transport.request("account/read", {"refreshToken": False}).get("account")
                if not isinstance(account, dict) or account.get("type") != "chatgpt":
                    raise ValueError("Kreditový pilot vyžaduje přihlášení přes ChatGPT.")
                receipt["account_type"] = "chatgpt"
                if not any(agent_roles.compatible(entry, selected) for entry in client.list_models(include_hidden=True)):
                    raise ValueError("Přesný kandidát není dostupný; náhradu nevolím.")
                def unchanged():
                    if preview() != frozen:
                        raise ValueError("Podklady se před odesláním změnily.")
                context = STATE / "context"
                client.transport = OneTurn(client.transport, context, selected, TRANSLATION_INSTRUCTIONS,
                    frozen["payload"], TRANSLATION_SCHEMA, unchanged)
                thread = start_data_only_thread(client, context, selected["model"], TRANSLATION_INSTRUCTIONS)["thread_id"]
                receipt["thread_id"] = thread
                atomic_write_json(receipt_path, receipt)
                answer = client.send_text(thread_id=thread, text=frozen["payload"], model=selected["model"],
                    effort="medium", approval_policy="never", sandbox_policy={"type": "readOnly", "networkAccess": False},
                    output_schema=TRANSLATION_SCHEMA)
            receipt.update(raw_answer=answer.answer, raw_usage=getattr(answer, "thread_token_usage", None))
            atomic_write_json(receipt_path, receipt)
            if getattr(answer, "delivered", False) is not True or getattr(answer, "thread_id", None) != thread:
                raise ValueError("Doručení konkrétního výsledku není ověřené.")
            usage = normalize_usage(getattr(answer, "thread_token_usage", None))
            cost = estimate_standard_credits(selected["model"], usage)
            if usage is None or cost is None or cost > 5 or usage["output_tokens"] > 16000 or usage["total_tokens"] > 100000:
                raise ValueError("Spotřeba není přijatelná nebo ověřená.")
            result = json.loads(answer.answer)
            if (not isinstance(result, dict) or set(result) != {"translation", "complete"} or result["complete"] is not True
                    or not isinstance(result["translation"], str)
                    or not .3 * frozen["source_characters"] <= len(result["translation"]) <= 4 * frozen["source_characters"]):
                raise ValueError("Výsledek není úplný překlad.")
            unchanged()
            receipt.update(state="review", token_usage=usage, estimated_standard_credits=cost,
                translation=result["translation"], semantic_review_required=True)
            atomic_write_json(receipt_path, receipt)
            return receipt
        except Exception as error:
            receipt.update(state="attention", error_type=type(error).__name__)
            atomic_write_json(receipt_path, receipt)
            raise
