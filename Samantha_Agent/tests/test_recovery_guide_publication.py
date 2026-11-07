from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import recovery_guide_publication as a
from app import recovery_guide_publish as p
from app import recovery_guide_quality as q
from app.file_persistence import exclusive_file_lock, FileLockTimeoutError
from app.recovery_guide_sources import canonical_json, digest
from tests import test_recovery_guide_quality as fixtures
from tests.test_recovery_guide import CLOUD


class Publication(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        (self.root/"local").mkdir();(self.root/"cloud").mkdir()
        self.local=self.root/"local/guide.txt";self.cloud=self.root/"cloud/guide.txt"
        self.local.write_bytes(b"old local\r\n");self.cloud.write_bytes(b"old cloud\r\n")
        self.store=a.PublicationStore(self.root/"state",sandbox_root=self.root,destinations=(self.local,self.cloud))
        self.snapshot=fixtures.snap();self.context=fixtures.context(self.snapshot)
        self.answer=fixtures.answer();self.dossier=fixtures.dossier(self.context)
        self.now=datetime(2026,11,7,12,tzinfo=timezone.utc)
        self.draft=self.store.prepare(self.answer,self.snapshot,self.dossier,self.context)

    def accept(self, request="one", draft=None, **kwargs):
        draft=draft or self.draft
        return self.store.accept(draft,request_id=request,confirmed_binding=draft.sha256,confirmed=True,now=self.now,**kwargs)

    def execute(self, receipt, **kwargs):
        params=dict(approval_sha256=receipt["approval_sha256"],current_inputs=lambda _:True,cloud_audit=lambda _:CLOUD,now=self.now)
        params.update(kwargs)
        return self.store.execute(receipt["request_id"],**params)

    def test_preview_and_missing_confirmation_write_nothing(self):
        result=self.store.accept(self.draft,request_id="one",confirmed_binding=self.draft.sha256)
        self.assertEqual(result["state"],"confirmation_required")
        self.assertFalse((self.root/"state").exists())
        self.assertEqual(self.local.read_bytes(),b"old local\r\n")

    def test_acceptance_rechecks_review_and_is_immutable(self):
        receipt=self.accept()
        again=self.store.accept(self.draft,request_id="one",confirmed_binding=self.draft.sha256,confirmed=False)
        self.assertEqual(receipt["approval_sha256"],again["approval_sha256"])
        self.answer["paragraphs"][0]["text"]="mutated caller dict"
        self.assertEqual(self.store.candidate_text(self.draft),self.snapshot.original.text)
        self.assertEqual(receipt["state"],"accepted")

    def test_publication_is_two_copies_with_all_three_originals_preserved(self):
        receipt=self.accept();result=self.execute(receipt)
        self.assertEqual(result["state"],"uploaded")
        self.assertEqual(self.local.read_bytes(),self.snapshot.original.text.encode())
        self.assertEqual(self.local.read_bytes(),self.cloud.read_bytes())
        self.assertEqual(result["model_calls"],0)
        self.assertEqual(result["physical_iphone_acceptance"],"not_verified")
        archives=list((self.root/"state/writes").glob("previous-*.txt"))
        self.assertEqual({p.read_bytes() for p in archives},{b"old local\r\n",b"old cloud\r\n"})
        self.assertEqual((self.root/"state/requests/one/source-original.txt").read_bytes(),self.snapshot.original.text.encode())

    def test_wrong_confirmation_or_request_does_not_write(self):
        with self.assertRaises(ValueError):
            self.store.accept(self.draft,request_id="one",confirmed_binding="0"*64,confirmed=True,now=self.now)
        with self.assertRaises(ValueError):
            self.accept(request="../escape")
        self.assertFalse((self.root/"state").exists())

    def test_unaccepted_execute_cannot_use_only_candidate_hash(self):
        with self.assertRaises(ValueError):
            self.store.execute("missing",approval_sha256=digest(self.snapshot.original.text),current_inputs=lambda _:True)
        self.assertFalse((self.root/"state").exists())
        self.assertFalse(hasattr(p,"publish"))

    def test_blocked_quality_cannot_be_approved(self):
        with self.assertRaises(ValueError):
            self.store.prepare(self.answer,self.snapshot,self.dossier,replace(self.context,application_scope_approved=False))

    def test_one_request_cannot_accept_a_different_dossier(self):
        self.accept()
        changed=deepcopy(self.dossier);changed["applications"]=list(reversed(changed["applications"]))
        draft=self.store.prepare(self.answer,self.snapshot,changed,self.context)
        with self.assertRaises(ValueError):self.accept(draft=draft)

    def test_tampered_candidate_packet_quality_original_and_approval_are_refused(self):
        for name in ["candidate.txt","packet.json","quality.json","source-original.txt","approval.json"]:
            with self.subTest(name=name):
                request="tamper-"+name.replace(".","-");receipt=self.accept(request=request)
                path=self.root/"state/requests"/request/name
                path.write_text('{}' if name.endswith('.json') else 'tampered')
                with self.assertRaises((ValueError,KeyError,TypeError)):
                    self.execute(receipt)
        self.assertEqual(self.local.read_bytes(),b"old local\r\n")

    def test_approval_digest_is_required_even_with_valid_packet(self):
        receipt=self.accept()
        with self.assertRaises(ValueError):self.execute(receipt,approval_sha256="0"*64)

    def test_approval_manifest_cannot_be_reformatted_after_acceptance(self):
        receipt=self.accept();path=self.root/"state/requests/one/approval.json"
        path.write_text(json.dumps(json.loads(path.read_text()),indent=2))
        with self.assertRaises(ValueError):self.execute(receipt)

    def test_current_sources_changed_or_proof_aged_stops_first_write(self):
        receipt=self.accept()
        result=self.execute(receipt,current_inputs=lambda _:False)
        self.assertEqual(result["state"],"inputs_changed_or_stale")
        self.assertEqual(self.local.read_bytes(),b"old local\r\n")
        self.assertFalse((self.root/"state/writes").exists())

    def test_dated_evidence_is_rechecked_before_first_delivery(self):
        self.dossier["applications"][0]["fields"]["version"]={"value":"Python 3.11","status":"documented",
            "source":"docs/current.md","quote":fixtures.DOC,"observed_on":"2026-11-07"}
        draft=self.store.prepare(self.answer,self.snapshot,self.dossier,self.context)
        receipt=self.accept(draft=draft)
        result=self.execute(receipt,now=datetime(2027,3,1,tzinfo=timezone.utc))
        self.assertEqual(result["state"],"inputs_changed_or_stale")
        self.assertEqual(self.local.read_bytes(),b"old local\r\n")

    def test_future_acceptance_or_changed_validator_needs_new_review(self):
        with self.assertRaises(ValueError):
            self.store.accept(self.draft,request_id="one",confirmed_binding=self.draft.sha256,confirmed=True,
                              now=datetime(2026,11,8,tzinfo=timezone.utc))
        receipt=self.accept()
        with patch.object(q,"VALIDATOR_VERSION",q.VALIDATOR_VERSION+1):
            with self.assertRaises(ValueError):self.execute(receipt)

    def test_second_copy_failure_rolls_back_safely_and_can_finish_same_candidate(self):
        receipt=self.accept();original=p.atomic_replace_text_under_external_lock
        def fail(path,text):
            if path==self.cloud:raise OSError("synthetic offline")
            original(path,text)
        with patch.object(p,"atomic_replace_text_under_external_lock",side_effect=fail):
            result=self.execute(receipt)
        self.assertEqual(result["state"],"attention")
        self.assertEqual(result["rollback"],"restored_local")
        self.assertEqual(self.local.read_bytes(),b"old local\r\n")
        self.assertEqual(self.execute(receipt,current_inputs=lambda _:False)["state"],"uploaded")

    def test_crash_after_first_replace_recovers_without_replacing_first_again(self):
        receipt=self.accept();original=p.atomic_write_json
        def crash(path,record):
            if record.get("state")=="local_saved":raise SystemExit()
            original(path,record)
        with patch.object(p,"atomic_write_json",side_effect=crash):
            with self.assertRaises(SystemExit):self.execute(receipt)
        calls=[];replace_text=p.atomic_replace_text_under_external_lock
        def capture(path,text):calls.append(path);replace_text(path,text)
        with patch.object(p,"atomic_replace_text_under_external_lock",side_effect=capture):
            result=self.execute(receipt,current_inputs=lambda _:False)
        self.assertEqual(result["state"],"uploaded")
        self.assertEqual(calls,[self.cloud])

    def test_crash_after_second_replace_resumes_without_rewriting_either_copy(self):
        receipt=self.accept();original=p.atomic_write_json
        def crash(path,record):
            if record.get("state")=="both_local_saved":raise SystemExit()
            original(path,record)
        with patch.object(p,"atomic_write_json",side_effect=crash):
            with self.assertRaises(SystemExit):self.execute(receipt)
        with patch.object(p,"atomic_replace_text_under_external_lock",side_effect=AssertionError("no repeat")):
            self.assertEqual(self.execute(receipt)["state"],"uploaded")

    def test_interrupted_acceptance_is_not_a_grant_and_resumes_same_inputs(self):
        original=a.atomic_create_text
        def crash(path,text,**kwargs):
            if path.name=="approval.json":raise SystemExit()
            original(path,text,**kwargs)
        with patch.object(a,"atomic_create_text",side_effect=crash):
            with self.assertRaises(SystemExit):self.accept()
        self.assertEqual(self.store.status("one")["state"],"not_accepted")
        self.assertEqual(self.local.read_bytes(),b"old local\r\n")
        self.assertEqual(self.execute(self.accept())["state"],"uploaded")

    def test_pending_icloud_retry_checks_metadata_without_any_new_replace(self):
        receipt=self.accept()
        result=self.execute(receipt,cloud_audit=lambda _:{**CLOUD,"uploaded":False})
        self.assertEqual(result["state"],"pending_icloud")
        with patch.object(p,"atomic_replace_text_under_external_lock",side_effect=AssertionError("must not rewrite")):
            self.assertEqual(self.execute(receipt)["state"],"uploaded")

    def test_initial_and_later_metadata_failure_do_not_claim_success(self):
        receipt=self.accept();calls=iter([CLOUD,{"available":False}])
        self.assertEqual(self.execute(receipt,cloud_audit=lambda _:next(calls))["state"],"pending_icloud")
        self.assertEqual(self.execute(receipt,cloud_audit=lambda _:{"available":False})["state"],"pending_icloud")

    def test_cloud_audit_exception_after_copies_is_pending(self):
        receipt=self.accept();calls=0
        def audit(_):
            nonlocal calls
            calls+=1
            if calls==2:raise TimeoutError("synthetic provider outage")
            return CLOUD
        self.assertEqual(self.execute(receipt,cloud_audit=audit)["state"],"pending_icloud")

    def test_non_icloud_parent_stops_before_target_writes(self):
        receipt=self.accept()
        result=self.execute(receipt,cloud_audit=lambda _:{"available":True,"ubiquitous":False})
        self.assertEqual(result["state"],"attention")
        self.assertEqual(self.local.read_bytes(),b"old local\r\n")
        self.assertEqual(self.cloud.read_bytes(),b"old cloud\r\n")

    def test_rollback_preserves_foreign_local_edit(self):
        receipt=self.accept();original=p.atomic_replace_text_under_external_lock
        def fail(path,text):
            if path==self.cloud:
                self.local.write_text("manual edit during transfer")
                raise OSError("synthetic failure")
            original(path,text)
        with patch.object(p,"atomic_replace_text_under_external_lock",side_effect=fail):
            result=self.execute(receipt)
        self.assertEqual(result["state"],"attention")
        self.assertEqual(self.local.read_text(),"manual edit during transfer")
        self.assertEqual(result["copies"]["local"],"changed")

    def test_rollback_failure_is_visible_and_recoverable(self):
        receipt=self.accept();original=p.atomic_replace_text_under_external_lock
        def fail(path,text):
            if path==self.cloud or text=="old local\r\n":raise OSError("synthetic rollback failure")
            original(path,text)
        with patch.object(p,"atomic_replace_text_under_external_lock",side_effect=fail):result=self.execute(receipt)
        self.assertEqual(result["state"],"attention")
        self.assertEqual(result["rollback"],"failed")
        self.assertEqual(result["copies"],{"local":"candidate","icloud":"baseline"})
        self.assertEqual(self.execute(receipt)["state"],"uploaded")

    def test_manual_edit_during_cloud_audit_is_not_uploaded_success(self):
        receipt=self.accept();calls=0
        def audit(_):
            nonlocal calls
            calls+=1
            if calls==2:self.local.write_text("human changed during audit")
            return CLOUD
        result=self.execute(receipt,cloud_audit=audit)
        self.assertEqual(result["state"],"attention")
        self.assertEqual(self.local.read_text(),"human changed during audit")
        self.assertEqual(result["copies"]["local"],"changed")

    def test_manual_edit_after_acceptance_is_preserved(self):
        receipt=self.accept();self.cloud.write_text("human edit")
        self.assertEqual(self.execute(receipt)["state"],"attention")
        self.assertEqual(self.cloud.read_text(),"human edit")

    def test_manual_revert_to_original_bytes_after_upload_is_not_reapplied(self):
        receipt=self.accept();self.execute(receipt)
        self.local.write_bytes(b"old local\r\n")
        with patch.object(p,"atomic_replace_text_under_external_lock",side_effect=AssertionError("must not overwrite revert")):
            self.assertEqual(self.execute(receipt)["state"],"attention")
        self.assertEqual(self.local.read_bytes(),b"old local\r\n")

    def test_manual_revert_while_waiting_for_cloud_is_preserved(self):
        receipt=self.accept();self.execute(receipt,cloud_audit=lambda _:{**CLOUD,"uploaded":False})
        self.cloud.write_bytes(b"old cloud\r\n")
        self.assertEqual(self.execute(receipt)["state"],"attention")
        self.assertEqual(self.cloud.read_bytes(),b"old cloud\r\n")

    def test_corrupted_archive_prevents_resume(self):
        receipt=self.accept();self.execute(receipt,cloud_audit=lambda _:{**CLOUD,"uploaded":False})
        archive=next((self.root/"state/writes").glob("previous-*.txt"));archive.write_text("corrupt")
        self.assertEqual(self.execute(receipt)["state"],"attention")

    def test_old_request_cannot_overwrite_a_newer_published_version(self):
        first=self.accept();self.execute(first)
        text=self.snapshot.original.text+"\nDoplňující podklad pro další obnovu.\n"
        snapshot=replace(self.snapshot,original=replace(self.snapshot.original,text=text,sha256=digest(text)))
        context=replace(self.context,snapshot_sha256=snapshot.sha256)
        draft=self.store.prepare(fixtures.answer(text),snapshot,self.dossier,context)
        second=self.accept(request="two",draft=draft);self.assertEqual(self.execute(second)["state"],"uploaded")
        self.assertEqual(self.execute(first)["state"],"superseded")
        self.assertEqual(self.local.read_text(),text)

    def test_active_marker_without_execution_record_does_not_revive_old_request(self):
        first=self.accept();self.execute(first)
        draft=self.store.prepare(self.answer,self.snapshot,self.dossier,self.context)
        second=self.accept(request="two",draft=draft)
        original=a.atomic_write_json
        def crash(path,record):
            if path==self.root/"state/requests/two/execution.json":raise SystemExit()
            original(path,record)
        with patch.object(a,"atomic_write_json",side_effect=crash):
            with self.assertRaises(SystemExit):self.execute(second)
        self.assertEqual(self.execute(first)["state"],"superseded")
        third=self.accept(request="three",draft=draft)
        self.assertEqual(self.execute(third)["state"],"waiting_previous_delivery")
        self.assertEqual(self.execute(second)["state"],"uploaded")

    def test_new_local_target_is_not_deleted_after_second_copy_failure(self):
        self.local.rename(self.root/"saved-old-local.txt")
        draft=self.store.prepare(self.answer,self.snapshot,self.dossier,self.context)
        receipt=self.accept(draft=draft)
        original=p.atomic_replace_text_under_external_lock
        def fail(path,text):
            if path==self.cloud:raise OSError("synthetic offline")
            original(path,text)
        with patch.object(p,"atomic_replace_text_under_external_lock",side_effect=fail):result=self.execute(receipt)
        self.assertEqual(result["state"],"attention")
        self.assertEqual(result["copies"],{"local":"candidate","icloud":"baseline"})
        self.assertEqual(self.local.read_bytes(),self.snapshot.original.text.encode())
        self.assertEqual(self.execute(receipt)["state"],"uploaded")

    def test_pending_previous_guide_blocks_a_different_approved_guide(self):
        first=self.accept();self.execute(first,cloud_audit=lambda _:{**CLOUD,"uploaded":False})
        draft=self.store.prepare(self.answer,self.snapshot,self.dossier,self.context)
        second=self.accept(request="two",draft=draft)
        self.assertEqual(self.execute(second)["state"],"waiting_previous_delivery")

    def test_store_lock_and_reconstructed_store_preserve_identity(self):
        receipt=self.accept()
        with exclusive_file_lock(self.root/"state/store"):
            with self.assertRaises(FileLockTimeoutError):self.execute(receipt)
        restored=a.PublicationStore(self.root/"state",sandbox_root=self.root,destinations=(self.local,self.cloud))
        self.assertEqual(restored.status("one")["approval_sha256"],receipt["approval_sha256"])

    def test_request_and_artifact_symlinks_are_not_followed(self):
        receipt=self.accept();directory=self.root/"state/requests/one"
        saved=directory/"candidate-saved.txt";(directory/"candidate.txt").rename(saved)
        (directory/"candidate.txt").symlink_to(saved)
        with self.assertRaises(ValueError):self.execute(receipt)

    def test_weakened_private_state_permissions_are_refused(self):
        receipt=self.accept();(self.root/"state").chmod(0o755)
        with self.assertRaises(ValueError):self.execute(receipt)
        (self.root/"state").chmod(0o700)

    def test_changed_destination_pair_cannot_reuse_acceptance(self):
        self.accept();other=self.root/"cloud/other.txt"
        changed=a.PublicationStore(self.root/"state",sandbox_root=self.root,destinations=(self.local,other))
        with self.assertRaises(ValueError):changed.status("one")

    def test_targets_outside_sandbox_and_production_mode_are_refused(self):
        with self.assertRaises(ValueError):
            a.PublicationStore(self.root/"state",sandbox_root=self.root,destinations=(self.local,Path('/outside/guide.txt')))
        with self.assertRaises(ValueError):
            a.PublicationStore(self.root/"state",sandbox_root=self.root,destinations=(self.local,self.cloud),mode="production")
        with self.assertRaisesRegex(ValueError,"sandbox_root_not_isolated"):
            a.PublicationStore(self.root/"state",sandbox_root=Path.home(),destinations=(self.local,self.cloud))

    def test_known_alias_target_works_but_retargeted_alias_refuses(self):
        alias=self.root/"Documents";alias.symlink_to(self.cloud.parent,target_is_directory=True)
        store=a.PublicationStore(self.root/"alias-state",sandbox_root=self.root,destinations=(self.local,alias/"guide.txt"))
        draft=store.prepare(self.answer,self.snapshot,self.dossier,self.context)
        receipt=store.accept(draft,request_id="alias",confirmed_binding=draft.sha256,confirmed=True,now=self.now)
        self.assertEqual(store.execute("alias",approval_sha256=receipt["approval_sha256"],current_inputs=lambda _:True,
                         cloud_audit=lambda _:CLOUD,now=self.now)["state"],"uploaded")
        alias.rename(self.root/"old-alias");alias.symlink_to(self.local.parent,target_is_directory=True)
        with self.assertRaises(ValueError):store.status("alias")


if __name__=="__main__":unittest.main()
