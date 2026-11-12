"""Explicit, revisioned human decisions. No model, network or outgoing action."""
from __future__ import annotations

import copy
from datetime import timezone

from app.work_repository import RepositoryMutation, WorkRepositoryError
from .followups import FollowupError, FollowupConflict, FOLLOWUP_ID, ITEM_ID, OPERATION, _space, _record, _text
from .followup_assessment import digest, suggestion_view, FollowupCandidate
from .followup_matching import trusted_evidence
from .followup_monitor import SOURCE_KEYS, _bump


def _audit(value, action, changes, at, operation):
    _bump(value, action, changes, at, operation)
    value["history"][-1]["operation_id"] = operation


def _source(document, value, identity, event):
    item = document["items"].get(identity)
    source = event.get("source", {})
    if (not item or item.get("account") != value["source"]["account"]
            or any(item.get(k) != source.get(k) for k in SOURCE_KEYS)
            or item.get("content_digest") != event.get("content_digest")):
        raise FollowupConflict("Podklad zprávy se změnil. Původní rozhodnutí nelze použít.")
    return item


def execute_review(service, command):
    if not isinstance(command, dict) or not isinstance(command.get("action"), str):
        raise FollowupError("Neplatné rozhodnutí o hlídání.")
    action = command.get("action")
    common = {"action", "id", "expected_revision", "operation_id", "confirmed"}
    allowed = common | ({"item_id", "source_digest", "decision"} if action == "resolve_binding" else {"suggestion_id"})
    if (set(command) != allowed or command["confirmed"] is not True
            or not isinstance(command["id"], str) or not FOLLOWUP_ID.fullmatch(command["id"])
            or type(command["expected_revision"]) is not int or command["expected_revision"] < 1
            or not isinstance(command["operation_id"], str) or not OPERATION.fullmatch(command["operation_id"])):
        raise FollowupError("Rozhodnutí vyžaduje přesný potvrzený podnět a revizi.")
    if action == "resolve_binding":
        if (not isinstance(command["decision"], str) or command["decision"] not in {"accept", "reject"}
                or any(not isinstance(command[k], str) or not ITEM_ID.fullmatch(command[k]) for k in ("item_id", "source_digest"))):
            raise FollowupError("Vyber přesnou zprávu a rozhodnutí o přiřazení.")
    elif action not in {"accept_suggestion", "reject_suggestion"} or not isinstance(command["suggestion_id"], str) or not ITEM_ID.fullmatch(command["suggestion_id"]):
        raise FollowupError("Vyber přesný obsahový návrh.")
    fingerprint = digest(command)
    at = service.clock().astimezone(timezone.utc).isoformat()

    def mutate(document):
        space = _space(document)
        old = space["operations"].get(command["operation_id"])
        if old:
            if set(old) != {"fingerprint", "followup_id", "revision"}:
                raise WorkRepositoryError("Neplatný doklad rozhodnutí.")
            if old["fingerprint"] != fingerprint:
                raise FollowupConflict("Stejná operace patří jinému rozhodnutí.")
            return RepositoryMutation(document, service._result(_record(space, old["followup_id"]), replay=True,
                                      operation_revision=old["revision"]), changed=False)
        value = _record(space, command["id"])
        if value["state"] != "active" or value["revision"] != command["expected_revision"]:
            raise FollowupConflict("Záležitost se mezitím změnila. Načti její aktuální stav.")
        related = []
        if action == "resolve_binding":
            identity = command["item_id"]
            observations = value.get("observations", {})
            event = observations.get("reviews", {}).get(identity)
            if (not event or event.get("generation") != value["generation"] or event.get("resolution")
                    or event.get("content_digest") != command["source_digest"]):
                raise FollowupConflict("Původní nejasná vazba už není otevřená.")
            item = _source(document, value, identity, event)
            if command["decision"] == "accept":
                for key in space["items"]:
                    other = _record(space, key)
                    if other["id"] != value["id"] and (other["source"]["item_id"] == identity
                            or identity in other.get("observations", {}).get("items", {})):
                        raise FollowupConflict("Zpráva už patří jiné záležitosti. Věci se automaticky neslučují.")
                observations["items"][identity] = {**copy.deepcopy(event), "decision":"human_linked", "human_confirmed":True}
                evidence = trusted_evidence(item)
                unique = evidence and sum(1 for other in document["items"].values()
                    if other.get("account") == item["account"] and (trusted_evidence(other) or {}).get("message_id") == evidence["message_id"]) == 1
                if unique:
                    if evidence["message_id"] not in observations["message_ids"]:
                        observations["message_ids"].append(evidence["message_id"])
                    observations["approved_senders"] = sorted(set(observations.get("approved_senders", [])) | {evidence["sender"]})
                    observations["approved_participants"] = sorted(set(observations.get("approved_participants", [])) | set(evidence["participants"]))
                for key in space["items"]:
                    other = _record(space, key)
                    review = other.get("observations", {}).get("reviews", {}).get(identity)
                    if (other["id"] != value["id"] and other["state"] == "active" and review
                            and review["generation"] == other["generation"] and not review.get("resolution")):
                        review["resolution"] = {"decision":"assigned_elsewhere", "at":at}
                        _invalidate_tracking(other)
                        _audit(other, "binding_decision", {"item_id":identity, "decision":"assigned_elsewhere"}, at, command["operation_id"])
                        related.append(other)
                value["assessment"] = {"version":1, "status":"manual_review", "source_item_id":identity,
                                       "source_digest":item["content_digest"], "attempt_id":""}
            event["resolution"] = {"decision":command["decision"], "at":at}
            _invalidate_tracking(value)
            changes = {"item_id":identity, "decision":command["decision"]}
            audit_action = "binding_decision"
        else:
            suggestion = suggestion_view(value)
            if (not suggestion or suggestion["attempt_id"] != command["suggestion_id"] or suggestion["status"] != "pending"):
                raise FollowupConflict("Obsahový návrh už neodpovídá aktuální záležitosti.")
            identity = suggestion["source_item_id"]
            event = value.get("observations", {}).get("items", {}).get(identity)
            if not event or event["generation"] != value["generation"]:
                raise FollowupConflict("Návrh nemá původní doloženou vazbu.")
            _source(document, value, identity, event)
            accepted = action == "accept_suggestion"
            changes = {"attempt_id":suggestion["attempt_id"], "decision":"accept" if accepted else "reject"}
            if accepted:
                candidate = FollowupCandidate.model_validate(suggestion["candidate"])
                if not candidate.next_step.strip() or not candidate.evidence:
                    raise FollowupError("Návrh nemá doložený další krok k převzetí.")
                # Completion is deliberately a separate explicit lifecycle action.
                changes.update(next_step=_text(candidate.next_step, 1000), waiting_on=candidate.waiting_on)
                value.update(next_step=changes["next_step"], waiting_on=changes["waiting_on"])
            value["suggestion"]["status"] = "accepted" if accepted else "rejected"
            audit_action = "suggestion_decision"
        _audit(value, audit_action, changes, at, command["operation_id"])
        space["operations"][command["operation_id"]] = {"fingerprint":fingerprint, "followup_id":value["id"], "revision":value["revision"]}
        from .followups import _view
        return RepositoryMutation(document, {**service._result(value, changed=True),
                                            "related_followups":[_view(v) for v in related]})
    return service.repository.transact(mutate).result


def _invalidate_tracking(value):
    tracking = value.get("tracking")
    if tracking:
        tracking.update(status="source_unverified", reason="binding_changed", check_key="")
        tracking["notice"].update(kind="source_unverified", review_item_ids=[])
