"""One reviewable image brief, proposed by chat and pinned by image approval."""
from __future__ import annotations

import json

from app.interior_atelier import AtelierError, _fingerprint, _text

BRIEF_PROTOCOL = "interior-brief-v1"
BLOCKING = {"queued", "running", "delivery_unknown", "result_ready"}
CHAT_RESPONSE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["answer", "brief"],
    "properties": {
        "answer": {"type": "string"},
        "brief": {"type": "object", "additionalProperties": False,
                  "required": ["changes", "preserve", "unresolved"], "properties": {
                      "changes": {"type": "string"}, "preserve": {"type": "string"},
                      "unresolved": {"type": "array", "items": {"type": "string"}}}},
    },
}
CHAT_BRIEF_INSTRUCTIONS = """
Rozhovor současně připravuje jeden návrh zadání pro příští obrázek. Vrať pouze
JSON podle schématu: answer je přirozená česká odpověď; brief.changes shrnuje
požadované změny, brief.preserve vše, co má zůstat, a brief.unresolved je seznam
dosud nerozhodnutých otázek. Vycházej z current_brief a přiloženého zadání.
Přenášej dohodnuté požadavky, neztrácej pevné podmínky. Pouhý dotaz nebo úvaha
„co kdyby“ není nové rozhodnutí: uveď ji v nejasnostech a požádej o upřesnění.
Podmínky zachování měň jen na výslovný požadavek, změnu jasně vysvětli v answer.
Pokud uživatel jen klade otázku, zachovej dosavadní návrh zadání. Při chybějícím
zadání nic nevymýšlej; prázdné changes a konkrétní unresolved jsou v pořádku.
Jde o návrh ke kontrole, nikoli o schválení generování. Obrázek nevytvářej.
"""
IMAGE_BRIEF_INSTRUCTIONS = """
Obrázek vytvářej výhradně ze schváleného approved_brief, pracovního obrázku,
vybraných referencí a kreslených poznámek. Historie diskuse není obrazové zadání.
changes jsou schválené změny a preserve podmínky zachování. unresolved nejsou
nová rozhodnutí: příslušné části ponech podle výchozího obrázku a neprezentuj
neověřené rozměry jako jisté. Nevymýšlej dodatečné změny z dřívějších úvah.
"""


def validate_brief(value):
    if not isinstance(value, dict) or set(value) != {"changes", "preserve", "unresolved"}:
        raise AtelierError("Souhrn architekta nemá úplný formát.")
    unresolved = value["unresolved"]
    if not isinstance(unresolved, list) or len(unresolved) > 20:
        raise AtelierError("Souhrn obsahuje nepovolený seznam nejasností.")
    return {"changes": _text(value["changes"], 12000), "preserve": _text(value["preserve"], 2000),
            "unresolved": [_text(item, 500, required=True) for item in unresolved]}


def parse_chat_answer(answer):
    try:
        value = json.loads(answer)
        if not isinstance(value, dict) or set(value) != {"answer", "brief"}:
            raise ValueError("shape")
        return _text(value["answer"], 100000, required=True), validate_brief(value["brief"])
    except (ValueError, TypeError) as error:
        raise AtelierError("Architekt nepředal ověřený souhrn zadání.") from error


def brief_basis(room, base_id, draft):
    return _fingerprint({"draft": {k: v for k, v in draft.items() if k != "revision"},
                         "notes": [n for n in room["notes"] if n["base_id"] == base_id]})


def brief_view(room, base_id, draft, project_id, room_id):
    jobs = list(room.get("ai_requests", {}).values())
    chats = [j for j in jobs if j["base_id"] == base_id and j.get("brief_protocol") == BRIEF_PROTOCOL
             and j["mode"] == "chat"]
    latest = max(enumerate(chats), key=lambda pair: (pair[1]["created_at"], pair[0]))[1] if chats else None
    parent = room["variants"].get(base_id, {})
    summary = {"changes": draft["prompt"], "preserve": draft["fixed_elements"],
               "unresolved": parent.get("brief_unresolved", [])}
    stale, reason, origin = False, "", "saved"
    fixed_changed = False
    if latest:
        candidate = latest.get("brief_proposal")
        if candidate:
            summary = candidate
            origin = "architect"
            stale = latest.get("applied_basis") != brief_basis(room, base_id, draft)
            fixed_changed = candidate["preserve"] != latest["context"].get("current_brief", {}).get("preserve", "")
        if latest["status"] != "completed" or not candidate:
            stale = True
            reason = ("Architekt ještě připravuje souhrn." if latest["status"] in BLOCKING else
                      "Poslední zpráva nemá ověřený souhrn. Upřesni zadání v rozhovoru.")
        elif stale:
            reason = "Podklady nebo rozpracovaná úprava se změnily. Nech architekta zadání upřesnit."
    selected = list(dict.fromkeys([draft["image_source_id"], *draft["source_ids"]]))
    selected = [i for i in selected if i]
    source = room["sources"].get(draft["image_source_id"])
    pending = any(j["base_id"] == base_id and j["status"] in BLOCKING for j in jobs)
    if not reason:
        if pending:
            reason = "Předchozí požadavek ještě nemá ověřený výsledek."
        elif not source:
            reason = "V Podkladech vyber pracovní obrázek."
        elif not summary["changes"].strip():
            reason = "Popiš architektovi požadované změny; připraví souhrn zadání."
        elif len(selected) > 6:
            reason = "Vyber nejvýše šest obrazových podkladů."
    token = _fingerprint({"protocol": BRIEF_PROTOCOL, "project_id": project_id, "room_id": room_id,
        "base_id": base_id, "draft": draft, "brief": summary,
        "proposal_id": latest["id"] if latest else "", "proposal_status": latest["status"] if latest else "",
        "files": {i: room["sources"][i]["files"] for i in selected if i in room["sources"]},
        "basis": brief_basis(room, base_id, draft)})
    return {**summary, "token": token, "revision": draft["revision"], "stale": stale,
            "can_generate": not bool(reason), "reason": reason, "origin": origin,
            "proposal_id": latest["id"] if latest else "", "fixed_changed": fixed_changed,
            "working_image": source["title"] if source else "",
            "references": [room["sources"][i]["title"] for i in selected if i in room["sources"] and i != draft["image_source_id"]],
            "source_count": len(selected),
            "drawing_count": len(draft["annotations"])}
