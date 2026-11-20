"""Render ```dot {#fig:...}``` figures to SVG with Graphviz, at build time.

``dot -Tsvg`` gets the source on stdin. ``-G/-N/-Efontname`` set the
default font to DejaVu Sans, the book's sans font (present on the system and
embedded in the PDF); a ``fontname`` in the source overrides them. SVGs are
cached in ``<cache>/dot/<sha256 of the source>.svg``, so an unchanged figure
never calls ``dot`` again.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
from pathlib import Path

DOT = "/usr/bin/dot"
FONT = "DejaVu Sans"
FONT_ARGS = [f"-Gfontname={FONT}", f"-Nfontname={FONT}", f"-Efontname={FONT}"]
TIMEOUT = 60

PROLOG_RE = re.compile(r"<\?xml.*?\?>|<!DOCTYPE.*?>|<!--.*?-->", re.S)
ID_RE = re.compile(r'\bid="([^"]*)"')
LOCAL_REF_RE = re.compile(r'(url\(#|href="#)')


def render_figures(book, cache, errors):
    """Set ``figure.svg`` on every dot figure; problems go to ``errors``."""
    folder = Path(cache) / "dot"
    for entry in book.entries():
        for block in entry.blocks:
            if getattr(block, "dot", None) is None:
                continue
            where = f"{entry.path.relative_to(book.root) if entry.path else entry.id}:{block.line}"
            try:
                svg = svg_for(block.dot, folder)
            except DotError as error:
                errors.append(f"{where}: figura {block.label}: {error}")
                continue
            block.svg = inline_svg(svg, f"fig-{block.label}", block.alt)


class DotError(Exception):
    pass


def svg_for(source, folder):
    """Return the SVG text for ``source``, from the cache or from ``dot``."""
    key = hashlib.sha256(source.encode("utf-8")).hexdigest()
    path = folder / f"{key}.svg"
    if path.exists():
        return path.read_text(encoding="utf-8")
    try:
        done = subprocess.run([DOT, "-Tsvg", *FONT_ARGS], input=source, capture_output=True,
                              text=True, timeout=TIMEOUT)
    except FileNotFoundError:
        raise DotError(f"no se encuentra Graphviz ({DOT})")
    except subprocess.TimeoutExpired:
        raise DotError(f"dot no terminó en {TIMEOUT} s")
    if done.returncode != 0 or "<svg" not in done.stdout:
        message = done.stderr.strip() or f"código de salida {done.returncode}"
        raise DotError(f"dot falló:\n{message}")
    folder.mkdir(parents=True, exist_ok=True)
    # Written atomically: concurrent builds share the cache.
    handle, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8") as out:
        out.write(done.stdout)
    os.replace(tmp, path)
    return done.stdout


def inline_svg(svg, prefix, alt):
    """The SVG as an inline element: no prolog, doctype or comments; ids
    prefixed so several figures on one page do not clash; ``role="img"`` and
    ``aria-label`` set to the alt text."""
    from html import escape

    svg = PROLOG_RE.sub("", svg).strip()
    svg = ID_RE.sub(lambda m: f'id="{prefix}-{m.group(1)}"', svg)
    svg = LOCAL_REF_RE.sub(lambda m: f"{m.group(1)}{prefix}-", svg)
    return svg.replace("<svg", f'<svg role="img" aria-label="{escape(alt)}"', 1)
