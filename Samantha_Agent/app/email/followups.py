"""Manual email follow-up lifecycle. No IMAP, model, scheduler or outgoing actions."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone

from app.work_repository import JsonWorkRepository, RepositoryMutation, WorkRepositoryError
from .continuous_agent import ContinuousEmailAgent


VERSION = 1
FIELDS = {"title", "goal", "next_step", "waiting_on", "check_at"}
OPERATION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}\Z")
ITEM_ID = re.compile(r"[0-9a-f]{64}\Z")
FOLLOWUP_ID = re.compile(r"[0-9a-f]{32}\Z")


class FollowupError(ValueError):
    code = "invalid_request"


class FollowupConflict(FollowupError):
    code = "conflict"


class FollowupNotFound(FollowupError):
    code = "not_found"


def _text(value, limit, *, required=True):
    if (not isinstance(value, str) or len(value) > limit
            or any(ord(c) < 32 and c not in "\n\t" for c in value)):
        raise FollowupError("Text hlídání má neplatný formát nebo délku.")
    value = value.strip()
    if required and not value:
        raise FollowupError("Doplň název, cíl a další krok hlídání.")
    return value


def _instant(value):
    if not isinstance(value, str) or len(value) > 64:
        raise FollowupError("Čas kontroly musí obsahovat datum, čas a časové pásmo.")
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
        return parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise FollowupError("Čas kontroly musí obsahovat datum, čas a časové pásmo.") from None


def _fields(value):
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise FollowupError("Hlídání vyžaduje úplný název, cíl, další krok a čas kontroly.")
    if value["waiting_on"] not in ("me", "other", "review", "unknown"):
        raise FollowupError("Neplatný údaj, kdo je na řadě.")
    return {"title": _text(value["title"], 160), "goal": _text(value["goal"], 2000),
            "next_step": _text(value["next_step"], 1000), "waiting_on": value["waiting_on"],
            "check_at": _instant(value["check_at"]).isoformat()}


def _space(document, *, create=False):
    if "followups" not in document:
        empty = {"version": VERSION, "items": {}, "operations": {}}
        if create:
            document["followups"] = empty
        return empty
    value = document["followups"]
    if (not isinstance(value, dict) or type(value.get("version")) is not int
            or value["version"] != VERSION or not isinstance(value.get("items"), dict)
            or not isinstance(value.get("operations"), dict)):
        raise WorkRepositoryError("Neznámá nebo poškozená verze evidence hlídání.")
    return value


def _record(space, identity):
    if not isinstance(identity, str) or not FOLLOWUP_ID.fullmatch(identity):
        raise WorkRepositoryError("Poškozená identita hlídání.")
    try:
        value = space["items"][identity]
    except KeyError:
        raise FollowupNotFound("Záležitost nebyla nalezena.") from None
    if (not isinstance(value, dict) or value.get("id") != identity
            or value.get("state") not in ("active", "completed")
            or any(type(value.get(k)) is not int or value[k] < 1 for k in ("revision", "generation"))
            or not isinstance(value.get("source"), dict) or not isinstance(value.get("history"), list)):
        raise WorkRepositoryError("Poškozený záznam hlídání.")
    try:
        _fields({k: value[k] for k in FIELDS})
        for key in ("created_at", "updated_at"):
            _instant(value[key])
        if value["state"] == "completed":
            _instant(value["completed_at"])
        elif value.get("completed_at") != "":
            raise FollowupError("Neplatný stav dokončení.")
        if not isinstance(value["source"].get("item_id"), str) or not ITEM_ID.fullmatch(value["source"]["item_id"]):
            raise FollowupError("Neplatná vazba na zprávu.")
        expected_id = hashlib.sha256(("email-followup-v1:" + value["source"]["item_id"]).encode()).hexdigest()[:32]
        if expected_id != identity or not value["history"]:
            raise FollowupError("Neplatná identita nebo historie.")
        last = value["history"][-1]
        if (not isinstance(last, dict) or last.get("revision") != value["revision"]
                or last.get("generation") != value["generation"]):
            raise FollowupError("Neplatná historie.")
        if "observations" in value:
            observations = value["observations"]
            if (not isinstance(observations, dict) or not isinstance(observations.get("message_ids"), list)
                    or not all(isinstance(v, str) for v in observations["message_ids"])
                    or any(not isinstance(observations.get(k), dict) for k in ("items", "reviews"))):
                raise FollowupError("Neplatné vazby zpráv.")
            for bucket in ("items", "reviews"):
                for key, event in observations[bucket].items():
                    if (not isinstance(key, str) or not ITEM_ID.fullmatch(key) or not isinstance(event, dict)
                            or event.get("item_id") != key or type(event.get("generation")) is not int
                            or not 1 <= event["generation"] <= value["generation"]
                            or not isinstance(event.get("source"), dict)
                            or not isinstance(event.get("decision"), str)):
                        raise FollowupError("Neplatný doklad související zprávy.")
                    _instant(event["observed_at"])
        if "tracking" in value:
            tracking = value["tracking"]
            if (not isinstance(tracking, dict) or tracking.get("version") != 1
                    or tracking.get("status") not in {"source_binding_unverified", "binding_review",
                        "source_unverified", "related_message", "due_no_observed_reply", "waiting"}
                    or not isinstance(tracking.get("notice"), dict)):
                raise FollowupError("Neplatný doklad kontroly.")
            _instant(tracking["last_checked_at"]); _instant(tracking["next_check_slot"])
            if tracking["last_verified_at"]:
                _instant(tracking["last_verified_at"])
    except (FollowupError, KeyError):
        raise WorkRepositoryError("Poškozený obsah hlídání.") from None
    return value


def _view(value, runtime=None):
    monitoring = "not_connected"
    if runtime and runtime["configured"]:
        monitoring = "running" if runtime["worker_recent"] else "worker_unverified"
    return {**copy.deepcopy(value), "monitoring": monitoring}


class EmailFollowups:
    def __init__(self, worker=None, *, clock=None, source_factory=None):
        self.worker = worker or ContinuousEmailAgent()
        self.repository = self.worker.repository
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.source_factory = source_factory

    def overview(self, query=None):
        query = {} if query is None else query
        if (not isinstance(query, dict) or set(query) - {"id", "item_id"}
                or "item_id" in query and ("id" not in query or not isinstance(query["item_id"], str)
                                           or not ITEM_ID.fullmatch(query["item_id"]))):
            raise FollowupError("Neplatný dotaz na hlídání.")
        document = self.repository.read()
        space = _space(document)
        from .followup_monitor import runtime_view
        runtime = runtime_view(document, self.clock().astimezone(timezone.utc),
                               JsonWorkRepository(self.worker.root / "service_health.json").read())
        base = {"ok": True, "version": VERSION,
                "capabilities": {"manual_lifecycle": True,
                    "automatic_monitoring": runtime["worker_recent"], "monitor_version": 1},
                "monitor": runtime}
        if "id" in query:
            identity = query["id"]
            if not isinstance(identity, str) or not FOLLOWUP_ID.fullmatch(identity):
                raise FollowupError("Neplatná identita záležitosti.")
            value = _record(space, identity)
            return {**base, "followup": _view(value, runtime),
                    "source_message": self._source_message(document, value, query.get("item_id", ""))}
        values = [_view(_record(space, key), runtime) for key in space["items"]]
        return {**base, "active": sorted((v for v in values if v["state"] == "active"),
                                        key=lambda v: (v["check_at"], v["id"])),
                "completed": sorted((v for v in values if v["state"] == "completed"),
                                    key=lambda v: (v["completed_at"], v["id"]), reverse=True)}

    @staticmethod
    def _source_message(document, value, item_id=""):
        """Read the bound cached source on explicit detail access, never refetch it."""
        items = document.get("items", {})
        source = value["source"]
        if item_id and item_id != source["item_id"]:
            observations = value.get("observations", {})
            event = observations.get("items", {}).get(item_id) or observations.get("reviews", {}).get(item_id)
            if not event:
                raise FollowupNotFound("Zpráva nepatří k této záležitosti.")
            source = {"item_id": item_id, **event["source"]}
        item = items.get(source["item_id"]) if isinstance(items, dict) else None
        keys = ("account", "provider", "folder", "uidvalidity", "uid", "content_digest")
        if not isinstance(item, dict) or any(item.get(key) != source.get(key) for key in keys):
            return None
        header, message = item.get("header"), item.get("message")
        if not isinstance(header, dict) or not isinstance(message, dict) or not isinstance(message.get("body_text"), str):
            return None
        return {"header": {key: header[key] if isinstance(header.get(key), str) else ""
                           for key in ("sender", "subject", "date")}, "body_text": message["body_text"]}

    def execute(self, payload):
        if not isinstance(payload, dict):
            raise FollowupError("Neplatný požadavek hlídání.")
        command = copy.deepcopy(payload)
        action = command.get("action")
        if action == "verify_source":
            return self._verify_source(command)
        common = {"action", "operation_id"}
        if action == "create":
            expected = common | {"source_item_id", "fields"}
        elif action == "update":
            expected = common | {"id", "expected_revision", "fields"}
        elif action == "set_state":
            expected = common | {"id", "expected_revision", "state"}
            if "check_at" in command:
                expected.add("check_at")
        else:
            raise FollowupError("Neznámá operace hlídání.")
        if set(command) != expected:
            raise FollowupError("Požadavek obsahuje chybějící nebo nepovolené údaje.")
        operation_id = command["operation_id"]
        if not isinstance(operation_id, str) or not OPERATION.fullmatch(operation_id):
            raise FollowupError("Operace nemá platnou trvalou identitu.")
        if action == "create":
            source_id = command["source_item_id"]
            if not isinstance(source_id, str) or not ITEM_ID.fullmatch(source_id):
                raise FollowupError("Neplatná identita zdrojové zprávy.")
        else:
            if not isinstance(command["id"], str) or not FOLLOWUP_ID.fullmatch(command["id"]):
                raise FollowupError("Neplatná identita záležitosti.")
            if type(command["expected_revision"]) is not int or command["expected_revision"] < 1:
                raise FollowupError("Chybí platná očekávaná revize.")
        if "fields" in command:
            command["fields"] = _fields(command["fields"])
        if action == "set_state":
            if command["state"] not in ("active", "completed"):
                raise FollowupError("Neplatný stav záležitosti.")
            if "check_at" in command:
                if command["state"] != "active":
                    raise FollowupError("Nový čas patří k obnovení hlídání.")
                command["check_at"] = _instant(command["check_at"]).isoformat()
        fingerprint = hashlib.sha256(json.dumps(command, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        now = self.clock().astimezone(timezone.utc)

        def mutate(document):
            space = _space(document, create=True)
            # Domain journal survives generic repository operation-cache eviction.
            previous = space["operations"].get(operation_id)
            if operation_id in space["operations"]:
                if (not isinstance(previous, dict) or set(previous) != {"fingerprint", "followup_id", "revision"}
                        or type(previous.get("revision")) is not int):
                    raise WorkRepositoryError("Poškozená účtenka operace hlídání.")
                if previous["fingerprint"] != fingerprint:
                    raise FollowupConflict("Stejná operace již patří jinému zadání.")
                value = _record(space, previous["followup_id"])
                return RepositoryMutation(document, self._result(value, replay=True,
                    operation_revision=previous["revision"]), changed=False)
            if action == "create":
                identity = hashlib.sha256(("email-followup-v1:" + command["source_item_id"]).encode()).hexdigest()[:32]
                if any(command["source_item_id"] in v.get("observations", {}).get("items", {})
                       for v in space["items"].values()):
                    raise FollowupConflict("Zpráva už patří k existující záležitosti. Otevři její hlídání.")
                if identity in space["items"]:
                    value = _record(space, identity)
                    if any(value[k] != command["fields"][k] for k in FIELDS):
                        raise FollowupConflict("Tato zpráva již má hlídání. Otevři existující záležitost.")
                    changed = False
                else:
                    source = self._source(document, command["source_item_id"])
                    self._future(command["fields"]["check_at"], now)
                    value = {"id": identity, "source": source, **command["fields"],
                             "state": "active", "revision": 1, "generation": 1,
                             "created_at": now.isoformat(), "updated_at": now.isoformat(),
                             "completed_at": "", "history": []}
                    space["items"][identity] = value
                    changed = True
            else:
                value = _record(space, command["id"])
                if value["revision"] != command["expected_revision"]:
                    raise FollowupConflict("Záležitost se mezitím změnila. Načti její aktuální stav.")
                if action == "update":
                    if value["state"] != "active":
                        raise FollowupConflict("Před úpravou nejdřív obnov hlídání vyřízené záležitosti.")
                    if command["fields"]["check_at"] != value["check_at"]:
                        self._future(command["fields"]["check_at"], now)
                    changes = {k: v for k, v in command["fields"].items() if v != value[k]}
                else:
                    target = command["state"]
                    changes = {}
                    if target != value["state"]:
                        changes = {"state": target, "generation": value["generation"] + 1,
                                   "completed_at": now.isoformat() if target == "completed" else ""}
                        if target == "active":
                            check_at = command.get("check_at", value["check_at"])
                            self._future(check_at, now)
                            changes["check_at"] = check_at
                    elif "check_at" in command:
                        raise FollowupError("Čas aktivního hlídání změň úpravou záležitosti.")
                changed = bool(changes)
                if changed:
                    value.update(changes, revision=value["revision"] + 1, updated_at=now.isoformat())
            if changed:
                event_fields = {k: copy.deepcopy(value[k]) for k in FIELDS} if action == "create" else changes
                value["history"].append({"action": action, "operation_id": operation_id,
                    "at": now.isoformat(), "revision": value["revision"],
                    "generation": value["generation"], "changes": event_fields})
            space["operations"][operation_id] = {"fingerprint": fingerprint,
                "followup_id": value["id"], "revision": value["revision"]}
            return RepositoryMutation(document, self._result(value, changed=changed))

        # Do not use the generic cache: it would skip payload fingerprint checks.
        return self.repository.transact(mutate).result

    def _verify_source(self, command):
        """One explicitly requested original read; never baseline/history scan."""
        if (set(command) != {"action", "id", "expected_revision", "operation_id", "confirmed"}
                or command["confirmed"] is not True
                or not isinstance(command["id"], str) or not FOLLOWUP_ID.fullmatch(command["id"])
                or type(command["expected_revision"]) is not int or command["expected_revision"] < 1
                or not isinstance(command["operation_id"], str) or not OPERATION.fullmatch(command["operation_id"])):
            raise FollowupError("Ověření vyžaduje potvrzení původního zdroje a jeho revize.")
        digest = hashlib.sha256(json.dumps(command, sort_keys=True).encode()).hexdigest()
        def previous(space):
            old = space["operations"].get(command["operation_id"])
            if old:
                if old["fingerprint"] != digest:
                    raise FollowupConflict("Stejná operace patří jinému zadání.")
                return self._result(_record(space, old["followup_id"]), replay=True,
                                    operation_revision=old["revision"])
        snapshot = self.repository.read()
        space = _space(snapshot)
        old = previous(space)
        if old:
            return old
        value = _record(space, command["id"])
        if value["state"] != "active" or value["revision"] != command["expected_revision"]:
            raise FollowupConflict("Záležitost se změnila; ověř její aktuální stav.")
        item = snapshot["items"].get(value["source"]["item_id"])
        keys = ("account", "provider", "folder", "uidvalidity", "uid", "content_digest")
        if not item or any(item.get(k) != value["source"].get(k) for k in keys):
            raise FollowupConflict("Uložený zdroj neodpovídá původní zprávě.")
        from .followup_matching import trusted_evidence, header_evidence
        evidence = trusted_evidence(item)
        if evidence is None:
            from .continuous_source import IMAPAgentSource
            factory = self.source_factory or (lambda original: IMAPAgentSource(original["provider"], original["folder"]))
            try:
                observed = factory(copy.deepcopy(item)).read_item(copy.deepcopy(item))
                actual = {"account": observed.account, "provider": observed.source.provider,
                          "folder": observed.source.mailbox, "uidvalidity": observed.uidvalidity,
                          "uid": observed.source.uid, "content_digest": observed.content_digest}
                if any(actual[k] != value["source"][k] for k in keys):
                    raise ValueError()
                evidence = header_evidence(observed.source.original_eml)
            except Exception:
                raise FollowupError("Původní e-mail nelze přesně ověřit. Hlídání a zdrojové pozice zůstaly zachované.") from None
        if not evidence["verified"]:
            raise FollowupError("Původní e-mail nemá jednoznačné hlavičky pro bezpečné přiřazení.")
        now = self.clock().astimezone(timezone.utc).isoformat()
        def save(document):
            from .followup_monitor import bind_cached, _bump
            space = _space(document)
            replay = previous(space)
            if replay:
                return RepositoryMutation(document, replay, changed=False)
            current = _record(space, command["id"])
            original = document["items"].get(current["source"]["item_id"], {})
            if (current["state"] != "active" or current["revision"] != command["expected_revision"]
                    or any(original.get(k) != value["source"].get(k) for k in keys)):
                raise FollowupConflict("Záležitost se během ověřování změnila.")
            original["thread_evidence"] = evidence
            if not bind_cached(document, current):
                raise FollowupConflict("Vazbu původního zdroje nelze potvrdit.")
            _bump(current, "source_verified", {"thread_binding": "verified_headers"}, now, command["operation_id"])
            current["history"][-1]["operation_id"] = command["operation_id"]
            space["operations"][command["operation_id"]] = {"fingerprint": digest,
                "followup_id": current["id"], "revision": current["revision"]}
            return RepositoryMutation(document, self._result(current, changed=True))
        return self.repository.transact(save).result

    @staticmethod
    def _future(value, now):
        if _instant(value) <= now:
            raise FollowupError("Zvol nový čas kontroly v budoucnosti.")

    @staticmethod
    def _result(value, *, changed=False, replay=False, operation_revision=None):
        return {"ok": True, "followup": _view(value), "changed": changed,
                "idempotent_replay": replay,
                "operation_revision": value["revision"] if operation_revision is None else operation_revision}

    @staticmethod
    def _source(document, identity):
        items = document.get("items", {})
        if not isinstance(items, dict):
            raise WorkRepositoryError("Neplatný zdroj e-mailových karet.")
        item = items.get(identity)
        if not isinstance(item, dict):
            raise FollowupNotFound("Zdrojová zpráva nebyla nalezena.")
        proposal = item.get("proposal")
        if not isinstance(proposal, dict) or type(proposal.get("important", True)) is not bool:
            raise FollowupError("Zdrojová zpráva nemá platné uložené posouzení.")
        if (item.get("status") not in ("awaiting_confirmation", "archived")
                or not proposal.get("important", True)):
            raise FollowupConflict("Hlídání založ z dostupné důležité e-mailové karty.")
        keys = ("account", "provider", "folder", "uidvalidity", "uid", "content_digest")
        if any(not isinstance(item.get(k), str) or not item[k] or len(item[k]) > 1000 for k in keys):
            raise FollowupError("Zdrojová zpráva nemá úplnou uloženou identitu.")
        return {"item_id": identity, **{k: item[k] for k in keys}, "thread_binding": "pending"}
