"""Trusted server bridge bound to one already-authorized Human–Adam turn."""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
import threading
import time
import uuid

from app import simple_development as development
from app import luna_development
from app.communication import agent_roles as roles
from app.file_persistence import atomic_write_json


class PortalDelegation:
    def __init__(self, *, engine=development):
        self._lock = threading.Lock()
        self._grant = None
        self._engine = engine

    def issue(self, *, manager, service, workstream_id, client_message_id, writable):
        """Only ProfileManager may issue this after its existing write-intent gate."""
        with self._lock:
            self._grant = None
            if writable is not True or not client_message_id:
                return ''
            try:
                roles.load_role(roles.CONFIG_PATH, role=roles.DEVELOPMENT_ROLE)
            except roles.AgentRoleError:
                return ''
            token = secrets.token_hex(32)
            channel = development._private_dir(Path(service.workspace.canonical_private_root)
                                               / 'communication/simple_development' / uuid.uuid4().hex)
            self._grant = {'token': token, 'service': service, 'workstream_id': workstream_id,
                           'client_message_id': client_message_id,
                           'thread_id': str(service.hub.snapshot().get('thread_id') or ''),
                           'root': Path(service.workspace.project_root).resolve(),
                           'request_digest': None, 'result': None, 'channel': channel}
            threading.Thread(target=self._serve, args=(token, channel, manager), daemon=True).start()
            return {'token': token, 'channel': str(channel)}

    def revoke(self, ticket):
        token = ticket.get('token', '') if isinstance(ticket, dict) else ''
        with self._lock:
            if self._grant and hmac.compare_digest(self._grant['token'], str(token)):
                atomic_write_json(self._grant['channel'] / 'closed.json', {'state': 'closed'})
                self._grant = None

    def _serve(self, token, channel, manager):
        seen = set()
        while True:
            grant = self._grant
            if not grant or grant['token'] != token:
                return
            for path in sorted(channel.glob('*.request.json')):
                if path.name in seen:
                    continue
                seen.add(path.name)
                try:
                    if path.is_symlink() or path.stat().st_size > 64000 or len(seen) > 4:
                        raise ValueError('Invalid request')
                    result = self.dispatch(json.loads(path.read_bytes()), manager=manager)
                except Exception:
                    result = {'state': 'blocked', 'reason': 'Neplatná lokální žádost.'}
                response = path.with_name(path.name.replace('.request.json', '.response.json'))
                if not response.exists() and not response.is_symlink():
                    atomic_write_json(response, result)
                    response.chmod(0o600)
            time.sleep(.1)

    def dispatch(self, payload, *, manager):
        if not self._lock.acquire(blocking=False):
            return {'state': 'blocked', 'reason': 'Předání už probíhá; neopakovat.'}
        try:
            grant = self._grant
            if not isinstance(payload, dict) or not grant or not isinstance(payload.get('token'), str):
                raise ValueError('Missing grant')
            if not hmac.compare_digest(grant['token'], payload['token']):
                raise ValueError('Wrong grant')
            service = grant['service']
            session = service.hub.snapshot()
            active = session.get('active_turn') or {}
            if (manager.active_workstream_id != grant['workstream_id']
                    or manager.active_service is not service or not session.get('connected')
                    or not session.get('turn_busy') or session.get('thread_id') != grant['thread_id']
                    or active.get('client_message_id') != grant['client_message_id']
                    or Path(service.workspace.project_root).resolve() != grant['root']):
                raise ValueError('Expired or foreign turn')
            operation = payload.get('operation')
            if operation in ('preview', 'run') and set(payload) == {'token', 'operation', 'task'}:
                engine = self._engine
                if (engine is development and isinstance(payload['task'], dict)
                        and payload['task'].get('kind') == luna_development.KIND):
                    engine = luna_development
                if operation == 'preview':
                    return engine.preview(payload['task'], root=grant['root'])
                digest = hashlib.sha256(json.dumps(payload['task'], sort_keys=True).encode()).hexdigest()
                if grant['request_digest'] is not None:
                    if digest != grant['request_digest']:
                        raise ValueError('Only one task per authorized turn')
                    return grant['result'] or {'state': 'attention', 'reason': 'Předání se přerušilo; neopakovat.'}
                grant['request_digest'] = digest
                grant['engine'] = engine
                grant['result'] = engine.run(payload['task'], root=grant['root'], confirmed=True)
                return grant['result']
            if operation == 'review_anchors' and set(payload) == {'token', 'operation', 'job_id', 'answer_digest', 'corrections'}:
                result = grant['result'] or {}
                if (grant.get('engine') is not luna_development or result.get('state') != 'attention'
                        or result.get('job_id') != payload['job_id'] or grant.get('review_started')):
                    raise ValueError('Foreign or repeated integration review')
                grant['review_started'] = True
                grant['result'] = luna_development.review_anchors(payload['job_id'], payload['answer_digest'], payload['corrections'],
                                                                   root=grant['root'], confirmed=True)
                return grant['result']
            if operation == 'accept' and set(payload) == {'token', 'operation', 'job_id', 'candidate_digest'}:
                result = grant['result'] or {}
                if (result.get('state') not in ('ready_for_review', 'applied')
                        or result.get('job_id') != payload['job_id']
                        or result.get('candidate_digest') != payload['candidate_digest']):
                    raise ValueError('Foreign or unreviewable candidate')
                grant['result'] = grant.get('engine', self._engine).accept(payload['job_id'], payload['candidate_digest'],
                                                       root=grant['root'], confirmed=True)
                return grant['result']
            raise ValueError('Unsupported operation or fields')
        except Exception:
            return {'state': 'blocked', 'reason': 'Předání nepatří k jednomu právě povolenému vývojovému tahu.'}
        finally:
            self._lock.release()


def control_block(ticket):
    if not ticket:
        return ''
    return ('\n\n[SIMPLE_DEVELOPMENT]\n'
            'Při výslovném pokynu Míly předej vývoj Luně, i pro více souborů a jiné jazyky. '
            'Použij task kind="explicit_project_change", explicit_luna=true, request_id, goal, '
            'files a context (mapy relativních cest na seznamy [první,poslední] řádek; '
            'prázdný seznam ve files povoluje nový soubor), test_modules (nezměněné tests.test_*). '
            'Menší navazující úkoly připrav Adam; nepřebírej výslovně zadaný vývoj bez oznámení překážky. '
            'Starší čistá Python funkce dál používá původní schéma. Volej '
            'app.simple_development_portal.request(operation="run", token=..., channel=..., task=...). '
            'Nepouštěj další App Server z izolovaného workspace. Role se vybírá centrálně. '
            'Jeden výsledek zkontroluj a přijmi stejným nástrojem operation="accept", job_id a candidate_digest. '
            'Pouze nepřesnou citaci old můžeš po kontrole jednou opravit operation="review_anchors" '
            's job_id, answer_digest a corrections (mapa indexu změny jako textu na přesné old); '
            'new zůstává od Luny, další model se nevolá. '
            'Při blocked/attention oznam konkrétní překážku; neopakuj nejistý modelový krok. '
            'Čekání je programové bez modelového pollingu; checkpoint a publikace zůstávají v Cockpitu.\n'
            f'token={ticket["token"]}\nchannel={ticket["channel"]}\n[/SIMPLE_DEVELOPMENT]')


def request(operation, *, token, channel, **data):
    """Filesystem IPC works inside the existing network-disabled editor sandbox."""
    channel = Path(channel)
    if (not isinstance(token, str) or not re.fullmatch(r'[0-9a-f]{64}', token)
            or not channel.is_dir() or any(p.is_symlink() for p in (channel, *channel.parents))):
        raise ValueError('Chybí platný lokální kanál aktuálního tahu.')
    payload = json.dumps({'token': token, 'operation': operation, **data}, sort_keys=True).encode()
    if len(payload) > 64000:
        raise ValueError('Žádost překročila povolený rozsah.')
    identity = hashlib.sha256(payload).hexdigest()
    path = channel / (identity + '.request.json')
    response = channel / (identity + '.response.json')
    if path.exists():
        if path.is_symlink() or json.loads(path.read_bytes()) != json.loads(payload):
            raise ValueError('Žádost se změnila.')
    else:
        atomic_write_json(path, json.loads(payload))
        path.chmod(0o600)
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        if response.exists():
            if response.is_symlink() or response.stat().st_size > 512000:
                raise ValueError('Neplatná lokální účtenka.')
            return json.loads(response.read_bytes())
        if (channel / 'closed.json').exists():
            return {'state': 'blocked', 'reason': 'Vývojový tah už skončil.'}
        time.sleep(.2)
    return {'state': 'attention', 'reason': 'Předání čeká na ověření; neopakovat automaticky.'}
