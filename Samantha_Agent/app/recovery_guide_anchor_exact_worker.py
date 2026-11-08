"""Offline exact-index executor worker. No transport, writes or model calls.

Rebuild the immutable request-local reference map for every action. The raw
numeric reply is retained separately from the internal legacy resolver form.
"""
from app import recovery_guide_anchor_exact_plan as plan
from app import recovery_guide_anchor_exact_schema as exact
from app.recovery_guide_anchors import Catalogue, AnchorError
from app.recovery_guide_costing import hydrate
from app.recovery_guide_quality import QualityError
from app.recovery_guide_sources import canonical_json, digest


def _inspection(cat, measured, batch):
    bundle = exact.inspection(cat, batch['source_paths'], measured['blocked_anchor_ids'])
    if (bundle.wire.sha256 != batch['wire_request_sha256']
            or bundle.index.sha256 != batch['reference_index_sha256']
            or digest(canonical_json(bundle.wire.schema)) != batch['schema_sha256']):
        raise AnchorError('exact_pilot_inspection_request_changed')
    return bundle


def _history(cat, measured, rows, encoding):
    if not isinstance(rows, list) or len(rows) != len(measured['batches']):
        raise AnchorError('exact_pilot_history_incomplete')
    history = []
    for batch, row in zip(measured['batches'], rows):
        bundle = _inspection(cat, measured, batch)
        if (row['inner'] != bundle.inner.envelope_json or row['wire'] != bundle.wire.envelope_json
                or row['reference_index_sha256'] != bundle.index.sha256):
            raise AnchorError('exact_pilot_history_binding_changed')
        exact.resolve_inspection(cat, bundle, row['raw'], encoding)
        history.append((bundle, row['raw']))
    return history


def perform(action, frozen, *, index=None, history=None, raw=None, module=None):
    if module is None:
        import tiktoken as module
    snapshot = hydrate(frozen['snapshot']); measured = frozen['measurements']
    encoding = module.get_encoding('o200k_base')
    identity = plan.old.reference.tokenizer_identity(module)
    if identity != measured['tokenizer']:
        raise AnchorError('exact_pilot_tokenizer_changed')
    if action == 'audit':
        if canonical_json(plan.measure(snapshot, module)) != canonical_json(measured):
            raise AnchorError('exact_pilot_plan_recalculation_changed')
        if not measured['synthesis_within_current_240000_limit']:
            raise AnchorError('exact_pilot_synthesis_limit_unsupported')
        return {'tokenizer': identity, 'plan_recalculated': True,
                'protocol_version': exact.VERSION, 'model_calls': 0}
    cat = Catalogue(snapshot); count = len(measured['batches'])
    if type(index) is not int or not 1 <= index <= count + 1:
        raise AnchorError('exact_pilot_phase_outside_plan')
    if index <= count:
        bundle = _inspection(cat, measured, measured['batches'][index-1])
        if action == 'validate':
            result = exact.resolve_inspection(cat, bundle, raw, encoding)['result']
            return {'response_sha256': digest(raw), 'covered': len(result['legacy']['covered']),
                    'findings': len(result['findings']), 'tokenizer': identity,
                    'reference_index_sha256': bundle.index.sha256}
    else:
        accepted = _history(cat, measured, history, encoding)
        bundle = exact.synthesis(cat, accepted, measured['blocked_anchor_ids'], encoding,
                                 measured['synthesis_input_acceptance_tokens'])
        if action == 'validate':
            candidate = exact.validate_synthesis(cat, bundle, raw, snapshot, encoding)
            return {'candidate': candidate, 'candidate_sha256': digest(candidate),
                    'response_sha256': digest(raw), 'tokenizer': identity,
                    'reference_index_sha256': bundle.index.sha256,
                    'application_inventory_complete': False, 'publication_authorized': False}
    if action != 'request':
        raise AnchorError('exact_pilot_unknown_worker_action')
    tokens = exact.request_tokens(bundle, encoding)
    limit = (measured['batches'][index-1]['input_acceptance_tokens'] if index <= count
             else measured['synthesis_input_acceptance_tokens'])
    if plan.old.reference.padded(tokens) > limit:
        raise AnchorError('exact_pilot_reference_input_exceeded')
    return {'inner': bundle.inner.envelope_json, 'wire': bundle.wire.envelope_json,
            'reference_index_sha256': bundle.index.sha256,
            'reference_tokens': tokens, 'tokenizer': identity}


def dispatch(data):
    try:
        return {'ok': True, 'value': perform(**data)}
    except Exception as exc:
        code = str(exc) if isinstance(exc, (AnchorError, QualityError)) else type(exc).__name__
        return {'ok': False, 'code': code}
