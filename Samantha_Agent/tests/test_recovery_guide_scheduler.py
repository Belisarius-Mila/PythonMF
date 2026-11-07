from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from app import recovery_guide_scheduler as s
from app.file_persistence import exclusive_file_lock
from scripts.recovery_guide_launchd import check_environment, launch_agent
from tests.test_recovery_guide import USAGE, CLOUD
from tests import test_recovery_guide_publication as publication_fixtures


class Scheduler(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name).resolve();self.root=self.base/"schedule"
        self.policy=s.SchedulerPolicy(enabled=True,schedule_approved=True,budget_approved=True,
            not_before="2026-11-01T00:00:00+00:00",role_policy_digest="a"*64,
            run_credits=2,month_credits=10,max_calls=2,max_seconds=60)
        self.scheduler=s.WeeklyScheduler(self.root,sandbox_root=self.base,policy=self.policy)
        self.now=datetime(2026,11,8,10,tzinfo=ZoneInfo("Europe/Prague"))
        self.analyses=[];self.deliveries=[];self.ready={k:True for k in s.ANALYSIS_READY}
        self.copies_current=False;self.publish=True;self.cloud_uploaded=True

    def preflight(self,job):
        return {"snapshot_sha256":"b"*64,"original_sha256":"c"*64,"source_count":2,
                "planned_calls":2,"reserved_credits":1,"copies_current":self.copies_current}

    def result(self,job,*,publication=True):
        return {"state":"review","request_id":job["request_id"],"slot":job["slot"],
            "snapshot_sha256":job["snapshot_sha256"],"source_count":job["source_count"],"coverage":job["source_count"],
            "candidate_sha256":"d"*64,"executor":job["executor"],"usage":USAGE,
            "reported_model_turns":2,"simulation":True,
            "publication":{"request_id":job["request_id"],"approval_sha256":"e"*64} if publication else None}

    def analyze(self,job):
        self.analyses.append(job)
        return self.result(job,publication=self.publish)

    def delivery_status(self,reference):
        return {**reference,"state":"accepted","candidate_sha256":"d"*64,"snapshot_sha256":"b"*64,"scope":"sandbox_only"}

    def deliver(self,reference):
        self.deliveries.append(reference)
        return {**self.delivery_status(reference),"state":"uploaded" if self.cloud_uploaded else "pending_icloud",
                "copies":{"local":"candidate","icloud":"candidate"}}

    def tick(self,**kwargs):
        params=dict(readiness=lambda:self.ready,preflight=self.preflight,analyze=self.analyze,
                    delivery_status=self.delivery_status,deliver=self.deliver)
        params.update(kwargs)
        return self.scheduler.tick(self.now,**params)

    def test_one_dispatch_same_week_for_timer_and_manual(self):
        result=self.tick();again=self.tick(trigger="manual")
        self.assertEqual(result["state"],"completed")
        self.assertEqual(again["action"],"replayed_receipt")
        self.assertEqual(len(self.analyses),1);self.assertEqual(len(self.deliveries),1)
        self.assertEqual(result["model_calls"],0)
        self.assertTrue(result["credits_are_simulated"])

    def test_restart_reuses_receipt_without_calling_analysis(self):
        self.tick()
        self.scheduler=s.WeeklyScheduler(self.root,sandbox_root=self.base,policy=self.policy)
        self.assertEqual(self.tick()["action"],"replayed_receipt")
        self.assertEqual(len(self.analyses),1)

    def test_disabled_policy_never_creates_state_or_calls_callbacks(self):
        self.scheduler=s.WeeklyScheduler(self.root,sandbox_root=self.base,policy=replace(self.policy,enabled=False))
        self.assertEqual(self.tick()["state"],"activation_required")
        self.assertFalse(self.root.exists());self.assertFalse(self.analyses)

    def test_catchup_is_latest_due_only_and_not_before_approval(self):
        self.now=datetime(2027,2,1,10,tzinfo=timezone.utc)
        result=self.tick()
        self.assertEqual(result["slot"],"2027-W04")
        self.assertEqual(len(list(self.root.glob('recovery-*.json'))),1)
        before=s.WeeklyScheduler(self.base/"before",sandbox_root=self.base,
            policy=replace(self.policy,not_before="2027-02-02T00:00:00+00:00"))
        self.scheduler=before
        self.assertEqual(self.tick()["state"],"not_due")

    def test_clock_rollback_does_not_create_an_older_job(self):
        self.tick();self.now=datetime(2026,11,2,10,tzinfo=timezone.utc)
        self.assertEqual(self.tick()["state"],"obsolete_clock_slot")
        self.assertEqual(len(self.analyses),1)

    def test_pending_delivery_precedes_new_week_and_skips_unstarted_backlog(self):
        self.cloud_uploaded=False;self.assertEqual(self.tick()["state"],"pending_icloud")
        self.now=datetime(2026,11,23,10,tzinfo=timezone.utc);self.cloud_uploaded=True
        result=self.tick()
        self.assertEqual(result["slot"],"2026-W45");self.assertEqual(len(self.analyses),1)
        self.assertEqual(self.tick()["slot"],"2026-W47")
        self.assertEqual(len(self.analyses),2)
        self.assertFalse((self.root/"recovery-2026-W46.json").exists())

    def test_unknown_analysis_blocks_all_future_weeks_without_retry(self):
        def fail(job):self.analyses.append(job);raise TimeoutError("private error")
        self.assertEqual(self.tick(analyze=fail)["state"],"attention")
        self.now=datetime(2026,11,23,10,tzinfo=timezone.utc)
        self.assertEqual(self.tick()["state"],"attention")
        self.assertEqual(len(self.analyses),1)
        self.assertNotIn("private error",next(self.root.glob('recovery-*.json')).read_text())

    def test_crash_marker_is_before_analysis_and_cannot_resubmit(self):
        def crash(job):self.analyses.append(job);raise SystemExit()
        with self.assertRaises(SystemExit):self.tick(analyze=crash)
        self.assertEqual(json.loads(next(self.root.glob('recovery-*.json')).read_text())["state"],"analysis_in_flight")
        self.assertEqual(self.tick()["reason"],"analysis_outcome_unknown")
        self.assertEqual(len(self.analyses),1)

    def test_known_receipt_reconciliation_does_not_repeat_analysis(self):
        captured=[]
        def crash(job):captured.append(job);raise SystemExit()
        with self.assertRaises(SystemExit):self.tick(analyze=crash)
        job=captured[0]
        result=self.scheduler.reconcile_analysis(job["request_id"],self.result(job),
            confirmed_identity=job["identity_sha256"],confirmed=True)
        self.assertEqual(result["state"],"delivery_ready")
        self.assertEqual(self.tick()["state"],"completed")
        self.assertFalse(self.analyses)

    def test_reconciliation_needs_exact_operator_confirmation(self):
        def fail(job):self.analyses.append(job);raise TimeoutError()
        job=self.tick(analyze=fail)
        with self.assertRaises(ValueError):
            self.scheduler.reconcile_analysis(job["request_id"],self.result(job),confirmed_identity=job["identity_sha256"])
        with self.assertRaises(ValueError):
            self.scheduler.reconcile_analysis(job["request_id"],self.result(job),confirmed_identity="0"*64,confirmed=True)
        self.tick();self.assertEqual(len(self.analyses),1)

    def test_acceptance_is_attached_to_existing_candidate_without_new_analysis(self):
        self.publish=False;job=self.tick()
        self.assertEqual(job["state"],"awaiting_acceptance")
        self.assertEqual(self.tick()["state"],"awaiting_acceptance")
        reference={"request_id":job["request_id"],"approval_sha256":"e"*64}
        self.scheduler.attach_publication(job["request_id"],reference,confirmed_identity=job["identity_sha256"],confirmed=True)
        replay=self.scheduler.attach_publication(job["request_id"],reference,confirmed_identity=job["identity_sha256"])
        self.assertEqual(replay["action"],"replayed_attachment")
        self.assertEqual(self.tick()["state"],"completed");self.assertEqual(len(self.analyses),1)

    def test_unconfirmed_or_different_acceptance_is_refused(self):
        self.publish=False;job=self.tick()
        with self.assertRaises(ValueError):
            self.scheduler.attach_publication(job["request_id"],{"request_id":"other","approval_sha256":"e"*64},
                confirmed_identity=job["identity_sha256"],confirmed=True)
        with self.assertRaises(ValueError):
            self.scheduler.attach_publication(job["request_id"],{},confirmed_identity="0"*64,confirmed=True)
        self.assertEqual(len(self.analyses),1)

    def test_month_and_run_budget_stop_before_analysis(self):
        self.scheduler=s.WeeklyScheduler(self.root,sandbox_root=self.base,policy=replace(self.policy,month_credits=1.5))
        self.tick();self.now=datetime(2026,11,15,10,tzinfo=timezone.utc)
        self.assertEqual(self.tick()["state"],"budget_blocked");self.assertEqual(len(self.analyses),1)
        self.scheduler=s.WeeklyScheduler(self.base/"low",sandbox_root=self.base,policy=replace(self.policy,run_credits=.5))
        self.assertEqual(self.tick()["state"],"budget_blocked");self.assertEqual(len(self.analyses),1)

    def test_actual_known_overrun_is_retained(self):
        def over(job):
            result=self.result(job);result["usage"]={**USAGE,"input_tokens":1_000_000,"total_tokens":1_000_020}
            return result
        result=self.tick(analyze=over)
        self.assertEqual(result["state"],"attention");self.assertGreater(result["credits"],result["reserved_credits"])

    def test_known_overrun_call_count_is_not_erased(self):
        def over(job):
            result=self.result(job);result["reported_model_turns"]=3;return result
        job=self.tick(analyze=over)
        self.assertEqual(job["state"],"attention");self.assertEqual(job["reported_model_turns"],3)

    def test_acceptance_time_limit_stops_before_delivery(self):
        self.scheduler=s.WeeklyScheduler(self.root,sandbox_root=self.base,policy=self.policy,clock=iter([0,61]).__next__)
        result=self.tick()
        self.assertEqual(result["state"],"attention");self.assertFalse(self.deliveries)

    def test_preflight_failure_remains_before_any_analysis(self):
        def fail(_):raise OSError("private path must stay hidden")
        result=self.tick(preflight=fail)
        self.assertEqual(result["state"],"attention");self.assertFalse(self.analyses)
        self.assertNotIn("private path",json.dumps(result))

    def test_result_snapshot_mismatch_cannot_be_delivered(self):
        def wrong(job):
            result=self.result(job);result["snapshot_sha256"]="0"*64;return result
        self.assertEqual(self.tick(analyze=wrong)["state"],"attention");self.assertFalse(self.deliveries)

    def test_unexpected_private_payload_is_not_persisted_but_usage_is_retained(self):
        def raw(job):
            result=self.result(job);result["answer"]="private payload must not persist";return result
        result=self.tick(analyze=raw)
        self.assertEqual(result["state"],"attention");self.assertGreater(result["credits"],0)
        self.assertNotIn("private payload",next(self.root.glob('recovery-*.json')).read_text())

    def test_delivery_attention_is_not_automatically_retried(self):
        def fail(reference):self.deliveries.append(reference);raise OSError("do not expose")
        self.assertEqual(self.tick(deliver=fail)["state"],"attention")
        self.tick();self.assertEqual(len(self.deliveries),1);self.assertEqual(len(self.analyses),1)

    def test_uploaded_label_without_both_copy_proofs_is_not_completion(self):
        def incomplete(reference):
            return {**self.delivery_status(reference),"state":"uploaded","copies":{"local":"baseline","icloud":"candidate"}}
        result=self.tick(deliver=incomplete)
        self.assertEqual(result["state"],"attention")
        self.assertNotIn("delivery",result)

    def test_delivery_crash_at_next_tick_does_not_need_analysis_auth(self):
        def crash(_):raise SystemExit()
        with self.assertRaises(SystemExit):self.tick(deliver=crash)
        self.ready["codex_auth"]=False
        self.assertEqual(self.tick()["state"],"completed");self.assertEqual(len(self.analyses),1)

    def test_incomplete_coverage_model_change_and_invalid_usage_stop_delivery(self):
        for index,change in enumerate((lambda r:r.update(coverage=1),
                lambda r:r["executor"].update(model="gpt-6-luna"),lambda r:r.update(usage=None))):
            self.scheduler=s.WeeklyScheduler(self.base/f"bad-{index}",sandbox_root=self.base,policy=self.policy)
            def bad(job):
                result=self.result(job);result["executor"]=dict(result["executor"]);change(result);return result
            self.assertEqual(self.tick(analyze=bad)["state"],"attention")
        self.assertFalse(self.deliveries)

    def test_no_change_is_complete_only_with_verified_existing_copies(self):
        def unchanged(job):
            result=self.result(job,publication=False);result.update(state="unchanged",candidate_sha256=job["original_sha256"]);return result
        self.assertEqual(self.tick(analyze=unchanged)["state"],"attention")
        self.scheduler=s.WeeklyScheduler(self.base/"unchanged",sandbox_root=self.base,policy=self.policy)
        self.copies_current=True
        proof=lambda job:{"copies_current":True,"candidate_sha256":job["candidate_sha256"],"snapshot_sha256":job["snapshot_sha256"]}
        self.assertEqual(self.tick(analyze=unchanged,verify_unchanged=proof)["state"],"completed_no_change")
        self.assertFalse(self.deliveries)

    def test_no_change_rechecks_copies_after_analysis(self):
        self.copies_current=True
        def unchanged(job):
            result=self.result(job,publication=False);result.update(state="unchanged",candidate_sha256=job["original_sha256"]);return result
        self.assertEqual(self.tick(analyze=unchanged,verify_unchanged=lambda _: {"copies_current":False})["state"],"attention")
        self.assertFalse(self.deliveries)

    def test_no_change_requires_an_independent_final_copy_audit(self):
        self.copies_current=True
        def unchanged(job):
            result=self.result(job,publication=False);result.update(state="unchanged",candidate_sha256=job["original_sha256"]);return result
        self.assertEqual(self.tick(analyze=unchanged)["state"],"attention")

    def test_boolean_counts_do_not_fake_complete_coverage(self):
        def bad(job):
            result=self.result(job);result["coverage"]=True;return result
        self.assertEqual(self.tick(analyze=bad)["state"],"attention");self.assertFalse(self.deliveries)

    def test_unavailable_login_network_auth_or_role_never_starts_analysis(self):
        for key in s.ANALYSIS_READY:
            self.ready[key]=False
            self.assertEqual(self.tick()["state"],"waiting_dependencies")
            self.ready[key]=True
        self.assertFalse(self.analyses)

    def test_pending_delivery_does_not_need_codex_but_needs_cloud(self):
        self.cloud_uploaded=False;self.tick();self.ready["codex_auth"]=False;self.ready["icloud_auth"]=False
        self.assertEqual(self.tick()["action"],"waiting_delivery_dependencies")
        self.ready["icloud_auth"]=True;self.cloud_uploaded=True
        self.assertEqual(self.tick()["state"],"completed");self.assertEqual(len(self.analyses),1)

    def test_readiness_exception_is_a_precondition_wait_not_a_model_retry(self):
        def error():raise OSError("private auth detail")
        self.assertEqual(self.tick(readiness=error)["state"],"waiting_dependencies")
        self.assertFalse(self.analyses)

    def test_policy_change_stops_existing_unfinished_job(self):
        self.cloud_uploaded=False;self.tick()
        self.scheduler=s.WeeklyScheduler(self.root,sandbox_root=self.base,policy=replace(self.policy,run_credits=3))
        self.assertEqual(self.tick()["action"],"policy_changed");self.assertEqual(len(self.deliveries),1)

    def test_busy_lock_and_delivery_crash_do_not_repeat_analysis(self):
        self.root.mkdir(mode=0o700)
        with exclusive_file_lock(self.root/"scheduler"):
            self.assertEqual(self.tick()["state"],"busy")
        def crash(_):raise SystemExit()
        with self.assertRaises(SystemExit):self.tick(deliver=crash)
        self.assertEqual(self.tick()["state"],"completed");self.assertEqual(len(self.analyses),1)

    def test_delivery_binding_and_manual_attention_block_next_week(self):
        def wrong(reference):return {**self.delivery_status(reference),"candidate_sha256":"0"*64}
        result=self.tick(delivery_status=wrong)
        self.assertEqual(result["state"],"attention");self.assertFalse(self.deliveries)
        self.now=datetime(2026,11,23,tzinfo=timezone.utc);self.tick()
        self.assertEqual(len(self.analyses),1)

    def test_status_is_read_only_and_reports_counts_cost_and_copy_state(self):
        self.assertEqual(s.inspect_status(self.root)["state"],"not_configured");self.assertFalse(self.root.exists())
        self.tick();status=s.inspect_status(self.root)
        self.assertEqual(status["last_run"]["source_count"],2)
        self.assertEqual(status["last_run"]["coverage"],2)
        self.assertEqual(status["last_run"]["delivery"]["state"],"uploaded")
        self.assertEqual(status["last_run"]["executor"]["model"],s.MODEL)

    def test_corrupt_local_job_does_not_create_another_analysis(self):
        self.tick();path=next(self.root.glob('recovery-*.json'));path.write_text('{bad json')
        self.assertEqual(self.tick()["state"],"attention");self.assertEqual(len(self.analyses),1)

    def test_scope_policy_and_private_permissions_are_enforced(self):
        with self.assertRaises(ValueError):s.WeeklyScheduler(self.root,sandbox_root=self.base,policy=self.policy,mode="production")
        with self.assertRaises(ValueError):s.WeeklyScheduler(self.root,sandbox_root=self.base,policy=replace(self.policy,schedule_approved=False))
        self.tick();self.root.chmod(0o755)
        with self.assertRaises(ValueError):self.tick()
        self.root.chmod(0o700)

    def test_state_alias_cannot_redirect_scheduler(self):
        outside=self.base/"elsewhere";outside.mkdir();self.root.symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):self.tick()
        self.assertEqual(list(outside.iterdir()),[])


class ClockAndLaunchd(unittest.TestCase):
    def test_dst_forward_back_and_year_boundary_use_one_prague_slot(self):
        policy=s.SchedulerPolicy()
        self.assertEqual(s.due_slot(datetime(2026,10,25,8,tzinfo=s.ZONE),policy)[0],"2026-W42")
        self.assertEqual(s.due_slot(datetime(2026,10,25,9,tzinfo=s.ZONE),policy)[0],"2026-W43")
        self.assertEqual(s.due_slot(datetime(2027,1,1,tzinfo=s.ZONE),policy)[0],"2026-W52")
        early=s.due_slot(datetime(2026,10,25,2,30,tzinfo=s.ZONE,fold=0),replace(policy,hour=2))
        late=s.due_slot(datetime(2026,10,25,2,30,tzinfo=s.ZONE,fold=1),replace(policy,hour=2))
        self.assertEqual(early,late)
        spring=s.due_slot(datetime(2026,3,29,3,0,tzinfo=s.ZONE),replace(policy,hour=2))
        self.assertEqual(spring[1].astimezone(s.ZONE).hour,3)

    def test_prepared_agent_has_absolute_paths_private_umask_and_no_keepalive(self):
        project=Path(__file__).resolve().parents[1];spec=launch_agent(project)
        self.assertEqual(spec["Umask"],0o077)
        self.assertNotIn("KeepAlive",spec)
        self.assertEqual(spec["StartInterval"],900)
        self.assertEqual(spec["ProgramArguments"][-1],"tick")

    def test_cli_bootstrap_under_minimal_service_path_is_read_only(self):
        result=check_environment(Path(__file__).resolve().parents[1])
        self.assertTrue(result["minimal_path_tested"])
        self.assertFalse(result["launchd_session_verified"])
        self.assertFalse(result["service_installed"])
        self.assertEqual(result["model_calls"],0)

    def test_schedule_preview_never_enables_proposed_sunday_time(self):
        result=s.schedule_preview(datetime(2026,11,7,tzinfo=s.ZONE))
        self.assertFalse(result["approved"]);self.assertFalse(result["enabled"]);self.assertFalse(result["writes"])


class DeliveryIntegration(unittest.TestCase):
    def test_scheduler_uses_accepted_writer_and_resumes_only_existing_bytes(self):
        case=publication_fixtures.Publication();case.setUp();self.addCleanup(case.doCleanups)
        now=datetime(2026,11,8,10,tzinfo=s.ZONE)
        case.context=replace(case.context,checked_on=now.date())
        policy=s.SchedulerPolicy(True,True,True,not_before="2026-11-01T00:00:00+00:00",role_policy_digest="a"*64,
                                run_credits=2,month_credits=10,max_calls=2,max_seconds=60)
        scheduler=s.WeeklyScheduler(case.root/"scheduler",sandbox_root=case.root,policy=policy)
        reads=[];uploaded=False
        def preflight(_):return {"snapshot_sha256":case.snapshot.sha256,"original_sha256":case.snapshot.original.sha256,
                                "source_count":len(case.snapshot.sources),"planned_calls":2,"reserved_credits":1,"copies_current":False}
        def analyze(job):
            reads.append(job)
            draft=case.store.prepare(case.answer,case.snapshot,case.dossier,case.context)
            receipt=case.store.accept(draft,request_id=job["request_id"],confirmed_binding=draft.sha256,confirmed=True,now=now)
            return {"state":"review","request_id":job["request_id"],"slot":job["slot"],"snapshot_sha256":case.snapshot.sha256,
                    "source_count":len(case.snapshot.sources),"coverage":len(case.snapshot.sources),"candidate_sha256":receipt["candidate_sha256"],
                    "executor":job["executor"],"usage":USAGE,"reported_model_turns":2,"simulation":True,
                    "publication":{"request_id":job["request_id"],"approval_sha256":receipt["approval_sha256"]}}
        status=lambda ref:case.store.status(ref["request_id"])
        deliver=lambda ref:case.store.execute(ref["request_id"],approval_sha256=ref["approval_sha256"],current_inputs=lambda _:True,
                                              cloud_audit=lambda _:{**CLOUD,"uploaded":uploaded},now=now)
        params=dict(readiness=lambda:{k:True for k in s.ANALYSIS_READY},preflight=preflight,analyze=analyze,delivery_status=status,deliver=deliver)
        self.assertEqual(scheduler.tick(now,**params)["state"],"pending_icloud")
        before=(case.local.stat().st_mtime_ns,case.cloud.stat().st_mtime_ns);uploaded=True
        self.assertEqual(scheduler.tick(now,**params)["state"],"completed")
        self.assertEqual(len(reads),1)
        self.assertEqual(before,(case.local.stat().st_mtime_ns,case.cloud.stat().st_mtime_ns))
        self.assertEqual(case.local.read_bytes(),case.cloud.read_bytes())


if __name__=="__main__":unittest.main()
