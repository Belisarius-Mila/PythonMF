"""Nonpaid exact-index schema plan. Does NOT alter or execute closed pilots."""
from dataclasses import asdict
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path

from app import recovery_guide_anchor_exact_schema as exact
from app import recovery_guide_anchor_full_plan as old
from app.recovery_guide_anchors import Catalogue,AnchorError
from app.recovery_guide_costing import hydrate
from app.recovery_guide_revision import collect_revision
from app.recovery_guide_sources import canonical_json,digest
from app.file_persistence import atomic_create_text,exclusive_file_lock

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'.venv/recovery_rec06_anchor_exact_plan'


def _schema_reservation(bundle,encoding,extra_rows):
    # Grouping by domain length bounds the branch count. Starting with one
    # mandatory coverage citation per document, d new distinct lengths need
    # at least 1+2+...+d extra selected rows. Original contributes one group.
    groups=2+int((math.sqrt(1+8*extra_rows)-1)//2)
    groups=min(groups,len(bundle.index.sources))
    schema=bundle.wire.schema;schema['$defs']['reference']={'anyOf':[]}
    base=old._tokens(encoding,schema)
    branch=exact._object({'source_id':{'type':'string','enum':[]},
        'citation_index':{'type':'integer','minimum':1,'maximum':1}})
    max_digits=max(len(str(len(v))) for v in bundle.index.sources.values())
    per_branch=old._tokens(encoding,branch)+max_digits+16
    enums=sum(old._tokens(encoding,canonical_json(sid))+2 for sid in bundle.index.sources)
    return base+groups*per_branch+enums+256,groups


def measure(snapshot,module=None):
    if module is None:import tiktoken as module
    baseline=old.measure(snapshot,module)
    encoding=module.get_encoding('o200k_base');cat=Catalogue(snapshot)
    blocked=baseline['blocked_anchor_ids'];rows=[];history=[]
    max_stats={'object_properties':0,'enum_values':0,'schema_name_enum_characters':0,'max_depth':0,'json_bytes':0}

    def seal(paths):
        bundle=exact.inspection(cat,paths,blocked);count=exact.request_tokens(bundle,encoding)
        if old.reference.padded(count)>old.MAX_INPUT:
            if len(paths)==1:raise AnchorError('exact_single_source_input_unsupported')
            seal(paths[:-1]);seal(paths[-1:]);return
        raw=canonical_json({'request_id':bundle.wire.payload['request_id'],
            'covered':{cat.source_id(path):1 for path in paths},'findings':[]})
        exact.resolve_inspection(cat,bundle,raw,encoding);history.append((bundle,raw))
        stats=exact.schema_stats(bundle.wire.schema)
        for k,v in stats.items():max_stats[k]=max(max_stats[k],v)
        rows.append({'index':len(rows)+1,'source_paths':list(paths),'source_count':len(paths),
            'wire_request_sha256':bundle.wire.sha256,'reference_index_sha256':bundle.index.sha256,
            'schema_sha256':digest(canonical_json(bundle.wire.schema)),
            'reference_input_tokens':count,'input_acceptance_tokens':old.reference.padded(count),
            'output_acceptance_tokens':old.OUTPUT['inspect'],'schema_stats':stats})

    for batch in baseline['batches']:seal(batch['source_paths'])
    paths=[path for row in rows for path in row['source_paths']]
    if len(set(paths))!=len(snapshot.sources) or len(paths)!=len(snapshot.sources):
        raise AnchorError('exact_plan_coverage_changed')
    if len(rows)>24:raise AnchorError('exact_plan_batch_limit')
    bundle=exact.synthesis(cat,history,blocked,encoding,10**12)
    payload=bundle.wire.payload;payload['data']['findings']=[];payload['data']['evidence_catalogue']=[]
    extra=len(rows)*old.MAX_FINDINGS*old.MAX_FINDING_REFS
    schema_reserve,groups=_schema_reservation(bundle,encoding,extra)
    fixed=old._tokens(encoding,exact.INSTRUCTIONS+exact.INSTRUCTIONS+canonical_json(payload))
    pool=len(cat.document_ids)+extra
    reference=fixed+schema_reserve+pool*(old.ROW_TOKENS+8)+len(rows)*(old.FINDINGS_TOKENS+16)+512
    limit=old.reference.padded(reference)
    total_in=sum(row['input_acceptance_tokens'] for row in rows)+limit
    total_out=len(rows)*old.OUTPUT['inspect']+old.OUTPUT['synthesize']
    price=round((total_in*50+total_out*250)/1e6,8)
    actual_schema_stats=exact.schema_stats(bundle.wire.schema)
    for k,v in actual_schema_stats.items():max_stats[k]=max(max_stats[k],v)
    return {'protocol':exact.VERSION,'state':'offline_exact_plan_adapter_not_integrated',
        'snapshot_sha256':snapshot.sha256,'catalogue_sha256':cat.sha256,
        'source_count':len(paths),'input_bytes':cat.stats()['source_text_bytes'],
        'tokenizer':baseline['tokenizer'],'batches':rows,'blocked_anchor_ids':blocked,
        'blocked_anchor_count':baseline['blocked_anchor_count'],'schema_stats_max':max_stats,
        'synthesis_fixture_schema_stats':actual_schema_stats,'synthesis_schema_groups_upper':groups,
        'synthesis_schema_reference_reservation':schema_reserve,'synthesis_payload_fixed_reference_tokens':fixed,
        'synthesis_reference_reservation':reference,'synthesis_input_acceptance_tokens':limit,
        'synthesis_within_current_240000_limit':limit<=old.MAX_INPUT,
        'synthesis_fixture_actual_reference_tokens':exact.request_tokens(bundle,encoding),
        'synthesis_max_evidence_rows':pool,'synthesis_fixture_not_a_model_result':True,
        'input_acceptance_tokens_total':total_in,'output_acceptance_tokens_total':total_out,
        'planned_inspections':len(rows),'planned_syntheses':1,'planned_model_calls':len(rows)+1,
        'planning_standard_credits_no_cache':price,'proposed_credit_acceptance':math.ceil(price/10)*10,
        'baseline_planning_standard_credits_no_cache':baseline['planning_standard_credits_no_cache'],
        'credit_delta':round(price-baseline['planning_standard_credits_no_cache'],8),
        'phase_seconds':baseline['phase_seconds'],'run_seconds_acceptance':len(rows)*300+900,
        'integer_indices_are_request_local':True,'long_blank_and_foreign_references_excluded':True,
        'all_source_texts_preserved':True,'execution_adapter_integrated':False,
        'provider_acceptance_live_verified':False,'reference_is_exact_sol_tokenizer':False,
        'hard_billing_or_output_cap':False,'automatic_retry':False,
        'model_calls':0,'publication_authorized':False,'old_jobs_reopened':False,
        'rates_per_million':baseline['rates_per_million'],'rates_checked':baseline['rates_checked'],
        'rates_source':baseline['rates_source']}


def _code():
    return {**old._code(),**{name:digest((ROOT/name).read_bytes()) for name in
        ('app/recovery_guide_anchor_exact_schema.py','app/recovery_guide_anchor_exact_plan.py')}}


def public_plan(envelope):
    p=envelope['plan'];measured={k:v for k,v in p['measurements'].items() if k!='blocked_anchor_ids'}
    try:
        current=(old.old._head()==p['snapshot']['head'] and not old.ORIGINAL.is_symlink()
            and digest(old.ORIGINAL.read_bytes())==p['snapshot']['original']['sha256'] and _code()==p['implementation'])
    except Exception:current=False
    return {k:v for k,v in p.items() if k not in {'snapshot','implementation','measurements'}}|{
        'plan_digest':envelope['plan_digest'],'snapshot':hydrate(p['snapshot']).receipt(),
        'measurements':measured,'frozen_inputs_current':current,'paid_execution_available':False}


def prepare(*,refresh=False):
    if any(path.is_symlink() for path in (STATE,*STATE.parents)):
        raise AnchorError('exact_plan_state_alias')
    STATE.mkdir(mode=0o700,parents=True,exist_ok=True)
    if STATE.stat().st_uid!=os.getuid() or STATE.stat().st_mode & 0o077:
        raise AnchorError('exact_plan_state_not_private')
    for path in STATE.rglob('*'):
        if path.is_symlink():raise AnchorError('exact_plan_artifact_alias')
    with exclusive_file_lock(STATE/'job',timeout=0):
        path=STATE/'plan.json';previous=json.loads(path.read_text()) if path.exists() else None
        if previous and not refresh:return public_plan(previous)
        if refresh and not previous:raise AnchorError('exact_plan_refresh_requires_original')
        head=old.old._head();snapshot=collect_revision(old.ORIGINAL,head,ROOT);code=_code()
        measured=old.old._tokenizer('''import json,sys
from app.recovery_guide_costing import hydrate
from app.recovery_guide_anchor_exact_plan import measure
print(json.dumps(measure(hydrate(json.load(sys.stdin)))))''',asdict(snapshot))
        plan={'request_id':'rec06-exact-index-plan-01','prepared_at':datetime.now(timezone.utc).isoformat(),
            'snapshot':asdict(snapshot),'measurements':measured,'implementation':code,
            'model':'gpt-6.1-sol','effort':'medium','serviceTierForTurn':'default',
            'paid_execution_approval_requested':False,'model_calls':0}
        if previous:plan['supersedes_plan_digest']=previous['plan_digest']
        if (old.old._head()!=head or _code()!=code or old.ORIGINAL.is_symlink()
                or digest(old.ORIGINAL.read_bytes())!=snapshot.original.sha256):
            raise AnchorError('exact_plan_changed_during_prepare')
        envelope={'plan':plan,'plan_digest':digest(canonical_json(plan))}
        target=STATE/'revisions'/(envelope['plan_digest']+'.json') if previous else path
        atomic_create_text(target,canonical_json(envelope))
        return public_plan(envelope)
