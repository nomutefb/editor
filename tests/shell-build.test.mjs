import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, cpSync, mkdirSync, readFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import {execFileSync} from 'node:child_process';

// Run the actual workflow stamping function in an isolated copy of the shell.
test('version workflow stamps authored source and survives rebuilding', () => {
  const root = resolve(import.meta.dirname, '..');
  const dir = mkdtempSync(join(tmpdir(), 'editor-stamp-'));
  try {
    cpSync(join(root, 'viewer-src'), join(dir, 'viewer-src'), {recursive: true});
    mkdirSync(join(dir, 'shared')); mkdirSync(join(dir, 'viewer'));
    cpSync(join(root, 'shared/build_shell.mjs'), join(dir, 'shared/build_shell.mjs'));
    const workflow = readFileSync(join(root, '.github/workflows/stamp-version.yml'), 'utf8');
    const fn = workflow.match(/          stamp_once\(\) \{[\s\S]*?\n          \}/)?.[0];
    assert.ok(fn, 'stamping function exists');
    execFileSync('bash', ['-eu', '-c', `${fn}\nstamp_once`], {
      cwd: dir, env: {...process.env, SHA: 'abc1234', TS: '260907_0900'},
    });
    execFileSync(process.execPath, ['shared/build_shell.mjs'], {cwd: dir});
    execFileSync(process.execPath, ['shared/build_shell.mjs', '--check'], {cwd: dir});
    assert.match(readFileSync(join(dir, 'viewer/index.html'), 'utf8'), /const BUILD_STAMP = 'abc1234 · 260907_0900';/);
  } finally { rmSync(dir, {recursive: true, force: true}); }
});
