import argparse
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

try:
    import numpy as np
    from PIL import Image
except ImportError:  # the scripts run under uv with numpy and Pillow; skip where the test Python lacks them
    np = None

FOLDER = Path(__file__).resolve().parents[1] / 'skills' / 'color-grade'


def load(name):
    spec = importlib.util.spec_from_file_location(name, FOLDER / f'{name}.py')
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def cube(fn, size=5):
    """A .cube text of a colour function fn on a size³ grid (R varies fastest)."""
    g = np.linspace(0, 1, size)
    rows = [fn(np.array([r, gg, b])) for b in g for gg in g for r in g]
    return f'LUT_3D_SIZE {size}\n' + '\n'.join(' '.join(f'{v:.5f}' for v in row) for row in rows) + '\n'


def hald(fn, level=2):
    """A HaldCLUT PNG (level² cube size, side level³) of fn."""
    n, side = level * level, level ** 3
    i = np.arange(side * side)
    rgb = np.stack([i % n, (i // n) % n, i // (n * n)], -1) / (n - 1)
    out = np.clip(np.array([fn(c) for c in rgb]), 0, 1)
    buf = io.BytesIO()
    Image.fromarray((out.reshape(side, side, 3) * 255).round().astype(np.uint8)).save(buf, 'PNG')
    return buf.getvalue()


@unittest.skipIf(np is None, 'numpy and Pillow not installed')
class FingerprintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = load('fetch_luts')

    def test_identity_cube_measures_unchanged(self):
        table = self.f.parse_cube(cube(lambda c: c))
        fp = self.f.fingerprint(lambda c: self.f.apply_lut(c, table))
        self.assertAlmostEqual(fp['contrast'], 1, places=2)
        self.assertAlmostEqual(fp['sat'], 1, places=2)
        self.assertLess(abs(fp['warm']) + abs(fp['skin_hue']) + abs(fp['black']), 0.5)
        self.assertEqual(self.f.auto_tags(fp), [])
        self.assertFalse(self.f.is_log(fp))

    def test_tags_from_numbers(self):
        warm = self.f.fingerprint(lambda c: np.clip(c * [1.12, 1.0, 0.85], 0, 1))
        self.assertIn('warm', self.f.auto_tags(warm))
        grey = self.f.fingerprint(lambda c: np.repeat(self.f.luma(c)[..., None], 3, -1))
        self.assertIn('bw', self.f.auto_tags(grey))
        matte = self.f.fingerprint(lambda c: 0.08 + c * 0.84)
        self.assertIn('matte', self.f.auto_tags(matte))

    def test_log_lut_detected(self):
        steep = self.f.fingerprint(lambda c: np.clip((c - 0.5) * 3 + 0.5, 0, 1))
        self.assertTrue(self.f.is_log(steep))

    def test_domain_and_broken_files(self):
        table = self.f.parse_cube('DOMAIN_MIN 0 0 0\nDOMAIN_MAX 2 2 2\n' + cube(lambda c: c, 3))
        self.assertAlmostEqual(float(self.f.apply_lut(np.array([0.5, 0.5, 0.5]), table)[0]), 0.25, places=3)
        for text in ('LUT_1D_SIZE 4\n0 0 0\n', 'LUT_3D_SIZE 3\n0 0 0\n', 'nothing'):
            with self.assertRaises(ValueError):
                self.f.parse_cube(text)

    def test_hald_matches_the_same_cube(self):
        fn = lambda c: np.clip(c ** 0.8 * [1.05, 1.0, 0.9], 0, 1)
        from_hald = self.f.hald_to_table(Image.open(io.BytesIO(hald(fn))))
        from_cube = self.f.parse_cube(cube(fn, 4))
        self.assertEqual(from_hald.shape, (4, 4, 4, 3))
        self.assertLess(float(np.abs(from_hald - from_cube).max()), 0.01)
        self.assertEqual(self.f.resample(from_hald, 9).shape, (9, 9, 9, 3))


@unittest.skipIf(np is None, 'numpy and Pillow not installed')
class IngestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        env = mock.patch.dict(os.environ, {'BASHCUT_SHARED_DATA': str(self.tmp / 'data'),
                                           'BASHCUT_SHARED_CACHE': str(self.tmp / 'cache')})
        env.start()
        self.addCleanup(env.stop)
        self.f = load('fetch_luts')
        own = self.tmp / 'own'
        own.mkdir()
        (own / 'warm.cube').write_text(cube(lambda c: np.clip(c * [1.15, 1.0, 0.8], 0, 1)))
        (own / 'warm-copy.cube').write_text(cube(lambda c: np.clip(c * [1.15, 1.0, 0.8], 0, 1)))  # same bytes
        (own / 'warm-near.cube').write_text(cube(lambda c: np.clip(c * [1.151, 1.0, 0.8], 0, 1)))  # same look
        (own / 'teal.png').write_bytes(hald(lambda c: np.clip(c * [0.85, 1.0, 1.15], 0, 1)))
        (own / 'log.cube').write_text(cube(lambda c: np.clip((c - 0.5) * 3 + 0.5, 0, 1)))
        (own / 'broken.cube').write_text('LUT_3D_SIZE 3\n1 2\n')
        self.own = own
        self.added = []

    def run_main(self, *args):
        calls = []

        def fake(*argv, retry=True):
            calls.append(argv)
            if argv[:2] == ('library', 'list'):  # what earlier runs added
                return {'items': [{'params': json.loads(dict(zip(a[2::2], a[3::2]))['--params'])}
                                  for a in self.added], 'next': None}
            return {'id': 'x'}

        out = io.StringIO()
        with mock.patch.object(self.f, 'bashcut', fake), mock.patch('sys.stdout', out):
            self.f.main(['--source', '', '--folder', str(self.own), *args])
        adds = [c for c in calls if c[:2] == ('library', 'add')]
        self.added += adds
        return out.getvalue().strip().splitlines(), adds

    def test_one_line_with_duplicates_log_and_broken(self):
        lines, adds = self.run_main()
        self.assertEqual(lines, ['3 added, 2 duplicates, 1 log, 1 broken, 0 already in the library'])
        self.assertEqual(len(adds), 3)
        args = dict(zip(adds[0][2::2], adds[0][3::2]))
        params = json.loads(args['--params'])
        self.assertIn('fp', params['lut'])
        self.assertTrue(Path(params['lut']['file']).exists())
        self.assertTrue(args['--tags'].startswith('lut,local'))
        tags = [dict(zip(a[2::2], a[3::2]))['--tags'] for a in adds]
        self.assertTrue(any('log' in t for t in tags))
        self.assertTrue(any('warm' in t for t in tags))
        again, adds = self.run_main()  # files kept from the first run are not measured again
        self.assertEqual(adds, [])
        self.assertEqual(again, ['0 added, 1 duplicates, 0 log, 1 broken, 4 already in the library'])

    def test_limit_caps_what_is_looked_at(self):
        lines, adds = self.run_main('--limit', '2')
        self.assertLessEqual(len(adds), 2)
        self.assertEqual(len(lines), 1)

    def test_failed_source_is_one_line(self):
        def boom(quota):
            raise OSError('curl exit 22')
            yield
        out = io.StringIO()
        with mock.patch.object(self.f, 'gmic', boom), mock.patch.object(self.f, 'bashcut', lambda *a, **k: {}), \
                mock.patch('sys.stdout', out):
            self.f.main(['--source', 'gmic', '--no-library'])
        self.assertEqual(out.getvalue().splitlines()[0], 'gmic: skipped (curl exit 22)')
        self.assertEqual(len(out.getvalue().splitlines()), 2)


@unittest.skipIf(np is None, 'numpy and Pillow not installed')
class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        env = mock.patch.dict(os.environ, {'BASHCUT_SHARED_DATA': str(self.tmp / 'data'),
                                           'BASHCUT_SHARED_CACHE': str(self.tmp / 'cache')})
        env.start()
        self.addCleanup(env.stop)
        self.g = load('grade')
        self.F = self.g.luts()
        self.addCleanup(lambda: sys.modules.pop('fetch_luts', None))
        rng = np.random.default_rng(1)
        self.frames = []
        for k, base in enumerate(([.8, .6, .5], [.3, .5, .7], [.2, .4, .1])):
            a = np.clip(np.array(base) * (0.6 + 0.5 * rng.random((60, 100, 1))) + k * 0.05, 0, 1)
            path = self.tmp / f'f{k}.png'
            Image.fromarray((a * 255).astype(np.uint8)).save(path)
            self.frames.append(str(path))
        self.items = []
        for name, fn in (('warm', lambda c: np.clip(c * [1.12, 1.0, 0.85], 0, 1)),
                         ('cool', lambda c: np.clip(c * [0.85, 1.0, 1.12], 0, 1)),
                         ('burn', lambda c: np.clip(c * 2.2, 0, 1)),
                         ('plain', lambda c: c)):
            path = self.tmp / f'{name}.cube'
            path.write_text(cube(fn, 9))
            table = self.F.read_cube(path)
            fp = self.F.fingerprint(lambda c: self.F.apply_lut(c, table))
            self.items.append({'id': f'lut-{name}', 'scope': 'user', 'name': name, 'tags': ['lut', 'local'],
                               'params': {'lut': {'fp': fp, 'file': str(path)}}})
        self.calls = []

    def fake(self, *argv, retry=True):
        self.calls.append(argv)
        if argv[:2] == ('media', 'frames'):
            return {'frames': [{'path': p} for p in self.frames]}
        if argv[:2] == ('library', 'list'):
            return {'items': self.items, 'next': None}
        if argv[:2] == ('project', 'data'):
            return {'plan': {'recipe': 'travel', 'stages': []}}
        if argv[:2] == ('timeline', 'get'):
            return {'tracks': [{'items': [{'at': 0, 'dur': 300}, {'at': 300, 'dur': 150}]}]}
        if argv[:2] == ('luts', 'import'):
            return {'lut': {'id': 'L1'}}
        if argv[:2] == ('adjustment', 'add'):
            return {'item': {'id': 'A1'}}
        return {}

    def options(self, **kw):
        base = dict(target='warm', n=8, check=20, gen=2, max_clip=1.0, max_crush=2.0, max_skin=8.0, wb_fit=0.5,
                    no_fit=False, log=False, key=None, scope=None)
        base.update(kw)
        return argparse.Namespace(**base)

    def candidates(self, **kw):
        out = io.StringIO()
        with mock.patch.object(self.F, 'bashcut', self.fake), mock.patch('sys.stdout', out):
            self.g.cmd_candidates(['/abs/clip.mp4'], self.options(**kw))
        return out.getvalue().strip().splitlines()

    def test_sheet_ranks_checks_and_adds_generated(self):
        lines = self.candidates()
        self.assertTrue(Path(lines[0].split()[0]).exists())
        self.assertIn("picks for 'travel'", lines[0])
        self.assertTrue(lines[1].startswith('1 warm'))
        self.assertFalse(any(' burn ' in f' {l} ' for l in lines[1:]))  # clips highlights: dropped
        self.assertEqual(sum('generated' in l for l in lines), 2)
        self.assertEqual(len(lines), 1 + 3 + 2)

    def test_target_kinds(self):
        frames = [np.repeat(np.linspace(0, 1, 64, dtype=np.float32)[:, None, None], 3, -1)]  # a ramp: black 0
        self.assertEqual(self.g.target_of('warm,matte', frames), {'warm': [3, 15], 'black': [4, 10]})
        self.assertIn('shadow_rb', self.g.target_of('matte-cinematic', frames))
        prof = self.tmp / 'profile.json'
        prof.write_text(json.dumps({'colour': {'black': 6, 'white': 85, 'sat': 25, 'tint_mid': [4, 0]}}))
        t = self.g.target_of(str(prof), frames)
        self.assertAlmostEqual(t['black'], 6, delta=1.1)
        self.assertEqual(t['warm'], 4)
        with self.assertRaises(SystemExit):
            self.g.target_of('sparkly', frames)

    def test_pick_applies_and_learns(self):
        self.candidates(target='clean')
        out = io.StringIO()
        with mock.patch.object(self.F, 'bashcut', self.fake), mock.patch('sys.stdout', out):
            self.g.cmd_pick('2', 0.7, None)
        add = next(c for c in self.calls if c[:2] == ('adjustment', 'add'))
        self.assertEqual(dict(zip(add[2::2], add[3::2]))['--duration'], '450')
        self.assertIn('applied 2', out.getvalue())
        updates = [c for c in self.calls if c[:2] == ('library', 'update')]
        self.assertEqual(len(updates), 3)
        last = json.loads((self.F.CACHE / 'candidates' / 'last.json').read_text())
        picked = next(e for e in last['entries'] if e['n'] == 2)['id']
        for u in updates:
            lut = json.loads(u[-1])['lut']
            self.assertEqual(lut['shown']['travel'], 1)
            self.assertEqual(lut.get('picks', {}).get('travel', 0), int(u[2] == picked))
        # the next video of this recipe ranks the earlier pick in the top 3
        for item in self.items:
            ref = f"user:{item['id']}"
            new = next((json.loads(u[-1]) for u in updates if u[2] == ref), None)
            if new:
                item['params'] = new
        ranked = self.g.rank(self.items, self.g.target_of('clean', []), 'travel')
        self.assertIn(picked, [f"user:{r[1]['id']}" for r in ranked[:3]])

    def test_pick_frames_takes_bright_dark_and_skin(self):
        dark, bright, skin, grey = (np.full((8, 8, 3), v, np.float32) for v in (0.1, 0.9, 0.5, 0.4))
        skin[:] = [0.8, 0.6, 0.5]
        self.assertEqual(self.g.pick_frames([grey, dark, bright, skin, grey]), [1, 2, 3])
        black = np.zeros((8, 8, 3), np.float32)
        noisy = [np.clip(f + np.random.default_rng(0).random((8, 8, 3)) * 0.2, 0, 1) for f in (dark, bright, skin, grey)]
        self.assertNotIn(0, self.g.pick_frames([black, *noisy]))


if __name__ == '__main__':
    unittest.main()
