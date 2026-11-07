"""Nonpaid reference planning with explicit, unproven safety margins.

Run measurement only in the worktree's isolated tokenizer environment. Counts
are for o200k_base, NOT an exact Sol mapping or a guaranteed billing ceiling.
"""
from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
import math

from app import recovery_guide_maintainer as m
from app.recovery_guide_preflight import PROPOSED_LIMITS, tokenizer_probe
from app.recovery_guide_sources import Snapshot, Source, canonical_json, digest

REFERENCE_MULTIPLIER = 1.25
PER_TURN_OVERHEAD = 8000


def hydrate(raw: dict) -> Snapshot:
    return Snapshot(raw['head'], Source(**raw['original']), tuple(Source(**r) for r in raw['sources']),
                    tuple(raw['scopes']), raw['excluded_text_files'])


def padded_count(text: str, reference: int) -> int:
    return math.ceil(reference * REFERENCE_MULTIPLIER) + (PER_TURN_OVERHEAD if text == m.INSTRUCTIONS else 0)


def measure(snapshot: Snapshot, *, module=None) -> dict:
    if module is None:
        import tiktoken as module
    encoding = module.get_encoding('o200k_base')
    counts = {}

    @lru_cache(maxsize=8)
    def count(text):
        key = digest(text)
        if key not in counts:
            counts[key] = len(encoding.encode_ordinary(text))
        return counts[key]

    baseline = m.plan(snapshot, count, PROPOSED_LIMITS)
    proposal = m.plan(snapshot, lambda text: padded_count(text, count(text)), PROPOSED_LIMITS)
    # Round the acceptance budget upward. Neither this nor m.plan's reservation
    # is an enforced output/token/billing cap on the App Server transport.
    credit_limit = math.ceil(proposal['reserved_credits'] / 10) * 10
    limits = asdict(PROPOSED_LIMITS) | {'run_credits': credit_limit, 'month_credits': credit_limit}
    return {'reference_encoding': 'o200k_base', 'tokenizer': tokenizer_probe(module),
        'model_tokenization_verified': False, 'reference_multiplier': REFERENCE_MULTIPLIER,
        'overhead_allowance_per_turn': PER_TURN_OVERHEAD, 'margin_is_proven_upper_bound': False,
        'baseline_reference_credits': baseline['reserved_credits'],
        'planning_standard_credits_with_margin': proposal['reserved_credits'],
        'input_planning_tokens_with_margin': proposal['input_bound'],
        'output_acceptance_tokens': proposal['output_bound'], 'planned_calls': proposal['calls'],
        'limits': limits, 'hard_billing_cap': False, 'cache_assumed': False,
        'shards': [{'index': i, 'source_count': len(p['sources']),
                    'source_paths': [s['path'] for s in p['sources']],
                    'payload_sha256': digest(canonical_json(p))} for i, p in enumerate(proposal['shards'])],
        'reference_counts': counts}
