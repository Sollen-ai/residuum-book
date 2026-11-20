"""Phase 1: collect, numbering, references, listings index, Appendix A, HTML."""

import re

LISTING = """
```res {{#lst:{label} caption="{caption}" run=none}}
module M
```
::: explanation
{explanation}
:::
"""


def test_sample_builds(accepted):
    code, out = accepted.build()
    assert code == 0, out
    page = accepted.html()
    assert "Parte 1: Primera parte" in page
    assert "<h2>1.1 Alfa</h2>" in page and "<h2>2.1 Beta</h2>" in page
    assert '<h3 id="sec-venta-sub">1.1.1 Una venta</h3>' in page
    assert "Índice de listados" in page
    assert "Apéndice A: Listados explicados" in page
    assert '<a href="#sec-s-beta">sección 2.1</a>' in page
    assert '<a href="#sec-s-alfa">Sección 1.1</a>' in page
    assert '<a href="#tbl-datos">tabla 1</a>' in page
    assert '<a href="#fig-esquema">figura 1</a>' in page


def test_reorder_renumbers_everything(accepted):
    spine = accepted.load()
    spine["parts"].reverse()
    accepted.save(spine)
    code, out = accepted.build()
    assert code == 0, out
    page = accepted.html()
    assert "Parte 1: Segunda parte" in page and "Parte 2: Primera parte" in page
    assert "<h2>1.1 Beta</h2>" in page and "<h2>2.1 Alfa</h2>" in page
    # Sections, subsections, listings and references all follow the new order.
    assert '<a href="#sec-s-beta">sección 1.1</a>' in page
    assert '<a href="#sec-venta-sub">sección 2.1.1</a>' in page
    assert '<h3 id="sec-venta-sub">2.1.1 Una venta</h3>' in page
    assert "<b>Listado 1.</b> Una compra" in page
    assert "<b>Listado 2.</b> Una venta" in page
    assert '<a href="#lst-venta">listado 2</a>' in page


def test_reorder_within_a_part(project):
    spine = project.load()
    spine["parts"][0]["sections"].append(spine["parts"][1]["sections"].pop())
    spine["parts"][0]["sections"].reverse()
    project.save(spine)
    code, out = project.cli("accept", "--all")
    assert code == 0, out
    code, out = project.build()
    assert code == 0, out
    page = project.html()
    assert "<h2>1.1 Beta</h2>" in page and "<h2>1.2 Alfa</h2>" in page
    assert '<h3 id="sec-venta-sub">1.2.1 Una venta</h3>' in page


def test_unresolved_reference_fails_in_both_modes(accepted):
    path = accepted.section("s-alfa")
    path.write_text(path.read_text() + "\nVéase @sec:nada y @lst:nada.\n")
    for extra in ((), ("--draft",)):
        code, out = accepted.build(*extra)
        assert code == 1
        assert "referencia sin resolver: @sec:nada" in out
        assert "referencia sin resolver: @lst:nada" in out


def test_reference_in_inline_code_is_left_alone(accepted):
    path = accepted.section("s-alfa")
    path.write_text(path.read_text() + "\nEl texto `@sec:nada` no es una referencia.\n")
    code, out = accepted.build()
    assert code == 0, out
    assert "<code>@sec:nada</code>" in accepted.html()


def test_missing_explanation_fails(accepted):
    path = accepted.section("s-alfa")
    path.write_text(path.read_text() + '\n```res {#lst:sola caption="Sola" run=none}\nmodule M\n```\n\nFin.\n')
    code, out = accepted.build("--draft")
    assert code == 1
    assert "listado sola: falta el bloque ::: explanation" in out


def test_missing_caption_or_run_kind_fails(accepted):
    path = accepted.section("s-alfa")
    path.write_text(path.read_text()
                    + '\n```res {#lst:x1 run=none}\nmodule M\n```\n::: explanation\nE.\n:::\n'
                    + '\n```res {#lst:x2 caption="C"}\nmodule M\n```\n::: explanation\nE.\n:::\n'
                    + '\n```res\nmodule M\n```\n')
    code, out = accepted.build("--draft")
    assert code == 1
    assert "listado x1: falta caption" in out
    assert "listado x2: falta run=<tipo>" in out
    assert "bloque res sin etiqueta" in out


def test_duplicate_label_fails(accepted):
    path = accepted.section("s-beta")
    path.write_text(path.read_text() + LISTING.format(label="venta", caption="Otra", explanation="E."))
    code, out = accepted.build("--draft")
    assert code == 1
    assert "etiqueta repetida: lst:venta" in out


def test_appendix_a_follows_listing_order(accepted):
    # Three listings in s-beta and one in s-alfa; the appendix follows book order.
    path = accepted.section("s-beta")
    path.write_text(path.read_text()
                    + LISTING.format(label="tres", caption="Tercero", explanation="Explica tres.")
                    + LISTING.format(label="cuatro", caption="Cuarto", explanation="Explica cuatro."))
    code, out = accepted.build()
    assert code == 0, out
    page = accepted.html()
    appendix = page[page.index('id="sec-appendix-a"'):]
    order = re.findall(r'<div class="explanation" id="exp-([\w-]+)">', appendix)
    assert order == ["venta", "compra", "tres", "cuatro"]
    numbers = re.findall(r'<a href="#lst-[\w-]+">Listado (\d+)</a>', appendix)
    assert numbers == ["1", "2", "3", "4"]
    groups = re.findall(r'<h3><a href="#(sec-[\w.-]+)">', appendix)
    assert groups == ["sec-s-alfa", "sec-s-beta"]
    # Links both ways.
    assert '<a href="#exp-cuatro">(explicación)</a>' in page
    assert '<div class="listing" id="lst-cuatro">' in page
    # The explanation is not left in the body.
    body = page[:page.index('id="sec-appendix-a"')]
    assert "Explica cuatro." not in body
    index = page[page.index('id="indice-de-listados"'):page.index("<main>")]
    assert re.findall(r'href="#lst-([\w-]+)"', index) == ["venta", "compra", "tres", "cuatro"]


def test_missing_section_is_placeholder_in_draft_and_error_in_final(accepted):
    spine = accepted.load()
    spine["parts"][1]["sections"].append({"id": "s-gamma", "title": "Gamma"})
    accepted.save(spine)
    code, out = accepted.build()
    assert code == 1
    assert "s-gamma: falta sections/s-gamma.md" in out
    code, out = accepted.build("--draft")
    assert code == 0, out
    page = accepted.html()
    assert "<h2>2.2 Gamma</h2>" in page
    assert "Sección pendiente: falta sections/s-gamma.md." in page


def test_section_file_without_spine_entry_fails_in_both_modes(accepted):
    accepted.section("s-huerfana").write_text("Sin entrada.\n")
    for extra in ((), ("--draft",)):
        code, out = accepted.build(*extra)
        assert code == 1
        assert "no hay ninguna entrada «s-huerfana»" in out


def test_level_one_heading_is_rejected(accepted):
    path = accepted.section("s-alfa")
    path.write_text("# Alfa\n\n" + path.read_text())
    code, out = accepted.build()
    assert code == 1
    assert "el título de nivel 1 lo pone spine.yaml" in out
