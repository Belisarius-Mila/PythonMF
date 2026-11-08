from dataclasses import replace, FrozenInstanceError
import json
import unittest

from app.recovery_guide_sources import Snapshot, Source, canonical_json, digest
from app.recovery_guide_anchors import Catalogue, AnchorError
from app import recovery_guide_anchor_protocol as p
from app import recovery_guide_quality as q
from tests.test_recovery_guide import ORIGINAL


def source(path,text,authority='documented_not_live'):
    return Source(path,digest(text),text,authority)


def snapshot():
    return Snapshot('a'*40,source('original_guide',ORIGINAL,'previous_version'),(
        source('memory/a.md','# Audio\n- restart aplikace nikdy sám nezapne mikrofon;\ngit status\n'),
        source('memory/b.md','# Přenos\r\n\r\n- oddělit 100 % odeslaných bytů od serverového `verified`;\r\n  konec bez newline')))


class Anchors(unittest.TestCase):
    def setUp(self):
        self.snap=snapshot();self.cat=Catalogue(self.snap)
        self.a=self.cat.source_id('memory/a.md');self.b=self.cat.source_id('memory/b.md')

    def response(self,request,*,findings=None):
        data=request.payload['data']
        return json.dumps({'request_id':request.payload['request_id'],
            'covered':{s['source_id']:next(l[0] for l in s['lines'] if l[0])
                       for s in data['sources']},'findings':findings or []},ensure_ascii=False)

    def inspect(self,paths=None,*,findings=None):
        request=p.inspection_request(self.cat,tuple(paths or ['memory/a.md','memory/b.md']))
        return request,self.response(request,findings=findings)

    def synth(self,*,findings=None):
        request,raw=self.inspect(findings=findings)
        return p.synthesis_request(self.cat,[(request,raw)])

    def output(self,request,paragraphs=None):
        return json.dumps({'request_id':request.payload['request_id'],'paragraphs':paragraphs or [
            {'text':ORIGINAL.strip(),'status':'unchanged','evidence':[]}]},ensure_ascii=False)

    def test_line_input_preserves_complete_unicode_crlf_and_blank_bytes(self):
        for sid in (self.cat.original_id,*self.cat.document_ids):
            data=self.cat.model_source(sid)
            self.assertEqual(''.join(r[1] for r in data['lines']),self.cat.source(sid).text)
            self.assertEqual(digest(''.join(r[1] for r in data['lines'])),data['sha256'])
        self.assertIsNone(self.cat.model_source(self.b)['lines'][1][0])

    def test_resolver_uses_exact_source_not_sentence_capitalization(self):
        a=self.cat.resolve(self.a,'l2',catalogue_sha256=self.cat.sha256)
        b=self.cat.resolve(self.b,'l3',catalogue_sha256=self.cat.sha256)
        self.assertEqual(a['quote'],'- restart aplikace nikdy sám nezapne mikrofon;')
        self.assertTrue(b['quote'].startswith('- oddělit 100 %'))
        self.assertNotIn('\r',b['quote'])

    def test_indent_trailing_spaces_and_unterminated_line_are_exact(self):
        c=Catalogue(replace(self.snap,sources=(source('memory/a.md','  citace  \nbez konce'),)))
        sid=c.source_id('memory/a.md')
        self.assertEqual(c.resolve(sid,'l1',catalogue_sha256=c.sha256)['quote'],'  citace  ')
        self.assertEqual(c.resolve(sid,'l2',catalogue_sha256=c.sha256)['quote'],'bez konce')

    def test_unknown_blank_anchor_or_wrong_catalogue_never_resolves(self):
        for sid,aid,sha in [(self.a,'l999',self.cat.sha256),(self.b,'l2',self.cat.sha256),
                             ('other','l1',self.cat.sha256),(self.a,'l1','0'*64),(self.a,True,self.cat.sha256)]:
            with self.subTest(sid=sid,aid=aid),self.assertRaises(AnchorError):
                self.cat.resolve(sid,aid,catalogue_sha256=sha)

    def test_empty_source_wrong_hash_duplicate_path_and_secret_are_rejected(self):
        for s in (source('memory/empty.md','\n \t'),Source('memory/a.md','bad','text','documented'),
                  self.snap.original,source('memory/secret.md','sk-'+'x'*30)):
            with self.subTest(path=s.path),self.assertRaises(ValueError):
                Catalogue(replace(self.snap,sources=(*self.snap.sources,s)))

    def test_snapshot_revision_and_changed_text_invalidate_old_request(self):
        request,raw=self.inspect()
        later=replace(self.snap,head='b'*40)
        with self.assertRaises(AnchorError):self.cat.assert_snapshot(later)
        with self.assertRaises(AnchorError):p.resolve_inspection(Catalogue(later),request,raw)
        changed=replace(self.snap,sources=(source('memory/a.md','changed'),self.snap.sources[1]))
        with self.assertRaises(AnchorError):p.resolve_inspection(Catalogue(changed),request,raw)

    def test_model_payload_and_schema_are_copies_not_mutable_catalogue_state(self):
        request,raw=self.inspect();before=request.sha256
        request.payload['data']['sources'].clear();request.schema['properties'].clear()
        self.cat.model_source(self.a)['lines'][0][1]='changed'
        self.assertEqual(request.sha256,before)
        self.assertEqual(len(p.resolve_inspection(self.cat,request,raw)['legacy']['covered']),2)

    def test_catalogue_fields_and_bindings_are_immutable(self):
        with self.assertRaises(FrozenInstanceError):self.cat.sha256='changed'
        with self.assertRaises(TypeError):self.cat._sources[self.a]=self.snap.original

    def test_inspect_excludes_original_and_cannot_skip_or_add_source(self):
        request,raw=self.inspect();a=json.loads(raw)
        for kind in ('missing','original','unknown','quote'):
            b=json.loads(raw)
            if kind=='missing':b['covered'].pop(self.a)
            elif kind=='original':b['covered'][self.cat.original_id]='l1'
            elif kind=='unknown':b['covered']['madeup']='l1'
            else:b['quote']='model text is not accepted'
            with self.subTest(kind=kind),self.assertRaises(AnchorError):
                p.resolve_inspection(self.cat,request,json.dumps(b))
        self.assertFalse(p.resolve_inspection(self.cat,request,raw)['semantic_correctness_proven'])

    def test_duplicate_json_keys_nonfinite_and_bad_utf8_are_rejected(self):
        request,raw=self.inspect()
        duplicate=raw.replace('"'+self.a+'": "l1"','"'+self.a+'": "l1", "'+self.a+'": "l1"')
        self.assertNotEqual(duplicate,raw)
        for bad in (duplicate,'{"x":NaN}','\ud800','not json'):
            with self.assertRaises(AnchorError):p.resolve_inspection(self.cat,request,bad)

    def test_reference_outside_inspection_scope_is_rejected_even_if_catalogued(self):
        request,raw=self.inspect(['memory/a.md']);a=json.loads(raw)
        a['findings']=[{'text':'claim','evidence':[{'source_id':self.b,'anchor_id':'l1'}]}]
        with self.assertRaises(AnchorError):p.resolve_inspection(self.cat,request,json.dumps(a))

    def test_findings_need_nonempty_valid_unique_evidence_and_safe_text(self):
        request,raw=self.inspect()
        for evidence,text in [([], 'claim'),([{'source_id':self.a,'anchor_id':'l999'}],'claim'),
            ([{'source_id':self.a,'anchor_id':'l1'}]*2,'claim'),
            ([{'source_id':self.a,'anchor_id':'l1'}],'sk-'+'x'*30)]:
            a=json.loads(raw);a['findings']=[{'text':text,'evidence':evidence}]
            with self.assertRaises(ValueError):p.resolve_inspection(self.cat,request,json.dumps(a))

    def test_truncated_input_or_tampered_schema_cannot_be_relabelled_as_same_request(self):
        request,raw=self.inspect()
        for kind in ('payload','schema'):
            data=json.loads(request.envelope_json)
            if kind=='payload':data['payload']['data']['sources'][0]['lines'].pop()
            else:data['schema']['additionalProperties']=True
            with self.assertRaises(AnchorError):
                p.resolve_inspection(self.cat,p.Request(canonical_json(data)),raw)

    def test_synthesis_needs_complete_nonduplicate_inspections(self):
        request,raw=self.inspect(['memory/a.md'])
        with self.assertRaisesRegex(AnchorError,'incomplete'):p.synthesis_request(self.cat,[(request,raw)])
        with self.assertRaisesRegex(AnchorError,'duplicate'):p.synthesis_request(self.cat,[(request,raw)]*2)

    def test_multiple_batches_keep_all_sources_and_findings(self):
        ra,a=self.inspect(['memory/a.md']);rb,b=self.inspect(['memory/b.md'])
        result=p.synthesis_request(self.cat,[(ra,a),(rb,b)])
        self.assertEqual(len(result.payload['data']['evidence_catalogue']),2)
        self.assertEqual(p.validate_synthesis(self.cat,result,self.output(result),self.snap),ORIGINAL)

    def test_synthesis_prose_capitalization_does_not_modify_resolved_quote(self):
        findings=[{'text':'Kontrola audio obnovy.','evidence':[{'source_id':self.a,'anchor_id':'l2'}]}]
        request=self.synth(findings=findings)
        rows=[{'text':ORIGINAL.strip(),'status':'unchanged','evidence':[]},
              {'text':'Restart aplikace nikdy sám nezapne mikrofon;','status':'unverified',
               'evidence':[{'source_id':self.a,'anchor_id':'l2'}]}]
        raw=self.output(request,rows);resolved=p.resolve_synthesis(self.cat,request,raw)
        self.assertTrue(resolved['paragraphs'][1]['text'].startswith('Restart'))
        self.assertTrue(resolved['paragraphs'][1]['evidence'][0]['quote'].startswith('- restart'))
        self.assertIn('[Neověřeno]',p.validate_synthesis(self.cat,request,raw,self.snap))

    def test_synthesis_cannot_cite_anchor_not_forwarded_to_it(self):
        request=self.synth()
        rows=[{'text':ORIGINAL.strip(),'status':'unverified',
               'evidence':[{'source_id':self.a,'anchor_id':'l3'}]}]
        with self.assertRaisesRegex(AnchorError,'verified_findings'):
            p.resolve_synthesis(self.cat,request,self.output(request,rows))

    def test_mutating_allowed_pool_does_not_grant_new_references(self):
        request=self.synth();data=json.loads(request.envelope_json)
        data['allowed_pairs'].append([self.a,'l3'])
        with self.assertRaises(AnchorError):
            p.resolve_synthesis(self.cat,p.Request(canonical_json(data)),self.output(request))

    def test_literal_quality_gate_still_blocks_unregistered_command(self):
        request=self.synth(findings=[{'text':'Příkaz.','evidence':[{'source_id':self.a,'anchor_id':'l3'}]}])
        rows=[{'text':ORIGINAL.strip(),'status':'unchanged','evidence':[]},
              {'text':'git status','status':'unverified','evidence':[{'source_id':self.a,'anchor_id':'l3'}]}]
        with self.assertRaises(q.QualityError) as error:
            p.validate_synthesis(self.cat,request,self.output(request,rows),self.snap)
        self.assertEqual(error.exception.code,'unregistered_command')

    def test_history_cannot_be_promoted_to_current_by_an_anchor(self):
        snap=replace(self.snap,sources=(replace(self.snap.sources[0],authority='historical_or_mixed'),self.snap.sources[1]))
        c=Catalogue(snap);r=p.inspection_request(c,tuple(s.path for s in snap.sources))
        raw=self.response(r);s=p.synthesis_request(c,[(r,raw)])
        rows=[{'text':ORIGINAL.strip(),'status':'unchanged','evidence':[]},
              {'text':'Historické nastavení.','status':'documented','evidence':[{'source_id':self.a,'anchor_id':'l1'}]}]
        with self.assertRaises(q.QualityError) as error:p.validate_synthesis(c,s,self.output(s,rows),snap)
        self.assertEqual(error.exception.code,'history_as_current')

    def test_schema_has_no_quote_field_and_refuses_excessive_source_enum(self):
        request,_=self.inspect();schema=request.schema
        self.assertEqual(set(schema['properties']['covered']['properties']),set(self.cat.document_ids))
        self.assertNotIn('quote',canonical_json(schema))
        many=replace(self.snap,sources=tuple(source(f'memory/{i}.md','line') for i in range(p.MAX_SCHEMA_SOURCES)))
        cat=Catalogue(many)
        with self.assertRaisesRegex(AnchorError,'unsupported'):
            p.inspection_request(cat,tuple(s.path for s in many.sources))


if __name__=='__main__':unittest.main()
