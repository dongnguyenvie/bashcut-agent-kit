import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

try:
    import numpy as np
except ImportError:  # grade.py runs under uv with numpy; skip where the test Python lacks it
    np = None

GRADE = Path(__file__).resolve().parents[1] / 'skills' / 'color-grade' / 'grade.py'
LOOKS = GRADE.parent / 'looks.json'


def module():
    spec = importlib.util.spec_from_file_location('grade', GRADE)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class LooksFileTests(unittest.TestCase):
    def test_targets_are_ranges_with_reasons(self):
        looks = json.loads(LOOKS.read_text(encoding='utf-8'))
        self.assertNotIn('mid_before_look', LOOKS.read_text(encoding='utf-8'))
        for name, look in looks.items():
            if name.startswith('_'):
                continue
            self.assertTrue(look.get('fitted'), name)
            for field, target in look['target'].items():
                self.assertEqual(set(target), {'ref', 'range', 'why'}, f'{name}.{field}')
                self.assertTrue(target['why'], f'{name}.{field}')
                ranges = target['range']
                if ranges is None:
                    continue
                # tints are [R-B, G-M]: one range (or null) per component
                ranges = [r for r in ranges if r is not None] if field.startswith('tint') else [ranges]
                for low, high in ranges:
                    if low is not None and high is not None:
                        self.assertLess(low, high, f'{name}.{field}')


@unittest.skipIf(np is None, 'numpy not installed')
class GradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = module()

    def test_overrides_only_what_is_passed(self):
        params = {'exposure': -0.1, 'wb': [1.0, 1.0, 1.0]}
        self.assertEqual(self.g.with_overrides(params), params)
        changed = self.g.with_overrides(params, exposure=0.3, wb=[1.1, 1.0, 0.9])
        self.assertAlmostEqual(changed['exposure'], 0.2)
        self.assertEqual(changed['wb'], [1.1, 1.0, 0.9])
        self.assertEqual(params['exposure'], -0.1)

    def test_compare_reports_differences_without_verdict(self):
        target = {'black': {'ref': 7.0, 'range': [4, 9], 'why': 'x'},
                  'white': {'ref': 84.0, 'range': [None, 90], 'why': 'x'},
                  'p5': {'ref': 8.9, 'range': None, 'why': 'x'},
                  'tint_high': {'ref': [1.5, -2.3], 'range': [[0, None], None], 'why': 'x'}}
        stats = {'black': 2.0, 'white': 95.5, 'p5': 9.9, 'tint_high': [-1.0, 3.0]}
        out = self.g.compare(stats, target)
        self.assertEqual(out['black'], {'value': 2.0, 'minusRef': -5.0, 'outside': -2.0})
        self.assertEqual(out['white']['outside'], 5.5)
        self.assertIsNone(out['p5']['outside'])
        self.assertEqual(out['tint_high']['outside'], [-1.0, None])
        self.assertEqual(out['tint_high']['minusRef'], [-2.5, 5.3])

    def test_stats_scale_is_0_to_100(self):
        grey = np.full((40, 40, 3), 128, np.uint8)
        s = self.g.stats(grey)
        self.assertAlmostEqual(s['mid'], 128 / 255 * 100, places=3)
        self.assertAlmostEqual(s['sat'], 0)
        self.assertEqual(self.g.stats(grey.astype(np.float32) / 255)['mid'], s['mid'])

    def test_lut_changes_only_with_passed_values(self):
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, folder)
        params = self.g.load_look('warm-film')
        plain = self.g.write_cube(params, str(folder / 'a.cube'), 9)
        same = self.g.write_cube(self.g.with_overrides(params), str(folder / 'b.cube'), 9)
        brighter = self.g.write_cube(self.g.with_overrides(params, exposure=0.5), str(folder / 'c.cube'), 9)
        self.assertEqual(Path(plain).read_text(), Path(same).read_text())
        self.assertGreater(self.g.read_cube(brighter)[1].mean(), self.g.read_cube(plain)[1].mean())


@unittest.skipIf(np is None or not shutil.which('ffmpeg') or not shutil.which('ffprobe'), 'needs numpy and ffmpeg')
class GradeCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = Path(tempfile.mkdtemp())
        cls.clip = cls.folder / 'clip.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=s=320x180:d=2',
                        '-pix_fmt', 'yuv420p', str(cls.clip)], check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.folder)

    def run_grade(self, *args):
        return subprocess.run([sys.executable, str(GRADE), *args], capture_output=True, text=True)

    def test_measure_json(self):
        result = self.run_grade('measure', str(self.clip), '--n', '2', '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertLessEqual(data['black'], data['mid'])
        self.assertLessEqual(data['mid'], data['white'])

    def test_match_reports_and_writes_nothing(self):
        result = self.run_grade('match', str(self.clip), 'matte-cinematic', '--n', '2', '--exposure', '0.2')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['passed'], {'exposure': 0.2, 'wb': None})
        self.assertIn('outside', data['fields']['black']['footage'])
        self.assertIn('outside', data['fields']['black']['withLook'])
        self.assertEqual(list(self.folder.glob('*.cube')), [])
        refused = self.run_grade('match', str(self.clip), 'matte-cinematic', '-o', str(self.folder / 'x.cube'))
        self.assertNotEqual(refused.returncode, 0)
        self.assertFalse((self.folder / 'x.cube').exists())


if __name__ == '__main__':
    unittest.main()
