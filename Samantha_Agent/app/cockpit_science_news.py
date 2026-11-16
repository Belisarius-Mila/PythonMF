"""Registered cockpit actions. Reads never start jobs; POSTs are explicit clicks."""
from __future__ import annotations

import threading

from app.science_news import ScienceNews, digest
from app.science_news_model import call_model, policy, TRANSLATION_INSTRUCTIONS, TRANSLATION_SCHEMA
from app.science_news_sources import reusable_full_text, SourcePreparationError

WORKERS = threading.BoundedSemaphore(2)


def science_news_overview(*, store=None):
    try:
        store = store or ScienceNews()
        result = store.overview()
        from app.science_news_recovery import weekly_status
        result["schedule"] = "Pátek 09:00 · Europe/Prague"
        try:
            approved = policy(store)
            result["activated"] = True
        except (OSError, ValueError):
            result["activated"] = False
        from datetime import datetime
        result['preparation'] = weekly_status(store, enabled=result['activated'],
            activated_at=datetime.fromisoformat(approved['activated_at']) if result['activated'] else None)
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
        preparation = item.get('translation_preparation', {})
        result = {"ok": True, "state": job.get("state", preparation.get('state', "not_started")),
            "title": item["title"], 'source_url': item['source_url']}
        if job.get('message'):
            result['message'] = job['message']
        if job.get('part_count'):
            result['part_count'] = job['part_count']
            result['completed_parts'] = job.get('completed_parts', 0)
        if not job and preparation.get('message'):
            result['message'] = preparation['message']
            result['error_code'] = preparation.get('error_code')
        return result
    except (OSError, ValueError, TypeError, KeyError):
        return {"ok": False, "message": "Stav překladu nelze ověřit."}


def translate(store, item, *, model=call_model):
    if len(item['source_text']) > 20_000:
        from app.science_news_translation import translate_study
        return translate_study(store, item, model=model)
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
        key = "translation_" + item["id"]
        existing = store._read()['jobs'].get(key)
        if existing and existing.get('kind') not in ('translation_group', 'translation_pending'):
            return {'ok': True, 'state': existing['state']}

        def preparation(state, message, code=None):
            with store.transaction() as data:
                data['items'][item['id']]['translation_preparation'] = {
                    'state': state, 'message': message, 'error_code': code}

        def blocked(code, message):
            preparation('blocked', message, code)
            return {'ok': False, 'state': 'blocked', 'error_code': code,
                    'operation_started': False, 'message': message}

        if not item.get("source_text"):
            preparation('preparing_source', 'Načítám a ověřuji úplný zdrojový text…')
            try:
                source_text, permission = reusable_full_text(item)
            except SourcePreparationError as error:
                return blocked(error.code, str(error))
            with store.transaction() as state:
                state["items"][item["id"]].update(source_text=source_text, translation_permission=permission)
            item = store.item(item["id"])
        if not item.get("source_text") or item.get("translation_permission") not in ("cc-by", "cc-by-sa", "cc0", "public-domain", "user-provided"):
            return blocked('permission_unverified', "Plný text a oprávnění k překladu zatím nejsou ověřené. Zdroj můžeš otevřít odkazem; abstrakt nevydávám za celý překlad.")
        acquired = WORKERS.acquire(blocking=False)
        if not acquired:
            return blocked('busy', "Připravují se jiné překlady. Zkus později.")
        with store.transaction() as state:
            if key in state["jobs"]:
                if state['jobs'][key].get('kind') not in ('translation_group', 'translation_pending'):
                    WORKERS.release()
                    acquired = False
                    return {"ok": True, "state": state["jobs"][key]["state"]}
            else:
                state["jobs"][key] = {"state": "running", 'kind': 'translation_pending'}
            state['items'][item['id']].pop('translation_preparation', None)

        def worker():
            from app.science_news_translation import TranslationBusy, translate_study
            status = None
            try:
                translate_study(store, item)
                status = "completed"
            except TranslationBusy:
                return
            except Exception:
                status = "attention"
            finally:
                try:
                    if status is not None:
                        with store.transaction() as state:
                            if state['jobs'][key].get('kind') != 'translation_group':
                                state["jobs"][key]["state"] = status
                finally:
                    WORKERS.release()
        threading.Thread(target=worker, daemon=True).start()
        return {"ok": True, "state": "running"}
    except (OSError, ValueError, TypeError, KeyError):
        if acquired:
            WORKERS.release()
        return {"ok": False, "message": "Překlad zatím není aktivovaný nebo ověřený; další modelový pokus nespouštím."}
