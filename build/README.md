# rbook: the book's build tool

Phases 1–4 of the plan in `HANDOFF.md`: collect, number, cross-references,
listings index, Appendix A, HTML, the listing runner, the checks
(spine, structure, word budget, plain language, readability, citations,
placeholders) with `out/report.md`, and rendering (PDF, booklet, plain text,
colophon, Appendix C).

## Commands

```sh
./book build [--draft] [--spine PATH]     # writes out/index.html and out/report.md
./book build --txt                        # also out/residuum.txt (system python is enough)
./book build --pdf                        # also out/residuum.pdf (runs in .venv/)
./book build --booklet                    # also out/residuum-booklet.pdf (and the PDF)
./book build --all                        # --pdf --booklet --txt; combine with --draft
./book check-spine [--spine PATH]         # the spine check alone (also the first build step)
./book accept <label>... | --all          # shows the diff, then writes expected/<label>.out
./book warm [--cmd query] [FILE]          # one compile-and-run of the launcher at the pinned commit
./book staleness [--ref main]             # pinned commit vs a later Residuum revision: changed files, affected sections (out/staleness.md)
python3 -m pytest build/tests             # tests (fake launcher)
RBOOK_REAL_LAUNCHER=1 python3 -m pytest build/tests   # plus one real-launcher test
```

Common options: `--spine PATH` (its folder is the project root; default
`./spine.yaml`), `--residuum PATH` (the Residuum repository, read only;
default `$RESIDUUM_REPO`, else `../residuum` next to this repository), `--cache DIR` (default `<root>/.cache`),
`--launcher PATH` (a stand-in launcher, for tests only).

A final build fails on any problem: a spine check error, a missing section
file, an unresolved reference, a malformed listing, a failed run, a missing
or different expected output, and any check finding of policy `error` or
`hard` (below). `--draft` turns missing section files into placeholder pages,
missing expected outputs into warnings and `hard` findings into warnings
("aviso:"); everything else still fails. `--guidelines DIR` picks the rule
files (default `<root>/guidelines`, or this repository's `guidelines/` when
the project has none, as in the test fixtures).

## Source syntax

One file per spine entry: `sections/<id>.md`, for `front_matter`, sections
and `back_matter` alike. The section title comes from
the spine; inside the file `##` is a subsection (numbered `6.8.1`), `###` a
sub-subsection (`6.8.1.1`), `#` is rejected. A heading can carry a label:
`## Título {#sec:label}`.

Listing:

````text
```res {#lst:sale caption="Una venta" run=query setup=sale-decls}
rule ...
```
::: explanation
Lo que el lector debe ver.
:::
````

- Required: `#lst:<label>` (letters, digits, `_`, `-`), `caption="..."`,
  `run=<kind>`, and the `::: explanation` block right after the fence.
- Kinds: `run`, `query`, `explain`, `execute` (the CLI command of that name),
  `expect-error` (must exit non-zero; its error text is shown; command `run`
  unless `cmd=query|explain|execute`), `include`, `none` (shown, not run).
- `include=residuum@<commit>:<path>[#L<a>[-L<b>]]`, with an empty fence body.
  The commit must be `book.pinned_commit`; the text is read with
  `git -C <residuum> show <commit>:<path>`.
- A `res` fence without a label is an error.

### Launcher options

`steps=<N>` (1..4096) and `trace=true` pass the launcher's own `--steps N`
and `--trace` to the run. Allowed on the four CLI kinds and on
`expect-error`; the launcher itself refuses them with `execute`. They are part
of the cache key.

### Hidden setup

`setup=<name>` joins the file `setup/<name>.res` (in the project root) with
the listing. The build runs `<setup>` + newline + `<listing body>`; the book
shows only the body. Put `module X` and the declarations in the setup, and
the rules or experiments the text discusses in the listing. Line numbers in
error messages count from the start of the setup. Allowed on the four CLI
kinds and on `expect-error`.

Figures: `![Pie](src){#fig:label}` alone on a line. Tables: a pipe table
followed by the line `: Pie {#tbl:label}`.

### Diagrams

A fenced `dot` block with a figure label is a diagram drawn at build time:

````text
```dot {#fig:s6-14-requisitos caption="El álgebra de requisitos" alt="Diagrama de Hasse de ..."}
digraph { rankdir=BT; a -> b; }
```
````

- Required: `#fig:<label>`, `caption="..."` and a non-empty `alt="..."`
  (the text that replaces the drawing); any other attribute, a missing one
  or an empty body is an error in every mode, `--draft` included. A `dot`
  fence without `{...}` is ordinary code.
- It is a figure like `![…](src){#fig:…}`: one numbering, the "Índice de
  figuras", `@fig:` references; a label used twice fails.
- `diagrams.py` runs `/usr/bin/dot -Tsvg` with `-Gfontname`, `-Nfontname`
  and `-Efontname` set to DejaVu Sans, the book's sans font; a `fontname`
  in the source overrides them. A failure of `dot` is a build error that
  quotes dot's stderr.
- The SVG is cached in `.cache/dot/<sha256 of the source>.svg` (under
  `--cache` when given); an unchanged block never calls `dot` again.
- HTML and PDF: the SVG is inline (no XML prolog, doctype or comments; its
  ids prefixed with `fig-<label>-`), with `role="img"` and `aria-label` = alt
  on the `<svg>`, inside `<figure class="dot">` with the numbered
  `<figcaption>`. In print it fits the measure (`max-width: 100%`, height
  auto) and the figure does not split from its caption (`break-inside:
  avoid`).
- Plain text: "Figura N. caption" and the alt text, not the source.
- The block is code: it is not prose for the checks and does not count
  toward words, and it is not a listing (Part 2 template, Appendix A).

References: `@sec:<spine id or heading label>`, `@lst:`, `@fig:`, `@tbl:`
become "sección 6.8", "parte 2", "apéndice B", "listado 3", "figura 2",
"tabla 1", linked. `@Sec:` capitalises. Inside inline code they are left
alone.

## Numbering

Front matter (the spine's top-level `front_matter` list, same entry schema as
sections) is unnumbered: it is rendered after the title page and colophon and
before the table of contents, its `##` headings have no number, and
`@sec:<id>` becomes its title ("Prefacio"). It is checked exactly as a
section (covers anchors, words, plain language, report row), and a missing
file is a placeholder in `--draft`.

Everything else is numbered from spine order: parts (1, 2, …), sections (`p.s`),
subsections, back-matter appendices (A, B, … for ids starting with
`appendix`), and listings, figures and tables (one sequence each for the
whole book). Reordering the spine renumbers everything.

Back matter: `appendix-a` is generated ("Apéndice A: Listados explicados",
explanations in listing order, grouped by section, linked both ways);
`sources` is generated from the bibliography (below); `appendix-c` is
included from the Residuum repository (see *Rendering*). Others need a
section file.

## Running listings

- The pinned commit is exported read-only:
  `git -C <residuum> archive <commit> | tar -x -C .cache/residuum-<commit>`.
  The Residuum repository itself is never written.
- Each listing is written to `.cache/run/<hash>/<label>.res` and run as
  `.cache/residuum-<commit>/residuum <cmd> <file>`. The launcher execs
  `scripts/test_safe.py --cli`, whose limits apply unchanged (1324 MiB, no
  swap, one job, one thread, 45 s compile, 15 s run). Cargo builds into the
  export's own `target/`, so compiled code persists across builds; a cold
  compile took 16 s at `d4d2282`.
- The runner's own diagnostics (report path, timing rows, `STOPPED` line) are
  removed from the output; paths of the listing file are shortened to
  `<label>.res`. A `STOPPED` line other than the fixture's `nonzero_exit`
  (a compile timeout, a memory stop) fails the build and is never accepted as
  an expected error.
- Outputs are cached in `.cache/outputs/<sha256>.json`; the hash covers the
  commit, kind, command, label, setup and source.
- Pinned outputs live in `expected/<label>.out` (CLI kinds and
  `expect-error`; includes are pinned by the commit). Only `./book accept`
  writes there.

## Checks (phase 3)

Code: `spinecheck.py`, `checks.py`, `prose.py`, `readability.py`, `bib.py`,
`report.py`. Rules are read from `guidelines/` and never repeated in code:
`plain-language.yaml` (thresholds, patterns, policies), `terms.txt`
(exempt terms, `avoid:` variants) and `criteria-template.md` (the verdict
heading and the verdict sentence's opening words, read from its "Checked"
list). Each finding has a policy:

| Policy | Final build | `--draft` | Findings |
|---|---|---|---|
| `error` | fails | fails | spine, covers anchors, owner headings, Part 2 template, citations |
| `hard` | fails | warning | word budget, `hard` plain-language rules, `avoid:` spellings, placeholders |
| `advisory` | report only | report only | `advisory` plain-language rules |

### Spine check

`./book check-spine`, and the first step of every build. The YAML parses;
ids are unique across `front_matter`, parts, sections and `back_matter`;
every `owners` value is a spine id; no key or list item is
null and no list item has unbalanced parentheses (both are what an unquoted
comma in a YAML flow list produces). Every `evidence` entry resolves at
`book.pinned_commit`, read with `git ls-tree` / `git show`, never the working
tree:

- `path`, a directory, or a glob (`*`, `?`, `[...]`) matching at least one file;
- `path (a, b)`: each anchor occurs in the file; a leading `section ` is
  dropped; `*` in an anchor matches any word characters (`substitute_*`);
- `path#La-Lb`: the range is inside the file;
- `git:log` (the commit exists), `git:tag <t>` (the tag exists);
- `series:<path>`: exists after `~` expansion;
- `sec:<id>` or `sec:<a>..<b>`: the ids exist, `a` before `b`;
- `listing:self`: the section declares `listings`.

### Structure

- **Covers anchors.** Each `covers` item needs `<!-- covers: n -->` in the
  section file (`n` from 1, spine order); subsection items use
  `<!-- covers: k.n -->` (`k` = subsection index from 1). One comment may
  list several (`<!-- covers: 1, 2 -->`). Missing, unknown and duplicate
  anchors are errors. HTML comments are never rendered.
- **Owner headings.** For every concept in `owners`, the owner section's
  spine title is reserved: a heading (any level) in another section whose
  text equals it is an error. Comparison is exact after folding both sides:
  Unicode decomposition with accents dropped, case folded, punctuation turned
  into spaces, spaces collapsed. There is no partial or fuzzy match.
- **Part 2 template** (`verdict: required`): prose before the first `##` and
  no listing there; at least one `res` listing and one listing in another
  fence language with `run=none`; the last heading is the template's
  `## Veredicto`; the last sentence under it starts with the template's
  `Según este criterio, Residuum`.
- **Word budget.** Prose words (paragraphs and list items; not code,
  listings, outputs, explanations, headings, tables, figures or comments)
  within ±15 % of `words` (constant `WORD_TOLERANCE`, from `AGENTS.md`).

### Language

Prose units are paragraphs, list items and explanation blocks
(`prose.py`). Explanations are checked but do not count toward words or
readability. Inline code, URLs, `@sec:`-style references and citations are
masked (one word each) before sentences are split. A sentence ends at
`.`, `!`, `?` or `…` followed by space and a capital, `¿`, `¡`, a digit, an
opening quote or bracket, or the end of the unit, so "6.8", "1,5" and
lower-case continuations do not split; a built-in list of abbreviations
(`p. ej.`, `etc.`, `Sr.`, `cf.` …) never ends a sentence.

- `check` rules: sentence words, paragraph words, commas per sentence
  (decimal commas excluded; list items exempt, since a list is the cure),
  runs of one-sentence paragraphs (consecutive paragraphs under the same
  heading; a list, listing or heading breaks the run; reported once).
- `patterns` rules: matched per sentence, case-insensitively. For `jerga`, a
  match overlapping a `terms.txt` spelling (field 1) is skipped.
- `sentence_initial` rules: each sentence that opens with a connector is
  reported; the second and later uses of the same one say "repetido".
- `avoid:` spellings (fifth field of `terms.txt`) found in prose are findings
  with `terms.policy`.
- Placeholders `TODO`, `FIXME`, `XXX` and `Respaldar…` in prose: `hard`.
- Readability: Fernández-Huerta per section, `206.84 − 60·(sílabas/palabras)
  − 1.02·(palabras/oraciones)`, with the syllable counter ported from
  `~/hanskellsen_docs/flesch_kincaid.py`. Never fails; under 10 words, "—".

### Citations and Fuentes

`[@key]`, `[@a; @b, p. 3]` and `@key` (not `@sec:`, `@lst:`, `@fig:`,
`@tbl:`, not inside inline code or fences, not after a word character as in
an e-mail address) must name an entry of `bib/references.bib`, read by a
small BibTeX reader (`bib.py`: `%` lines are comments; `@comment`,
`@preamble`, `@string` are skipped). In the text, `[@key]` becomes
"(Autor, año)" and `@key` "Autor (año)", linked. The `sources` back-matter
entry is generated: the cited entries only, sorted by author and year.
Names are split at `and` outside braces; a name wrapped whole in braces
(`author = {{Court of Appeals of New York}}`) is corporate and shown whole,
in the text and in Fuentes. Persons are shortened to the family name.

### Report

`out/report.md` is written on every build, failing or not: per section the
status (`status:` in the spine entry, else "pendiente" without a file,
"borrador" with one, "generada" for generated pages), words against the
budget, Fernández-Huerta, counts of errors, hard and advisory findings,
TODOs, and listings (ok / fallidos / sin expected); then every finding with
file:line, rule, type, message and excerpt, and the build's other errors.

## Rendering (phase 4)

Code: `render.py` (HTML and the print stylesheet `PRINT_CSS`), `pdf.py`,
`booklet.py`, `text.py`, `colophon.py`, `reference.py`, `gitinfo.py`.
HTML is the default output; the others are opt-in, so `--draft` builds stay
fast.

### The virtual environment

WeasyPrint and pypdf live in `.venv/` at the repository root (ignored by
git), never system-wide:

```sh
python3 -m venv .venv && .venv/bin/pip install -r build/requirements.txt
```

`build/requirements.txt` pins every package (the build's own three,
WeasyPrint, pypdf and their dependencies). WeasyPrint also needs the system
libraries pango, harfbuzz and fontconfig; the fonts used are DejaVu Serif,
Sans and Sans Mono (Liberation as fallback). When `--pdf`, `--booklet` or
`--all` is given, `./book` re-executes itself with `.venv/bin/python`; if the
venv does not exist it stops with a Spanish message saying how to create
it. HTML and `--txt` builds run with the plain system `python3` (with
`markdown-it-py`, `jinja2`, `pyyaml`).

### Outputs

- **`out/index.html`.** Title page (title and `book.authors`), colophon,
  front matter, table of contents (parts,
  sections and their `##` subsections, back matter and Appendix C's
  subsections), lists of listings, of figures and of tables (the last two
  only when the book has any), body, back matter.
- **`out/residuum.pdf`.** The same HTML rendered by WeasyPrint with the
  `<style media="print">` sheet: A5 pages, mirrored margins, running heads
  (part on left pages, section on right pages, set with `string-set`), page
  numbers at the foot, every part and back-matter entry starting on a right
  page, `hyphens: auto` with `lang="es"` (pyphen's Spanish patterns), code
  and outputs wrapped (`pre-wrap`) at 7 pt so nothing overflows, page
  numbers in every index (`target-counter`), and working internal links.
  The title page and colophon have no heads or numbers. Metadata: title
  from `<title>`, author from `<meta name="author">` (`book.authors`), `/Lang
  es` from `<html lang>`. Outline (bookmarks, from `bookmark-level` in
  `PRINT_CSS`): colophon, front matter, the indexes, parts and back matter at
  level 1, sections and appendix subsections at 2, subsections at 3. The PDF
  is tagged (WeasyPrint's `pdf_tags=True`: `/StructTreeRoot`, `/MarkInfo`).
  Tables use automatic layout; cells never hyphenate words of 8 characters
  or fewer (`hyphenate-limit-chars: 9 4 4`) and rows do not split across
  pages. Inline code is never hyphenated: `render.break_code` keeps each code
  word whole (a nowrap span when it holds `-` or `/`) and, only in a word
  longer than its measure (60 characters in prose; 90 divided by the column
  count in a table), adds `<wbr>` before `.` and after `_`, `/`, `::`, `(`.
- **`out/residuum-booklet.pdf`.** Fold-and-staple imposition of the PDF on
  sheets twice the page width (A4 landscape for A5), ported from
  `~/hanskellsen_docs/build_booklet.py`. Blank pages pad the end to a
  multiple of 4 (the original keeps the last page as a back cover; this book
  has none). Its PDF title is the book's plus " (folleto para imprimir)", so
  that it is not taken for the reading edition, `out/residuum.pdf`. Print double-sided, flip on the short edge, fold, staple.
  `booklet_order(n)` gives the page order and is unit-tested.
- **`out/residuum.txt`.** The whole book as plain text: colophon, table of
  contents, indexes, numbered headings, prose (Markdown kept, references
  and citations as words, comments removed), listings indented four spaces
  with their outputs, Appendix A, Fuentes and Appendix C.

### Colophon

Front matter after the title page, in Spanish: the Residuum commit (full
sha and commit date, from `git rev-parse` / `git show -s` on the Residuum
repository), the build tool's git state (`git log -1` of this repository,
plus "con cambios sin confirmar" when `build/` or `book` differ), the
Python, WeasyPrint and pypdf versions of the interpreter that ran the build
("no instalado en este Python" for an HTML build with the system python),
the build date and the mode, after the authors (`book.authors`). Only the date varies between builds of the
same checkout; set `SOURCE_DATE_EPOCH` to fix it.

### Appendix C

The `appendix-c` back-matter entry is
`git -C <residuum> show <full pinned sha>:docs/language-reference.md`
(never the working tree; `--residuum` picks the repository). The
document's `#` title is dropped (the appendix heading replaces it); `##`
headings become numbered subsections (C.1, C.2, …; the letter follows the
entry's position among the appendices), `###` become C.1.1, deeper levels
are unnumbered. The text is Residuum's own Markdown: book references,
citations, listing syntax and the checks do not apply to it. Relative links
point to the file on GitHub at the full pinned sha. If the file cannot be
read, a final build fails and a draft shows a placeholder with a warning.
A `sections/appendix-c.md` file is an error, as for the other generated
entries.

### Tests

`build/tests/test_render.py`: plain text, Appendix C (from a throwaway git
repository, pinned to its first commit), colophon, lists of figures and
tables, booklet order for 8 and 10 pages, and, only when `.venv/` exists,
a PDF and booklet build of the sample (more than one page, a section title
in the extracted text). `build/tests/test_front.py`: front matter (render,
unnumbered `@sec:preface`, checks, draft placeholder, duplicate ids, spine
evidence), authors, corporate authors, inline-code breaks, and (venv only)
the PDF outline, metadata, tagging and the booklet title.
