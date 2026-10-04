import importlib.util
import json
import pathlib
import tempfile
import unittest


def module():
    path = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'release.py'
    spec = importlib.util.spec_from_file_location('release', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


release = module()
URL = 'https://github.com/dongnguyenvie/bashcut-agent-kit/releases/download/v0.0.2/bashcut-agent-kit-0.0.2.zip'


def entry(**changes):
    value = {'version': '0.0.2', 'minAppVersion': '0.0.1', 'url': URL, 'sha256': 'a' * 64,
             'signature': 'ed25519:AAAA', 'size': 10, 'releasedAt': '2026-10-04'}
    value.update(changes)
    return value


class ReleaseTests(unittest.TestCase):
    def test_valid_catalog(self):
        self.assertEqual(release.validate({'schemaVersion': 1, 'kit': 'bashcut', 'versions': [entry()]}), [])

    def test_rejects_unsigned_mismatched_or_duplicate_versions(self):
        document = {'schemaVersion': 1, 'kit': 'bashcut', 'versions': [
            entry(signature=None), entry(url=URL.replace('v0.0.2/', 'v0.0.3/')), entry(sha256='XYZ')]}
        problems = '\n'.join(release.validate(document))
        for expected in ['signature', 'url must be', 'sha256', 'listed twice']:
            self.assertIn(expected, problems)

    def test_register_prepends_and_refuses_republishing(self):
        with tempfile.TemporaryDirectory() as folder:
            catalog = pathlib.Path(folder) / 'releases.json'
            catalog.write_text(json.dumps({'schemaVersion': 1, 'kit': 'bashcut', 'versions': [entry(version='0.0.1')]}))
            release.register(entry(), catalog)
            self.assertEqual([v['version'] for v in json.loads(catalog.read_text())['versions']], ['0.0.2', '0.0.1'])
            with self.assertRaises(SystemExit):
                release.register(entry(), catalog)

    def test_archive_holds_only_distributed_files(self):
        files = [str(path) for path in release.tracked_files()]
        self.assertIn('.claude-plugin/plugin.json', files)
        self.assertTrue(any(name.startswith('skills/') for name in files))
        for excluded in ['tests/', '.github/', 'releases.json']:
            self.assertFalse(any(name.startswith(excluded) for name in files), excluded)


if __name__ == '__main__':
    unittest.main()
