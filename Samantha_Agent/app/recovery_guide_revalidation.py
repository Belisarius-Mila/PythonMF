"""One explicit, immutable runtime revalidation; never retries a model turn.

Keeps the existing role, files, schedule time and LaunchAgent. A successful
probe permits runtime_evidence replacement and only an exact explicitly
approved optional per-run budget/inspection-reserve refresh.
"""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone
import json
import subprocess
from dataclasses import replace
import os
import plistlib
import re

from app.file_persistence import atomic_create_text, atomic_write_json, exclusive_file_lock
from app.recovery_guide_sources import canonical_json, digest, MAX_USER_INPUT_TEXT_CHARS
from app import recovery_guide_runtime_config as configuration
from app.recovery_guide_runtime_live import IsolatedCounter
from app.recovery_guide_anchor_transport import StandardTurn
from app.recovery_guide_trial import MODEL, PEER, DISABLED_FEATURES, _socket
from app.release_usage import normalize_usage, estimate_standard_credits

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'data/private/recovery_runtime_revalidation'
INSTRUCTIONS = 'Read only the supplied synthetic data. Return the values of headTag, middleTag and tailTag as JSON. Do not use tools or other agents.'
SCHEMA = {'type':'object','properties':{k:{'type':'string'} for k in ('headTag','middleTag','tailTag')},'required':['headTag','middleTag','tailTag'],'additionalProperties':False}


def _now():return datetime.now(timezone.utc).isoformat()

def _client():
    from app.communication.luna_release import new_luna_client
    return new_luna_client()

def owned_configuration():
    agent = Path.home()/'Library/LaunchAgents/com.samantha.recovery-guide.plist'
    if agent.is_symlink() or agent.stat().st_uid != os.getuid():raise ValueError('revalidation_foreign_agent')
    spec = plistlib.loads(agent.read_bytes());project = Path(spec['WorkingDirectory'])
    if spec['Label'] != 'com.samantha.recovery-guide' or spec['ProgramArguments'] != [str(project/'.venv/bin/python'),str(project/'scripts/recovery_guide.py'),'tick']:
        raise ValueError('revalidation_foreign_agent')
    config = configuration.load(project)
    if config is None:raise ValueError('revalidation_activation_required')
    config.guard()
    return config, digest(agent.read_bytes())

def _protocol(config):
    root=config.project;schema=root/'.venv/recovery_rec06_peer_schema/v2'
    turn=(schema/'TurnStartParams.json').read_bytes();thread=(schema/'ThreadStartResponse.json').read_bytes()
    prop=json.loads(turn)['properties'].get('serviceTierForTurn',{})
    if prop.get('type')!=['string','null'] or 'standard speed' not in prop.get('description',''):
        raise ValueError('revalidation_standard_contract_missing')
    package=json.loads((root/'.venv/recovery_rec06_cli/node_modules/@openai/codex/package.json').read_text())
    if package.get('version')!=PEER:raise ValueError('revalidation_reviewed_protocol_changed')
    features=(root/'.venv/recovery_rec06_disabled_features.txt').read_text()
    rows={parts[0]:parts[-1] for line in features.splitlines() if len(parts:=line.split())>=3}
    if any(rows.get(name)!='false' for name in DISABLED_FEATURES):raise ValueError('revalidation_feature_contract_missing')
    return digest(canonical_json({'version':PEER,'disabled_features_sha256':digest(features),
        'turn_schema_sha256':digest(turn),'thread_schema_sha256':digest(thread)}))

def _observe(client,config):
    from app.communication.agent_roles import resolve_role
    selected = resolve_role(client.list_models(include_hidden=True),role='recovery_document_maintainer')
    account = client.transport.request('account/read',{'refreshToken':False}).get('account')
    if not isinstance(account,dict) or account.get('type') != 'chatgpt':raise ValueError('revalidation_subscription_required')
    if (selected['model'] != MODEL or selected['reasoning_effort'] != 'medium' or selected.get('fallback')
            or selected['policy_digest'] != config.payload['schedule']['role_policy_digest']):
        raise ValueError('revalidation_role_changed')
    protocol = _protocol(config)
    if protocol != config.payload['runtime_evidence']['protocol_sha256']:raise ValueError('revalidation_protocol_review_required')
    return {'server_version':client.server_version.raw,'protocol_sha256':protocol,'socket':_socket(client),'role_policy_digest':selected['policy_digest']}

def _implementation():
    return {name:digest((ROOT/name).read_bytes()) for name in ('app/recovery_guide_revalidation.py','app/recovery_guide_anchor_transport.py','app/recovery_guide_trial.py','app/routine_tasks.py','app/codex_appserver.py')}

def _root(request_id):
    if not isinstance(request_id,str) or not re.fullmatch('[a-zA-Z0-9_-]{12,80}',request_id):raise ValueError('revalidation_request_id')
    path = STATE/request_id
    if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('revalidation_alias')
    path.mkdir(parents=True,mode=0o700,exist_ok=True)
    return path

def _macos():
    return subprocess.check_output(["/usr/bin/sw_vers","-productVersion"],text=True,timeout=10).strip()

def _budget_snapshot(config,macos_baseline=None,max_calls=None):
    from app.recovery_guide_runtime_live import build,configuration_source
    runtime,unused=build(config)
    try:snapshot=runtime.snapshot_provider(runtime._original())
    finally:unused.close()
    proposed=config.payload
    if macos_baseline is not None:proposed['publication_policy']['macos_baseline']=macos_baseline
    if max_calls is not None:
        proposed['schedule']['max_calls']=max_calls;proposed['limits']['max_calls']=max_calls
    proposed['schedule']['run_credits']=250
    proposed['limits'].update(run_credits=250,inspection_output_tokens=3000)
    configuration.validate_payload(proposed)
    source=configuration_source(proposed)
    return replace(snapshot,sources=tuple(source if item.path==source.path else item for item in snapshot.sources)),proposed

def _budget_plan(config,counter,macos_baseline=None,max_calls=None):
    from app import recovery_guide_maintainer as maintainer
    from zoneinfo import ZoneInfo
    snapshot,proposed=_budget_snapshot(config,macos_baseline,max_calls)
    planned=maintainer.plan(snapshot,counter,maintainer.Limits(**proposed['limits']),review_date=datetime.now(ZoneInfo('Europe/Prague')).date())
    return {'max_calls':proposed['limits']['max_calls'],'run_credits':250,'inspection_output_tokens':3000,'month_credits':proposed['schedule']['month_credits'],
        'source_head':snapshot.head,'snapshot_sha256':snapshot.sha256,'source_count':len(snapshot.sources),
        'calls':planned['calls'],'reserved_credits':planned['reserved_credits'],'input_bound':planned['input_bound'],'output_bound':planned['output_bound'],'inspection_max_chars':max(len(canonical_json(shard)) for shard in planned['shards'])}

def _assert_budget(config,plan):
    macos=plan.get('macos_refresh')
    if macos and _macos()!=macos['after']:raise ValueError('revalidation_macos_changed')
    approved=plan.get('budget_refresh')
    if approved:
        snapshot,_=_budget_snapshot(config,macos['after'] if macos else None,approved.get('max_calls'))
        if snapshot.sha256!=approved['snapshot_sha256'] or snapshot.head!=approved['source_head']:
            raise ValueError('revalidation_budget_sources_changed')

def prepare(*,request_id,client_factory=None,refresh_budget=False,proposed_macos=None,proposed_max_calls=None):
    path = _root(request_id)
    with exclusive_file_lock(path/'operation'):
        if (path/'plan.json').exists():
            prior=json.loads((path/'plan.json').read_text())
            previous_macos=(prior['plan'].get('macos_refresh') or {}).get('after')
            if bool(prior['plan'].get('budget_refresh'))!=bool(refresh_budget) or previous_macos!=proposed_macos or (prior['plan'].get('call_limit_refresh') or {}).get('after')!=proposed_max_calls:raise ValueError('revalidation_request_scope_changed')
            return prior
        config,agent_sha = owned_configuration()
        if proposed_max_calls is not None and (not refresh_budget or type(proposed_max_calls) is not int or proposed_max_calls<=0):raise ValueError('revalidation_call_limit_proposal_invalid')
        call_refresh={'before':config.payload['limits']['max_calls'],'after':proposed_max_calls} if proposed_max_calls is not None else None
        observed_macos=_macos();baseline=config.payload.get('publication_policy',{}).get('macos_baseline')
        if proposed_macos is not None and proposed_macos!=observed_macos:raise ValueError('revalidation_macos_proposal_not_observed')
        if refresh_budget and baseline and baseline!=observed_macos and proposed_macos is None:raise ValueError('revalidation_macos_review_required')
        macos_refresh={'before':baseline,'after':proposed_macos} if proposed_macos is not None else None
        with (client_factory or _client)() as client:observed = _observe(client,config)
        counter = IsolatedCounter(config)
        try:
            tags={k:digest(request_id+k)[:24] for k in SCHEMA['required']}
            def payload(n):return {'headTag':tags['headTag'],'firstSyntheticSection':'0123456789abcdef '*n,'middleTag':tags['middleTag'],'secondSyntheticSection':'0123456789abcdef '*n,'tailTag':tags['tailTag']}
            ceiling = min(config.payload['limits']['input_tokens'],config.payload['runtime_evidence']['input_tokens'])
            if ceiling<200000:raise ValueError('revalidation_context_plan_required')
            overhead=counter(INSTRUCTIONS*2+canonical_json(SCHEMA))+8000
            low,high=1,50000
            while low<high:
                middle=(low+high+1)//2
                if len(canonical_json(payload(middle)))<=MAX_USER_INPUT_TEXT_CHARS and counter(canonical_json(payload(middle)))+overhead<=ceiling-2000:low=middle
                else:high=middle-1
            data=payload(low);bound=counter(canonical_json(data))+overhead
            budget=_budget_plan(config,counter,proposed_macos,proposed_max_calls) if refresh_budget else None
        finally:counter.close()
        plan={'request_id':request_id,'prepared_at':_now(),'activation_sha256':config.sha256,'agent_sha256':agent_sha,
            'runtime':observed,'implementation':_implementation(),'payload_sha256':digest(canonical_json(data)),
            'expected_answer':tags,'input_reservation_tokens':bound,'output_reservation_tokens':1024,
            'input_text_chars':len(canonical_json(data)),'max_input_text_chars':MAX_USER_INPUT_TEXT_CHARS,'context_admission_tokens':ceiling,'call_limit_refresh':call_refresh,'macos_observation':observed_macos,'macos_refresh':macos_refresh,'budget_refresh':budget,'acceptance_standard_credits':15,'billing_hard_cap':False,
            'model':MODEL,'effort':'medium','model_turns':1,'serviceTierForTurn':'default',
            'changes_after_accept':('runtime_evidence plus only explicitly bound optional budget_refresh, call_limit_refresh and macos_refresh; same role, monthly credit limit, schedule time, LaunchAgent and destinations')}
        envelope={'plan':plan,'digest':digest(canonical_json(plan))}
        atomic_create_text(path/'payload.json',canonical_json(data));atomic_create_text(path/'plan.json',canonical_json(envelope))
        return envelope

def run(*,request_id,approved_digest,confirmed=False,client_factory=None):
    path=_root(request_id)
    with exclusive_file_lock(path/'operation'):
        envelope=json.loads((path/'plan.json').read_text());plan=envelope['plan']
        if confirmed is not True or approved_digest!=envelope['digest'] or digest(canonical_json(plan))!=approved_digest:raise ValueError('revalidation_exact_approval_required')
        receipt=path/'receipt.json'
        if receipt.exists():return json.loads(receipt.read_text())
        config,agent_sha=owned_configuration()
        if config.sha256!=plan['activation_sha256'] or agent_sha!=plan['agent_sha256'] or _implementation()!=plan['implementation']:raise ValueError('revalidation_inputs_changed')
        payload=json.loads((path/'payload.json').read_text())
        if len(canonical_json(payload))>MAX_USER_INPUT_TEXT_CHARS:raise ValueError('revalidation_input_character_limit')
        if digest(canonical_json(payload))!=plan['payload_sha256']:raise ValueError('revalidation_payload_changed')
        _assert_budget(config,plan)
        record={'state':'reserved','request_id':request_id,'plan_digest':approved_digest,'model_turn_attempts':0,'automatic_retry':False,'started_at':_now()}
        atomic_create_text(receipt,canonical_json(record));guard=None
        try:
            with (client_factory or _client)() as client:
                if _observe(client,config)!=plan['runtime']:raise ValueError('revalidation_runtime_changed')
                def before_send(thread_id):
                    config.guard()
                    if _socket(client)!=plan['runtime']['socket']:raise ValueError('revalidation_socket_changed')
                    record.update(state='delivery_unknown',thread_id=thread_id,model_turn_attempts=1);atomic_write_json(receipt,record)
                context=path/'context';context.mkdir(mode=0o700,exist_ok=True)
                request=SimpleNamespace(payload=payload,schema=SCHEMA)
                guard=StandardTurn(client.transport,context=context,request=request,instructions=INSTRUCTIONS,before_send=before_send);client.transport=guard
                from app.routine_tasks import start_data_only_thread
                thread=start_data_only_thread(client,context,MODEL,INSTRUCTIONS)
                result=client.send_text(thread_id=thread['thread_id'],text=canonical_json(payload),model=MODEL,effort='medium',client_message_id=request_id,sandbox_policy={'type':'readOnly','networkAccess':False},approval_policy='never',output_schema=SCHEMA)
                record.update(state='completed_unreviewed',result=result.as_dict());atomic_write_json(receipt,record)
                usage=normalize_usage(result.thread_token_usage);cost=estimate_standard_credits(MODEL,usage)
                passed=(result.delivered and usage is not None and cost is not None and cost<=15 and not guard.unexpected_items
                    and usage['input_tokens']<=plan['input_reservation_tokens'] and usage['input_tokens']>=100000
                    and usage['output_tokens']<=1024 and json.loads(result.answer)==plan['expected_answer'])
                record.update(state='verified' if passed else 'attention',accepted=passed,usage=usage,estimated_standard_credits=cost)
        except Exception as error:
            record.update(state='attention',accepted=False,error_type=type(error).__name__,delivery_unknown=record['state']=='delivery_unknown')
            from app.codex_appserver import AppServerRpcError
            if isinstance(error,AppServerRpcError):
                record['rpc_error']={'method':error.method,'code':error.code,'server_message':str(error.server_message or '')[:4096],'data_sha256':digest(canonical_json(error.data))}
                record['rpc_rejection_observed']=True
        record['finished_at']=_now();atomic_write_json(receipt,record);return record

def accept(*,request_id,approved_digest,confirmed=False,client_factory=None):
    path=_root(request_id)
    with exclusive_file_lock(path/'operation'):
        envelope=json.loads((path/'plan.json').read_text());plan=envelope['plan'];record=json.loads((path/'receipt.json').read_text())
        if confirmed is not True or envelope['digest']!=approved_digest or digest(canonical_json(plan))!=approved_digest or record.get('plan_digest')!=approved_digest or record.get('accepted') is not True:raise ValueError('revalidation_verified_plan_required')
        config,agent_sha=owned_configuration()
        if record.get('activation_after_sha256'):
            if config.sha256!=record['activation_after_sha256']:raise ValueError('revalidation_activation_changed')
            record['state']='accepted';atomic_write_json(path/'receipt.json',record);return record
        if config.sha256!=plan['activation_sha256'] or agent_sha!=plan['agent_sha256'] or _implementation()!=plan['implementation']:raise ValueError('revalidation_inputs_changed')
        with (client_factory or _client)() as client:
            if _observe(client,config)!=plan['runtime']:raise ValueError('revalidation_runtime_changed')
        _assert_budget(config,plan)
        payload=config.payload
        if plan.get('macos_refresh'):payload['publication_policy']['macos_baseline']=plan['macos_refresh']['after']
        if plan.get('budget_refresh'):
            budget=plan['budget_refresh'];payload['schedule']['run_credits']=budget['run_credits']
            if plan.get('call_limit_refresh'):
                if budget.get('max_calls')!=plan['call_limit_refresh']['after']:raise ValueError('revalidation_call_limit_binding_changed')
                payload['schedule']['max_calls']=budget['max_calls'];payload['limits']['max_calls']=budget['max_calls']
            payload['limits'].update(run_credits=budget['run_credits'],inspection_output_tokens=budget['inspection_output_tokens'])
        payload['runtime_evidence']={'server_version':plan['runtime']['server_version'],'protocol_sha256':plan['runtime']['protocol_sha256'],
            'input_tokens':plan['context_admission_tokens'],'reference':'Verified owned shared peer, Sol/medium Standard synthetic context probe '+request_id+'; padded reference admission, not exact prompt token mapping. Receipt '+digest(canonical_json(record))}
        configuration.validate_payload(payload)
        record.update(state='activation_write_pending',activation_after_sha256=digest(canonical_json(payload)));atomic_write_json(path/'activation-before.json',config.payload);atomic_write_json(path/'receipt.json',record)
        config.guard();atomic_write_json(config.path,payload)
        record['state']='accepted';atomic_write_json(path/'receipt.json',record);return record
