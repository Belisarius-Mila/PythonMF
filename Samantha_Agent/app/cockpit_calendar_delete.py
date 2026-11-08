"""Registered confirmed deletion endpoint, using existing origin/host guards."""
from app.calendar_delete import CalendarDeletion
from app.cockpit_calendar_agenda import AGENDA

DELETIONS = CalendarDeletion(on_deleted=lambda: AGENDA.request_refresh(force=True))


def calendar_delete_action(payload):
    try:
        return DELETIONS.execute(payload)
    except ValueError as exc:
        return {'ok':False,'message':str(exc)}
    except Exception:
        return {'ok':False,'message':'Výsledek není potvrzený. Ověř původní smazání; další smazání automaticky neopakuj.'}
