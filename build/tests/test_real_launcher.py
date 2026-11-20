"""Opt-in: the real Residuum launcher at the pinned commit.

Run with RBOOK_REAL_LAUNCHER=1. It uses the book's own .cache (the export of
the pinned commit and its Cargo target), so a warm cache makes it fast; a
cached output is not re-run.
"""

import os
import shutil
from pathlib import Path

import pytest

from conftest import FIXTURES
from rbook.cli import main

BOOK = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(os.environ.get("RBOOK_REAL_LAUNCHER") != "1",
                                reason="set RBOOK_REAL_LAUNCHER=1 to run the real launcher")


def test_real_launcher_run_and_expect_error(tmp_path, capsys):
    root = tmp_path / "real"
    shutil.copytree(FIXTURES / "real", root)
    code = main(["build", "--spine", str(root / "spine.yaml"), "--cache", str(BOOK / ".cache")])
    err = capsys.readouterr().err
    assert code == 0, err
    page = (root / "out" / "index.html").read_text()
    assert "Known after close:" in page
    assert "unknown verb `keeps`" in page
