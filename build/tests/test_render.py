"""Phase 4: plain text, Appendix C, colophon, booklet imposition, PDF."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import FAKE
from rbook.booklet import booklet_order

BOOK_ROOT = Path(__file__).resolve().parents[2]
VENV_PYTHON = BOOK_ROOT / ".venv" / "bin" / "python"

REFERENCE = """\
# Referencia del lenguaje Formal (`.res`)

Introducción con un [enlace](../AGENTS.md) y otro [externo](https://example.org/).

## Ejecutar un fichero

Texto con @ tau y [@clave] que no son referencias del libro.

```res
module Minimal
# no es un título
```

### Detalle

Más.

## Reglas

Fin.
"""


@pytest.fixture
def residuum(tmp_path):
    """A git repository with docs/language-reference.md; the file changes in
    the second commit, so the test can tell which commit was read."""
    root = tmp_path / "residuum"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "language-reference.md").write_text(REFERENCE, encoding="utf-8")
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid",
               GIT_COMMITTER_DATE="2026-01-02T03:04:05+00:00", GIT_AUTHOR_DATE="2026-01-02T03:04:05+00:00")

    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], check=True, env=env,
                              capture_output=True, text=True).stdout.strip()

    git("init", "-q")
    git("add", ".")
    git("commit", "-q", "-m", "one")
    pinned = git("rev-parse", "HEAD")
    (root / "docs" / "language-reference.md").write_text("# Otra\n\n## Cambiada después\n", encoding="utf-8")
    git("commit", "-q", "-am", "two")
    return root, pinned


def with_reference(project, pinned):
    spine = project.load()
    spine["book"]["pinned_commit"] = pinned[:7]
    spine["back_matter"].append({"id": "appendix-c", "title": "Apéndice C: Referencia del lenguaje"})
    project.save(spine)


# -- plain text ---------------------------------------------------------------

def test_txt_has_numbered_headings_and_outputs(accepted):
    code, out = accepted.build("--txt")
    assert code == 0, out
    text = (accepted.root / "out" / "residuum.txt").read_text(encoding="utf-8")
    assert "Parte 1: Primera parte" in text
    assert "\n1.1 Alfa\n" in text and "\n2.1 Beta\n" in text
    assert "\n1.1.1 Una venta\n" in text and "\n1.1.1.1 Detalle\n" in text
    assert "\n2.1.1 Compra\n" in text
    # References become words; listings and their outputs are included.
    assert "Véase sección 2.1 y el listado 1." in text
    assert "Listado 1. Una venta y su consecuencia" in text
    assert "    rule vende() = a() <= b()" in text
    assert "  Salida de residuum run:" in text
    assert "    run: 2 líneas" in text
    assert "  Salida de residuum query:" in text
    # The table of contents lists subsections; Appendix A holds the explanations.
    assert "    1.1.1 Una venta" in text
    appendix = text[text.index("Apéndice A: Listados explicados\n==="):]
    assert "La preparación `decls` declara el módulo." in appendix
    assert "<!--" not in text


def test_txt_is_not_written_by_default(accepted):
    code, out = accepted.build()
    assert code == 0, out
    assert not (accepted.root / "out" / "residuum.txt").exists()
    assert not (accepted.root / "out" / "residuum.pdf").exists()


# -- Appendix C ---------------------------------------------------------------

def test_appendix_c_is_included_from_the_pinned_commit(accepted, residuum):
    repo, pinned = residuum
    with_reference(accepted, pinned)
    code, out = accepted.build("--txt", residuum=repo)
    assert code == 0, out
    page = accepted.html()
    appendix = page[page.index('id="sec-appendix-c"'):]
    assert "Apéndice B: Referencia del lenguaje" in page   # the second appendix in this spine
    assert '<h3 id="sec-appendix-c-1">B.1 Ejecutar un fichero</h3>' in appendix
    assert '<h4 id="sec-appendix-c-1.1">B.1.1 Detalle</h4>' in appendix
    assert '<h3 id="sec-appendix-c-2">B.2 Reglas</h3>' in appendix
    # The document's own title is replaced by the appendix heading.
    assert "Referencia del lenguaje Formal" not in appendix
    # Its text is Residuum's: no book references or citations apply.
    assert "@ tau y [@clave]" in appendix
    assert "# no es un título" in appendix
    assert f'href="https://github.com/Sollen-ai/residuum/blob/{pinned}/AGENTS.md"' in appendix
    assert 'href="https://example.org/"' in appendix
    # Read at the pinned commit, not the later one.
    assert "Cambiada después" not in page
    # Subsections appear in the table of contents.
    toc = page[page.index('id="indice"'):page.index('id="indice-de-listados"')]
    assert '<a href="#sec-appendix-c-2">B.2 Reglas</a>' in toc
    text = (accepted.root / "out" / "residuum.txt").read_text(encoding="utf-8")
    assert "\nB.1 Ejecutar un fichero\n" in text and "\nB.1.1 Detalle\n" in text


def test_appendix_c_is_c_after_a_and_b(accepted, residuum):
    repo, pinned = residuum
    with_reference(accepted, pinned)
    spine = accepted.load()
    spine["back_matter"].insert(1, {"id": "appendix-b", "title": "Apéndice B: Caso"})
    accepted.save(spine)
    code, out = accepted.build("--draft", residuum=repo)
    assert code == 0, out
    assert '<h3 id="sec-appendix-c-1">C.1 Ejecutar un fichero</h3>' in accepted.html()


def test_appendix_c_unreadable_fails_final_and_warns_in_draft(accepted, residuum, tmp_path):
    repo, _ = residuum
    with_reference(accepted, "0" * 40)
    code, out = accepted.build(residuum=repo)
    assert code == 1
    assert "appendix-c: no se puede leer docs/language-reference.md" in out
    code, out = accepted.build("--draft", residuum=repo)
    assert code == 0, out
    assert "aviso: appendix-c: no se puede leer" in out
    assert "Falta la referencia del lenguaje" in accepted.html()


# -- colophon -----------------------------------------------------------------

def test_colophon_shows_the_commit_and_versions(accepted, residuum, monkeypatch):
    repo, pinned = residuum
    with_reference(accepted, pinned)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1767225600")   # 2026-01-01
    code, out = accepted.build("--txt", residuum=repo)
    assert code == 0, out
    page = accepted.html()
    colophon = page[page.index('id="colofon"'):page.index('id="indice"')]
    assert f"commit {pinned}, del 2026-01-02" in colophon
    assert "Herramienta de build" in colophon and "rbook, " in colophon
    assert "Python" in colophon and "WeasyPrint" in colophon and "pypdf" in colophon
    assert "<dd>2026-01-01</dd>" in colophon
    # After the title page, before the table of contents.
    assert page.index('class="title-page"') < page.index('id="colofon"') < page.index('id="indice"')
    text = (accepted.root / "out" / "residuum.txt").read_text(encoding="utf-8")
    assert f"Residuum: commit {pinned}, del 2026-01-02" in text
    # Deterministic apart from the date: a second build gives the same page.
    code, out = accepted.build(residuum=repo)
    assert code == 0, out
    assert accepted.html() == page


def test_colophon_with_unknown_commit(accepted):
    code, out = accepted.build("--residuum", str(accepted.root))
    assert code == 0, out
    assert "commit abc1234 (no se encontró en el repositorio)" in accepted.html()


# -- lists of figures and tables ------------------------------------------------

def test_lists_of_figures_and_tables(accepted):
    code, out = accepted.build()
    assert code == 0, out
    page = accepted.html()
    figures = page[page.index('id="indice-de-figuras"'):page.index("<main>")]
    assert '<a href="#fig-esquema">Figura 1. Esquema de la compra (Sección 2.1)</a>' in figures
    assert '<a href="#tbl-datos">Tabla 1. Datos de ejemplo (Sección 1.1)</a>' in page


def test_no_figure_list_without_figures(accepted):
    path = accepted.section("s-beta")
    path.write_text(re.sub(r"!\[.*\n|La @fig:esquema.*\n", "", path.read_text()))
    code, out = accepted.build()
    assert code == 0, out
    assert 'id="indice-de-figuras"' not in accepted.html()
    assert 'id="indice-de-tablas"' in accepted.html()


# -- booklet imposition -------------------------------------------------------

def test_booklet_order_8_pages():
    assert booklet_order(8) == [(7, 0), (1, 6), (5, 2), (3, 4)]


def test_booklet_order_10_pages_pads_to_12():
    assert booklet_order(10) == [(None, 0), (1, None), (9, 2), (3, 8), (7, 4), (5, 6)]


def test_booklet_order_covers_every_page_once():
    for n in range(1, 30):
        order = booklet_order(n)
        assert len(order) * 2 % 4 == 0
        pages = [p for side in order for p in side if p is not None]
        assert sorted(pages) == list(range(n))


# -- PDF (needs .venv/) ---------------------------------------------------------

needs_venv = pytest.mark.skipif(not VENV_PYTHON.exists(), reason="no hay .venv/ con WeasyPrint")


@needs_venv
def test_pdf_and_booklet(accepted):
    run = subprocess.run([str(VENV_PYTHON), str(BOOK_ROOT / "book"), "build", "--pdf", "--booklet",
                          "--spine", str(accepted.spine), "--launcher", str(FAKE)],
                         capture_output=True, text=True, timeout=300)
    assert run.returncode == 0, run.stderr
    pdf = accepted.root / "out" / "residuum.pdf"
    booklet = accepted.root / "out" / "residuum-booklet.pdf"
    probe = subprocess.run([str(VENV_PYTHON), "-c", """
import sys
from pypdf import PdfReader
book, booklet = PdfReader(sys.argv[1]), PdfReader(sys.argv[2])
print(len(book.pages), len(booklet.pages))
print("\\n".join(page.extract_text() for page in book.pages))
""", str(pdf), str(booklet)], capture_output=True, text=True, timeout=120)
    assert probe.returncode == 0, probe.stderr
    counts, text = probe.stdout.split("\n", 1)
    pages, sides = map(int, counts.split())
    assert pages > 1
    assert sides == len(booklet_order(pages))
    assert "1.1 Alfa" in text
    assert "Colofón" in text


def test_book_script_without_venv_explains(tmp_path):
    """./book's re-exec check, run from a copy with no .venv/ beside it."""
    copy = tmp_path / "book"
    copy.write_text((BOOK_ROOT / "book").read_text())
    run = subprocess.run([sys.executable, str(copy), "build", "--pdf"], capture_output=True, text=True,
                         timeout=60)
    assert run.returncode == 1
    assert "necesitan el entorno virtual .venv/" in run.stderr
