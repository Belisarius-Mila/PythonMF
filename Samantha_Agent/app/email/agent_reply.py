"""Two-step replies for continuous-agent cards, with durable send outcomes."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
import smtplib
import ssl
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import formataddr, format_datetime, getaddresses, make_msgid

import certifi

from app.file_persistence import exclusive_file_lock
from .config import load_smtp_config
from .continuous_agent import ContinuousEmailAgent
from .continuous_source import IMAPAgentSource
from .outbound import save_sent_copy_best_effort, validate_email_address


def _address(value: str) -> str:
    if "\r" in value or "\n" in value:
        raise ValueError("Adresa nesmí obsahovat nový řádek.")
    return validate_email_address(value)


def _ids(value: str) -> list[str]:
    return re.findall(r"<[^<>\s]+@[^<>\s]+>", value)


def _confirmation_digest(raw: bytes, fields: dict) -> str:
    frozen = {key: fields[key] for key in ("account", "provider", "sender", "recipient", "subject", "body", "proposal_digest")}
    frozen["message_digest"] = hashlib.sha256(raw).hexdigest()
    return hashlib.sha256(json.dumps(frozen, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def build_reply(observed, proposal: dict, config, *, now=None) -> EmailMessage:
    parent = BytesParser(policy=policy.default).parsebytes(observed.source.original_eml)
    addresses = getaddresses(parent.get_all("Reply-To", []) or parent.get_all("From", []))
    if len(addresses) != 1:
        raise ValueError("Odpověď vyžaduje jednoho jednoznačného příjemce.")
    name, recipient = addresses[0]
    recipient = _address(recipient)
    sender = _address(config.address)
    if config.provider != observed.source.provider:
        raise ValueError("Odesílací účet neodpovídá zdrojové zprávě.")
    subject = proposal.get("reply_subject") or "Re: " + observed.source.subject
    body = proposal.get("reply_draft", "")
    if not subject.strip() or any(c in subject for c in "\r\n") or not body.strip():
        raise ValueError("Vyplň jednořádkový předmět a text odpovědi.")
    message = EmailMessage(policy=policy.SMTP)
    message["From"] = sender
    message["To"] = formataddr((name, recipient))
    message["Subject"] = subject
    message["Date"] = format_datetime(now or datetime.now(timezone.utc))
    message["Message-ID"] = make_msgid(domain=sender.rsplit("@", 1)[1])
    parent_ids = _ids(str(parent.get("Message-ID", "")))
    if len(parent_ids) == 1:
        message["In-Reply-To"] = parent_ids[0]
    references = _ids(str(parent.get("References", "")))
    if not references:
        previous = _ids(str(parent.get("In-Reply-To", "")))
        references = previous if len(previous) == 1 else []
    references += parent_ids
    if references:
        message["References"] = " ".join(dict.fromkeys(references))
    message.set_content(body, cte="quoted-printable")
    return message


@dataclass(frozen=True)
class ReplySMTPOutcome:
    status: str
    session_close_ok: bool = True
    error_type: str = ""


class ReplySMTPTransport:
    def __init__(self, smtp_factory=None):
        self.smtp_factory = smtp_factory

    def __call__(self, raw: bytes, config, recipient: str) -> ReplySMTPOutcome:
        result, data_started = None, False
        try:
            context = ssl.create_default_context(cafile=certifi.where())
            factory = self.smtp_factory or (smtplib.SMTP_SSL if config.security == "ssl" else smtplib.SMTP)
            kwargs = {"timeout": 30}
            if config.security == "ssl": kwargs["context"] = context
            with factory(config.host, config.port, **kwargs) as smtp:
                smtp.ehlo()
                if config.security == "starttls":
                    smtp.starttls(context=context)
                    smtp.ehlo()
                smtp.login(config.address, config.password)
                message = BytesParser(policy=policy.default).parsebytes(raw)
                data_started = True
                refused = smtp.send_message(message, from_addr=config.address, to_addrs=[recipient])
                if not isinstance(refused, dict):
                    raise ValueError("SMTP neposkytlo jednoznačný výsledek.")
                result = ReplySMTPOutcome("not_sent" if refused else "smtp_sent")
        except Exception as exc:
            if result is not None:
                return replace(result, session_close_ok=False)
            rejected = isinstance(exc, (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused, smtplib.SMTPDataError))
            return ReplySMTPOutcome("not_sent" if rejected or not data_started else "delivery_unknown",
                                    error_type=type(exc).__name__)
        return result


class AgentReplyService:
    def __init__(self, worker=None, *, source_factory=IMAPAgentSource,
                 config_loader=load_smtp_config, transport=None, sent_copy_saver=save_sent_copy_best_effort):
        self.worker = worker or ContinuousEmailAgent()
        self.source_factory, self.config_loader = source_factory, config_loader
        self.transport = transport or ReplySMTPTransport()
        self.sent_copy_saver = sent_copy_saver

    def prepare(self, item_id: str, *, expected_digest: str) -> dict:
        item = self.worker.status()["items"][item_id]
        if item["proposal_digest"] != expected_digest:
            raise ValueError("Koncept se změnil; načti jeho aktuální verzi.")
        observed = self.source_factory(item["provider"], item["folder"]).read_item(item)
        if observed.item_id != item_id or observed.content_digest != item["content_digest"]:
            raise ValueError("Zdroj zprávy neodpovídá kartě.")
        config = self.config_loader(item["provider"])
        account_key = hashlib.sha256(
            f"{config.provider}|{config.address.casefold()}|{observed.source.mailbox}".encode()).hexdigest()
        if account_key != observed.account:
            raise ValueError("Odesílací účet neodpovídá příjemci původní zprávy.")
        message = build_reply(observed, item["proposal"], config)
        raw = message.as_bytes()
        recipient_name, recipient = getaddresses([str(message["To"])])[0]
        confirmation = {
            "status": "prepared", "proposal_digest": expected_digest,
            "confirmation_token": secrets.token_urlsafe(24),
            "account": item["account"], "provider": item["provider"],
            "sender": config.address, "recipient": recipient, "recipient_name": recipient_name,
            "subject": str(message["Subject"]), "body": item["proposal"]["reply_draft"],
            "message_id": str(message["Message-ID"]),
            "message_b64": base64.b64encode(raw).decode("ascii"),
        }
        confirmation["confirmation_digest"] = _confirmation_digest(raw, confirmation)
        with exclusive_file_lock(self.worker.root / "worker", timeout=0):
            def update(document):
                current = document["items"][item_id]
                if (current["proposal_digest"] != expected_digest
                    or current["status"] not in {"awaiting_confirmation", "archived"}
                    or current.get("reply", {}).get("status") in {"sending", "smtp_sent", "delivery_unknown"}):
                    raise ValueError("Odpověď se změnila nebo již má evidovaný pokus o odeslání.")
                current["reply"] = confirmation
            self.worker._update(update)
        return {key: value for key, value in confirmation.items() if key != "message_b64"}

    def send(self, item_id: str, *, confirmation_token: str, confirmation_digest: str, confirmed: bool) -> dict:
        # Validate identity before constructing a per-message lock path.
        if item_id not in self.worker.status()["items"]:
            raise ValueError("Karta nebyla nalezena.")
        with exclusive_file_lock(self.worker.root / f"reply-{item_id}", timeout=0):
            with exclusive_file_lock(self.worker.root / "worker", timeout=0):
                item = self.worker.status()["items"][item_id]
                reply = item.get("reply", {})
                if (confirmed is not True or not confirmation_token or not confirmation_digest
                    or not secrets.compare_digest(reply.get("confirmation_token", ""), confirmation_token)
                    or not secrets.compare_digest(reply.get("confirmation_digest", ""), confirmation_digest)
                    or item["proposal_digest"] != reply.get("proposal_digest")):
                    raise ValueError("Potvrzení neodpovídá konečnému příjemci a textu.")
                if reply["status"] == "smtp_sent":
                    return reply["receipt"]
                if reply["status"] == "sending":
                    self.worker._update(lambda d: d["items"][item_id]["reply"].update(status="delivery_unknown"))
                    raise ValueError("Předchozí pokus byl přerušený; nejdřív ověř jeho výsledek.")
                if reply["status"] != "prepared" or item["status"] not in {"awaiting_confirmation", "archived"}:
                    raise ValueError("Tento pokus nelze opakovat. Nejdřív ověř původní výsledek.")
                raw = base64.b64decode(reply["message_b64"], validate=True)
                current_fields = {**reply, "account": item["account"], "provider": item["provider"],
                                  "proposal_digest": item["proposal_digest"]}
                if _confirmation_digest(raw, current_fields) != confirmation_digest:
                    raise ValueError("Připravená zpráva se změnila.")
                config = self.config_loader(item["provider"])
                if config.address != reply["sender"] or config.provider != item["provider"]:
                    raise ValueError("Odesílací účet se změnil; připrav nové potvrzení.")
                self.worker._update(lambda d: d["items"][item_id]["reply"].update(status="sending"))
            try:
                outcome = self.transport(raw, config, reply["recipient"])
            except Exception as exc:
                outcome = ReplySMTPOutcome("delivery_unknown", error_type=type(exc).__name__)
            stamp = datetime.now(timezone.utc)
            receipt = {"status": outcome.status, "message_id": reply["message_id"],
                       "recipient": reply["recipient"], "sender": reply["sender"], "subject": reply["subject"],
                       "checked_at": stamp.isoformat(), "session_close_ok": outcome.session_close_ok,
                       "sent_copy_status": "pending" if outcome.status == "smtp_sent" else "not_attempted"}
            self.worker._update(lambda d: d["items"][item_id]["reply"].update(status=outcome.status, receipt=receipt))
            if outcome.status == "smtp_sent":
                try:
                    copy = self.sent_copy_saver(raw, config, stamp)
                    receipt.update(sent_copy_status=copy.status, sent_copy_provider=copy.provider, sent_copy_folder=copy.folder)
                except Exception:
                    receipt["sent_copy_status"] = "failed"
                self.worker._update(lambda d: d["items"][item_id]["reply"].update(receipt=receipt))
            return receipt
