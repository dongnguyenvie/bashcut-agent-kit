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
# grade.py reads LUTs with fetch_luts.py, which lives in the Online Resources plugin (bashcut.resources); the kit's
# fetch_luts.py runs that copy. Tests use a bashcut-plugins checkout next to this repo, else skip.
PLUGIN = Path(os.environ.get('BASHCUT_RESOURCES_DIR')
              or Path(__file__).resolve().parents[2] / 'bashcut-plugins' / 'plugins' / 'resources')


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
@unittest.skipUnless((PLUGIN / 'scripts' / 'fetch_luts.py').is_file(), 'no bashcut.resources checkout')
class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        env = mock.patch.dict(os.environ, {'BASHCUT_RESOURCES_DIR': str(PLUGIN),
                                           'BASHCUT_SHARED_DATA': str(self.tmp / 'data'),
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
