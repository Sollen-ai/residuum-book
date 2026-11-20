"""out/residuum.txt: the whole book as plain text.

Headings are numbered as in the HTML; references and citations become
words; listings are indented four spaces and followed by their output.
Prose keeps its Markdown, which reads well as plain text, without the
``covers`` comments.
"""

from __future__ import annotations

import html
import re

from .bib import render_sources
from .parse import Figure, Heading, Listing, TableCaption
from .reference import Raw
from .runner import PINNED_KINDS

WIDTH = 72


def _indent(text, prefix="    "):
    return "\n".join(prefix + line if line else "" for line in text.rstrip("\n").split("\n"))


def _underline(text, char):
    return f"{text}\n{char * min(max(len(text), 3), WIDTH)}"


def _strip_tags(fragment):
    fragment = re.sub(r"<li[^>]*>", "- ", fragment)
    fragment = re.sub(r"</(li|p|h\d)>", "\n", fragment)
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def render_text(book, colophon=None):
    from .render import _prose   # shares the reference and citation handling

    scratch = []      # problems are reported by the HTML render, once

    def prose(text, where=""):
        return _prose(book, text, where, scratch, link=False).strip("\n")

    out = [_underline(book.title, "="), ""]
    if book.authors:
        out += [*book.authors, ""]
    if book.edition:
        out += [f"Edición {book.edition}. Describe Residuum en el commit {book.commit or ''}.", ""]
    if book.draft:
        out += ["Borrador: este build admite secciones y salidas pendientes.", ""]
    if colophon:
        out += [_underline("Colofón", "-"), ""]
        out += [f"{label}: {value}" for label, value in colophon.lines()]
        out.append("")

    for entry in book.front:
        out += ["", _underline(entry.heading, "="), ""]
        out += _entry(book, entry, prose)
    out += [_underline("Índice", "-"), ""]
    for entry in book.front:
        out.append(entry.heading)
    for part in book.parts:
        out.append(f"Parte {part.number}: {part.title}")
        for entry in part.sections:
            out.append(f"  {entry.heading}")
            out += [f"    {h.number} {prose(h.title)}" for h in _subsections(entry)]
    for entry in book.back:
        out.append(entry.heading)
        out += [f"    {h.number} {h.title}" for h in _subsections(entry)]
    out.append("")
    out += [_underline("Índice de listados", "-"), ""]
    if book.listings:
        out += [f"Listado {l.number}. {getattr(l, 'caption_text', l.caption)} ({getattr(l, 'where', '')})"
                for l in book.listings]
    else:
        out.append("No hay listados.")
    out.append("")
    for name, items in (("figuras", book.figures), ("tablas", book.tables)):
        if items:
            word = "Figura" if name == "figuras" else "Tabla"
            out += [_underline(f"Índice de {name}", "-"), ""]
            out += [f"{word} {i.number}. {getattr(i, 'caption_text', i.caption)} ({getattr(i, 'where', '')})"
                    for i in items]
            out.append("")

    for part in book.parts:
        out += ["", _underline(f"Parte {part.number}: {part.title}", "="), ""]
        for entry in part.sections:
            out += ["", _underline(entry.heading, "-"), ""]
            out += _entry(book, entry, prose)
    for entry in book.back:
        out += ["", _underline(entry.heading, "="), ""]
        out += _entry(book, entry, prose)
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip("\n") + "\n"


def _subsections(entry):
    return [b for b in entry.blocks if isinstance(b, Heading) and b.level == 2 and b.number]


def _entry(book, entry, prose):
    if entry.generated == "listings":
        return _appendix(book, prose)
    if entry.generated == "sources":
        return [_strip_tags(render_sources(book.bib, book.cited)), ""]
    if entry.placeholder:
        return [f"[{entry.placeholder}]", ""]
    out = []
    if entry.generated == "reference" and getattr(entry, "source", None):
        out += [f"Incluido de {entry.source}.", ""]
    for block in entry.blocks:
        if isinstance(block, Raw):
            out += [block.text.strip("\n"), ""]
        elif isinstance(block, str):
            text = prose(block)
            if text.strip():
                out += [text, ""]
        elif isinstance(block, Heading):
            title = block.title if entry.generated == "reference" else prose(block.title)
            number = f"{block.number} " if block.number else ""
            out += ["", f"{number}{title}", ""]
        elif isinstance(block, Figure) and block.dot is not None:
            out += [f"Figura {block.number}. {getattr(block, 'caption_text', block.caption)}", "",
                    _indent(f"[Dibujo] {block.alt}"), ""]
        elif isinstance(block, Figure):
            out += [f"[Figura {block.number}. {block.caption_text if hasattr(block, 'caption_text') else block.caption}"
                    f" ({block.src})]", ""]
        elif isinstance(block, TableCaption):
            out += [f"Tabla {block.number}. {getattr(block, 'caption_text', block.caption)}", ""]
        elif isinstance(block, Listing):
            out += _listing(block)
    return out


def _listing(listing):
    caption = getattr(listing, "caption_text", listing.caption)
    out = [f"Listado {listing.number}. {caption}", ""]
    out += [_indent(listing.shown or listing.body + "\n"), ""]
    if listing.kind == "include":
        spec = listing.include
        lines = f", líneas {spec['start']}–{spec['end']}" if spec["start"] else ""
        out += [f"  (Copiado de {spec['path']} en residuum@{spec['commit']}{lines}.)", ""]
    result = listing.result
    if listing.kind in PINNED_KINDS and result is not None and result.text is not None:
        word = "Error" if listing.kind == "expect-error" else "Salida"
        label = f"  {word} de residuum {result.command}:"
        if getattr(listing, "unpinned", False):
            label += " (salida sin fijar en expected/)"
        out += [label, "", _indent(result.text or "(sin salida)\n"), ""]
    return out


def _appendix(book, prose):
    if not book.listings:
        return ["No hay listados.", ""]
    out, current = [], None
    for listing in book.listings:
        if listing.section_id != current:
            current = listing.section_id
            entry = next(e for e in book.entries() if e.id == current)
            out += ["", entry.heading, ""]
        caption = getattr(listing, "caption_text", listing.caption)
        out += [f"Listado {listing.number}. {caption}", "", prose(listing.explanation), ""]
    return out
