"""Reference pricing for TWO small protocol turns, never full-corpus approval."""
import hashlib
from importlib.metadata import version
import math
from pathlib import Path

from app import recovery_guide_anchor_protocol as protocol
from app.recovery_guide_anchors import Catalogue
from app.recovery_guide_sources import canonical_json, digest

CASES = {
    'Samantha_Agent/camino/tasks/C01c_RECOVERABLE_AUDIO.md':
        '- restart aplikace nikdy sám nezapne mikrofon;',
    'Samantha_Agent/camino/tasks/C02b_CHUNK_TRANSFER_EXPERIMENT.md':
        '- oddělit 100 % odeslaných bytů od serverového `verified`;',
}
FINDING_BYTES = 1500
RAW_INSPECTION_BYTES = 14000
OUTPUT_LIMITS = {'inspect': 4096, 'synthesize': 32000}
INSTRUCTIONS = protocol.INSTRUCTIONS + '''
Toto je malá zkouška protokolu, ne revize celé dokumentace. V inspect vrať
právě dvě findings, každé s jedním odkazem a nejvýše 1500 UTF-8 byty textu:
jedno pro pravidlo, že restart aplikace sám nezapne mikrofon, druhé pro
oddělení odeslaných bytů od serverového verified. V covered použij tytéž řádky.
V synthesize vlož celý original doslovně jako jediný první paragraph se
statusem unchanged; zachovej jeho mezery a zalomení. Přidej dva krátké
samostatné odstavce se statusem unverified a těmito dvěma evidencemi.
Neoznačuj zkoušku za přijatý návod ani důkaz živého nastavení.'''


def expected_pairs(cat):
    pairs = []
    for path, quote in CASES.items():
        sid = cat.source_id(path)
        text = cat.source(sid).text
        if text.count(quote) != 1:
            raise ValueError('anchor_case_source_changed')
        ref = cat.reference_at(sid, text.index(quote))
        pairs.append((sid, ref['anchor_id']))
    return pairs


def fixture(cat, request):
    """Trusted pricing/test fixture only. Never a model result or acceptance."""
    pairs = expected_pairs(cat)
    return canonical_json({'request_id': request.payload['request_id'],
        'covered': dict(pairs), 'findings': [{'text': 'fixture', 'evidence': [
            {'source_id': sid, 'anchor_id': aid}]} for sid, aid in pairs]})


def tokenizer_identity(module):
    # This package is imported only in the caller's isolated tokenizer process.
    root = Path(module.__file__).resolve().parent
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob('*') if p.suffix in {'.py', '.so'}):
        h.update(path.relative_to(root).as_posix().encode()); h.update(path.read_bytes())
    enc = module.get_encoding('o200k_base')
    h.update(canonical_json({'pattern': enc._pat_str, 'special_tokens': enc._special_tokens}).encode())
    # Pin encoding table too, not just the Python wrapper version.
    for token, rank in sorted(enc._mergeable_ranks.items(), key=lambda r: r[1]):
        h.update(len(token).to_bytes(4, 'big')); h.update(token); h.update(rank.to_bytes(8, 'big'))
    return {'package': 'tiktoken', 'version': version('tiktoken'), 'encoding': 'o200k_base',
        'implementation_sha256': h.hexdigest(), 'exact_model_mapping': False,
        'full_appserver_prompt_exact': False}


def request_tokens(request, module):
    text = INSTRUCTIONS + INSTRUCTIONS + canonical_json(request.payload) + canonical_json(request.schema)
    return len(module.get_encoding('o200k_base').encode_ordinary(text))


def padded(reference):
    return math.ceil(reference * 1.25) + 8000


def measure(snapshot, module=None):
    if module is None:
        import tiktoken as module
    cat = Catalogue(snapshot)
    inspect = protocol.inspection_request(cat, tuple(CASES))
    synth = protocol.synthesis_request(cat, [(inspect, fixture(cat, inspect))])
    a, b = request_tokens(inspect, module), request_tokens(synth, module)
    # Two finding strings, each <=1500 UTF-8 bytes; canonical JSON can escape
    # each byte to <=6 ASCII bytes. One-byte BPE tokens give a conservative
    # reference allowance, plus variable request-hash tokenization. NOT Sol proof.
    allowance = 2 * FINDING_BYTES * 6 + 256
    limits = {'inspect': padded(a), 'synthesize': padded(b + allowance)}
    if max(limits.values()) > 150000:
        raise ValueError('anchor_small_trial_context_reservation_exceeded')
    credits = round((sum(limits.values()) * 50 + sum(OUTPUT_LIMITS.values()) * 250) / 1_000_000, 8)
    return {'tokenizer': tokenizer_identity(module), 'reference_input_tokens': {'inspect': a, 'synthesize_fixture': b},
        'synthesis_findings_reference_allowance': allowance,
        'input_acceptance_tokens': limits, 'output_acceptance_tokens': OUTPUT_LIMITS,
        'planning_standard_credits_no_cache': credits,
        'acceptance_standard_credits': math.ceil(credits), 'planned_calls': 2,
        'hard_billing_or_output_cap': False, 'model_context_limit_verified': False,
        'margin_proven_for_sol': False, 'reference_multiplier': 1.25,
        'overhead_allowance_per_turn': 8000, 'raw_inspection_bytes': RAW_INSPECTION_BYTES,
        'rates_per_million': {'input': 50, 'cached_input': 2.5, 'output': 250},
        'rates_checked': '2026-11-07', 'rates_source': 'https://learn.chatgpt.com/docs/pricing#token-rates',
        'inspect_request_sha256': inspect.sha256,
        'inspect_schema_sha256': digest(canonical_json(inspect.schema)),
        'synthesis_fixture_request_sha256': synth.sha256,
        'synthesis_request_is_dynamic': True, 'synthesis_fixture_schema_sha256': digest(canonical_json(synth.schema)),
        'snapshot_sha256': snapshot.sha256, 'catalogue_sha256': cat.sha256,
        'source_text_bytes': cat.stats()['source_text_bytes']}
