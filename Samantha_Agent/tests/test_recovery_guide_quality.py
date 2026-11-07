from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from app import recovery_guide_quality as q
from app.recovery_guide_sources import Source, Snapshot, digest
from tests import test_recovery_guide as fixtures

ORIGINAL = """1. MAC
Python .venv Codex App Server config/agent_roles.json Cockpit launchd PATH
Tailscale HTTPS záloha data mimo Git Camino Xcode podpis instalace přihlášení
oprávnění a iCloud. Obnov všechny potřebné soubory podle uvedených zdrojů.

2. IPHONE
iPhone instalace a podpis, spojení Tailscale HTTPS, důvěra vývojáři,
oprávnění a iCloud. Fyzické ověření je samostatný ruční krok.
"""
DOC = "Python 3.11 je dokumentovaná verze. PictNew konfigurace /safe/pict.json; model gpt-6.1-sol."


def snap(text=DOC, authority="documented_not_live"):
    return Snapshot("a" * 40, Source("original_guide", digest(ORIGINAL), ORIGINAL, "previous_version"),
                    (Source("docs/current.md", digest(text), text, authority),))


def answer(original=ORIGINAL):
    return {"paragraphs": [{"text": original.strip(), "status": "unchanged", "evidence": []}]}


def added(text, quote=DOC, status="documented"):
    value = answer()
    value["paragraphs"].append({"text": text, "status": status,
                              "evidence": [{"source": "docs/current.md", "quote": quote}]})
    return value


def dossier(context):
    return {"applications": [{"name": name, "fields": {field: {
        "value": "neověřeno", "status": "unverified", "source": None, "quote": None, "observed_on": None}
        for field in q.FIELDS}} for name in context.applications]}


def context(snapshot):
    return q.ReviewContext(snapshot.sha256, date(2026,11,7),
        facts=(q.SourceFact("docs/current.md",snapshot.sources[0].sha256,"documented","2026-11-07"),),
        applications=("Python","Codex","Cockpit","Tailscale","Camino","Xcode","iCloud"),application_scope_approved=True,
        macos_expected="TestOS 1", macos_observed="TestOS 1")


class Core(unittest.TestCase):
    def assert_code(self, expected, value, snapshot=None, **kw):
        with self.assertRaises(q.QualityError) as caught:
            q.validate(value, snapshot or snap(), **kw)
        self.assertEqual(caught.exception.code, expected)

    def test_valid_unchanged_and_changed_path(self):
        q.validate(answer(),snap())
        q.validate(added("PictNew konfigurace /safe/pict.json."),snap())

    def test_path_must_be_in_quoted_part_not_elsewhere_in_file(self):
        self.assert_code("uncited_technical_literal",added("Použij /invented/location.","Python 3.11 je dokumentovaná verze."))
        self.assert_code("uncited_technical_literal",added("Použij /safe/pict."))

    def test_model_role_change_needs_exact_evidence(self):
        self.assert_code("uncited_technical_literal",added("Model gpt-6-luna."))
        q.validate(added("Model gpt-6.1-sol."),snap())

    def test_false_unchanged_shortcut_rejected(self):
        value=answer();value["paragraphs"][0]["text"] += "\nInvented setting."
        self.assert_code("false_unchanged",value)

    def test_only_headings_without_section_content_rejected(self):
        value=added("1. MAC\n\n2. IPHONE\n"+"Padding "*100)
        value["paragraphs"]=value["paragraphs"][1:]
        self.assert_code("chapter_content_lost",value)

    def test_duplicate_and_reordered_chapters(self):
        self.assert_code("duplicate_chapter",added("1. MAC\nExtra chapter."))
        source=snap(); changed=ORIGINAL[ORIGINAL.index("2. IPHONE"):]+"\n"+ORIGINAL[:ORIGINAL.index("2. IPHONE")]
        source=replace(source,sources=(Source("docs/current.md",digest(changed),changed,"documented_not_live"),))
        value={"paragraphs":[{"text":changed,"status":"documented","evidence":[{"source":"docs/current.md","quote":changed}]}]}
        self.assert_code("reordered_chapters",value,source)

    def test_tampered_or_missing_source(self):
        source=snap();source=replace(source,sources=(replace(source.sources[0],sha256="0"*64),))
        self.assert_code("source_hash_mismatch",answer(),source)
        value=added("PictNew");value["paragraphs"][1]["evidence"][0]["source"]="missing.md"
        self.assert_code("unsupported_citation",value)

    def test_history_or_proposal_cannot_be_current_configuration(self):
        self.assert_code("history_as_current",added("PictNew konfigurace /safe/pict.json."),snap(authority="historical_or_mixed"))
        self.assert_code("history_as_current",added("PictNew konfigurace /safe/pict.json."),snap(authority="proposed"))

    def test_unverified_label_is_visible_in_plain_txt(self):
        text=q.validate(added("PictNew konfigurace /safe/pict.json.",status="unverified"),snap(authority="historical_or_mixed"))
        self.assertIn("[Neověřeno]\nPictNew",text)

    def test_unproven_iphone_and_live_claim(self):
        for text in ["Dnes ověřeno na iPhonu.","iPhone je ověřen.","Cockpit HTTP 200."]:
            with self.subTest(text=text):
                self.assert_code("unproven_live_claim",added(text))

    def test_known_retired_voice_is_blocked_even_if_unchanged(self):
        old=ORIGINAL+"\nSpusť read_only_voice.\n"
        source=replace(snap(),original=Source("original_guide",digest(old),old,"previous_version"))
        self.assert_code("retired_voice_reference",answer(old),source)

    def test_unregistered_shell_forms_rejected_without_execution(self):
        for text in ["$ python3 scripts/status.py","```bash\npython3 scripts/status.py\n```","`python3 scripts/status.py`","Spusť python3 scripts/status.py"]:
            source=snap(text)
            with self.subTest(text=text):
                self.assert_code("unregistered_command",added(text,text),source)

    def test_registered_and_cited_command_can_be_reviewed(self):
        command="python3 scripts/status.py";source=snap("$ "+command)
        ctx=replace(context(source),workflows=(("registered_status",command),))
        q.validate(added("$ "+command,"$ "+command),source,context=ctx)

    def test_credential_assignment_bidi_and_invalid_utf8(self):
        for text,code in [("heslo="+"A"*16,"credential_assignment"),("text\u202ereversed","hidden_control"),("\ud800","unsafe_text")]:
            with self.subTest(code=code):
                self.assert_code(code,added(text))

    def test_malformed_model_status_is_a_safe_validation_error(self):
        value=added("PictNew");value["paragraphs"][1]["status"]=[]
        self.assert_code("invalid_paragraph",value)

    def test_quoted_secret_is_also_rejected_without_logging_value(self):
        text='Python dokumentace. "password": "'+"A"*16+'"'
        source=snap(text)
        self.assert_code("credential_assignment",added("Python dokumentace.",text),source)

    def test_registered_command_context_cannot_be_reused_after_source_change(self):
        ctx=replace(context(snap()),snapshot_sha256="0"*64)
        self.assert_code("review_snapshot_changed",answer(),context=ctx)

    def test_no_change_preserves_original_bytes(self):
        source=snap()
        self.assertEqual(q.validate(answer(),source).encode(),source.original.text.encode())

    def test_date_only_edit_does_not_pretend_content_update(self):
        original="Datum: 2026-10-19\n\n"+ORIGINAL
        changed=original.replace("2026-10-19","2026-11-07")
        source=replace(snap(changed),original=Source("original_guide",digest(original),original,"previous_version"))
        value={"paragraphs":[{"text":changed,"status":"documented","evidence":[{"source":"docs/current.md","quote":changed}]}]}
        self.assert_code("date_only_change",value,source)

    def test_preface_cannot_silently_disappear(self):
        original="Nejprve vyber dokončenou zálohu, nic nespouštěj před kontrolou identity.\n\n"+ORIGINAL
        source=replace(snap(),original=Source("original_guide",digest(original),original,"previous_version"))
        self.assert_code("preface_lost",answer(),source)


class Acceptance(unittest.TestCase):
    def setUp(self):
        self.source=snap();self.ctx=context(self.source);self.data=dossier(self.ctx)

    def check(self, *, value=None, source=None, ctx=None, data=None):
        return q.review(value or answer(),source or self.source,self.data if data is None else data,ctx or self.ctx)

    def assert_issue(self, code, **kw):
        result=self.check(**kw)
        self.assertEqual(result["state"],"blocked")
        self.assertIn(code,[i["code"] for i in result["issues"]])
        self.assertFalse(result["publication_authorized"])

    def set_field(self, **changes):
        field={"value":"Python 3.11","status":"documented","source":"docs/current.md",
               "quote":DOC,"observed_on":"2026-11-07"}
        field.update(changes);self.data["applications"][0]["fields"]["version"]=field

    def test_complete_explicit_unknowns_are_review_not_publication(self):
        result=self.check();self.assertEqual(result["state"],"review")
        self.assertTrue(result["semantic_review_required"])
        self.assertFalse(result["publication_authorized"])

    def test_production_application_inventory_has_no_guessed_approval(self):
        self.assert_issue("application_scope_unapproved",ctx=replace(self.ctx,application_scope_approved=False))
        self.assert_issue("application_scope_unapproved",ctx=replace(self.ctx,applications=()))

    def test_new_application_must_have_every_mac_and_iphone_field(self):
        ctx=replace(self.ctx,applications=(*self.ctx.applications,"PictNew"))
        self.assert_issue("application_coverage",ctx=ctx)
        data=dossier(ctx);self.assertEqual(self.check(ctx=ctx,data=data)["state"],"review")
        del data["applications"][-1]["fields"]["iphone_permissions"]
        self.assert_issue("application_fields_missing",ctx=ctx,data=data)

    def test_documented_app_value_and_line_hash_anchor(self):
        self.set_field();result=self.check()
        self.assertEqual(result["state"],"review")
        self.assertEqual(result["anchors"][0]["source_sha256"],self.source.sources[0].sha256)
        self.assertEqual(result["anchors"][0]["line_start"],1)

    def test_app_value_cannot_be_invented_or_borrowed_from_other_app(self):
        self.set_field(value="Python 9.99");self.assert_issue("unsupported_application_value")
        self.set_field(value="PictNew");self.assert_issue("application_not_in_evidence")

    def test_phone_verification_cannot_be_promoted_from_documentation(self):
        self.set_field(status="manual_verified");self.assert_issue("phone_proof_not_manual")

    def test_iphone_permission_change_needs_specific_and_manual_evidence(self):
        source=snap("Camino: oprávnění k fotografiím je dokumentované.")
        ctx=context(source)
        field={"value":"oprávnění k fotografiím","status":"manual_verified","source":"docs/current.md",
               "quote":source.sources[0].text,"observed_on":"2026-11-07"}
        self.data["applications"][4]["fields"]["iphone_permissions"]=field
        self.assert_issue("phone_proof_not_manual",source=source,ctx=ctx)
        field["value"]="plný přístup k fotografiím"
        self.assert_issue("unsupported_application_value",source=source,ctx=ctx)

    def test_application_start_command_cannot_bypass_workflow_catalog(self):
        text="Python: `python3 scripts/status.py` je spouštěcí příkaz."
        source=snap(text);ctx=context(source)
        self.set_field(value="python3 scripts/status.py",quote=text)
        self.assert_issue("unregistered_command",source=source,ctx=ctx)

    def test_stale_future_and_forged_date(self):
        self.set_field()
        for date_text,code in [("2025-01-01","stale_evidence"),("2026-12-01","future_evidence"),("bad","invalid_evidence_date")]:
            ctx=replace(self.ctx,facts=(replace(self.ctx.facts[0],observed_on=date_text),))
            with self.subTest(code=code):self.assert_issue(code,ctx=ctx)
        self.set_field(observed_on="2026-11-06");self.assert_issue("evidence_date_mismatch")

    def test_manual_proof_is_bound_to_exact_quote(self):
        self.set_field(status="manual_verified")
        fact=replace(self.ctx.facts[0],authority="manual_verified",quote_sha256="0"*64)
        self.assert_issue("live_evidence_anchor_mismatch",ctx=replace(self.ctx,facts=(fact,)))
        fact=replace(fact,quote_sha256=digest(DOC))
        self.assertEqual(self.check(ctx=replace(self.ctx,facts=(fact,)))["state"],"review")

    def test_new_macos_and_unresolved_conflict_block_review(self):
        self.assert_issue("new_macos_requires_review",ctx=replace(self.ctx,macos_observed="TestOS 2"))
        self.assert_issue("macos_baseline_unverified",ctx=replace(self.ctx,macos_observed=None))
        self.assert_issue("unresolved_recovery_conflict",ctx=replace(self.ctx,unresolved_conflicts=("permission conflict",)))

    def test_changed_snapshot_and_source_fact_block(self):
        self.assert_issue("review_snapshot_changed",ctx=replace(self.ctx,snapshot_sha256="0"*64))
        self.set_field();self.assert_issue("fact_hash_mismatch",ctx=replace(self.ctx,facts=(replace(self.ctx.facts[0],sha256="0"*64),)))

    def test_missing_topic_is_visible(self):
        original=ORIGINAL.replace("launchd","autostart")
        source=replace(self.source,original=Source("original_guide",digest(original),original,"previous_version"))
        self.assert_issue("missing_topic",value=answer(original),source=source,ctx=replace(self.ctx,snapshot_sha256=source.sha256))

    def test_unknown_status_cannot_hide_asserted_settings(self):
        self.set_field(status="unverified")
        self.assert_issue("false_unverified")

    def test_history_cannot_be_relabelled_as_current_by_model(self):
        self.set_field();fact=replace(self.ctx.facts[0],authority="historical")
        self.assert_issue("history_as_current",ctx=replace(self.ctx,facts=(fact,)))

    def test_cold_reader_bundle_has_guide_and_checklist_but_no_conversation(self):
        bundle=q.cold_reader_bundle(answer(),self.source,self.data,self.ctx)
        self.assertFalse(bundle["private_history_included"])
        self.assertFalse(bundle["reader_test_executed"])
        self.assertEqual(bundle["application_dossier"],self.data)
        self.assertIn("1. MAC",bundle["guide"])
        self.assertNotIn("sources",bundle)
        self.assertEqual(bundle["quality_receipt"]["dossier_sha256"],digest(q.canonical_json(bundle["application_dossier"])))
        self.data["applications"][0]["fields"]["purpose"]["value"]="changed after review"
        self.assertEqual(bundle["application_dossier"]["applications"][0]["fields"]["purpose"]["value"],"neověřeno")
        with self.assertRaises(q.QualityError):
            q.cold_reader_bundle(answer(),self.source,{},self.ctx)

    def test_bundle_is_readable_in_fresh_isolated_process_from_stdin_only(self):
        bundle=q.cold_reader_bundle(answer(),self.source,self.data,self.ctx)
        reader='''import json,sys
p=json.load(sys.stdin)
assert p["private_history_included"] is False
assert "1. MAC" in p["guide"] and "2. IPHONE" in p["guide"]
assert p["quality_receipt"]["publication_authorized"] is False
unknown=sum(v["status"]=="unverified" for a in p["application_dossier"]["applications"] for v in a["fields"].values())
print(json.dumps({"unknown_fields":unknown,"applications":len(p["application_dossier"]["applications"])}))'''
        with tempfile.TemporaryDirectory() as empty:
            result=subprocess.run([sys.executable,"-I","-c",reader],input=json.dumps(bundle),
                cwd=empty,env={"PATH":"/usr/bin:/bin"},text=True,capture_output=True,check=True,timeout=10)
        self.assertEqual(json.loads(result.stdout),{"unknown_fields":len(q.FIELDS)*len(self.ctx.applications),"applications":7})


class Pipeline(unittest.TestCase):
    setUp=fixtures.Pilot.setUp
    run_pilot=fixtures.Pilot.run_pilot
    call=fixtures.Pilot.call

    def test_invalid_synthesis_stops_without_candidate_or_second_attempt(self):
        original=self.call
        def call(payload,kind):
            response=original(payload,kind)
            if kind=="synthesize":response["answer"]["paragraphs"][0]["text"] += "\nmade up"
            return response
        result=self.run_pilot(call=call)
        self.assertEqual(result["state"],"attention")
        self.assertEqual(result["quality_issue"],"false_unchanged")
        self.assertFalse((self.state/"2026-W45-candidate.txt").exists())
        self.run_pilot(call=call)
        self.assertEqual(len(self.calls),2)


if __name__=="__main__":
    unittest.main()
