import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from rbook.cli import main  # noqa: E402

FIXTURES = HERE / "fixtures"
FAKE = FIXTURES / "fake_residuum.py"


class Project:
    def __init__(self, root, capsys):
        self.root = root
        self.capsys = capsys
        self.spine = root / "spine.yaml"

    def cli(self, *args, launcher=True, residuum=None):
        argv = list(args) + ["--spine", str(self.spine)]
        if launcher:
            argv += ["--launcher", str(FAKE)]
        if residuum:
            argv += ["--residuum", str(residuum)]
        self.capsys.readouterr()
        code = main(argv)
        captured = self.capsys.readouterr()
        return code, captured.err + captured.out

    def build(self, *extra, **kw):
        return self.cli("build", *extra, **kw)

    def html(self):
        return (self.root / "out" / "index.html").read_text(encoding="utf-8")

    def section(self, ident):
        return self.root / "sections" / f"{ident}.md"

    def load(self):
        return yaml.safe_load(self.spine.read_text(encoding="utf-8"))

    def save(self, spine):
        self.spine.write_text(yaml.safe_dump(spine, allow_unicode=True, sort_keys=False), encoding="utf-8")


@pytest.fixture
def project(tmp_path, capsys):
    root = tmp_path / "book"
    shutil.copytree(FIXTURES / "sample", root)
    return Project(root, capsys)


@pytest.fixture
def accepted(project):
    code, out = project.cli("accept", "--all")
    assert code == 0, out
    return project


@pytest.fixture
def repo(tmp_path):
    """A throwaway git repository standing in for Residuum (for includes)."""
    root = tmp_path / "residuum"
    root.mkdir()
    (root / "docs").mkdir()
    (root / "docs" / "ten.txt").write_text("".join(f"línea {n}\n" for n in range(1, 11)))
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    for args in (["init", "-q"], ["add", "."], ["commit", "-q", "-m", "one"]):
        subprocess.run(["git", "-C", str(root), *args], check=True, env=env)
    (root / "docs" / "ten.txt").write_text("cambiado\n")
    for args in (["commit", "-q", "-am", "two"],):
        subprocess.run(["git", "-C", str(root), *args], check=True, env=env)

    def sha(rev):
        return subprocess.run(["git", "-C", str(root), "rev-parse", rev], check=True,
                              capture_output=True, text=True).stdout.strip()

    return root, sha("HEAD~1"), sha("HEAD")


@pytest.fixture
def checked(tmp_path, capsys):
    """The phase 3 fixture: sections that pass every check."""
    root = tmp_path / "book"
    shutil.copytree(FIXTURES / "checks", root)
    return Project(root, capsys)
