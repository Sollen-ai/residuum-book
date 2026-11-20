"""Read-only git queries for the colophon and Appendix C.

Every call is ``git -C <repo> ...`` with a read-only subcommand
(``rev-parse``, ``show``, ``status``); nothing is ever written to the
repository.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(Exception):
    pass


def git(repo, *args):
    try:
        run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    except OSError as error:
        raise GitError(f"git {' '.join(args)}: {error}")
    if run.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {run.stderr.decode(errors='replace').strip()}")
    return run.stdout.decode("utf-8")


def commit_info(repo, commit):
    """(full sha, ISO commit date) of ``commit`` in ``repo``."""
    full = git(repo, "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}").strip()
    if not full:
        raise GitError(f"commit desconocido: {commit}")
    date = git(repo, "show", "-s", "--format=%cI", full).strip()
    return full, date


def show(repo, commit, path):
    """The text of ``path`` at ``commit`` (``git show <commit>:<path>``)."""
    return git(repo, "show", f"{commit}:{path}")


def tool_state(repo, paths=("build", "book")):
    """A short description of the build tool's own git state, in Spanish."""
    repo = Path(repo)
    try:
        head = git(repo, "log", "-1", "--format=%h %cs").strip()
    except GitError:
        return "fuera de un repositorio git"
    if not head:
        return "repositorio git sin commits"
    short, date = head.split(" ", 1)
    try:
        dirty = bool(git(repo, "status", "--porcelain", "--", *paths).strip())
    except GitError:
        dirty = False
    state = f"commit {short} del {date}"
    if dirty:
        state += ", con cambios sin confirmar en " + " y ".join(f"{p}" for p in paths)
    return state
