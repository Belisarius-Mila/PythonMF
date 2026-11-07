"""REC-05 durable scheduler, sandbox callbacks only; no live model transport.

Public production CLI remains inactive until REC-06. No installation, daemon,
external notification or model call occurs on import or preview/status.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta, timezone
import json
import math
from pathlib import Path
import re
import tempfile
import time as monotonic_time
from typing import Callable
from zoneinfo import ZoneInfo

from app.file_persistence import atomic_write_json, exclusive_file_lock, FileLockTimeoutError
from app.recovery_guide_sources import canonical_json, digest
from app.recovery_guide_maintainer import MODEL, ROLE
from app.release_usage import normalize_usage, estimate_standard_credits

ZONE = ZoneInfo("Europe/Prague")
DONE = {"completed", "completed_no_change"}
DELIVERY = {"delivery_ready", "delivery_in_flight", "pending_icloud"}
STATES = DONE | DELIVERY | {"analysis_in_flight","awaiting_acceptance","attention"}
COMMON_READY = ("mac_available", "user_session", "network", "icloud_auth")
ANALYSIS_READY = (*COMMON_READY, "codex_auth", "role_current", "standard_tier", "context_proven", "source_scope_approved")
HASH = re.compile(r"[0-9a-f]{64}")
ID = re.compile(r"recovery-\d{4}-W\d{2}")


@dataclass(frozen=True)
class SchedulerPolicy:
    enabled: bool = False
    schedule_approved: bool = False
    budget_approved: bool = False
    weekday: int = 6
    hour: int = 9
    not_before: str | None = None
    role_policy_digest: str | None = None
    run_credits: float = 0
    month_credits: float = 0
    max_calls: int = 0
    max_seconds: int = 0

    @property
    def sha256(self):
        return digest(canonical_json(asdict(self)))

    def check(self):
        if type(self.weekday) is not int or self.weekday not in range(7) or type(self.hour) is not int or self.hour not in range(24):
            raise ValueError("invalid_schedule")
        if self.enabled:
            if self.schedule_approved is not True or self.budget_approved is not True:
                raise ValueError("unapproved_policy")
            if not HASH.fullmatch(self.role_policy_digest or "") or not self.not_before:
                raise ValueError("missing_policy_binding")
            _instant(self.not_before)
            if (any(type(n) not in {int,float} or not math.isfinite(n) or n <= 0 for n in (self.run_credits,self.month_credits))
                    or any(type(n) is not int or n <= 0 for n in (self.max_calls,self.max_seconds))):
                raise ValueError("invalid_budget")


def _instant(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("timezone_required")
    return result.astimezone(timezone.utc)


def due_slot(now: datetime, policy: SchedulerPolicy) -> tuple[str, datetime]:
    policy.check()
    if now.tzinfo is None:
        raise ValueError("timezone_required")
    local = now.astimezone(ZONE)
    day = local.date() - timedelta(days=(local.weekday()-policy.weekday)%7)

    def due(day):
        # Fold 0 selects the first repeated hour. A nonexistent spring hour
        # coalesces forward on round-trip through UTC, once per ISO week.
        return datetime.combine(day,time(policy.hour),tzinfo=ZONE).replace(fold=0).astimezone(timezone.utc)

    result = due(day)
    if result > now.astimezone(timezone.utc):
        day -= timedelta(days=7);result = due(day)
    iso = day.isocalendar()
    return f"{iso.year}-W{iso.week:02d}",result


def schedule_preview(now: datetime, policy: SchedulerPolicy = SchedulerPolicy()) -> dict:
    slot,due = due_slot(now,policy)
    next_day = due.astimezone(ZONE).date()+timedelta(days=7)
    following = datetime.combine(next_day,time(policy.hour),tzinfo=ZONE).replace(fold=0)
    return {"timezone":"Europe/Prague","weekday":policy.weekday,"hour":policy.hour,
        "approved":policy.schedule_approved,"enabled":policy.enabled,"latest_nominal_slot":slot,
        "latest_due_utc":due.isoformat(),"next_due_local":following.astimezone(timezone.utc).astimezone(ZONE).isoformat(),
        "missed_slots_policy":"one_latest_due_only","model_calls":0,"writes":False}


def inspect_status(root: Path) -> dict:
    """Read-only projection for CLI/Cockpit workflow receipt. Never mkdir/lock."""
    if any(p.is_symlink() for p in (root,*root.parents)):
        raise ValueError("state_alias_refused")
    jobs=[]
    if root.exists():
        for path in sorted(root.glob("recovery-????-W??.json")):
            jobs.append(_read_job(path))
    pending=[j for j in jobs if j["state"] not in DONE]
    last=jobs[-1] if jobs else None
    fields=("request_id","slot","state","candidate_sha256","snapshot_sha256","source_count","coverage",
            "credits","reserved_credits","reported_model_turns","delivery","reason","updated_at","executor","usage")
    project=lambda job:{key:job[key] for key in fields if key in job}
    return {"state":"not_configured" if not jobs else "attention" if pending else "idle",
            "last_run":project(last) if last else None,"pending":[project(j) for j in pending],
            "job_count":len(jobs),"scope":"sandbox_only","model_calls":0,"credits_are_simulated":True,
            "live_status_audit":False,"writes":False}


def _read_job(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>128_000:raise ValueError("invalid_job_file")
    job=json.loads(path.read_text())
    if not isinstance(job,dict):raise ValueError("invalid_job")
    if (job.get("schema")!=1 or job.get("simulation") is not True or not isinstance(job.get("request_id"),str) or not ID.fullmatch(job["request_id"])
            or path.name!=job["request_id"]+".json" or not isinstance(job.get("state"),str) or job["state"] not in STATES
            or type(job.get("source_count")) is not int or job["source_count"]<=0):raise ValueError("invalid_job")
    for key in ("snapshot_sha256","original_sha256","policy_sha256","identity_sha256"):
        if not isinstance(job.get(key),str) or not HASH.fullmatch(job[key]):raise ValueError("invalid_job_hash")
    for key in ("reserved_credits","credits"):
        value=job.get(key,0)
        if type(value) not in {int,float} or not math.isfinite(value) or value<0:raise ValueError("invalid_job_cost")
    if "coverage" in job and (type(job["coverage"]) is not int or not 0<=job["coverage"]<=job["source_count"]):
        raise ValueError("invalid_coverage")
    if "usage" in job and normalize_usage(job["usage"]) is None:raise ValueError("invalid_usage")
    if "reason" in job and (not isinstance(job["reason"],str) or job["reason"] not in {"analysis_outcome_unknown","analysis_not_verified","delivery_not_verified"}):
        raise ValueError("invalid_reason")
    return job


class WeeklyScheduler:
    def __init__(self, root: Path, *, sandbox_root: Path, policy: SchedulerPolicy,
                 mode: str = "sandbox", clock: Callable[[],float] = monotonic_time.monotonic):
        if mode != "sandbox":raise ValueError("production_scheduler_disabled")
        policy.check()
        self.sandbox=sandbox_root.resolve(strict=True)
        allowed=(Path(__file__).resolve().parents[1]/".venv",Path(tempfile.gettempdir()).resolve())
        if not sandbox_root.is_absolute() or sandbox_root.is_symlink() or not any(self.sandbox!=p and self.sandbox.is_relative_to(p) for p in allowed):
            raise ValueError("sandbox_not_isolated")
        self.root=root.absolute();self.policy=policy;self.clock=clock
        if not self.root.resolve().is_relative_to(self.sandbox) or ".." in self.root.parts:
            raise ValueError("state_outside_sandbox")
        stat=self.sandbox.stat();self.identity=(stat.st_dev,stat.st_ino)
        self._guard()

    def _guard(self):
        stat=self.sandbox.stat()
        if (stat.st_dev,stat.st_ino)!=self.identity:raise ValueError("sandbox_changed")
        if any(p.is_symlink() for p in (self.root,*self.root.parents)) or (self.root/"scheduler.lock").is_symlink():
            raise ValueError("state_alias_refused")
        if self.root.exists() and self.root.stat().st_mode & 0o077:raise ValueError("state_not_private")

    def _jobs(self):
        self._guard();result=[]
        for path in sorted(self.root.glob("recovery-????-W??.json")):
            result.append(_read_job(path))
        return result

    def _save(self,job):
        atomic_write_json(self.root/(job["request_id"]+".json"),job)

    @staticmethod
    def _ready(readiness):
        try:
            result=readiness()
            return result if isinstance(result,dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _public(job,action):
        return {**job,"action":action,"scope":"sandbox_only","model_calls":0,"credits_are_simulated":True}

    def _result(self,job,result):
        allowed={"state","request_id","slot","snapshot_sha256","source_count","coverage","candidate_sha256",
                 "executor","usage","reported_model_turns","publication","simulation"}
        if not isinstance(result,dict) or result.get("simulation") is not True:
            raise ValueError("invalid_analysis_receipt")
        if type(result.get("source_count")) is not int:raise ValueError("invalid_source_count")
        for key in ("request_id","slot","snapshot_sha256","source_count"):
            if result.get(key)!=job[key]:raise ValueError("analysis_binding_changed")
        executor=result.get("executor",{})
        if (executor.get("role")!=ROLE or executor.get("model")!=MODEL or executor.get("reasoning_effort")!="medium"
                or executor.get("policy_digest")!=self.policy.role_policy_digest):raise ValueError("executor_changed")
        usage=normalize_usage(result.get("usage"));credits=estimate_standard_credits(MODEL,usage)
        if usage is None or credits is None:raise ValueError("unknown_usage")
        job.update(usage=usage,credits=credits)
        calls=result.get("reported_model_turns")
        if type(calls) is not int or calls<1:raise ValueError("invalid_call_count")
        job["reported_model_turns"]=calls
        if set(result)-allowed:raise ValueError("unexpected_analysis_payload")
        if calls>job["planned_calls"]:raise ValueError("call_limit")
        if credits>job["reserved_credits"] or credits>self.policy.run_credits:raise ValueError("cost_limit")
        coverage=result.get("coverage")
        if type(coverage) is int and 0<=coverage<=job["source_count"]:job["coverage"]=coverage
        if type(coverage) is not int or coverage!=job["source_count"]:raise ValueError("incomplete_coverage")
        sha=result.get("candidate_sha256")
        if not isinstance(sha,str) or not HASH.fullmatch(sha):raise ValueError("missing_candidate")
        job.update(candidate_sha256=sha,coverage=result["coverage"])
        if result.get("state")=="unchanged":
            if sha!=job["original_sha256"] or result.get("publication") is not None or not job["copies_current"]:
                raise ValueError("false_no_change")
            job["state"]="completed_no_change"
        elif result.get("state")=="review":
            publication=result.get("publication")
            job["state"]="awaiting_acceptance"
            if publication is not None:
                self._reference(job,publication)
                job.update(publication=publication,state="delivery_ready")
        else:raise ValueError("analysis_attention")

    @staticmethod
    def _reference(job,publication):
        if (not isinstance(publication,dict) or set(publication)!={"request_id","approval_sha256"}
                or publication["request_id"]!=job["request_id"]
                or not isinstance(publication["approval_sha256"],str) or not HASH.fullmatch(publication["approval_sha256"])):
            raise ValueError("invalid_publication_reference")

    def _deliver(self,job,now,readiness,delivery_status,deliver):
        self._reference(job,job["publication"])
        ready=self._ready(readiness)
        if any(ready.get(key) is not True for key in COMMON_READY):
            return self._public(job,"waiting_delivery_dependencies")
        known=delivery_status(dict(job["publication"]))
        for key,expected in (("request_id",job["request_id"]),("approval_sha256",job["publication"]["approval_sha256"]),
                             ("candidate_sha256",job["candidate_sha256"]),("snapshot_sha256",job["snapshot_sha256"]),("scope","sandbox_only")):
            if known.get(key)!=expected:raise ValueError("delivery_binding_changed")
        if known.get("state") not in {"accepted","applying","pending_icloud","uploaded"}:
            raise ValueError("delivery_attention")
        job.update(state="delivery_in_flight",updated_at=now.isoformat());self._save(job)
        result=deliver(dict(job["publication"]))
        for key in ("request_id","approval_sha256","candidate_sha256","snapshot_sha256","scope"):
            if result.get(key)!=known.get(key):raise ValueError("delivery_result_changed")
        if result.get("state") not in {"uploaded","pending_icloud"}:raise ValueError("delivery_attention")
        if result.get("copies")!={"local":"candidate","icloud":"candidate"}:raise ValueError("delivery_copies_unverified")
        job.update(state="completed" if result["state"]=="uploaded" else "pending_icloud",
                   delivery={"state":result["state"],"copies":result.get("copies",{}),"physical_iphone_acceptance":"not_verified"})
        self._save(job)
        return self._public(job,"delivery_reconciled")

    @staticmethod
    def _verify_no_change(job,verify_unchanged):
        if verify_unchanged is None:raise ValueError("missing_final_copy_audit")
        proof=verify_unchanged(json.loads(canonical_json(job)))
        if (not isinstance(proof,dict) or proof.get("copies_current") is not True
                or proof.get("candidate_sha256")!=job["candidate_sha256"]
                or proof.get("snapshot_sha256")!=job["snapshot_sha256"]):raise ValueError("no_change_not_verified")
        job["final_copies_verified"]=True

    def tick(self,now:datetime,*,readiness:Callable,preflight:Callable,analyze:Callable,
             delivery_status:Callable,deliver:Callable,trigger="timer",verify_unchanged:Callable|None=None) -> dict:
        self._guard()
        if trigger not in {"timer","manual"}:raise ValueError("invalid_trigger")
        slot,due=due_slot(now,self.policy)
        if self.policy.enabled is not True:return {"state":"activation_required","model_calls":0,"writes":False}
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        try:
            with exclusive_file_lock(self.root/"scheduler",timeout=0):
                jobs=self._jobs();pending=[j for j in jobs if j["state"] not in DONE]
                if len(pending)>1:raise ValueError("multiple_pending_jobs")
                if pending:
                    job=pending[0]
                    if job["policy_sha256"]!=self.policy.sha256:return self._public(job,"policy_changed")
                    if job["state"]=="analysis_in_flight":
                        job.update(state="attention",reason="analysis_outcome_unknown");self._save(job)
                    if job["state"] in DELIVERY:
                        try:return self._deliver(job,now,readiness,delivery_status,deliver)
                        except Exception:
                            job.update(state="attention",reason="delivery_not_verified");self._save(job)
                    return self._public(job,"operator_attention" if job["state"]=="attention" else "awaiting_acceptance")
                if due<_instant(self.policy.not_before):return {"state":"not_due","model_calls":0}
                request_id="recovery-"+slot
                previous=next((j for j in jobs if j["request_id"]==request_id),None)
                if previous:return self._public(previous,"replayed_receipt")
                if jobs and due<=max(_instant(j["due_utc"]) for j in jobs):return {"state":"obsolete_clock_slot","model_calls":0}
                ready=self._ready(readiness)
                if any(ready.get(key) is not True for key in ANALYSIS_READY):
                    return {"state":"waiting_dependencies","missing":[k for k in ANALYSIS_READY if ready.get(k) is not True],"model_calls":0}
                prepared=preflight({"request_id":request_id,"slot":slot})
                for key in ("snapshot_sha256","original_sha256"):
                    if not isinstance(prepared.get(key),str) or not HASH.fullmatch(prepared[key]):raise ValueError("invalid_preflight")
                if (type(prepared.get("source_count")) is not int or prepared["source_count"]<=0
                        or type(prepared.get("copies_current")) is not bool
                        or type(prepared.get("planned_calls")) is not int or not 1<=prepared["planned_calls"]<=self.policy.max_calls):raise ValueError("invalid_preflight")
                reserve=prepared.get("reserved_credits")
                if type(reserve) not in {int,float} or not math.isfinite(reserve) or not 0<reserve<=self.policy.run_credits:
                    return {"state":"budget_blocked","model_calls":0}
                month=now.astimezone(ZONE).strftime("%Y-%m")
                spent=sum(max(j["reserved_credits"],j.get("credits",0)) for j in jobs if j["month"]==month)
                if spent+reserve>self.policy.month_credits:return {"state":"budget_blocked","model_calls":0}
                job={"schema":1,"simulation":True,"request_id":request_id,"slot":slot,"due_utc":due.isoformat(),"month":month,
                     "policy_sha256":self.policy.sha256,"trigger":trigger,"state":"analysis_in_flight",
                     "executor":{"role":ROLE,"model":MODEL,"reasoning_effort":"medium","policy_digest":self.policy.role_policy_digest},
                     "snapshot_sha256":prepared["snapshot_sha256"],"original_sha256":prepared["original_sha256"],
                     "source_count":prepared["source_count"],"planned_calls":prepared["planned_calls"],
                     "copies_current":prepared["copies_current"],
                     "reserved_credits":reserve,"analysis_invocations":1,"updated_at":now.isoformat()}
                job["identity_sha256"]=digest(canonical_json(job));self._save(job)
                start=self.clock()
                try:
                    result=analyze(json.loads(canonical_json(job)))
                    self._result(job,result)
                    if self.clock()-start>self.policy.max_seconds:raise ValueError("time_limit")
                    if job["state"]=="completed_no_change":self._verify_no_change(job,verify_unchanged)
                except Exception:
                    job.update(state="attention",reason="analysis_not_verified");self._save(job)
                    return self._public(job,"operator_attention")
                self._save(job)
                if job["state"] in DELIVERY:
                    try:return self._deliver(job,now,readiness,delivery_status,deliver)
                    except Exception:
                        job.update(state="attention",reason="delivery_not_verified");self._save(job)
                return self._public(job,"analysis_recorded")
        except FileLockTimeoutError:
            return {"state":"busy","model_calls":0}
        except (OSError,ValueError,KeyError,TypeError):
            return {"state":"attention","reason":"scheduler_precondition_not_verified","model_calls":0}

    def attach_publication(self,request_id:str,reference:dict,*,confirmed_identity:str,confirmed=False) -> dict:
        """Operator attaches an already accepted REC-04 artifact, never a model."""
        if not ID.fullmatch(request_id):raise ValueError("invalid_job_id")
        self._guard()
        if not self.root.exists():raise ValueError("unknown_job")
        with exclusive_file_lock(self.root/"scheduler",timeout=0):
            job=next((j for j in self._jobs() if j["request_id"]==request_id),None)
            if job is None or self.policy.enabled is not True or job["policy_sha256"]!=self.policy.sha256:
                raise ValueError("job_policy_not_authorized")
            if confirmed_identity!=job["identity_sha256"]:raise ValueError("attachment_not_confirmed")
            if job.get("publication")==reference and job["state"] in DELIVERY|DONE:
                return self._public(job,"replayed_attachment")
            if confirmed is not True:raise ValueError("attachment_not_confirmed")
            if job["state"]!="awaiting_acceptance":raise ValueError("job_not_awaiting_acceptance")
            self._reference(job,reference);job.update(publication=dict(reference),state="delivery_ready");self._save(job)
            return self._public(job,"acceptance_attached")

    def reconcile_analysis(self,request_id:str,result:dict,*,confirmed_identity:str,confirmed=False,
                           verify_unchanged:Callable|None=None) -> dict:
        """Attach a known local receipt after a crash; never resubmit analysis."""
        if not ID.fullmatch(request_id):raise ValueError("invalid_job_id")
        self._guard()
        if not self.root.exists():raise ValueError("unknown_job")
        with exclusive_file_lock(self.root/"scheduler",timeout=0):
            job=next((j for j in self._jobs() if j["request_id"]==request_id),None)
            if job is None or self.policy.enabled is not True:raise ValueError("job_policy_not_authorized")
            if (confirmed is not True or confirmed_identity!=job["identity_sha256"]
                    or job["policy_sha256"]!=self.policy.sha256
                    or job["state"] not in {"attention","analysis_in_flight"}
                    or job.get("reason") not in {None,"analysis_not_verified","analysis_outcome_unknown"}):
                raise ValueError("reconciliation_not_confirmed")
            candidate=json.loads(canonical_json(job));self._result(candidate,result)
            if candidate["state"]=="completed_no_change":self._verify_no_change(candidate,verify_unchanged)
            if candidate["credits"]<job.get("credits",0):raise ValueError("known_cost_cannot_disappear")
            if candidate["reported_model_turns"]<job.get("reported_model_turns",0):raise ValueError("known_calls_cannot_disappear")
            candidate.pop("reason",None);candidate["reconciled_locally"]=True;self._save(candidate)
            return self._public(candidate,"known_receipt_attached")
