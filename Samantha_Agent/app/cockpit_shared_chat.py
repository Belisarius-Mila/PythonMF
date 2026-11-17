"""Shared-chat HTTP adapter under Cockpit's existing host/origin checks."""
from http import HTTPStatus

from app.shared_chat import SharedChat, ChatError
from app.cockpit_frontend import SHARED_CHAT_HTML

CHAT = SharedChat()


def shared_chat_status(token, editor_id, *, service=None):
    if not token:
        return {'ok': True, 'needs_setup': True}
    try:
        return (service or CHAT).status(token, editor_id)
    except ChatError as error:
        return {'ok': False, 'message': str(error)}
    except Exception:
        return {'ok': False, 'message': 'Rozhovor nelze ověřit. Zachovej rozepsaný text a obnov přehled.'}


def shared_chat_action(payload, *, peer='local', service=None):
    try:
        return (service or CHAT).execute(payload, peer=peer)
    except ChatError as error:
        return {'ok': False, 'message': str(error)}
    except Exception:
        return {'ok': False, 'message': 'Výsledek není ověřený. Obnov stav původní zprávy; novou kopii neodesílej.'}


def shared_chat_get(parsed, responder):
    if parsed.path not in ('/samantha/', '/api/samantha-chat/state', '/api/samantha-chat/library/item'):
        return False
    if parsed.path == '/api/samantha-chat/library/item':
        from urllib.parse import parse_qs
        try:
            query = parse_qs(parsed.query, keep_blank_values=True)
            if set(query) - {'id', 'offset', 'sha256'} or any(len(v) != 1 for v in query.values()):
                raise ValueError()
            result = CHAT.library_detail(responder.headers.get('X-Samantha-Client', ''),
                responder.headers.get('X-Samantha-Editor', ''), query.get('id', [''])[0],
                int(query.get('offset', ['0'])[0]), query.get('sha256', [''])[0])
        except Exception:
            result = {'ok': False, 'message': 'Položku nelze ověřit. Obnov výběr v tomto rozhovoru.'}
        responder.respond_json(result, status=HTTPStatus.OK if result['ok'] else HTTPStatus.BAD_REQUEST)
        return True
    if parsed.query:
        responder.respond_json({'ok': False, 'message': 'Neplatný požadavek.'}, status=HTTPStatus.BAD_REQUEST)
    elif parsed.path == '/samantha/':
        responder.respond_html(SHARED_CHAT_HTML)
    else:
        result = shared_chat_status(responder.headers.get('X-Samantha-Client', ''),
                                    responder.headers.get('X-Samantha-Editor', ''))
        responder.respond_json(result, status=HTTPStatus.OK if result['ok'] else HTTPStatus.BAD_REQUEST)
    return True
