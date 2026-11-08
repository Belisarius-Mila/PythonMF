import json
import re
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import urlopen
from unittest.mock import patch

from app import cockpit


class CockpitHomeScreenTests(unittest.TestCase):
    def setUp(self):
        self.server=ThreadingHTTPServer(('127.0.0.1',0),cockpit.CockpitServer().make_handler())
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.shutdown)
        self.base=f'http://127.0.0.1:{self.server.server_port}'
    def shutdown(self):self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)
    def get(self,path):
        try:r=urlopen(self.base+path,timeout=5)
        except HTTPError as exc:r=exc
        with r:return r.status,r.read(),dict(r.headers)

    def manifest_for(self,page):
        code,body,_=self.get(page);self.assertEqual(code,200)
        links=re.findall(r'<link rel="manifest" href="([^"]+)"',body.decode())
        self.assertEqual(len(links),1)
        code,raw,headers=self.get(links[0]);self.assertEqual(code,200)
        self.assertEqual(headers['Content-Type'],'application/manifest+json');self.assertIn('no-store',headers['Cache-Control'])
        data=json.loads(raw)
        return {**data,'effective_id':urljoin(self.base+links[0],data['id']),
                'effective_start':urljoin(self.base+links[0],data['start_url'])}

    def test_main_installed_from_calendar_still_starts_at_cockpit(self):
        home=self.manifest_for('/');calendar=self.manifest_for('/calendar/')
        self.assertEqual(home,calendar)
        self.assertEqual(home['effective_start'],self.base+'/');self.assertEqual(home['effective_id'],self.base+'/')
        self.assertEqual(home['display'],'standalone')

    def test_task_and_main_are_distinct_apps_and_keep_existing_task_identity(self):
        main=self.manifest_for('/');task=self.manifest_for('/calendar/task/')
        self.assertNotEqual(main['effective_id'],task['effective_id'])
        self.assertEqual(task['effective_id'],self.base+'/calendar/task/')
        self.assertEqual(task['effective_start'],self.base+'/calendar/task/')
        self.assertEqual(task['scope'],'/calendar/task/');self.assertNotEqual(main['name'],task['name'])

    def test_install_metadata_never_redirects_or_calls_calendar_mutations(self):
        with patch('app.cockpit_calendar_tasks.TASKS.execute') as create,patch('app.cockpit_calendar_delete.DELETIONS.execute') as delete:
            for page in ['/','/calendar/','/calendar/task/']:
                code,body,headers=self.get(page);self.assertEqual(code,200);self.assertNotIn('Location',headers)
            create.assert_not_called();delete.assert_not_called()

    def test_manifest_cannot_choose_a_destination_from_query(self):
        for path in ['/cockpit.webmanifest?start_url=/calendar/task/','/calendar/task/manifest.webmanifest?entry=main']:
            code,body,headers=self.get(path);self.assertEqual(code,400);self.assertFalse(json.loads(body)['ok']);self.assertNotIn('Location',headers)
