"""Appendix C: ``docs/language-reference.md`` from the Residuum repository at
``book.pinned_commit``, read with ``git show`` (never the working tree).

The document's ``#`` title is dropped (the appendix heading replaces it);
``##`` becomes a numbered subsection (C.1), ``###`` a sub-subsection
(C.1.1), deeper levels stay unnumbered. The text is rendered as plain
Markdown: no book references, citations or listing syntax apply, because the
document is Residuum's, not the book's. Relative links point to the file on
GitHub at the full pinned commit.
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass

from . import gitinfo
from .parse import FENCE_RE, HEADING_RE, Heading

REFERENCE_ID = "appendix-c"
REFERENCE_PATH = "docs/language-reference.md"
GITHUB = "https://github.com/Sollen-ai/residuum/blob"
LINK_RE = re.compile(r"(?<!!)\[(?P<text>[^\]\n]*)\]\((?P<target>[^)\s]+)\)")


@dataclass
class Raw:
    """Markdown copied from the Residuum repository; rendered as is."""
    text: str


def split_reference(text, entry_number, entry_id, full_commit, path=REFERENCE_PATH):
    """Return the blocks (Heading | Raw) of the reference document."""
    blocks, buffer, fence = [], [], None
    sub = subsub = unnumbered = 0
    base = posixpath.dirname(path)

    def flush():
        if buffer:
            blocks.append(Raw(_links("\n".join(buffer) + "\n", base, full_commit, fence_aware=True)))
            buffer.clear()

    for n, line in enumerate(text.splitlines(), 1):
        if fence is not None:
            buffer.append(line)
            if re.match(r"^ {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$", line):
                fence = None
            continue
        match = FENCE_RE.match(line)
        if match:
            fence = match.group("fence")
            buffer.append(line)
            continue
        heading = HEADING_RE.match(line)
        if not heading:
            buffer.append(line)
            continue
        flush()
        level = len(heading.group("hashes"))
        title = heading.group("title").rstrip("#").rstrip()
        if level == 1:
            continue
        block = Heading(level, _links(title, base, full_commit), None, n)
        if level == 2:
            sub, subsub = sub + 1, 0
            block.number = f"{entry_number}.{sub}"
        elif level == 3:
            subsub += 1
            block.number = f"{entry_number}.{max(sub, 1)}.{subsub}"
        unnumbered += 1
        suffix = block.number[len(entry_number) + 1:] if block.number else f"h{unnumbered}"
        block.anchor = f"sec-{entry_id}-{suffix}"
        blocks.append(block)
    flush()
    return blocks


def _links(text, base, full_commit, fence_aware=False):
    """Point relative Markdown links at the file on GitHub at the commit."""

    def fix(match):
        target = match.group("target")
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
            return match.group(0)
        path, _, anchor = target.partition("#")
        resolved = posixpath.normpath(posixpath.join(base, path))
        url = f"{GITHUB}/{full_commit}/{resolved}" + (f"#{anchor}" if anchor else "")
        return f"[{match.group('text')}]({url})"

    if not fence_aware:
        return LINK_RE.sub(fix, text)
    out, fence = [], None
    for line in text.split("\n"):
        if fence is None:
            match = FENCE_RE.match(line)
            if match:
                fence = match.group("fence")
                out.append(line)
            else:
                out.append(LINK_RE.sub(fix, line))
        else:
            out.append(line)
            if re.match(r"^ {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$", line):
                fence = None
    return "\n".join(out)


def load_reference(book, residuum, errors):
    """Fill the Appendix C entry from the pinned commit.

    A failure to read it is an error in a final build and a placeholder with
    a warning in a draft.
    """
    entry = next((e for e in book.back if e.generated == "reference"), None)
    if entry is None:
        return
    try:
        if not book.commit:
            raise gitinfo.GitError("el spine no tiene book.pinned_commit")
        full, _ = gitinfo.commit_info(residuum, book.commit)
        text = gitinfo.show(residuum, full, REFERENCE_PATH)
    except gitinfo.GitError as error:
        message = f"{entry.id}: no se puede leer {REFERENCE_PATH} en {book.commit}: {error}"
        if book.draft:
            entry.placeholder = f"Falta la referencia del lenguaje: no se pudo leer {REFERENCE_PATH}."
            book.warnings.append(message)
        else:
            errors.append(message)
        return
    entry.blocks = split_reference(text, entry.number, entry.id, full)
    entry.source = f"{REFERENCE_PATH} en residuum@{full}"
