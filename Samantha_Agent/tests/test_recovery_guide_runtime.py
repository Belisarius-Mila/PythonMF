from contextlib import contextmanager
from dataclasses import asdict,replace
from datetime import datetime,timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from app import recovery_guide_maintainer as m
from app import recovery_guide_consolidation as c
from app import recovery_guide_runtime_config as config
from app import recovery_guide_runtime_live as live
from app.recovery_guide_runtime import RecoveryRuntime
from app.recovery_guide_scheduler import WeeklyScheduler,SchedulerPolicy,ANALYSIS_READY,inspect_status
from app.recovery_guide_publication import PublicationStore,PublicationDraft
from app.recovery_guide_sources import canonical_json,digest
from app.file_persistence import atomic_replace_text_under_external_lock
from tests import test_recovery_guide_quality as fixtures
from tests.test_recovery_guide import consolidated_answer,USAGE,CLOUD


class Runtime(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name).resolve()
        for folder in ('local','cloud'):(self.root/folder).mkdir()
        self.bootstrap=self.root/'bootstrap.txt';self.bootstrap.write_text(fixtures.ORIGINAL)
        self.targets=(self.root/'local/guide.txt',self.root/'cloud/guide.txt')
        self.policy=SchedulerPolicy(True,True,True,not_before='2026-11-01T00:00:00+00:00',
            role_policy_digest='a'*64,run_credits=50,month_credits=1000,max_calls=8,max_seconds=60)
        self.scheduler=WeeklyScheduler(self.root/'schedule',sandbox_root=self.root,policy=self.policy)
        self.store=PublicationStore(self.root/'publication',sandbox_root=self.root,destinations=self.targets)
        self.now=datetime(2026,11,8,10,tzinfo=ZoneInfo('Europe/Prague'))
        self.calls=[];self.opens=[];self.paths=[];self.cloud=True;self.failure=None
        self.runtime=self.make()

    def snapshot(self,path):
        self.paths.append(path);text=path.read_text();base=fixtures.snap()
        return replace(base,original=replace(base.original,text=text,sha256=digest(text)))

    @contextmanager
    def factory(self,directory,executor,**kwargs):
        self.opens.append((directory,executor))
        yield self.call

    def call(self,payload,kind):
        self.calls.append((payload,kind))
        if self.failure:raise self.failure
        answer=({'covered':[{'source':s['path'],'quote':s['text']} for s in payload['sources']],
                 'notes':'Dokumentovaný stav, nikoli živý audit.'} if kind=='inspect' else consolidated_answer(payload))
        return {'answer':answer,'usage':USAGE}

    def make(self):
        return RecoveryRuntime(scheduler=self.scheduler,publication=self.store,
            limits=m.Limits(40000,2000,8,50,1000,60),bootstrap=self.bootstrap,
            bootstrap_sha256=digest(fixtures.ORIGINAL),snapshot_provider=self.snapshot,count_tokens=len,
            call_factory=self.factory,readiness=lambda:{k:True for k in ANALYSIS_READY},
            assert_snapshot=lambda s,p:self.snapshot(p).sha256==s.sha256,
            cloud_audit=lambda p:CLOUD if self.cloud else {**CLOUD,'uploaded':False})

    def tick(self):return self.runtime.tick(self.now)

    def accept(self,job=None):
        job=job or self.tick();saved=self.runtime._load(job['request_id']);snapshot=saved[2]
        context=replace(fixtures.context(snapshot),checked_on=self.now.date())
        draft=self.runtime.prepare_acceptance(job['request_id'],dossier=fixtures.dossier(context),context=context)
        result=self.runtime.accept(job['request_id'],draft,confirmed_binding=draft.sha256,
            confirmed_identity=job['identity_sha256'],confirmed=True,now=self.now)
        self.assertEqual(result['state'],'delivery_ready');return job,draft

    def test_complete_chain_requires_acceptance_then_delivers_same_bytes(self):
        job=self.tick();self.assertEqual(job['state'],'awaiting_acceptance');self.assertEqual(len(self.calls),2)
        self.assertFalse(any(p.exists() for p in self.targets))
        self.accept(job);result=self.tick();self.assertEqual(result['state'],'completed')
        self.assertEqual(self.targets[0].read_bytes(),self.targets[1].read_bytes())
        self.assertIn(c.STAMP+'08112026',self.targets[0].read_text());self.assertEqual(len(self.calls),2)
        self.assertEqual(self.tick()['action'],'replayed_receipt');self.assertEqual(len(self.calls),2)

    def test_second_week_reads_last_accepted_guide_not_bootstrap(self):
        self.accept();self.tick();first=self.targets[0].read_text();self.now+=timedelta(days=7)
        self.accept();result=self.tick();second=self.targets[0].read_text()
        self.assertEqual(result['state'],'completed');self.assertEqual(len(self.calls),4)
        self.assertEqual(self.calls[2][0]['original']['text'],first)
        self.assertIn(c.STAMP+'15112026',second);self.assertNotIn('08112026',second)
        self.assertEqual(second.count(c.STAMP),1);self.assertNotIn('DOPLNĚNÍ',second)

    def test_pending_cloud_blocks_new_model_and_reconciles_same_job(self):
        self.accept();self.cloud=False;self.assertEqual(self.tick()['state'],'pending_icloud')
        self.now+=timedelta(days=7);self.runtime=self.make();self.cloud=True
        self.assertEqual(self.tick()['slot'],'2026-W45');self.assertEqual(len(self.calls),2)
        self.assertEqual(self.tick()['slot'],'2026-W46');self.assertEqual(len(self.calls),4)

    def test_unknown_model_outcome_blocks_future_weeks_and_retains_raw_marker(self):
        self.failure=TimeoutError('PRIVATE_ERROR');job=self.tick();self.assertEqual(job['state'],'attention')
        self.now+=timedelta(days=14);self.failure=None;self.runtime=self.make();self.tick()
        self.assertEqual(len(self.calls),1)
        raw=json.loads((self.root/'analysis'/job['request_id']/'raw/001.json').read_text())
        self.assertEqual(raw['state'],'delivery_unknown');self.assertNotIn('PRIVATE_ERROR',canonical_json(job))
        self.assertTrue(job['credits_are_lower_bound'])

    def test_process_death_keeps_unknown_marker_without_another_model(self):
        self.failure=SystemExit()
        with self.assertRaises(SystemExit):self.tick()
        self.failure=None;self.runtime=self.make();self.assertEqual(self.tick()['state'],'attention')
        self.assertEqual(len(self.calls),1)

    def test_invalid_format_cannot_reach_acceptance_or_writer(self):
        original=self.call
        def bad(payload,kind):
            response=original(payload,kind)
            if kind=='synthesize':response['answer']['sections']['c01'].append({'action':'keep','block':1})
            return response
        self.call=bad;job=self.tick();self.assertEqual(job['state'],'attention')
        self.assertFalse(any(p.exists() for p in self.targets))
        self.assertTrue((self.root/'analysis'/job['request_id']/'raw/002.json').exists())

    def test_source_change_after_generation_blocks_acceptance(self):
        job=self.tick();self.bootstrap.write_text(fixtures.ORIGINAL+'\nChanged')
        with self.assertRaisesRegex(ValueError,'not_current'):self.accept(job)
        self.assertFalse(any(p.exists() for p in self.targets));self.assertEqual(len(self.calls),2)

    def test_human_edit_after_completed_delivery_does_not_fall_back_to_old_original(self):
        self.accept();self.tick();self.targets[0].write_text('Changed manually')
        self.now+=timedelta(days=7);self.assertEqual(self.tick()['state'],'attention');self.assertEqual(len(self.calls),2)

    def test_acceptance_cannot_mix_other_candidate_or_identity(self):
        job=self.tick();saved=self.runtime._load(job['request_id']);context=replace(fixtures.context(saved[2]),checked_on=self.now.date())
        draft=self.runtime.prepare_acceptance(job['request_id'],dossier=fixtures.dossier(context),context=context)
        with self.assertRaisesRegex(ValueError,'acceptance_changed'):
            self.runtime.accept(job['request_id'],draft,confirmed_binding=draft.sha256,confirmed_identity='b'*64,confirmed=True,now=self.now)
        raw=json.loads(draft.packet_json);raw['format_request']='{}'
        with self.assertRaisesRegex(ValueError,'acceptance_changed'):
            self.runtime.accept(job['request_id'],PublicationDraft(canonical_json(raw)),confirmed_binding=draft.sha256,
                confirmed_identity=job['identity_sha256'],confirmed=True,now=self.now)
        self.assertFalse(any(p.exists() for p in self.targets))

    def test_application_scope_and_dossier_checks_are_not_bypassed_by_new_format(self):
        job=self.tick();snapshot=self.runtime._load(job['request_id'])[2]
        context=replace(fixtures.context(snapshot),checked_on=self.now.date(),application_scope_approved=False)
        with self.assertRaisesRegex(ValueError,'quality_gate_blocked'):
            self.runtime.prepare_acceptance(job['request_id'],dossier=fixtures.dossier(context),context=context)

    def test_crash_between_copies_resumes_delivery_without_model(self):
        self.accept();original=atomic_replace_text_under_external_lock;calls=[]
        def interrupted(path,text):
            if path==self.targets[1]:raise SystemExit()
            calls.append(path);return original(path,text)
        with patch('app.recovery_guide_publish.atomic_replace_text_under_external_lock',side_effect=interrupted):
            with self.assertRaises(SystemExit):self.tick()
        self.assertTrue(self.targets[0].exists());self.assertFalse(self.targets[1].exists())
        self.runtime=self.make();self.assertEqual(self.tick()['state'],'completed')
        self.assertEqual(len(self.calls),2);self.assertEqual(self.targets[0].read_bytes(),self.targets[1].read_bytes())

    def test_non_default_schedule_keeps_one_shared_slot(self):
        self.policy=replace(self.policy,weekday=0,hour=8)
        self.scheduler=WeeklyScheduler(self.root/'schedule',sandbox_root=self.root,policy=self.policy)
        self.runtime=self.make();job=self.tick();self.assertEqual(job['slot'],'2026-W45')
        self.assertEqual(job['state'],'awaiting_acceptance')
        self.assertTrue((self.root/'analysis'/job['request_id']/'controller'/'2026-W45.json').exists())


class Configuration(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name).resolve()
        self.home=self.root/'home';self.home.mkdir();self.project=self.root/'project';self.project.mkdir()
        self.path=self.project/'data/private/recovery_guide_runtime/activation.json'
        self.value={'schema':1,'enabled':True,'approved_at':'2026-11-01T00:00:00+00:00',
            'schedule':asdict(SchedulerPolicy(True,True,True,not_before='2026-11-01T00:00:00+00:00',
                role_policy_digest='a'*64,run_credits=50,month_credits=1000,max_calls=8,max_seconds=60)),
            'limits':asdict(m.Limits(40000,2000,8,50,1000,60)),
            'source_ref':'refs/heads/main','publication_policy':{'mode':'manual'},
            'scopes':['docs/'],'bootstrap':{'path':str(self.root/'guide.txt'),'sha256':'b'*64},
            'tokenizer':{'package_version':'test','encoding':'o200k_base','margin':1.2,'reference_uncertainty_accepted':True},
            'runtime_evidence':{'server_version':'test','protocol_sha256':'c'*64,'input_tokens':40000,'reference':'accepted context test'}}

    def save(self):
        self.path.parent.mkdir(parents=True,mode=0o700,exist_ok=True);self.path.write_text(canonical_json(self.value));self.path.chmod(0o600)
        return config.load(self.project,self.home)

    def test_absent_configuration_run_tick_status_are_inert(self):
        for action in ('run','tick','status'):
            with patch.object(live,'build',side_effect=AssertionError('must not build')):
                result=live.entry(action,project=self.project,home=self.home)
            self.assertEqual(result['state'],'activation_required');self.assertEqual(result['model_calls'],0)
        self.assertFalse(self.path.parent.exists())

    def test_disabled_configuration_is_inert(self):
        self.value['enabled']=False;self.value['schedule']['enabled']=False;self.save()
        with patch.object(live,'build',side_effect=AssertionError('must not build')):
            self.assertEqual(live.entry('tick',project=self.project,home=self.home)['state'],'activation_required')

    def test_owned_frozen_configuration_only_permits_fixed_targets(self):
        cfg=self.save();cfg.permits(cfg.root/'schedule',cfg.destinations)
        with self.assertRaisesRegex(ValueError,'targets_outside'):cfg.permits(cfg.root/'pub',(self.root/'a',self.root/'b'))
        with self.assertRaisesRegex(ValueError,'state_outside'):cfg.permits(self.root/'outside')
        self.value['limits']['run_credits']=51;self.path.write_text(canonical_json(self.value))
        with self.assertRaisesRegex(ValueError,'activation_changed'):cfg.guard()

    def test_world_readable_activation_is_rejected(self):
        self.save();self.path.chmod(0o644)
        with self.assertRaisesRegex(ValueError,'not_private'):config.load(self.project,self.home)

    def test_unapproved_reference_counter_or_context_are_rejected(self):
        for key in ('tokenizer','runtime_evidence'):
            with self.subTest(key=key):
                old=self.value[key]
                self.value[key]={**old,**({'reference_uncertainty_accepted':False} if key=='tokenizer' else {'input_tokens':1})}
                with self.assertRaisesRegex(ValueError,'counter_not_approved|context_evidence'):self.save()
                self.value[key]=old

    def test_production_scope_needs_a_current_private_activation(self):
        cfg=self.save()
        for path in cfg.destinations:path.parent.mkdir(parents=True,exist_ok=True)
        policy=SchedulerPolicy(**self.value['schedule'])
        schedule=WeeklyScheduler(cfg.root/'schedule',sandbox_root=cfg.root,policy=policy,mode='production',activation=cfg)
        store=PublicationStore(cfg.root/'pub',sandbox_root=cfg.root,destinations=cfg.destinations,mode='production',activation=cfg)
        self.assertEqual(schedule.scope,'production');self.assertEqual(store.scope,'production')
        self.value['enabled']=False;self.path.write_text(canonical_json(self.value))
        with self.assertRaisesRegex(ValueError,'activation_changed'):schedule._guard()
        with self.assertRaisesRegex(ValueError,'activation_changed'):store._guard()

    def test_status_never_builds_or_starts_a_tokenizer_or_client(self):
        self.save()
        with patch.object(live,'build',side_effect=AssertionError('must not build')):
            result=live.entry('status',project=self.project,home=self.home)
        self.assertEqual(result['scope'],'production');self.assertEqual(result['state'],'not_configured')



    def test_live_delivery_readiness_does_not_open_app_server_or_tokenizer(self):
        import os
        from types import SimpleNamespace
        cfg=self.save()
        for path in cfg.destinations:path.parent.mkdir(parents=True,exist_ok=True)
        original_stat=os.stat
        def stat(path,*args,**kwargs):
            return SimpleNamespace(st_uid=os.getuid()) if str(path)=='/dev/console' else original_stat(path,*args,**kwargs)
        with patch.object(live,'icloud_metadata',return_value=CLOUD),patch.object(live.os,'stat',side_effect=stat),patch('app.communication.luna_release.new_luna_client') as client:
            runtime,counter=live.build(cfg)
            ready=runtime.delivery_readiness()
            self.assertTrue(all(ready[k] for k in ('mac_available','user_session','network','icloud_auth')))
            client.assert_not_called();self.assertIsNone(counter.child)


class ProductionIntegration(Runtime):
    def setUp(self):
        super().setUp()
        configuration=Configuration();configuration.setUp();self.addCleanup(configuration.doCleanups)
        configuration.value['bootstrap']={'path':str(self.bootstrap),'sha256':digest(fixtures.ORIGINAL)}
        self.configuration=configuration;self.cfg=configuration.save()
        self.policy=SchedulerPolicy(**self.cfg.payload['schedule'])
        self.root=self.cfg.root
        self.targets=self.cfg.destinations
        for path in self.targets:path.parent.mkdir(parents=True,exist_ok=True)
        self.scheduler=WeeklyScheduler(self.root/'schedule',sandbox_root=self.root,policy=self.policy,
            mode='production',activation=self.cfg)
        self.store=PublicationStore(self.root/'publication',sandbox_root=self.root,destinations=self.targets,
            mode='production',activation=self.cfg)
        self.runtime=self.make()

    def test_production_receipt_reports_actual_simulated_wire_count_without_marking_usage_simulated(self):
        job=self.tick();self.assertFalse(job['simulation']);self.assertFalse(job['credits_are_simulated'])
        self.assertEqual(job['model_calls'],2);self.accept(job);self.assertEqual(self.tick()['state'],'completed')
        self.assertFalse(inspect_status(self.root/'schedule',scope='production')['credits_are_simulated'])

    def test_new_activation_cannot_resume_an_old_pending_job(self):
        self.accept();self.cloud=False;self.assertEqual(self.tick()['state'],'pending_icloud')
        self.configuration.value['scopes']=['docs/','iOS/'];self.cfg=self.configuration.save()
        self.scheduler=WeeklyScheduler(self.root/'schedule',sandbox_root=self.root,policy=self.policy,
            mode='production',activation=self.cfg)
        self.store=PublicationStore(self.root/'publication',sandbox_root=self.root,destinations=self.targets,
            mode='production',activation=self.cfg)
        self.runtime=self.make();result=self.tick()
        self.assertEqual(result['action'],'policy_changed');self.assertEqual(len(self.calls),2)

    def test_non_default_schedule_keeps_one_shared_slot(self):
        self.configuration.value['schedule']['weekday']=0
        self.configuration.value['schedule']['hour']=8
        self.cfg=self.configuration.save();self.policy=SchedulerPolicy(**self.cfg.payload['schedule'])
        self.scheduler=WeeklyScheduler(self.root/'schedule',sandbox_root=self.root,policy=self.policy,
            mode='production',activation=self.cfg)
        self.store=PublicationStore(self.root/'publication',sandbox_root=self.root,destinations=self.targets,
            mode='production',activation=self.cfg)
        self.runtime=self.make();job=self.tick()
        self.assertEqual(job['state'],'awaiting_acceptance');self.assertEqual(job['slot'],'2026-W45')

    def test_production_does_not_accept_legacy_paragraph_fallback(self):
        snap=fixtures.snap();context=fixtures.context(snap)
        with self.assertRaisesRegex(ValueError,'integrated_format_required'):
            self.store.prepare(fixtures.answer(),snap,fixtures.dossier(context),context)



class TransportBinding(unittest.TestCase):
    def setUp(self):
        from app.codex_appserver import CodexAppServerClient,CodexVersion
        from tests.test_recovery_guide_trial import Wire as BaseWire
        from types import SimpleNamespace
        import copy
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name).resolve()
        outer=self
        class Wire(BaseWire):
            def __init__(self):super().__init__(outer.root/'synthetic.sock');self.threads=0;self.reuse=False
            def request(self,method,params):
                if method=='thread/start':
                    self.threads+=1;reply=super().request(method,params)
                    reply['thread']['id']='thread-'+str(1 if self.reuse else self.threads);return reply
                if method!='turn/start':return super().request(method,params)
                self.calls.append((method,copy.deepcopy(params)))
                marker=json.loads((outer.root/'transport'/f'{self.threads:03d}.json').read_text())
                outer.assertEqual(marker['state'],'delivery_unknown')
                thread=params['threadId'];turn='turn-'+str(self.threads)
                items=[{'type':'userMessage','clientId':params['clientUserMessageId']},
                    {'type':'agentMessage','id':'final','phase':'final_answer','text':'{"ok":true}'}]
                self.events=[{'method':'turn/started','params':{'turn':{'id':turn}}},
                    {'method':'thread/tokenUsage/updated','params':{'tokenUsage':{'total':self.usage}}},
                    {'method':'turn/completed','params':{'turn':{'id':turn,'status':'completed','items':items}}}]
                for e in self.events:e['params'].update(threadId=thread,turnId=turn)
                return {'turn':{'id':turn}}
        self.wire=Wire();self.client=CodexAppServerClient.__new__(CodexAppServerClient)
        self.client.transport=self.wire;self.client.server_version=CodexVersion.parse('codex-cli '+self.wire.version)
        self.client.version=SimpleNamespace(raw='synthetic')
        self.selection={'role':m.ROLE,'model':m.MODEL,'reasoning_effort':'medium','policy_digest':'a'*64,'fallback':False}
        self.enterContext(patch('app.communication.agent_roles.assert_current',return_value=self.selection))
        self.enterContext(patch('app.communication.agent_roles.resolve_role',return_value=self.selection))
        self.current=lambda:True

    @contextmanager
    def client_factory(self):yield self.client

    def binding(self):return live.live_calls(self.root,self.selection,assert_current=lambda:self.current(),client_factory=self.client_factory)

    def test_standard_is_explicit_and_threads_are_read_only_without_project_tools(self):
        with self.binding() as call:
            self.assertTrue(call({'original':'data','sources':[]},'inspect')['answer']['ok'])
            request=c.prepare(fixtures.snap(),[],self.now_date())
            call(request.payload,'synthesize')
        turns=[p for name,p in self.wire.calls if name=='turn/start']
        self.assertEqual(len(turns),2)
        self.assertTrue(all(p['serviceTierForTurn']=='default' for p in turns))
        self.assertTrue(all(p['sandboxPolicy']=={'type':'readOnly','networkAccess':False} for p in turns))
        self.assertEqual(turns[1]['outputSchema'],c.schema(request.payload))
        starts=[p for name,p in self.wire.calls if name=='thread/start']
        self.assertTrue(all(p['ephemeral'] and p['config']['features.shell_tool'] is False for p in starts))
        self.assertIs(self.client.transport,self.wire)

    @staticmethod
    def now_date():return datetime(2026,11,8).date()

    def test_disconnect_preserves_unknown_thread_turn_and_restores_transport(self):
        self.wire.fail='receive'
        with self.binding() as call:
            with self.assertRaises(Exception):call({},'inspect')
        marker=json.loads((self.root/'transport/001.json').read_text())
        self.assertEqual(marker['state'],'delivery_unknown');self.assertEqual(marker['turn_id'],'turn-1')
        self.assertEqual(marker['thread_id'],'thread-1');self.assertIs(self.client.transport,self.wire)
        self.assertEqual(len([x for x in self.wire.calls if x[0]=='turn/start']),1)

    def test_drift_between_thread_and_turn_prevents_paid_send(self):
        answers=iter([True,False]);self.current=lambda:next(answers)
        with self.binding() as call:
            with self.assertRaisesRegex(ValueError,'changed_before_send'):call({},'inspect')
        self.assertFalse(any(name=='turn/start' for name,_ in self.wire.calls))

    def test_reused_thread_is_rejected_before_second_turn(self):
        self.wire.reuse=True
        with self.binding() as call:
            call({},'inspect')
            with self.assertRaisesRegex(ValueError,'thread_reused'):call({},'inspect')
        self.assertEqual(len([x for x in self.wire.calls if x[0]=='turn/start']),1)


class Counter(unittest.TestCase):
    def test_lazy_pinned_counter_margin_cache_and_close(self):
        import io
        from types import SimpleNamespace
        cfg=SimpleNamespace(project=Path('/unused'),payload={'tokenizer':{'package_version':'test','encoding':'o200k_base','margin':1.2}})
        child=SimpleNamespace(stdin=io.StringIO(),stdout=io.StringIO('{"package_version":"test","encoding":"o200k_base"}\n7\n'),wait=lambda **kwargs:0)
        counter=live.IsolatedCounter(cfg)
        with patch.object(live.subprocess,'Popen',return_value=child) as factory,patch.object(live.select,'select',side_effect=lambda r,*args:(r,[],[])):
            self.assertFalse(factory.called);self.assertEqual(counter('abc'),9);self.assertEqual(counter('abc'),9)
            self.assertEqual(factory.call_count,1);self.assertEqual(child.stdin.getvalue().count('\n'),1)
            counter.close();self.assertTrue(child.stdin.closed);self.assertTrue(child.stdout.closed)



class WorkflowAuthority(unittest.TestCase):
    def test_run_and_tick_are_registered_as_confirmed_model_and_write_workflows(self):
        from app.workflows.commands import WORKFLOW_COMMANDS
        commands={c.command_id:c for c in WORKFLOW_COMMANDS}
        for action in ('run','tick'):
            command=commands['recovery_guide_'+action]
            self.assertTrue(command.requires_confirmation)
            self.assertEqual(command.risk,'paid_model_and_private_write')
            self.assertEqual(command.argv[-1],action)
        self.assertFalse(commands['recovery_guide_status'].requires_confirmation)



class DeliveryIndependence(unittest.TestCase):
    setUp=Runtime.setUp
    snapshot=Runtime.snapshot
    factory=Runtime.factory
    call=Runtime.call
    make=Runtime.make
    tick=Runtime.tick
    accept=Runtime.accept
    def test_already_accepted_delivery_needs_no_codex_role_or_authentication(self):
        self.accept();self.cloud=False;self.tick();self.cloud=True
        def unavailable():raise AssertionError('model readiness must not be consulted')
        self.runtime.readiness=unavailable
        self.runtime.delivery_readiness=lambda:{k:True for k in ('mac_available','user_session','network','icloud_auth')}
        self.assertEqual(self.tick()['state'],'completed');self.assertEqual(len(self.calls),2)



class AutomaticPublication(unittest.TestCase):
    snapshot=Runtime.snapshot
    factory=Runtime.factory
    call=Runtime.call
    make=Runtime.make
    tick=Runtime.tick
    accept=Runtime.accept
    def setUp(self):
        Runtime.setUp(self)
        self.runtime.automatic_profile=lambda snap,day:(fixtures.dossier(fixtures.context(snap)),
            replace(fixtures.context(snap),checked_on=day))

    # Reuse the fixture, not the manual-acceptance expectations of Runtime.
    def test_successful_tick_writes_both_copies_without_weekly_manual_action(self):
        result=self.tick();self.assertEqual(result['state'],'completed')
        self.assertEqual(len(self.calls),2);self.assertEqual(self.targets[0].read_bytes(),self.targets[1].read_bytes())
        self.assertEqual(self.tick()['action'],'replayed_receipt');self.assertEqual(len(self.calls),2)

    def test_invalid_dossier_keeps_old_copies_and_does_not_call_model_again(self):
        def bad(snap,day):return {'applications':[]},replace(fixtures.context(snap),checked_on=day)
        self.runtime.automatic_profile=bad
        result=self.tick();self.assertEqual(result['automatic_publication'],'blocked')
        self.assertFalse(any(p.exists() for p in self.targets));self.tick();self.assertEqual(len(self.calls),2)

    def test_changed_macos_requires_attention_without_publishing(self):
        def bad(snap,day):return fixtures.dossier(fixtures.context(snap)),replace(fixtures.context(snap),checked_on=day,macos_observed='Changed OS')
        self.runtime.automatic_profile=bad
        result=self.tick();self.assertEqual(result['automatic_publication'],'blocked')
        self.assertFalse(any(p.exists() for p in self.targets))

    def test_automatic_second_week_starts_from_last_published_guide(self):
        self.assertEqual(self.tick()['state'],'completed');first=self.targets[0].read_text()
        self.now+=timedelta(days=7);self.assertEqual(self.tick()['state'],'completed')
        self.assertEqual(self.calls[2][0]['original']['text'],first);self.assertEqual(len(self.calls),4)

    def test_crash_after_approval_before_scheduler_attachment_reuses_acceptance(self):
        original=self.scheduler.attach_publication
        with patch.object(self.scheduler,'attach_publication',side_effect=SystemExit()):
            with self.assertRaises(SystemExit):self.tick()
        self.scheduler.attach_publication=original
        self.assertEqual(self.tick()['state'],'completed');self.assertEqual(len(self.calls),2)


class SourceAndPolicy(unittest.TestCase):
    setUp=Configuration.setUp
    save=Configuration.save
    # Reuse the private configuration fixture without inherited test cases.
    def test_main_documents_are_read_from_git_objects_without_switching_worktree(self):
        import subprocess
        def git(*args):return subprocess.check_output(['git','-C',str(self.project),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',*args],text=True).strip()
        git('init','-q','-b','main');(self.project/'docs').mkdir();doc=self.project/'docs/current.md'
        doc.write_text('First public documentation.');git('add','docs/current.md');git('commit','-qm','first')
        git('branch','data');doc.write_text('Current main documentation.');git('commit','-qam','second')
        main=git('rev-parse','main');git('checkout','-q','data')
        seed=self.root/'guide.txt';seed.write_text(fixtures.ORIGINAL)
        cfg=self.save()
        for path in cfg.destinations:path.parent.mkdir(parents=True,exist_ok=True)
        runtime,counter=live.build(cfg);snap=runtime.snapshot_provider(seed)
        self.assertEqual(snap.head,main);self.assertIn('Current main documentation.',snap.sources[0].text)
        self.assertEqual(git('branch','--show-current'),'data');self.assertEqual(doc.read_text(),'First public documentation.')
        self.assertTrue(runtime.assert_snapshot(snap,seed))
        git('update-ref','refs/heads/main',git('rev-parse','data'))
        self.assertFalse(runtime.assert_snapshot(snap,seed));self.assertIsNone(counter.child)

    def test_automatic_profile_marks_settings_unverified_and_checks_macos_baseline(self):
        from types import SimpleNamespace
        self.value['publication_policy']={'mode':'validated_auto_v1','applications':['Python','Codex'],
            'macos_baseline':'Test OS'}
        cfg=self.save()
        for path in cfg.destinations:path.parent.mkdir(parents=True,exist_ok=True)
        runtime,_=live.build(cfg)
        with patch.object(live.subprocess,'check_output',return_value='Test OS\n'):
            dossier,context=runtime.automatic_profile(fixtures.snap(),datetime(2026,11,8).date())
        self.assertTrue(context.application_scope_approved)
        self.assertEqual(context.macos_expected,context.macos_observed)
        self.assertTrue(all(v['status']=='unverified' for a in dossier['applications'] for v in a['fields'].values()))



class BillingBasis(unittest.TestCase):
    setUp=TransportBinding.setUp
    client_factory=TransportBinding.client_factory
    binding=TransportBinding.binding
    def test_api_key_account_is_rejected_before_thread_or_turn(self):
        original=self.wire.request
        def request(method,params):
            return {'account':{'type':'apiKey'}} if method=='account/read' else original(method,params)
        self.wire.request=request
        with self.assertRaisesRegex(ValueError,'subscription_account_required'):
            with self.binding() as call:call({},'inspect')
        self.assertFalse(any(name in {'thread/start','turn/start'} for name,_ in self.wire.calls))


if __name__=='__main__':unittest.main()
