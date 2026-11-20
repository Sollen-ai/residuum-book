"""``./book staleness``: how far the book is behind the Residuum repository.

The book describes Residuum at ``book.pinned_commit``. This report compares
that commit with a later revision (``--ref``, by default ``main``) of the
local Residuum repository, read-only:

* how many commits the pin is behind, and whether it is an ancestor;
* which files changed between the two;
* which spine entries depend on a changed file, through their repo
  ``evidence`` (paths, globs, directories, anchors, line ranges), their
  ``run=include`` listings, or Appendix C (``docs/language-reference.md``);
* whether runnable listings may change: they run the whole language, so any
  change under ``src/`` can change an output. Re-pinning and rebuilding shows
  the actual differences (``expected/`` diffs).

It never fetches: update the local Residuum checkout first (``git fetch``
there, by its owner) if the reference should be the remote's state.
"""

from __future__ import annotations

import fnmatch
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .book import REFERENCE
from .reference import REFERENCE_PATH
from .spinecheck import ANCHOR_RE, LINES_RE

LISTING_SOURCES = ("src/",)   # changes here can change any runnable listing's output


class StalenessError(Exception):
    pass


def _git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise StalenessError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def evidence_pattern(item):
    """The repo path or glob an evidence entry depends on, or None if it is not repo evidence."""
    if not isinstance(item, str) or item.startswith(("series:", "sec:", "listing:", "git:", "diagrams:")):
        return None
    match = LINES_RE.match(item)
    if match:
        return match.group("path")
    match = ANCHOR_RE.match(item)
    if match:
        return match.group("path").strip()
    return item.strip()


def matches(pattern, path):
    if any(ch in pattern for ch in "*?["):
        return fnmatch.fnmatchcase(path, pattern)
    return path == pattern or path.startswith(pattern.rstrip("/") + "/")


@dataclass
class Report:
    pinned: str
    ref: str
    pinned_full: str
    ref_full: str
    ancestor: bool
    behind: int
    changed: list                       # (status, path)
    affected: dict = field(default_factory=dict)   # entry id -> sorted changed paths
    titles: dict = field(default_factory=dict)     # entry id -> title
    listings_may_change: list = field(default_factory=list)  # changed paths under LISTING_SOURCES

    @property
    def current(self):
        return self.pinned_full == self.ref_full

    def markdown(self):
        lines = ["# Vigencia del libro", "",
                 f"- Commit fijado: `{self.pinned}` (`{self.pinned_full}`)",
                 f"- Comparado con: `{self.ref}` (`{self.ref_full}`)"]
        if self.current:
            lines += ["", "El libro está al día: el commit fijado es la referencia."]
            return "\n".join(lines) + "\n"
        relation = (f"{self.behind} commit(s) por detrás" if self.ancestor
                    else f"no es antecesor de `{self.ref}`; {self.behind} commit(s) en `{self.ref}` no están en él")
        lines += [f"- Relación: {relation}",
                  f"- Ficheros cambiados: {len(self.changed)}", ""]
        if self.listings_may_change:
            lines += [f"Cambió código bajo {', '.join(LISTING_SOURCES)} ({len(self.listings_may_change)} "
                      "fichero(s)). Las salidas de los listados ejecutables pueden cambiar: para verlas, "
                      "fija el nuevo commit y reconstruye; el build muestra cada diferencia con expected/.", ""]
        if self.affected:
            lines += ["## Entradas que citan ficheros cambiados", "",
                      "| Id | Título | Ficheros |", "|---|---|---|"]
            for ident, paths in self.affected.items():
                shown = ", ".join(f"`{p}`" for p in paths[:6]) + (f" y {len(paths) - 6} más" if len(paths) > 6 else "")
                lines.append(f"| {ident} | {self.titles.get(ident, '')} | {shown} |")
        else:
            lines.append("Ninguna entrada del spine cita un fichero cambiado.")
        return "\n".join(lines) + "\n"


def staleness(spine, listings, residuum, ref="main"):
    """Compare ``book.pinned_commit`` with ``ref`` in ``residuum``. ``listings``: parsed listings."""
    pinned = str((spine.get("book") or {}).get("pinned_commit") or "")
    if not pinned:
        raise StalenessError("el spine no tiene book.pinned_commit")
    pinned_full = _git(residuum, "rev-parse", "--verify", f"{pinned}^{{commit}}").strip()
    ref_full = _git(residuum, "rev-parse", "--verify", f"{ref}^{{commit}}").strip()
    ancestor = subprocess.run(["git", "-C", str(residuum), "merge-base", "--is-ancestor", pinned_full, ref_full],
                              capture_output=True).returncode == 0
    behind = int(_git(residuum, "rev-list", "--count", f"{pinned_full}..{ref_full}").strip() or 0)
    changed = []
    for line in _git(residuum, "diff", "--name-status", "--no-renames", pinned_full, ref_full).splitlines():
        status, _, path = line.partition("\t")
        if path:
            changed.append((status, path))
    report = Report(pinned, ref, pinned_full, ref_full, ancestor, behind, changed)
    paths = [p for _, p in changed]
    report.listings_may_change = [p for p in paths if p.startswith(LISTING_SOURCES)]

    entries = list(spine.get("front_matter") or [])
    for part in spine.get("parts") or []:
        entries.extend(part.get("sections") or [])
    entries.extend(spine.get("back_matter") or [])
    depends = {}
    for entry in entries:
        ident = entry["id"]
        report.titles[ident] = entry.get("title", "")
        patterns = depends.setdefault(ident, set())
        for item in entry.get("evidence") or []:
            pattern = evidence_pattern(item)
            if pattern:
                patterns.add(pattern)
        if ident == REFERENCE:
            patterns.add(REFERENCE_PATH)
    for listing in listings:
        if listing.include:
            depends.setdefault(listing.section_id, set()).add(listing.include["path"])
    for ident, patterns in depends.items():
        hit = sorted({p for p in paths for pattern in patterns if matches(pattern, p)})
        if hit:
            report.affected[ident] = hit
    return report


def write(report, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True)
    path = out_dir / "staleness.md"
    path.write_text(report.markdown(), encoding="utf-8")
    return path
