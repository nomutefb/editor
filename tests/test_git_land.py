"""Exercise actual commits and competing writers without network access."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

HELPER = Path(__file__).resolve().parents[1] / '.github/scripts/git_land.sh'

class LandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.origin = self.root / 'origin.git'
        self.work = self.root / 'work'
        self.git(self.root, 'init', '--bare', str(self.origin))
        self.git(self.root, 'clone', str(self.origin), str(self.work))
        self.git(self.work, 'checkout', '-b', 'main')
        self.git(self.work, 'config', 'user.email', 'test@example.test')
        self.git(self.work, 'config', 'user.name', 'Test')
        (self.work / 'data').mkdir()
        (self.work / 'data/a.txt').write_text('original\n')
        (self.work / 'data/rows.jsonl').write_text('{"base":1}\n')
        self.git(self.work, 'add', '.')
        self.git(self.work, 'commit', '-m', 'initial')
        self.git(self.work, 'push', '-u', 'origin', 'main')
        self.other = self.root / 'other'
        self.git(self.root, 'clone', '-b', 'main', str(self.origin), str(self.other))
        self.git(self.other, 'config', 'user.email', 'test@example.test')
        self.git(self.other, 'config', 'user.name', 'Other')

    def git(self, cwd, *args):
        r = subprocess.run(['git', *args], cwd=cwd, text=True, capture_output=True)
        if r.returncode: raise AssertionError(r.stderr)
        return r.stdout

    def land(self, *paths):
        env = dict(os.environ, RUNNER_TEMP=str(self.root / 'recovery'), PAGES_COALESCE='0')
        return subprocess.run(['bash', str(HELPER), 'test result', *paths], cwd=self.work, env=env, text=True, capture_output=True)

    def publish_other(self):
        self.git(self.other, 'add', '-A')
        self.git(self.other, 'commit', '-m', 'other')
        self.git(self.other, 'push')

    def test_save_and_optional_absent(self):
        (self.work / 'data/a.txt').write_text('changed\n')
        r = self.land('data', 'optional.json')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.git(self.work, 'show', 'origin/main:data/a.txt'), 'changed\n')

    def test_explicit_file_deletion(self):
        (self.work / 'data/a.txt').unlink()
        r = self.land('data/a.txt')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn('data/a.txt', self.git(self.work, 'ls-tree', '-r', '--name-only', 'origin/main'))

    def test_concurrent_explicit_deletion(self):
        (self.work / 'data/a.txt').unlink()
        (self.other / 'data/a.txt').unlink()
        self.publish_other()
        r = self.land('data/a.txt')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.work / 'data/a.txt').exists())

    def test_failed_commit_preserves_snapshot(self):
        hook = self.work / '.git/hooks/pre-commit'
        hook.write_text('#!/bin/sh\nexit 1\n'); hook.chmod(0o755)
        (self.work / 'data/a.txt').write_text('must survive\n')
        r = self.land('data')
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn('착지 성공', r.stdout)
        copies = list((self.root / 'recovery').glob('editor-recovery/run-*/files/data/a.txt'))
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies[0].read_text(), 'must survive\n')

    def test_remote_new_and_deleted_files(self):
        (self.other / 'data/a.txt').unlink()
        (self.other / 'data/new.txt').write_text('remote\n')
        self.publish_other()
        (self.work / 'data/rows.jsonl').write_text('{"base":1}\n{"local":1}\n')
        r = self.land('data')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.work / 'data/a.txt').exists())
        self.assertEqual((self.work / 'data/new.txt').read_text(), 'remote\n')

    def test_append_union_deduplicates(self):
        (self.other / 'data/rows.jsonl').write_text('{"base":1}\n{"both":1}\n{"remote":1}\n')
        self.publish_other()
        (self.work / 'data/rows.jsonl').write_text('{"base":1}\n{"both":1}\n{"local":1}\n')
        r = self.land('data')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = (self.work / 'data/rows.jsonl').read_text().splitlines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(len(set(lines)), 4)

if __name__ == '__main__':
    unittest.main()
