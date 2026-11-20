"""Phase 2: listing runner, expected outputs, accept, cache, includes."""

from rbook.runner import split_stderr

ERROR_LISTING = """
```res {{#lst:{label} caption="Un error" run={kind}}}
module Mal
rule r() = ERROR
```
::: explanation
Residuum rechaza este módulo.
:::
"""

OK_EXPECT_ERROR = """
```res {#lst:bien caption="No falla" run=expect-error}
module Bien
```
::: explanation
Debería fallar, pero no falla.
:::
"""


def include_listing(spec, label="inc"):
    return f"""
```text {{#lst:{label} caption="Un extracto" run=include include={spec}}}
```
::: explanation
Copiado del repositorio.
:::
"""


def append(project, ident, text):
    path = project.section(ident)
    path.write_text(path.read_text() + text)


def test_changed_output_fails_with_diff(accepted):
    path = accepted.section("s-alfa")
    path.write_text(path.read_text().replace("rule vende() = a() <= b()",
                                             "rule vende() = a() <= b()\nrule otra() = c() <= d()"))
    code, out = accepted.build()
    assert code == 1
    assert "la salida no coincide con expected/venta.out" in out
    assert "--- expected/venta.out" in out and "+++ actual/venta.out" in out
    assert "-run: 2 líneas" in out and "+run: 3 líneas" in out
    assert "+  rule otra() = c() <= d()" in out
    # The build never writes expected/.
    assert (accepted.root / "expected" / "venta.out").read_text().startswith("run: 2 líneas")
    # Also in draft mode.
    code, out = accepted.build("--draft")
    assert code == 1 and "+++ actual/venta.out" in out


def test_accept_shows_diff_then_writes(project):
    expected = project.root / "expected"
    code, out = project.build()
    assert code == 1
    assert "falta expected/venta.out" in out
    assert not expected.exists()
    code, out = project.cli("accept", "venta")
    assert code == 0, out
    assert "--- /dev/null" in out and "+++ expected/venta.out" in out and "+run: 2 líneas" in out
    assert (expected / "venta.out").read_text() == "run: 2 líneas\n  module Venta\n  rule vende() = a() <= b()\n"
    assert not (expected / "compra.out").exists()
    code, out = project.build()
    assert code == 1 and "falta expected/compra.out" in out and "venta.out" not in out
    # A changed listing: accept prints the diff before writing.
    path = project.section("s-alfa")
    path.write_text(path.read_text().replace("module Venta", "module Venta2"))
    code, out = project.cli("accept", "--all")
    assert code == 0, out
    assert "-  module Venta\n+  module Venta2" in out
    assert out.index("+  module Venta2") < out.index("escrito expected/venta.out")
    assert "Venta2" in (expected / "venta.out").read_text()
    code, out = project.cli("accept", "venta")
    assert code == 0 and "venta: sin cambios" in out
    code, out = project.build()
    assert code == 0, out


def test_accept_rejects_unknown_label(project):
    code, out = project.cli("accept", "nada")
    assert code == 1 and "nada: no hay ningún listado ejecutable" in out


def test_draft_reports_missing_expected(project):
    code, out = project.build("--draft")
    assert code == 0, out
    assert "aviso: " in out and "falta expected/venta.out" in out
    assert "salida sin fijar" in project.html()
    assert not (project.root / "expected").exists()


def test_output_is_placed_after_listing(accepted):
    code, out = accepted.build()
    assert code == 0, out
    page = accepted.html()
    listing = page.index('<div class="listing" id="lst-compra">')
    source = page.index("rule compra() = c() &lt;= d()", listing)
    output = page.index("query: 3 líneas", listing)
    assert listing < source < output < page.index("</div>\n", output)
    # The hidden setup ran (the fake echoes it) but is not shown as source.
    shown = page[listing:output]
    assert "seeded verb c()" not in shown
    assert "Salida de <code>residuum query</code>" in page


def test_expect_error_succeeds_on_failure(project):
    append(project, "s-alfa", ERROR_LISTING.format(label="mal", kind="expect-error"))
    code, out = project.cli("accept", "mal")
    assert code == 0, out
    text = (project.root / "expected" / "mal.out").read_text()
    assert text == "error en mal.res: rule r() = ERROR\n"   # stderr, with the path normalised
    code, out = project.build("--draft")
    assert code == 0, out
    assert "Error de <code>residuum run</code>" in project.html()


def test_expect_error_fails_on_success(project):
    append(project, "s-alfa", OK_EXPECT_ERROR)
    code, out = project.build("--draft")
    assert code == 1
    assert "listado bien: run=expect-error, pero residuum run terminó bien" in out


def test_run_listing_that_fails_breaks_the_build(project):
    append(project, "s-alfa", ERROR_LISTING.format(label="mal", kind="run"))
    code, out = project.build("--draft")
    assert code == 1
    assert "listado mal: residuum run falló (código 1)" in out
    assert "error en mal.res: rule r() = ERROR" in out


def test_cache_avoids_rerunning(accepted, tmp_path, monkeypatch):
    log = tmp_path / "calls.log"
    monkeypatch.setenv("FAKE_RESIDUUM_LOG", str(log))
    code, out = accepted.build()
    assert code == 0, out
    assert not log.exists()          # accept already filled the cache
    (accepted.root / "setup" / "decls.res").write_text("module Compra\nseeded verb c()\nseeded verb d()\n")
    code, out = accepted.build()
    assert code == 1 and "+  seeded verb d()" in out     # the setup is part of the hash
    assert log.read_text() == "query compra.res\n"


def test_missing_setup_fails(accepted):
    (accepted.root / "setup" / "decls.res").unlink()
    code, out = accepted.build("--draft")
    assert code == 1 and "setup=decls: no existe setup/decls.res" in out


def test_include_line_ranges(project, repo):
    root, first, _ = repo
    spine = project.load()
    spine["book"]["pinned_commit"] = first[:7]
    project.save(spine)
    append(project, "s-alfa", include_listing(f"residuum@{first[:7]}:docs/ten.txt#L3-L5")
           + include_listing(f"residuum@{first}:docs/ten.txt#L7", label="una"))
    code, out = project.cli("accept", "--all")
    assert code == 0, out
    code, out = project.build(residuum=root)
    assert code == 0, out
    page = project.html()
    assert '<code class="language-text">línea 3\nlínea 4\nlínea 5\n</code>' in page
    assert '<code class="language-text">línea 7\n</code>' in page
    assert "líneas 3–5" in page
    assert "línea 2\n" not in page
    # Includes are not runner outputs: nothing pinned for them.
    assert not (project.root / "expected" / "inc.out").exists()


def test_include_range_out_of_file_fails(project, repo):
    root, first, _ = repo
    spine = project.load()
    spine["book"]["pinned_commit"] = first
    project.save(spine)
    append(project, "s-alfa", include_listing(f"residuum@{first}:docs/ten.txt#L9-L12"))
    code, out = project.build("--draft", residuum=root)
    assert code == 1 and "rango L9-L12 fuera del fichero (10 líneas)" in out


def test_wrong_include_commit_fails(project, repo):
    root, first, second = repo
    spine = project.load()
    spine["book"]["pinned_commit"] = first
    project.save(spine)
    append(project, "s-alfa", include_listing(f"residuum@{second[:7]}:docs/ten.txt#L1-L2"))
    code, out = project.build("--draft", residuum=root)
    assert code == 1
    assert f"el commit {second[:7]} no es book.pinned_commit ({first})" in out


def test_include_body_must_be_empty(project):
    append(project, "s-alfa", '\n```text {#lst:inc caption="X" run=include include=residuum@abc1234:a.txt}\n'
                              'texto pegado\n```\n::: explanation\nE.\n:::\n')
    code, out = project.build("--draft")
    assert code == 1 and "un listado include no lleva cuerpo" in out


def test_split_stderr_of_the_real_runner():
    stderr = ("Reports: /x/target/test-diagnostics/2026-1\n"
              "compile residuum | 0 | 0.4123s | 120.50 MiB RSS\n"
              "venta.res | 1 | 0.0100s | 3.20 MiB RSS\n"
              "error: unknown verb `b` at 3:5\n"
              "STOPPED: venta.res: nonzero_exit; no remaining tests executed. See /x/02.output.txt\n")
    kept, infra = split_stderr(stderr, "venta.res")
    assert kept == "error: unknown verb `b` at 3:5" and infra is None
    kept, infra = split_stderr("Reports: /x\nSTOPPED: compile residuum: timeout; no remaining tests "
                               "executed. See /x/01.output.txt\n", "venta.res")
    assert infra.startswith("STOPPED: compile residuum: timeout")


def test_steps_and_trace_reach_the_launcher(project, tmp_path, monkeypatch):
    log = tmp_path / "calls.log"
    monkeypatch.setenv("FAKE_RESIDUUM_LOG", str(log))
    append(project, "s-alfa", '```res {#lst:pasos caption="Pasos" run=run steps=3 trace=true}\n'
                              'module Pasos\n```\n::: explanation\nDos pasos.\n:::\n')
    code, out = project.build("--draft")
    assert "run pasos.res --steps 3 --trace" in log.read_text(), out


def test_steps_out_of_range_fails(project):
    append(project, "s-alfa", '```res {#lst:pasos caption="Pasos" run=run steps=0}\n'
                              'module Pasos\n```\n::: explanation\nDos pasos.\n:::\n')
    code, out = project.build("--draft")
    assert code == 1 and "steps=0: se espera un entero entre 1 y 4096" in out
