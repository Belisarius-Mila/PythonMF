"""Explicit, private email calendar suggestions under Cockpit access checks."""
from app.email.calendar_draft import CalendarDraftService

CALENDAR_DRAFTS=CalendarDraftService()


def email_calendar_draft_status(item_id, *, service=None):
    try:
        return (service or CALENDAR_DRAFTS).status(item_id)
    except Exception:
        return {'ok':False,'message':'Návrh není dostupný pro tuto zprávu. Obnov kartu; nový modelový pokus nebyl spuštěn.'}


def email_calendar_draft_action(payload, *, service=None):
    try:
        return (service or CALENDAR_DRAFTS).execute(payload)
    except ValueError as exc:
        return {'ok':False,'message':str(exc)}
    except Exception:
        return {'ok':False,'message':'Výsledek operace není potvrzený. Obnov stav stejného návrhu; modelový pokus neopakuj.'}
