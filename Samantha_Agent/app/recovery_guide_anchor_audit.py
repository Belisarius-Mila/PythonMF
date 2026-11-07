"""Read-only offline regression on the two closed REC-06 receipts.

Constructed ID responses are TEST FIXTURES, not new model responses. They do
not accept old notes, repair raw receipts or reopen their paid job. No SDK.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from app.recovery_guide_costing import hydrate
from app.recovery_guide_anchors import Catalogue, AnchorError
from app import recovery_guide_anchor_protocol as protocol
from app.recovery_guide_sources import canonical_json, digest

ROOT = Path(__file__).resolve().parents[1]
PARENT = '09a6ed5becbe07e8d2a5703e29639b5f30aff9c3a40db4af7f2220bf999f4e0b'


def audit_saved() -> dict:
    state = ROOT / '.venv/recovery_rec06_full_pilot'
    packet = json.loads((state / 'revisions' / (PARENT + '.json')).read_text())
    if digest(canonical_json(packet['packet'])) != packet['approval_digest'] or packet['approval_digest'] != PARENT:
        raise AnchorError('audit_saved_packet_changed')
    packet = packet['packet']
    snapshot = hydrate(packet['snapshot'])
    closed = json.loads((ROOT / 'memory/reports/recovery_guide_rec06_full_result_20261107.json').read_text())
    if closed['approved_manifest_digest'] != PARENT or closed['actual_sdk_turns'] != 2:
        raise AnchorError('audit_closed_result_changed')
    files = [state / 'turns/01.json', state / 'turns/02.json', state / 'attempt.json',
             state / 'receipt-recovery-attempt.json']
    before = {str(path): digest(path.read_bytes()) for path in files}
    cat = Catalogue(snapshot)
    # All full lines, including whitespace/CRLF, reconstruct the frozen source.
    for sid in (cat.original_id, *cat.document_ids):
        if ''.join(line[1] for line in cat.model_source(sid)['lines']) != cat.source(sid).text:
            raise AnchorError('audit_source_truncated')
    proposals = {(r['source'], r['model_quote']): r for r in closed['citation_issues']}
    inspections, checks = [], []
    for index, path in enumerate(files[:2]):
        raw = json.loads(path.read_text())
        receipt = raw['receipt']
        if raw['state'] != 'completed' or not receipt['delivered']:
            raise AnchorError('audit_delivery_not_known')
        if digest(path.read_bytes()) != closed['turns'][index]['receipt_sha256']:
            raise AnchorError('audit_raw_receipt_changed')
        response = json.loads(receipt['answer'])
        expected = packet['measurements']['shards'][index]['source_paths']
        if raw['payload_sha256'] != packet['measurements']['shards'][index]['payload_sha256']:
            raise AnchorError('audit_saved_payload_changed')
        request = protocol.inspection_request(cat, tuple(expected))
        covered, case_fixtures, original_rows = {}, 0, 0
        for row in response['covered']:
            if row['source'] == snapshot.original.path:
                original_rows += 1
                continue
            sid = cat.source_id(row['source'])
            source = cat.source(sid)
            quote = row['quote']
            if quote not in source.text:
                # Explicit previously-reviewed regression fixture only. No
                # generic fuzzy match, lowercasing or changes to the live result.
                proposal = proposals.get((row['source'], quote))
                if not proposal or proposal['source_sha256'] != source.sha256 or not proposal['review_only']:
                    raise AnchorError('audit_unknown_nonliteral_case')
                quote = proposal['source_quote']
                if source.text.count(quote) != 1:
                    raise AnchorError('audit_fixture_quote_not_unique')
                case_fixtures += 1
            ref = cat.reference_at(sid, source.text.index(quote))
            if sid in covered:
                raise AnchorError('audit_duplicate_source')
            covered[sid] = ref['anchor_id']
        fixture = canonical_json({'request_id': request.payload['request_id'], 'covered': covered, 'findings': []})
        resolved = protocol.resolve_inspection(cat, request, fixture)
        if {r['source'] for r in resolved['legacy']['covered']} != set(expected):
            raise AnchorError('audit_incomplete_fixture')
        inspections.append((request, fixture))
        old_payload = {'original': asdict(snapshot.original),
            'sources': [asdict(s) for s in snapshot.sources if s.path in expected]}
        checks.append({'batch': index + 1, 'sources': len(covered), 'case_regression_fixtures': case_fixtures,
            'original_excluded_from_coverage_fixture': original_rows,
            'old_payload_bytes': len(canonical_json(old_payload).encode()),
            'anchored_payload_bytes': len(canonical_json(request.payload).encode()),
            'response_schema_bytes': len(canonical_json(request.schema).encode()),
            'all_resolved_quotes_exact': True, 'fixture_not_a_model_response': True})
    try:
        protocol.synthesis_request(cat, inspections)
    except AnchorError as exc:
        if str(exc) != 'incomplete_snapshot_coverage':
            raise
    else:
        raise AnchorError('audit_partial_history_incorrectly_accepted')
    covered_paths, input_bytes, schema_bytes = [], 0, 0
    for batch in packet['measurements']['shards']:
        request = protocol.inspection_request(cat, tuple(batch['source_paths']))
        input_bytes += len(canonical_json(request.payload).encode())
        schema_bytes += len(canonical_json(request.schema).encode())
        covered_paths.extend(batch['source_paths'])
    if len(covered_paths) != len(set(covered_paths)) or set(covered_paths) != {s.path for s in snapshot.sources}:
        raise AnchorError('audit_full_manifest_incomplete')
    if before != {str(path): digest(path.read_bytes()) for path in files}:
        raise AnchorError('audit_old_job_changed')
    return {'state': 'offline_anchor_regression_passed', **cat.stats(),
        'saved_receipts_checked': 2, 'fixture_documents': sum(c['sources'] for c in checks),
        'case_regression_fixtures': sum(c['case_regression_fixtures'] for c in checks),
        'checks': checks, 'full_inspection_requests_built': len(packet['measurements']['shards']),
        'full_manifest_documents': len(covered_paths), 'all_inspection_payload_bytes': input_bytes,
        'all_inspection_schema_bytes': schema_bytes,
        'old_paid_job_unchanged': True, 'old_notes_reaccepted': False,
        'partial_history_synthesis_refused': True, 'live_anchor_model_tested': False,
        'model_calls': 0, 'publication_authorized': False, 'new_trial_pricing_required': True}
