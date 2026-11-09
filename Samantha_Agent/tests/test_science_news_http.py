import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from app import cockpit
from app.science_news import ScienceNews, identity
from tests.test_science_news import item


class ScienceHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=ScienceNews(Path(self.temp.name)/'news',Path(self.temp.name)/'archive')
        self.store.publish('fixture',[item()],available_at='2026-01-02T12:00:00+00:00')
        self.worker_patch=patch('app.cockpit_science_news.ScienceNews',return_value=self.store)
        self.worker_patch.start();self.addCleanup(self.worker_patch.stop)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),cockpit.CockpitServer().make_handler())
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.stop)
        self.host=f'127.0.0.1:{self.server.server_port}'

    def stop(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)

    def request(self,path,body=None,origin=None):
        conn=HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        headers={}
        if body is not None:
            headers={'Content-Type':'application/json','Origin':origin or 'http://'+self.host}
        conn.request('GET' if body is None else 'POST',path,body=None if body is None else json.dumps(body),headers=headers)
        response=conn.getresponse();result=(response.status,response.read().decode());conn.close();return result

    def test_science_news_decision_http_and_reconnect_receipt(self):
        status,body=self.request('/api/science-news')
        self.assertEqual(status,200);self.assertEqual(json.loads(body)['pending_count'],1)
        payload={'item_id':identity(item()),'action':'save','request_id':'same_request'}
        for _ in range(2):
            status,body=self.request('/api/science-news/decision',payload)
            self.assertEqual(status,200);self.assertTrue(json.loads(body)['ok'])
        self.assertEqual(json.loads(self.request('/api/science-news')[1])['pending_count'],0)
        self.assertEqual(len(list((self.store.archive_root/'articles').iterdir())),1)

    def test_foreign_origin_cannot_decide(self):
        self.assertEqual(self.request('/api/science-news/decision',{'item_id':identity(item()),'action':'dismiss','request_id':'one'},origin='https://other.example.org')[0],403)
        self.assertEqual(self.store.overview()['pending_count'],1)

    def test_science_news_translation_is_inactive_without_any_model(self):
        with patch('app.cockpit_science_news.call_model') as model:
            status,body=self.request('/api/science-news/translate',{'item_id':identity(item())})
            self.assertEqual(status,200);self.assertFalse(json.loads(body)['ok']);model.assert_not_called()
        self.assertEqual(self.store._read()['jobs'],{})

    def test_translation_window_is_read_only_and_pollable(self):
        before=self.store.path.read_bytes()
        status,body=self.request('/science-news/translation?id='+identity(item()))
        self.assertEqual(status,200);self.assertIn('Český překlad',body)
        self.assertNotIn('method:',body)
        status,body=self.request('/api/science-news/translation?id='+identity(item()))
        self.assertEqual(json.loads(body)['state'],'not_started')
        self.assertEqual(before,self.store.path.read_bytes())

    def test_science_news_unfollow_is_explicit_and_registered(self):
        news=identity(item());self.store.decide(news,'follow','one')
        status,body=self.request('/api/science-news/unfollow',{'topic_id':news})
        self.assertEqual(status,200);self.assertTrue(json.loads(body)['ok'])
        self.assertFalse(self.store.overview()['follows'][0]['active'])
        paths={i['path'] for i in cockpit.COCKPIT_POST_ACTIONS}
        self.assertTrue({'/api/science-news/decision','/api/science-news/translate','/api/science-news/unfollow'}<=paths)
