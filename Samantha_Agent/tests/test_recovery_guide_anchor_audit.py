from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import recovery_guide_anchor_audit as audit
from app.recovery_guide_sources import Snapshot, Source, canonical_json, digest
from app.recovery_guide_anchors import AnchorError


class AuditTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve()
        self.enterContext(patch.object(audit,'ROOT',self.root))
        self.state=self.root/'.venv/recovery_rec06_full_pilot'
        def source(path,text):return Source(path,digest(text),text,'documented_not_live')
        self.sources=(source('memory/first.md','first source'),source('memory/audio.md','- restart aplikace;'),
                      source('memory/transfer.md','- oddělit byty;'),source('memory/future.md','not read yet'))
        original=source('original_guide','1. OBNOVA\nWhole original guide.\n')
        snap=Snapshot('a'*40,original,self.sources)
        payloads=[{'original':asdict(original),'sources':[asdict(x) for x in rows]} for rows in
                  ((self.sources[0],),self.sources[1:3],(self.sources[3],))]
        packet={'snapshot':asdict(snap),'measurements':{'shards':[{
            'source_paths':[x['path'] for x in p['sources']],'payload_sha256':digest(canonical_json(p))} for p in payloads]}}
        self.parent=digest(canonical_json(packet));self.enterContext(patch.object(audit,'PARENT',self.parent))
        self.write(self.state/'revisions'/(self.parent+'.json'),{'packet':packet,'approval_digest':self.parent})
        a={'covered':[{'source':original.path,'quote':original.text},
                      {'source':self.sources[0].path,'quote':self.sources[0].text}],'notes':'Never reaccept these notes.'}
        b={'covered':[{'source':self.sources[1].path,'quote':'Restart aplikace;'},
                      {'source':self.sources[2].path,'quote':'Oddělit byty;'}],'notes':'Never reaccept these notes either.'}
        turns=[]
        for i,response in enumerate((a,b),1):
            path=self.state/'turns'/f'{i:02d}.json'
            self.write(path,{'state':'completed','payload_sha256':digest(canonical_json(payloads[i-1])),
                             'receipt':{'delivered':True,'answer':json.dumps(response)}})
            turns.append({'receipt_sha256':digest(path.read_bytes())})
        issues=[{'source':self.sources[i].path,'source_sha256':self.sources[i].sha256,
                 'model_quote':row['quote'],'source_quote':self.sources[i].text[2:],'review_only':True}
                for i,row in zip((1,2),b['covered'])]
        self.report=self.root/'memory/reports/recovery_guide_rec06_full_result_20261107.json'
        self.write(self.report,{'approved_manifest_digest':self.parent,'actual_sdk_turns':2,
                                'turns':turns,'citation_issues':issues})
        self.write(self.state/'attempt.json',{'state':'attention'})
        self.write(self.state/'receipt-recovery-attempt.json',{'state':'attention'})

    def write(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))

    def test_audit_is_read_only_and_fixtures_do_not_reaccept_old_job(self):
        before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result=audit.audit_saved()
        self.assertEqual(result['model_calls'],0)
        self.assertEqual(result['fixture_documents'],3)
        self.assertEqual(result['case_regression_fixtures'],2)
        self.assertEqual(result['full_manifest_documents'],4)
        self.assertTrue(result['partial_history_synthesis_refused'])
        self.assertFalse(result['old_notes_reaccepted'])
        self.assertFalse(result['live_anchor_model_tested'])
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_modified_receipt_fails_without_model_or_repair(self):
        path=self.state/'turns/02.json';raw=json.loads(path.read_text())
        raw['receipt']['answer']='changed';self.write(path,raw)
        with self.assertRaisesRegex(AnchorError,'receipt_changed'):audit.audit_saved()

    def test_unreviewed_nonliteral_case_is_not_automatically_lowercased(self):
        report=json.loads(self.report.read_text());report['citation_issues']=[];self.write(self.report,report)
        with self.assertRaisesRegex(AnchorError,'unknown_nonliteral'):audit.audit_saved()


if __name__=='__main__':unittest.main()
