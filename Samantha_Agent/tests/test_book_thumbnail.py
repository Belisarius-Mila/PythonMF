from email.message import Message
from io import BytesIO
import unittest
import urllib.error
from unittest.mock import Mock
from PIL import Image
from app.book_thumbnail import MAX_DOWNLOAD_BYTES, _CoverRedirect, fetch_thumbnail


def jpeg():
    data = BytesIO()
    image = Image.new('RGB', (600, 900), 'red')
    exif = Image.Exif(); exif[270] = 'Private source metadata'
    image.save(data, 'JPEG', exif=exif)
    return data.getvalue()


class Response(BytesIO):
    def __init__(self, body, mime='image/jpeg', url='https://covers.openlibrary.org/b/id/123-S.jpg'):
        super().__init__(body)
        self.headers = Message(); self.headers['Content-Type'] = mime
        self.url = url
    def geturl(self): return self.url


class BookThumbnailTests(unittest.TestCase):
    def test_fixed_endpoint_small_jpeg_strips_metadata(self):
        opener = Mock(return_value=Response(jpeg()))
        data, status = fetch_thumbnail('0385472579', opener=opener)
        self.assertEqual(status, 'stored')
        self.assertEqual(opener.call_args.args[0].full_url, 'https://covers.openlibrary.org/b/isbn/9780385472579-S.jpg?default=false')
        self.assertEqual(opener.call_args.kwargs['timeout'], 3)
        with Image.open(BytesIO(data)) as image:
            self.assertEqual(image.format, 'JPEG')
            self.assertLessEqual(image.width, 240); self.assertLessEqual(image.height, 320)
            self.assertFalse(image.getexif())
        self.assertLess(len(data), 64 * 1024)

    def test_missing_and_network_failures_are_nonblocking(self):
        for code, status in [(404, 'not_found'), (410, 'not_found'), (429, 'unavailable'), (500, 'unavailable')]:
            error = urllib.error.HTTPError('https://covers.openlibrary.org/', code, '', {}, None)
            self.assertEqual(fetch_thumbnail('0385472579', opener=Mock(side_effect=error)), (None, status))
        self.assertEqual(fetch_thumbnail('0385472579', opener=Mock(side_effect=TimeoutError())), (None, 'unavailable'))

    def test_rejects_foreign_target_html_huge_invalid_and_placeholder_images(self):
        tiny = BytesIO(); Image.new('RGB', (1, 1)).save(tiny, 'PNG')
        for response in [Response(jpeg(), url='http://covers.openlibrary.org/a.jpg'),
                         Response(jpeg(), url='https://example.com/a.jpg'),
                         Response(jpeg(), url='https://user@covers.openlibrary.org/a.jpg'),
                         Response(b'<svg/>', mime='image/svg+xml'), Response(b'broken'),
                         Response(b'x' * (MAX_DOWNLOAD_BYTES + 1)), Response(tiny.getvalue(), mime='image/png')]:
            with self.subTest(url=response.url, size=len(response.getvalue())):
                self.assertEqual(fetch_thumbnail('0385472579', opener=Mock(return_value=response)), (None, 'unavailable'))

    def test_redirect_cannot_leave_fixed_https_provider(self):
        for url in ['http://covers.openlibrary.org/a', 'https://127.0.0.1/a', 'https://example.com/a']:
            with self.assertRaises(ValueError): _CoverRedirect().redirect_request(None, None, 302, '', {}, url)

    def test_invalid_isbn_never_queries_provider(self):
        opener = Mock()
        with self.assertRaises(ValueError): fetch_thumbnail('not-an-isbn', opener=opener)
        opener.assert_not_called()
