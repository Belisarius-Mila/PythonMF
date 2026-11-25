from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import base64
import json
import subprocess
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from PIL import Image
import pdfplumber
from app.documents import scan_inbox as scans

def page(color, size=(80, 120)):
    data = BytesIO()
    Image.new('RGB', size, color).save(data, 'JPEG')
    return base64.b64encode(data.getvalue()).decode()

class ScanInbox(unittest.TestCase):

    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.pages = [page('white'), page('blue')]
        self.raw = scans.images_pdf(self.pages)
        self.args = {'scan_id': 'a' * 32, 'title': 'Zkušební dokument', 'raw': self.raw, 'confirmed': True, 'vault_dir': self.root}

    def test_confirmation_order_and_no_ocr_or_final_import(self):
        with self.assertRaises(ValueError):
            scans.save_scan(**{**self.args, 'confirmed': False})
        self.assertEqual(list(self.root.iterdir()), [])
        scans.save_scan(**self.args)
        pdf = scans.resolve_scan('a' * 32, vault_dir=self.root)
        with pdfplumber.open(pdf) as document:
            self.assertEqual(len(document.pages), 2)
        self.assertEqual(scans.list_scans(vault_dir=self.root)[0]['pages'], 2)
        self.assertFalse((self.root / 'vault').exists())

    def test_concurrent_retry_and_conflicting_content(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: scans.save_scan(**self.args), range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(len(scans.list_scans(vault_dir=self.root)), 1)
        with self.assertRaises(ValueError):
            scans.save_scan(**{**self.args, 'raw': scans.images_pdf([page('red')])})

    def test_resume_after_pdf_write(self):
        with patch.object(scans, 'atomic_create_text', side_effect=OSError('disk')):
            with self.assertRaises(OSError):
                scans.save_scan(**self.args)
        self.assertEqual(scans.list_scans(vault_dir=self.root), [])
        scans.save_scan(**self.args)
        self.assertTrue(scans.resolve_scan('a' * 32, vault_dir=self.root).is_file())

    def test_deterministic_render_and_invalid_inputs(self):
        self.assertEqual(self.raw, scans.images_pdf(self.pages))
        for pages in ([], ['!!!'], self.pages * 16):
            with self.assertRaises(ValueError):
                scans.images_pdf(pages)
        for ref in ('../elsewhere', 'z' * 32):
            with self.assertRaises(ValueError):
                scans.save_scan(**{**self.args, 'scan_id': ref})
        with self.assertRaises(ValueError):
            scans.save_scan(**{**self.args, 'raw': b'not a PDF'})
        scans.save_scan(**self.args)
        scans.resolve_scan('a' * 32, vault_dir=self.root).write_bytes(b'%PDF-corrupt')
        with self.assertRaises(ValueError):
            scans.resolve_scan('a' * 32, vault_dir=self.root)

    def test_image_exif_orientation_is_preserved(self):
        data = BytesIO()
        image = Image.new('RGB', (120, 80), 'white')
        exif = Image.Exif()
        exif[274] = 6
        image.save(data, 'JPEG', exif=exif)
        raw = scans.images_pdf([base64.b64encode(data.getvalue()).decode()])
        with pdfplumber.open(BytesIO(raw)) as document:
            self.assertGreater(document.pages[0].height, document.pages[0].width)

class ScanHttp(unittest.TestCase):

    def setUp(self):
        from app import cockpit
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), cockpit.CockpitServer(host='127.0.0.1', port=0).make_handler())
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (self.server.shutdown(), self.server.server_close(), thread.join()))
        self.url = f'http://127.0.0.1:{self.server.server_address[1]}'
        actual_save, actual_list, actual_resolve = (scans.save_scan, scans.list_scans, scans.resolve_scan)
        self.enterContext(patch.object(scans, 'save_scan', side_effect=lambda **kw: actual_save(**{**kw, 'vault_dir': self.root})))
        self.enterContext(patch.object(scans, 'list_scans', side_effect=lambda: actual_list(vault_dir=self.root)))
        self.enterContext(patch.object(scans, 'resolve_scan', side_effect=lambda key, **kw: actual_resolve(key, vault_dir=self.root)))

    def test_confirmed_save_list_preview_and_repeat(self):
        raw = scans.images_pdf([page('white'), page('blue')])
        url = self.url + '/api/documents/scans/pdf?scan_id=' + 'b' * 32 + '&title=Test'
        request = Request(url, data=raw, headers={'Content-Type': 'application/pdf', 'Origin': self.url, 'X-Confirm-Save': 'yes'})
        for _ in range(2):
            with urlopen(request) as response:
                self.assertTrue(json.load(response)['ok'])
        with urlopen(self.url + '/api/documents/scans') as response:
            self.assertEqual(len(json.load(response)['items']), 1)
        with urlopen(self.url + '/api/documents/scans/pdf?scan_id=' + 'b' * 32) as response:
            self.assertEqual(response.headers['Content-Type'], 'application/pdf')
            self.assertEqual(response.read(), raw)

    def test_selected_scan_works_even_with_an_older_scandocu_process(self):
        from types import SimpleNamespace
        scans.save_scan(scan_id="e"*32,title="Vybraný sken",
                        raw=scans.images_pdf([page("white")]),confirmed=True,vault_dir=self.root)
        with patch("app.cockpit.start_scandocu") as start:
            with urlopen(self.url+"/scandocu/?scan_ref="+"e"*32) as response:
                self.assertIn("requestedScanRef",response.read().decode())
            candidate=SimpleNamespace(to_api=lambda:{"found":True,"title":"document","token":"fixture"})
            with patch("app.documents.scandocu.prepare_scandocu_candidate",return_value=candidate):
                with urlopen(self.url+"/api/scandocu/next?scan_ref="+"e"*32) as response:
                    self.assertEqual(json.load(response)["title"],"Vybraný sken")
            start.assert_not_called()

    def test_missing_confirmation_and_cross_origin_rejected(self):
        raw = scans.images_pdf([page('white')])
        url = self.url + '/api/documents/scans/pdf?scan_id=' + 'c' * 32 + '&title=Test'
        for headers in ({'Origin': self.url}, {'Origin': 'https://outside.invalid', 'X-Confirm-Save': 'yes'}):
            with self.assertRaises(HTTPError):
                urlopen(Request(url, data=raw, headers={**headers, 'Content-Type': 'application/pdf'}))
        self.assertEqual(list(self.root.iterdir()), [])

class ScanFrontend(unittest.TestCase):

    def test_phone_capture_preview_confirmation_and_retry(self):
        script = Path(__file__).with_name('document_scan_frontend.test.cjs')
        result = subprocess.run(['node', '--test', str(script)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ScanDocuSelection(unittest.TestCase):
    def test_exact_saved_scan_is_selected_with_its_title(self):
        from types import SimpleNamespace
        from app.documents.scandocu import ScanDocuServer
        with TemporaryDirectory() as temporary:
            root=Path(temporary).resolve()
            scans.save_scan(scan_id='d'*32,title='Vícestránková smlouva',
                            raw=scans.images_pdf([page('white')]),confirmed=True,vault_dir=root)
            app=ScanDocuServer(vault_dir=root)
            server=ThreadingHTTPServer(('127.0.0.1',0),app.make_handler())
            thread=threading.Thread(target=server.serve_forever,daemon=True)
            thread.start()
            try:
                fake=SimpleNamespace(to_api=lambda:{'found':True,'title':'document','token':'synthetic'})
                with patch('app.documents.scandocu.prepare_scandocu_candidate',return_value=fake) as prepare:
                    with urlopen(f'http://127.0.0.1:{server.server_address[1]}/api/next?scan_ref='+ 'd'*32) as response:
                        result=json.load(response)
                self.assertEqual(result['title'],'Vícestránková smlouva')
                self.assertEqual(prepare.call_args.args[0],scans.resolve_scan('d'*32,vault_dir=root))
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
