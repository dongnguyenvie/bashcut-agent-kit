import importlib.util
from pathlib import Path
import unittest


def module(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / 'scripts' / f'{name}.py')
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


checks = module('check_commands')


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


if __name__ == '__main__':
    unittest.main()
