from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.communication.human_adam_work_state import build_human_adam_work_state
from app.communication.human_adam_job_progress import build_server_job_progress
from app.communication.human_adam_work import operation_id

SCOPE = "layer-human-adam-development"
AT = "2026-11-12T09:00:00+00:00"
BEFORE = "2026-11-12T08:00:00+00:00"
AFTER = "2026-11-12T08:30:00+00:00"
HEAD = "a" * 40


class ServerJobProgressTests(unittest.TestCase):
    def setUp(self):
        self.parent={'operation_id':operation_id(SCOPE,'request-current'),'client_request_id':'request-current',
            'thread_id':'thread-current','profile_id':'human_adam'}
        self.record={**self.parent,'scope':{'workstream_id':SCOPE,'thread_id':'thread-current','profile_id':'human_adam'},
            'delivery_state':'confirmed','created_at':BEFORE,'updated_at':AFTER,'completion':{},
            '_accepted_input':'PRIVATE_TEXT'}
        self.job={'workstream_id':SCOPE,'profile_id':'human_adam','client_message_id':'request-current',
            'idempotency_key':'b'*64,'state':'running','created_at':AFTER,'updated_at':AT,'checkpoint_head':'',
            'visible_answer':'PRIVATE_TEXT'}
        self.release={'workstream_id':SCOPE,'job_id':'c'*32,'parent_work':self.parent,
            'parent_thread_id':'thread-current','target_head':HEAD,'expected_code_stamp':'d'*16,
            'state':'running','phase':'verification','created_at':AFTER,'updated_at':AT,
            'deployment_target':'cockpit','return_channel':'cockpit','dry_run':False,
            'push_state':'confirmed','deployment_state':'requested','token':'PRIVATE_TEXT','verification':{}}

    def build(self,**changes):
        return build_server_job_progress(**({'workstream_id':SCOPE,'thread_id':'thread-current',
            'latest_client_id':'request-current','observed_at':AT,'latest_received_at':BEFORE,
            'records':[self.record]}|changes))

    def test_model_result_can_be_confirmed_while_checkpoint_is_still_active(self):
        result=self.build(completion_job=self.job)
        self.assertEqual(result['current_job_id'],self.job['idempotency_key'])
        self.assertEqual(result['jobs'][0]['phase'],'checkpoint_validation')
        self.assertEqual(result['jobs'][0]['outcome'],'unverified')
        self.assertEqual(result['jobs'][0]['parent'],self.parent)
        self.assertNotIn('PRIVATE_TEXT',json.dumps(result))
        self.assertEqual(result['actions'],{'retry':False,'publish':False,'recover':False})

    def test_old_foreign_thread_profile_or_uncertain_parent_cannot_be_current(self):
        for changes in ({'thread_id':'new-thread'},{'latest_client_id':'new-request'},
                        {'records':[{**self.record,'delivery_state':'unknown'}]},
                        {'completion_job':{**self.job,'profile_id':'knihovna'}},
                        {'completion_job':{**self.job,'workstream_id':'project-foreign'}}):
            with self.subTest(changes=changes):
                result=self.build(**({'completion_job':self.job}|changes))
                self.assertIsNone(result['current_job_id'])

    def test_stored_terminal_checkpoint_reference_survives_next_global_job(self):
        self.record['completion']={'kind':'completion','job_id':'b'*64,'state':'completed'}
        result=self.build(completion_job={**self.job,'workstream_id':'project-foreign'})
        self.assertEqual(result['jobs'][0]['outcome'],'completion_confirmed')
        self.assertIsNone(result['current_job_id'])

    def test_release_has_exact_parent_and_actual_target(self):
        for target in ('cockpit','github_pages'):
            result=self.build(releases=[{**self.release,'deployment_target':target}])
            self.assertEqual(result['current_job_id'],self.release['job_id'])
            self.assertEqual(result['jobs'][0]['deployment_target'],target)
            self.assertEqual(result['jobs'][0]['parent'],self.parent)
            self.assertNotIn('PRIVATE_TEXT',json.dumps(result))

    def test_executor_usage_belongs_only_to_the_exact_release_and_unknown_is_not_zero(self):
        usage={'input_tokens':10,'cached_input_tokens':2,'output_tokens':5,'reasoning_output_tokens':1,'total_tokens':15}
        result=self.build(releases=[self.release|{'luna_proof':{'token_usage':usage,'private':'PRIVATE_TEXT'}}])
        self.assertEqual(result['jobs'][0]['executor_usage'],usage)
        self.assertNotIn('PRIVATE_TEXT',json.dumps(result))
        self.assertIsNone(self.build(releases=[self.release])['jobs'][0]['executor_usage'])
        self.assertIsNone(self.build(releases=[self.release|{'luna_proof':{'token_usage':usage|{'total_tokens':99}}}])['jobs'][0]['executor_usage'])

    def test_foreign_release_and_same_project_different_parent_are_not_current(self):
        result=self.build(releases=[{**self.release,'workstream_id':'project-foreign'}])
        self.assertEqual(result['jobs'],[])
        for binding in ({**self.parent,'thread_id':'old-thread'},{**self.parent,'operation_id':'e'*32}):
            result=self.build(releases=[{**self.release,'parent_work':binding}])
            self.assertIsNone(result['current_job_id'])
            self.assertIsNone(result['jobs'][0]['parent'])

    def test_terminal_release_is_separate_and_never_overrides_new_model_work(self):
        release={**self.release,'return_channel':'caller','parent_work':None}
        result=self.build(releases=[release])
        self.assertEqual(result['current_job_id'],release['job_id'])
        self.assertIsNone(result['jobs'][0]['parent'])
        self.assertIsNone(self.build(releases=[release],model_running=True)['current_job_id'])
        self.assertIsNone(self.build(releases=[release],latest_received_at=AT)['current_job_id'])

    def test_later_deployment_proof_does_not_rewrite_or_repeat_attention_release(self):
        self.release.update(state='attention',phase='done',deployment_state='uncertain')
        original=copy.deepcopy(self.release)
        proof={'state':'deployed','workstream_id':SCOPE,'main_head':HEAD,'expected_code_stamp':'d'*16,
            'smoke_count':5,'deployed_at':AT}
        result=self.build(releases=[self.release],deployment=proof)
        row=result['jobs'][0]
        self.assertEqual(row['state'],'attention')
        self.assertTrue(row['later_verified'])
        self.assertEqual(row['outcome'],'deployment_verified')
        self.assertEqual(row['deployment_state'],'uncertain')
        self.assertEqual(original,self.release)
        self.assertIsNone(result['current_job_id'])
        for changes in ({'main_head':'e'*40},{'expected_code_stamp':'e'*16},{'smoke_count':4},
                        {'workstream_id':'project-foreign'},{'deployed_at':BEFORE}):
            self.assertEqual(self.build(releases=[self.release],deployment=proof|changes)['jobs'][0]['outcome'],'unverified')
        self.assertEqual(self.build(releases=[self.release|{'dry_run':True}],deployment=proof)['jobs'][0]['outcome'],'unverified')

    def test_own_exact_pages_receipt_confirms_pages_but_not_cockpit(self):
        self.release.update(deployment_target='github_pages',state='completed',phase='done',
            verification={'state':'deployed','main_head':HEAD,'deployment_target':'github_pages',
                          'deployment_id':123,'smoke_http_status':200})
        self.assertEqual(self.build(releases=[self.release])['jobs'][0]['outcome'],'deployment_verified')
        self.release['deployment_target']='cockpit'
        self.assertEqual(self.build(releases=[self.release])['jobs'][0]['outcome'],'unverified')

    def test_missing_source_changed_snapshot_and_future_receipt_never_grant_current_work(self):
        for changes in ({'consistent':False},{'source_errors':('publication',)},
                        {'releases':[self.release|{'updated_at':'2030-01-01T00:00:00Z'}]}):
            self.assertIsNone(self.build(**({'releases':[self.release]}|changes))['current_job_id'])

    def test_missing_checkpoint_head_is_attention_and_never_claims_saved_code(self):
        result=self.build(completion_job=self.job|{'state':'completed','checkpoint_head':''})
        self.assertEqual(result['jobs'][0]['phase'],'attention')
        self.assertEqual(result['jobs'][0]['outcome'],'unverified')
        self.assertEqual(result['current_job_id'],self.job['idempotency_key'])

    def test_unknown_release_phase_is_unavailable_rather_than_completed(self):
        result=self.build(releases=[self.release|{'phase':'unknown-private-phase'}])
        self.assertFalse(result['consistent'])
        self.assertTrue(result['source_unavailable'])
        self.assertIsNone(result['current_job_id'])

    def test_successful_later_release_keeps_earlier_attention_only_in_history(self):
        old=self.release|{'state':'attention','phase':'done','return_channel':'caller','parent_work':None}
        new=self.release|{'job_id':'f'*32,'state':'completed','phase':'done','created_at':'2026-11-12T08:45:00Z',
            'return_channel':'caller','parent_work':None,'verification':{'state':'deployed','main_head':HEAD,
                'deployment_target':'cockpit','code_stamp':'d'*16,'smoke_count':5}}
        result=self.build(releases=[old,new])
        self.assertIsNone(result['current_job_id'])
        self.assertEqual(result['jobs'][0]['outcome'],'deployment_verified')
        self.assertEqual(result['jobs'][1]['state'],'attention')


def message(**changes):
    return dict(client_message_id="request-current", thread_id="thread-current",
                received_at=BEFORE, completed_at=AFTER, status="completed",
                delivery_confirmed=True, user_text="PRIVATE_TEXT", answer="PRIVATE_TEXT") | changes


def session(**changes):
    return dict(thread_id="thread-current", connected=True, turn_busy=False,
                updated_at=AFTER, messages=[message()], active_turn=None) | changes


def completion(**changes):
    return dict(schema_version=1, server_authoritative=True, workstream_id=SCOPE,
                client_message_id="request-current", state="checkpoint_completed",
                updated_at=AFTER, summary="PRIVATE_TEXT") | changes


def release(**changes):
    return dict(workstream_id=SCOPE, job_id="release-current", state="completed",
                active=False, created_at=AFTER, updated_at=AT,
                deployment_target="github_pages", target_short=HEAD[:12], dry_run=False,
                message="PRIVATE_TEXT", token="PRIVATE_TEXT", verification={}) | changes


def build(**changes):
    return build_human_adam_work_state(**(dict(
        workstream_id=SCOPE, observed_at=AT, session_snapshot=session(),
        runtime_snapshot={"reachable": True},
    ) | changes))


class WorkStateTests(unittest.TestCase):
    def test_interrupted_history_requires_terminal_proof(self):
        for confirmed in (False,True):
            with self.subTest(confirmed=confirmed):
                result=build(session_snapshot=session(messages=[message(status="interrupted",delivery_confirmed=False,
                    terminal_confirmed=confirmed,turn_id="turn-current")]))
                self.assertEqual(result["history"][0]["state"],"interrupted" if confirmed else "unverified")
                self.assertEqual(result["summary"]["state"],"ready" if confirmed else "unverified")

    def test_idle_connected_is_ready_and_does_not_grant_mutations(self):
        result = build()
        self.assertEqual(result["summary"]["state"], "ready")
        self.assertEqual(result["actions"], {"refresh_status": True, "inspect_work": True,
                                           "steer": False, "interrupt": False})
        self.assertEqual(result["model"]["state"], "idle")
        self.assertNotIn("PRIVATE_TEXT", json.dumps(result))

    def test_running_model_has_priority_over_old_attention_and_completion(self):
        result = build(session_snapshot=session(turn_busy=True, active_turn={"client_message_id": "request-current", "started_at": BEFORE},
            messages=[message(status="pending", delivery_confirmed=False)]),
            completion_snapshot=completion(client_message_id="request-old"),
            release_snapshot=release(state="attention"))
        self.assertEqual(result["summary"]["state"], "running")
        self.assertEqual(result["publication"]["state"], "recorded")
        self.assertTrue(any(i["code"] == "receipt_attention" for i in result["incidents"]))
        self.assertEqual(result["summary"]["operation_id"], result["model"]["operation"]["operation_id"])

    def test_wrong_active_request_is_unverified(self):
        result = build(session_snapshot=session(turn_busy=True, active_turn={"client_message_id": "wrong"}))
        self.assertEqual(result["summary"]["state"], "unverified")
        self.assertIsNone(result["model"]["operation"])

    def test_latest_message_from_other_thread_does_not_replace_current_one(self):
        result = build(session_snapshot=session(messages=[message(), message(thread_id="another", status="delivery_unknown")]))
        self.assertEqual(result["summary"]["state"], "ready")

    def test_unknown_delivery_survives_disconnection_without_becoming_running(self):
        result = build(session_snapshot=session(connected=False, messages=[message(status="delivery_unknown", delivery_confirmed=False)]))
        self.assertEqual(result["connection"]["state"], "disconnected")
        self.assertEqual(result["summary"]["state"], "unverified")

    def test_old_unknown_delivery_is_history_after_new_completed_request(self):
        result = build(session_snapshot=session(messages=[message(client_message_id="old", status="delivery_unknown"), message()]))
        self.assertEqual(result["summary"]["state"], "ready")

    def test_completion_waits_for_confirmed_model_result_and_same_request(self):
        job = dict(workstream_id=SCOPE, client_message_id="request-current", state="running", updated_at=AFTER)
        result = build(completion_job_snapshot=job)
        self.assertEqual(result["summary"]["state"], "verifying")
        self.assertEqual(result["completion"]["operation"]["parent_operation_id"], result["history"][0]["operation_id"])
        for other in [job | {"client_message_id": "old"}, job | {"updated_at": "2020-01-01T00:00:00Z"}, job | {"workstream_id": "project-other"}]:
            with self.subTest(other=other):
                self.assertNotEqual(build(completion_job_snapshot=other)["completion"]["state"], "verifying")
        self.assertNotEqual(build(completion_job_snapshot=job,session_snapshot=session(messages=[message(delivery_confirmed=False)]))["completion"]["state"],"verifying")

    def test_newer_completion_record_wins_over_old_job(self):
        result = build(completion_snapshot=completion(state="receipt_accepted"), completion_job_snapshot={
            "workstream_id": SCOPE, "client_message_id": "old", "state": "completed", "updated_at": BEFORE})
        self.assertEqual(result["completion"]["state"], "verifying")

    def test_foreign_records_are_not_returned_as_history_or_incidents(self):
        result = build(completion_snapshot=completion(workstream_id="project-other"), release_snapshot=release(workstream_id="project-other"))
        self.assertEqual([r["kind"] for r in result["history"]], ["model"])
        self.assertFalse(result["incidents"])

    def test_active_publication_is_explicitly_receipt_reported_not_live_verified(self):
        result = build(release_snapshot=release(state="running", active=True))
        self.assertEqual(result["summary"]["state"], "publication_reported")
        self.assertEqual(result["publication"]["operation"]["liveness"], "not_checked")
        self.assertIsNone(result["publication"]["operation"]["client_request_id"])
        self.assertEqual(result["publication"]["outcome"], "unverified")

    def test_old_reported_release_does_not_become_current_work(self):
        result = build(release_snapshot=release(state="running", active=True,created_at="2020-01-01T00:00:00Z"))
        self.assertEqual(result["summary"]["state"], "ready")
        self.assertEqual(result["publication"]["state"], "recorded")

    def test_current_empty_conversation_can_report_its_new_release(self):
        result = build(session_snapshot=session(messages=[]),release_snapshot=release(state="queued",active=True))
        self.assertEqual(result["summary"]["state"],"publication_reported")

    def test_later_exact_deployment_evidence_does_not_rewrite_attention_receipt(self):
        source = release(state="attention", verification={"state":"deployed", "main_head":HEAD,
            "deployment_target":"github_pages", "deployment_id":42,"smoke_http_status":200})
        before = copy.deepcopy(source)
        result = build(release_snapshot=source)
        self.assertEqual(result["publication"]["outcome"], "deployment_verified")
        self.assertEqual(result["publication"]["operation"]["state"], "attention")
        self.assertEqual(source,before)
        self.assertTrue(any(i["code"]=="receipt_attention_verified_deployment" for i in result["incidents"]))

    def test_wrong_head_target_or_smoke_cannot_confirm_publication(self):
        good={"state":"deployed","main_head":HEAD,"deployment_target":"github_pages","deployment_id":42,"smoke_http_status":200}
        for patch_value in [{"main_head":"b"*40},{"deployment_target":"cockpit"},{"deployment_id":True},{"smoke_http_status":503}]:
            self.assertEqual(build(release_snapshot=release(verification=good|patch_value))["publication"]["outcome"],"unverified")

    def test_dry_run_never_confirms_a_deployment(self):
        result=build(release_snapshot=release(dry_run=True,state="dry_run_completed",verification={
            "state":"deployed","main_head":HEAD,"deployment_target":"github_pages","deployment_id":42,"smoke_http_status":200}))
        self.assertEqual(result["publication"]["outcome"],"dry_run_completed")

    def test_future_publication_is_unverified(self):
        result=build(release_snapshot=release(updated_at="2027-01-01T00:00:00Z"))
        self.assertEqual(result["publication"]["state"],"unverified")

    def test_revision_is_stable_when_only_observation_time_changes(self):
        first=build();second=build(observed_at="2026-11-12T10:00:00Z")
        self.assertEqual(first["revision"],second["revision"])
        self.assertNotEqual(first["observed_at"],second["observed_at"])
        self.assertNotEqual(first["revision"],build(session_snapshot=session(connected=False))["revision"])

    def test_scope_change_invalidates_all_current_operations(self):
        result=build(snapshot_consistent=False,release_snapshot=release(state="running",active=True))
        self.assertFalse(result["consistent"])
        self.assertEqual(result["summary"]["state"],"unverified")
        self.assertIsNone(result["summary"]["operation_id"])
        self.assertFalse(result["history"])

    def test_bad_source_is_separate_from_no_work(self):
        result=build(source_errors=("session","publication"))
        self.assertEqual(result["summary"]["state"],"unverified")
        self.assertEqual(len([i for i in result["incidents"] if i["code"]=="source_unavailable"]),2)
        self.assertEqual(build(source_errors=("publication",))["summary"]["state"],"unverified")

    def test_inputs_are_unchanged_and_raw_fields_are_not_exported(self):
        values={"session_snapshot":session(),"completion_snapshot":completion(),"release_snapshot":release()}
        before=copy.deepcopy(values)
        result=build(**values)
        self.assertEqual(values,before)
        self.assertNotIn("PRIVATE_TEXT",json.dumps(result))

    def test_unknown_state_or_bad_field_types_do_not_leak_source_text(self):
        result=build(completion_snapshot=completion(state="PRIVATE_TEXT"),release_snapshot=release(state="PRIVATE_TEXT"),
                     session_snapshot=session(messages=[message(status=[])]))
        self.assertNotIn("PRIVATE_TEXT",json.dumps(result))
        self.assertEqual(result["publication"]["operation"]["state"],"unverified")

    def test_future_completion_cannot_be_verifying(self):
        result=build(completion_snapshot=completion(state="receipt_accepted",updated_at="2027-01-01T00:00:00Z"))
        self.assertNotEqual(result["completion"]["state"],"verifying")

    def test_confirmed_delivery_and_connection_generation_are_independent(self):
        result=build(session_snapshot=session(connection_generation=2,messages=[message(delivery_confirmed=False)]))
        self.assertEqual(result["connection"]["state"],"connected")
        self.assertEqual(result["model"]["state"],"unverified")
        self.assertEqual(result["scope"]["connection_generation"],2)

    def test_future_model_start_cannot_claim_running(self):
        result=build(session_snapshot=session(turn_busy=True,messages=[message(status="pending")],
            active_turn={"client_message_id":"request-current","started_at":"2027-01-01T00:00:00Z"}))
        self.assertEqual(result["model"]["state"],"unverified")

    def test_invalid_scope_or_clock_is_fail_closed(self):
        for overrides in [{"workstream_id":"/private/path"},{"observed_at":"not a clock"}]:
            self.assertFalse(build(**overrides)["consistent"])


class WorkStateIntegrationTests(unittest.TestCase):
    def test_scope_rotation_during_job_adapter_read_invalidates_the_whole_projection(self):
        from tests import test_human_adam_profiles as fixtures
        from app.communication.human_adam_work import WorkStore
        with tempfile.TemporaryDirectory() as directory:
            manager,*_=fixtures.HumanAdamProfileManagerTests().make_manager(Path(directory))
            try:
                payload=manager.status();service=manager.active_service
                def rotate(*args):
                    service.hub.thread_id='rotated-during-jobs'
                    return []
                with patch.object(WorkStore,'recent',side_effect=rotate):
                    result=manager._project_work_state(payload,SCOPE,service)
                self.assertFalse(result['consistent'])
                self.assertFalse(result['server_jobs']['consistent'])
                self.assertIsNone(result['server_jobs']['current_job_id'])
            finally:manager.close()

    def test_status_adds_projection_without_release_recovery_or_source_writes(self):
        from tests import test_human_adam_profiles as fixtures
        from app.communication.luna_release import LunaReleaseStore
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            manager,*_=fixtures.HumanAdamProfileManagerTests().make_manager(root)
            try:
                manager.status()  # Existing manager bootstrap is outside the new projection.
                before={str(p.relative_to(root)):(p.read_bytes(),p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}
                with patch.object(LunaReleaseStore,"status",side_effect=AssertionError("mutating recovery")):
                    result=manager.status()
                after={str(p.relative_to(root)):(p.read_bytes(),p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}
                self.assertEqual(before,after)
                projection=result["work_state"]
                self.assertEqual(projection["scope"]["workstream_id"],SCOPE)
                self.assertTrue(projection["read_only"])
                self.assertFalse(projection["writes_performed"])
            finally:manager.close()

    def test_corrupt_release_receipt_does_not_break_session_status(self):
        from tests import test_human_adam_profiles as fixtures
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);manager,*_=fixtures.HumanAdamProfileManagerTests().make_manager(root)
            try:
                folder=root/"luna_release";folder.mkdir();(folder/"current.json").write_text("bad-json")
                result=manager.status()
                self.assertTrue(result["ok"])
                self.assertIn({"source":"publication","code":"source_unavailable"},result["work_state"]["incidents"])
            finally:manager.close()

    def test_thread_rotation_during_collection_invalidates_projection(self):
        from tests import test_human_adam_profiles as fixtures
        with tempfile.TemporaryDirectory() as directory:
            manager,*_=fixtures.HumanAdamProfileManagerTests().make_manager(Path(directory))
            try:
                payload=manager.status();service=manager.active_service
                service.hub.thread_id="rotated-thread"
                result=manager._project_work_state(payload,SCOPE,service)
                self.assertFalse(result["consistent"])
                self.assertEqual(result["summary"]["state"],"unverified")
            finally:manager.close()

    def test_new_message_during_collection_cannot_reactivate_an_old_snapshot(self):
        from tests import test_human_adam_profiles as fixtures
        with tempfile.TemporaryDirectory() as directory:
            manager,*_=fixtures.HumanAdamProfileManagerTests().make_manager(Path(directory))
            try:
                payload=manager.status();service=manager.active_service
                service.hub.messages.append(message(client_message_id="newer-request"))
                result=manager._project_work_state(payload,SCOPE,service)
                self.assertFalse(result["consistent"])
                self.assertIsNone(result["summary"]["operation_id"])
            finally:manager.close()
