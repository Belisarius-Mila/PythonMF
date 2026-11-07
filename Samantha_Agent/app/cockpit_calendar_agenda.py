"""Dashboard calendar endpoints within the existing Cockpit host/origin guards."""
from app.calendar_agenda import CalendarAgenda

AGENDA = CalendarAgenda()


def calendar_agenda_status():
    try: return AGENDA.snapshot()
    except Exception: return {'ok':False,'message':'Přehled kalendáře nyní nelze načíst.'}


def calendar_agenda_action(payload):
    try: return AGENDA.execute(payload)
    except ValueError as exc: return {'ok':False,'message':str(exc)}
    except Exception: return {'ok':False,'message':'Přehled nyní nelze aktualizovat. Zkus jej obnovit později.'}
