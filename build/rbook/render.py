"""Render the numbered book as one HTML page."""

from __future__ import annotations

import html
import re

import jinja2
from markdown_it import MarkdownIt

from .bib import render_sources, resolve_cites
from .book import resolve_refs
from .parse import FENCE_RE
from .parse import Figure, Heading, Listing, TableCaption
from .runner import PINNED_KINDS

MD = MarkdownIt("commonmark", {"html": False}).enable("table")
PLACEHOLDER = "RBOOKBLOCK{:05d}"
PLACEHOLDER_RE = re.compile(r"<p>(RBOOKBLOCK\d{5})</p>")

PRINT_CSS = """\
@page {
  size: A5;
  margin: 17mm 15mm 18mm 15mm;
  @bottom-center { content: counter(page); font: 8pt "DejaVu Sans", sans-serif; color: #555; }
}
@page :left {
  margin-left: 13mm; margin-right: 17mm;
  @top-left { content: string(part); font: italic 7.5pt "DejaVu Sans", sans-serif; color: #555; }
}
@page :right {
  margin-left: 17mm; margin-right: 13mm;
  @top-right { content: string(section); font: italic 7.5pt "DejaVu Sans", sans-serif; color: #555; }
}
@page cover {
  @top-left { content: none; } @top-right { content: none; } @bottom-center { content: none; }
}
@page :blank {
  @top-left { content: none; } @top-right { content: none; } @bottom-center { content: none; }
}
html { hyphens: auto; }
body { font: 9.5pt/1.42 "DejaVu Serif", "Liberation Serif", serif; max-width: none; margin: 0; padding: 0;
       background: #fff; color: #000; }
h1, h2, h3, h4, h5, h6 { font-family: "DejaVu Sans", "Liberation Sans", sans-serif; hyphens: manual;
                         break-after: avoid; bookmark-level: none; }
h1 { font-size: 15pt; } h2 { font-size: 12pt; } h3 { font-size: 10.5pt; } h4, h5, h6 { font-size: 9.5pt; }
p, li { orphans: 2; widows: 2; }
a { color: inherit; text-decoration: none; }
.title-page { page: cover; break-after: page; text-align: center; padding-top: 45mm; }
.title-page h1.book { font-size: 20pt; margin: 0 0 8mm; }
.title-page .authors { font-size: 11pt; margin: 0 0 1.5mm; }
.colophon { page: cover; break-after: right; font-size: 7.5pt; padding-top: 70mm; }
.colophon h2 { font-size: 9pt; }
.colophon dt { font-weight: bold; } .colophon dd { margin: 0 0 1.5mm 0; overflow-wrap: anywhere; }
nav { break-before: page; }
nav#indice { break-before: right; }
nav h2 { string-set: part content(), section content(); }
nav ol { padding-left: 4mm; margin: 0; }
nav > ol { padding-left: 0; }
nav li { margin: .6mm 0; }
nav ol ol ol { font-size: 8pt; }
nav a::after { content: leader('.') target-counter(attr(href url), page); }
section.front { break-before: right; }
section.front > h1 { string-set: part content(), section content(); }
section.part { break-before: right; }
section.part > h1 { string-set: part content(), section ""; border-top: 1.5pt solid #000;
                    padding-top: 4mm; margin-top: 25mm; }
section.section > h2 { string-set: section content(); margin-top: 8mm; }
section.back { break-before: right; }
section.back > h1 { string-set: part content(), section content(); }
pre { white-space: pre-wrap; overflow-wrap: anywhere; overflow: visible; hyphens: manual;
      font-size: 7pt; line-height: 1.35; padding: 2mm 3mm; background: #f2f2ef; }
/* Inline code is never hyphenated nor broken inside a word. break_code()
   wraps each word that holds a break opportunity ("-", "/", ...) in a nowrap
   span; a word too long for its measure becomes several spans with a <wbr>
   before "." and after "_" "/" "::" "(". */
code { font-family: "DejaVu Sans Mono", "Liberation Mono", monospace; hyphens: none; }
code .w { white-space: nowrap; }
p code, li code { overflow-wrap: normal; font-size: 8.5pt; }
td code, th code { overflow-wrap: normal; font-size: 7.5pt; }
.listing, figure { margin: 4mm 0; }
.caption { break-after: avoid; }
.caption, figcaption, .table-caption, .output-label { font-size: 7.5pt; color: #333; }
.output-label { margin-top: 0; }
.output pre { background: #fff; border: .5pt solid #bbb; border-left: 2pt solid #888; }
.output.error pre { border-left-color: #a3261b; }
/* Automatic layout: a column is never narrower than its longest word, so
   words are not split to squeeze a column; words of 8 characters or fewer
   are never hyphenated. */
table { width: 100%; table-layout: auto; font-size: 8pt; }
td, th { border: .5pt solid #999; overflow-wrap: normal; hyphenate-limit-chars: 9 4 4; }
tr { break-inside: avoid; }
/* PDF outline: front matter, parts and back matter at level 1, sections and
   back-matter subsections at 2, subsections at 3. */
nav h2, .colophon h2, section.front > h1, section.part > h1, section.back > h1 { bookmark-level: 1; }
section.part > h1 { bookmark-state: closed; }
section.section > h2, section.front h3, section.back h3 { bookmark-level: 2; }
section.section h3, section.back h4 { bookmark-level: 3; }
section.back .explanation h4 { bookmark-level: none; }
.pending { border: .5pt dashed #999; color: #555; }
"""

TEMPLATE = jinja2.Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True).from_string("""\
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title|e }}</title>
{% if authors %}<meta name="author" content="{{ authors|join(', ')|e }}">
{% endif %}
<style>
:root { --fg: #1d1d1f; --bg: #fdfdfb; --muted: #5c5c66; --rule: #d9d9de; --code: #f3f3f0; --bad: #a3261b; }
@media (prefers-color-scheme: dark) {
  :root { --fg: #e6e6e3; --bg: #18181a; --muted: #a0a0a8; --rule: #3a3a40; --code: #232326; --bad: #ff8a7a; }
}
html { hyphens: auto; }
body { background: var(--bg); color: var(--fg); font: 17px/1.6 Georgia, "Times New Roman", serif;
       max-width: 46rem; margin: 0 auto; padding: 1rem 16px 4rem; }
h1, h2, h3, h4, h5 { font-family: system-ui, sans-serif; line-height: 1.25; hyphens: manual; }
h1.book { font-size: 2.1rem; margin-top: 2rem; }
section.part > h1 { border-top: 2px solid var(--fg); padding-top: 1rem; margin-top: 3rem; }
a { color: inherit; }
pre { background: var(--code); padding: .75rem 1rem; overflow-x: auto; font-size: .85rem; line-height: 1.45;
      hyphens: manual; }
code { font-family: ui-monospace, "DejaVu Sans Mono", monospace; hyphens: manual; }
.listing, figure { margin: 1.5rem 0; }
.caption, figcaption, .table-caption { font-family: system-ui, sans-serif; font-size: .9rem; color: var(--muted); }
.caption b, figcaption b, .table-caption b { color: var(--fg); }
.output-label { font-family: system-ui, sans-serif; font-size: .8rem; color: var(--muted); margin-top: -.5rem; }
.output pre { border-left: 3px solid var(--rule); }
.output.error pre { border-left-color: var(--bad); }
.pending { border: 1px dashed var(--rule); padding: .75rem 1rem; color: var(--muted); }
.unpinned { color: var(--bad); }
.colophon { font-size: .85rem; color: var(--muted); }
.colophon dt { font-weight: bold; color: var(--fg); } .colophon dd { margin: 0 0 .4rem 0; }
nav ol { list-style: none; padding-left: 1.2rem; }
ul.sources li { margin-bottom: .4rem; }
nav > ol { padding-left: 0; }
table { border-collapse: collapse; } td, th { border: 1px solid var(--rule); padding: .25rem .5rem; }
img { max-width: 100%; }
</style>
<style media="print">
{{ print_css }}
</style>
</head>
<body>
<section class="title-page">
<h1 class="book">{{ title|e }}</h1>
{% for author in authors %}
<p class="authors">{{ author|e }}</p>
{% endfor %}
{% if draft %}<p class="pending">Borrador: este build admite secciones y salidas pendientes.</p>{% endif %}
</section>
{% if colophon %}
<section class="colophon" id="colofon">
<h2>Colofón</h2>
<dl>
{% for label, value in colophon.lines() %}
<dt>{{ label|e }}</dt><dd>{{ value|e }}</dd>
{% endfor %}
</dl>
</section>
{% endif %}
{% for entry in front %}
<section class="front" id="{{ entry.anchor }}">
<h1>{{ entry.heading|e }}</h1>
{{ entry.html }}
</section>
{% endfor %}
<nav id="indice">
<h2>Índice</h2>
<ol>
{% for entry in front %}
<li><a href="#{{ entry.anchor }}">{{ entry.heading|e }}</a></li>
{% endfor %}
{% for part in parts %}
<li><a href="#{{ part.anchor }}">Parte {{ part.number }}: {{ part.title|e }}</a>
<ol>
{% for entry in part.sections %}
<li><a href="#{{ entry.anchor }}">{{ entry.heading|e }}</a>{% if entry.toc %}

<ol>
{% for h in entry.toc %}
<li><a href="#{{ h.anchor }}">{{ h.number }} {{ h.html_title }}</a></li>
{% endfor %}
</ol>{% endif %}</li>
{% endfor %}
</ol></li>
{% endfor %}
{% for entry in back %}
<li><a href="#{{ entry.anchor }}">{{ entry.heading|e }}</a>{% if entry.toc %}

<ol>
{% for h in entry.toc %}
<li><a href="#{{ h.anchor }}">{{ h.number }} {{ h.html_title }}</a></li>
{% endfor %}
</ol>{% endif %}</li>
{% endfor %}
</ol>
</nav>
<nav id="indice-de-listados">
<h2>Índice de listados</h2>
{% if listings %}
<ol>
{% for l in listings %}
<li><a href="#lst-{{ l.label }}">Listado {{ l.number }}. {{ l.caption_text|e }} ({{ l.where|e }})</a></li>
{% endfor %}
</ol>
{% else %}
<p>No hay listados.</p>
{% endif %}
</nav>
{% if figures %}
<nav id="indice-de-figuras">
<h2>Índice de figuras</h2>
<ol>
{% for f in figures %}
<li><a href="#fig-{{ f.label }}">Figura {{ f.number }}. {{ f.caption_text|e }} ({{ f.where|e }})</a></li>
{% endfor %}
</ol>
</nav>
{% endif %}
{% if tables %}
<nav id="indice-de-tablas">
<h2>Índice de tablas</h2>
<ol>
{% for t in tables %}
<li><a href="#tbl-{{ t.label }}">Tabla {{ t.number }}. {{ t.caption_text|e }} ({{ t.where|e }})</a></li>
{% endfor %}
</ol>
</nav>
{% endif %}
<main>
{% for part in parts %}
<section class="part" id="{{ part.anchor }}">
<h1>Parte {{ part.number }}: {{ part.title|e }}</h1>
{% for entry in part.sections %}
<section class="section" id="{{ entry.anchor }}">
<h2>{{ entry.heading|e }}</h2>
{{ entry.html }}
</section>
{% endfor %}
</section>
{% endfor %}
{% for entry in back %}
<section class="back" id="{{ entry.anchor }}">
<h1>{{ entry.heading|e }}</h1>
{{ entry.html }}
</section>
{% endfor %}
</main>
</body>
</html>
""")


def render_book(book, errors, colophon=None):
    """Return the HTML text of the book; problems are appended to ``errors``."""
    where_of = {}
    for entry in book.entries():
        for block in entry.blocks:
            if isinstance(block, (Listing, Figure, TableCaption)):
                where_of[(type(block).__name__, block.label)] = entry
    for listing in book.listings:
        listing.caption_text = resolve_cites(
            resolve_refs(listing.caption, book.refs, f"{listing.path}:{listing.line}", errors, link=False),
            book.bib, link=False)
        listing.where = _where(where_of[("Listing", listing.label)])
    for item in book.figures + book.tables:
        # The body renders these captions and reports their problems; here they are only read.
        item.caption_text = resolve_refs(item.caption, book.refs, "", [], link=False)
        item.where = _where(where_of[(type(item).__name__, item.label)])
    for entry in book.entries():
        if entry.generated == "listings":
            entry.html = _appendix(book, where_of, errors)
        elif entry.generated == "sources":
            entry.html = render_sources(book.bib, book.cited)
        elif entry.placeholder:
            entry.html = f'<p class="pending">{html.escape(entry.placeholder)}</p>'
        elif entry.generated == "reference":
            entry.html = _reference(entry)
        elif entry.path is None:      # missing file in a final build: already an error
            entry.html = ""
        else:
            entry.html = _section(book, entry, errors)
        entry.toc = [b for b in entry.blocks if isinstance(b, Heading) and b.level == 2 and b.number]
    page = TEMPLATE.render(title=book.title, authors=book.authors, draft=book.draft, front=book.front,
                           parts=book.parts, back=book.back,
                           listings=book.listings, figures=book.figures, tables=book.tables,
                           colophon=colophon, print_css=PRINT_CSS)
    return break_code(page)


# Inline code breaks only after these, and only in a token longer than its
# measure allows: PROSE_CODE_CHARS in running text (a line holds about 65
# characters of 8.5 pt mono), and in a table cell TABLE_CODE_CHARS divided by
# the number of columns, times 1.5 (a column may take more than its share).
CODE_BREAK_RE = re.compile(r"(::|[._/(])")
PROSE_CODE_CHARS = 60
TABLE_CODE_CHARS = 60
PRE_RE = re.compile(r"(<pre\b.*?</pre>)", re.S)
TABLE_RE = re.compile(r"(<table\b.*?</table>)", re.S)
INLINE_CODE_RE = re.compile(r"<code>([^<]*)</code>")
# Characters after which (or before which) line breaking may wrap a word: hyphens,
# "/", "|", "?", "!", "%", braces, dashes, "…".
LINE_BREAK_CHARS_RE = re.compile(r"[-/|?!%{}\u2010-\u2015\u2026]")


def _code_breaks(text, limit):
    def token(match):
        word = match.group(0)
        if len(word) > limit:
            # Before a ".", after the others: "Closure<wbr>.update", "begin_<wbr>stepwise".
            word = CODE_BREAK_RE.sub(lambda m: "\0" + m.group(1) if m.group(1) == "." else m.group(1) + "\0",
                                     word)
        pieces = [piece for piece in word.split("\0") if piece]
        if len(pieces) == 1 and not LINE_BREAK_CHARS_RE.search(word):
            return word      # no break opportunity inside: no span needed
        return "<wbr>".join(f'<span class="w">{piece}</span>' for piece in pieces)

    return INLINE_CODE_RE.sub(lambda m: "<code>" + re.sub(r"\S+", token, m.group(1)) + "</code>", text)


def break_code(page):
    """Keep inline-code words unbroken, with <wbr> break opportunities only
    in words too long for their measure (not in <pre>)."""
    out = []
    for piece in PRE_RE.split(page):
        if piece.startswith("<pre"):
            out.append(piece)
            continue
        for chunk in TABLE_RE.split(piece):
            if chunk.startswith("<table"):
                first_row = re.search(r"<tr>(.*?)</tr>", chunk, re.S)
                columns = max(1, len(re.findall(r"<t[hd]\b", first_row.group(1)))) if first_row else 1
                out.append(_code_breaks(chunk, int(TABLE_CODE_CHARS / columns * 1.5)))
            else:
                out.append(_code_breaks(chunk, PROSE_CODE_CHARS))
    return "".join(out)


def _where(entry):
    return entry.ref[:1].upper() + entry.ref[1:]


def _reference(entry):
    """Appendix C: Residuum's own Markdown, with numbered headings."""
    out = []
    source = getattr(entry, "source", None)
    if source:
        out.append(f'<p class="output-label">Incluido de <code>{html.escape(source)}</code>.</p>')
    for block in entry.blocks:
        if isinstance(block, Heading):
            level = min(block.level + 1, 6)
            block.html_title = MD.renderInline(block.title)
            number = f"{block.number} " if block.number else ""
            out.append(f'<h{level} id="{block.anchor}">{number}{block.html_title}</h{level}>')
        else:
            out.append(MD.render(block.text))
    return "\n".join(out)


def _md(book, text, where, errors):
    return MD.render(_prose(book, text, where, errors))


COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def _prose(book, text, where, errors, link=True):
    """Resolve references and citations and drop HTML comments (the
    ``covers`` anchors), outside fenced code."""
    out, chunk, fence = [], [], None

    def flush():
        if chunk:
            piece = "\n".join(chunk)
            piece = COMMENT_RE.sub("", piece)
            piece = resolve_cites(resolve_refs(piece, book.refs, where, errors, link=link), book.bib, link=link)
            out.append(piece)
            chunk.clear()

    for line in text.split("\n"):
        if fence is None:
            match = FENCE_RE.match(line)
            if match:
                flush()
                fence = match.group("fence")
                out.append(line)
                continue
            chunk.append(line)
        else:
            out.append(line)
            if re.match(r"^ {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$", line):
                fence = None
    flush()
    return "\n".join(out)


def _section(book, entry, errors):
    pieces, html_blocks = [], {}
    rel = entry.path.relative_to(book.root)
    for block in entry.blocks:
        if isinstance(block, str):
            pieces.append(_prose(book, block, str(rel), errors))
            continue
        key = PLACEHOLDER.format(len(html_blocks))
        html_blocks[key] = _block(book, block, f"{rel}:{block.line}", errors)
        pieces.append(f"\n\n{key}\n\n")
    rendered = MD.render("".join(pieces))
    return PLACEHOLDER_RE.sub(lambda m: html_blocks[m.group(1)], rendered)


def _block(book, block, where, errors):
    if isinstance(block, Heading):
        level = min(block.level + 1, 6)
        number = f"{block.number} " if block.number else ""
        title = MD.renderInline(_prose(book, block.title, where, errors, link=False))
        block.html_title = title
        return f'<h{level} id="{block.anchor}">{number}{title}</h{level}>'
    if isinstance(block, Figure):
        caption = html.escape(resolve_refs(block.caption, book.refs, where, errors, link=False))
        return (f'<figure id="fig-{block.label}"><img src="{html.escape(block.src)}" alt="{caption}">'
                f'<figcaption><b>Figura {block.number}.</b> {caption}</figcaption></figure>')
    if isinstance(block, TableCaption):
        caption = html.escape(resolve_refs(block.caption, book.refs, where, errors, link=False))
        return f'<p class="table-caption" id="tbl-{block.label}"><b>Tabla {block.number}.</b> {caption}</p>'
    return _listing(block)


def _listing(listing):
    lang = f' class="language-{html.escape(listing.lang)}"' if listing.lang else ""
    shown = listing.shown if listing.shown else listing.body + "\n"
    parts = [f'<div class="listing" id="lst-{listing.label}">',
             f'<div class="caption"><b>Listado {listing.number}.</b> {html.escape(getattr(listing, "caption_text", listing.caption))} '
             f'<a href="#exp-{listing.label}">(explicación)</a></div>',
             f"<pre><code{lang}>{html.escape(shown)}</code></pre>"]
    if listing.kind == "include":
        spec = listing.include
        lines = f", líneas {spec['start']}–{spec['end']}" if spec["start"] else ""
        parts.append(f'<div class="output-label">Copiado de <code>{html.escape(spec["path"])}</code> '
                     f'en residuum@{html.escape(spec["commit"])}{lines}.</div>')
    result = listing.result
    if listing.kind in PINNED_KINDS and result is not None and result.text is not None:
        error = listing.kind == "expect-error"
        label = (f"Error de <code>residuum {result.command}</code>" if error
                 else f"Salida de <code>residuum {result.command}</code>")
        if getattr(listing, "unpinned", False):
            label += ' <span class="unpinned">(salida sin fijar en expected/)</span>'
        parts.append(f'<div class="output{" error" if error else ""}">'
                     f'<pre>{html.escape(result.text) or "(sin salida)"}</pre>'
                     f'<div class="output-label">{label}</div></div>')
    parts.append("</div>")
    return "\n".join(parts)


def _appendix(book, where_of, errors):
    if not book.listings:
        return "<p>No hay listados.</p>"
    out, current = [], None
    for listing in book.listings:
        entry = where_of[("Listing", listing.label)]
        if entry is not current:
            current = entry
            out.append(f'<h3><a href="#{entry.anchor}">{html.escape(entry.heading)}</a></h3>')
        out.append(f'<div class="explanation" id="exp-{listing.label}">')
        out.append(f'<h4><a href="#lst-{listing.label}">Listado {listing.number}</a>. '
                   f"{html.escape(listing.caption_text)}</h4>")
        out.append(_md(book, listing.explanation, f"{listing.path}:{listing.line}", errors))
        out.append("</div>")
    return "\n".join(out)
