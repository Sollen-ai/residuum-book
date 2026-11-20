"""Front matter, authors, corporate authors in citations, inline-code
breaks, and the PDF outline and metadata."""

import subprocess

import pytest

from conftest import FAKE
from rbook import bib as bibmod
from rbook.render import break_code
from test_render import BOOK_ROOT, VENV_PYTHON, needs_venv

PREFACE = """\
Este libro es para quien programa. <!-- covers: 1 -->

## Cómo leerlo

<!-- covers: 2 -->
Empieza por @sec:s-alfa y sigue el orden del índice.
"""

AUTHORS = ["Ana Pérez", "Claude (Anthropic)"]


def with_front(project, preface=PREFACE):
    spine = project.load()
    spine["book"]["authors"] = AUTHORS
    spine["front_matter"] = [{"id": "preface", "title": "Prefacio",
                              "covers": ["Para quién es.", "Cómo leerlo."]}]
    project.save(spine)
    if preface is not None:
        project.section("preface").write_text(preface, encoding="utf-8")
    path = project.section("s-alfa")
    path.write_text(path.read_text(encoding="utf-8") + "\nEl @sec:preface lo resume; @Sec:preface también.\n",
                    encoding="utf-8")


# -- front matter ---------------------------------------------------------------

def test_front_matter_is_unnumbered_before_the_table_of_contents(accepted):
    with_front(accepted)
    code, out = accepted.build("--txt")
    assert code == 0, out
    page = accepted.html()
    assert page.index('id="colofon"') < page.index('<section class="front" id="sec-preface">') \
        < page.index('<nav id="indice">')
    assert '<h1>Prefacio</h1>' in page
    # Its subsections have no number; @sec:preface is its title.
    assert '<h3 id="sec-preface-h1">Cómo leerlo</h3>' in page
    assert 'El <a href="#sec-preface">Prefacio</a> lo resume' in page
    # In the table of contents, first, and the parts keep their numbers.
    toc = page[page.index('<nav id="indice">'):page.index('id="indice-de-listados"')]
    assert toc.index('href="#sec-preface">Prefacio<') < toc.index("Parte 1: Primera parte")
    assert "1.1 Alfa" in toc
    text = (accepted.root / "out" / "residuum.txt").read_text(encoding="utf-8")
    assert text.index("Prefacio\n========") < text.index("Índice\n------")
    assert "Este libro es para quien programa." in text


def test_front_matter_is_checked_and_reported(accepted):
    with_front(accepted, preface="Un prefacio sin anclas.\n")
    code, out = accepted.build("--draft")
    assert code == 1
    assert "sections/preface.md: [covers] falta el ancla <!-- covers: 1 -->" in out
    report = (accepted.root / "out" / "report.md").read_text(encoding="utf-8")
    assert "|  | preface | Prefacio | borrador |" in report


def test_front_matter_placeholder_in_draft_and_error_in_final(accepted):
    with_front(accepted, preface=None)
    code, out = accepted.build("--draft")
    assert code == 0, out
    assert "aviso: preface: falta sections/preface.md (marcador de borrador)" in out
    assert "Sección pendiente: falta sections/preface.md." in accepted.html()
    code, out = accepted.build()
    assert code == 1 and "preface: falta sections/preface.md" in out


def test_duplicate_id_across_front_matter_and_sections(accepted):
    with_front(accepted)
    spine = accepted.load()
    spine["front_matter"][0]["id"] = "s-alfa"
    accepted.save(spine)
    code, out = accepted.cli("check-spine")
    assert code == 1 and "id repetido: s-alfa" in out
    code, out = accepted.build("--draft")
    assert code == 1 and "id repetido: s-alfa" in out


def test_spine_check_resolves_front_matter_evidence(checked, repo):
    repo_path, first, _ = repo
    spine = checked.load()
    spine["book"]["pinned_commit"] = first
    spine["front_matter"] = [{"id": "preface", "title": "Prefacio",
                              "evidence": ["docs/ten.txt", "docs/nada.txt", "sec:s-uno..s-dos", "sec:preface"]}]
    checked.save(spine)
    code, out = checked.cli("check-spine", residuum=repo_path)
    assert code == 1
    assert "preface: evidencia «docs/nada.txt»: no existe en" in out
    assert "«docs/ten.txt»" not in out and "«sec:" not in out
    spine["front_matter"][0]["evidence"] = ["docs/ten.txt", "sec:preface..s-uno"]
    checked.save(spine)
    code, out = checked.cli("check-spine", residuum=repo_path)
    assert code == 0, out
    assert "spine correcto: 5 entradas" in out


# -- authors ------------------------------------------------------------------------

def test_authors_on_the_title_page_colophon_and_head(accepted):
    with_front(accepted)
    code, out = accepted.build("--txt")
    assert code == 0, out
    page = accepted.html()
    title_page = page[page.index('class="title-page"'):page.index('id="colofon"')]
    assert '<p class="authors">Ana Pérez</p>' in title_page
    assert '<p class="authors">Claude (Anthropic)</p>' in title_page
    colophon = page[page.index('id="colofon"'):page.index('id="sec-preface"')]
    assert "<dt>Autores</dt><dd>Ana Pérez, Claude (Anthropic)</dd>" in colophon
    head = page[:page.index("</head>")]
    assert '<meta name="author" content="Ana Pérez, Claude (Anthropic)">' in head
    text = (accepted.root / "out" / "residuum.txt").read_text(encoding="utf-8")
    assert "Autores: Ana Pérez, Claude (Anthropic)" in text


def test_no_authors_no_author_lines(accepted):
    code, out = accepted.build()
    assert code == 0, out
    page = accepted.html()
    assert 'name="author"' not in page and "Autor" not in page


# -- corporate authors ------------------------------------------------------------

BIB = """\
@misc{riggs1889,
  author = {{Court of Appeals of New York}},
  title  = {Riggs v. Palmer},
  year   = {1889}
}
@book{mixto,
  author = {Pérez, Ana and {Ministerio de Justicia y Derechos Humanos} and Luis Ruiz},
  title  = {Mixto},
  year   = 2001
}
@book{dos,
  author = {{Grupo Uno and Dos} and Ana Pérez},
  title  = {Dos},
  year   = 2002
}
"""


def test_corporate_author_is_kept_whole():
    entries = bibmod.read_bib(BIB)
    riggs = entries["riggs1889"]
    assert bibmod.short_author(riggs) == "Court of Appeals of New York"
    assert bibmod.resolve_cites("[@riggs1889]", entries, link=False) == "(Court of Appeals of New York, 1889)"
    assert bibmod.resolve_cites("@riggs1889", entries, link=False) == "Court of Appeals of New York (1889)"
    # Persons are still shortened; "and" inside braces does not split.
    assert bibmod.short_author(entries["mixto"]) == "Pérez et al."
    assert bibmod.full_names(entries["mixto"]) == ["Pérez, Ana", "Ministerio de Justicia y Derechos Humanos",
                                                  "Luis Ruiz"]
    assert bibmod.short_author(entries["dos"]) == "Grupo Uno and Dos y Pérez"
    sources = bibmod.render_sources(entries, ["riggs1889", "dos"])
    assert '<li id="ref-riggs1889">Court of Appeals of New York (1889).' in sources
    assert "Grupo Uno and Dos; Ana Pérez (2002)." in sources


def test_corporate_author_in_the_built_book(checked):
    (checked.root / "bib" / "corp.bib").write_text(BIB, encoding="utf-8")
    path = checked.section("s-uno")
    path.write_text(path.read_text(encoding="utf-8").replace("[@kowalski1979]", "[@riggs1889]"),
                    encoding="utf-8")
    code, out = checked.build("--draft")
    assert code == 0, out
    page = checked.html()
    assert '(<a href="#ref-riggs1889">Court of Appeals of New York, 1889</a>)' in page
    assert "York, 1889" not in page.replace("New York, 1889", "")


# -- inline code breaks -----------------------------------------------------------

def test_inline_code_breaks_only_long_words_at_separators():
    page = ("<p><code>IncrementalClosure.update</code> <code>docs/a-b.md</code></p>"
            "<p><code>IncrementalClosure::begin_stepwise_update(additions)_and_some_more_text_here</code></p>"
            "<table><tr><th>a</th><th>b</th><th>c</th><th>d</th><th>e</th></tr>"
            "<tr><td><code>IncrementalClosure.update</code></td></tr></table>"
            "<pre><code>very_long.identifier_inside_a_listing_is_never_touched_by_this_at_all</code></pre>")
    out = break_code(page)
    # Short enough: unchanged, or one unbreakable span when it holds "-" or "/".
    assert "<p><code>IncrementalClosure.update</code>" in out
    assert '<code><span class="w">docs/a-b.md</span></code>' in out
    # Too long for the line: breaks after "::", "_", "(" and before ".".
    assert ('<span class="w">IncrementalClosure::</span><wbr><span class="w">begin_</span><wbr>'
            '<span class="w">stepwise_</span>') in out
    assert '<span class="w">update(</span><wbr><span class="w">additions)_</span>' in out
    # A five-column table allows 18 characters.
    assert '<td><code><span class="w">IncrementalClosure</span><wbr><span class="w">.update</span></code></td>' in out
    assert "<pre><code>very_long.identifier_inside_a_listing_is_never_touched_by_this_at_all</code></pre>" in out


# -- PDF outline, tags and metadata (needs .venv/) -----------------------------------

@needs_venv
def test_pdf_outline_metadata_and_booklet_title(accepted):
    with_front(accepted)
    spine = accepted.load()
    spine["book"]["title"] = "Libro de prueba"
    accepted.save(spine)
    run = subprocess.run([str(VENV_PYTHON), str(BOOK_ROOT / "book"), "build", "--booklet",
                          "--spine", str(accepted.spine), "--launcher", str(FAKE)],
                         capture_output=True, text=True, timeout=300)
    assert run.returncode == 0, run.stderr
    probe = subprocess.run([str(VENV_PYTHON), "-c", """
import sys
from pypdf import PdfReader
book, booklet = PdfReader(sys.argv[1]), PdfReader(sys.argv[2])
def walk(items, depth):
    for item in items:
        if isinstance(item, list):
            walk(item, depth + 1)
        else:
            print(f"{depth}|{item.title}")
walk(book.outline, 0)
root = book.trailer["/Root"]
print("META|" + book.metadata.get("/Title") + "|" + book.metadata.get("/Author") + "|" + str(root.get("/Lang")))
print("TAGGED|" + str("/StructTreeRoot" in root) + "|" + str(root.get("/MarkInfo", {}).get("/Marked")))
print("BOOKLET|" + booklet.metadata.get("/Title"))
""", str(accepted.root / "out" / "residuum.pdf"), str(accepted.root / "out" / "residuum-booklet.pdf")],
        capture_output=True, text=True, timeout=120)
    assert probe.returncode == 0, probe.stderr
    lines = probe.stdout.splitlines()
    outline = [line for line in lines if line[0].isdigit()]
    for expected in ("0|Colofón", "0|Prefacio", "1|Cómo leerlo", "0|Índice", "0|Parte 1: Primera parte",
                     "1|1.1 Alfa", "2|1.1.1 Una venta", "0|Parte 2: Segunda parte",
                     "0|Apéndice A: Listados explicados"):
        assert expected in outline, outline
    assert outline.index("0|Prefacio") < outline.index("0|Índice") < outline.index("0|Parte 1: Primera parte")
    assert not any(line.endswith("|Libro de prueba") for line in outline)   # the title page is not a bookmark
    assert "META|Libro de prueba|Ana Pérez, Claude (Anthropic)|es" in lines
    assert "TAGGED|True|True" in lines
    assert "BOOKLET|Libro de prueba (folleto para imprimir)" in lines
