"""Registered edit endpoint under the existing Cockpit access guards."""
from app.calendar_edit import CalendarEditing
from app.cockpit_calendar_agenda import AGENDA


def saved(before, after):
    try: AGENDA.follow_edit(before, after)
    finally: AGENDA.request_refresh(force=True)


EDITS = CalendarEditing(on_saved=saved)


def calendar_edit_action(payload):
    try: return EDITS.execute(payload)
    except ValueError as exc: return {'ok':False,'message':str(exc)}
    except Exception: return {'ok':False,'message':'Úpravu nelze potvrdit. Ověř pouze původní úpravu; neopakuj zápis.'}
