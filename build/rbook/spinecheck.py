"""The spine check: ``./book check-spine``, also run at the start of every build.

It checks that:

* the YAML parses, and ids are unique across ``front_matter``, parts,
  sections and ``back_matter`` (``book.load_spine``);
* every ``owners`` value is the id of a spine entry;
* no key has a null value, and no list item has unbalanced parentheses.
  Both come from unquoted commas in YAML flow lists:
  ``[a (b, c)]`` is two items, ``a (b`` and ``c)``;
* every ``evidence`` entry resolves at ``book.pinned_commit``, in the forms
  the spine's header comment documents:

  - ``<path>``: a file or directory of the Residuum repository; ``*``, ``?``
    and ``[...]`` make it a glob that must match at least one file;
  - ``<path> (<anchor>, <anchor>)``: each anchor occurs in the file (a
    leading ``section `` is dropped; ``*`` inside an anchor matches any run
    of word characters, as in ``substitute_*``);
  - ``<path>#L<a>-L<b>``: the range lies within the file;
  - ``git:log``: the commit exists; ``git:tag <t>``: the tag exists;
  - ``series:<path>``: the path exists after ``~`` expansion;
  - ``sec:<id>`` or ``sec:<a>..<b>``: the ids exist (``a`` before ``b``);
  - ``listing:self``: the section declares at least one listing.

Files are read with ``git ls-tree`` and ``git show <commit>:<path>``, never
from the working tree.
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
from pathlib import Path, PurePosixPath

from .book import BuildFailed, load_spine

ANCHOR_RE = re.compile(r"^(?P<path>[^()]+?)\s*\((?P<anchors>.*)\)\s*$")
LINES_RE = re.compile(r"^(?P<path>[^#\s]+)#L(?P<start>\d+)(?:-L(?P<end>\d+))?$")
SEC_RE = re.compile(r"^sec:(?P<first>[^.\s]+(?:\.[^.\s]+)*?)(?:\.\.(?P<last>\S+))?$")


class Repo:
    """Read-only view of the Residuum repository at one commit."""

    def __init__(self, path, commit):
        self.path = Path(path)
        self.commit = commit
        self._files = None
        self._texts = {}

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.path), *args], capture_output=True, text=True)

    def check_commit(self):
        result = self.git("rev-parse", "--verify", "-q", f"{self.commit}^{{commit}}")
        if result.returncode != 0:
            raise LookupError(f"el commit {self.commit} no existe en {self.path}")

    def files(self):
        if self._files is None:
            result = self.git("ls-tree", "-r", "--name-only", "-z", self.commit)
            if result.returncode != 0:
                raise LookupError(f"git ls-tree {self.commit} falló: {result.stderr.strip()}")
            self._files = [f for f in result.stdout.split("\0") if f]
            self._dirs = {str(p) for f in self._files for p in PurePosixPath(f).parents if str(p) != "."}
            self._set = set(self._files)
        return self._files

    def is_file(self, path):
        self.files()
        return path in self._set

    def is_dir(self, path):
        self.files()
        return path.rstrip("/") in self._dirs

    def text(self, path):
        if path not in self._texts:
            result = self.git("show", f"{self.commit}:{path}")
            self._texts[path] = result.stdout if result.returncode == 0 else None
        return self._texts[path]

    def tag(self, name):
        return self.git("rev-parse", "--verify", "-q", f"refs/tags/{name}").returncode == 0


def check_spine(spine_path, residuum):
    """Return (spine or None, errors, count of evidence entries checked)."""
    errors = []
    try:
        spine = load_spine(spine_path, errors)
    except BuildFailed as failure:
        return None, failure.errors, 0
    name = Path(spine_path).name
    _walk(spine, "", name, errors)
    front = list(spine.get("front_matter") or [])
    entries = front + [s for p in spine["parts"] for s in p["sections"]] + list(spine.get("back_matter") or [])
    order = [item["id"] for item in front] + [p["id"] for p in spine["parts"]]
    for part in spine["parts"]:
        order.extend(s["id"] for s in part["sections"])
    order.extend(item["id"] for item in spine.get("back_matter") or [])
    position = {ident: n for n, ident in enumerate(order)}

    owners = spine.get("owners") or {}
    if not isinstance(owners, dict):
        errors.append(f"{name}: `owners` debe ser un mapa concepto -> id")
        owners = {}
    for concept, owner in owners.items():
        if owner not in position:
            errors.append(f"{name}: owners.{concept}: «{owner}» no es el id de ninguna entrada")

    commit = (spine.get("book") or {}).get("pinned_commit")
    repo = Repo(residuum, str(commit)) if commit is not None else None
    repo_problem = None
    checked = 0
    for entry in entries:
        evidence = entry.get("evidence")
        if evidence is None:
            continue
        if not isinstance(evidence, list):
            errors.append(f"{name}: {entry['id']}: `evidence` debe ser una lista")
            continue
        for item in evidence:
            where = f"{name}: {entry['id']}: evidencia «{item}»"
            if not isinstance(item, str):
                errors.append(f"{where}: debe ser un texto")
                continue
            checked += 1
            needs_repo = not item.startswith(("series:", "sec:", "listing:"))
            if needs_repo:
                if repo is None:
                    errors.append(f"{where}: falta book.pinned_commit")
                    continue
                if repo_problem is None:
                    try:
                        repo.check_commit()
                        repo.files()
                        repo_problem = ""
                    except LookupError as error:
                        repo_problem = str(error)
                        errors.append(f"{name}: {repo_problem}")
                if repo_problem:
                    continue
            problem = _evidence(item, entry, repo, position)
            if problem:
                errors.append(f"{where}: {problem}")
    return spine, errors, checked


def _walk(value, path, name, errors):
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{path}.{key}" if path else str(key)
            if child is None:
                errors.append(f"{name}: {here}: valor nulo (¿una coma sin comillas en una lista?)")
            _walk(child, here, name, errors)
    elif isinstance(value, list):
        for n, child in enumerate(value):
            here = f"{path}[{n}]"
            if child is None:
                errors.append(f"{name}: {here}: elemento nulo")
            if isinstance(child, str) and not _balanced(child):
                errors.append(f"{name}: {here}: paréntesis desequilibrados en «{child}» "
                              "(¿una coma sin comillas en una lista?)")
            _walk(child, here, name, errors)


def _balanced(text):
    depth = 0
    for ch in text:
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if depth < 0:
            return False
    return depth == 0


def _evidence(item, entry, repo, position):
    if item == "listing:self":
        return None if entry.get("listings") else "listing:self, pero la sección no declara `listings`"
    if item.startswith("series:"):
        path = Path(item[len("series:"):]).expanduser()
        return None if path.exists() else f"no existe {path}"
    if item.startswith("sec:"):
        match = SEC_RE.match(item)
        if not match:
            return "forma no válida; se espera sec:<id> o sec:<id>..<id>"
        first, last = match.group("first"), match.group("last")
        for ident in (first, last):
            if ident is not None and ident not in position:
                return f"«{ident}» no es el id de ninguna entrada"
        if last is not None and position[last] < position[first]:
            return f"«{last}» va antes que «{first}» en el spine"
        return None
    if item == "git:log":
        return None
    if item.startswith("git:"):
        match = re.fullmatch(r"git:tag\s+(\S+)", item)
        if not match:
            return "forma no válida; se espera git:log o git:tag <etiqueta>"
        return None if repo.tag(match.group(1)) else f"la etiqueta {match.group(1)} no existe"
    match = LINES_RE.match(item)
    if match:
        path = match.group("path")
        text = repo.text(path) if repo.is_file(path) else None
        if text is None:
            return f"{path} no existe en {repo.commit}"
        start = int(match.group("start"))
        end = int(match.group("end") or start)
        count = len(text.splitlines())
        if not 1 <= start <= end <= count:
            return f"líneas {start}-{end} fuera del fichero ({count} líneas)"
        return None
    match = ANCHOR_RE.match(item)
    if match:
        path = match.group("path").strip()
        text = repo.text(path) if repo.is_file(path) else None
        if text is None:
            return f"{path} no existe en {repo.commit}"
        missing = []
        for anchor in (a.strip() for a in match.group("anchors").split(",")):
            anchor = re.sub(r"^section\s+", "", anchor)
            if not anchor:
                continue
            pattern = r"\w*".join(re.escape(piece) for piece in anchor.split("*"))
            if not re.search(pattern, text):
                missing.append(anchor)
        return f"no aparece en {path}: {', '.join(missing)}" if missing else None
    path = item.strip()
    if any(ch in path for ch in "*?["):
        return None if any(fnmatch.fnmatchcase(f, path) for f in repo.files()) \
            else f"ningún fichero coincide con {path} en {repo.commit}"
    if repo.is_file(path) or repo.is_dir(path):
        return None
    return f"no existe en {repo.commit}"
