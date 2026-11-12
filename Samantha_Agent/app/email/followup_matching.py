"""Conservative header evidence. A match is never proof of content or delivery."""
from __future__ import annotations

import hashlib
import re
from email import policy
from email.parser import BytesHeaderParser
from email.utils import getaddresses

TOKEN = re.compile(r"<([A-Za-z0-9.!#$%&'*+\-/=?^_`{|}~]+)@([A-Za-z0-9][A-Za-z0-9._-]*)>")


def _ids(values, *, single=False):
    if len(values) > 1:
        raise ValueError("duplicate_header")
    text = str(values[0]) if values else ""
    if len(text) > 16000:
        raise ValueError("oversized_header")
    matches = list(TOKEN.finditer(text))
    if TOKEN.sub("", text).strip() or len(matches) > 100 or (single and len(matches) != 1):
        raise ValueError("invalid_message_id")
    return list(dict.fromkeys("<" + m[1] + "@" + m[2].lower() + ">" for m in matches))


def _addresses(values):
    result = []
    addresses = []
    for value in values:
        if getattr(value, "defects", ()):
            raise ValueError("invalid_participant")
        if hasattr(value, "addresses"):
            addresses.extend(v.addr_spec for v in value.addresses)
        else:
            addresses.extend(address for _, address in getaddresses([str(value)]))
    for address in addresses:
        if (address.count("@") != 1 or not all(address.split("@"))
                or len(address) > 320 or any(c.isspace() or ord(c) < 33 for c in address)):
            raise ValueError("invalid_participant")
        local, domain = address.rsplit("@", 1)
        address = local + "@" + domain.lower()
        result.append(address)
    if len(result) > 100:
        raise ValueError("oversized_participants")
    return sorted(set(result))


def header_evidence(raw: bytes) -> dict:
    """No body copy; exact raw digest binds this small index to its origin."""
    result = {"version": 1, "verified": False, "reason": "invalid_headers"}
    if not isinstance(raw, bytes):
        return result
    result["content_digest"] = hashlib.sha256(raw).hexdigest()
    header = re.split(br"\r?\n\r?\n", raw, maxsplit=1)[0]
    if len(header) > 65536:
        return result
    try:
        message = BytesHeaderParser(policy=policy.default).parsebytes(header + b"\r\n\r\n")
        if message.defects:
            raise ValueError("invalid_headers")
        identity = _ids(message.get_all("Message-ID", []), single=True)[0]
        parent = _ids(message.get_all("In-Reply-To", []))
        references = _ids(message.get_all("References", []))
        senders = message.get_all("From", [])
        if len(senders) != 1:
            raise ValueError("invalid_sender")
        sender = _addresses(senders)
        recipients = _addresses(message.get_all("To", []) + message.get_all("Cc", []))
        if len(sender) != 1 or not recipients:
            raise ValueError("invalid_participant")
        return {**result, "verified": True, "reason": "", "message_id": identity,
                "in_reply_to": parent, "references": references, "sender": sender[0],
                "participants": sorted(set(sender + recipients))}
    except (ValueError, TypeError, IndexError):
        return result


def trusted_evidence(item: dict) -> dict | None:
    value = item.get("thread_evidence")
    if (not isinstance(value, dict) or value.get("version") != 1 or value.get("verified") is not True
            or value.get("content_digest") != item.get("content_digest")
            or not isinstance(value.get("message_id"), str) or not TOKEN.fullmatch(value["message_id"])
            or any(not isinstance(value.get(k), list) for k in ("participants", "in_reply_to", "references"))
            or not isinstance(value.get("sender"), str)
            or not all(isinstance(v, str) for v in value["participants"])
            or any(not isinstance(v, str) or not TOKEN.fullmatch(v)
                   for k in ("in_reply_to", "references") for v in value[k])):
        return None
    return value


def binding_candidates(document: dict, item_id: str, followups: list[dict]) -> tuple[list[str], str]:
    """Return affected IDs and one conservative decision, in the same account."""
    item = document["items"][item_id]
    evidence = trusted_evidence(item)
    account = item["account"]
    scoped = [v for v in followups if v["source"]["account"] == account
              and v["source"]["item_id"] != item_id]
    def manual_candidates():
        def subject(header):
            return re.sub(r"^(?:(?:re|fw|fwd|odp)\s*:\s*)+", "", header.get("subject", "").strip(), flags=re.I).casefold()
        header = item.get("header", {})
        return [v["id"] for v in scoped if v["state"] == "active" and subject(header) and
                subject(document["items"].get(v["source"]["item_id"], {}).get("header", {})) == subject(header)]
    if not evidence:
        return manual_candidates(), "unverified_headers"
    links = set(evidence["in_reply_to"] + evidence["references"])
    def known_ids(value):
        known = set(value.get("observations", {}).get("message_ids", []))
        original = document["items"].get(value["source"]["item_id"], {})
        root = trusted_evidence(original)
        if (root and original.get("account") == value["source"]["account"]
                and root["content_digest"] == value["source"]["content_digest"]):
            known.add(root["message_id"])
        return known
    affected = []
    for value in scoped:
        known = known_ids(value)
        if links & known or evidence["message_id"] in known:
            affected.append(value)
    if not affected:
        return manual_candidates(), "unproven_thread"
    identities = [v["id"] for v in affected if v["state"] == "active"]
    if not identities:
        return [], "closed_matter"
    if len(affected) != 1:
        return identities, "ambiguous_thread"
    # Every referenced Message-ID must identify at most one stored message.
    for identity in links | {evidence["message_id"]}:
        if sum(1 for other in document["items"].values() if other.get("account") == account
               and (trusted_evidence(other) or {}).get("message_id") == identity) > 1:
            return identities, "duplicate_message_id"
    value = affected[0]
    known = known_ids(value)
    anchor = trusted_evidence(document["items"].get(value["source"]["item_id"], {}))
    if not anchor or value["source"].get("thread_binding") != "verified_headers":
        return identities, "unverified_source"
    if (evidence["message_id"] in known or len(evidence["in_reply_to"]) > 1
            or evidence["in_reply_to"] and not set(evidence["in_reply_to"]) <= known):
        return identities, "conflicting_parent"
    approved = value.get("observations", {})
    senders = {anchor["sender"]} | set(approved.get("approved_senders", []))
    participants = set(anchor["participants"]) | set(approved.get("approved_participants", []))
    if (evidence["sender"] not in senders or not set(evidence["participants"]) <= participants):
        return identities, "participants_changed"
    return identities, "linked"
