#!/usr/bin/env python3
"""Fake Residuum launcher for tests: same interface, no Residuum.

Prints a summary of the fixture. A line containing ERROR makes it fail with
that line on stderr, like a rejected program.
"""
import os
import sys
from pathlib import Path

command, fixture = sys.argv[1], Path(sys.argv[2]).resolve()
lines = fixture.read_text().splitlines()
if os.environ.get("FAKE_RESIDUUM_LOG"):
    with open(os.environ["FAKE_RESIDUUM_LOG"], "a") as log:
        log.write(f"{command} {fixture.name}{''.join(' ' + a for a in sys.argv[3:])}\n")
for line in lines:
    if "ERROR" in line:
        print(f"error en {fixture}: {line.strip()}", file=sys.stderr)
        sys.exit(1)
print(f"{command}: {len(lines)} líneas")
for line in lines:
    print(f"  {line}")
