"""Manual continuation from ONE proven completed receipt, never a turn retry.

prepare() is nonpaid. resume() binds the exact deterministic correction under
the existing human-approved job. Unknown/failed delivery, missing telemetry, another paid
turn or another recovery attempt cannot enter this path. Original files stay.
"""
from __future__ import annotations

import copy
from datetime import datetime
import json
import math
from pathlib import Path

from app import recovery_guide_full_pilot as f
from app import recovery_guide_maintainer as m
from app.file_persistence import atomic_create_text, atomic_write_json, exclusive_file_lock
from app.release_usage import normalize_usage, estimate_standard_credits
from app.recovery_guide_sources import canonical_json, digest


def _guard():
    f._guard()
    for name in ('receipt-recovery.json', 'receipt-recovery-attempt.json', 'receipt-recovery-controller', 'receipt-replay.json'):
        if (f.STATE / name).is_symlink():
            raise ValueError('receipt_recovery_alias')


def _implementation():
    return {**f._code(), 'app/recovery_guide_receipt_recovery.py': digest(Path(__file__).read_bytes())}


def _known():
    attempt = json.loads((f.STATE / 'attempt.json').read_text())
    parent = f._approved_packet(attempt['approval_digest'])
    packet = parent['packet']
    status = m.status(f.STATE / 'controller', attempt['slot'])
    if (attempt.get('state') != 'attention' or status.get('state') != 'attention'
            or status.get('model_calls') != 1 or status.get('completed_calls') != 1
            or status.get('coverage') != 0 or len(status.get('turns', [])) != 1
            or sorted(p.name for p in (f.STATE / 'turns').glob('*.json')) != ['01.json']):
        raise ValueError('receipt_recovery_only_one_completed_turn_allowed')
    path = f.STATE / 'turns/01.json'
    if path.is_symlink():
        raise ValueError('receipt_recovery_alias')
    raw = json.loads(path.read_text())
    receipt = raw.get('receipt', {})
    if (raw.get('state') != 'completed' or raw.get('phase') != 'inspect'
            or raw.get('unexpected_item_types') != [] or receipt.get('delivered') is not True
            or receipt.get('status') != 'completed' or receipt.get('turn_started_confirmed') is not True
            or receipt.get('user_item_count') != 1
            or receipt.get('client_message_id') != f.REQUEST + '-1'
            or not receipt.get('thread_id') or not receipt.get('turn_id')):
        raise ValueError('receipt_recovery_delivery_not_proven')
    usage = normalize_usage(receipt.get('thread_token_usage'))
    cost = estimate_standard_credits(m.MODEL, usage)
    limits = m.Limits(**packet['measurements']['limits'])
    duration = receipt.get('duration_ms')
    if (usage is None or cost is None or cost != status.get('credits')
            or usage['input_tokens'] > limits.input_tokens or usage['output_tokens'] > limits.inspection_reserve
            or type(duration) is not int or not 0 <= duration <= 90000 or cost > limits.run_credits):
        raise ValueError('receipt_recovery_usage_not_acceptable')
    names = packet['measurements']['shards'][0]['source_paths']
    by_name = {s['path']: s for s in packet['snapshot']['sources']}
    payload = {'original': packet['snapshot']['original'], 'sources': [by_name[n] for n in names]}
    if digest(canonical_json(payload)) != raw.get('payload_sha256'):
        raise ValueError('receipt_recovery_payload_changed')
    answer, correction = f.normalize_inspection(json.loads(receipt['answer']), payload)
    if correction is None:
        raise ValueError('receipt_recovery_not_the_exact_redundant_original_case')
    changed = {n for n, sha in f._code().items() if packet['implementation'].get(n) != sha}
    if changed - {'app/recovery_guide_full_pilot.py'}:
        raise ValueError('receipt_recovery_unrelated_implementation_change')
    return parent, status, raw, payload, answer, correction, cost, digest(path.read_bytes())


def prepare():
    """Freeze a nonpaid known-receipt checkpoint. Old job state stays intact."""
    _guard()
    with exclusive_file_lock(f.STATE / 'job', timeout=0):
        path = f.STATE / 'receipt-recovery.json'
        if path.exists():
            return public_card(json.loads(path.read_text()))
        if (f.STATE / 'receipt-recovery-attempt.json').exists():
            raise ValueError('receipt_recovery_already_attempted')
        parent, status, raw, payload, answer, correction, cost, raw_sha = _known()
        packet = copy.deepcopy(parent['packet'])
        packet['implementation'] = f._code()
        packet['measurements']['limits']['seconds'] -= math.ceil(raw['receipt']['duration_ms'] / 1000)
        if not f._current(packet) or f.calibration._protocol() != packet['protocol']:
            raise ValueError('receipt_recovery_inputs_changed')
        repair = {'request_id': f.REQUEST, 'parent_approval_digest': parent['approval_digest'],
            'packet': packet, 'slot': status['slot'], 'original_now': raw['receipt']['requested_at'],
            'known_receipt_sha256': raw_sha, 'known_turn_id': raw['receipt']['turn_id'],
            'known_payload_sha256': digest(canonical_json(payload)), 'correction': correction,
            'known_standard_credits': cost, 'accepted_existing_sources': len(answer['covered']),
            'remaining_sdk_turns': packet['measurements']['planned_calls'] - 1,
            'total_credit_limit': packet['measurements']['limits']['run_credits'],
            'implementation': _implementation(), 'automatic_retry': False, 'publication': False}
        envelope = {'repair': repair, 'approval_digest': digest(canonical_json(repair))}
        atomic_create_text(path, canonical_json(envelope))
        return public_card(envelope)


def public_card(envelope):
    repair = envelope['repair']
    return {k: v for k, v in repair.items() if k not in {'packet', 'implementation'}} | {
        'approval_digest': envelope['approval_digest'], 'state': 'known_receipt_checkpoint_ready',
        'source_count': len(repair['packet']['snapshot']['sources']),
        'snapshot_sha256': f.hydrate(repair['packet']['snapshot']).sha256,
        'remaining_credit_allowance': round(repair['total_credit_limit'] - repair['known_standard_credits'], 8),
        'model': m.MODEL, 'effort': 'medium', 'serviceTierForTurn': 'default', 'hard_billing_cap': False}


def _current(repair):
    path = f.STATE / 'turns/01.json'
    return (not path.is_symlink() and digest(path.read_bytes()) == repair['known_receipt_sha256']
            and _implementation() == repair['implementation'] and f._current(repair['packet'])
            and f.calibration._protocol() == repair['packet']['protocol'])


def resume(*, approved_digest: str, client_factory=None):
    """Explicit known-result continuation. Reuses turn 1 locally, SDK starts at 2.

    One recovery marker under the SAME job lock prevents a second continuation.
    Original run/refresh remain closed. No call to turn 1 or new paid job ID.
    """
    _guard()
    with exclusive_file_lock(f.STATE / 'job', timeout=0):
        envelope = json.loads((f.STATE / 'receipt-recovery.json').read_text())
        repair = envelope['repair']
        if approved_digest != envelope['approval_digest'] or approved_digest != digest(canonical_json(repair)):
            raise ValueError('receipt_recovery_exact_checkpoint_required')
        marker_path = f.STATE / 'receipt-recovery-attempt.json'
        controller = f.STATE / 'receipt-recovery-controller'
        if marker_path.exists():
            old = json.loads(marker_path.read_text())
            result = m.status(controller, repair['slot'])
            return {**(result if result['state'] != 'not_started' else old), 'replayed_receipt': True}
        if not _current(repair):
            raise ValueError('receipt_recovery_inputs_changed')
        _, _, raw, payload, accepted, correction, _, sha = _known()
        if sha != repair['known_receipt_sha256'] or correction != repair['correction']:
            raise ValueError('receipt_recovery_saved_result_changed')
        marker = {'state': 'reserved', 'request_id': f.REQUEST, 'approval_digest': approved_digest,
                  'slot': repair['slot'], 'paid_turns_already_known': 1, 'automatic_retry': False}
        atomic_create_text(marker_path, canonical_json(marker))
        try:
            with (client_factory or f.calibration._client)() as client:
                if f.calibration._runtime(client) != repair['packet']['runtime']:
                    raise ValueError('receipt_recovery_runtime_changed')
                reviewer = f.Reviewer(client, repair['packet'])
                reviewer.calls = 1  # SDK turn 1 already completed; never request it.
                steps = 0

                def call(next_payload, kind):
                    nonlocal steps
                    if not _current(repair):
                        raise ValueError('receipt_recovery_inputs_changed')
                    steps += 1
                    if steps == 1:
                        if kind != 'inspect' or digest(canonical_json(next_payload)) != repair['known_payload_sha256']:
                            raise ValueError('receipt_recovery_wrong_local_replay')
                        atomic_create_text(f.STATE / 'receipt-replay.json', canonical_json({
                            'kind': 'existing_completed_receipt_no_sdk_call', 'turn_id': repair['known_turn_id'],
                            'receipt_sha256': sha, 'normalization': correction}))
                        return {'answer': accepted, 'usage': raw['receipt']['thread_token_usage']}
                    return reviewer(next_payload, kind)

                result = m.run(f.hydrate(repair['packet']['snapshot']), state_dir=controller,
                    now=datetime.fromisoformat(repair['original_now']),
                    limits=m.Limits(**repair['packet']['measurements']['limits']),
                    count_tokens=f.Counter(repair['packet']['measurements']), call=call,
                    approved_snapshot=f.hydrate(repair['packet']['snapshot']).sha256,
                    assert_sources=lambda: _current(repair), confirmed=True, legacy_format=True)
        except Exception as exc:
            marker.update(state='attention', error_type=type(exc).__name__)
            result = marker
        marker['state'] = result['state']
        atomic_write_json(marker_path, marker)
        return result
