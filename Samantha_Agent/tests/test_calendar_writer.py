import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch

from app.calendar_writer import CalendarWriter
from app.calendar_access_pilot import CalendarPilotError, _sha

EVENT={'operation_id':'00000000-0000-4000-8000-000000000001','calendar_id':'private-target','title':'Test',
       'start':'2026-11-11T09:00:00+00:00','end':'2026-11-11T10:00:00+00:00','time_zone':'Europe/Prague',
       'all_day':False,'location':'','join_url':'','reminders':[1440,60]}


class CalendarWriterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.calls=[];self.change={}
        self.writer=CalendarWriter(self.root,runner=self.run_command)
        app=self.root/'Writer.app';binary=app/'Contents/MacOS/CalendarWriter';binary.parent.mkdir(parents=True)
        binary.write_bytes(b'synthetic');info=app/'Contents/Info.plist';info.write_bytes(b'info')
        (self.root/'build.json').write_text(json.dumps({'app':str(app),'binary_sha256':_sha(binary),'info_sha256':_sha(info),'source_sha256':_sha(self.writer.source)}))

    def run_command(self,args,**kwargs):
        args=list(map(str,args));self.calls.append(args)
        if args[:2]==['/bin/launchctl','submit']:
            path=Path(args[-1]);request=json.loads(path.read_text());event=request['event']
            result={'schema':1,'operation':request['operation'],'request_id':request['request_id'],
                    'bundle_identifier':self.writer.bundle_id,'parent_pid':1,'operation_id':event['operation_id'],'expected':event,
                    'authorization':'full_access','calendar_writes':request['operation']=='create','status':'saved_verified',
                    'event':{**event,'event_id':'native-id','marker':'Samantha event: '+event['operation_id']},**deepcopy(self.change)}
            (path.parent/'response.json').write_text(json.dumps(result))
        return subprocess.CompletedProcess(args,0,'','')

    def test_create_uses_own_signed_build_exact_event_and_native_service_context(self):
        result=self.writer.execute_event(EVENT,confirmed=True)
        self.assertEqual(result['status'],'saved_verified')
        self.assertEqual(len([c for c in self.calls if c[:2]==['/bin/launchctl','submit']]),1)
        self.assertEqual(len([c for c in self.calls if c[:2]==['/bin/launchctl','remove']]),1)
        self.assertFalse(any('/usr/bin/open' in c or 'swiftc' in c for c in self.calls))

    def test_recovery_is_read_only_and_cannot_accept_writing_response(self):
        self.assertEqual(self.writer.execute_event(EVENT,confirmed=True,recover=True)['operation'],'recover')
        self.change={'calendar_writes':True}
        with self.assertRaises(CalendarPilotError):self.writer.execute_event(EVENT,confirmed=True,recover=True)

    def test_wrong_identity_context_and_readback_alarm_mismatch_fail(self):
        for change in ({'parent_pid':99},{'operation_id':'foreign'},{'expected':{}},{'bundle_identifier':'foreign'},
                       {'event':{**EVENT,'event_id':'native-id','marker':'Samantha event: '+EVENT['operation_id'],'reminders':[60]}}):
            self.change=change
            with self.subTest(change=change),self.assertRaises(CalendarPilotError):self.writer.execute_event(EVENT,confirmed=True)

    def test_confirmation_and_binary_hash_required_before_submit(self):
        with self.assertRaises(CalendarPilotError):self.writer.execute_event(EVENT)
        _,_,binary=self.writer._build_info();binary.write_bytes(b'changed')
        with self.assertRaises(CalendarPilotError):self.writer.execute_event(EVENT,confirmed=True)
        self.assertEqual(self.calls,[])

    def test_native_source_has_one_create_and_durable_claim_before_save(self):
        source=self.writer.source.read_text()
        self.assertEqual(source.count('store.save('),1)
        self.assertIn('if exists || operation == "recover"',source)
        self.assertLess(source.index('fsync(journalFD)'),source.index('store.save('))
        for api in ('store.remove(', 'EKReminder(', 'event.attendees =', 'reset('):self.assertNotIn(api,source)
        self.assertIn('EKAlarm(relativeOffset:',source)
