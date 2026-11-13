from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
import urllib.error
import urllib.request

from app.agent_supervisor import AgentSupervisor, evaluate, email_row, LABELS
from app.agent_supervisor_probes import collect
from app.agent_supervisor_service import SupervisorService, CONFIRMATION, SOURCES
from app.cockpit_agent_supervisor import agent_supervisor_overview
from app.work_repository import WorkRepositoryError, RepositoryMutation

NOW = datetime(2026, 11, 13, 8, 30, tzinfo=timezone.utc)
FAILURE = "https://api.pushcut.io/secret-failure/notifications/SupervisorFailure"
RECOVERY = "https://api.pushcut.io/secret-recovery/notifications/SupervisorRecovery"


def evidence(now=NOW):
    at = now.isoformat()
    return {"email": {"enabled": True, "installed": True, "owned": True, "loaded": True,
        "health": {"status": "already_completed", "finished_at": at, "started_at": at},
        "sources": [{"health": "ok", "error": "", "uidvalidity": "1", "followup_scan": {
            "status": "complete", "as_of": now.replace(minute=0).isoformat(),
            "verified_at": at, "uidvalidity": "1"}}]},
        "cockpit": {"reachable": True}, "appserver": {"reachable": True},
        "autosave": {"watcher_count": 1, "latest_modified_at": at, "last_error": False},
        "storage": {"free_gib": 40}}


class EvaluationTests(unittest.TestCase):
    def test_healthy_scan_and_all_registered_probes(self):
        rows = evaluate(evidence(), NOW)
        self.assertEqual({v["id"] for v in rows}, set(LABELS))
        self.assertEqual({v["state"] for v in rows}, {"ok"})

    def test_loaded_or_configured_flag_does_not_prove_worker(self):
        value = evidence()["email"]
        value["health"]["finished_at"] = (NOW-timedelta(minutes=6)).isoformat()
        self.assertEqual(email_row(value, NOW)["code"], "heartbeat_missing")
        value["enabled"] = False
        self.assertEqual(email_row(value, NOW)["state"], "disabled")

    def test_completed_slot_is_not_complete_source_evidence(self):
        value = evidence()["email"]
        value["schedule"] = {"status": "completed", "completed_slot": NOW.isoformat()}
        value["sources"][0]["followup_scan"]["as_of"] = (NOW-timedelta(hours=1)).isoformat()
        self.assertEqual(email_row(value, NOW)["code"], "scan_missing")

    def test_each_configured_source_needs_complete_same_epoch_scan(self):
        for key, change in (("status", "incomplete"), ("uidvalidity", "2"),
                            ("verified_at", (NOW+timedelta(seconds=1)).isoformat())):
            with self.subTest(key=key):
                value = evidence()["email"]
                value["sources"].append(copy.deepcopy(value["sources"][0]))
                value["sources"][1]["followup_scan"][key] = change
                self.assertEqual(email_row(value, NOW)["code"], "scan_missing")

    def test_grace_period_and_night_are_not_a_missed_hour(self):
        early = NOW.replace(minute=3)
        value = evidence(early)["email"]
        value["sources"][0]["followup_scan"]["as_of"] = (early-timedelta(hours=1)).isoformat()
        self.assertEqual(email_row(value, early)["code"], "scan_due")
        night = NOW.replace(hour=23)
        value["health"]["finished_at"] = night.isoformat()
        self.assertEqual(email_row(value, night)["state"], "outside_hours")
        self.assertIn("07:00", email_row(value, night)["next_due_at"])

    def test_verified_long_work_is_not_misreported_as_dead(self):
        value = evidence()["email"]
        value["health"] = {"status": "running", "started_at": (NOW-timedelta(minutes=25)).isoformat()}
        value["worker_running"] = True
        self.assertEqual(email_row(value, NOW)["state"], "working")
        value["health"]["started_at"] = (NOW-timedelta(minutes=46)).isoformat()
        self.assertEqual(email_row(value, NOW)["code"], "working_long")
        value["worker_running"] = False
        self.assertNotEqual(email_row(value, NOW)["state"], "working")

    def test_future_clock_worker_error_and_source_error_stay_unverified(self):
        value = evidence()["email"]
        value["health"]["finished_at"] = (NOW+timedelta(seconds=1)).isoformat()
        self.assertEqual(email_row(value, NOW)["code"], "clock_invalid")
        value = evidence()["email"]; value["health"]["status"] = "failed"
        self.assertEqual(email_row(value, NOW)["code"], "worker_failed")
        value = evidence()["email"]; value["sources"][0]["error"] = "PRIVATE ERROR"
        self.assertEqual(email_row(value, NOW)["code"], "source_error")

    def test_autosave_missing_old_future_and_disk_thresholds(self):
        for change, expected in (({"watcher_count": 0}, "autosave_missing"),
                ({"watcher_count": 2}, "autosave_missing"),
                ({"last_error": True}, "autosave_failed"),
                ({"latest_modified_at": (NOW-timedelta(minutes=21)).isoformat()}, "autosave_old"),
                ({"latest_modified_at": (NOW+timedelta(seconds=1)).isoformat()}, "clock_invalid")):
            value = evidence();value["autosave"].update(change)
            self.assertEqual(next(v for v in evaluate(value,NOW) if v["id"]=="autosave")["code"], expected)
        for free, expected in ((14,"error"),(29,"warning"),(30,"ok"),(None,"unknown"),(float("nan"),"unknown")):
            value=evidence();value["storage"]["free_gib"]=free
            self.assertEqual(evaluate(value,NOW)[-1]["state"],expected)

    def test_probe_failure_is_scoped_and_exception_text_is_discarded(self):
        probes = {key: (lambda key=key:evidence()[key]) for key in LABELS}
        probes["email"] = Mock(side_effect=RuntimeError("PRIVATE TOKEN"))
        value=collect(probes=probes)
        self.assertNotIn("PRIVATE",json.dumps(value))
        rows=evaluate(value,NOW)
        self.assertEqual(rows[0]["state"],"unknown")
        self.assertEqual(rows[1]["state"],"ok")


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)/"supervisor";self.value=evidence();self.sent=[]
        self.service=AgentSupervisor(self.root,collector=lambda:copy.deepcopy(self.value),
            clock=lambda:NOW,sender=lambda url:self.sent.append(url) or {"status":"accepted"})

    def enable(self, notifications=True):
        return self.service.configure(enabled=True, notifications_enabled=notifications,
            failure_url=FAILURE if notifications else "", recovery_url=RECOVERY if notifications else "",confirmed=True)

    def test_status_and_disabled_tick_never_initialize_probe_or_write(self):
        self.service.collector=Mock(side_effect=AssertionError("probe"))
        self.assertFalse(self.service.status()["configured"])
        self.assertEqual(self.service.check(scheduled=True)["status"],"disabled")
        self.assertFalse(self.root.exists())
        self.service.collector.assert_not_called()

    def test_manual_check_is_explicit_redacted_and_never_sends(self):
        self.value["email"]["body"]="PRIVATE FULL MAIL"
        with self.assertRaises(ValueError):self.service.check()
        self.enable();self.value["cockpit"]["reachable"]=False
        result=self.service.check(confirmed=True)
        self.assertTrue(result["snapshot_recent"])
        self.assertFalse(result["worker_recent"])
        self.assertEqual(self.sent,[])
        self.assertNotIn("PRIVATE",self.service.repository.path.read_text())
        self.assertEqual(self.service.repository.read()["incidents"],{})

    def test_incident_and_recovery_sent_once_across_instances(self):
        self.enable();self.value["cockpit"]["reachable"]=False
        self.service.check(scheduled=True);self.service.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE])
        restarted=AgentSupervisor(self.root,collector=lambda:self.value,clock=lambda:NOW,sender=self.service.sender)
        restarted.check(scheduled=True)
        self.value["cockpit"]["reachable"]=True
        restarted.check(scheduled=True);restarted.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE,RECOVERY])
        self.value["cockpit"]["reachable"]=False
        restarted.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE,RECOVERY,FAILURE])

    def test_multiple_failed_agents_are_one_notification_per_sampling_batch(self):
        self.enable()
        self.value["cockpit"]["reachable"]=False;self.value["appserver"]["reachable"]=False
        result=self.service.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE])
        self.assertEqual(result["notification_counts"]["accepted"],1)
        self.value=evidence();self.service.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE,RECOVERY])

    def test_starting_worker_does_not_report_recovery_before_scan_completion(self):
        self.enable()
        scan=self.value["email"]["sources"][0]["followup_scan"]
        scan["as_of"]=(NOW-timedelta(hours=1)).isoformat()
        self.service.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE])
        healthy=copy.deepcopy(self.value["email"]["health"])
        self.value["email"].update(worker_running=True,health={"status":"running","started_at":NOW.isoformat()})
        self.service.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE])
        self.value["email"]["health"]=healthy
        self.service.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE])
        scan["as_of"]=NOW.replace(minute=0).isoformat()
        self.service.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE,RECOVERY])

    def test_unsent_failure_waits_through_working_state_without_being_lost(self):
        self.enable()
        self.value["email"]["sources"][0]["followup_scan"]["status"]="incomplete"
        with patch.object(self.service,"_dispatch"):self.service.check(scheduled=True)
        healthy=copy.deepcopy(self.value["email"]["health"])
        self.value["email"].update(worker_running=True,health={"status":"running","started_at":NOW.isoformat()})
        self.service.check(scheduled=True)
        self.assertEqual(self.sent,[])
        self.value["email"]["health"]=healthy
        self.service.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE])

    def test_uncertain_send_and_crashed_sending_are_never_replayed(self):
        self.enable();self.value["cockpit"]["reachable"]=False
        self.service.sender=lambda url:self.sent.append(url) or {"status":"delivery_unknown"}
        self.service.check(scheduled=True);self.service.check(scheduled=True)
        self.assertEqual(len(self.sent),1)
        def crash(document):
            for event in document["events"].values():event["status"]="sending"
            return RepositoryMutation(document)
        self.service.repository.transact(crash)
        result=self.service.check(scheduled=True)
        self.assertEqual(result["notification_counts"]["delivery_unknown"],1)
        self.assertEqual(len(self.sent),1)
        self.value["cockpit"]["reachable"]=True;self.service.check(scheduled=True)
        self.assertEqual(len(self.sent),1)

    def test_unsent_failure_is_superseded_when_agent_recovers_before_dispatch(self):
        self.enable();self.value["cockpit"]["reachable"]=False
        with patch.object(self.service,"_dispatch"):
            self.service.check(scheduled=True)
        self.value["cockpit"]["reachable"]=True
        result=self.service.check(scheduled=True)
        self.assertEqual(self.sent,[])
        self.assertEqual(result["notification_counts"]["superseded"],1)

    def test_unsent_recovery_cannot_claim_a_new_failed_episode_is_healthy(self):
        self.enable();self.value["cockpit"]["reachable"]=False;self.service.check(scheduled=True)
        self.value["cockpit"]["reachable"]=True
        with patch.object(self.service,"_dispatch"):
            self.service.check(scheduled=True)
        self.value["cockpit"]["reachable"]=False
        result=self.service.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE,FAILURE])
        self.assertEqual(result["notification_counts"]["superseded"],1)

    def test_failed_post_completion_write_does_not_resend(self):
        self.enable();self.value["cockpit"]["reachable"]=False
        original=self.service.repository.transact;calls=[]
        def fail_finish(updater,**kwargs):
            calls.append(1)
            if len(calls)==3:raise OSError("disk full after send")
            return original(updater,**kwargs)
        with patch.object(self.service.repository,"transact",side_effect=fail_finish):
            with self.assertRaises(OSError):self.service.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE])
        self.service.check(scheduled=True)
        self.assertEqual(self.sent,[FAILURE])

    def test_stale_snapshot_is_unknown_without_changing_persistence(self):
        self.service.check(confirmed=True)
        before=self.service.repository.path.read_bytes()
        self.service.clock=lambda:NOW+timedelta(minutes=6)
        result=self.service.status()
        self.assertFalse(result["snapshot_recent"])
        self.assertEqual({v["code"] for v in result["rows"]},{"snapshot_stale"})
        self.assertEqual(self.service.repository.path.read_bytes(),before)

    def test_two_workers_are_serialized_and_do_not_double_send(self):
        self.enable();self.value["cockpit"]["reachable"]=False
        entered=threading.Event();release=threading.Event()
        def blocked():entered.set();release.wait(3);return self.value
        self.service.collector=blocked
        thread=threading.Thread(target=lambda:self.service.check(scheduled=True));thread.start()
        try:
            self.assertTrue(entered.wait(2))
            second=AgentSupervisor(self.root,collector=Mock(side_effect=AssertionError("duplicate")),clock=lambda:NOW)
            self.assertEqual(second.check(scheduled=True)["status"],"busy")
        finally:release.set();thread.join(4)
        self.assertEqual(self.sent,[FAILURE])

    def test_secrets_never_appear_in_status_and_injected_snapshot_fields_are_removed(self):
        self.enable();self.service.check(scheduled=True)
        def inject(document):
            document["rows"][0]["private"]="PRIVATE MAIL"
            document["rows"][0]["message"]="SECRET TOKEN"
            return RepositoryMutation(document)
        self.service.repository.transact(inject)
        result=json.dumps(self.service.status())
        for secret in ("secret-failure","secret-recovery","PRIVATE MAIL","SECRET TOKEN"):
            self.assertNotIn(secret,result)

    def test_corrupt_store_is_not_reinitialized_as_healthy(self):
        self.root.mkdir();self.service.repository.path.write_text("not json")
        self.assertFalse(agent_supervisor_overview(service=self.service)["ok"])
        self.assertEqual(self.service.repository.path.read_text(),"not json")

    def test_configuration_requires_confirmation_valid_hooks_and_never_sends(self):
        for kwargs in ({"enabled":True}, {"enabled":True,"confirmed":True,"failure_url":None},
                {"enabled":True,"confirmed":True,"notifications_enabled":True,"failure_url":FAILURE,"recovery_url":FAILURE}):
            with self.assertRaises(ValueError):self.service.configure(**kwargs)
        self.assertFalse(self.root.exists());self.enable()
        self.assertEqual(self.sent,[])


class ServiceTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.project=Path(temp.name)/"project";self.root=Path(temp.name)/"state"
        self.agents=Path(temp.name)/"agents"
        for name in SOURCES+(".venv/bin/python",):
            target=self.project/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text("fixture")
        self.commands=[]
        def runner(argv,**kwargs):
            self.commands.append(argv);return subprocess.CompletedProcess(argv,0,"","")
        self.control=SupervisorService(project=self.project,root=self.root,agents=self.agents,runner=runner)

    def test_preview_has_no_system_writes_and_activation_requires_exact_digest(self):
        plan=self.control.preview();self.assertFalse(self.agents.exists());self.assertFalse(self.root.exists())
        with self.assertRaises(ValueError):self.control.install(approved_digest=plan["digest"],confirmation="ano")
        (self.project/SOURCES[0]).write_text("changed")
        with self.assertRaises(ValueError):self.control.install(approved_digest=plan["digest"],confirmation=CONFIRMATION)
        self.assertEqual(self.commands,[])

    def test_install_only_owns_its_agent_and_does_not_enable_notifications(self):
        result=self.control.install(approved_digest=self.control.preview()["digest"],confirmation=CONFIRMATION)
        self.assertTrue(result["ok"]);self.assertFalse(result["notifications_enabled"])
        self.assertTrue(AgentSupervisor(self.root).config()["enabled"])
        before=len(self.commands)
        second=self.control.install(approved_digest=self.control.preview()["digest"],confirmation=CONFIRMATION)
        self.assertEqual(second["status"],"existing_receipt")
        self.assertFalse(any("bootstrap" in cmd for cmd in self.commands[before:]))

    def test_uncertain_bootstrap_is_not_repeated_and_foreign_plist_is_preserved(self):
        self.control.runner=Mock(side_effect=TimeoutError("unknown"))
        result=self.control.install(approved_digest=self.control.preview()["digest"],confirmation=CONFIRMATION)
        self.assertEqual(result["status"],"uncertain")
        self.assertFalse(AgentSupervisor(self.root).config()["enabled"])
        self.control.runner=Mock(return_value=subprocess.CompletedProcess([],0,"",""))
        self.control.install(approved_digest=self.control.preview()["digest"],confirmation=CONFIRMATION)
        self.assertFalse(any("bootstrap" in call.args[0] for call in self.control.runner.call_args_list))

    def test_foreign_definition_cannot_be_overwritten(self):
        self.agents.mkdir();self.control.target.write_text("FOREIGN")
        with self.assertRaises(ValueError):self.control.install(approved_digest=self.control.preview()["digest"],confirmation=CONFIRMATION)
        self.assertEqual(self.control.target.read_text(),"FOREIGN")


class HttpTests(unittest.TestCase):
    def test_status_get_is_read_only_and_query_is_rejected(self):
        import app.cockpit as cockpit
        sentinel={"ok":True,"rows":[],"configured":False}
        with patch.object(cockpit,"agent_supervisor_overview",return_value=sentinel) as read:
            server=ThreadingHTTPServer(("127.0.0.1",0),cockpit.CockpitServer().make_handler())
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                url=f"http://127.0.0.1:{server.server_port}/api/agent-supervisor/status"
                with urllib.request.urlopen(url,timeout=5) as response:self.assertEqual(json.load(response),sentinel)
                with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(url+"?check=1",timeout=5)
                self.assertEqual(error.exception.code,400);self.assertEqual(read.call_count,1)
            finally:server.shutdown();server.server_close();thread.join(3)

    def test_frontend_executes_safe_rendering_and_clears_stale_green_on_failure(self):
        from scripts.cockpit_quality_gate import node_binary
        result=subprocess.run([node_binary(),str(Path(__file__).with_name("agent_supervisor_frontend.test.cjs"))],
            capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=="__main__":unittest.main()
