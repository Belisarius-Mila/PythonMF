"""Weekly composition: snapshot -> generator -> explicit acceptance -> two copies.

Construction is inert. tick uses the scheduler's one durable slot. Delivery
and reconciliation never call the model. No production configuration is made.
"""
from dataclasses import asdict
from datetime import datetime
import json
import threading
from pathlib import Path
from zoneinfo import ZoneInfo

from app import recovery_guide_consolidation as c
from app import recovery_guide_maintainer as m
from app import recovery_guide_quality as q
from app.file_persistence import atomic_create_text, atomic_write_json
from app.recovery_guide_costing import hydrate
from app.recovery_guide_sources import canonical_json,digest
from app.release_usage import TOKEN_KEYS


class RecoveryRuntime:
    def __init__(self, *, scheduler, publication, limits, bootstrap:Path, bootstrap_sha256:str,
                 snapshot_provider, count_tokens, call_factory, readiness, assert_snapshot,
                 cloud_audit, delivery_readiness=None, assert_activation=lambda:None):
        self.scheduler,self.publication,self.limits=scheduler,publication,limits
        self.bootstrap,self.bootstrap_sha256=bootstrap,bootstrap_sha256
        self.snapshot_provider,self.count=snapshot_provider,count_tokens
        self.call_factory,self.readiness,self.assert_snapshot=call_factory,readiness,assert_snapshot
        self.cloud_audit,self.assert_activation=cloud_audit,assert_activation
        self.delivery_readiness=delivery_readiness or readiness
        if scheduler.scope!=publication.scope:raise ValueError('runtime_scope_mismatch')
        if scheduler.activation is not None and asdict(limits)!=scheduler.activation.payload['limits']:
            raise ValueError('runtime_limits_outside_activation')
        self.root=scheduler.root.parent/'analysis'
        if self.root==publication.root or self.root==scheduler.root:raise ValueError('runtime_state_collision')
        self.prepared=None;self.now=None;self.lock=threading.Lock()

    def _directory(self,request_id):
        from app.recovery_guide_scheduler import ID
        if not isinstance(request_id,str) or not ID.fullmatch(request_id):raise ValueError('runtime_request_id')
        root=self.root/request_id
        if any(p.is_symlink() for p in (root,*root.parents)):raise ValueError('runtime_analysis_alias')
        return root

    def _original(self):
        jobs=self.scheduler._jobs()
        completed=[j for j in jobs if j['state'] in {'completed','completed_no_change'}]
        local,cloud=self.publication.destinations
        if completed:
            last=max(completed,key=lambda j:j['due_utc']);sha=last['candidate_sha256']
            if not all(p.is_file() and not p.is_symlink() and digest(p.read_bytes())==sha for p in (local,cloud)):
                raise ValueError('runtime_last_accepted_copies_changed')
            return local
        if (self.bootstrap.is_symlink() or not self.bootstrap.is_file()
                or digest(self.bootstrap.read_bytes())!=self.bootstrap_sha256):raise ValueError('runtime_bootstrap_changed')
        return self.bootstrap

    def _preflight(self,job):
        self.assert_activation()
        original=self._original();snapshot=self.snapshot_provider(original)
        policy=self.scheduler.policy
        limits=self.limits
        if (limits.max_calls>policy.max_calls or limits.run_credits>policy.run_credits
                or limits.month_credits>policy.month_credits or limits.seconds>policy.max_seconds):
            raise ValueError('runtime_budget_policy_mismatch')
        day=self.now.astimezone(ZoneInfo('Europe/Prague')).date()
        planned=m.plan(snapshot,self.count,limits,review_date=day)
        self.prepared=(job,snapshot,original,planned)
        return {'snapshot_sha256':snapshot.sha256,'original_sha256':snapshot.original.sha256,
                'source_count':len(snapshot.sources),'planned_calls':planned['calls'],
                'reserved_credits':planned['reserved_credits'],'copies_current':False}

    def _current(self,snapshot,original):
        try:
            self.assert_activation()
            return self.assert_snapshot(snapshot,original) is True
        except Exception:return False

    def _analyze(self,job):
        identity,snapshot,original,_=self.prepared
        if any(identity[k]!=job[k] for k in ('request_id','slot')):raise ValueError('runtime_dispatch_changed')
        directory=self._directory(job['request_id']);directory.mkdir(parents=True,mode=0o700,exist_ok=True)
        packet={'snapshot':asdict(snapshot),'source_path':str(original),'job_identity':job['identity_sha256'],
                'format_contract':c.VERSION,'revision_time':self.now.isoformat()}
        atomic_create_text(directory/'packet.json',canonical_json(packet))
        # The injected factory must assert the same dedicated role and Standard
        # scope. Model setup happens only after scheduler admission is durable.
        with self.call_factory(directory,job['executor'],assert_current=lambda:self._current(snapshot,original)) as call:
            index=0
            def recorded(payload,kind):
                nonlocal index
                index+=1;path=directory/'raw'/f'{index:03d}.json'
                atomic_create_text(path,canonical_json({'state':'delivery_unknown','phase':kind,
                    'request_sha256':digest(canonical_json(payload))}))
                response=call(payload,kind)
                atomic_write_json(path,{'state':'received_unreviewed','phase':kind,'response':response})
                return response
            receipt=m.run(snapshot,state_dir=directory/'controller',now=self.now,limits=self.limits,
                count_tokens=self.count,call=recorded,approved_snapshot=snapshot.sha256,
                assert_sources=lambda:self._current(snapshot,original),confirmed=True,
                weekday=self.scheduler.policy.weekday,hour=self.scheduler.policy.hour)
        atomic_write_json(directory/'result.json',receipt)
        usage={key:sum(row.get('usage',{}).get(key,0) for row in receipt.get('turns',[])) for key in TOKEN_KEYS}
        return {'state':receipt['state'],'request_id':job['request_id'],'slot':job['slot'],
            'snapshot_sha256':snapshot.sha256,'source_count':len(snapshot.sources),
            'coverage':receipt.get('coverage',0),'candidate_sha256':receipt.get('candidate_sha256'),
            'executor':job['executor'],'usage':usage,'reported_model_turns':receipt.get('model_calls',0),
            'simulation':self.scheduler.simulation,'publication':None,'format_contract':c.VERSION,
            'usage_complete':receipt.get('completed_calls',0)==receipt.get('model_calls',0)}

    def _load(self,request_id):
        directory=self._directory(request_id)
        for part in ('packet.json','result.json','controller'):
            if (directory/part).is_symlink():raise ValueError('runtime_artifact_alias')
        packet=json.loads((directory/'packet.json').read_text());snapshot=hydrate(packet['snapshot'])
        job=next((j for j in self.scheduler._jobs() if j['request_id']==request_id),None)
        result=json.loads((directory/'result.json').read_text())
        if (job is None or packet['job_identity']!=job['identity_sha256']
            or snapshot.sha256!=job['snapshot_sha256'] or result['state']!='review'
            or result['candidate_sha256']!=job.get('candidate_sha256')
            or packet['format_contract']!=c.VERSION):raise ValueError('runtime_review_binding_changed')
        controller=directory/'controller';slot=job['slot']
        paths=[controller/(slot+suffix) for suffix in ('-request.json','-evidence.json','-candidate.txt')]
        if any(p.is_symlink() for p in paths):raise ValueError('runtime_artifact_alias')
        request=c.Request(paths[0].read_text());answer=json.loads(paths[1].read_text())
        candidate=c.validate(answer,snapshot,request)['candidate']
        if paths[2].read_bytes()!=candidate.encode() or digest(candidate)!=result['candidate_sha256']:
            raise ValueError('runtime_candidate_changed')
        return job,packet,snapshot,request,answer

    def prepare_acceptance(self,request_id,*,dossier,context):
        self.assert_activation()
        job,packet,snapshot,request,answer=self._load(request_id)
        if job['state']!='awaiting_acceptance' or not self._current(snapshot,Path(packet['source_path'])):
            raise ValueError('runtime_review_not_current')
        return self.publication.prepare(answer,snapshot,dossier,context,format_request=request)

    def accept(self,request_id,draft,*,confirmed_binding,confirmed_identity,confirmed=False,now=None):
        self.assert_activation()
        job,packet,snapshot,request,answer=self._load(request_id)
        raw=json.loads(draft.packet_json)
        if (canonical_json(raw['snapshot'])!=canonical_json(asdict(snapshot)) or raw['answer']!=answer or raw.get('format_request')!=request.envelope
            or confirmed_identity!=job['identity_sha256']):raise ValueError('runtime_acceptance_changed')
        if job['state']=='awaiting_acceptance' and not self._current(snapshot,Path(packet['source_path'])):
            raise ValueError('runtime_review_not_current')
        receipt=self.publication.accept(draft,request_id=request_id,confirmed_binding=confirmed_binding,
            confirmed=confirmed,now=now)
        if receipt['state']=='confirmation_required':return receipt
        return self.scheduler.attach_publication(request_id,
            {'request_id':request_id,'approval_sha256':receipt['approval_sha256']},
            confirmed_identity=confirmed_identity,confirmed=confirmed)

    def _deliver(self,reference):
        def current(manifest):
            job,saved,snapshot,_,_=self._load(reference['request_id'])
            return (self._current(snapshot,Path(saved['source_path']))
                and manifest['candidate_sha256']==job['candidate_sha256']
                and manifest['original_sha256']==snapshot.original.sha256)
        return self.publication.execute(reference['request_id'],approval_sha256=reference['approval_sha256'],
            current_inputs=current,cloud_audit=self.cloud_audit,now=self.now)

    def tick(self,now:datetime,*,trigger='timer'):
        if not self.lock.acquire(blocking=False):return {'state':'busy','model_calls':0}
        try:
            self.assert_activation();self.now=now;self.prepared=None
            return self.scheduler.tick(now,readiness=self.readiness,preflight=self._preflight,analyze=self._analyze,
                delivery_status=lambda r:self.publication.status(r['request_id']),deliver=self._deliver,trigger=trigger,
                delivery_readiness=self.delivery_readiness)
        finally:self.lock.release()
