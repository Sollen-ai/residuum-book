"""Run listings through the Residuum launcher at the pinned commit.

The Residuum repository is never modified. The pinned commit is exported
read-only with ``git archive <commit> | tar -x`` into
``.cache/residuum-<commit>/`` and its launcher (``residuum``, which execs
``scripts/test_safe.py --cli``) runs there under that runner's limits. Cargo's
target directory is the export's own ``target/``, so compiled dependencies
persist across builds.
"""

from __future__ import annotations

import contextlib
import difflib
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .parse import CLI_COMMANDS

CACHE_VERSION = 1
# Safety net only; the runner enforces its own compile (45 s) and run (15 s)
# timeouts inside its cgroup.
OUTER_TIMEOUT = 300
PINNED_KINDS = CLI_COMMANDS + ("expect-error",)
DIAGNOSTIC_RE = re.compile(r"^.* \| -?\d+ \| \d+(?:\.\d+)?s \| \d+(?:\.\d+)? MiB RSS$")


class RunError(Exception):
    pass


@dataclass
class Result:
    command: str          # e.g. "query"
    text: str | None      # output shown in the book (stdout, or stderr for expect-error)
    error: str | None     # why the listing failed the build
    cached: bool = False


def normalise(text):
    text = text.replace("\r\n", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n" if lines else ""


def unified_diff(old, new, old_name, new_name):
    return "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                        old_name, new_name))


def split_stderr(stderr, fixture_name):
    """Drop test_safe.py's diagnostics (report path, timing rows, STOPPED line).

    Returns (kept text, infrastructure problem or None). A STOPPED line for the
    fixture with ``nonzero_exit`` is Residuum rejecting the program; any other
    STOPPED line (compile timeout, memory stop, cgroup failure) is the runner
    refusing to run, which never counts as an expected error.
    """
    kept, infra = [], None
    for line in stderr.splitlines():
        if line.startswith("Reports: ") or DIAGNOSTIC_RE.match(line):
            continue
        if line.startswith("STOPPED: "):
            if not line.startswith(f"STOPPED: {fixture_name}: nonzero_exit;"):
                infra = line
            continue
        kept.append(line)
    return "\n".join(kept), infra


class Runner:
    def __init__(self, root, commit, residuum, launcher=None, log=None, cache=None):
        self.root = Path(root)
        self.commit = commit
        self.residuum = Path(residuum)
        self.launcher = Path(launcher).resolve() if launcher else None
        self.log = log or (lambda message: print(message, file=sys.stderr))
        self.cache = Path(cache).resolve() if cache else self.root / ".cache"
        self._full = {}

    # -- git, read-only -------------------------------------------------
    def git(self, *args, binary=False):
        run = subprocess.run(["git", "-C", str(self.residuum), *args], capture_output=True)
        if run.returncode != 0:
            raise RunError(f"git {' '.join(args)}: {run.stderr.decode(errors='replace').strip()}")
        return run.stdout if binary else run.stdout.decode("utf-8")

    def full_commit(self, commit):
        if commit not in self._full:
            self._full[commit] = self.git("rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}").strip()
        return self._full[commit]

    def pinned(self):
        if not self.commit:
            raise RunError("el spine no tiene book.pinned_commit")
        return self.commit

    # -- includes ---------------------------------------------------------
    def include(self, spec):
        pinned = self.pinned()
        try:
            same = spec["commit"] == pinned or self.full_commit(spec["commit"]) == self.full_commit(pinned)
        except RunError as error:
            raise RunError(f"include {spec['spec']}: commit desconocido ({error})")
        if not same:
            raise RunError(f"include {spec['spec']}: el commit {spec['commit']} no es "
                           f"book.pinned_commit ({pinned})")
        text = self.git("show", f"{self.full_commit(pinned)}:{spec['path']}")
        if spec["start"] is None:
            return text if text.endswith("\n") or not text else text + "\n"
        lines = text.splitlines()
        start, end = spec["start"], spec["end"]
        if not 1 <= start <= end <= len(lines):
            raise RunError(f"include {spec['spec']}: rango L{start}-L{end} fuera del fichero "
                           f"({len(lines)} líneas)")
        return "\n".join(lines[start - 1:end]) + "\n"

    # -- launcher ---------------------------------------------------------
    def export(self):
        """The read-only export of the pinned commit; created on first use."""
        pinned = self.pinned()
        full = self.full_commit(pinned)
        target = self.cache / f"residuum-{pinned}"
        marker = target / ".rbook-export"
        if marker.exists() and marker.read_text().strip() == full:
            return target
        if target.exists():
            raise RunError(f"{target} existe pero no es una exportación completa de {full}; "
                           "bórralo a mano y vuelve a construir")
        partial = self.cache / f"residuum-{pinned}.partial"
        if partial.exists():
            shutil.rmtree(partial)
        partial.mkdir(parents=True)
        self.log(f"exportando residuum@{pinned} en {target} (git archive, sólo lectura)")
        archive = subprocess.Popen(["git", "-C", str(self.residuum), "archive", full],
                                   stdout=subprocess.PIPE)
        tar = subprocess.run(["tar", "-x", "-C", str(partial)], stdin=archive.stdout, capture_output=True)
        archive.stdout.close()
        if archive.wait() != 0 or tar.returncode != 0:
            raise RunError(f"no se pudo exportar {full}: {tar.stderr.decode(errors='replace')}")
        (partial / ".rbook-export").write_text(full + "\n")
        partial.rename(target)
        return target

    def launcher_path(self):
        if self.launcher:
            return self.launcher
        with self.residuum_lock():
            path = self.export() / "residuum"
        if not path.is_file():
            raise RunError(f"{path}: la exportación no tiene launcher")
        return path

    def setup_text(self, listing):
        if not listing.setup:
            return ""
        path = self.root / "setup" / f"{listing.setup}.res"
        if not path.is_file():
            raise RunError(f"setup={listing.setup}: no existe {path.relative_to(self.root)}")
        return path.read_text(encoding="utf-8")

    def source(self, listing):
        setup = self.setup_text(listing)
        body = listing.body + "\n"
        return (setup.rstrip("\n") + "\n" + body) if setup else body

    def key(self, listing, command, source):
        launcher = "" if self.launcher is None else str(self.launcher)
        # The label names the fixture file, which appears in error messages.
        material = [CACHE_VERSION, self.commit, listing.kind, command, launcher,
                    listing.label, source]
        if listing.steps is not None or listing.trace:
            material.append(self.options(listing))
        material = json.dumps(material)
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    @contextlib.contextmanager
    def residuum_lock(self):
        """Serialise every real launcher call (and the export) across processes.

        Residuum's runner allows one job; several builds may run at once (one
        agent per section), so they queue here instead of running in parallel.
        """
        if self.launcher is not None:
            yield
            return
        self.cache.mkdir(parents=True, exist_ok=True)
        with open(self.cache / "residuum.lock", "w") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    @staticmethod
    def options(listing):
        """The launcher's own options (--steps N, --trace), in its order."""
        extra = []
        if listing.steps is not None:
            extra += ["--steps", str(listing.steps)]
        if listing.trace:
            extra.append("--trace")
        return extra

    def invoke(self, launcher, command, fixture, extra=()):
        with self.residuum_lock():
            return self._invoke(launcher, command, fixture, extra)

    def _invoke(self, launcher, command, fixture, extra=()):
        args = [str(launcher), command, str(fixture), *extra]
        if not os.access(launcher, os.X_OK):
            args = [sys.executable] + args
        try:
            run = subprocess.run(args, cwd=fixture.parent, capture_output=True, timeout=OUTER_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise RunError(f"el launcher no terminó en {OUTER_TIMEOUT} s")
        out = run.stdout.decode("utf-8", errors="replace")
        err = run.stderr.decode("utf-8", errors="replace")
        prefixes = [(str(fixture.parent) + os.sep, ""), (str(fixture.parent), ".")]
        if self.launcher is None:
            prefixes.append((str(launcher.parent), "<residuum>"))
        for old, new in prefixes:
            out, err = out.replace(old, new), err.replace(old, new)
        return run.returncode, out, err

    def run(self, listing):
        """Run one listing; return a Result. Infrastructure problems are errors."""
        command = (listing.cmd or "run") if listing.kind == "expect-error" else listing.kind
        try:
            source = self.source(listing)
            key = self.key(listing, command, source)
            cached = self.cache / "outputs" / f"{key}.json"
            if cached.exists():
                data = json.loads(cached.read_text(encoding="utf-8"))
                status, out, err, from_cache = data["exit"], data["stdout"], data["stderr"], True
            else:
                launcher = self.launcher_path()
                rundir = self.cache / "run" / key[:16]
                rundir.mkdir(parents=True, exist_ok=True)
                fixture = rundir / f"{listing.label}.res"
                fixture.write_text(source, encoding="utf-8")
                self.log(f"ejecutando listado {listing.label}: residuum {command}")
                status, out, raw_err = self.invoke(launcher, command, fixture, self.options(listing))
                err, infra = split_stderr(raw_err, fixture.name)
                if infra:
                    hint = (" La compilación en frío puede superar los 45 s del runner; lo ya "
                            "compilado se conserva, así que vuelve a construir (o ./book warm)."
                            if "compile" in infra else "")
                    raise RunError(f"el runner de Residuum no ejecutó el listado: {infra}.{hint}")
                cached.parent.mkdir(parents=True, exist_ok=True)
                cached.write_text(json.dumps(dict(exit=status, stdout=out, stderr=err)), encoding="utf-8")
                from_cache = False
        except RunError as error:
            return Result(command, None, str(error))
        if listing.kind == "expect-error":
            if status == 0:
                return Result(command, None, f"run=expect-error, pero residuum {command} terminó bien",
                              from_cache)
            return Result(command, normalise(err or out), None, from_cache)
        if status != 0:
            return Result(command, None, f"residuum {command} falló (código {status}):\n{normalise(err)}",
                          from_cache)
        return Result(command, normalise(out), None, from_cache)


def expected_path(root, label):
    return Path(root) / "expected" / f"{label}.out"


def compare(root, listing, text):
    """Return (status, diff) with status 'same', 'missing' or 'differs'."""
    path = expected_path(root, listing.label)
    if not path.exists():
        return "missing", ""
    old = path.read_text(encoding="utf-8")
    if old == text:
        return "same", ""
    return "differs", unified_diff(old, text, f"expected/{listing.label}.out", f"actual/{listing.label}.out")
