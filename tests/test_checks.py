import importlib.util
from pathlib import Path
import unittest
import json
import shutil
import subprocess
import sys
import tempfile


def module(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / 'scripts' / f'{name}.py')
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


checks = module('check_commands')
versions = module('check_version')


class ChecksTests(unittest.TestCase):
    def setUp(self):
        self.commands = checks.catalog('### `bashcut voice speak <text> [--takes <count>]`\n### `bashcut media list`')

    def test_valid_examples_and_quoted_text(self):
        text = '```sh\nbashcut voice speak "--not-an-option" \\\n --takes 3 [--format text] # --comment\n```\n`bashcut media list`'
        self.assertEqual(checks.validate(text, self.commands), [])
        self.assertEqual(len(list(checks.examples(text))), 2)

    def test_unknown_command_and_flag(self):
        self.assertIn('Unknown command', checks.validate('`bashcut media missing`', self.commands)[0])
        self.assertIn('--missing', checks.validate('`bashcut voice speak hello [--missing=3]`', self.commands)[0])

    def test_empty_catalog_is_an_error(self):
        with self.assertRaises(ValueError):
            checks.catalog('not the generated reference')

    def test_version_order(self):
        self.assertGreater(versions.version('0.0.10'), versions.version('0.0.9'))
        with self.assertRaises(ValueError):
            versions.version('latest')


class VersionGateTests(unittest.TestCase):
    def test_skill_change_requires_bump(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'scripts').mkdir()
            (root / 'skills').mkdir()
            (root / '.claude-plugin').mkdir()
            script = root / 'scripts/check_version.py'
            shutil.copyfile(Path(versions.__file__), script)
            manifest = root / '.claude-plugin/plugin.json'
            manifest.write_text(json.dumps({'version': '0.0.1'}))
            skill = root / 'skills/test.md'
            skill.write_text('initial')

            def git(*args):
                return subprocess.check_output(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                                                *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()

            git('init')
            git('add', '.')
            git('commit', '-m', 'base')
            base = git('rev-parse', 'HEAD')
            command = [sys.executable, str(script), '--base', base]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            skill.write_text('changed')
            git('add', '.')
            git('commit', '-m', 'skill')
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('require a higher', rejected.stderr)
            manifest.write_text(json.dumps({'version': '0.0.2'}))
            git('add', '.')
            git('commit', '-m', 'version')
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
