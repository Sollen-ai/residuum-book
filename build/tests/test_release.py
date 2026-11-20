"""Edition, licence and source on the title page and colophon; ./book staleness."""

from rbook.staleness import evidence_pattern, matches


def test_edition_license_and_source(accepted):
    spine = accepted.load()
    spine["book"].update(edition="es-1.0", license="CC BY 4.0",
                         license_url="https://creativecommons.org/licenses/by/4.0/deed.es",
                         source="https://github.com/ejemplo/libro")
    accepted.save(spine)
    code, out = accepted.build("--txt")
    assert code == 0, out
    page = accepted.html()
    title_page = page[page.index('class="title-page"'):page.index('id="colofon"')]
    commit = spine["book"]["pinned_commit"]
    assert f"Edición es-1.0. Describe Residuum en el commit {commit}." in title_page
    colophon = page[page.index('id="colofon"'):]
    assert "<dt>Edición</dt><dd>es-1.0</dd>" in colophon
    assert "<dt>Licencia</dt><dd>CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/deed.es)." in colophon
    assert "licencia MIT" in colophon
    assert "<dt>Fuentes del libro</dt><dd>https://github.com/ejemplo/libro</dd>" in colophon
    text = (accepted.root / "out" / "residuum.txt").read_text(encoding="utf-8")
    assert f"Edición es-1.0. Describe Residuum en el commit {commit}." in text
    assert "Licencia: CC BY 4.0" in text


def test_no_edition_no_lines(accepted):
    code, out = accepted.build()
    assert code == 0, out
    page = accepted.html()
    assert "Edición" not in page and "Licencia" not in page


def test_edition_must_be_text(accepted):
    spine = accepted.load()
    spine["book"]["edition"] = ["es"]
    accepted.save(spine)
    code, out = accepted.build("--draft")
    assert code == 1 and "book.edition debe ser un texto" in out


def test_evidence_patterns():
    assert evidence_pattern("src/a.rs (foo, bar)") == "src/a.rs"
    assert evidence_pattern("docs/x.md#L3-L9") == "docs/x.md"
    assert evidence_pattern("tests/*.rs") == "tests/*.rs"
    for other in ("sec:s1", "series:~/x", "git:log", "listing:self", "diagrams:docs/a.md"):
        assert evidence_pattern(other) is None
    assert matches("docs", "docs/a.md") and matches("docs/", "docs/a.md")
    assert matches("tests/*.rs", "tests/t.rs") and not matches("doc", "docs/a.md")


def test_staleness_reports_changed_evidence(checked, repo):
    repo_path, first, second = repo
    spine = checked.load()
    spine["book"]["pinned_commit"] = first
    sections = [s for part in spine["parts"] for s in part["sections"]]
    assert len(sections) >= 2
    sections[0]["evidence"] = ["docs/ten.txt#L1-L3"]
    sections[1]["evidence"] = ["sec:" + sections[0]["id"]]
    checked.save(spine)
    code, out = checked.cli("staleness", "--ref", second, residuum=repo_path)
    assert code == 0, out
    assert "1 commit(s) por detrás" in out
    assert f"| {sections[0]['id']} |" in out and "`docs/ten.txt`" in out
    assert f"| {sections[1]['id']} |" not in out
    assert (checked.root / "out" / "staleness.md").is_file()
    code, out = checked.cli("staleness", "--ref", first, residuum=repo_path)
    assert code == 0 and "El libro está al día" in out


def test_staleness_unknown_ref(checked, repo):
    repo_path, first, _ = repo
    spine = checked.load()
    spine["book"]["pinned_commit"] = first
    checked.save(spine)
    code, out = checked.cli("staleness", "--ref", "no-such-branch", residuum=repo_path)
    assert code == 1 and "no-such-branch" in out
