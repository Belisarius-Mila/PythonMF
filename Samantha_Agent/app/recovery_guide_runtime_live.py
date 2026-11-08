"""Inactive-by-default binding to the existing shared socket and private config.

No service start, role edit, installation, paid call or operating write on
import/status. A separately provisioned activation is required for run/tick.
"""
from contextlib import contextmanager
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import select
import subprocess
import sys
from types import SimpleNamespace

from app import recovery_guide_maintainer as m
from app import recovery_guide_consolidation as c
from app import recovery_guide_runtime_config as configuration
from app.recovery_guide_sources import collect,canonical_json,digest
from app.recovery_guide_scheduler import SchedulerPolicy,WeeklyScheduler,inspect_status
from app.recovery_guide_publication import PublicationStore
from app.recovery_guide_publish import icloud_metadata
from app.recovery_guide_runtime import RecoveryRuntime
from app.file_persistence import atomic_write_json
from app.release_usage import normalize_usage


class IsolatedCounter:
    """One temporary tokenizer child per CLI run, no package/environment edits."""
    def __init__(self,config):self.config=config;self.child=None
    @lru_cache(maxsize=8)
    def __call__(self,text):
        settings=self.config.payload['tokenizer']
        if self.child is None:
            script='''import sys,json,tiktoken
from importlib.metadata import version
e=tiktoken.get_encoding('o200k_base')
print(json.dumps({'package_version':version('tiktoken'),'encoding':e.name}),flush=True)
for line in sys.stdin:
 print(len(e.encode_ordinary(json.loads(line))),flush=True)
'''
            root=self.config.project
            self.child=subprocess.Popen([str(root/'.venv/recovery_tokenizer/bin/python'),'-u','-c',script],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,
                env={**os.environ,'TIKTOKEN_CACHE_DIR':str(root/'.venv/recovery_tokenizer/cache')})
            identity=json.loads(self._line())
            if any(identity[k]!=settings[k] for k in ('encoding','package_version')):
                self.close();raise ValueError('runtime_tokenizer_identity_changed')
        self.child.stdin.write(json.dumps(text,ensure_ascii=False)+'\n');self.child.stdin.flush()
        result=math.ceil(int(self._line())*settings['margin'])
        if result<0:raise ValueError('runtime_counter_invalid')
        return result
    def _line(self):
        if not select.select([self.child.stdout],[],[],30)[0]:raise ValueError('runtime_tokenizer_timeout')
        line=self.child.stdout.readline()
        if not line:raise ValueError('runtime_tokenizer_unavailable')
        return line
    def close(self):
        self.__call__.cache_clear()
        if self.child is not None:
            self.child.stdin.close()
            try:self.child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.child.terminate()
                try:self.child.wait(timeout=3)
                except subprocess.TimeoutExpired:self.child.kill();self.child.wait(timeout=3)
            self.child.stdout.close();self.child=None


@contextmanager
def live_calls(directory,executor,*,assert_current,client_factory=None):
    from app.communication import agent_roles
    from app.communication.luna_release import new_luna_client
    from app.recovery_guide_anchor_full_pilot import ObservedTurn
    from app.routine_tasks import start_data_only_thread
    agent_roles.assert_current(executor,role=m.ROLE)
    with (client_factory or new_luna_client)() as client:
        selected=agent_roles.resolve_role(client.list_models(include_hidden=True),role=m.ROLE)
        if (any(selected[k]!=executor[k] for k in ('role','model','reasoning_effort','policy_digest'))
                or selected.get('fallback') or selected['model']!=m.MODEL or selected['reasoning_effort']!='medium'):
            raise ValueError('runtime_executor_changed')
        counter=0;threads=set()
        def call(payload,kind):
            nonlocal counter
            if kind not in {'inspect','synthesize'}:raise ValueError('runtime_unknown_phase')
            agent_roles.assert_current(executor,role=m.ROLE)
            if assert_current() is not True:raise ValueError('runtime_inputs_changed_before_thread')
            counter+=1
            schema=m.INSPECT_SCHEMA if kind=='inspect' else c.schema(payload)
            request=SimpleNamespace(payload=payload,schema=schema)
            context=directory/'context'/str(counter);path=directory/'transport'/f'{counter:03d}.json'
            def before_send(thread):
                agent_roles.assert_current(executor,role=m.ROLE)
                if assert_current() is not True:raise ValueError('runtime_inputs_changed_before_send')
                if thread in threads:raise ValueError('runtime_thread_reused')
                threads.add(thread)
                atomic_write_json(path,{'state':'delivery_unknown','phase':kind,'thread_id':thread,
                    'request_sha256':digest(canonical_json(payload))})
            original=client.transport
            guard=ObservedTurn(original,context=context,request=request,instructions=m.REVIEW_INSTRUCTIONS,before_send=before_send)
            client.transport=guard
            try:
                thread=start_data_only_thread(client,context,m.MODEL,m.REVIEW_INSTRUCTIONS)
                result=client.send_text(thread_id=thread['thread_id'],text=canonical_json(payload),model=m.MODEL,
                    effort='medium',approval_policy='never',sandbox_policy={'type':'readOnly','networkAccess':False},
                    output_schema=schema,client_message_id=directory.name+'-'+str(counter))
                atomic_write_json(path,{'state':'received_unreviewed','phase':kind,'receipt':result.as_dict(),
                    'unexpected_item_types':sorted(guard.unexpected_items)})
                if not result.delivered or guard.unexpected_items:raise ValueError('runtime_delivery_not_verified')
                agent_roles.assert_current(executor,role=m.ROLE)
                return {'answer':json.loads(result.answer),'usage':normalize_usage(result.thread_token_usage)}
            except Exception:
                # Preserve any full receipt already saved above. Before-send
                # unknown markers must never be replaced with fabricated failure.
                saved=json.loads(path.read_text()) if path.exists() else {'state':'not_verified_before_send','phase':kind}
                if saved['state']=='delivery_unknown':
                    saved.update(turn_id=guard.turn_id,terminal_status=guard.terminal_status,
                        observed_usage=guard.observed_usage)
                atomic_write_json(path,saved)
                raise
            finally:client.transport=original
        yield call


def build(config):
    config.guard();p=config.payload
    policy=SchedulerPolicy(**p['schedule']);limits=m.Limits(**p['limits'])
    scheduler=WeeklyScheduler(config.root/'schedule',sandbox_root=config.root,policy=policy,
        mode='production',activation=config)
    publication=PublicationStore(config.root/'publication',sandbox_root=config.root,
        destinations=config.destinations,mode='production',activation=config)
    counter=IsolatedCounter(config)
    def snapshot(original):return collect(original,config.project,companion_scopes=tuple(p['scopes']))
    def assert_snapshot(frozen,original):return snapshot(original).sha256==frozen.sha256
    def common_readiness():
        config.guard()
        cloud=icloud_metadata(config.destinations[1].parent)
        cloud_ok=cloud.get('available') is True and cloud.get('ubiquitous') is True
        return {'mac_available':True,'user_session':os.stat('/dev/console').st_uid==os.getuid(),
            'network':cloud_ok,'icloud_auth':cloud_ok}
    def readiness():
        from app.communication import agent_roles
        from app.communication.luna_release import new_luna_client
        from app import recovery_guide_trial as calibration
        ready=common_readiness()
        # Dependency observations cannot guarantee future provider delivery.
        # Delivery uses common_readiness directly and never needs this socket.
        try:
            with new_luna_client() as client:
                selected=agent_roles.resolve_role(client.list_models(include_hidden=True),role=m.ROLE)
                effective=client.read_effective_config(cwd=config.project)
                evidence=p['runtime_evidence']
                context_ok=(client.server_version.raw==evidence['server_version']
                    and digest(canonical_json(calibration._protocol()))==evidence['protocol_sha256'])
            role_ok=(selected['policy_digest']==policy.role_policy_digest and selected['model']==m.MODEL
                and selected['reasoning_effort']=='medium' and not selected.get('fallback'))
            ready.update(codex_auth=True,role_current=role_ok,
                standard_tier=effective.get('service_tier') in {None,'default'},context_proven=context_ok,
                source_scope_approved=bool(p['scopes']))
        except Exception:pass
        return ready
    runtime=RecoveryRuntime(scheduler=scheduler,publication=publication,limits=limits,
        bootstrap=Path(p['bootstrap']['path']),bootstrap_sha256=p['bootstrap']['sha256'],snapshot_provider=snapshot,
        count_tokens=counter,call_factory=live_calls,readiness=readiness,assert_snapshot=assert_snapshot,
        cloud_audit=icloud_metadata,delivery_readiness=common_readiness,assert_activation=config.guard)
    return runtime,counter


def entry(action,*,project=configuration.ROOT,home=None,now=None):
    config=configuration.load(project,home)
    if config is None or config.payload['enabled'] is not True:
        return {'state':'activation_required','model_calls':0,'writes':False,
            'runtime_integrated':True,'format_contract':c.VERSION,
            'reason':'Nutná samostatně schválená aktivační konfigurace, role, rozsah a rozpočet.'}
    config.guard()
    if action=='status':return inspect_status(config.root/'schedule',scope='production')
    if action not in {'run','tick'}:raise ValueError('runtime_unknown_action')
    from datetime import datetime
    from zoneinfo import ZoneInfo
    runtime,counter=build(config)
    try:return runtime.tick(now or datetime.now(ZoneInfo('Europe/Prague')),trigger='manual' if action=='run' else 'timer')
    finally:counter.close()
