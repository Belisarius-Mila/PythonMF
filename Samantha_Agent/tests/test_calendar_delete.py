from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import threading
import unittest
from unittest.mock import Mock, patch

from app.calendar_delete import CalendarDeletion, CalendarDeleteHelper, event_summary
from app.calendar_access_pilot import CalendarPilotError
from app.file_persistence import FileLockTimeoutError

EVENT={'calendar_id':'private','title':'Káva','start':'2026-11-11T09:00:00Z','end':'2026-11-11T10:00:00Z','all_day':False}
IDENTITY={'event_id':'native-event','item_id':'native-item','fingerprint':'a'*64,'recurring':False}


class CalendarDeleteTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()/'deletes';self.now=datetime(2026,11,8,12,tzinfo=timezone.utc)
        self.selection={'revision':4,'read_calendar_ids':['private'],'target_calendar_id':'private',
                        'calendars':[{'id':'private','title':'Osobní','writable':True}]}
        self.calendar=Mock();self.calendar.snapshot.side_effect=lambda:deepcopy(self.selection)
        self.helper=Mock();self.helper.transact.side_effect=self.native
        self.calls=[];self.refreshed=[];self.result='deleted_verified'
        self.service=CalendarDeletion(self.root,calendar=self.calendar,helper=self.helper,clock=lambda:self.now,on_deleted=lambda:self.refreshed.append(True))

    def native(self,operation,event,**kwargs):
        self.calls.append((operation,deepcopy(event),deepcopy(kwargs)))
        return {'status':'preview' if operation=='inspect' else self.result,'identity':deepcopy(IDENTITY)}

    def prepare(self,event=None):return self.service.execute({'action':'prepare','event':event or EVENT})
    def action(self,action,request_id):
        return self.service.execute({'action':action,'request_id':request_id,**({} if action=='status' else {'confirmed':True})})

    def test_prepare_only_reads_and_keeps_native_identity_server_side(self):
        p=self.prepare();self.assertEqual(p['state'],'prepared');self.assertEqual(self.calls[0][0],'inspect')
        self.assertNotIn('identity',p);self.assertNotIn('native-event',json.dumps(p));self.assertEqual(self.refreshed,[])
        self.assertEqual(self.service._read(self.service._path(p['request_id']))['identity'],IDENTITY)

    def test_exact_confirmation_deletes_once_and_replay_is_read_only(self):
        p=self.prepare();done=self.action('delete',p['request_id']);self.assertEqual(done['state'],'deleted')
        for action in ['delete','status','recover']:self.assertEqual(self.action(action,p['request_id'])['state'],'deleted')
        self.assertEqual([r[0] for r in self.calls],['inspect','delete']);self.assertEqual(self.refreshed,[True])
        self.assertEqual(self.calls[-1][2],{'operation_id':p['request_id'],'identity':IDENTITY})

    def test_concurrent_confirmations_cannot_enter_native_delete_twice(self):
        p=self.prepare();entered=threading.Event();release=threading.Event();results=[]
        def native(operation,event,**kwargs):
            self.calls.append((operation,event,kwargs));entered.set();release.wait(5);return {'status':'deleted_verified'}
        self.helper.transact.side_effect=native
        thread=threading.Thread(target=lambda:results.append(self.action('delete',p['request_id'])),daemon=True);thread.start()
        try:
            self.assertTrue(entered.wait(3))
            with self.assertRaises(FileLockTimeoutError):self.action('delete',p['request_id'])
        finally:release.set();thread.join(5)
        self.assertEqual(results[0]['state'],'deleted');self.assertEqual([r[0] for r in self.calls],['inspect','delete'])

    def test_multiline_task_title_keeps_exact_text(self):
        event=EVENT|{'title':'Vyzvednout balík\nPošta Vodičkova'}
        p=self.prepare(event);self.assertEqual(p['event']['title'],event['title'])

    def test_no_mutation_before_durable_claim(self):
        p=self.prepare()
        def call(operation,event,**kwargs):
            self.assertEqual(self.service._read(self.service._path(p['request_id']))['state'],'pending')
            return {'status':'deleted_verified'}
        self.helper.transact.side_effect=call
        self.assertEqual(self.action('delete',p['request_id'])['state'],'deleted')

    def test_failed_claim_never_calls_native_delete(self):
        p=self.prepare()
        with patch.object(self.service,'_save',side_effect=OSError('disk')):
            with self.assertRaises(OSError):self.action('delete',p['request_id'])
        self.assertEqual([r[0] for r in self.calls],['inspect'])

    def test_unknown_send_never_repeats_delete_and_only_recovers_original(self):
        p=self.prepare();self.helper.transact.side_effect=TimeoutError('unknown')
        self.assertEqual(self.action('delete',p['request_id'])['state'],'unknown')
        self.helper.transact.reset_mock();self.helper.transact.side_effect=self.native
        self.assertEqual(self.action('delete',p['request_id'])['state'],'unknown');self.helper.transact.assert_not_called()
        self.assertEqual(self.action('recover',p['request_id'])['state'],'deleted')
        self.assertEqual(self.calls[-1][0],'recover_delete');self.assertEqual(self.calls[-1][2]['operation_id'],p['request_id'])

    def test_restart_preserves_unknown_without_new_mutation(self):
        p=self.prepare();self.result='delete_unknown';self.action('delete',p['request_id'])
        other=CalendarDeletion(self.root,calendar=self.calendar,helper=self.helper,clock=lambda:self.now)
        self.assertEqual(other.execute({'action':'status','request_id':p['request_id']})['state'],'unknown')
        self.assertEqual(other.execute({'action':'delete','request_id':p['request_id'],'confirmed':True})['state'],'unknown')
        self.assertEqual([r[0] for r in self.calls],['inspect','delete'])

    def test_recovery_access_loss_keeps_original_uncertainty_open(self):
        p=self.prepare();self.result='delete_unknown';self.action('delete',p['request_id'])
        for result in ['authorization_required','calendar_unavailable']:
            self.result=result;self.assertEqual(self.action('recover',p['request_id'])['state'],'unknown')
        self.result='deleted_verified';self.assertEqual(self.action('recover',p['request_id'])['state'],'deleted')
        self.assertEqual([r[0] for r in self.calls].count('delete'),1)

    def test_expired_preview_or_changed_selection_never_mutates(self):
        for kind in ['expiry','revision','readonly','unselected']:
            with self.subTest(kind=kind):
                self.setUp();p=self.prepare()
                if kind=='expiry':self.now+=timedelta(minutes=6)
                if kind=='revision':self.selection['revision']+=1
                if kind=='readonly':self.selection['calendars'][0]['writable']=False
                if kind=='unselected':self.selection.update(read_calendar_ids=[],target_calendar_id='')
                self.assertEqual(self.action('delete',p['request_id'])['state'],'changed')
                self.assertEqual([r[0] for r in self.calls],['inspect'])

    def test_changed_event_permission_and_invitation_block(self):
        for status in ['changed','unsupported','calendar_unavailable']:
            self.helper.transact.return_value={'status':status};self.helper.transact.side_effect=None
            with self.assertRaises(ValueError):self.prepare()
        self.assertEqual(self.refreshed,[])

    def test_native_final_guard_change_does_not_trigger_another_delete(self):
        p=self.prepare();self.result='changed'
        self.assertEqual(self.action('delete',p['request_id'])['state'],'changed')
        self.action('delete',p['request_id']);self.assertEqual([r[0] for r in self.calls],['inspect','delete'])

    def test_setup_is_explicit_and_separate_from_prepare(self):
        self.helper._build_info.side_effect=CalendarPilotError('missing')
        self.assertEqual(self.prepare()['state'],'setup_required');self.helper.build.assert_not_called();self.helper.authorize_current.assert_not_called()
        with self.assertRaises(ValueError):self.service.execute({'action':'authorize','confirmed':False})
        self.service.execute({'action':'authorize','confirmed':True})
        self.helper.build.assert_called_once_with(confirmed=True);self.helper.authorize_current.assert_called_once_with(confirmed=True)

    def test_no_confirmation_extra_fields_or_client_identity_can_delete(self):
        p=self.prepare()
        for payload in [{'action':'delete','request_id':p['request_id']},{'action':'delete','request_id':p['request_id'],'confirmed':False},
                        {'action':'delete','request_id':p['request_id'],'confirmed':True,'identity':IDENTITY},
                        {'action':'delete','request_id':'../other','confirmed':True},{'action':'delete_all','confirmed':True}]:
            with self.assertRaises(ValueError):self.service.execute(payload)
        self.assertEqual([r[0] for r in self.calls],['inspect'])

    def test_invalid_summary_stops_before_native_read(self):
        for changes in [{'all_day':1},{'title':''},{'title':'a\x00other'},{'end':EVENT['start']},{'extra':'field'},{'calendar_id':'other'}]:
            with self.assertRaises(ValueError):self.prepare(EVENT|changes)
        self.assertEqual(self.calls,[])

    def test_symlink_state_cannot_redirect_delete(self):
        p=self.prepare();path=self.service._path(p['request_id']);target=path.with_name('other.json');target.write_text('{}')
        other=self.root/('b'*32);other.mkdir();(other/'state.json').symlink_to(target)
        with self.assertRaises(ValueError):self.action('delete','b'*32)
        self.assertEqual([r[0] for r in self.calls],['inspect'])

    def test_read_status_never_connects_or_creates_new_record(self):
        with self.assertRaises(ValueError):self.action('status','c'*32)
        self.helper.transact.assert_not_called()
        self.assertFalse(self.root.exists())

    def test_refresh_failure_cannot_change_known_deleted_result(self):
        self.service.on_deleted=Mock(side_effect=OSError('refresh'));p=self.prepare()
        self.assertEqual(self.action('delete',p['request_id'])['state'],'deleted')
        self.assertEqual(self.action('delete',p['request_id'])['state'],'deleted')


class CalendarDeleteHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
        self.helper=CalendarDeleteHelper(self.root);self.helper._build_info=Mock(return_value=({},None,Path('/fake-helper')))
        self.helper._run=Mock(side_effect=self.command);self.change={};self.no_response=False
    def command(self,args):
        if 'submit' in args:
            path=Path(args[-1]);request=json.loads(path.read_text())
            if not self.no_response:
                value={**request,'expected':request['event'],'parent_pid':1,'bundle_identifier':self.helper.bundle_id,'authorization':'full_access',
                       'calendar_writes':request['operation']=='delete','status':'preview' if request['operation']=='inspect' else 'deleted_verified',
                       'identity':IDENTITY}|self.change
                (path.parent/'response.json').write_text(json.dumps(value))
        return ''
    def test_inspect_delete_and_recover_are_exact_bound_operations(self):
        self.assertEqual(self.helper.transact('inspect',EVENT)['identity'],IDENTITY)
        for op in ['delete','recover_delete']:
            self.change={'calendar_writes':op=='delete'}
            self.assertEqual(self.helper.transact(op,EVENT,operation_id='a'*32,identity=IDENTITY)['status'],'deleted_verified')
    def test_foreign_or_mutating_read_receipts_are_rejected(self):
        for change in [{'calendar_writes':True},{'expected':EVENT|{'title':'other'}},{'parent_pid':9},
                       {'bundle_identifier':'foreign'},{'identity':IDENTITY|{'fingerprint':'bad'}},{'authorization':'denied'}]:
            self.change=change
            with self.assertRaises(CalendarPilotError):self.helper.transact('inspect',EVENT)
    def test_recovery_cannot_claim_a_write_or_different_identity(self):
        for change in [{'calendar_writes':True},{'identity':IDENTITY|{'event_id':'other'}},{'operation_id':'b'*32}]:
            self.change=change
            with self.assertRaises(CalendarPilotError):self.helper.transact('recover_delete',EVENT,operation_id='a'*32,identity=IDENTITY)
    def test_timeout_never_resubmits_native_process(self):
        self.no_response=True
        with patch.object(self.helper,'_write',side_effect=lambda p,v:p.write_text(json.dumps(v))), patch('app.calendar_delete.time.monotonic',side_effect=[0,26]):
            with self.assertRaises(CalendarPilotError):self.helper.transact('delete',EVENT,operation_id='a'*32,identity=IDENTITY)
        self.assertEqual(sum('submit' in call.args[0] for call in self.helper._run.call_args_list),1)


@unittest.skipUnless(sys.platform=='darwin','Native Swift transaction harness requires macOS frameworks')
class CalendarDeleteNativeTests(unittest.TestCase):
    def test_production_transaction_logic_against_in_memory_eventkit(self):
        # Compile the actual native implementation against a fake EventKit API.
        # This exercises journals, changing identities, recurring span, duplicates,
        # invitations and uncertain removals without opening a calendar database.
        with tempfile.TemporaryDirectory(prefix='calendar-delete-native-test-') as temp:
            root=Path(temp).resolve()
            source=Path('scripts/calendar_delete.swift').read_text()
            core=source.split('\ndo {\n    let args=')[0].replace('import EventKit\n','')
            core='enum NativeTestError: Error { case invalid(Int) }\n'+core.replace('throw DeleteError.invalid','throw NativeTestError.invalid(#line)')
            fake=Path('tests/calendar_delete_fake_eventkit.swift').read_text()
            code=core+'\n'+fake+'\ndo { try runCalendarDeleteHarness(URL(fileURLWithPath:CommandLine.arguments[1])) } catch { fputs("native_harness_failed: \\(error)\\n",stderr);exit(2) }\n'
            path=root/'test.swift';path.write_text(code);binary=root/'test'
            compiled=subprocess.run(['/usr/bin/xcrun','swiftc','-swift-version','5',str(path),'-framework','AppKit','-o',str(binary)],capture_output=True,text=True,timeout=180)
            self.assertEqual(compiled.returncode,0,compiled.stderr)
            result=subprocess.run([str(binary),str(root/'state')],capture_output=True,text=True,timeout=25)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('15 PASS; real calendar access: false',result.stdout)
