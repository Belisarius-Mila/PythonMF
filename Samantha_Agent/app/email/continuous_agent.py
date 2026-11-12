"""Restartable email -> model proposal -> confirmed archive, without a daemon.

Review state holds headers, proposals and full bodies of important messages.
The business archive is created solely by accept_archive(). No email is sent.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from difflib import SequenceMatcher
from email.utils import getaddresses
from pathlib import Path
import re
from threading import Event
from typing import Callable
import unicodedata
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from app.file_persistence import atomic_write_text, exclusive_file_lock
from app.work_repository import JsonWorkRepository, RepositoryMutation
from .archive_service import save_email_archive
from .continuous_source import ObservedEmail
from .proposal_policy import PROPOSAL_INSTRUCTIONS, load_reply_name, proposal_payload, signed_draft


DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data/private/continuous_agent"
IMPORTANCE_PREFERENCE_INSTRUCTIONS = (
    "importance_preferences obsahují výslovné přání uživatele: podobné zprávy od tohoto odesílatele "
    "zpravidla považovat za nedůležité. Je to vodítko, ne zákaz. Stále přečti celý obsah; "
    "novou konkrétní žádost o reakci, termín, platbu nebo jiný důležitý dopad posuď podle obsahu "
    "a v případě potřeby ponech important=true."
)


def importance_subject_key(subject: str) -> str:
    text = unicodedata.normalize("NFKC", subject).casefold().strip()
    text = re.sub(r"^(?:(?:re|fw|fwd|odp|přep|aw|wg)\s*(?:\[\d+\])?\s*:\s*)+", "", text)
    return " ".join("#" if token.isdecimal() else token for token in re.findall(r"[^\W_]+", text))


def _importance_sender(header: str) -> str:
    addresses = getaddresses([header])
    if len(addresses) != 1:
        # Decoding an RFC 2047 display name can expose its comma without
        # quotes. Recover only one final <mailbox>, with no other address or
        # group syntax in the display prefix; never discard a second sender.
        single = re.fullmatch(r'([^<>@:\r\n;"\\]+)<([^<>\r\n]+)>[ \t]*', header)
        if single and "," in single[1] and single[1].strip():
            mailbox = single[2].strip()
            if mailbox.count("@") == 1 and not any(c.isspace() for c in mailbox):
                addresses = getaddresses([mailbox])
    if len(addresses) != 1:
        raise ValueError("Preference vyžaduje jednoznačného odesílatele.")
    address = addresses[0][1].casefold()
    if address.count("@") != 1 or any(c.isspace() for c in address) or not all(address.split("@")):
        raise ValueError("Odesílatel nemá platnou e-mailovou adresu.")
    return address


def _similar_importance_subject(first: str, second: str) -> bool:
    if first == second:
        return True
    if min(len(first), len(second)) < 16:
        return False
    left, right = set(first.split()) - {"#"}, set(second.split()) - {"#"}
    common = left & right
    return (len(common) >= 2 and len(common) / len(left | right) >= 0.6
            and SequenceMatcher(None, first, second, autojunk=False).ratio() >= 0.82)


class ArchiveMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1)
    domain: str
    document_type: str
    counterparty: str
    tags: list[str]


class EmailProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    reply_draft: str
    archive_recommended: bool
    metadata: ArchiveMetadata
    important: bool = True
    reply_subject: str = ""


@dataclass(frozen=True)
class EmailAssessment:
    """Additive result; the saved/editable EmailProposal contract stays unchanged."""
    proposal: EmailProposal
    calendar_suggestion: dict


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def proposal_digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class ContinuousEmailAgent:
    def __init__(self, root: Path = DEFAULT_ROOT):
        self.root = Path(root)
        self.repository = JsonWorkRepository(self.root / "state.json", default={"sources": {}, "items": {}})

    def status(self) -> dict:
        """Read existing state; does not initialize storage or contact providers."""
        return self.repository.read()

    def _update(self, callback) -> None:
        def mutate(document):
            callback(document)
            return RepositoryMutation(document)
        self.repository.transact(mutate)

    def remember_low_importance(self, item_id: str) -> str:
        """Remember an explicit preference; leave the current card and mailbox alone."""
        with exclusive_file_lock(self.root / "worker", timeout=0):
            result = []
            def update(document):
                item = document["items"][item_id]
                if item["status"] not in {"awaiting_confirmation", "archived", "hourly_summary"}:
                    raise ValueError("Preferenci lze uložit z karty nebo hodinového přehledu zpráv.")
                sender = _importance_sender(item["header"]["sender"])
                subject = item["header"]["subject"]
                key = importance_subject_key(subject)
                if not any(c.isalpha() for c in key):
                    raise ValueError("Předmět neposkytuje dostatečný vzor pro budoucí zprávy.")
                identity = (item["account"], sender, key)
                preference_id = hashlib.sha256(repr(identity).encode()).hexdigest()
                preferences = document.setdefault("importance_preferences", {})
                old = preferences.get(preference_id, {})
                preferences[preference_id] = {
                    "account": item["account"], "sender": sender, "subject": subject,
                    "subject_key": key, "active": True,
                    "created_at": old.get("created_at", _now()), "updated_at": _now(),
                }
                result.append(preference_id)
            self._update(update)
            return result[0]

    def forget_importance_preference(self, preference_id: str) -> None:
        with exclusive_file_lock(self.root / "worker", timeout=0):
            self._update(lambda d: d["importance_preferences"][preference_id].update(
                active=False, updated_at=_now()))

    def matching_importance_preferences(self, observed: ObservedEmail) -> tuple[dict[str, str], ...]:
        try:
            sender = _importance_sender(observed.source.sender)
        except ValueError:
            return ()
        subject = importance_subject_key(observed.source.subject)
        preferences = self.status().get("importance_preferences", {})
        matches = [
            {"id": key, "sender": p["sender"], "subject": p["subject"], "preference": "prefer_low_importance"}
            for key, p in sorted(preferences.items(), key=lambda row: row[1]["updated_at"], reverse=True)
            if p["active"] and p["account"] == observed.account and p["sender"] == sender
            and _similar_importance_subject(p["subject_key"], subject)
        ]
        return tuple(matches[:5])

    def cycle(self, source, propose: Callable[[ObservedEmail], EmailProposal | EmailAssessment], *, limit: int = 10,
              cycle_at: datetime | None = None, should_stop: Callable[[], bool] = lambda: False) -> dict:
        """Process each identity once. First scan starts with oldest existing mail.

        A failed/interrupted model request remains visible and is never retried
        automatically. Later messages can proceed; the failed item retains its UID.
        """
        with exclusive_file_lock(self.root / "cycle", timeout=0):
            if should_stop():
                return {"health": "paused", "proposals": 0, "fetched": 0}
            state = self.status()
            cursor = state["sources"].get(source.key, {})
            try:
                scan = source.scan(cursor, limit=limit)
            except Exception as exc:
                self._update(lambda d: d["sources"].setdefault(source.key, {}).update(
                    checked_at=_now(), health="error", error=type(exc).__name__))
                return {"health": "error", "proposals": 0}
            created = 0
            hour = (cycle_at or datetime.now(timezone.utc)).astimezone(ZoneInfo("Europe/Prague")).replace(
                minute=0, second=0, microsecond=0).isoformat()
            for observed in scan.messages:
                if should_stop():
                    return {"health": "paused", "proposals": created, "fetched": len(scan.messages)}
                item_id = observed.item_id
                existing = self.status()["items"].get(item_id)
                if existing is None:
                    hints = self.matching_importance_preferences(observed)
                    item = {
                        "account": observed.account, "uidvalidity": observed.uidvalidity,
                        "uid": observed.source.uid, "folder": observed.source.mailbox,
                        "provider": observed.source.provider,
                        "hour": hour,
                        "header": {"sender": observed.source.sender, "subject": observed.source.subject,
                                   "date": observed.source.date, "provider": observed.source.provider},
                        "content_digest": observed.content_digest,
                        "importance_preference_ids": [hint["id"] for hint in hints],
                        "status": "analyzing", "created_at": _now(),
                    }
                    self._update(lambda d: d["items"].__setitem__(item_id, item))
                    try:
                        assessed = propose(replace(observed, importance_preferences=hints))
                        suggestion = assessed.calendar_suggestion if isinstance(assessed, EmailAssessment) else None
                        proposal = EmailProposal.model_validate(
                            assessed.proposal if isinstance(assessed, EmailAssessment) else assessed).model_dump()
                        if suggestion and suggestion['status'] == 'ready':
                            proposal['important'] = True  # A proposed meeting/deadline must remain visible.
                    except Exception as exc:
                        self._update(lambda d: d["items"][item_id].update(
                            status="analysis_failed", error=type(exc).__name__))
                    else:
                        visible_message = {"body_text": observed.source.body_text} if proposal["important"] else {}
                        def save_assessment(document):
                            document["items"][item_id].update(
                                status="awaiting_confirmation" if proposal["important"] else "hourly_summary",
                                message=visible_message, proposal=proposal,
                                proposal_digest=proposal_digest(proposal))
                            if suggestion is not None:
                                document["items"][item_id]['calendar_suggestion'] = suggestion
                            if proposal["important"] and document.get("pushcut", {}).get("enabled"):
                                event = document.setdefault("notification_hours", {}).setdefault(hour, {
                                    "status": "pending", "created_at": _now(), "item_ids": []})
                                event["item_ids"].append(item_id)
                        self._update(save_assessment)
                        created += 1
                elif existing["status"] == "analyzing":
                    self._update(lambda d: d["items"][item_id].update(status="analysis_interrupted"))
                self._update(lambda d: d["sources"].__setitem__(source.key, {
                    "uidvalidity": scan.uidvalidity, "after_uid": int(observed.source.uid),
                    "health": "ok", "checked_at": _now(),
                }))
            self._update(lambda d: d["sources"].setdefault(source.key, {}).update(
                health="ok", checked_at=_now(), error=""))
            return {"health": "ok", "proposals": created, "fetched": len(scan.messages)}

    def dismiss(self, item_ids: list[str], *, action: str) -> None:
        """Hide reviewed cards/summary rows locally; no mailbox operation exists here."""
        if action not in {"dismiss", "ignore"} or not item_ids or len(item_ids) > 1000:
            raise ValueError("Neplatná místní akce.")
        with exclusive_file_lock(self.root / "worker", timeout=0):
            def update(document):
                for item_id in item_ids:
                    item = document["items"][item_id]
                    if item.get("reply", {}).get("status") == "sending":
                        raise ValueError("Odeslání právě probíhá; vyčkej na výsledek.")
                    if item["status"] not in {"awaiting_confirmation", "hourly_summary", "dismissed", "ignored", "archived"}:
                        raise ValueError("Tuto položku nyní nelze vyřadit.")
                    item.update(status="dismissed" if action == "dismiss" else "ignored", dismissed_at=_now())
            self._update(update)

    def run(self, sources, propose, *, stop: Event, interval_seconds: float = 60, limit: int = 10) -> None:
        """Blocking service loop, independent of Cockpit; caller owns its lifecycle."""
        if interval_seconds <= 0:
            raise ValueError("Interval musí být kladný.")
        sources = tuple(sources)
        if not sources:
            raise ValueError("Je třeba alespoň jeden zdroj.")
        while not stop.is_set():
            for source in sources:
                if stop.is_set():
                    return
                self.cycle(source, propose, limit=limit)
            stop.wait(interval_seconds)

    def edit_proposal(self, item_id: str, proposal: EmailProposal, *, expected_digest: str) -> str:
        """An edited draft gets a new digest, invalidating confirmation of the old one."""
        with exclusive_file_lock(self.root / "worker", timeout=0):
            item = self.status()["items"][item_id]
            if (item["status"] not in {"awaiting_confirmation", "archived"}
                or item["proposal_digest"] != expected_digest
                or item.get("reply", {}).get("status") in {"sending", "smtp_sent", "delivery_unknown"}):
                raise ValueError("Návrh se změnil nebo už není připravený k úpravě.")
            value = EmailProposal.model_validate(proposal).model_dump()
            if item["status"] == "archived":
                for field in set(value) - {"reply_subject", "reply_draft"}:
                    if value[field] != item["proposal"].get(field):
                        raise ValueError("U uložené zprávy lze upravit pouze koncept odpovědi.")
            digest = proposal_digest(value)
            self._update(lambda d: d["items"][item_id].update(proposal=value, proposal_digest=digest))
            return digest

    def accept_archive(self, observed: ObservedEmail, *, confirmed_digest: str) -> dict:
        """Execute exactly the reviewed model proposal against the same full source.

        Caller supplies a freshly read message and the digest from the review UI.
        A complete archive is published by an atomic directory rename; after a
        crash its receipt is reconciled rather than creating another archive.
        """
        with exclusive_file_lock(self.root / "worker", timeout=0):
            item_id = observed.item_id
            item = self.status()["items"][item_id]
            if item.get("proposal_digest") != confirmed_digest or not confirmed_digest:
                raise ValueError("Potvrzení neodpovídá aktuálnímu návrhu.")
            if item["content_digest"] != observed.content_digest:
                raise ValueError("Obsah zdrojového e-mailu se změnil.")
            if item["status"] not in {"awaiting_confirmation", "saving", "archived"}:
                raise ValueError("Návrh nelze uložit v tomto stavu.")
            archive_root = self.root / "archive"
            target = archive_root / item_id
            if target.exists():
                receipt = json.loads((target / "receipt.json").read_text())
                if receipt["proposal_digest"] != confirmed_digest or receipt["content_digest"] != observed.content_digest:
                    raise ValueError("Existující archiv neodpovídá potvrzenému návrhu.")
            else:
                if item["status"] == "archived":
                    raise ValueError("Dříve uložený archiv chybí; je třeba kontrola.")
                self._update(lambda d: d["items"][item_id].update(status="saving"))
                archive_root.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(prefix=".prepare-", dir=archive_root) as staging:
                    result = save_email_archive(observed.source, directory=Path(staging))
                    atomic_write_text(result.path / "agent_metadata.json", json.dumps(item["proposal"], ensure_ascii=False))
                    receipt = {"item_id": item_id, "proposal_digest": confirmed_digest,
                               "content_digest": observed.content_digest, "archived_at": _now()}
                    atomic_write_text(result.path / "receipt.json", json.dumps(receipt))
                    result.path.rename(target)
            self._update(lambda d: d["items"][item_id].update(status="archived", receipt=receipt))
            return receipt


class SDKEmailProposer:
    """Model supplies meaning and metadata, without the old triage heuristics."""

    def __init__(self, model: str, *, runner=None, reply_name: str | None = None):
        if not model.strip():
            raise ValueError("Model musí být výslovně zvolený.")
        self.model, self.runner = model, runner
        self.reply_name = load_reply_name() if reply_name is None else reply_name

    def __call__(self, observed: ObservedEmail) -> EmailProposal:
        from agents import Agent, Runner, RunConfig

        agent = Agent(
            name="Průběžný e-mailový agent", model=self.model, output_type=EmailProposal,
            instructions=PROPOSAL_INSTRUCTIONS + " " + IMPORTANCE_PREFERENCE_INSTRUCTIONS,
        )
        source = proposal_payload(observed, self.reply_name)
        result = (self.runner or Runner.run_sync)(
            agent, json.dumps(source, ensure_ascii=False), max_turns=3,
            run_config=RunConfig(tracing_disabled=True),
        )
        proposal = EmailProposal.model_validate(result.final_output)
        proposal.reply_draft = signed_draft(proposal.reply_draft, self.reply_name)
        return proposal
