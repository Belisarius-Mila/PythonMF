"""Read-only install identity for the main Cockpit, separate from task entry."""
import json
from http import HTTPStatus

MANIFEST_PATH = '/cockpit.webmanifest'
MANIFEST = {'id':'/', 'name':'Samantha Cockpit', 'short_name':'Cockpit',
            'start_url':'/', 'scope':'/', 'display':'standalone', 'lang':'cs',
            'background_color':'#f5f7fa', 'theme_color':'#245ccd'}


def cockpit_manifest_route(parsed, responder):
    if parsed.path != MANIFEST_PATH:
        return False
    if parsed.query:
        responder.respond_json({'ok':False,'message':'Neplatný požadavek.'},status=HTTPStatus.BAD_REQUEST)
        return True
    data=json.dumps(MANIFEST,ensure_ascii=False).encode('utf-8')
    responder.send_response(HTTPStatus.OK)
    responder.send_header('Content-Type','application/manifest+json')
    responder.send_header('Content-Length',str(len(data)))
    responder.send_header('Cache-Control','no-store')
    responder.send_header('X-Content-Type-Options','nosniff')
    responder.end_headers();responder.wfile.write(data)
    return True
