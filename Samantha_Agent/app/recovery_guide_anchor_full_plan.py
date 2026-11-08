"""Nonpaid full-corpus planning and offline contracts. NO model runner.

All full texts remain in each request. Bounded citations/findings reserve the
single synthesis input; nothing is silently clipped. This module grants no
execution/publication authority and never opens a model thread/turn.
"""
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path

from app import recovery_guide_anchor_protocol as protocol
from app import recovery_guide_anchor_costing as reference
from app import recovery_guide_full_pilot as old
from app import recovery_guide_anchor_trial as small
from app.recovery_guide_anchors import Catalogue, AnchorError
from app.recovery_guide_costing import hydrate
from app.recovery_guide_revision import collect_revision
from app.recovery_guide_sources import canonical_json, digest
from app.file_persistence import atomic_create_text, exclusive_file_lock

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.venv/recovery_rec06_anchor_full_plan'
ORIGINAL = small.ORIGINAL
MAX_INPUT = 240000
ROW_TOKENS = 160
FINDINGS_TOKENS = 1000
MAX_FINDINGS = 6
MAX_FINDING_REFS = 2
OUTPUT = {'inspect': 4096, 'synthesize': 32000}
INSTRUCTIONS = protocol.INSTRUCTIONS + '''
Toto je plán úplné revize, ne předchozí malý test. Přečti všechny celé zdroje.
anchor_request obsahuje původní kontrakt. citation_limits.excluded_anchors
jsou řádky, které lze číst, ale v tomto protokolu nelze použít jako citaci.
V inspect vrať nejvýše šest konkrétních findings, každé nejvýše se dvěma
evidencemi. Souhrnná findings musí být stručná (referenční rezerva 1000 tokenů).
Neopisuj všechny dokumenty do findings; covered přesto musí pokrýt každý zdroj.
Při syntéze zachovej úplný návod a kapitoly; změny dolož předanou evidencí.
Přednost má skutečné doložené nastavení Macu/iPhonu a aplikací; historické,
navržené nebo neověřené nevydávej za současně ověřené. Nic nepublikuj.'''


def _tokens(encoding, value):
    return len(encoding.encode_ordinary(value if isinstance(value, str) else canonical_json(value)))


def _row(cat, sid, aid, quote):
    return {'source_id': sid, 'anchor_id': aid, 'source': cat.source(sid).path, 'quote': quote}


def _index(cat, encoding):
    blocked, first, count = {}, {}, 0
    for sid in (cat.original_id, *cat.document_ids):
        denied = []
        for aid, raw in cat.model_source(sid)['lines']:
            if aid is None:
                continue
            if _tokens(encoding, _row(cat, sid, aid, raw.rstrip('\r\n'))) > ROW_TOKENS:
                denied.append(aid); count += 1
            elif sid not in first:
                first[sid] = aid
        if sid not in first:
            raise AnchorError('full_plan_source_has_no_bounded_citation')
        if denied:
            blocked[sid] = denied
    return blocked, first, count


def inspection(cat, paths, blocked):
    """Inner request validates the unchanged protocol; wire adds explicit limits."""
    inner = protocol.inspection_request(cat, tuple(paths))
    return inner, _wire(inner, blocked, 'inspect')


def _wire(inner, blocked, phase):
    schema = inner.schema
    if phase == 'inspect':
        findings = schema['properties']['findings']
        findings['maxItems'] = MAX_FINDINGS
        findings['items']['properties']['evidence']['maxItems'] = MAX_FINDING_REFS
    data = inner.payload['data']
    ids = {data['original']['source_id']}
    ids.update(s['source_id'] for s in data.get('sources', []))
    if phase == 'synthesize':
        ids.update(row['source_id'] for row in data['evidence_catalogue'])
    payload = {'anchor_request': inner.payload, 'citation_limits': {
        'reference_encoding': 'o200k_base', 'row_reference_tokens': ROW_TOKENS,
        'findings_reference_tokens': FINDINGS_TOKENS,
        'excluded_anchors': {sid: blocked[sid] for sid in sorted(ids) if sid in blocked}}}
    return protocol.Request(canonical_json({'payload': payload, 'schema': schema}))


def _request_tokens(request, encoding):
    return _tokens(encoding, INSTRUCTIONS + INSTRUCTIONS + canonical_json(request.payload)
                   + canonical_json(request.schema))


def validate_inspection(cat, inner, raw, encoding):
    """Offline narrowed contract; never modifies raw, calls a model or accepts a job."""
    if len(raw.encode('utf-8')) > 64000:
        raise AnchorError('full_plan_inspection_response_bytes')
    result = protocol.resolve_inspection(cat, inner, raw)
    findings = result['findings']
    if (len(findings) > MAX_FINDINGS or _tokens(encoding, findings) > FINDINGS_TOKENS
            or any(len(f['evidence']) > MAX_FINDING_REFS for f in findings)):
        raise AnchorError('full_plan_findings_reservation_exceeded')
    for sid, aid in result['selected_refs']:
        quote = cat.resolve(sid, aid, catalogue_sha256=cat.sha256)['quote']
        if _tokens(encoding, _row(cat, sid, aid, quote)) > ROW_TOKENS:
            raise AnchorError('full_plan_citation_reservation_exceeded')
    return result


def synthesis(cat, inspections, blocked, encoding, input_limit):
    """All known results, no dropping of findings/evidence to fit a budget."""
    inspections = tuple(inspections)
    for inner, raw in inspections:
        validate_inspection(cat, inner, raw, encoding)
    inner = protocol.synthesis_request(cat, inspections)
    wire = _wire(inner, blocked, 'synthesize')
    count = _request_tokens(wire, encoding)
    if reference.padded(count) > input_limit:
        raise AnchorError('full_plan_synthesis_reservation_exceeded')
    return inner, wire, count


def measure(snapshot, module=None):
    if module is None:
        import tiktoken as module
    cat = Catalogue(snapshot)
    if not cat.document_ids or len(cat.document_ids) + 1 > protocol.MAX_SCHEMA_SOURCES:
        raise AnchorError('full_plan_source_count_unsupported')
    encoding = module.get_encoding('o200k_base')
    blocked, first, denied_count = _index(cat, encoding)
    rows, fixture_history = [], []
    # Cheap additive packing estimate, followed by exact recount of every
    # finished wire request. Oversized single sources STOP; never split text.
    source_sizes = {sid: _tokens(encoding, cat.model_source(sid)) +
                    _tokens(encoding, blocked.get(sid, [])) + 64 for sid in cat.document_ids}
    one_path = cat.source(cat.document_ids[0]).path
    _, one_wire = inspection(cat, (one_path,), blocked)
    base = _request_tokens(one_wire, encoding) - source_sizes[cat.document_ids[0]] + 2048
    pending, estimate = [], base

    def seal(ids):
        paths = [cat.source(sid).path for sid in ids]
        inner, wire = inspection(cat, paths, blocked)
        actual = _request_tokens(wire, encoding)
        if reference.padded(actual) > MAX_INPUT:
            if len(ids) == 1:
                raise AnchorError('full_plan_single_document_input_exceeded')
            seal(ids[:-1]); seal(ids[-1:]); return
        raw = canonical_json({'request_id': inner.payload['request_id'],
            'covered': {sid: first[sid] for sid in ids}, 'findings': []})
        validate_inspection(cat, inner, raw, encoding)
        fixture_history.append((inner, raw))
        rows.append({'index': len(rows)+1, 'source_paths': paths,
            'source_count': len(paths), 'inner_request_sha256': inner.sha256,
            'wire_request_sha256': wire.sha256,
            'wire_schema_sha256': digest(canonical_json(wire.schema)),
            'reference_input_tokens': actual, 'input_acceptance_tokens': reference.padded(actual),
            'output_acceptance_tokens': OUTPUT['inspect']})

    for sid in cat.document_ids:
        if pending and reference.padded(estimate + source_sizes[sid]) > MAX_INPUT:
            seal(pending); pending, estimate = [], base
        pending.append(sid); estimate += source_sizes[sid]
    if pending:
        seal(pending)
    paths = [path for row in rows for path in row['source_paths']]
    if len(set(paths)) != len(snapshot.sources) or set(paths) != {s.path for s in snapshot.sources}:
        raise AnchorError('full_plan_incomplete_or_duplicate_coverage')
    if len(rows) > 24:
        raise AnchorError('full_plan_too_many_inspection_batches')
    # Build all complete fixture results solely to prove the full scope and
    # schema can reach synthesis. They are NEVER represented as model findings.
    synth_inner = protocol.synthesis_request(cat, fixture_history)
    synth_wire = _wire(synth_inner, blocked, 'synthesize')
    empty = synth_wire.payload
    empty['anchor_request']['data']['findings'] = []
    empty['anchor_request']['data']['evidence_catalogue'] = []
    fixed = _tokens(encoding, INSTRUCTIONS + INSTRUCTIONS + canonical_json(empty)
                    + canonical_json(synth_wire.schema))
    max_pool = len(cat.document_ids) + len(rows)*MAX_FINDINGS*MAX_FINDING_REFS
    # Row and findings counts are validated on exact reference serialization;
    # spare boundary/hash tokens cover concatenation effects. Sol mapping and
    # hidden prompt overhead remain unproven. Exact recount is STILL mandatory.
    synth_reference = fixed + max_pool*(ROW_TOKENS+8) + len(rows)*(FINDINGS_TOKENS+16) + 512
    synth_limit = reference.padded(synth_reference)
    if synth_limit > MAX_INPUT:
        raise AnchorError('full_plan_synthesis_bound_unsupported')
    _, _, actual_fixture = synthesis(cat, fixture_history, blocked, encoding, synth_limit)
    total_in = sum(row['input_acceptance_tokens'] for row in rows) + synth_limit
    total_out = len(rows)*OUTPUT['inspect'] + OUTPUT['synthesize']
    price = round((total_in*50 + total_out*250)/1_000_000, 8)
    return {'state': 'nonpaid_plan_ready_execution_adapter_required',
        'snapshot_sha256': snapshot.sha256, 'catalogue_sha256': cat.sha256,
        'tokenizer': reference.tokenizer_identity(module), 'batches': rows,
        'blocked_anchor_ids': blocked, 'blocked_anchor_count': denied_count,
        'blocked_anchor_index_sha256': digest(canonical_json(blocked)),
        'citation_row_reference_limit': ROW_TOKENS, 'findings_reference_limit_per_batch': FINDINGS_TOKENS,
        'findings_max_per_batch': MAX_FINDINGS, 'evidence_max_per_finding': MAX_FINDING_REFS,
        'source_count': len(snapshot.sources), 'input_bytes': cat.stats()['source_text_bytes'],
        'complete_source_texts_preserved': True, 'coverage_planned': 1.0,
        'synthesis_fixed_reference_tokens': fixed, 'synthesis_max_evidence_rows': max_pool,
        'synthesis_reference_reservation': synth_reference,
        'synthesis_input_acceptance_tokens': synth_limit,
        'synthesis_fixture_actual_reference_tokens': actual_fixture,
        'synthesis_fixture_not_a_model_result': True,
        'input_acceptance_tokens_total': total_in, 'output_acceptance_tokens_total': total_out,
        'synthesis_output_acceptance_tokens': OUTPUT['synthesize'],
        'planned_inspections': len(rows), 'planned_syntheses': 1, 'planned_model_calls': len(rows)+1,
        'planning_standard_credits_no_cache': price, 'proposed_credit_acceptance': math.ceil(price/10)*10,
        'phase_seconds': {'inspect': 300, 'synthesize': 900},
        'run_seconds_acceptance': len(rows)*300+900,
        'time_basis': {'measured_small_synthesis_ms': 400240, 'measured_synthesis_output_tokens': 19837,
            'future_synthesis_output_tokens': 32000, 'output_scaled_seconds_with_25_percent_margin':
                round(400.240*32000/19837*1.25, 3), 'rounded_proposal_seconds': 900},
        'reference_multiplier': 1.25, 'overhead_reference_tokens_per_turn': 8000,
        'margin_proven_for_sol': False, 'live_context_limit_verified': False,
        'hard_billing_output_or_wallclock_cap': False, 'automatic_retry': False,
        'source_scope_approved': False, 'application_inventory_complete': False,
        'model_calls_started': 0, 'execution_adapter_implemented': False,
        'publication_authorized': False, 'weekly_activation': False,
        'rates_per_million': {'input': 50, 'cached_input': 2.5, 'output': 250},
        'rates_checked': '2026-11-08', 'rates_source': 'https://learn.chatgpt.com/docs/pricing#token-rates'}


def _code():
    return {**small._code(), 'app/recovery_guide_anchor_full_plan.py': digest(Path(__file__).read_bytes()),
            'app/recovery_guide_preflight.py': digest((ROOT/'app/recovery_guide_preflight.py').read_bytes())}


def prepare(*, refresh=False):
    """Read-only source/runtime audit + immutable private PLAN. No run() exists."""
    if any(p.is_symlink() for p in (STATE, *STATE.parents)):
        raise AnchorError('full_plan_state_alias')
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    if STATE.stat().st_uid != os.getuid() or STATE.stat().st_mode & 0o077:
        raise AnchorError('full_plan_state_not_private')
    for name in ('plan.json', 'job.lock', 'revisions'):
        if (STATE/name).is_symlink():
            raise AnchorError('full_plan_artifact_alias')
    with exclusive_file_lock(STATE/'job', timeout=0):
        path = STATE/'plan.json'
        previous = json.loads(path.read_text()) if path.exists() else None
        if previous and not refresh:
            return public_plan(previous)
        if refresh and not previous:
            raise AnchorError('full_plan_refresh_requires_original')
        head = old._head(); snapshot = collect_revision(ORIGINAL, head, ROOT)
        implementation = _code()
        measured = old._tokenizer('''import json,sys
from app.recovery_guide_costing import hydrate
from app.recovery_guide_anchor_full_plan import measure
print(json.dumps(measure(hydrate(json.load(sys.stdin)))))''', asdict(snapshot))
        from app.recovery_guide_preflight import runtime_observation
        runtime = runtime_observation()  # Registered read-only RPCs, NO thread/start.
        plan = {'request_id': 'rec06-anchors-full-plan-01',
            'prepared_at': datetime.now(timezone.utc).isoformat(), 'snapshot': asdict(snapshot),
            'measurements': measured, 'runtime': runtime, 'implementation': implementation,
            'model': 'gpt-6.1-sol', 'effort': 'medium', 'serviceTierForTurn': 'default',
            'old_jobs_reopened': False, 'paid_execution_approval_requested': False}
        if previous:
            plan['supersedes_plan_digest'] = previous['plan_digest']
        if (old._head() != head or ORIGINAL.is_symlink() or _code() != implementation
                or digest(ORIGINAL.read_bytes()) != snapshot.original.sha256):
            raise AnchorError('full_plan_inputs_changed_during_prepare')
        envelope = {'plan': plan, 'plan_digest': digest(canonical_json(plan))}
        target = STATE/'revisions'/(envelope['plan_digest']+'.json') if previous else path
        atomic_create_text(target, canonical_json(envelope))
        return public_plan(envelope)


def public_plan(envelope):
    p = envelope['plan']
    measurements = {k:v for k,v in p['measurements'].items() if k != 'blocked_anchor_ids'}
    try:
        current = (old._head() == p['snapshot']['head'] and not ORIGINAL.is_symlink()
            and digest(ORIGINAL.read_bytes()) == p['snapshot']['original']['sha256']
            and _code() == p['implementation'])
    except Exception:
        current = False
    return {k:v for k,v in p.items() if k not in {'snapshot','measurements','implementation'}} | {
        'plan_digest': envelope['plan_digest'], 'snapshot': hydrate(p['snapshot']).receipt(),
        'measurements': measurements, 'model_calls_started': 0,
        'paid_execution_available': False, 'publication_authorized': False,
        'frozen_inputs_current': current}
