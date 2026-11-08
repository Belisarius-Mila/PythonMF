"""Explicit full anchor candidate pilot. prepare is nonpaid; run needs approval.

One durable job across all pre-attempt cards. No continuation/reset/retry,
production writer, scheduler, role changes or daemon startup. A process death
leaves the original receipt/unknown marker; another run only reads that job.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time

from app import recovery_guide_anchor_full_plan as planning
from app import recovery_guide_anchor_protocol as protocol
from app import recovery_guide_trial as calibration
from app.recovery_guide_anchor_transport import StandardTurn
from app.recovery_guide_anchors import AnchorError
from app.recovery_guide_costing import hydrate
from app.recovery_guide_sources import canonical_json, digest
from app.file_persistence import atomic_create_text, atomic_write_json, exclusive_file_lock
from app.release_usage import normalize_usage, estimate_standard_credits

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.venv/recovery_rec06_anchor_full_pilot'
REQUEST = 'rec06-anchors-full-01'


class ObservedTurn(StandardTurn):
    """Retain terminal telemetry even when the unchanged client raises."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.terminal_status = None
        self.observed_usage = None

    def receive(self, predicate, **kwargs):
        event = super().receive(predicate, **kwargs)
        params = event.get('params', {})
        if event.get('method') == 'thread/tokenUsage/updated':
            value = params.get('tokenUsage')
            self.observed_usage = normalize_usage(value.get('total') if isinstance(value, dict) else None,
                                                   camel_case=True)
        if event.get('method') == 'turn/completed':
            status = params.get('turn', {}).get('status')
            if status in {'completed','failed','interrupted'}:
                self.terminal_status = status
        return event


def _now():
    return datetime.now(timezone.utc).isoformat()


def _guard():
    if any(p.is_symlink() for p in (STATE, *STATE.parents)):
        raise AnchorError('full_anchor_state_alias')
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    if STATE.stat().st_uid != os.getuid() or STATE.stat().st_mode & 0o077:
        raise AnchorError('full_anchor_state_not_private')
    for path in STATE.rglob('*'):
        if path.is_symlink():
            raise AnchorError('full_anchor_artifact_alias')


def _code():
    return {**planning._code(), **{name:digest((ROOT/name).read_bytes()) for name in
        ('app/recovery_guide_anchor_full_pilot.py', 'app/recovery_guide_anchor_full_worker.py')}}


def _load_plan(plan_digest):
    if not isinstance(plan_digest, str) or not re.fullmatch('[a-f0-9]{64}', plan_digest):
        raise AnchorError('full_anchor_exact_plan_required')
    if any(p.is_symlink() for p in (planning.STATE, *planning.STATE.parents)):
        raise AnchorError('full_anchor_plan_alias')
    path = planning.STATE/'plan.json'
    if path.is_symlink():
        raise AnchorError('full_anchor_plan_alias')
    original = json.loads(path.read_text())
    if original['plan_digest'] != plan_digest:
        path = planning.STATE/'revisions'/(plan_digest+'.json')
        if path.is_symlink() or path.parent.is_symlink():
            raise AnchorError('full_anchor_plan_alias')
        original = json.loads(path.read_text())
    if original['plan_digest'] != plan_digest or digest(canonical_json(original['plan'])) != plan_digest:
        raise AnchorError('full_anchor_plan_changed')
    if not planning.public_plan(original)['frozen_inputs_current']:
        raise AnchorError('full_anchor_plan_stale')
    return original['plan']


def _offline(action, plan, **kwargs):
    result = planning.old._tokenizer('''import json,sys
from app.recovery_guide_anchor_full_worker import dispatch
print(json.dumps(dispatch(json.load(sys.stdin)),ensure_ascii=False))''',
        {'action': action, 'frozen': plan, **kwargs})
    if not result.get('ok'):
        code = result.get('code', 'worker_failure')
        if not isinstance(code, str) or not re.fullmatch('[A-Za-z0-9_]{1,100}', code):
            code = 'worker_failure'
        raise AnchorError('full_anchor_offline_' + code)
    return result['value']


def _runtime(client):
    return {**calibration._runtime(client), 'local_cli_version': client.version.raw}


def _current(packet):
    plan = packet['plan']
    return (planning.old._head() == plan['snapshot']['head'] and not planning.ORIGINAL.is_symlink()
        and digest(planning.ORIGINAL.read_bytes()) == plan['snapshot']['original']['sha256']
        and planning._code() == plan['implementation'] and _code() == packet['implementation'])


def public_card(envelope):
    packet = envelope['packet']; plan = packet['plan']
    measured = {k:v for k,v in plan['measurements'].items() if k not in
        {'blocked_anchor_ids','state','execution_adapter_implemented','model_calls_started'}}
    try:
        current = _current(packet)
    except Exception:
        current = False
    return {k:v for k,v in packet.items() if k not in {'plan','implementation','runtime'}} | {
        'approval_digest': envelope['approval_digest'], 'state': 'awaiting_exact_full_pilot_approval',
        'snapshot': hydrate(plan['snapshot']).receipt(), 'measurements': measured,
        'runtime': {k:v for k,v in packet['runtime'].items() if k != 'socket'},
        'frozen_inputs_current': current, 'model_calls_started': 0,
        'source_scope_approval_requested': True, 'application_inventory_complete': False}


def prepare(*, plan_digest, refresh=False, client_factory=None):
    """Audit an exact plan + existing socket, persist an immutable execution card."""
    _guard()
    with exclusive_file_lock(STATE/'job', timeout=0):
        path = STATE/'packet.json'
        previous = json.loads(path.read_text()) if path.exists() else None
        if previous and not refresh:
            if previous['packet']['plan_digest'] != plan_digest:
                raise AnchorError('full_anchor_explicit_card_refresh_required')
            return public_card(previous)
        if refresh and not previous:
            raise AnchorError('full_anchor_refresh_requires_original')
        if any((STATE/name).exists() for name in ('attempt.json','turns','context','candidate.txt')):
            raise AnchorError('full_anchor_refresh_after_attempt_refused')
        plan = _load_plan(plan_digest)
        audit = _offline('audit', plan)
        with (client_factory or calibration._client)() as client:
            runtime = _runtime(client)
        packet = {'request_id': REQUEST, 'plan_digest': plan_digest, 'plan': plan,
            'prepared_at': _now(), 'implementation': _code(), 'runtime': runtime,
            'protocol': calibration._protocol(), 'tokenizer_audit': audit,
            'model': calibration.MODEL, 'effort': 'medium', 'serviceTierForTurn': 'default',
            'candidate_only': True, 'execution_adapter_implemented': True,
            'central_role_changed': False, 'role_status': 'explicit_candidate_not_activated',
            'automatic_retry': False, 'publication_authorized': False, 'weekly_activation': False,
            'old_jobs_reopened': False, 'new_command_allowlist': [], 'live_settings_facts': [],
            'validation_policy': 'unchanged_quality_gate_no_unregistered_commands_or_unproven_live_claims',
            'transport_wait_timeout_seconds': 90, 'hard_billing_output_or_wallclock_cap': False,
            'shell_tool_exposure_disabled': True, 'live_zero_tools_proven_for_full_plan': False,
            'unified_exec_backend_independently_disableable': False,
            'authentication_billing_identity_proven': False,
            'known_limitations': ['reference_encoding_not_exact_sol', 'context_limit_unverified',
                'no_hard_billing_or_output_or_wallclock_cap', 'bounded_citations_and_findings',
                'new_wire_envelope_not_live_tested', 'no_application_inventory_or_live_iphone_facts']}
        if previous:
            packet['supersedes_approval_digest'] = previous['approval_digest']
        if not _current(packet):
            raise AnchorError('full_anchor_changed_during_prepare')
        envelope = {'packet': packet, 'approval_digest': digest(canonical_json(packet))}
        target = STATE/'revisions'/(envelope['approval_digest']+'.json') if previous else path
        atomic_create_text(target, canonical_json(envelope))
        return public_card(envelope)


def _approved(approved_digest):
    if not isinstance(approved_digest, str) or not re.fullmatch('[a-f0-9]{64}', approved_digest):
        raise AnchorError('full_anchor_exact_approval_required')
    envelope = json.loads((STATE/'packet.json').read_text())
    if envelope['approval_digest'] != approved_digest:
        path = STATE/'revisions'/(approved_digest+'.json')
        if path.is_symlink() or not path.is_file():
            raise AnchorError('full_anchor_unknown_approved_card')
        envelope = json.loads(path.read_text())
    if envelope['approval_digest'] != approved_digest or digest(canonical_json(envelope['packet'])) != approved_digest:
        raise AnchorError('full_anchor_card_changed')
    return envelope['packet']


def status():
    """Read just this fixed job's atomic receipt; no mkdir, lock, model or RPC."""
    if any(p.is_symlink() for p in (STATE, *STATE.parents, STATE/'attempt.json')):
        raise AnchorError('full_anchor_status_alias')
    if STATE.exists() and (STATE.stat().st_uid != os.getuid() or STATE.stat().st_mode & 0o077):
        raise AnchorError('full_anchor_state_not_private')
    path = STATE/'attempt.json'
    return json.loads(path.read_text()) if path.exists() else {
        'request_id': REQUEST, 'state': 'not_started', 'model_turn_attempts': 0}


def _phase_limits(packet, index):
    measured = packet['plan']['measurements']; batches = measured['batches']
    if index <= len(batches):
        row = batches[index-1]
        return 'inspect', row['input_acceptance_tokens'], row['output_acceptance_tokens']
    if index != len(batches) + 1:
        raise AnchorError('full_anchor_phase_outside_plan')
    return 'synthesize', measured['synthesis_input_acceptance_tokens'], measured['synthesis_output_acceptance_tokens']


def _turn(client, packet, index, request, before_wire, assert_budget):
    _guard()
    phase, input_limit, output_limit = _phase_limits(packet, index)
    measured = packet['plan']['measurements']
    if (request['tokenizer'] != measured['tokenizer']
            or planning.reference.padded(request['reference_tokens']) > input_limit):
        raise AnchorError('full_anchor_request_reference_exceeded')
    assert_budget()
    if not _current(packet) or _runtime(client) != packet['runtime'] or calibration._protocol() != packet['protocol']:
        raise AnchorError('full_anchor_changed_before_thread')
    wire = protocol.Request(request['wire']); context = STATE/'context'/str(index)
    path = STATE/'turns'/f'{index:02d}.json'
    record = {'index': index, 'phase': phase, 'state': 'thread_starting',
        'inner': request['inner'], 'wire': request['wire'], 'wire_request_sha256': wire.sha256,
        'reference_tokens': request['reference_tokens'], 'prepared_at': _now()}
    atomic_create_text(path, canonical_json(record))

    def before_send(thread):
        assert_budget()
        for prior in sorted((STATE/'turns').glob('*.json')):
            if prior == path:
                continue
            known = json.loads(prior.read_text())
            if thread == known.get('thread_id') or thread == known.get('receipt', {}).get('thread_id'):
                raise AnchorError('full_anchor_thread_reused')
        if (not _current(packet) or calibration._socket(client) != packet['runtime']['socket']
                or calibration._protocol() != packet['protocol']):
            raise AnchorError('full_anchor_changed_before_send')
        record.update(state='delivery_unknown', thread_id=thread, sent_at=_now())
        atomic_write_json(path, record)
        before_wire()

    original = client.transport
    guard = ObservedTurn(original, context=context, request=wire,
                         instructions=planning.INSTRUCTIONS, before_send=before_send)
    client.transport = guard
    try:
        from app.routine_tasks import start_data_only_thread
        thread = start_data_only_thread(client, context, calibration.MODEL, planning.INSTRUCTIONS)
        result = client.send_text(thread_id=thread['thread_id'], text=canonical_json(wire.payload),
            model=calibration.MODEL, effort='medium', approval_policy='never',
            client_message_id=REQUEST+'-'+str(index), output_schema=wire.schema,
            sandbox_policy={'type':'readOnly','networkAccess':False})
        record.update(state='completed_unreviewed', receipt=result.as_dict(),
            unexpected_item_types=sorted(guard.unexpected_items))
        atomic_write_json(path, record)
        usage = normalize_usage(result.thread_token_usage)
        credits = estimate_standard_credits(calibration.MODEL, usage)
        record.update(usage=usage, estimated_standard_credits=credits)
        atomic_write_json(path, record)
        checks = {'delivery': result.delivered, 'usage': usage is not None and credits is not None,
            'tools': not guard.unexpected_items,
            'input': usage is not None and usage['input_tokens'] <= input_limit,
            'output': usage is not None and usage['output_tokens'] <= output_limit,
            'duration': result.duration_ms <= measured['phase_seconds'][phase]*1000}
        record['acceptance'] = checks; atomic_write_json(path, record)
        if not all(checks.values()):
            raise AnchorError('full_anchor_receipt_acceptance_failed')
        return result.answer, credits
    except Exception as exc:
        details = {key:getattr(exc, key) for key in
            ('method','code','data','server_message','status','turn_error','will_retry')
            if getattr(exc, key, None) is not None}
        if details:
            record['structured_error'] = details  # PRIVATE raw evidence, never public card/result.
        record['terminal_status'] = guard.terminal_status
        record['last_observed_usage'] = guard.observed_usage
        if guard.terminal_status and guard.observed_usage is not None and 'usage' not in record:
            record.update(usage=guard.observed_usage,
                estimated_standard_credits=estimate_standard_credits(calibration.MODEL, guard.observed_usage),
                usage_from_terminal_event=True)
        record.update(error_type=type(exc).__name__, turn_id=guard.turn_id,
                      delivery_unknown=record['state'] == 'delivery_unknown' and not guard.terminal_status)
        atomic_write_json(path, record)
        raise
    finally:
        client.transport = original


def _ledger(record):
    values = []; unknown = False; completed = 0; terminal = 0
    for path in sorted((STATE/'turns').glob('*.json')):
        row = json.loads(path.read_text())
        if path.name != f"{row['index']:02d}.json":
            raise AnchorError('full_anchor_ledger_shape_changed')
        if row.get('receipt', {}).get('delivered'):
            completed += 1
        if row.get('receipt') or row.get('terminal_status'):
            terminal += 1
        value = row.get('estimated_standard_credits')
        if value is not None:
            values.append(value)
        elif row['state'] != 'thread_starting':
            unknown = True
    known = round(sum(values), 8)
    record.update(known_standard_credits=known, completed_receipts=completed, terminal_receipts=terminal,
        estimated_standard_credits=None if unknown or record['model_turn_attempts'] > terminal else known)


def run(*, approved_digest, client_factory=None):
    """One trusted exact human approval, one job. Replays NEVER reconnect."""
    _guard()
    with exclusive_file_lock(STATE/'job', timeout=0):
        packet = _approved(approved_digest); path = STATE/'attempt.json'
        if path.exists():
            previous = json.loads(path.read_text())
            if previous['approval_digest'] != approved_digest:
                raise AnchorError('full_anchor_job_already_reserved')
            return previous
        if not _current(packet) or calibration._protocol() != packet['protocol']:
            raise AnchorError('full_anchor_frozen_inputs_changed')
        measured = packet['plan']['measurements']; started = time.monotonic()
        record = {'request_id': REQUEST, 'approval_digest': approved_digest, 'plan_digest': packet['plan_digest'],
            'state': 'reserved', 'accepted': False, 'started_at': _now(), 'phase_attempts': 0,
            'model_turn_attempts': 0, 'completed_receipts': 0, 'accepted_inspection_batches': 0,
            'known_standard_credits': 0.0, 'estimated_standard_credits': 0.0,
            'automatic_retry': False, 'publication_authorized': False, 'weekly_activation': False,
            'application_inventory_complete': False}
        atomic_create_text(path, canonical_json(record))
        history = []
        try:
            _offline('audit', packet['plan'])
            with (client_factory or calibration._client)() as client:
                if _runtime(client) != packet['runtime']:
                    raise AnchorError('full_anchor_runtime_changed')
                for index in range(1, len(measured['batches'])+2):
                    phase, input_limit, output_limit = _phase_limits(packet, index)
                    reserve = (input_limit*50 + output_limit*250)/1_000_000
                    def assert_budget():
                        if time.monotonic()-started > measured['run_seconds_acceptance']:
                            raise AnchorError('full_anchor_run_time_exceeded')
                        if record['known_standard_credits']+reserve > measured['proposed_credit_acceptance']+1e-8:
                            raise AnchorError('full_anchor_remaining_credit_reservation_exceeded')
                    assert_budget()
                    request = _offline('request', packet['plan'], index=index, history=history)
                    record.update(state='in_flight', phase_attempts=index)
                    atomic_write_json(path, record)
                    def before_wire():
                        record['model_turn_attempts'] += 1
                        record['estimated_standard_credits'] = None
                        atomic_write_json(path, record)
                    raw, credits = _turn(client, packet, index, request, before_wire, assert_budget)
                    _ledger(record); atomic_write_json(path, record)
                    if not _current(packet):
                        raise AnchorError('full_anchor_sources_changed_after_completion')
                    checked = _offline('validate', packet['plan'], index=index, history=history, raw=raw)
                    if phase == 'inspect':
                        history.append({'inner': request['inner'], 'raw': raw})
                        record['accepted_inspection_batches'] += 1
                    else:
                        candidate = checked['candidate']
                        if digest(candidate) != checked['candidate_sha256']:
                            raise AnchorError('full_anchor_candidate_hash_changed')
                        atomic_create_text(STATE/'candidate.txt', candidate)
                        record['candidate_sha256'] = checked['candidate_sha256']
                    atomic_write_json(path, record)
                if (time.monotonic()-started > measured['run_seconds_acceptance']
                        or not _current(packet)):
                    raise AnchorError('full_anchor_final_time_or_sources_changed')
            record.update(state='full_anchor_candidate_validated', accepted=True)
        except Exception as exc:
            record.update(state='attention', error_type=type(exc).__name__)
            record['reason'] = str(exc) if isinstance(exc, AnchorError) else 'review_private_receipts'
        try:
            _ledger(record)
        except Exception:
            record.update(state='attention', accepted=False, estimated_standard_credits=None,
                          reason='full_anchor_ledger_requires_review')
        record.update(finished_at=_now(), elapsed_seconds=round(time.monotonic()-started,3))
        atomic_write_json(path, record)
        return record
