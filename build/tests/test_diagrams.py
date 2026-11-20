"""Build-time diagrams: ```dot {#fig:...}``` blocks rendered by Graphviz."""

import os
import stat

import pytest

from rbook import diagrams

pytestmark = pytest.mark.skipif(not os.access(diagrams.DOT, os.X_OK), reason="Graphviz no instalado")

DOT_FIGURE = '''
```dot {#fig:red caption="Una red pequeña" alt="Tres nodos: a apunta a b y b apunta a c."}
digraph { rankdir=LR; a -> b -> c; }
```
'''


def add_figures(project, alfa=DOT_FIGURE, beta=None):
    """A dot figure in s-alfa (before the image figure of s-beta) and,
    optionally, another one after it."""
    path = project.section("s-alfa")
    path.write_text(path.read_text() + alfa)
    if beta is not None:
        path = project.section("s-beta")
        path.write_text(path.read_text() + beta)


@pytest.fixture
def counting_dot(tmp_path, monkeypatch):
    """A stand-in for dot that logs each call and runs the real one."""
    log = tmp_path / "dot-calls.log"
    script = tmp_path / "dot"
    script.write_text(f'#!/bin/sh\necho call >> "{log}"\nexec {diagrams.DOT} "$@"\n')
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setattr(diagrams, "DOT", str(script))
    return lambda: len(log.read_text().splitlines()) if log.exists() else 0


def test_numbering_mixed_with_image_figures(accepted):
    add_figures(accepted, beta='\n```dot {#fig:otra caption="Otra red" alt="Un nodo solo."}\n'
                               'digraph { x; }\n```\n')
    code, out = accepted.build()
    assert code == 0, out
    page = accepted.html()
    figures = page[page.index('id="indice-de-figuras"'):page.index("<main>")]
    assert '<a href="#fig-red">Figura 1. Una red pequeña (Sección 1.1)</a>' in figures
    assert '<a href="#fig-esquema">Figura 2. Esquema de la compra (Sección 2.1)</a>' in figures
    assert '<a href="#fig-otra">Figura 3. Otra red (Sección 2.1)</a>' in figures
    assert '<a href="#fig-esquema">figura 2</a>' in page


def test_fig_reference_resolves(accepted):
    add_figures(accepted, alfa=DOT_FIGURE + "\nLa @fig:red resume.\n")
    code, out = accepted.build()
    assert code == 0, out
    assert '<a href="#fig-red">figura 1</a>' in accepted.html()


def test_svg_inline_in_html(accepted):
    add_figures(accepted)
    code, out = accepted.build()
    assert code == 0, out
    page = accepted.html()
    start = page.index('<figure class="dot" id="fig-red">')
    figure = page[start:page.index("</figure>", start)]
    assert '<svg role="img" aria-label="Tres nodos: a apunta a b y b apunta a c."' in figure
    assert "<?xml" not in page and "<!DOCTYPE svg" not in page
    assert 'font-family="DejaVu Sans' in figure
    assert 'id="fig-red-graph0"' in figure
    assert "<figcaption><b>Figura 1.</b> Una red pequeña</figcaption>" in figure


def test_alt_text_in_plain_text(accepted):
    add_figures(accepted)
    code, out = accepted.build("--txt")
    assert code == 0, out
    text = (accepted.root / "out" / "residuum.txt").read_text(encoding="utf-8")
    assert "Figura 1. Una red pequeña\n\n    [Dibujo] Tres nodos: a apunta a b y b apunta a c." in text
    assert "digraph" not in text


@pytest.mark.parametrize("attrs", ['caption="Red"', 'caption="Red" alt=""', 'caption="Red" alt="  "'])
@pytest.mark.parametrize("mode", [(), ("--draft",)])
def test_missing_alt_fails(project, attrs, mode):
    add_figures(project, alfa=f"\n```dot {{#fig:red {attrs}}}\ndigraph {{ a; }}\n```\n")
    code, out = project.build(*mode)
    assert code != 0
    assert "figura red: falta alt" in out


def test_missing_caption_and_unknown_attribute_fail(project):
    add_figures(project, alfa='\n```dot {#fig:red alt="A" color=red}\ndigraph { a; }\n```\n')
    code, out = project.build("--draft")
    assert code != 0
    assert "falta caption" in out and "atributo desconocido: color" in out


def test_duplicate_label_fails(project):
    add_figures(project, alfa=DOT_FIGURE.replace("#fig:red", "#fig:esquema"))
    code, out = project.build("--draft")
    assert code != 0
    assert "etiqueta repetida: fig:esquema" in out


def test_dot_syntax_error_shows_dot_message(project):
    add_figures(project, alfa='\n```dot {#fig:rota caption="Rota" alt="Nada."}\ndigraph { a -> ; }\n```\n')
    code, out = project.build("--draft")
    assert code != 0
    assert "figura rota: dot falló" in out
    assert "syntax error in line 1" in out


def test_cache_skips_dot_on_second_build(accepted, counting_dot):
    add_figures(accepted)
    code, out = accepted.build()
    assert code == 0, out
    assert counting_dot() == 1
    cached = list((accepted.root / ".cache" / "dot").glob("*.svg"))
    assert len(cached) == 1 and len(cached[0].stem) == 64
    first = accepted.html()
    code, out = accepted.build()
    assert code == 0, out
    assert counting_dot() == 1
    assert accepted.html() == first


def test_dot_source_is_not_prose(accepted):
    # Long, comma-heavy "sentences" inside the block would fail the plain-
    # language rules and the word budget if they were counted as prose.
    words = ", ".join(f"palabra{n}" for n in range(200))
    add_figures(accepted, alfa=f'\n```dot {{#fig:red caption="Red" alt="Un nodo."}}\n'
                               f'digraph {{ a [label="{words}"]; }}\n```\n')
    code, out = accepted.build()
    assert code == 0, out
    report = (accepted.root / "out" / "report.md").read_text(encoding="utf-8")
    assert "palabra1" not in report
