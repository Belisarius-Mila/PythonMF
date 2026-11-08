"""Prepare a concrete inactive proposal; activate only with the safety phrase.

One initial, explicitly accepted guide is published without a model. The first
paid weekly slot is in the future. No hidden install on prepare/import.
"""
from dataclasses import asdict
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
from zoneinfo import ZoneInfo

from app import recovery_guide_runtime_config as cfg
from app import recovery_guide_runtime_live as live
from app import recovery_guide_consolidation as c
from app import recovery_guide_maintainer as m
from app.communication import agent_roles
from app.file_persistence import atomic_create_text,atomic_write_json
from app.recovery_guide_sources import Source,Snapshot,canonical_json,digest,target_preview
from app.recovery_guide_publish import Target,icloud_metadata,file_hash
from scripts.recovery_guide_launchd import launch_agent

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'.venv/recovery_guide_activation'
CONFIRMATION='Potvrzuji globální brzdu: rozumím riziku a chci pokračovat.'
CODE=('app/recovery_guide_activation.py','app/recovery_guide_runtime.py','app/recovery_guide_runtime_config.py',
      'app/recovery_guide_runtime_live.py','app/recovery_guide_consolidation.py','app/recovery_guide_maintainer.py',
      'app/recovery_guide_quality.py','app/recovery_guide_publication.py','app/recovery_guide_publish.py',
      'app/recovery_guide_scheduler.py','app/recovery_guide_revision.py','app/communication/agent_roles.py',
      'app/routine_tasks.py','app/codex_appserver.py','app/release_usage.py',
      'app/recovery_guide_anchor_transport.py','app/recovery_guide_anchor_full_pilot.py',
      'app/recovery_guide_trial.py','scripts/recovery_guide.py','scripts/recovery_guide_launchd.py')


def _implementation():return {name:digest((ROOT/name).read_bytes()) for name in CODE}


def _private():
    cfg.private(STATE);STATE.mkdir(mode=0o700,parents=True,exist_ok=True)


def prepare(*,cost_path:Path,seed:Path,run_credits:float,month_credits:float,first_due:datetime,
            applications:list[str],runtime_evidence:dict,macos_baseline:str,home=None,now=None):
    """Nonpaid, private proposal. Budgets are proposals, never assumed approval."""
    _private();home=home or Path.home();now=now or datetime.now(timezone.utc)
    if first_due.tzinfo is None or first_due<=now:raise ValueError('activation_first_slot_must_be_future')
    cost=json.loads(cost_path.read_text())
    if cost['planned_calls']>20:raise ValueError('activation_call_plan_exceeds_limit')
    if cost['reserved_credits']>run_credits:raise ValueError('activation_budget_below_plan')
    if seed.is_symlink() or digest(seed.read_bytes())!=cost['seed_sha256']:raise ValueError('activation_seed_changed')
    roles=ROOT/'config/agent_roles.json';old=roles.read_bytes();after=json.loads(old)
    if m.ROLE in after['roles']:raise ValueError('activation_role_already_configured')
    trial=json.loads((ROOT/'.venv/recovery_rec06_trial/receipt.json').read_text())
    if trial.get('state')!='trial_passed' or trial.get('accepted') is not True:raise ValueError('activation_role_trial_not_passed')
    after['roles'][m.ROLE]={'label':'Týdenní správce obnovovací dokumentace','preferred_model':m.MODEL,
        'approved_models':[{'model':m.MODEL,'reasoning_effort':'medium',
            'cost_review':'Standard 50/2.5/250 per million; activation proposal 2026-11-08; no cache assumed.',
            'dry_run_evidence':'REC-06 synthetic trial_passed 2026-11-07, same Sol/medium Standard peer, receipt '+digest(canonical_json(trial))}]}
    role_text=json.dumps(after,ensure_ascii=False,indent=2)+'\n'
    role_path=STATE/'role-candidate.json'
    if role_path.exists() and role_path.read_text()!=role_text:raise ValueError('activation_role_proposal_changed')
    if not role_path.exists():atomic_create_text(role_path,role_text)
    binding=agent_roles.load_role(role_path,role=m.ROLE)
    paths=target_preview(home,home/'Desktop/PythonMF');targets=tuple(Target.pin(Path(paths[k])) for k in ('local','icloud'))
    day=now.astimezone(ZoneInfo('Europe/Prague')).date()
    original=Source('original_guide',digest(seed.read_bytes()),seed.read_text(),'previous_version')
    snapshot=Snapshot(cost['source_head'],original,())
    request=c.prepare(snapshot,[],day)
    answer={'request_id':request.payload['request_id'],'sections':{s['id']:[{'action':'keep','block':b['id']} for b in s['blocks']] for s in request.payload['guide_layout']['sections']}}
    candidate=c.validate(answer,snapshot,request)['candidate']
    limits={**cost['provisional_limits_not_approved'],'run_credits':run_credits,'month_credits':month_credits,'max_calls':20}
    config={'schema':1,'enabled':True,'approved_at':now.isoformat(),'source_ref':'refs/heads/main',
        'publication_policy':{'mode':'validated_auto_v1','applications':applications,'macos_baseline':macos_baseline},
        'schedule':{'enabled':True,'schedule_approved':True,'budget_approved':True,'weekday':6,'hour':9,
            'not_before':first_due.isoformat(),'role_policy_digest':binding['policy_digest'],
            'run_credits':run_credits,'month_credits':month_credits,'max_calls':20,'max_seconds':limits['seconds']},
        'limits':limits,'scopes':['docs/','MatysekANJ/docs/','iOS/'],
        'bootstrap':{'path':targets[0].path,'sha256':digest(candidate)},'tokenizer':cost['tokenizer'],
        'runtime_evidence':runtime_evidence}
    cfg.validate_payload(config)
    spec=launch_agent(ROOT);plist=plistlib.dumps(spec).decode('utf-8')
    proposal={'state':'awaiting_safety_and_budget_confirmation','implementation':_implementation(),
        'config':config,'role_before_sha256':digest(old),'role_after':role_text,
        'targets':[asdict(t) for t in targets],'seed_path':str(seed),'seed_sha256':original.sha256,
        'snapshot':asdict(snapshot),'request':request.envelope,'answer':answer,
        'candidate_sha256':digest(candidate),'candidate_bytes':len(candidate.encode()),
        'plist':plist,'home':str(home),'cost':cost,'bootstrap_request':'recovery-bootstrap-'+day.strftime('%Y%m%d')}
    sha=digest(canonical_json(proposal));path=STATE/(sha+'.json')
    if not path.exists():atomic_create_text(path,canonical_json(proposal))
    return {'proposal_sha256':sha,'state':proposal['state'],'first_due':first_due.isoformat(),
        'run_credits':run_credits,'month_credits':month_credits,'planned_credits':cost['reserved_credits'],
        'planned_calls':cost['planned_calls'],'source_count':cost['source_count'],
        'targets':[t.path for t in targets],'candidate_sha256':digest(candidate),'candidate_bytes':len(candidate.encode()),
        'paid_model_calls':0,'service_installed':False}


def activate(*,proposal_sha256,confirmation,runner=None,cloud_audit=None,now=None):
    """Trusted final action. Idempotent copies; never retry launch uncertainty."""
    if confirmation!=CONFIRMATION:raise ValueError('activation_exact_safety_confirmation_required')
    if not isinstance(proposal_sha256,str) or not re.fullmatch('[a-f0-9]{64}',proposal_sha256):raise ValueError('activation_exact_proposal_required')
    _private();path=STATE/(proposal_sha256+'.json')
    if path.is_symlink():raise ValueError('activation_proposal_alias')
    p=json.loads(path.read_text())
    if digest(canonical_json(p))!=proposal_sha256 or _implementation()!=p['implementation']:raise ValueError('activation_proposal_changed')
    now=now or datetime.now(timezone.utc)
    if datetime.fromisoformat(p['config']['schedule']['not_before'])<=now:raise ValueError('activation_first_slot_requires_refresh')
    seed=Path(p['seed_path']);roles=ROOT/'config/agent_roles.json';home=Path(p['home'])
    if seed.is_symlink() or digest(seed.read_bytes())!=p['seed_sha256']:raise ValueError('activation_seed_changed')
    if roles.is_symlink():raise ValueError('activation_role_alias')
    if digest(roles.read_bytes())!=p['role_before_sha256'] and json.loads(roles.read_text())!=json.loads(p['role_after']):raise ValueError('activation_other_roles_changed')
    for raw in p['targets']:
        raw={**raw,'aliases':tuple(tuple(a) for a in raw['aliases'])};target=Target(**raw)
        if file_hash(target.check()) not in {target.baseline,p['candidate_sha256']}:raise ValueError('activation_target_changed')
    run=runner or subprocess.run;domain='gui/'+str(os.getuid());label=domain+'/com.samantha.recovery-guide'
    def loaded():
        result=run(['/bin/launchctl','print',label],capture_output=True,text=True,check=False)
        return result.returncode==0,result.stdout
    receipt_path=STATE/(proposal_sha256+'-activation.json')
    receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else {'state':'prepared','launch_attempted':False}
    present,listing=loaded()
    agent=home/'Library/LaunchAgents/com.samantha.recovery-guide.plist'
    def matches(text):
        rows={line.strip().strip(chr(34)) for line in text.splitlines()}
        return all(arg in rows for arg in plistlib.loads(p['plist'].encode())['ProgramArguments'])
    if present and (not agent.is_file() or agent.read_text()!=p['plist'] or not matches(listing)):
        raise ValueError('activation_other_launchagent')
    if agent.is_symlink() or (agent.exists() and agent.read_text()!=p['plist']):raise ValueError('activation_launchagent_file_changed')
    config_path=ROOT/'data/private/recovery_guide_runtime/activation.json';config_text=canonical_json(p['config'])
    if config_path.exists() and (config_path.is_symlink() or config_path.read_text()!=config_text):raise ValueError('activation_existing_configuration_changed')
    atomic_write_json(receipt_path,receipt)
    # Only this dedicated role changes; all other bindings remain identical.
    if json.loads(roles.read_text())!=json.loads(p['role_after']):atomic_write_json(roles,json.loads(p['role_after']))
    if digest(roles.read_bytes())!=digest(p['role_after']):
        # atomic_write_json uses its own canonical style; bind semantic equality.
        if json.loads(roles.read_text())!=json.loads(p['role_after']):raise ValueError('activation_role_write_not_verified')
    cfg.private(config_path.parent)
    config_path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    if not config_path.exists():atomic_create_text(config_path,config_text)
    config=cfg.load(ROOT,home);runtime,counter=live.build(config)
    try:
        request_id=p['bootstrap_request'];known=runtime.publication.status(request_id)
        if known['state']=='not_accepted':
            from app.recovery_guide_costing import hydrate
            snap=hydrate(p['snapshot']);request=c.Request(p['request'])
            dossier,context=runtime.automatic_profile(snap,now.astimezone(ZoneInfo('Europe/Prague')).date())
            draft=runtime.publication.prepare(p['answer'],snap,dossier,context,format_request=request)
            if digest(runtime.publication.candidate_text(draft))!=p['candidate_sha256']:raise ValueError('activation_candidate_changed')
            known=runtime.publication.accept(draft,request_id=request_id,confirmed_binding=draft.sha256,confirmed=True,now=now)
        delivery=runtime.publication.execute(request_id,approval_sha256=known['approval_sha256'],
            current_inputs=lambda _:digest(seed.read_bytes())==p['seed_sha256'],cloud_audit=cloud_audit or icloud_metadata,now=now)
        receipt.update(state='baseline_'+delivery['state'],candidate_sha256=p['candidate_sha256'],copies=delivery.get('copies'))
        atomic_write_json(receipt_path,receipt)
        if delivery['state']!='uploaded':return receipt
    finally:counter.close()
    if not agent.exists():atomic_create_text(agent,p['plist'])
    if not present:
        if receipt.get('launch_attempted'):return {**receipt,'state':'launch_outcome_unknown_operator_required'}
        receipt.update(state='launch_outcome_unknown',launch_attempted=True);atomic_write_json(receipt_path,receipt)
        result=run(['/bin/launchctl','bootstrap',domain,str(agent)],capture_output=True,text=True,check=False)
        present,listing=loaded()
        if not present or not matches(listing):
            return {**receipt,'state':'launch_outcome_unknown_operator_required'}
    receipt.update(state='active',first_due=p['config']['schedule']['not_before'],paid_model_calls=0)
    atomic_write_json(receipt_path,receipt);return receipt
