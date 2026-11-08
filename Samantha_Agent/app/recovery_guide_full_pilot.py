"""Explicit full-corpus REC-06 trial; no weekly activation or publication.

Only prepare() is nonpaid. run() consumes ONE durable job for an exact human
approved packet. A failed/uncertain/partly completed job never starts again.
The candidate model is explicit; central roles and production code stay intact.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess

from app import recovery_guide_maintainer as m
from app import recovery_guide_trial as calibration
from app.file_persistence import atomic_create_text, atomic_write_json, exclusive_file_lock
from app.recovery_guide_costing import hydrate, padded_count
from app.recovery_guide_revision import collect_revision
from app.recovery_guide_sources import canonical_json, digest

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.venv/recovery_rec06_full_pilot'
ORIGINAL = Path.home() / 'Desktop/OBNOVA_SAMANTHY_NOVY_MAC.txt'
REQUEST = 'rec06-full-corpus-01'


def _guard():
    if any(p.is_symlink() for p in (STATE, *STATE.parents)):
        raise ValueError('full_pilot_state_alias')
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    if STATE.stat().st_uid != os.getuid() or STATE.stat().st_mode & 0o077:
        raise ValueError('full_pilot_state_not_private')
    for name in ('packet.json', 'attempt.json', 'job.lock', 'context', 'controller', 'turns', 'revisions'):
        if (STATE / name).is_symlink():
            raise ValueError('full_pilot_artifact_alias')


def _head():
    return subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'refs/heads/main'],
                                   text=True).strip()


def _code():
    names = ('app/recovery_guide_full_pilot.py', 'app/recovery_guide_revision.py',
        'app/recovery_guide_costing.py', 'app/recovery_guide_maintainer.py',
        'app/recovery_guide_sources.py', 'app/recovery_guide_quality.py',
        'app/recovery_guide_trial.py', 'app/routine_tasks.py', 'app/codex_appserver.py',
        'app/file_persistence.py', 'app/release_usage.py', 'app/communication/luna_release.py',
        'config/agent_roles.json')
    return {n: digest((ROOT / n).read_bytes()) for n in names}


def _tokenizer(script, data, *, timeout=240):
    result = subprocess.run([str(ROOT / '.venv/recovery_tokenizer/bin/python'), '-c', script],
        input=canonical_json(data), text=True, capture_output=True, check=True, timeout=timeout,
        cwd=ROOT, env={**os.environ, 'TIKTOKEN_CACHE_DIR': str(ROOT / '.venv/recovery_tokenizer/cache')})
    return json.loads(result.stdout)


def _measure(snapshot):
    return _tokenizer('''import json,sys
from app.recovery_guide_costing import hydrate,measure
print(json.dumps(measure(hydrate(json.load(sys.stdin)))))''', asdict(snapshot))


class Counter:
    def __init__(self, measurements):
        self.counts = dict(measurements['reference_counts'])

    def __call__(self, text):
        key = digest(text)
        if key not in self.counts:
            self.counts[key] = _tokenizer('''import json,sys,tiktoken
print(json.dumps(len(tiktoken.get_encoding('o200k_base').encode_ordinary(json.load(sys.stdin)))))''', text)
        return padded_count(text, self.counts[key])


def _calibration():
    path = calibration.STATE / 'receipt.json'
    record = json.loads(path.read_text())
    if record.get('state') != 'trial_passed' or record.get('model_turn_attempts') != 1:
        raise ValueError('full_pilot_calibration_missing')
    return {'sha256': digest(path.read_bytes()), 'credits': record['estimated_standard_credits'],
            'input_tokens': record['usage']['input_tokens'], 'output_tokens': record['usage']['output_tokens']}


def prepare(*, project_only=False, refresh=False):
    """Read committed main + original, freeze a packet. No threads or turns."""
    _guard()
    with exclusive_file_lock(STATE / 'job', timeout=0):
        path = STATE / 'packet.json'
        previous = None
        if path.exists():
            envelope = json.loads(path.read_text())
            if envelope['packet']['project_only'] != project_only:
                raise ValueError('full_pilot_existing_scope_differs')
            if not refresh:
                return public_card(envelope)
            if (STATE / 'attempt.json').exists() or (STATE / 'controller').exists() or (STATE / 'turns').exists():
                raise ValueError('full_pilot_refresh_after_attempt_refused')
            previous = envelope
        elif refresh:
            raise ValueError('full_pilot_refresh_requires_original')
        head = _head()
        snapshot = collect_revision(ORIGINAL, head, ROOT, project_only=project_only)
        measured = _measure(snapshot)
        if previous:
            prior_limits = previous['packet']['measurements']['limits']
            if measured['planning_standard_credits_with_margin'] > prior_limits['run_credits']:
                raise ValueError('full_pilot_refresh_exceeds_previous_budget')
            measured['limits']['run_credits'] = prior_limits['run_credits']
            measured['limits']['month_credits'] = prior_limits['month_credits']
        with calibration._client() as client:
            runtime = calibration._runtime(client)
        if _head() != head or digest(ORIGINAL.read_bytes()) != snapshot.original.sha256:
            raise ValueError('full_pilot_sources_changed_during_prepare')
        packet = {'request_id': REQUEST, 'prepared_at': datetime.now(timezone.utc).isoformat(),
            'project_only': project_only, 'snapshot': asdict(snapshot), 'measurements': measured,
            'runtime': runtime, 'protocol': calibration._protocol(), 'implementation': _code(),
            'calibration': _calibration(), 'model': m.MODEL, 'effort': 'medium',
            'serviceTierForTurn': 'default', 'candidate_only': True, 'publication': False,
            'automatic_retry': False, 'weekly_activation': False, 'central_role_activation': False,
            'phone_settings_manually_verified': False, 'application_scope_approved': False}
        if previous:
            packet['supersedes_approval_digest'] = previous['approval_digest']
        envelope = {'packet': packet, 'approval_digest': digest(canonical_json(packet))}
        if previous:
            path = STATE / 'revisions' / (envelope['approval_digest'] + '.json')
        atomic_create_text(path, canonical_json(envelope))
        return public_card(envelope)


def _approved_packet(approved_digest):
    if not isinstance(approved_digest, str) or not re.fullmatch(r'[0-9a-f]{64}', approved_digest):
        raise ValueError('full_pilot_exact_approval_required')
    original = json.loads((STATE / 'packet.json').read_text())
    if original.get('approval_digest') == approved_digest:
        return original
    path = STATE / 'revisions' / (approved_digest + '.json')
    if path.is_symlink() or not path.is_file():
        raise ValueError('full_pilot_unknown_approved_packet')
    return json.loads(path.read_text())


def public_card(envelope):
    packet = envelope['packet']
    measured = {k: v for k, v in packet['measurements'].items() if k != 'reference_counts'}
    return {k: v for k, v in packet.items() if k not in
            {'snapshot', 'measurements', 'runtime', 'implementation'}} | {
        'approval_digest': envelope['approval_digest'], 'state': 'awaiting_exact_scope_and_cost_approval',
        'snapshot': hydrate(packet['snapshot']).receipt(), 'measurements': measured,
        'runtime': {k: v for k, v in packet['runtime'].items() if k != 'socket'},
        'model_turns_started': 0, 'production_writes': False,
        'live_server_context_limit_verified': False, 'whole_application_inventory_complete': False}


class StandardTransport:
    """One dynamic approved payload, one new thread, one Standard turn."""
    def __init__(self, inner, context, payload, schema, before_send):
        self.inner, self.context = inner, context
        self.payload, self.schema, self.before_send = canonical_json(payload), schema, before_send
        self.thread = None
        self.turn_id = None
        self.thread_attempted = self.turn_attempted = False
        self.unexpected_items = set()

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def receive(self, predicate, **kwargs):
        # Reuse the event-only audit, not the fixed calibration request scope.
        return calibration.StandardOneTurn.receive(self, predicate, **kwargs)

    def request(self, method, params):
        if method == 'thread/start':
            if self.thread_attempted:
                raise ValueError('full_pilot_second_thread')
            self.thread_attempted = True
            if (params.get('cwd') != str(self.context.resolve()) or params.get('model') != m.MODEL
                    or params.get('approvalPolicy') != 'never' or params.get('sandbox') != 'read-only'
                    or params.get('ephemeral') is not True or params.get('baseInstructions') != m.INSTRUCTIONS
                    or params.get('developerInstructions') != m.INSTRUCTIONS):
                raise ValueError('full_pilot_thread_scope_changed')
            config = {**params.get('config', {}), **{'features.' + n: False for n in calibration.DISABLED_FEATURES}}
            reply = self.inner.request(method, {**params, 'config': config})
            sandbox = reply.get('sandbox', {})
            if (reply.get('model') != m.MODEL or reply.get('cwd') != str(self.context.resolve())
                    or reply.get('approvalPolicy') != 'never' or sandbox.get('type') != 'readOnly'
                    or sandbox.get('networkAccess', False) is not False):
                raise ValueError('full_pilot_effective_permissions_unconfirmed')
            self.thread = reply.get('thread', {}).get('id')
            return reply
        if method == 'turn/start':
            if self.turn_attempted or not self.thread or params.get('threadId') != self.thread:
                raise ValueError('full_pilot_second_or_foreign_turn')
            if (params.get('model') != m.MODEL or params.get('effort') != 'medium'
                    or params.get('approvalPolicy') != 'never' or params.get('outputSchema') != self.schema
                    or params.get('input') != [{'type': 'text', 'text': self.payload}]
                    or params.get('sandboxPolicy') != {'type': 'readOnly', 'networkAccess': False}
                    or 'serviceTier' in params):
                raise ValueError('full_pilot_turn_scope_changed')
            self.turn_attempted = True
            self.before_send(self.thread)
            reply = self.inner.request(method, {**params, 'serviceTierForTurn': 'default'})
            self.turn_id = reply.get('turn', {}).get('id')
            return reply
        if method not in {'config/read', 'skills/list'}:
            raise ValueError('full_pilot_rpc_outside_scope')
        return self.inner.request(method, params)


class Reviewer:
    def __init__(self, client, packet):
        self.client, self.packet, self.calls = client, packet, 0

    def __call__(self, payload, kind):
        from app.routine_tasks import start_data_only_thread
        if kind not in {'inspect', 'synthesize'}:
            raise ValueError('full_pilot_unknown_phase')
        shards = self.packet['measurements']['shards']
        expected_kind = 'inspect' if self.calls < len(shards) else 'synthesize'
        if self.calls >= len(shards) + 1 or kind != expected_kind:
            raise ValueError('full_pilot_phase_outside_plan')
        if kind == 'inspect' and digest(canonical_json(payload)) != shards[self.calls]['payload_sha256']:
            raise ValueError('full_pilot_payload_outside_plan')
        if kind == 'synthesize' and (payload.get('original') != self.packet['snapshot']['original']['text']
                                    or len(payload.get('findings', [])) != len(shards)):
            raise ValueError('full_pilot_synthesis_outside_plan')
        if calibration._runtime(self.client) != self.packet['runtime'] or not _current(self.packet):
            raise ValueError('full_pilot_runtime_or_sources_changed')
        self.calls += 1
        path = STATE / 'turns' / f'{self.calls:02d}.json'
        record = {'state': 'thread_starting', 'phase': kind, 'payload_sha256': digest(canonical_json(payload))}
        atomic_create_text(path, canonical_json(record))
        schema = m.INSPECT_SCHEMA if kind == 'inspect' else m.SYNTHESIS_SCHEMA
        original = self.client.transport

        def before_send(thread):
            if calibration._socket(self.client) != self.packet['runtime']['socket'] or not _current(self.packet):
                raise ValueError('full_pilot_changed_before_send')
            record.update(state='delivery_unknown', thread_id=thread)
            atomic_write_json(path, record)

        context = STATE / 'context' / str(self.calls)
        guard = StandardTransport(original, context, payload, schema, before_send)
        self.client.transport = guard
        try:
            thread = start_data_only_thread(self.client, context, m.MODEL, m.INSTRUCTIONS)
            result = self.client.send_text(thread_id=thread['thread_id'], text=canonical_json(payload),
                model=m.MODEL, effort='medium', approval_policy='never',
                client_message_id=REQUEST + '-' + str(self.calls), output_schema=schema,
                sandbox_policy={'type': 'readOnly', 'networkAccess': False})
            record.update(state='completed', receipt=result.as_dict(), unexpected_item_types=sorted(guard.unexpected_items))
            atomic_write_json(path, record)  # Preserve usage even when JSON/content fail.
            try:
                answer = json.loads(result.answer)
            except (ValueError, TypeError):
                answer = None
            if guard.unexpected_items:
                answer = None
            if kind == 'inspect':
                answer, normalization = normalize_inspection(answer, payload)
                if normalization:
                    record['normalization'] = normalization
                    atomic_write_json(path, record)
            return {'answer': answer, 'usage': result.thread_token_usage}
        except Exception:
            if guard.turn_id:
                record['turn_id'] = guard.turn_id
                atomic_write_json(path, record)
            raise
        finally:
            self.client.transport = original


def normalize_inspection(answer, payload):
    """Only exclude one exact original-guide citation from document coverage.

    Raw receipt stays intact. Missing/duplicate/unknown sources, changed quotes
    and all other schema errors remain errors. No invented or repaired text.
    """
    if (not isinstance(answer, dict) or set(answer) != {'covered', 'notes'}
            or not isinstance(answer['covered'], list) or not isinstance(answer['notes'], str)):
        return answer, None
    rows = answer['covered']
    original = payload['original']
    texts = {s['path']: s['text'] for s in payload['sources']}
    if len(rows) != len(texts) + 1 or original['path'] in texts:
        return answer, None
    try:
        extras = [r for r in rows if isinstance(r, dict) and r.get('source') == original['path']]
        docs = [r for r in rows if r not in extras]
        if len(extras) != 1 or len(docs) != len(texts) or {r['source'] for r in docs} != set(texts):
            return answer, None
        m.citation(extras[0], {original['path']: original['text']})
        for row in docs:
            m.citation(row, texts)
    except (ValueError, TypeError, KeyError):
        return answer, None
    return {'covered': docs, 'notes': answer['notes']}, {
        'kind': 'exclude_exact_original_from_document_coverage', 'kept_sources': len(docs),
        'original_quote_sha256': digest(extras[0]['quote'])}


def _current(packet):
    return (_head() == packet['snapshot']['head'] and not ORIGINAL.is_symlink()
            and digest(ORIGINAL.read_bytes()) == packet['snapshot']['original']['sha256']
            and _code() == packet['implementation'] and _calibration() == packet['calibration'])


def run(*, approved_digest: str, now=None, client_factory=None):
    """Run one explicitly approved FULL trial. Repeated calls only read receipt.

    Unknown token mapping, unproven margins and no hard billing cap MUST be
    part of the concrete human approval. No writer or central role activation.
    """
    _guard()
    with exclusive_file_lock(STATE / 'job', timeout=0):
        envelope = _approved_packet(approved_digest)
        packet = envelope['packet']
        if (approved_digest != envelope['approval_digest']
                or approved_digest != digest(canonical_json(packet))):
            raise ValueError('full_pilot_exact_approval_required')
        attempt = STATE / 'attempt.json'
        if attempt.exists():
            old = json.loads(attempt.read_text())
            if old['approval_digest'] != approved_digest:
                raise ValueError('full_pilot_job_already_reserved')
            status = m.status(STATE / 'controller', old['slot'])
            return {**(status if status['state'] != 'not_started' else old), 'replayed_receipt': True}
        if not _current(packet) or calibration._protocol() != packet['protocol']:
            raise ValueError('full_pilot_frozen_inputs_changed')
        now = now or datetime.now(timezone.utc)
        marker = {'request_id': REQUEST, 'state': 'reserved', 'slot': m.weekly_slot(now),
                  'approval_digest': approved_digest, 'model_calls': 0, 'automatic_retry': False}
        atomic_create_text(attempt, canonical_json(marker))
        try:
            with (client_factory or calibration._client)() as client:
                if calibration._runtime(client) != packet['runtime']:
                    raise ValueError('full_pilot_runtime_changed')
                result = m.run(hydrate(packet['snapshot']), state_dir=STATE / 'controller', now=now,
                    limits=m.Limits(**packet['measurements']['limits']), count_tokens=Counter(packet['measurements']),
                    call=Reviewer(client, packet), approved_snapshot=hydrate(packet['snapshot']).sha256,
                    assert_sources=lambda: _current(packet), confirmed=True, legacy_format=True)
        except Exception as exc:
            marker.update(state='attention', error_type=type(exc).__name__)
            result = marker
        marker['state'] = result['state']
        atomic_write_json(attempt, marker)
        return result
