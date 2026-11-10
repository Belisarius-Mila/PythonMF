from copy import deepcopy
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock,patch

from app.calendar_edit import CalendarEditing
from app.calendar_access_pilot import CalendarPilotError
from app.calendar_edit_helper import CalendarEditHelper
from app.file_persistence import FileLockTimeoutError

EVENT={'calendar_id':'private','title':'Káva','start':'2026-11-11T09:00:00+00:00','end':'2026-11-11T10:00:00+00:00','all_day':False}
IDENTITY={'event_id':'native-event','item_id':'native-item','fingerprint':'a'*64,'recurring':False}
CHANGES={'title':'Upravená káva','date':'2026-11-12','time':'11:30'}


class CalendarEditTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.base=Path(tmp.name).resolve();self.root=self.base/'calendar_edits'
        self.now=datetime(2026,11,9,tzinfo=timezone.utc)
        self.selection={'ready':True,'revision':4,'calendars':[{'id':'private','writable':True}],
                        'read_calendar_ids':['private'],'target_calendar_id':'private','events':[deepcopy(EVENT)]}
        self.calendar=Mock();self.calendar.snapshot.side_effect=lambda:deepcopy(self.selection)
        self.helper=Mock();self.helper.transact.side_effect=self.native
        self.calls=[];self.refreshed=[];self.result='edited_verified'
        self.service=CalendarEditing(self.root,calendar=self.calendar,helper=self.helper,clock=lambda:self.now,on_saved=lambda *args:self.refreshed.append(args))

    def native(self,op,event,**kwargs):
        self.calls.append((op,deepcopy(event),deepcopy(kwargs)))
        if op=='inspect':return {'status':'preview','identity':deepcopy(IDENTITY),'calendar_title':'Osobní',
            'timezone':'Europe/Prague','start_day':'2026-11-11','end_day':'2026-11-11'}
        self.assertEqual(self.service._read()['items'][kwargs['operation_id']]['state'],'pending' if op=='update' else 'unknown')
        return {'status':self.result,'event':kwargs['replacement']}

    def prepare(self,event=None):return self.service.execute({'action':'prepare','event':event or EVENT})
    def action(self,action,request_id,**more):
        return self.service.execute({'action':action,'request_id':request_id,**({'confirmed':True} if action!='status' else {}),**more})
    def update(self,p,changes=None):return self.action('update',p['request_id'],changes=changes or CHANGES)

    def test_prepare_only_reads_and_prepopulates_original_local_time(self):
        p=self.prepare();self.assertEqual(p['state'],'prepared');self.assertEqual(p['form'],{'title':'Káva','date':'2026-11-11','time':'10:00'})
        self.assertNotIn('identity',p);self.assertNotIn('native-event',json.dumps(p));self.assertEqual([c[0] for c in self.calls],['inspect'])

    def test_verified_edit_preserves_duration_target_and_only_one_update(self):
        p=self.prepare();v=self.update(p)
        self.assertEqual(v['state'],'verified');self.assertEqual(v['event']['title'],CHANGES['title'])
        start=datetime.fromisoformat(v['event']['start']);end=datetime.fromisoformat(v['event']['end'])
        self.assertEqual(start.hour,10);self.assertEqual(end-start,timedelta(hours=1));self.assertEqual(v['event']['calendar_id'],'private')
        for action in ['update','recover','status']:
            args={'changes':CHANGES} if action=='update' else {}
            self.assertEqual(self.action(action,p['request_id'],**args)['state'],'verified')
        self.assertEqual([c[0] for c in self.calls],['inspect','update']);self.assertEqual(len(self.refreshed),1)

    def test_unknown_edit_is_never_repeated_even_by_new_prepare_or_restart(self):
        p=self.prepare();self.result='edit_unknown';self.assertEqual(self.update(p)['state'],'unknown')
        self.assertEqual(self.prepare()['request_id'],p['request_id']);self.assertEqual(self.update(p)['state'],'unknown')
        other=CalendarEditing(self.root,calendar=self.calendar,helper=self.helper,clock=lambda:self.now)
        self.assertEqual(other.execute({'action':'current'})['request_id'],p['request_id'])
        self.assertEqual(other.execute({'action':'status','request_id':p['request_id']})['state'],'unknown')
        self.result='edited_verified';self.assertEqual(self.action('recover',p['request_id'])['state'],'verified')
        self.assertEqual([c[0] for c in self.calls],['inspect','update','recover_update'])

    def test_timeout_permission_loss_and_recovery_keep_original_identity(self):
        p=self.prepare();self.helper.transact.side_effect=TimeoutError();self.assertEqual(self.update(p)['state'],'unknown')
        self.helper.transact.side_effect=self.native
        for result in ['authorization_required','calendar_unavailable','changed']:
            self.result=result;self.assertEqual(self.action('recover',p['request_id'])['state'],'unknown')
        self.assertEqual([c[0] for c in self.calls].count('update'),0)

    def test_changed_or_expired_preview_never_mutates(self):
        for change in ['revision','expiry','readonly','missing','stale','duplicate']:
            with self.subTest(change=change):
                self.setUp();p=self.prepare()
                if change=='revision':self.selection['revision']+=1
                elif change=='expiry':self.now+=timedelta(minutes=11)
                elif change=='readonly':self.selection['calendars'][0]['writable']=False
                elif change=='missing':self.selection['events']=[]
                elif change=='stale':self.selection['ready']=False
                elif change=='duplicate':self.selection['events'].append(deepcopy(EVENT))
                self.assertEqual(self.update(p)['state'],'changed');self.assertEqual([c[0] for c in self.calls],['inspect'])

    def test_unknown_recovery_exposes_permission_repair_without_repeating_update(self):
        p=self.prepare();self.result='edit_unknown';self.update(p)
        self.result='authorization_required'
        response=self.action('recover',p['request_id'])
        self.assertEqual(response['state'],'unknown')
        self.assertTrue(response['needs_authorization'])
        self.assertTrue(self.service.execute({'action':'current'})['needs_authorization'])
        self.service.execute({'action':'authorize','confirmed':True})
        self.result='edited_verified'
        response=self.action('recover',p['request_id'])
        self.assertEqual(response['state'],'verified')
        self.assertFalse(response['needs_authorization'])
        self.assertEqual([c[0] for c in self.calls].count('update'),1)

    def test_invalid_changes_and_dst_fail_before_update(self):
        p=self.prepare()
        for changes in [CHANGES|{'title':''},CHANGES|{'date':'2026-02-30'},CHANGES|{'time':'25:00'},
                        CHANGES|{'date':'2027-03-28','time':'02:30'},CHANGES|{'date':'2027-10-31','time':'02:30'},
                        CHANGES|{'calendar_id':'other'},CHANGES|{'title':'bad\x00'}]:
            self.assertIn('validation_error',self.update(p,changes))
        self.assertEqual([c[0] for c in self.calls],['inspect'])

    def test_all_day_duration_keeps_local_days_across_dst(self):
        row={'event':EVENT|{'all_day':True},'timezone':'Europe/Prague','start_day':'2026-03-27','end_day':'2026-03-29'}
        result=self.service._replacement(row,CHANGES|{'date':'2027-03-27'})
        self.assertTrue(result['all_day']);start=datetime.fromisoformat(result['start']);end=datetime.fromisoformat(result['end'])
        self.assertEqual(end.date()-start.date(),timedelta(days=2));self.assertEqual((end-start).total_seconds(),47*3600)

    def test_failed_durable_claim_stops_before_native_mutation(self):
        p=self.prepare()
        with patch('app.calendar_edit.save_locked',side_effect=OSError()):
            with self.assertRaises(OSError):self.update(p)
        self.assertEqual([c[0] for c in self.calls],['inspect'])

    def test_two_previews_and_concurrent_confirmations_cannot_update_twice(self):
        a,b=self.prepare(),self.prepare();entered=threading.Event();release=threading.Event();answers=[]
        def blocked(op,event,**kw):
            entered.set();release.wait(5);return {'status':'edited_verified','event':kw['replacement']}
        self.helper.transact.side_effect=blocked
        worker=threading.Thread(target=lambda:answers.append(self.update(a)),daemon=True);worker.start()
        try:
            self.assertTrue(entered.wait(3))
            with self.assertRaises(FileLockTimeoutError):self.update(b)
        finally:release.set();worker.join(5)
        self.assertEqual(answers[0]['state'],'verified');self.helper.transact.assert_called()

    def test_pending_delete_blocks_edit_and_pending_edit_blocks_delete(self):
        directory=self.base/'calendar_deletions'/('a'*32);directory.mkdir(parents=True)
        (directory/'state.json').write_text('{"state":"unknown"}')
        with self.assertRaises(ValueError):self.prepare()
        from app.calendar_mutation_guard import mutation_guard
        self.root.mkdir();(self.root/'state.json').write_text('{"items":{"one":{"state":"unknown"}}}')
        with self.assertRaises(ValueError):
            with mutation_guard(self.base,operation='delete'):pass

    def test_setup_requires_separate_explicit_confirmation(self):
        self.helper._build_info.side_effect=CalendarPilotError('missing')
        self.assertEqual(self.prepare()['state'],'setup_required');self.helper.build.assert_not_called()
        with self.assertRaises(ValueError):self.service.execute({'action':'authorize','confirmed':False})
        self.service.execute({'action':'authorize','confirmed':True});self.helper.build.assert_called_once_with(confirmed=True)

    def test_malformed_requests_never_touch_helper(self):
        for payload in [None,{}, {'action':'update','confirmed':True}, {'action':'prepare','event':EVENT|{'extra':True}},
                        {'action':'status','request_id':'../escape'}]:
            with self.assertRaises(ValueError):self.service.execute(payload)
        self.helper.transact.assert_not_called()


@unittest.skipUnless(sys.platform=='darwin','Swift AppKit harness requires macOS')
class NativeCalendarEditTests(unittest.TestCase):
    def test_production_native_transaction_against_in_memory_eventkit(self):
        with tempfile.TemporaryDirectory(prefix='calendar-edit-native-') as tmp:
            root=Path(tmp).resolve();source=Path('scripts/calendar_edit.swift').read_text()
            core=source.split('\ndo {\n    let args=')[0].replace('import EventKit\n','')
            core='enum NativeEditTestError: Error { case invalid(Int) }\n'+core.replace('throw EditError.invalid','throw NativeEditTestError.invalid(#line)')
            fake=Path('tests/calendar_delete_fake_eventkit.swift').read_text().split('func runCalendarDeleteHarness(')[0]
            harness=Path('tests/calendar_edit_fake_eventkit.swift').read_text()
            code=core+'\n'+fake+'\n'+harness+'\ndo { try runCalendarEditHarness(URL(fileURLWithPath:CommandLine.arguments[1]).resolvingSymlinksInPath()) } catch { fputs("edit_harness_failed: \\(error)\\n",stderr);exit(2) }\n'
            path=root/'test.swift';path.write_text(code);binary=root/'test'
            result=subprocess.run(['/usr/bin/xcrun','swiftc','-swift-version','5',str(path),'-framework','AppKit','-o',str(binary)],capture_output=True,text=True,timeout=180)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary),str(root/'state')],capture_output=True,text=True,timeout=25)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('calendar edit native: PASS; real calendar access: false',result.stdout)


class CalendarEditHelperTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name).resolve()
        self.helper=CalendarEditHelper(self.root);self.helper._build_info=Mock(return_value=({},None,Path('/fake-helper')))
        self.helper._run=Mock(side_effect=self.command);self.change={};self.no_response=False
    def command(self,args):
        if 'submit' in args and not self.no_response:
            path=Path(args[-1]);request=json.loads(path.read_text())
            value={**request,'expected':request['event'],'parent_pid':1,'bundle_identifier':self.helper.bundle_id,'authorization':'full_access',
                   'calendar_writes':request['operation']=='update','status':'preview' if request['operation']=='inspect' else 'edited_verified',
                   'identity':IDENTITY,'event':request['replacement'], 'calendar_title':'Osobní','timezone':'Europe/Prague',
                   'start_day':'2026-11-11','end_day':'2026-11-11'}|self.change
            (path.parent/'response.json').write_text(json.dumps(value))
        return ''
    def test_strict_inspect_update_and_recovery_receipts(self):
        self.assertEqual(self.helper.transact('inspect',EVENT)['identity'],IDENTITY)
        for op in ['update','recover_update']:
            self.assertEqual(self.helper.transact(op,EVENT,operation_id='a'*32,identity=IDENTITY,replacement=EVENT)['status'],'edited_verified')
    def test_mismatched_receipts_and_mutating_reads_rejected(self):
        for change in [{'calendar_writes':True},{'expected':EVENT|{'title':'other'}},{'parent_pid':9},
                       {'bundle_identifier':'foreign'},{'identity':IDENTITY|{'fingerprint':'bad'}},{'authorization':'denied'}]:
            self.change=change
            with self.assertRaises(CalendarPilotError):self.helper.transact('inspect',EVENT)
        for change in [{'calendar_writes':True},{'identity':IDENTITY|{'event_id':'other'}},{'operation_id':'b'*32},
                       {'event':EVENT|{'title':'other'}},{'replacement':EVENT|{'title':'other'}}]:
            self.change=change
            with self.assertRaises(CalendarPilotError):self.helper.transact('recover_update',EVENT,operation_id='a'*32,identity=IDENTITY,replacement=EVENT)
    def test_timeout_submits_only_one_native_process(self):
        self.no_response=True
        with patch.object(self.helper,'_write',side_effect=lambda p,v:p.write_text(json.dumps(v))),patch('app.calendar_edit_helper.time.monotonic',side_effect=[0,26]):
            with self.assertRaises(CalendarPilotError):self.helper.transact('update',EVENT,operation_id='a'*32,identity=IDENTITY,replacement=EVENT)
        self.assertEqual(sum('submit' in call.args[0] for call in self.helper._run.call_args_list),1)
