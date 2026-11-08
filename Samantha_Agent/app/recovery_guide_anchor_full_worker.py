"""Pure offline worker for the full pilot's isolated tokenizer interpreter.

No transport, model invocation, file writes or publication. Safe diagnostics
only. Full requests and candidates travel solely through the private pipe.
"""
from app import recovery_guide_anchor_full_plan as plan
from app import recovery_guide_anchor_protocol as protocol
from app.recovery_guide_anchors import Catalogue, AnchorError
from app.recovery_guide_costing import hydrate
from app.recovery_guide_quality import QualityError
from app.recovery_guide_sources import canonical_json, digest


def _history(cat, measured, rows, encoding):
    if not isinstance(rows, list) or len(rows) != len(measured['batches']):
        raise AnchorError('full_anchor_history_incomplete')
    history = []
    for batch, row in zip(measured['batches'], rows):
        inner, wire = plan.inspection(cat, batch['source_paths'], measured['blocked_anchor_ids'])
        if (inner.sha256 != batch['inner_request_sha256'] or wire.sha256 != batch['wire_request_sha256']
                or row['inner'] != inner.envelope_json):
            raise AnchorError('full_anchor_history_binding_changed')
        plan.validate_inspection(cat, inner, row['raw'], encoding)
        history.append((inner, row['raw']))
    return history


def perform(action, frozen, *, index=None, history=None, raw=None, module=None):
    if module is None:
        import tiktoken as module
    snapshot = hydrate(frozen['snapshot']); measured = frozen['measurements']
    encoding = module.get_encoding('o200k_base')
    identity = plan.reference.tokenizer_identity(module)
    if identity != measured['tokenizer']:
        raise AnchorError('full_anchor_tokenizer_changed')
    if action == 'audit':
        if canonical_json(plan.measure(snapshot, module)) != canonical_json(measured):
            raise AnchorError('full_anchor_plan_recalculation_changed')
        return {'tokenizer': identity, 'plan_recalculated': True, 'model_calls': 0}
    cat = Catalogue(snapshot)
    count = len(measured['batches'])
    if type(index) is not int or not 1 <= index <= count + 1:
        raise AnchorError('full_anchor_phase_outside_plan')
    if index <= count:
        batch = measured['batches'][index-1]
        inner, wire = plan.inspection(cat, batch['source_paths'], measured['blocked_anchor_ids'])
        if (inner.sha256 != batch['inner_request_sha256'] or wire.sha256 != batch['wire_request_sha256']
                or digest(canonical_json(wire.schema)) != batch['wire_schema_sha256']):
            raise AnchorError('full_anchor_inspection_request_changed')
        if action == 'validate':
            result = plan.validate_inspection(cat, inner, raw, encoding)
            return {'response_sha256': digest(raw), 'covered': len(result['legacy']['covered']),
                    'findings': len(result['findings']), 'tokenizer': identity}
    else:
        accepted = _history(cat, measured, history, encoding)
        inner, wire, _ = plan.synthesis(cat, accepted, measured['blocked_anchor_ids'], encoding,
                                        measured['synthesis_input_acceptance_tokens'])
        if action == 'validate':
            decoded = protocol.resolve_synthesis(cat, inner, raw)
            for paragraph, original in zip(decoded['paragraphs'], protocol._parse(raw)['paragraphs']):
                for citation, ref in zip(paragraph['evidence'], original['evidence']):
                    row = plan._row(cat, ref['source_id'], ref['anchor_id'], citation['quote'])
                    if plan._tokens(encoding, row) > plan.ROW_TOKENS:
                        raise AnchorError('full_anchor_final_citation_reservation_exceeded')
            candidate = protocol.validate_synthesis(cat, inner, raw, snapshot)
            return {'candidate': candidate, 'candidate_sha256': digest(candidate),
                'response_sha256': digest(raw), 'tokenizer': identity,
                'application_inventory_complete': False, 'publication_authorized': False}
    if action != 'request':
        raise AnchorError('full_anchor_unknown_worker_action')
    tokens = plan._request_tokens(wire, encoding)
    limit = (measured['batches'][index-1]['input_acceptance_tokens'] if index <= count
             else measured['synthesis_input_acceptance_tokens'])
    if plan.reference.padded(tokens) > limit:
        raise AnchorError('full_anchor_reference_input_exceeded')
    return {'inner': inner.envelope_json, 'wire': wire.envelope_json,
            'reference_tokens': tokens, 'tokenizer': identity}


def dispatch(data):
    try:
        return {'ok': True, 'value': perform(**data)}
    except Exception as exc:
        code = str(exc) if isinstance(exc, (AnchorError, QualityError)) else type(exc).__name__
        return {'ok': False, 'code': code}
