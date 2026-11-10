"""Registered cockpit actions. Reads never start jobs; POSTs are explicit clicks."""
from __future__ import annotations

import threading

from app.science_news import ScienceNews, digest
from app.science_news_model import call_model, policy, TRANSLATION_INSTRUCTIONS, TRANSLATION_SCHEMA
from app.science_news_sources import reusable_full_text

WORKERS = threading.BoundedSemaphore(2)


def science_news_overview(*, store=None):
    try:
        store = store or ScienceNews()
        result = store.overview()
        result["schedule"] = "Pátek 09:00 · Europe/Prague"
        try:
            policy(store)
            result["activated"] = True
        except (OSError, ValueError):
            result["activated"] = False
        return result
    except (OSError, ValueError, TypeError, KeyError):
        return {"ok": False, "message": "ScienceNews nelze načíst; stav novinek není ověřený."}


def science_news_decision_action(payload, *, store=None):
    try:
        store = store or ScienceNews()
        if payload.get("action") == "save":
            item = store.item(payload.get("item_id"))
            if not item.get("translation"):
                started = bool(item.get("operation"))
                return {"ok": False, "state": "attention" if started else "translation_required",
                    "operation_started": started,
                    "message": "Pro uložení celé zprávy nejprve dokonči český překlad tlačítkem Přeložit celou zprávu. Samotný abstrakt neukládám."}
        return store.decide(payload.get("item_id"), payload.get("action"), payload.get("request_id"))
    except (OSError, ValueError, TypeError, KeyError):
        return {"ok": False, "message": "Rozhodnutí nebylo ověřeno. Zpráva zůstává ve frontě; ověř stejný požadavek."}


def science_news_unfollow_action(payload, *, store=None):
    try:
        return (store or ScienceNews()).unfollow(payload.get("topic_id"))
    except (OSError, ValueError, TypeError, KeyError):
        return {"ok": False, "message": "Změnu sledování se nepodařilo ověřit."}


def science_news_translation_status(item_id, *, store=None):
    try:
        store = store or ScienceNews()
        item = store.item(item_id)
        job = store._read()["jobs"].get("translation_" + item_id, {})
        if item.get("translation"):
            return {"ok": True, "state": "completed", "title": item["title"], "translation": item["translation"], "source_url": item["source_url"]}
        return {"ok": True, "state": job.get("state", "not_started"), "title": item["title"]}
    except (OSError, ValueError, TypeError, KeyError):
        return {"ok": False, "message": "Stav překladu nelze ověřit."}


def translate(store, item, *, model=call_model):
    key = "model_translation_" + item["id"]
    answer = model(store, key, {"source_text": item["source_text"]}, TRANSLATION_INSTRUCTIONS, TRANSLATION_SCHEMA)
    text = answer.get("translation", "")
    if (set(answer) != {"translation", "complete"} or answer["complete"] is not True
            or not isinstance(text, str) or not 0.3 * len(item["source_text"]) <= len(text) <= 4 * len(item["source_text"])):
        raise ValueError("Překlad není úplný; nelze jej vydávat za celý text.")
    with store.transaction() as state:
        current = state["items"][item["id"]]
        if digest(current.get("source_text")) != digest(item["source_text"]):
            raise ValueError("Zdrojový text se změnil.")
        current["translation"] = text


def science_news_translate_action(payload, *, store=None):
    store = store or ScienceNews()
    acquired = False
    try:
        item = store.item(payload.get("item_id"))
        if item.get("translation"):
            return {"ok": True, "state": "completed"}
        policy(store)
        if not item.get("source_text"):
            source_text, permission = reusable_full_text(item)
            with store.transaction() as state:
                state["items"][item["id"]].update(source_text=source_text, translation_permission=permission)
            item = store.item(item["id"])
        if not item.get("source_text") or item.get("translation_permission") not in ("cc-by", "cc-by-sa", "cc0", "public-domain", "user-provided"):
            return {"ok": False, "message": "Plný text a oprávnění k překladu zatím nejsou ověřené. Zdroj můžeš otevřít odkazem; abstrakt nevydávám za celý překlad."}
        acquired = WORKERS.acquire(blocking=False)
        if not acquired:
            return {"ok": False, "message": "Připravují se jiné překlady. Zkus později."}
        key = "translation_" + item["id"]
        with store.transaction() as state:
            if key in state["jobs"]:
                WORKERS.release()
                acquired = False
                return {"ok": True, "state": state["jobs"][key]["state"]}
            state["jobs"][key] = {"state": "running"}

        def worker():
            try:
                translate(store, item)
                status = "completed"
            except Exception:
                status = "attention"
            finally:
                try:
                    with store.transaction() as state:
                        state["jobs"][key]["state"] = status
                finally:
                    WORKERS.release()
        threading.Thread(target=worker, daemon=True).start()
        return {"ok": True, "state": "running"}
    except (OSError, ValueError, TypeError, KeyError):
        if acquired:
            WORKERS.release()
        return {"ok": False, "message": "Překlad zatím není aktivovaný nebo ověřený; další modelový pokus nespouštím."}
