"""Task entry page and private actions inside Cockpit's existing access guards."""
import json
from http import HTTPStatus

from app.calendar_tasks import CalendarTasks
from app.cockpit_calendar_agenda import AGENDA
from app.cockpit_frontend import CALENDAR_TASK_HTML, FRONTEND_ROOT

TASKS = CalendarTasks(on_saved=lambda: AGENDA.request_refresh(force=True))
BASE = '/calendar/task/'
MANIFEST = {'id': BASE, 'name': 'Zadání úkolu · Samantha', 'short_name': 'Nový úkol',
            'start_url': BASE, 'scope': BASE, 'display': 'standalone', 'lang': 'cs',
            'background_color': '#f5f7fa', 'theme_color': '#245ccd',
            'icons': [{'src': BASE+'icon.svg', 'sizes': 'any', 'type': 'image/svg+xml'},
                      {'src': BASE+'icon-180.png', 'sizes': '180x180', 'type': 'image/png'}]}


def calendar_task_status():
    try:
        return TASKS.context()
    except Exception:
        return {'ok': False, 'message': 'Nastavení kalendáře nyní nelze načíst.'}


def calendar_task_action(payload):
    try:
        return TASKS.execute(payload)
    except ValueError as error:
        return {'ok': False, 'message': str(error)}
    except Exception:
        return {'ok': False, 'message': 'Výsledek není potvrzený. Uchovej zadání a ověř pouze původní zápis.'}


def task_page_route(parsed, responder):
    assets = {BASE+'manifest.webmanifest': ('application/manifest+json', json.dumps(MANIFEST, ensure_ascii=False).encode()),
              BASE+'icon.svg': ('image/svg+xml', None), BASE+'icon-180.png': ('image/png', None)}
    if parsed.path not in {BASE, *assets}:
        return False
    if parsed.query:
        responder.respond_json({'ok': False, 'message': 'Neplatný požadavek.'}, status=HTTPStatus.BAD_REQUEST)
    elif parsed.path == BASE:
        responder.respond_html(CALENDAR_TASK_HTML)
    else:
        mime, data = assets[parsed.path]
        if data is None:
            data = (FRONTEND_ROOT/'calendar_task'/parsed.path.rsplit('/', 1)[1]).read_bytes()
        responder.send_response(HTTPStatus.OK)
        responder.send_header('Content-Type', mime)
        responder.send_header('Content-Length', str(len(data)))
        responder.send_header('Cache-Control', 'no-store')
        responder.send_header('X-Content-Type-Options', 'nosniff')
        responder.end_headers()
        responder.wfile.write(data)
    return True
