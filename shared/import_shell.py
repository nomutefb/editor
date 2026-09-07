#!/usr/bin/env python3
"""Import explicit edits made by legacy viewer generators into the authored fragments."""
from pathlib import Path
import difflib
import json

ROOT = Path(__file__).resolve().parent.parent

def main():
    folder = ROOT / 'viewer-src'
    names = json.loads((folder / 'manifest.json').read_text())
    fragments = [(folder / n).read_text() for n in names]
    before = ''.join(fragments)
    after = (ROOT / 'viewer/index.html').read_text()
    if before == after:
        print('Shell source is already current'); return
    old_lines, new_lines = before.splitlines(keepends=True), after.splitlines(keepends=True)
    ops = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes()
    def new_offset(offset):
        for tag, a, b, c, d in ops:
            if a <= offset <= b:
                if tag == 'equal': return c + offset - a
                return c if offset == a else d
        return len(new_lines)
    bounds, total = [0], 0
    for part in fragments[:-1]:
        total += len(part.splitlines(keepends=True)); bounds.append(new_offset(total))
    bounds.append(len(new_lines))
    for name, a, b in zip(names, bounds, bounds[1:]):
        (folder / name).write_text(''.join(new_lines[a:b]))
    assert ''.join((folder / n).read_text() for n in names) == after
    print('Imported legacy generator changes; review viewer-src diff before committing')

if __name__ == '__main__':
    main()
