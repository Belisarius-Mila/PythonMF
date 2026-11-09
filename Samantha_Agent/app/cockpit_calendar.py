"""Calendar overview routes within Cockpit's existing host/origin boundary."""
from http import HTTPStatus
import subprocess

from app.calendar_access_pilot import CalendarPilotError
from app.calendar_agenda import CalendarAgenda
from app.calendar_overview import CalendarOverview, CalendarOverviewError, CalendarSelectionConflict
from app.cockpit_frontend import CALENDAR_OVERVIEW_HTML
from app.file_persistence import FilePersistenceError


def calendar_overview_action(payload, *, store=None):
    try:
        overview = store or CalendarOverview()
        value = overview.execute(payload)
        return CalendarAgenda(overview).display_overview(value)
    except CalendarSelectionConflict as exc:
        return {"ok": False, "error": "conflict", "message": str(exc)}
    except CalendarOverviewError as exc:
        return {"ok": False, "error": "invalid_request", "message": str(exc)}
    except (OSError, ValueError, CalendarPilotError, FilePersistenceError, subprocess.SubprocessError):
        return {"ok": False, "error": "unavailable", "message": "Kalendáře nejsou dostupné. Kolize nejsou ověřené. Obnov přehled a případně povol přístup na Macu."}


class CalendarOverviewRoutes:
    def dispatch(self, *, parsed, responder):
        if parsed.path not in {"/calendar/", "/api/calendar/overview"}:
            return False
        if parsed.query:
            responder.respond_json({"ok": False, "message": "Neplatný požadavek."}, status=HTTPStatus.BAD_REQUEST)
        elif parsed.path == "/calendar/":
            responder.respond_html(CALENDAR_OVERVIEW_HTML)
        else:
            try:
                overview = CalendarOverview()
                responder.respond_json(CalendarAgenda(overview).display_overview(overview.snapshot()))
            except (OSError, ValueError, CalendarPilotError):
                responder.respond_json({"ok": False, "message": "Uložený přehled není dostupný. Kolize nejsou ověřené."}, status=HTTPStatus.CONFLICT)
        return True
