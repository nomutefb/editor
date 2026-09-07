#!/usr/bin/env python3
"""Compatibility entrypoint for the Node shell assembler."""
from pathlib import Path
import subprocess
import sys
if __name__ == '__main__':
    sys.exit(subprocess.call(['node', str(Path(__file__).with_suffix('.mjs')), *sys.argv[1:]]))
