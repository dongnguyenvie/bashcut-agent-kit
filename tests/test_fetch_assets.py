"""Asset search scripts (P2-S1) with mocked HTTP: no network, keys only from the environment."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.parse

SKILLS = Path(__file__).resolve().parents[1] / 'skills'


def load(relative):
    path = SKILLS / relative
    spec = importlib.util.spec_from_file_location(path.stem, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class FakeWeb:
    """Answers get(url, …) from a list of (url prefix, body); records every call."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, url, *args, **kwargs):
        headers = kwargs.get('headers')
        if headers is None:
            headers = next((a for a in args if isinstance(a, dict)), None)
        self.calls.append((url, headers))
        for prefix, body in self.routes:
            if url.startswith(prefix):
                if isinstance(body, Exception):
                    raise body
                return body if isinstance(body, bytes) else json.dumps(body).encode()
        raise OSError(f'curl exit 22 for {url}')

    def query(self, prefix):
        url = next(u for u, _ in self.calls if u.startswith(prefix))
        return urllib.parse.parse_qs(urllib.parse.urlparse(url).query)


def run(module, argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        module.main(argv)
    return [json.loads(line) for line in out.getvalue().splitlines()]


PIXABAY_PHOTOS = {'hits': [{'id': 11, 'pageURL': 'https://pixabay.com/photos/pot-11/', 'tags': 'clay, pot',
                            'previewURL': 'https://cdn.pixabay.com/p/11_150.jpg', 'imageWidth': 4000,
                            'imageHeight': 6000, 'largeImageURL': 'https://pixabay.com/get/11_1280.jpg',
                            'user': 'ann'}]}
PIXABAY_VIDEO = {'hits': [{'id': 22, 'pageURL': 'https://pixabay.com/videos/x-22/', 'tags': 'river', 'duration': 14,
                           'user': 'bo', 'videos': {
                               'large': {'url': '', 'width': 0, 'height': 0},
                               'medium': {'url': 'https://cdn.pixabay.com/v/22_medium.mp4', 'width': 1920, 'height': 1080},
                               'small': {'url': 'https://cdn.pixabay.com/v/22_small.mp4', 'width': 1280, 'height': 720},
                               'tiny': {'url': 'https://cdn.pixabay.com/v/22_tiny.mp4', 'width': 960, 'height': 540,
                                        'thumbnail': 'https://cdn.pixabay.com/v/22_tiny.jpg'}}}]}
PEXELS_VIDEO = {'id': 33, 'url': 'https://www.pexels.com/video/33/', 'duration': 9, 'image': 'https://p/33.jpg',
                'user': {'name': 'Cy'}, 'video_files': [
                    {'width': 2160, 'height': 3840, 'link': 'https://videos.pexels.com/33-uhd.mp4'},
                    {'width': 1080, 'height': 1920, 'link': 'https://videos.pexels.com/33-hd.mp4'},
                    {'width': 540, 'height': 960, 'link': 'https://videos.pexels.com/33-sd.mp4'}]}


class StockTests(unittest.TestCase):
    def setUp(self):
        self.stock = load('stock-images/fetch_stock.py')

    def test_no_key_fails_loudly(self):
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaises(SystemExit) as stop:
            run(self.stock, ['--query', 'pot'])
        self.assertIn('PIXABAY_API_KEY', str(stop.exception.code))

    def test_pixabay_search_uses_the_env_key_and_lists_candidates(self):
        web = FakeWeb([('https://pixabay.com/api/', PIXABAY_PHOTOS)])
        with mock.patch.dict(os.environ, {'PIXABAY_API_KEY': 'k-env'}, clear=True), \
                mock.patch.object(self.stock, 'get', web):
            rows = run(self.stock, ['--query', 'clay pot', '--count', '5'])
        query = web.query('https://pixabay.com/api/')
        self.assertEqual(query['key'], ['k-env'])
        self.assertEqual(query['orientation'], ['vertical'])
        self.assertEqual(query['per_page'], ['5'])
        self.assertEqual(rows, [{'id': '11', 'source': 'pixabay', 'kind': 'photo',
                                 'page': 'https://pixabay.com/photos/pot-11/', 'author': 'ann', 'tags': 'clay, pot',
                                 'license': 'Pixabay Content License', 'size': '4000x6000',
                                 'preview': 'https://cdn.pixabay.com/p/11_150.jpg',
                                 'url': 'https://pixabay.com/get/11_1280.jpg'}])

    def test_pixabay_video_download_takes_smallest_rendition_at_least_1080(self):
        web = FakeWeb([('https://pixabay.com/api/videos/', PIXABAY_VIDEO),
                       ('https://cdn.pixabay.com/v/22_medium.mp4', b'mp4-bytes')])
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.dict(os.environ, {'PIXABAY_API_KEY': 'k'}, clear=True), \
                mock.patch.object(self.stock, 'get', web):
            rows = run(self.stock, ['--kind', 'video', '--ids', '22', '--dest', folder])
            self.assertEqual(rows[0]['file'], 'pixabay-22-river.mp4')
            self.assertEqual((Path(folder) / rows[0]['file']).read_bytes(), b'mp4-bytes')
        self.assertEqual(web.query('https://pixabay.com/api/videos/')['id'], ['22'])
        self.assertEqual(rows[0]['size'], '1920x1080')
        self.assertEqual(rows[0]['seconds'], 14)

    def test_pexels_key_goes_in_the_header_not_the_url(self):
        web = FakeWeb([('https://api.pexels.com/videos/videos/33', PEXELS_VIDEO),
                       ('https://videos.pexels.com/33-hd.mp4', b'x')])
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.dict(os.environ, {'PEXELS_API_KEY': 'secret'}, clear=True), \
                mock.patch.object(self.stock, 'get', web):
            rows = run(self.stock, ['--source', 'pexels', '--kind', 'video', '--ids', '33', '--dest', folder])
        api_url, headers = web.calls[0]
        self.assertNotIn('secret', api_url)
        self.assertEqual(headers, {'Authorization': 'secret'})
        self.assertEqual(rows[0]['size'], '1080x1920')
        self.assertEqual(rows[0]['author'], 'Cy')

    def test_a_missing_id_is_reported_and_the_rest_continue(self):
        web = FakeWeb([('https://pixabay.com/api/?key=k&id=404', {'hits': []}),
                       ('https://pixabay.com/api/?key=k&id=11', PIXABAY_PHOTOS),
                       ('https://pixabay.com/get/11_1280.jpg', b'jpg')])
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.dict(os.environ, {'PIXABAY_API_KEY': 'k'}, clear=True), \
                mock.patch.object(self.stock, 'get', web):
            rows = run(self.stock, ['--ids', '404,11', '--dest', folder])
        self.assertEqual(rows[0], {'id': '404', 'source': 'pixabay', 'error': 'not found'})
        self.assertEqual(rows[1]['file'], 'pixabay-11-clay-pot.jpg')

    def test_no_key_in_the_source(self):
        text = (SKILLS / 'stock-images/fetch_stock.py').read_text()
        self.assertNotRegex(text, r'key=[0-9a-f]{10,}|Authorization": "[A-Za-z0-9]{20,}')


FREESOUND = {'results': [{'id': 5, 'name': 'Whoosh 1', 'username': 'dee', 'duration': 1.234,
                          'license': 'http://creativecommons.org/publicdomain/zero/1.0/',
                          'url': 'https://freesound.org/people/dee/sounds/5/',
                          'previews': {'preview-hq-mp3': 'https://cdn.freesound.org/previews/0/5-hq.mp3'}}]}


class FreesoundTests(unittest.TestCase):
    def setUp(self):
        self.audio = load('audio-mix/fetch_audio.py')

    def test_freesound_first_with_a_key_cc0_filter_token_header(self):
        web = FakeWeb([('https://freesound.org/apiv2/search/', FREESOUND),
                       ('https://cdn.freesound.org/previews/0/5-hq.mp3', b'mp3')])
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.dict(os.environ, {'FREESOUND_API_KEY': 'fs-key'}, clear=True), \
                mock.patch.object(self.audio, 'get', web):
            rows = run(self.audio, ['--dest', folder, '--sfx', 'whoosh'])
            self.assertEqual((Path(folder) / 'sfx-whoosh.mp3').read_bytes(), b'mp3')
        url, headers = web.calls[0]
        self.assertNotIn('fs-key', url)
        self.assertEqual(headers, {'Authorization': 'Token fs-key'})
        self.assertEqual(web.query('https://freesound.org/')['filter'],
                         ['license:"Creative Commons 0" duration:[0 TO 5]'])
        self.assertIsNone(web.calls[1][1])  # the preview download carries no key
        self.assertEqual(rows, [{'file': 'sfx-whoosh.mp3', 'kind': 'sfx', 'title': 'Whoosh 1', 'from': 'freesound',
                                 'seconds': 1.2, 'license': 'http://creativecommons.org/publicdomain/zero/1.0/',
                                 'author': 'dee', 'source': 'https://freesound.org/people/dee/sounds/5/'}])

    def test_cc_by_only_after_cc0_found_nothing(self):
        calls = []

        def web(url, *args, **kwargs):
            calls.append(url)
            if url.startswith('https://freesound.org/'):
                licence = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)['filter'][0]
                return json.dumps(FREESOUND if '"Attribution"' in licence else {'results': []}).encode()
            return b'mp3'

        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.dict(os.environ, {'FREESOUND_API_KEY': 'k'}, clear=True), \
                mock.patch.object(self.audio, 'get', web):
            rows = run(self.audio, ['--dest', folder, '--sfx', 'pop', '--sfx-seconds', '2'])
        self.assertEqual(len([c for c in calls if 'freesound.org/apiv2' in c]), 2)
        self.assertIn('duration%3A%5B0+TO+2%5D', calls[0])
        self.assertEqual(rows[0]['from'], 'freesound')

    def test_without_a_key_falls_back_to_mixkit(self):
        page = b'<a href="https://assets.mixkit.co/active_storage/sfx/1/1-preview.mp3">'
        web = FakeWeb([('https://mixkit.co/free-sound-effects/pop/', page),
                       ('https://assets.mixkit.co/', b'mp3')])
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(self.audio, 'get', web):
            rows = run(self.audio, ['--dest', folder, '--sfx', 'pop'])
        self.assertFalse(any('freesound' in u for u, _ in web.calls))
        self.assertEqual(rows[0]['from'], 'mixkit')

    def test_freesound_source_without_key_says_so(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(os.environ, {}, clear=True):
            rows = run(self.audio, ['--dest', folder, '--sfx', 'pop', '--sfx-source', 'freesound'])
        self.assertEqual(rows[0]['error'], 'FREESOUND_API_KEY is not set')


FONT_META = {'id': 'be-vietnam-pro', 'family': 'Be Vietnam Pro', 'weights': [400, 600, 800],
             'subsets': ['latin', 'vietnamese'], 'license': 'OFL-1.1', 'type': 'google'}
GOOGLE_LIST = b")]}'\n" + json.dumps({'manifest': {'fileRefs': [
    {'filename': 'static/BeVietnamPro-SemiBold.ttf', 'url': 'https://fonts.gstatic.com/s/semibold.ttf'},
    {'filename': 'BeVietnamPro-ExtraBold.ttf', 'url': 'https://fonts.gstatic.com/s/xb.ttf'},
    {'filename': 'static/BeVietnamPro-ExtraBold.ttf', 'url': 'https://fonts.gstatic.com/s/xb-static.ttf'},
    {'filename': 'static/BeVietnamPro-ExtraBoldItalic.ttf', 'url': 'https://fonts.gstatic.com/s/xbi.ttf'}]}}).encode()


class FontTests(unittest.TestCase):
    def setUp(self):
        self.font = load('captions-text/fetch_font.py')

    def test_search_filters_by_subset_and_name(self):
        catalogue = [{'id': 'be-vietnam-pro', 'family': 'Be Vietnam Pro', 'category': 'sans-serif',
                      'weights': [400, 800], 'styles': ['normal', 'italic'], 'license': 'OFL-1.1', 'type': 'google'},
                     {'id': 'montserrat', 'family': 'Montserrat', 'weights': [400], 'styles': ['normal'],
                      'variable': True, 'type': 'google'}]
        web = FakeWeb([('https://api.fontsource.org/v1/fonts', catalogue)])
        with mock.patch.object(self.font, 'get', web):
            rows = run(self.font, ['--subset', 'vietnamese', '--query', 'vietnam', '--weight', '800'])
        self.assertEqual(web.query('https://api.fontsource.org/'), {'subsets': ['vietnamese'], 'weights': ['800']})
        self.assertEqual(rows, [{'id': 'be-vietnam-pro', 'family': 'Be Vietnam Pro', 'category': 'sans-serif',
                                 'weights': [400, 800], 'italic': True, 'license': 'OFL-1.1', 'type': 'google'}])

    def test_download_takes_whole_static_files_from_google_fonts(self):
        web = FakeWeb([('https://api.fontsource.org/v1/fonts/be-vietnam-pro', FONT_META),
                       ('https://fonts.google.com/download/list?family=Be%20Vietnam%20Pro', GOOGLE_LIST),
                       ('https://fonts.gstatic.com/s/semibold.ttf', b'sb'),
                       ('https://fonts.gstatic.com/s/xb-static.ttf', b'xb')])
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(self.font, 'get', web):
            rows = run(self.font, ['--family', 'Be Vietnam Pro', '--weights', '600,800,700', '--dest', folder])
            self.assertEqual((Path(folder) / 'BeVietnamPro-ExtraBold.ttf').read_bytes(), b'xb')
        self.assertEqual(rows[0], {'family': 'Be Vietnam Pro', 'weight': 700, 'error': 'weights are [400, 600, 800]'})
        self.assertEqual([r['file'] for r in rows[1:]], ['BeVietnamPro-SemiBold.ttf', 'BeVietnamPro-ExtraBold.ttf'])
        self.assertFalse(any('jsdelivr' in u for u, _ in web.calls))  # never Fontsource's per-subset files

    def test_italic_and_variable_only_families(self):
        refs = json.loads(GOOGLE_LIST[5:])['manifest']['fileRefs']
        self.assertEqual(self.font.pick_files(refs, [800], True)[0][1]['url'], 'https://fonts.gstatic.com/s/xbi.ttf')
        variable = [{'filename': 'Foo-VariableFont_wght.ttf', 'url': 'v'},
                    {'filename': 'Foo-Italic-VariableFont_wght.ttf', 'url': 'vi'}]
        self.assertEqual(self.font.pick_files(variable, [700], False), [(None, variable[0])])

    def test_a_family_not_on_google_fonts_is_refused(self):
        web = FakeWeb([('https://api.fontsource.org/v1/fonts/foo', {'family': 'Foo', 'type': 'other',
                                                                     'source': 'https://example.org/foo'})])
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(self.font, 'get', web):
            rows = run(self.font, ['--family', 'Foo', '--dest', folder])
        self.assertIn('not on Google Fonts', rows[0]['error'])


if __name__ == '__main__':
    unittest.main()
