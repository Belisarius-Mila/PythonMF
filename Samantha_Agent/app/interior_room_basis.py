"""One room-wide plan and user-entered measurements shared by all variants."""
from __future__ import annotations

import copy

from app.interior_atelier import AtelierConflict, AtelierError, _text

BLOCKING = {'queued', 'running', 'delivery_unknown', 'result_ready'}


def room_basis(room):
    return copy.deepcopy(room.get('room_basis', {'plan_source_id': '', 'measurements': '', 'revision': 0}))


def effective_sources(room, draft):
    return list(dict.fromkeys(i for i in [draft['image_source_id'], room_basis(room)['plan_source_id'], *draft['source_ids']] if i))


def save_room_basis(room, payload):
    current = room_basis(room)
    if type(payload['expected_basis_revision']) is not int or payload['expected_basis_revision'] != current['revision']:
        raise AtelierConflict('Společný půdorys nebo míry změnil jiný klient. Porovnej je s uloženým stavem.')
    plan_id = payload['plan_source_id']
    if not isinstance(plan_id, str) or plan_id and room['sources'].get(plan_id, {}).get('kind') != 'plan':
        raise AtelierError('Vyber půdorys této místnosti nahraný jako Náčrt nebo rozměry.')
    measurements = _text(payload['measurements'], 6000)
    if plan_id == current['plan_source_id'] and measurements == current['measurements']:
        return current['revision']
    if any(j['status'] in BLOCKING for j in room.get('ai_requests', {}).values()):
        raise AtelierConflict('Místnost má neukončený AI požadavek. Nejdříve ověř jeho původní výsledek.')
    room['room_basis'] = {'plan_source_id': plan_id, 'measurements': measurements, 'revision': current['revision'] + 1}
    return current['revision'] + 1


def detach_room_plan(room, asset_id):
    basis = room_basis(room)
    if basis['plan_source_id'] == asset_id:
        room['room_basis'] = {**basis, 'plan_source_id': '', 'revision': basis['revision'] + 1}
