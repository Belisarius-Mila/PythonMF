"""Isolated TWO-turn anchor compatibility trial. prepare() never invokes a model.

Only trusted human approval of an exact private packet permits run(). One
fixed durable job across all pre-attempt revisions; no resume/reset/retry API.
No writer, scheduler, role activation, production client or old job changes.
"""
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from app import recovery_guide_trial as calibration
from app import recovery_guide_full_pilot as old
from app import recovery_guide_anchor_costing as cost
from app import recovery_guide_anchor_protocol as protocol
from app.recovery_guide_anchor_transport import StandardTurn
from app.recovery_guide_anchors import Catalogue
from app.recovery_guide_costing import hydrate
from app.recovery_guide_revision import collect_revision
from app.recovery_guide_sources import canonical_json, digest
from app.release_usage import normalize_usage, estimate_standard_credits
from app.file_persistence import atomic_create_text, atomic_write_json, exclusive_file_lock

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.venv/recovery_rec06_anchor_trial'
ORIGINAL = Path.home() / 'Desktop/OBNOVA_SAMANTHY_NOVY_MAC.txt'
REQUEST = 'rec06-anchors-small-01'


def _now():
    return datetime.now(timezone.utc).isoformat()


def _guard():
    if any(p.is_symlink() for p in (STATE, *STATE.parents)):
        raise ValueError('anchor_state_alias')
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    if STATE.stat().st_uid != os.getuid() or STATE.stat().st_mode & 0o077:
        raise ValueError('anchor_state_not_private')
    for name in ('job.lock', 'packet.json', 'revisions', 'attempt.json', 'context',
                 'turns', 'turns/01.json', 'turns/02.json', 'context/1', 'context/2'):
        if (STATE / name).is_symlink():
            raise ValueError('anchor_artifact_alias')
    if (STATE / 'revisions').exists() and any(p.is_symlink() for p in (STATE / 'revisions').iterdir()):
        raise ValueError('anchor_revision_alias')


def _head():
    return old._head()  # Git object ref through THIS checkout, never another worktree.


def _code():
    names = ('app/recovery_guide_anchor_trial.py', 'app/recovery_guide_anchor_transport.py',
        'app/recovery_guide_anchor_costing.py', 'app/recovery_guide_anchors.py',
        'app/recovery_guide_anchor_protocol.py', 'app/recovery_guide_revision.py',
        'app/recovery_guide_sources.py', 'app/recovery_guide_costing.py',
        'app/recovery_guide_quality.py', 'app/recovery_guide_maintainer.py',
        'app/recovery_guide_trial.py', 'app/recovery_guide_full_pilot.py',
        'app/routine_tasks.py', 'app/codex_appserver.py', 'app/file_persistence.py',
        'app/release_usage.py', 'app/communication/luna_release.py',
        'app/communication/agent_roles.py', 'config/agent_roles.json')
    return {n: digest((ROOT / n).read_bytes()) for n in names}


def _snapshot(head):
    whole = collect_revision(ORIGINAL, head, ROOT)
    selected = tuple(s for s in whole.sources if s.path in cost.CASES)
    if {s.path for s in selected} != set(cost.CASES):
        raise ValueError('anchor_small_manifest_missing_source')
    return replace(whole, sources=selected, scopes=tuple(cost.CASES),
                   excluded_text_files=whole.excluded_text_files + len(whole.sources) - len(selected))


def _measure(snapshot):
    return old._tokenizer('''import json,sys
from app.recovery_guide_costing import hydrate
from app.recovery_guide_anchor_costing import measure
print(json.dumps(measure(hydrate(json.load(sys.stdin)))))''', asdict(snapshot))


def _count_request(request):
    return old._tokenizer('''import json,sys,tiktoken
from app.recovery_guide_anchor_protocol import Request
from app.recovery_guide_anchor_costing import request_tokens,tokenizer_identity
r=Request(json.load(sys.stdin))
print(json.dumps({'tokens':request_tokens(r,tiktoken),'tokenizer':tokenizer_identity(tiktoken)}))''',
        request.envelope_json)


def _current(packet):
    return (_head() == packet['snapshot']['head'] and not ORIGINAL.is_symlink()
        and digest(ORIGINAL.read_bytes()) == packet['snapshot']['original']['sha256']
        and _code() == packet['implementation'])


def public_card(envelope):
    p = envelope['packet']
    return {k: v for k, v in p.items() if k not in {'snapshot', 'implementation', 'runtime'}} | {
        'approval_digest': envelope['approval_digest'],
        'state': 'awaiting_exact_small_trial_approval',
        'snapshot': hydrate(p['snapshot']).receipt(),
        'runtime': {k: v for k, v in p['runtime'].items() if k != 'socket'},
        'model_turns_started': 0, 'full_corpus_review': False,
        'production_writes': False, 'semantic_correctness_proven': False}


def prepare(*, refresh=False, client_factory=None):
    """Freeze a nonpaid small card. Explicit refresh only BEFORE any attempt."""
    _guard()
    with exclusive_file_lock(STATE / 'job', timeout=0):
        path = STATE / 'packet.json'
        previous = json.loads(path.read_text()) if path.exists() else None
        if previous and not refresh:
            return public_card(previous)
        if refresh and not previous:
            raise ValueError('anchor_refresh_requires_original')
        if (STATE / 'attempt.json').exists() or (STATE / 'turns').exists() or (STATE / 'context').exists():
            raise ValueError('anchor_refresh_after_attempt_refused')
        head = _head()
        snapshot = _snapshot(head)
        measured = _measure(snapshot)
        with (client_factory or calibration._client)() as client:
            runtime = calibration._runtime(client)
        packet = {'request_id': REQUEST, 'prepared_at': _now(), 'model': calibration.MODEL,
            'effort': 'medium', 'serviceTierForTurn': 'default', 'snapshot': asdict(snapshot),
            'measurements': measured, 'runtime': runtime, 'protocol': calibration._protocol(),
            'implementation': _code(), 'instructions': cost.INSTRUCTIONS,
            'candidate_only': True, 'central_role_changed': False, 'central_role_binding': None,
            'role_status': 'explicit_candidate_not_activated', 'automatic_retry': False,
            'publication': False, 'weekly_activation': False, 'old_job_reopened': False,
            'max_turns': 2, 'duration_acceptance_ms_per_turn': 300000,
            'transport_wait_timeout_seconds': 90, 'end_to_end_hard_timeout': False,
            'shell_tool_exposure_disabled': True, 'live_zero_tools_proven': False,
            'unified_exec_backend_independently_disableable': False,
            'synthesis_binding': 'derive_from_exact_accepted_inspect_request_and_raw_receipt',
            'phone_settings_manually_verified': False, 'application_scope_approved': False}
        if previous:
            packet['supersedes_approval_digest'] = previous['approval_digest']
        if not _current(packet):
            raise ValueError('anchor_sources_changed_during_prepare')
        envelope = {'packet': packet, 'approval_digest': digest(canonical_json(packet))}
        target = STATE / 'revisions' / (envelope['approval_digest'] + '.json') if previous else path
        atomic_create_text(target, canonical_json(envelope))
        return public_card(envelope)


def _approved(digest_value):
    if not isinstance(digest_value, str) or not re.fullmatch(r'[0-9a-f]{64}', digest_value):
        raise ValueError('anchor_exact_approval_required')
    envelope = json.loads((STATE / 'packet.json').read_text())
    if envelope['approval_digest'] != digest_value:
        path = STATE / 'revisions' / (digest_value + '.json')
        if path.is_symlink() or not path.is_file():
            raise ValueError('anchor_unknown_approved_packet')
        envelope = json.loads(path.read_text())
    if envelope['approval_digest'] != digest_value or digest(canonical_json(envelope['packet'])) != digest_value:
        raise ValueError('anchor_packet_changed')
    return envelope['packet']


def _inspect(cat, request, raw):
    if len(raw.encode()) > cost.RAW_INSPECTION_BYTES:
        raise ValueError('anchor_inspect_response_too_large')
    result = protocol.resolve_inspection(cat, request, raw)
    data = json.loads(raw)
    pairs = cost.expected_pairs(cat)
    if (data['covered'] != dict(pairs) or len(data['findings']) != 2
            or any(len(f['text'].encode()) > cost.FINDING_BYTES or len(f['evidence']) != 1 for f in data['findings'])
            or sorted((f['evidence'][0]['source_id'], f['evidence'][0]['anchor_id']) for f in data['findings']) != sorted(pairs)):
        raise ValueError('anchor_small_case_coverage_failed')
    return result


def _synthesis(cat, request, raw, snapshot):
    result = protocol.resolve_synthesis(cat, request, raw)
    changed = [p for p in result['paragraphs'] if p['status'] != 'unchanged']
    pairs = cost.expected_pairs(cat)
    expected = [cat.resolve(sid, aid, catalogue_sha256=cat.sha256) for sid, aid in pairs]
    if (len(changed) != 2 or any(p['status'] != 'unverified' or len(p['evidence']) != 1 for p in changed)
            or sorted(canonical_json(p['evidence'][0]) for p in changed) != sorted(map(canonical_json, expected))):
        raise ValueError('anchor_small_synthesis_evidence_failed')
    # Preserve the entire original, not merely its headings/length (core gate is weaker).
    unchanged = '\n\n'.join(p['text'] for p in result['paragraphs'] if p['status'] == 'unchanged')
    if unchanged.strip() != snapshot.original.text.strip():
        raise ValueError('anchor_small_original_changed')
    return protocol.validate_synthesis(cat, request, raw, snapshot)


def _turn(client, packet, request, index, before_wire):
    phase = 'inspect' if index == 1 else 'synthesize'
    measured = _count_request(request)
    limits = packet['measurements']
    if (measured['tokenizer'] != limits['tokenizer']
            or cost.padded(measured['tokens']) > limits['input_acceptance_tokens'][phase]):
        raise ValueError('anchor_request_exceeds_approved_reference_plan')
    if (not _current(packet) or calibration._runtime(client) != packet['runtime']
            or calibration._protocol() != packet['protocol']):
        raise ValueError('anchor_changed_before_thread')
    path = STATE / 'turns' / f'{index:02d}.json'
    record = {'state': 'thread_starting', 'request_sha256': request.sha256,
        'request': request.envelope_json, 'phase': phase, 'reference_tokens': measured['tokens']}
    atomic_create_text(path, canonical_json(record))

    def before_send(thread):
        if (not _current(packet) or calibration._socket(client) != packet['runtime']['socket']
                or calibration._protocol() != packet['protocol']):
            raise ValueError('anchor_changed_before_send')
        record.update(state='delivery_unknown', thread_id=thread)
        atomic_write_json(path, record)
        before_wire()

    original = client.transport
    guard = StandardTurn(original, context=STATE / 'context' / str(index), request=request,
        instructions=cost.INSTRUCTIONS, before_send=before_send)
    client.transport = guard
    try:
        from app.routine_tasks import start_data_only_thread
        thread = start_data_only_thread(client, guard.context, calibration.MODEL, cost.INSTRUCTIONS)
        receipt = client.send_text(thread_id=thread['thread_id'], text=canonical_json(request.payload),
            model=calibration.MODEL, effort='medium', approval_policy='never',
            client_message_id=REQUEST + '-' + str(index), output_schema=request.schema,
            sandbox_policy={'type': 'readOnly', 'networkAccess': False})
        record.update(state='completed_unreviewed', receipt=receipt.as_dict(),
            unexpected_item_types=sorted(guard.unexpected_items))
        atomic_write_json(path, record)  # Preserve raw receipt BEFORE every acceptance check.
        usage = normalize_usage(receipt.thread_token_usage)
        credits = estimate_standard_credits(calibration.MODEL, usage)
        record.update(usage=usage, estimated_standard_credits=credits)
        atomic_write_json(path, record)
        if (not receipt.delivered or usage is None or credits is None or guard.unexpected_items
                or usage['input_tokens'] > limits['input_acceptance_tokens'][phase]
                or usage['output_tokens'] > limits['output_acceptance_tokens'][phase]
                or receipt.duration_ms > packet['duration_acceptance_ms_per_turn']):
            raise ValueError('anchor_receipt_acceptance_failed')
        return receipt.answer, record
    except Exception as exc:
        record.update(error_type=type(exc).__name__, turn_id=guard.turn_id,
                      delivery_unknown=record['state'] == 'delivery_unknown')
        atomic_write_json(path, record)
        raise
    finally:
        client.transport = original


def run(*, approved_digest, client_factory=None):
    """Trusted explicit approval only. Every replay returns the old job, never sends."""
    _guard()
    with exclusive_file_lock(STATE / 'job', timeout=0):
        packet = _approved(approved_digest)
        path = STATE / 'attempt.json'
        if path.exists():
            previous = json.loads(path.read_text())
            if previous['approval_digest'] != approved_digest:
                raise ValueError('anchor_job_already_reserved')
            return previous
        if not _current(packet) or calibration._protocol() != packet['protocol']:
            raise ValueError('anchor_frozen_inputs_changed')
        record = {'request_id': REQUEST, 'approval_digest': approved_digest, 'state': 'reserved',
            'started_at': _now(), 'accepted': False, 'model_turn_attempts': 0, 'phase_attempts': 0,
            'estimated_standard_credits': 0.0, 'known_standard_credits': 0.0, 'automatic_retry': False,
            'publication_authorized': False, 'full_corpus_review': False}
        atomic_create_text(path, canonical_json(record))
        known_total = 0.0
        try:
            cat = Catalogue(hydrate(packet['snapshot']))
            request = protocol.inspection_request(cat, tuple(cost.CASES))
            if request.sha256 != packet['measurements']['inspect_request_sha256']:
                raise ValueError('anchor_inspect_request_changed')
            with (client_factory or calibration._client)() as client:
                if calibration._runtime(client) != packet['runtime']:
                    raise ValueError('anchor_runtime_changed')
                for index in (1, 2):
                    record.update(state='in_flight', phase_attempts=index)
                    atomic_write_json(path, record)  # BEFORE even thread/start; death never resumes.
                    def before_wire():
                        record['model_turn_attempts'] += 1
                        record['estimated_standard_credits'] = None
                        atomic_write_json(path, record)
                    raw, turn = _turn(client, packet, request, index, before_wire)
                    known_total = round(known_total + turn['estimated_standard_credits'], 8)
                    record.update(estimated_standard_credits=known_total, known_standard_credits=known_total)
                    atomic_write_json(path, record)
                    if record['estimated_standard_credits'] > packet['measurements']['acceptance_standard_credits']:
                        raise ValueError('anchor_total_cost_acceptance_exceeded')
                    if index == 1:
                        _inspect(cat, request, raw)
                        request = protocol.synthesis_request(cat, [(request, raw)])
                    else:
                        candidate = _synthesis(cat, request, raw, hydrate(packet['snapshot']))
                        record['candidate_sha256'] = digest(candidate)  # No guide publication/writer.
            record.update(state='small_trial_passed', accepted=True)
        except Exception as exc:
            record.update(state='attention', error_type=type(exc).__name__)
            # Zero cost is never claimed for an incomplete/unknown turn. Preserve
            # all available numeric receipts, even if _turn failed acceptance.
            receipts = [json.loads(p.read_text()) for p in sorted((STATE / 'turns').glob('*.json'))]
            values = [r.get('estimated_standard_credits') for r in receipts]
            record['known_standard_credits'] = round(sum(v for v in values if v is not None), 8)
            record['estimated_standard_credits'] = (round(sum(values), 8)
                if receipts and all(v is not None for v in values) else None)
            record['reason'] = str(exc) if isinstance(exc, ValueError) and str(exc).startswith('anchor_') else 'review_private_receipts'
        record['finished_at'] = _now()
        atomic_write_json(path, record)
        return record
