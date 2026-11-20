"""Phase 3: spine check, structure checks, plain language, readability,
citations, placeholders and the report. Each check has a passing case (the
``checked`` fixture builds clean) and at least one failing case."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from rbook import bib as bibmod
from rbook.checks import _template, fold
from rbook.prose import read_doc, sentences, words
from rbook.readability import fernandez_huerta, syllables_es

REPO_ROOT = Path(__file__).resolve().parents[2]


def edit(project, ident, old, new):
    path = project.section(ident)
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append(project, ident, text):
    path = project.section(ident)
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


def unbudget(project):
    """Drop the word budgets, for tests that append prose."""
    spine = project.load()
    for part in spine["parts"]:
        for section in part["sections"]:
            section.pop("words", None)
    project.save(spine)


def report(project):
    return (project.root / "out" / "report.md").read_text(encoding="utf-8")


# --- the passing fixture ---------------------------------------------------

def test_checked_fixture_passes_final_build(checked):
    code, out = checked.build()
    assert code == 0, out
    page = checked.html()
    assert "covers:" not in page                       # anchors are not rendered
    assert '<a href="#ref-kowalski1979">Kowalski, 1979</a>' in page
    assert '<a href="#ref-belnap1977">Belnap (1977)</a>' in page
    sources = page[page.index('id="sec-sources"'):page.index('id="sec-appendix-a"')]
    assert 'id="ref-belnap1977"' in sources and 'id="ref-kowalski1979"' in sources
    assert sources.index("Belnap") < sources.index("Kowalski")
    assert "Nadie" not in sources                      # only cited entries
    text = report(checked)
    assert "| 1.1 | s-uno | Las reglas de Residuum | borrador | 69 / 70 |" in text
    assert "## Hallazgos" in text and "Ninguno." in text


def test_report_status_and_pending(checked):
    spine = checked.load()
    spine["parts"][0]["sections"][0]["status"] = "revisión"
    spine["parts"][1]["sections"].append({"id": "s-tres", "title": "Tres", "words": 100})
    checked.save(spine)
    code, out = checked.build("--draft")
    assert code == 0, out
    text = report(checked)
    assert "| s-uno | Las reglas de Residuum | revisión |" in text
    assert "| s-tres | Tres | pendiente | 0 / 100 |" in text
    assert "| s-dos | Expresividad | borrador |" in text


def test_report_is_written_when_the_build_fails(checked):
    append(checked, "s-uno", "\nTODO revisar.\n")
    code, out = checked.build()
    assert code == 1
    text = report(checked)
    assert "sections/s-uno.md:" in text and "marcador" in text and "TODO" in text


# --- spine check -------------------------------------------------------------

def evidence_spine(project, repo_path, commit, evidence, tmp_path):
    spine = project.load()
    spine["book"]["pinned_commit"] = commit
    spine["parts"][0]["sections"][0]["evidence"] = evidence
    spine["parts"][0]["sections"][0]["listings"] = [{"kind": "run", "what": "algo"}]
    project.save(spine)
    return project.cli("check-spine", residuum=repo_path)


def tag(repo_path, name, rev):
    subprocess.run(["git", "-C", str(repo_path), "tag", name, rev], check=True)


GOOD_EVIDENCE = ["docs/ten.txt", "docs", "docs/*.txt", "docs/ten.txt (línea 3, section línea 4, lín*a 5)",
                 "docs/ten.txt#L2-L10", "git:log", "git:tag v1", "sec:s-uno", "sec:s-uno..s-dos",
                 "listing:self"]


def test_spine_check_passes(checked, repo, tmp_path):
    repo_path, first, _ = repo
    tag(repo_path, "v1", first)
    series = tmp_path / "serie.txt"
    series.write_text("x")
    code, out = evidence_spine(checked, repo_path, first, GOOD_EVIDENCE + [f"series:{series}"], tmp_path)
    assert code == 0, out
    assert "spine correcto: 4 entradas, 2 dueños, 11 evidencias resueltas" in out


@pytest.mark.parametrize("item, message", [
    ("docs/nada.txt", "no existe en"),
    ("doc/*.txt", "ningún fichero coincide con doc/*.txt"),
    ("docs/ten.txt (línea 3, cambiado)", "no aparece en docs/ten.txt: cambiado"),
    ("docs/ten.txt#L9-L11", "líneas 9-11 fuera del fichero (10 líneas)"),
    ("git:tag v9", "la etiqueta v9 no existe"),
    ("git:blame", "forma no válida"),
    ("series:~/no-existe-residuum-book.txt", "no existe"),
    ("sec:s-nada", "«s-nada» no es el id de ninguna entrada"),
    ("sec:s-dos..s-uno", "«s-uno» va antes que «s-dos»"),
])
def test_spine_check_rejects_bad_evidence(checked, repo, tmp_path, item, message):
    repo_path, first, _ = repo
    code, out = evidence_spine(checked, repo_path, first, ["docs/ten.txt", item], tmp_path)
    assert code == 1
    assert f"s-uno: evidencia «{item}»: {message}" in out


def test_spine_check_reads_the_commit_not_the_working_tree(checked, repo, tmp_path):
    repo_path, first, head = repo
    (repo_path / "docs" / "nuevo.txt").write_text("sin commit\n")
    code, out = evidence_spine(checked, repo_path, head, ["docs/ten.txt (línea 3)", "docs/nuevo.txt"], tmp_path)
    assert code == 1
    assert "no aparece en docs/ten.txt: línea 3" in out
    assert "evidencia «docs/nuevo.txt»: no existe en" in out


def test_spine_check_listing_self_needs_listings(checked, repo, tmp_path):
    repo_path, first, _ = repo
    spine = checked.load()
    spine["parts"][0]["sections"][0]["evidence"] = ["listing:self"]
    checked.save(spine)
    code, out = checked.cli("check-spine", residuum=repo_path)
    assert code == 1 and "la sección no declara `listings`" in out


def test_spine_check_unknown_commit(checked, repo, tmp_path):
    repo_path, _, _ = repo
    code, out = evidence_spine(checked, repo_path, "0000000", ["docs/ten.txt"], tmp_path)
    assert code == 1 and "el commit 0000000 no existe" in out


def test_spine_check_owner_null_and_parentheses(checked):
    text = checked.spine.read_text(encoding="utf-8")
    text = text.replace("criterio: s-dos", "criterio: s-nada\n  vacio:")
    text = text.replace("covers: [El criterio en Residuum.]", "covers: [El criterio (uno, dos) en Residuum.]")
    checked.spine.write_text(text, encoding="utf-8")
    code, out = checked.cli("check-spine")
    assert code == 1
    assert "owners.criterio: «s-nada» no es el id de ninguna entrada" in out
    assert "owners.vacio: valor nulo" in out
    assert "parts[1].sections[0].covers[0]: paréntesis desequilibrados en «El criterio (uno»" in out
    assert "covers[1]: paréntesis desequilibrados en «dos) en Residuum.»" in out
    # The build runs the same check first.
    code, out = checked.build("--draft")
    assert code == 1 and "owners.criterio: «s-nada»" in out


def test_spine_check_yaml_and_duplicate_ids(checked):
    checked.spine.write_text(checked.spine.read_text().replace("id: s-dos", "id: s-uno"))
    code, out = checked.cli("check-spine")
    assert code == 1 and "id repetido: s-uno" in out
    checked.spine.write_text("parts: [\n")
    code, out = checked.cli("check-spine")
    assert code == 1 and "no se puede leer el spine" in out


def test_real_spine_passes():
    if not Path("/home/maitreya/residuum/.git").exists():
        pytest.skip("no Residuum repository")
    from rbook.spinecheck import check_spine
    _, errors, checked_count = check_spine(REPO_ROOT / "spine.yaml", "/home/maitreya/residuum")
    assert errors == [] and checked_count > 100


# --- covers anchors ----------------------------------------------------------

def test_covers_missing_unknown_duplicate(checked):
    edit(checked, "s-uno", "<!-- covers: 2 -->", "<!-- covers: 3 -->")
    edit(checked, "s-dos", "<!-- covers: 1.2 -->", "<!-- covers: 1.1 -->")
    for extra in ((), ("--draft",)):
        code, out = checked.build(*extra)
        assert code == 1
        assert "sections/s-uno.md:7: [covers] ancla covers: 3 desconocida; el spine da 1, 2" in out
        assert "sections/s-uno.md: [covers] falta el ancla <!-- covers: 2 --> «Cómo se deriva un hecho.»" in out
        assert "sections/s-dos.md:29: [covers] ancla covers: 1.1 repetida (primera en la línea 26)" in out
        assert "falta el ancla <!-- covers: 1.2 --> «Segundo detalle.»" in out


# --- owner headings -----------------------------------------------------------

def test_owner_heading_is_rejected_outside_its_owner(checked):
    edit(checked, "s-dos", "## Detalle", "## las REGLAS de residuúm")
    code, out = checked.build("--draft")
    assert code == 1
    assert ("sections/s-dos.md:24: [dueño] el título repite el de la sección dueña de «reglas» (s-uno); "
            "remite a ella con @sec:s-uno «las REGLAS de residuúm»") in out


def test_owner_heading_is_allowed_in_the_owner(checked):
    edit(checked, "s-uno", "## Derivar un hecho", "## Las reglas de Residuum")
    code, out = checked.build()
    assert code == 0, out


def test_fold_ignores_case_and_accents():
    assert fold("Las Reglas  de RESIDUÚM.") == fold("las reglas de residuum")


# --- Part 2 template ----------------------------------------------------------

def test_template_reads_the_criteria_template():
    text = (REPO_ROOT / "guidelines" / "criteria-template.md").read_text(encoding="utf-8")
    assert _template(text) == ("## Veredicto", "Según este criterio, Residuum")


@pytest.mark.parametrize("old, new, message", [
    ("La expresividad mide qué ideas puede escribir un programador sin rodeos.\n"
     "Un lenguaje expresivo dice mucho con poco código.\n", "",
     "falta la definición genérica del criterio antes del primer ##"),
    ("```res {#lst:criterio", "```text {#lst:criterio", "falta un listado res"),
    ("```prolog {#lst:contraste caption=\"Una cláusula de Prolog\" run=none}",
     "```res {#lst:contraste caption=\"Una cláusula\" run=none}",
     "falta un listado de contraste en otro lenguaje con run=none"),
    ("## Veredicto", "## Conclusión", "el último título debe ser «## Veredicto»"),
    ("Según este criterio, Residuum ofrece", "Residuum ofrece",
     "la última oración debe empezar por «Según este criterio, Residuum»"),
])
def test_template_failures(checked, old, new, message):
    edit(checked, "s-dos", old, new)
    code, out = checked.build("--draft")
    assert code == 1
    assert f"[plantilla] {message}" in out


def test_template_listing_before_first_subsection(checked):
    edit(checked, "s-dos", "## El criterio en Residuum",
         '```res {#lst:pronto caption="Pronto" run=none}\nmodule P\n```\n::: explanation\nE.\n:::\n\n'
         "## El criterio en Residuum")
    code, out = checked.build("--draft")
    assert code == 1 and "[plantilla] un listado antes del primer ##" in out


def test_template_applies_only_to_verdict_sections(checked):
    edit(checked, "s-uno", "Una regla dice", "Hoy. Una regla dice")
    spine = checked.load()
    del spine["parts"][1]["sections"][0]["verdict"]
    checked.save(spine)
    edit(checked, "s-dos", "## Veredicto", "## Cierre")
    code, out = checked.build()
    assert code == 0, out


# --- word budget -------------------------------------------------------------

def test_word_budget_error_in_final_warning_in_draft(checked):
    spine = checked.load()
    spine["parts"][0]["sections"][0]["words"] = 200
    checked.save(spine)
    code, out = checked.build()
    assert code == 1
    assert "error: sections/s-uno.md: [palabras] 69 palabras de prosa; el spine pide 200 (±15 %: 170-230)" in out
    code, out = checked.build("--draft")
    assert code == 0, out
    assert "aviso: sections/s-uno.md: [palabras] 69 palabras de prosa" in out


def test_word_budget_ignores_code_listings_explanations_and_anchors(checked):
    append(checked, "s-uno", '\n```res {#lst:larga caption="Larga" run=none}\n' + "palabra " * 300
           + "\n```\n::: explanation\n" + "Una explicación muy larga. " * 5 + "\n:::\n\n"
           + "| a | b |\n|---|---|\n| " + "x " * 50 + "| y |\n\n## Un título con varias palabras más\n"
           + "\n<!-- covers: nota interna con muchas palabras que no cuentan -->\n")
    code, out = checked.build()
    assert "[palabras]" not in out


# --- plain language ------------------------------------------------------------

LONG = " ".join(["palabra"] * 38) + "."


def test_long_sentence_fails_final_and_is_reported_in_draft(checked):
    append(checked, "s-uno", f"\nResiduum usa una {LONG}\n")
    code, out = checked.build()
    assert code == 1
    assert "[frases_cortas] Frases cortas: 41 (límite >= 38)" in out
    code, out = checked.build("--draft")
    assert code == 0, out
    assert "aviso: sections/s-uno.md:" in out and "[frases_cortas]" in out


def test_sentence_at_threshold_minus_one_passes(checked):
    unbudget(checked)
    append(checked, "s-uno", "\n" + " ".join(["Palabra"] + ["palabra"] * 36) + ".\n")
    code, out = checked.build()
    assert code == 0, out


def test_comma_run_fails_but_list_items_do_not(checked):
    code, out = checked.build()
    assert code == 0, out              # s-dos has a list item with four commas
    append(checked, "s-uno", "\nEl cierre usa uno, dos, tres, cuatro y cinco hechos, sin lista.\n")
    code, out = checked.build()
    assert code == 1 and "[listas] Enumeración sin lista: 4 (límite >= 4)" in out


def test_decimal_commas_are_not_commas(checked):
    unbudget(checked)
    append(checked, "s-uno", "\nLos valores 1,5 y 2,5 y 3,5 y 4,5 son decimales.\n")
    code, out = checked.build()
    assert code == 0, out


def test_long_paragraph(checked):
    append(checked, "s-uno", "\n" + "Una oración breve de cinco palabras. " * 17 + "\n")
    code, out = checked.build()
    assert code == 1 and "[parrafos_eternos] Párrafos eternos: 102 (límite >= 100)" in out


def test_advisory_rules_are_reported_only(checked):
    unbudget(checked)
    append(checked, "s-uno", "\nEl hecho es derivado por la regla. Luego el cierre termina."
           " Dicho cierre es finito.\n\nUno.\n\nDos.\n\nTres.\n\nCuatro.\n")
    code, out = checked.build()
    assert code == 0, out
    text = report(checked)
    assert "| voz_pasiva | consejo | Voz pasiva: «es derivado por»" in text
    assert "| conectores | consejo | Conectores de secuencia: abre con «Luego»" in text
    assert "| jerga | consejo | Jerga pesada / rebuscada: «Dicho»" in text
    assert "| parrafos_una_oracion | consejo | Párrafos de una sola oración: 4 (límite >= 4)" in text


def test_repeated_connector_is_reported_again(checked):
    append(checked, "s-uno", "\nLuego el cierre crece. Luego el cierre termina.\n")
    checked.build()
    assert "abre con «Luego»; repetido (2.ª vez en la sección)" in report(checked)


def test_patterns_skip_inline_code_and_headings(checked):
    append(checked, "s-uno", "\nEl texto `es derivado por` no cuenta.\n\n## Dicho título\n\nFin del texto.\n")
    checked.build()
    text = report(checked)
    assert "voz_pasiva" not in text and "jerga" not in text


def custom_guidelines(project, extra_terms):
    target = project.root / "guidelines"
    shutil.copytree(REPO_ROOT / "guidelines", target)
    with (target / "terms.txt").open("a", encoding="utf-8") as handle:
        handle.write(extra_terms)


def test_terms_exempt_jargon_and_avoid_variants(checked):
    custom_guidelines(checked, "dicho cierre\tconcept\tsaid closure\tprueba\n"
                               "cierre\tconcept\tclosure\tprueba\tavoid: clausura, closure\n")
    append(checked, "s-uno", "\nDicho cierre es un término. La clausura no lo es. El `closure` es código.\n")
    code, out = checked.build()
    assert code == 1
    assert "[términos] «clausura»: el libro escribe «cierre» «La clausura no lo es.»" in out
    assert "«closure»" not in out
    assert "jerga" not in report(checked)


def test_unusable_rule_file_fails(checked):
    custom_guidelines(checked, "")
    path = checked.root / "guidelines" / "plain-language.yaml"
    path.write_text(path.read_text().replace("sentence word count >=", "sentence syllables >="))
    code, out = checked.build("--draft")
    assert code == 1 and "regla frases_cortas: no sé evaluar «sentence syllables >= thresholds.sentence_words»" in out


def test_sentence_splitting_spanish():
    doc = read_doc("¿Qué deriva la regla? ¡Un hecho! El valor 6.8 y la sección 2.1 siguen, p. ej. en "
                   "`a.b. C` o en etc. Sr. Pérez lo dice. Fin…\n")
    found = [s.text for s in sentences(doc.units[0])]
    assert len(found) == 4, found
    assert found[0] == "¿Qué deriva la regla?" and found[1] == "¡Un hecho!"
    assert found[2].startswith("El valor 6.8") and found[2].endswith("lo dice.")


def test_list_items_are_their_own_units():
    doc = read_doc("Intro:\n\n- uno, dos, tres, cuatro, cinco\n  sigue aquí;\n- dos.\n\n1. tres\n")
    kinds = [(u.kind, u.line) for u in doc.units]
    assert kinds == [("para", 1), ("item", 3), ("item", 5), ("item", 7)]
    assert "sigue aquí" in doc.units[1].text


def test_words_count_numbers_and_masked_tokens():
    doc = read_doc("La versión 6.8 de `x.y` cita @sec:s-uno y [@clave].\n")
    assert len(words(sentences(doc.units[0])[0].text)) == 9   # each masked token is one word


# --- readability ---------------------------------------------------------------

def test_syllables_es():
    assert [syllables_es(w) for w in ("programa", "lenguaje", "oración", "país", "poesía", "cielo")] \
        == [3, 3, 3, 2, 4, 2]


def test_readability_is_reported_never_failing(checked):
    code, out = checked.build()
    assert code == 0
    assert "| 69 / 70 | 95.3 |" in report(checked)
    assert fernandez_huerta(["uno"] * 5, 1) is None


# --- citations -------------------------------------------------------------------

def test_unknown_citation_fails_in_both_modes(checked):
    append(checked, "s-uno", "\nOtra obra lo dice [@nadie2020; @kowalski1979, p. 3]. Escribe a "
           "autor@example.org.\n")
    for extra in ((), ("--draft",)):
        code, out = checked.build(*extra)
        assert code == 1
        assert "[cita] cita sin entrada en bib/*.bib: @nadie2020" in out
        assert "references.bib: @example" not in out and "references.bib: @kowalski1979" not in out


def test_citation_in_inline_code_is_not_a_citation(checked):
    unbudget(checked)
    append(checked, "s-uno", "\nEl evento usa `@nadie` como marca de tiempo.\n")
    code, out = checked.build()
    assert code == 0, out


def test_no_citations_renders_empty_sources(checked):
    edit(checked, "s-uno", " [@kowalski1979]", "")
    edit(checked, "s-uno", " @belnap1977", "")
    checked.build("--draft")
    assert "No hay fuentes citadas." in checked.html()


def test_bib_reader():
    entries = bibmod.read_bib('% comentario con @falso{x,\n@comment{nada}\n@string{a = "b"}\n'
                              '@book{k1, author = {Pérez, Ana and Ruiz, Luis}, title = "T {\\&} U", year = 2001}\n'
                              "@misc(k2, title = {Sin autor})\n")
    assert set(entries) == {"k1", "k2"}
    assert entries["k1"].fields["title"] == "T & U"
    assert bibmod.short_author(entries["k1"]) == "Pérez y Ruiz"
    with pytest.raises(bibmod.BibError):
        bibmod.read_bib("@book{k1, title = {abierto}\n")
    with pytest.raises(bibmod.BibError):
        bibmod.read_bib("@book{k1, year=1}\n@book{k1, year=2}\n")


def test_malformed_bib_fails_the_build(checked):
    (checked.root / "bib" / "references.bib").write_text("@book{roto, title = {sin cerrar}\n")
    code, out = checked.build("--draft")
    assert code == 1 and "bib/references.bib: línea 1: entrada @book sin cerrar" in out


# --- placeholders ------------------------------------------------------------------

@pytest.mark.parametrize("marker", ["TODO", "FIXME", "XXX", "Respaldar"])
def test_placeholder_fails_final_and_is_reported_in_draft(checked, marker):
    append(checked, "s-uno", f"\nEsta frase dice {marker} aquí.\n")
    code, out = checked.build()
    assert code == 1 and f"[marcador] marcador pendiente «{marker}»" in out
    code, out = checked.build("--draft")
    assert code == 0, out
    assert f"aviso: sections/s-uno.md:" in out
    assert "| 1 | 1 (1 / 0 / 0) |" in report(checked)


def test_placeholder_in_code_is_ignored(checked):
    unbudget(checked)
    append(checked, "s-uno", "\nEl código `TODO` no es un marcador.\n\n```text\nTODO\n```\n")
    code, out = checked.build()
    assert code == 0, out
