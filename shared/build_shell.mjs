import {readFileSync, writeFileSync, readdirSync} from 'node:fs';
import {dirname, join, basename, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export function buildShell(check = false) {
  const source = join(ROOT, 'viewer-src');
  const names = JSON.parse(readFileSync(join(source, 'manifest.json'), 'utf8'));
  if (!Array.isArray(names) || !names.length || new Set(names).size !== names.length || names.some(n => basename(n) !== n || !n.endsWith('.part'))) throw Error('Invalid shell manifest');
  const actual = readdirSync(source).filter(n => n.endsWith('.part'));
  if (actual.length !== names.length || actual.some(n => !names.includes(n))) throw Error('Unlisted or missing shell fragment');
  const result = Buffer.concat(names.map(n => readFileSync(join(source, n))));
  const target = join(ROOT, 'viewer/index.html');
  if (check) {
    if (!result.equals(readFileSync(target))) throw Error('Shell differs: run python3 shared/build_shell.py');
  } else writeFileSync(target, result);
  console.log(`Shell: ${names.length} source sections, ${result.length} bytes`);
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) buildShell(process.argv.includes('--check'));
