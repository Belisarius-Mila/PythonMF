"""Explicit continuation of one fully delivered inspection; no turn retry.

Original receipts remain byte-identical. Only a complete first result with
measured cost can be replayed locally. A single durable marker prevents a
second continuation, including after an unknown later delivery.
"""
from dataclasses import replace,asdict
from datetime import datetime,timezone
from pathlib import Path
import json,subprocess,math
from contextlib import contextmanager
from app import recovery_guide_maintainer as m,recovery_guide_consolidation as c
from app import recovery_guide_inspection as inspection
from app.recovery_guide_revalidation import owned_configuration,_observe,_client
from app.recovery_guide_runtime_live import build,live_calls
from app.recovery_guide_costing import hydrate
from app.recovery_guide_sources import canonical_json,digest,MAX_USER_INPUT_TEXT_CHARS
from app.file_persistence import atomic_create_text,atomic_write_json,exclusive_file_lock
from app.release_usage import normalize_usage,estimate_standard_credits,TOKEN_KEYS

ROOT=Path(__file__).resolve().parents[1]
FILES=('app/recovery_guide_known_result.py','app/recovery_guide_maintainer.py','app/recovery_guide_inspection.py','app/recovery_guide_runtime_live.py','app/recovery_guide_sources.py')


def implementation():return {name:digest((ROOT/name).read_bytes()) for name in FILES}

def _paths(config,request_id,stage="first"):
    from app.recovery_guide_scheduler import ID
    if not ID.fullmatch(request_id):raise ValueError('known_result_invalid_job')
    original=config.root/'analysis'/request_id
    recovery=config.root/'known-result'/request_id
    if stage not in {'first','received'}:raise ValueError('known_result_invalid_stage')
    if stage=='received':recovery=recovery/'received-prefix'
    if any(path.is_symlink() for path in (original,*original.parents,recovery,*recovery.parents)):raise ValueError('known_result_alias')
    return original,recovery

def _current(runtime,snapshot,original,head,config):
    config.guard()
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=head:return False
    current=runtime.snapshot_provider(original)
    return replace(current,head=snapshot.head).sha256==snapshot.sha256

def _known(config,request_id,counter):
    original,recovery=_paths(config,request_id)
    jobpath=config.root/'schedule'/(request_id+'.json');slot=request_id.removeprefix('recovery-')
    initial=(jobpath,original/'packet.json',original/'controller'/(slot+'.json'),original/'raw/001.json',original/'transport/001.json')
    if any(path.is_symlink() for item in initial for path in (item,*item.parents)):raise ValueError('known_result_artifact_alias')
    job=json.loads(jobpath.read_text())
    if job.get('slot')!=slot:raise ValueError('known_result_slot_changed')
    packet=json.loads((original/'packet.json').read_text());snapshot=hydrate(packet['snapshot'])
    status=json.loads((original/'controller'/(job['slot']+'.json')).read_text())
    rawpath=original/'raw/001.json';transportpath=original/'transport/001.json'
    checked_paths=(jobpath,original/'packet.json',original/'controller'/(job['slot']+'.json'),rawpath,transportpath)
    if any(path.is_symlink() for item in checked_paths for path in (item,*item.parents)):raise ValueError('known_result_artifact_alias')
    raw=json.loads(rawpath.read_text());transport=json.loads(transportpath.read_text());receipt=transport.get('receipt',{})
    if (job['state']!='attention' or status['state']!='attention' or status['model_calls']!=1 or status['completed_calls']!=1
        or status['coverage']!=0 or len(status['turns'])!=1 or packet['job_identity']!=job['identity_sha256']
        or snapshot.sha256!=job['snapshot_sha256'] or raw['state']!='received_unreviewed' or raw.get('phase')!='inspect' or transport.get('phase')!='inspect'
        or status['turns'][0].get('phase')!='inspect' or status['turns'][0].get('state')!='received'
        or receipt.get('delivered') is not True or receipt.get('status')!='completed'
        or receipt.get('turn_started_confirmed') is not True or receipt.get('user_item_count')!=1
        or transport.get('unexpected_item_types')!=[] or not receipt.get('turn_id') or not receipt.get('thread_id')
        or receipt.get('client_message_id')!=request_id+'-1'
        or sorted(path.name for path in (original/'raw').glob('*.json'))!=['001.json']
        or sorted(path.name for path in (original/'transport').glob('*.json'))!=['001.json']):raise ValueError('known_result_delivery_not_proven')
    usage=normalize_usage(receipt.get('thread_token_usage'));cost=estimate_standard_credits(m.MODEL,usage)
    duration=receipt.get('duration_ms')
    if type(duration) is not int or not 0<=duration<=config.payload['limits']['seconds']*1000:raise ValueError('known_result_duration_invalid')
    if usage is None or cost!=status['credits'] or normalize_usage(raw['response']['usage'])!=usage:raise ValueError('known_result_usage_changed')
    rawanswer=json.loads(receipt['answer'])
    logical=raw['response']['answer']
    names=[row['source'] for row in logical['covered'] if row['source']!=snapshot.original.path]
    count=len(names);payload={'original':asdict(snapshot.original),'sources':[asdict(row) for row in snapshot.sources[:count]]}
    compact=bool(rawanswer.get('covered')) and set(rawanswer['covered'][0])=={'i','q'}
    wire_payload=inspection.wire(payload) if compact else payload
    logical_sha=digest(canonical_json(payload))
    if logical_sha!=status['turns'][0]['payload_sha256']:raise ValueError('known_result_payload_not_exact')
    if raw.get('request_sha256',logical_sha)!=logical_sha or transport.get('request_sha256',digest(canonical_json(wire_payload)))!=digest(canonical_json(wire_payload)):raise ValueError('known_result_payload_not_exact')
    accepted=inspection.normalize(rawanswer,payload) if compact else inspection.normalize_known(rawanswer,payload)
    if accepted!=inspection.normalize_known(logical,payload):raise ValueError('known_result_answer_changed')
    first_instructions=m.REVIEW_INSTRUCTIONS+(inspection.instructions(config.payload['limits'].get('inspection_output_tokens',3000)) if compact else '')
    first_schema=inspection.SCHEMA if compact else m.INSPECT_SCHEMA
    first_bound=(counter(canonical_json(wire_payload))+counter(first_instructions)+counter(canonical_json(first_schema))+512)*50/1_000_000+config.payload['limits'].get('inspection_output_tokens',config.payload['limits']['output_tokens'])*250/1_000_000
    if cost>first_bound or usage['input_tokens']+usage['output_tokens']>config.payload['limits']['input_tokens']:raise ValueError('known_result_exceeds_original_admission')
    proof={'payload':payload,'response':{'answer':accepted,'usage':usage},'credits':cost,'maximum_known_credits':first_bound,
        'elapsed_seconds':math.ceil(duration/1000),'raw_sha256':digest(rawpath.read_bytes()),'transport_sha256':digest(transportpath.read_bytes()),'delivery_confirmed':True}
    return job,packet,snapshot,proof

def _prefix(config,request_id,counter,stage):
    job,packet,snapshot,first=_known(config,request_id,counter)
    if stage=='first':return job,packet,snapshot,first
    _,base=_paths(config,request_id);_,target=_paths(config,request_id,stage)
    prior=json.loads((base/'plan.json').read_text());attempt=json.loads((base/'attempt.json').read_text());directory=base/request_id
    controller=json.loads((directory/'controller'/(job['slot']+'.json')).read_text())
    if (prior['digest']!=digest(canonical_json(prior['plan'])) or attempt['plan_digest']!=prior['digest'] or attempt['state']!='attention'
        or controller['model_calls']!=2 or controller['completed_calls']!=1 or controller['coverage']!=len(first['payload']['sources'])
        or controller['state']!='attention' or controller['snapshot_sha256']!=snapshot.sha256 or controller['credits']!=first['credits']
        or prior['plan']['snapshot_sha256']!=snapshot.sha256 or prior['plan']['known_raw_sha256']!=first['raw_sha256']
        or len(controller['turns'])!=2 or controller['turns'][1]['state']!='in_flight'
        or sorted(p.name for p in (directory/'transport').glob('*.json'))!=['002.json']
        or list((directory/'raw').glob('*.json'))):raise ValueError('received_prefix_not_exact')
    path=directory/'transport/002.json'
    if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('received_prefix_alias')
    transport=json.loads(path.read_text());receipt=transport.get('receipt',{})
    if (transport.get('phase')!='inspect' or transport.get('state')!='received_unreviewed' or transport.get('unexpected_item_types')!=[]
        or receipt.get('delivered') is not True or receipt.get('status')!='completed' or receipt.get('turn_started_confirmed') is not True
        or receipt.get('user_item_count')!=1 or not receipt.get('thread_id') or not receipt.get('turn_id')
        or receipt.get('client_message_id')!=request_id+'-2'):raise ValueError('received_prefix_delivery_not_proven')
    start=len(first['payload']['sources']);count=prior['plan']['inspection_source_counts'][1]
    payload={'original':asdict(snapshot.original),'sources':[asdict(row) for row in snapshot.sources[start:start+count]]}
    if controller['turns'][1]['payload_sha256']!=digest(canonical_json(payload)):raise ValueError('received_prefix_payload_changed')
    raw=json.loads(receipt['answer']);review=json.loads((target/'reviewed-second.json').read_text())
    if review['transport_sha256']!=digest(path.read_bytes()):raise ValueError('received_prefix_receipt_changed')
    answer=review['answer'];accepted=inspection.normalize_known(answer,payload)
    # Editorial changes may repair quotations only; preserve complete original
    # indices, source identities, notes and all provider bytes.
    if (set(raw)!={'covered','notes'} or raw['notes']!=answer['notes'] or len(raw['covered'])!=count
        or any(type(row.get('i')) not in {int,float} or not math.isfinite(row['i']) or int(row['i'])!=row['i'] for row in raw['covered'])
        or sorted(row.get('i') for row in raw['covered'])!=list(range(count))
        or [row['source'] for row in accepted['covered']]!=[payload['sources'][int(row['i'])]['path'] for row in raw['covered']]):raise ValueError('received_prefix_edit_scope')
    usage=normalize_usage(receipt.get('thread_token_usage'));cost=estimate_standard_credits(m.MODEL,usage)
    maximum=(prior['plan']['limits']['input_tokens']*50+prior['plan']['limits']['inspection_output_tokens']*250)/1_000_000
    duration=receipt.get('duration_ms')
    if (usage is None or cost is None or cost>maximum or usage['input_tokens']+usage['output_tokens']>prior['plan']['limits']['input_tokens']
        or usage['output_tokens']>prior['plan']['limits']['inspection_output_tokens'] or type(duration) is not int or not 0<=duration<=prior['plan']['limits']['seconds']*1000):raise ValueError('received_prefix_usage_not_proven')
    second={'payload':payload,'response':{'answer':accepted,'usage':usage},'credits':cost,'maximum_known_credits':maximum,
        'elapsed_seconds':math.ceil(duration/1000),'raw_sha256':digest(path.read_bytes()),'transport_sha256':digest(path.read_bytes()),'delivery_confirmed':True}
    return job,packet,snapshot,[first,second]


def prepare(*,request_id,preview=False,stage='first',reviewed_second=None):
    config,_=owned_configuration();runtime,counter=build(config)
    try:
        original,recovery=_paths(config,request_id,stage);recovery.mkdir(parents=True,mode=0o700,exist_ok=True)
        with exclusive_file_lock(recovery/'operation',timeout=0):
            if stage=='received' and reviewed_second is not None:_once(recovery/'reviewed-second.json',canonical_json(reviewed_second))
            if not preview and subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('known_result_source_not_committed')
            if not preview and (recovery/'plan.json').exists():return json.loads((recovery/'plan.json').read_text())
            job,packet,snapshot,known=_prefix(config,request_id,counter,stage)
            head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
            if not _current(runtime,snapshot,Path(packet['source_path']),head,config):raise ValueError('known_result_documents_changed')
            # Lower future output reserve; compact evidence keeps the complete corpus.
            limits=replace(runtime.limits,inspection_output_tokens=min(2800,runtime.limits.inspection_reserve),run_credits=min(runtime.limits.run_credits,job['reserved_credits']),seconds=runtime.limits.seconds-sum(row['elapsed_seconds'] for row in (known if isinstance(known,list) else [known])))
            now=datetime.fromisoformat(packet['revision_time'])
            planned=m.plan(snapshot,counter,limits,review_date=now.date(),known_first=known)
            if planned['calls']>job['planned_calls'] or planned['reserved_credits']>job['reserved_credits']:raise ValueError('known_result_remaining_budget_not_approved')
            with _client() as client:runtime_observation=_observe(client,config)
            record={'runtime':runtime_observation,'request_id':request_id,'job_sha256':digest((config.root/'schedule'/(request_id+'.json')).read_bytes()),
                'activation_sha256':config.sha256,'source_head':head,'snapshot_sha256':snapshot.sha256,
                'known_review_sha256':digest((recovery/'reviewed-second.json').read_bytes()) if stage=='received' else None,'stage':stage,'known_count':len(known) if isinstance(known,list) else 1,'known_proofs':[{key:row[key] for key in ('raw_sha256','transport_sha256','credits','elapsed_seconds')} for row in (known if isinstance(known,list) else [known])],
                'known_raw_sha256':(known[0] if isinstance(known,list) else known)['raw_sha256'],'known_transport_sha256':(known[0] if isinstance(known,list) else known)['transport_sha256'],
                'known_credits':sum(row['credits'] for row in (known if isinstance(known,list) else [known])),'elapsed_known_seconds':sum(row['elapsed_seconds'] for row in (known if isinstance(known,list) else [known])),'original_result_sha256':digest((original/'result.json').read_bytes()),'original_reserved_credits':job['reserved_credits'],
                'inspection_source_counts':[len(row['sources']) for row in planned['shards']],'planned_credits':planned['reserved_credits'],'total_calls':planned['calls'],'remaining_provider_turns':planned['calls']-(len(known) if isinstance(known,list) else 1),
                'limits':asdict(limits),'implementation':implementation(),'automatic_retry':False}
            envelope={'plan':record,'digest':digest(canonical_json(record))}
            if not preview:atomic_create_text(recovery/'plan.json',canonical_json(envelope))
            return envelope
    finally:counter.close()

def run(*,request_id,approved_digest,confirmed=False,stage='first'):
    config,_=owned_configuration();runtime,counter=build(config);original,recovery=_paths(config,request_id,stage)
    try:
        with exclusive_file_lock(config.root/'schedule/scheduler',timeout=0),exclusive_file_lock(recovery/'operation',timeout=0):
            envelope=json.loads((recovery/'plan.json').read_text());plan=envelope['plan'];marker=recovery/'attempt.json'
            if confirmed is not True or approved_digest!=envelope['digest'] or digest(canonical_json(plan))!=approved_digest:raise ValueError('known_result_exact_confirmation_required')
            if marker.exists():return json.loads(marker.read_text())
            if config.sha256!=plan['activation_sha256'] or implementation()!=plan['implementation']:raise ValueError('known_result_implementation_changed')
            jobpath=config.root/'schedule'/(request_id+'.json')
            if digest(jobpath.read_bytes())!=plan['job_sha256']:raise ValueError('known_result_job_changed')
            job,packet,snapshot,known=_prefix(config,request_id,counter,stage)
            def current():
                return (implementation()==plan['implementation'] and _current(runtime,snapshot,Path(packet['source_path']),plan['source_head'],config)
                    and digest((original/'raw/001.json').read_bytes())==plan['known_raw_sha256']
                    and digest((original/'transport/001.json').read_bytes())==plan['known_transport_sha256']
                    and (stage=='first' or (digest((_paths(config,request_id)[1]/request_id/'transport/002.json').read_bytes())==plan['known_proofs'][1]['transport_sha256']
                        and digest((recovery/'reviewed-second.json').read_bytes())==plan['known_review_sha256'])))
            if not current():raise ValueError('known_result_inputs_changed')
            state={'state':'reserved','request_id':request_id,'plan_digest':approved_digest,'automatic_retry':False,'known_provider_turns':plan.get('known_count',1)};atomic_create_text(marker,canonical_json(state))
            directory=recovery/request_id;directory.mkdir(mode=0o700,exist_ok=True)
            @contextmanager
            def verified_client():
                with _client() as client:
                    if _observe(client,config)!=plan['runtime']:raise ValueError('known_result_runtime_changed')
                    yield client
            with live_calls(directory,job['executor'],assert_current=current,inspection_output_tokens=plan['limits']['inspection_output_tokens'],start_index=plan.get('known_count',1),client_factory=verified_client) as call:
                # Completed prefix turns are replayed locally, never through call().
                result=m.run(snapshot,state_dir=directory/'controller',now=datetime.fromisoformat(packet['revision_time']),
                    limits=m.Limits(**plan['limits']),count_tokens=counter,call=call,approved_snapshot=snapshot.sha256,
                    assert_sources=current,confirmed=True,known_first=known,weekday=runtime.scheduler.policy.weekday,hour=runtime.scheduler.policy.hour)
            atomic_write_json(directory/'result.json',result)
            state.update(state=result['state'],credits=result.get('credits'),completed_calls=result.get('completed_calls'));atomic_write_json(marker,state)
            if result['state']!='review':return state
            if result['state']=='review':
                state.update(coverage=result['coverage'],candidate_sha256=result['candidate_sha256'])
                atomic_write_json(marker,state)
            return state
    finally:counter.close()


def _review_state(recovery):
    envelope=json.loads((recovery/'plan.json').read_text());plan=envelope['plan'];state=json.loads((recovery/'attempt.json').read_text())
    if envelope['digest']!=digest(canonical_json(plan)) or state.get('plan_digest')!=envelope['digest']:raise ValueError('known_result_plan_changed')
    return plan,state


def prepare_publication(*,request_id,manual_answer=None,stage='first'):
    """Nonpaid editorial/quality review; original generated evidence is retained."""
    config,_=owned_configuration();runtime,counter=build(config);original,recovery=_paths(config,request_id,stage)
    try:
        plan,state=_review_state(recovery)
        if state['state']!='review' or implementation()!=plan['implementation']:raise ValueError('known_result_review_not_ready')
        packet=json.loads((original/'packet.json').read_text());snapshot=hydrate(packet['snapshot']);directory=recovery/request_id;slot=request_id.removeprefix('recovery-');controller=directory/'controller'
        if not _current(runtime,snapshot,Path(packet['source_path']),plan['source_head'],config):raise ValueError('known_result_documents_changed')
        result=json.loads((directory/'result.json').read_text());request=c.Request((controller/(slot+'-request.json')).read_text());generated=json.loads((controller/(slot+'-evidence.json')).read_text());answer=generated if manual_answer is None else manual_answer
        checked=c.validate(answer,snapshot,request);day=datetime.fromisoformat(packet['revision_time']).date();dossier,context=runtime.automatic_profile(snapshot,day)
        draft=runtime.publication.prepare(answer,snapshot,dossier,context,format_request=request)
        envelope={'binding_sha256':draft.sha256,'candidate_sha256':checked['candidate_sha256'],'generated_answer_sha256':digest(canonical_json(generated)),'reviewed_answer':answer,'packet':draft.packet_json}
        atomic_write_json(recovery/'publication-review.json',envelope)
        return {'state':'reviewed','binding_sha256':draft.sha256,'candidate_sha256':checked['candidate_sha256'],'operator_edit':answer!=generated}
    finally:counter.close()


def _once(path,text):
    if path.exists():
        if path.is_symlink() or path.read_text()!=text:raise ValueError('known_result_existing_artifact_changed')
    else:atomic_create_text(path,text)


def publish(*,request_id,confirmed_binding,confirmed=False,stage='first'):
    """Reconcile exact known analysis, then deliver; no analysis callback exists."""
    from app.recovery_guide_publication import PublicationDraft
    from app.recovery_guide_scheduler import DELIVERY,DONE
    config,_=owned_configuration();runtime,counter=build(config);original,recovery=_paths(config,request_id,stage)
    try:
        with exclusive_file_lock(recovery/'operation',timeout=0):
            plan,state=_review_state(recovery);review=json.loads((recovery/'publication-review.json').read_text());draft=PublicationDraft(review['packet'])
            if confirmed is not True or draft.sha256!=confirmed_binding or review['binding_sha256']!=confirmed_binding:raise ValueError('known_result_publication_confirmation_required')
            if state.get('confirmed_binding') not in {None,confirmed_binding}:raise ValueError('known_result_publication_binding_changed')
            if state['state'] in DONE:return state
            if implementation()!=plan['implementation'] or config.sha256!=plan['activation_sha256']:raise ValueError('known_result_implementation_changed')
            jobpath=config.root/'schedule'/(request_id+'.json');packet=json.loads((original/'packet.json').read_text());snapshot=hydrate(packet['snapshot']);directory=recovery/request_id;slot=request_id.removeprefix('recovery-');controller=directory/'controller'
            if state['state'] in {'review','attaching_result'}:
                if not _current(runtime,snapshot,Path(packet['source_path']),plan['source_head'],config):raise ValueError('known_result_documents_changed')
                with exclusive_file_lock(config.root/'schedule/scheduler',timeout=0):
                    job=json.loads(jobpath.read_text());result=json.loads((directory/'result.json').read_text());request=c.Request((controller/(slot+'-request.json')).read_text());answer=review['reviewed_answer'];checked=c.validate(answer,snapshot,request)
                    if checked['candidate_sha256']!=review['candidate_sha256']:raise ValueError('known_result_review_changed')
                    result={**result,'candidate_sha256':checked['candidate_sha256']}
                    usage={key:sum(row.get('usage',{}).get(key,0) for row in result['turns']) for key in TOKEN_KEYS}
                    analysis={'state':'review','request_id':request_id,'slot':slot,'snapshot_sha256':snapshot.sha256,'source_count':len(snapshot.sources),'coverage':result['coverage'],'candidate_sha256':result['candidate_sha256'],'executor':job['executor'],'usage':usage,'reported_model_turns':result['model_calls'],'publication':None,'simulation':False,'usage_complete':True,'format_contract':c.VERSION}
                    if state['state']=='review':
                        if digest(jobpath.read_bytes())!=plan['job_sha256']:raise ValueError('known_result_job_changed')
                        if digest((original/'result.json').read_bytes())!=plan['original_result_sha256']:raise ValueError('known_result_old_receipt_changed')
                        _once(recovery/'original-job.json',jobpath.read_text());_once(recovery/'original-result.json',(original/'result.json').read_text())
                        state.update(state='attaching_result',confirmed_binding=confirmed_binding);atomic_write_json(recovery/'attempt.json',state)
                    else:
                        if digest((recovery/'original-job.json').read_bytes())!=plan['job_sha256'] or digest((recovery/'original-result.json').read_bytes())!=plan['original_result_sha256']:raise ValueError('known_result_before_image_changed')
                    original_job=json.loads((recovery/'original-job.json').read_text());derived=json.loads(canonical_json(original_job));runtime.scheduler._result(derived,analysis)
                    if job['identity_sha256']!=original_job['identity_sha256'] or job['snapshot_sha256']!=snapshot.sha256:raise ValueError('known_result_job_changed')
                    if job['state'] not in {'attention','analysis_in_flight','awaiting_acceptance'}:raise ValueError('known_result_job_transition_changed')
                    if job['state']=='awaiting_acceptance' and (job.get('candidate_sha256')!=checked['candidate_sha256'] or job.get('usage')!=usage):raise ValueError('known_result_job_changed')
                    values={'-request.json':request.envelope,'-evidence.json':canonical_json(answer),'-candidate.txt':checked['candidate'],'-consolidation-audit.json':canonical_json({k:v for k,v in checked.items() if k!='candidate'})}
                    for suffix,value in values.items():_once(original/'controller'/(slot+suffix),value)
                    existing=(original/'result.json').read_bytes()
                    if digest(existing)!=plan['original_result_sha256'] and digest(canonical_json(json.loads(existing)))!=digest(canonical_json(result)):raise ValueError('known_result_old_receipt_changed')
                    atomic_write_json(original/'result.json',result)
                if job['state'] in {'attention','analysis_in_flight'}:
                    runtime.scheduler.reconcile_analysis(request_id,analysis,confirmed_identity=job['identity_sha256'],confirmed=True)
                state.update(state='awaiting_acceptance',candidate_sha256=checked['candidate_sha256']);atomic_write_json(recovery/'attempt.json',state)
            if state['state'] not in {'awaiting_acceptance','pending_icloud','delivery_ready','delivery_in_flight'}:raise ValueError('known_result_delivery_state')
            receipt=runtime.publication.accept(draft,request_id=request_id,confirmed_binding=confirmed_binding,confirmed=True)
            job=next(row for row in runtime.scheduler._jobs() if row['request_id']==request_id)
            runtime.scheduler.attach_publication(request_id,{'request_id':request_id,'approval_sha256':receipt['approval_sha256']},confirmed_identity=job['identity_sha256'],confirmed=True)
            runtime.assert_snapshot=lambda frozen,path:_current(runtime,snapshot,path,plan['source_head'],config)
            with exclusive_file_lock(config.root/'schedule/scheduler',timeout=0):
                job=next(row for row in runtime.scheduler._jobs() if row['request_id']==request_id)
                if job['state'] in DELIVERY:
                    delivered=runtime.scheduler._deliver(job,datetime.now().astimezone(),runtime.delivery_readiness,
                        lambda ref:runtime.publication.status(ref['request_id']),runtime._deliver)
                    state.update(state=delivered['state'])
                elif job['state'] in DONE:state.update(state=job['state'])
                else:raise ValueError('known_result_delivery_state')
            atomic_write_json(recovery/'attempt.json',state);return state
    finally:counter.close()


def apply_owned_code(*,request_id,expected_main_head,confirmed=False):
    """Deploy only reviewed recovery modules to the owned existing service.

    No LaunchAgent, process, role, network or unrelated worktree changes.
    Dirty/foreign destination files are refused and original bytes preserved.
    """
    import os
    config,_=owned_configuration();original,recovery=_paths(config,request_id)
    if confirmed is not True:raise ValueError('known_code_confirmation_required')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=expected_main_head:raise ValueError('known_code_source_changed')
    job=json.loads((config.root/'schedule'/(request_id+'.json')).read_text())
    if job['state'] not in {'completed','completed_no_change'}:raise ValueError('known_code_job_not_complete')
    names=('app/recovery_guide_sources.py','app/recovery_guide_inspection.py','app/recovery_guide_maintainer.py','app/recovery_guide_runtime_live.py','app/recovery_guide_anchor_transport.py','tests/test_recovery_guide_runtime.py')
    journal=config.root/'owned-code'/expected_main_head;journal.mkdir(parents=True,mode=0o700,exist_ok=True)
    receipt=journal/'receipt.json'
    with exclusive_file_lock(config.root/'schedule/scheduler',timeout=0),exclusive_file_lock(journal/'operation',timeout=0):
        if receipt.exists():
            result=json.loads(receipt.read_text())
            if any(digest((config.project/row['path']).read_bytes())!=row['after_sha256'] for row in result['files']):raise ValueError('known_code_deployment_changed')
            return result
        if any(json.loads(path.read_text()).get('state')=='analysis_in_flight' for path in (config.root/'schedule').glob('recovery-????-W??.json')):raise ValueError('known_code_active_model_job')
        saved_plan=journal/'plan.json'
        previous=json.loads(saved_plan.read_text()) if saved_plan.exists() else None
        if previous and (previous['source_head']!=expected_main_head or {row['path'] for row in previous['files']}!=set(names)):raise ValueError('known_code_plan_changed')
        rows=[];contents={}
        for name in names:
            source=ROOT/name;target=config.project/name
            if source.is_symlink() or target.is_symlink() or any(parent.is_symlink() for parent in target.parents):raise ValueError('known_code_alias')
            if target.exists() and target.stat().st_uid!=os.getuid():raise ValueError('known_code_foreign_owner')
            dirty=subprocess.check_output(['git','status','--porcelain','--',name],cwd=config.project,text=True).strip()
            committed=subprocess.check_output(['git','show',expected_main_head+':Samantha_Agent/'+name],cwd=ROOT)
            if source.read_bytes()!=committed:raise ValueError('known_code_uncommitted_source')
            contents[name]=committed.decode('utf-8')
            before=target.read_bytes() if target.exists() else None
            if previous:
                row=next(row for row in previous['files'] if row['path']==name)
                if row['after_sha256']!=digest(committed) or (digest(before) if before is not None else None) not in {row['before_sha256'],row['after_sha256']}:raise ValueError('known_code_destination_changed')
                if row['before_sha256'] is not None and digest((journal/'before'/name).read_bytes())!=row['before_sha256']:raise ValueError('known_code_before_image_changed')
            else:
                if dirty:raise ValueError('known_code_destination_dirty')
                if before is not None:
                    saved=journal/'before'/name;saved.parent.mkdir(parents=True,mode=0o700,exist_ok=True);_once(saved,before.decode())
                row={'path':name,'before_sha256':digest(before) if before is not None else None,'after_sha256':digest(committed)}
            rows.append(row)
        _once(journal/'plan.json',canonical_json({'source_head':expected_main_head,'files':rows}))
        from app.file_persistence import atomic_write_text
        for row in rows:
            target=config.project/row['path']
            if target.is_symlink():raise ValueError('known_code_alias')
            actual=digest(target.read_bytes()) if target.exists() else None
            if actual==row['after_sha256']:continue
            if actual!=row['before_sha256']:raise ValueError('known_code_destination_changed')
            atomic_write_text(target,contents[row['path']])
        if any(digest((config.project/row['path']).read_bytes())!=row['after_sha256'] for row in rows):raise ValueError('known_code_deployment_not_verified')
        result={'state':'completed','source_head':expected_main_head,'files':rows,'service_definition_changed':False,'restart':False,'unrelated_changes_preserved':True};atomic_write_json(receipt,result);return result
