"""The kit's Claude Code hooks with a fake bashcut CLI: no app, no network."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HOOKS = Path(__file__).resolve().parents[1] / 'hooks'


@unittest.skipUnless(shutil.which('perl') and shutil.which('sh'), 'needs sh and perl')
class HookTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder)
        self.calls = self.folder / 'calls.txt'
        self.cli = self.folder / 'bashcut'
        self.fail_cli(False)
        self.env = {**os.environ, 'BASHCUT_CLI': str(self.cli), 'BASHCUT_KIT_STATE': str(self.folder / 'state')}

    def fail_cli(self, fail):
        # Records its arguments, one call per line; exits 1 when "no project is open".
        self.cli.write_text('#!/bin/sh\nprintf "%s|" "$@" >>"' + str(self.calls) + '"\necho >>"' + str(self.calls)
                            + '"\nexit ' + ('1' if fail else '0') + '\n')
        self.cli.chmod(0o755)

    def hook(self, name, payload):
        out = subprocess.run(['sh', str(HOOKS / name)], input=json.dumps(payload), capture_output=True, text=True,
                             env=self.env, timeout=20)
        return out.returncode, out.stdout, out.stderr

    def calls_made(self):
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def prompt(self, text, session='s1'):
        return self.hook('correction.sh', {'session_id': session, 'hook_event_name': 'UserPromptSubmit',
                                           'prompt': text})

    def test_corrections_are_logged_and_announced_in_one_line(self):
        for text in ['Không, dùng nhạc lofi chứ không phải nhạc EDM', 'thật ra tiêu đề phải giữ 2 giây',
                     'Lần sau đừng đặt chữ lên mặt người nói', 'No, keep the first take.',
                     'Actually the logo goes top right', 'I said captions at the bottom']:
            code, out, _ = self.prompt(text)
            self.assertEqual(code, 0)
            self.assertTrue(out.startswith('[bc] Possible correction'), text)
            self.assertEqual(out.count('\n'), 1, text)
        calls = self.calls_made()
        self.assertEqual(len(calls), 6)
        self.assertEqual(calls[0], 'run|append|correction|--text|Không, dùng nhạc lofi chứ không phải nhạc EDM|')

    def test_other_messages_cost_nothing(self):
        for text in ['Dựng vlog Đà Lạt 60 giây', 'Không khí ở đây thế nào?', 'Thêm nhạc nền nhẹ nhàng',
                     'Is the hook too long?', '/bc:setup', '<task-notification>no, actually</task-notification>',
                     'không ' + 'x' * 2000]:
            code, out, err = self.prompt(text)
            self.assertEqual((code, out), (0, ''), text)
        self.assertEqual(self.calls_made(), [])

    def test_long_quote_is_cut_and_one_line(self):
        self.prompt('Không, ' + 'rất dài\n' * 60)
        text = self.calls_made()[0].split('|')[4]
        self.assertLessEqual(len(text), 161)
        self.assertTrue(text.endswith('…'))

    def test_no_project_open_stays_silent(self):
        self.fail_cli(True)
        code, out, _ = self.prompt('Không, dùng bản thứ hai')
        self.assertEqual((code, out), (0, ''))
        self.assertFalse((self.folder / 'state' / 's1.corrections').exists())

    def test_manual_compact_is_held_once_then_quotes_come_back(self):
        self.prompt('Không, dùng bản thứ hai', session='abc')
        code, _, err = self.hook('precompact.sh', {'session_id': 'abc', 'trigger': 'manual'})
        self.assertEqual(code, 2)
        self.assertIn('1 correction(s)', err)
        self.assertEqual(self.hook('precompact.sh', {'session_id': 'abc', 'trigger': 'manual'})[0], 0)
        code, out, _ = self.hook('after-compact.sh', {'session_id': 'abc', 'source': 'compact'})
        self.assertEqual(code, 0)
        self.assertIn('- "Không, dùng bản thứ hai"', out)
        self.assertIn('bc:self-learn', out)
        self.assertFalse((self.folder / 'state' / 'abc.corrections').exists())
        # Nothing left: a plain reminder only.
        out = self.hook('after-compact.sh', {'session_id': 'abc', 'source': 'compact'})[1]
        self.assertTrue(out.startswith('[bc] Context was compacted: re-read'))

    def test_auto_compact_and_no_corrections_never_block(self):
        self.prompt('Không, dùng bản thứ hai', session='abc')
        self.assertEqual(self.hook('precompact.sh', {'session_id': 'abc', 'trigger': 'auto'})[0], 0)
        self.assertEqual(self.hook('precompact.sh', {'session_id': 'other', 'trigger': 'manual'})[0], 0)

    def test_after_compact_silent_without_a_project(self):
        self.fail_cli(True)
        self.assertEqual(self.hook('after-compact.sh', {'session_id': 'abc', 'source': 'compact'})[1], '')

    def test_skill_hook_still_records(self):
        self.hook('record-skill.sh', {'tool_name': 'Skill', 'tool_input': {'skill': 'bc:rough-cut'}})
        self.assertEqual(self.calls_made(), ['run|append|skill|--name|bc:rough-cut|--verified-by|hook|'])

    def test_hooks_json_points_at_existing_scripts(self):
        config = json.loads((HOOKS / 'hooks.json').read_text())
        for event, groups in config['hooks'].items():
            for group in groups:
                for hook in group['hooks']:
                    script = hook['command'].split('/hooks/')[1].rstrip('"')
                    self.assertTrue((HOOKS / script).is_file(), f'{event}: {script}')


if __name__ == '__main__':
    unittest.main()
