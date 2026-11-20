# Handoff: residuum-book

State on 2026-11-19. Read `AGENTS.md` first.

## What was asked

The owner's requirements, in their words where possible:

1. A repo that **builds the book automatically**.
2. It **has the code snippets**, **runs them and puts the output within the
   book**.
3. It **verifies the language guidelines** (plain language).
4. It has **everything in manageable sections**.
5. It **lists all listings**, and has **the explanation of each at the end**.
6. It **renumbers by itself**.
7. "**What else?**": see *Additional features* below; accepted as the plan.
8. **Only the Residuum book.**
9. A **table of contents as spine**, drawn from the most complete existing
   chapters and from the sections most similar to Residuum in subject matter.
10. For each section, **a very specified guideline of its subject matter**, so
    agents can write sections without content drift.

## What exists

| File | Status |
|---|---|
| `spine.yaml` | Done and translated to Spanish: 9 parts, 69 sections plus back matter, about 59,300 words. Checked: parses with no split items, unique ids, every owner resolves, every evidence entry resolves at `d4d2282`. Keys, ids, evidence, `rules:` and comments stay English |
| `AGENTS.md` | Done: standing rules for agents (English) |
| `guidelines/` | Done: `lineamientos_lenguaje_llano.txt` (verbatim), `plain-language.yaml` (machine rules, series thresholds), `terms.txt` (150 lines: one spelling per term), `criteria-template.md` (Part 2 shape) |
| `build/`, `./book` | Phases 1-5 done: build, listing runner (`steps=`/`trace=` options, cross-process lock), checks, `out/report.md`, HTML/PDF/booklet/txt (PDF tools in `.venv/`, `build/requirements.txt`), local pre-commit hook. 101 tests |
| `sections/`, `setup/`, `bib/`, `expected/` | First full draft on 2026-11-19: all 69 sections plus Appendix B, 104 listings, fact-checked against `d4d2282` by independent reviewers. Final build passes (383 A5 pages). Section `status` in the spine is still unset: the owner reviews and sets it |
| Pre-commit check | Done: `build/hooks/pre-commit`, enabled with `git config core.hooksPath build/hooks` (replaces GitHub CI; see Plan, phase 5) |

## Decisions taken, and why

- **Spine from the Haskell chapter** (`~/tableOfContentsHaskell.txt`, 8
  parts). Residuum is a general-purpose typed logic language (its experiments
  include Peano arithmetic as well as law), so the general-purpose chapter
  fits better than Catala, which is domain-specific. Haskell's Parts 4–5
  (types; subprograms, currying, partial application) match Residuum's
  rules, Programs and β-reduction closely.
- **Series additions kept:**
  - Part 1 also has "From Source Code to Machine Execution" and the criteria
    list, from `~/hanskellsen_docs/books/programming-language` 1.3–1.4 and
    `~/toccatala.txt` 1.3–1.4;
  - Part 2 is the series' fixed 12 criteria, each ending in a verdict.
- **Borrowed sub-structure:**
  - Well-Definedness takes the four subsections of the HAnSKELLsen book;
  - Modeling Ability and Semantic Clarity are adapted from Catala;
  - Part 6 names its semantic tradition in each title (denotational,
    operational, axiomatic), as the revised Catala Part 3 does;
  - the worked example (Catala 3.7.1) and the appendices (Catala 7) are kept.
- **Residuum-specific sections** with no counterpart elsewhere:
  - time as a type;
  - residuation and abduction, the core contribution, in the role Catala
    gives its default calculus;
  - FOUR entailment;
  - bounded execution;
  - effects as Residuum's input/output.
- **Drift control:** every section has a purpose, `covers`, `excludes`,
  `evidence`, `listings` and `words`, and each concept has one owner section.
- **Language: English** (provisional), like the series' PL chapters.

Sources studied:
- `~/tableOfContentsHaskell.txt`;
- `~/toccatala.txt`, `~/catala.txt` and `~/Catala Language Design.pdf` (the
  preface: audience and scope);
- `~/hanskellsen_docs/books/programming-language` (English, unfinished: stops
  at 3.3);
- `~/hanskellsen_docs/books/hanskellsen` (Spanish monograph, plain-language
  edited in `txt_edit_1/`, audited in `audit_lenguaje_llano.md`).

No Haskell or Catala chapter prose exists on this machine, only TOCs and
plans.

## Decisions settled on 2026-11-19

1. **Book language: Spanish.** Readability is Fernández-Huerta. Agent
   documents stay English.
2. **Pinned commit: `d4d2282`** (`book.pinned_commit`).
3. **Terms:** code names exactly as in the code (`Known`, `seeds`,
   `premises`, `Program`, `RuleUse`, `default`); concepts in the Spanish the
   Residuum docs use most (cierre, regla, evento, consulta, sello, premisa,
   efecto). Fixed in `guidelines/terms.txt`.
4. **Criterion names:** Expresividad, Buena definición, Tipos y estructuras de
   datos, Modularidad, Entrada y salida, Portabilidad y estandarización,
   Eficiencia y rendimiento, Pedagogía y facilidad de aprendizaje,
   Generalidad, Capacidad de modelado, Legibilidad, Claridad semántica.
   Verdict sentence: "Según este criterio, Residuum ...".
5. **Source format:** Markdown sections plus a Python build (no pandoc on this
   machine; `markdown_it` + `jinja2`).
6. **Evidence kinds** beyond repo paths: `git:log`, `git:tag`, `series:`,
   `sec:`, `listing:self` (spine header comment).

## External review (2026-11-19)

A reviewer read the first draft. Acted on: preface with the central
contribution (`front_matter: preface`), guided tour `s1.7` before the
criteria, parser determinism vs grammar unambiguity (s3.5, s9.1), table
layout, institutional authors in citations, PDF outline and tags, authors
(`book.authors`), booklet title. Not acted on: removing Appendix A
repetition (Appendix A is an owner requirement). The reviewer read the
booklet as the reading edition; send `out/residuum.pdf` to reviewers.

## Denotational section from residuum-diagrams (2026-11-19)

The owner asked for the compendium's order structures (`~/residuum-diagrams`,
`compendio/compendio.tex`) in the book's denotational block, with readable
names instead of a0, g, h. Added:
- `book.diagrams` (path, commit `ac4727f`) and the `diagrams:<entry>`
  evidence kind, checked by `check-spine` like repo evidence;
- section `s6.14` after s6.4 (numbered 6.5): closed-state lattice,
  requirements as upsets, the Heyting algebra and the residual answer as
  Heyting implication, the extensional program order, cooperating rules,
  fidelity. Owners `requirement_denotation` and `program_order`. Its example
  is the compendium's six rules as an agent deciding whether to `send`;
- `dot` figure blocks rendered by Graphviz at build time, alt text required;
- two-sentence references in s6.3, s6.8, s6.10 and s6.12, and the
  default-condition time rule in s6.9 (a compendium finding).
residuum-diagrams computed its enumerations at residuum `f3c8df3`; the
section's listings rerun the example at `d4d2282`. Known cosmetic issue:
poppler prints "Embedded font file may be invalid" for WeasyPrint's font
subsets; the pages render correctly.

## What the book needs from the Residuum repo

The book never edits Residuum; these are requests to its owner.

1. **Universality experiment (asked for on 2026-11-19).** s2.9 now says the
   core computes recursively (Peano arithmetic, polynomial sum and product)
   but that nobody has shown or ruled out that it is universal. Horn clauses
   with a successor constructor are Turing-complete in general
   (Tärnlund 1977); Residuum has `after`, recursion and decrementing matches.
   A fixture plus test in the style of the Peano experiments that simulates a
   two-counter (Minsky) machine, with a doc classifying the result, would let
   the book state universality as a tested result. When it lands, re-pin
   `book.pinned_commit`, add the doc to s2.9's evidence, and revise s2.9's
   verdict and s8.1's table row together.
2. **A machine-readable way to tell a rejected program from a refused run**
   in the launcher's output (the build parses `test_safe.py`'s diagnostics).
3. **A printable SurfaceAST/TypedAST** (s6.13 cannot show those stages).

## Open decisions (owner)

0. **Book review.** Read the draft (`out/residuum.pdf`) and set each
   section's `status`. Known gaps the writers reported:
   - No preface: the plan's "audience and scope" preface has no spine entry.
   - s3.2's EBNF is hand-written from `src/formal.rs`, not machine-checked;
     Residuum has no grammar file.
   - s6.13 cannot show SurfaceAST/TypedAST: no CLI command prints them.
   - Briefs the evidence contradicts or that need updating: s2.6 and s2.7
     have `listings: []` but the Part 2 template needs listings; s5.2/s5.7
     want `explain`, not `run`; s6.6, s7.8, s4.10 cite files outside their
     evidence lists; s6.8, s6.13, s7.7 have one-item `covers` joined by
     semicolons.
   - Residuum docs found outdated by the code (E6 in the monotonic spec on
     incremental Programs; the explicit-query-substitutions doc's
     "pendiente"): the book follows the code and says so.

1. **Where the repo lives:** local only for now, or `Sollen-ai/residuum-book`.
   Nothing in the build depends on it.
2. **Word budget.** About 59,300 words is three times the HAnSKELLsen book. The
   owner may trim `words` per section.
3. **Translator's judgement calls** to confirm (see `guidelines/terms.txt`):
   "requisito residual" (docs mostly say bare "requisito"); English terms kept
   in Spanish prose because the docs have no Spanish form (β-reduction,
   entailment, binding, provenance, launcher); "lógica de defaults";
   "significado de bajo nivel" for lowered meaning.

## Design

```
residuum-book/
  AGENTS.md  HANDOFF.md
  spine.yaml            TOC + per-section brief (source of truth for scope)
  book.yaml             (optional split of spine.yaml's `book:` block)
  sections/<id>.md      one file per spine section, e.g. sections/s6.8.md
  guidelines/           plain-language rules, terms.txt (exempt jargon),
                        criteria template
  bib/references.bib    bibliography
  expected/<label>.out  pinned listing outputs (golden files)
  build/                the tool (Python package)
  out/                  generated HTML, PDF, booklet, txt; never edited
```

Build stages, all driven by `spine.yaml`:

1. **Collect.** Read `spine.yaml`. Load `sections/<id>.md` in spine order. A
   section file with no spine entry, or a spine entry with no file, is an
   error; in draft mode it is a placeholder.
2. **Check structure.**
   - Every `covers` item is addressed: the author marks each one with a
     `<!-- covers: n -->` anchor.
   - No heading duplicates another section's owner topic.
   - Part 2 sections end in a verdict.
   - Word count is within ±15 %.
3. **Run listings.**
   - Each `res` listing runs through the Residuum launcher at the pinned commit
     (via a worktree), under its limits.
   - `expect-error` must fail; `include` copies from the repo at the commit.
   - Outputs are cached by content hash and compared with `expected/`. Any
     difference fails the build and shows the diff.
4. **Number.** Parts, sections, listings, figures and tables are numbered from
   spine order. `@sec:`, `@lst:`, `@fig:` and `@tbl:` references resolve, and
   unresolved ones fail.
5. **Check language.**
   - The plain-language rules apply, outside code blocks.
   - Readability is reported per section.
   - The terminology list fixes one spelling per term.
   - Citations resolve. "Respaldar" or TODO placeholders fail a final build
     but not a draft.
6. **Assemble.**
   - Front matter: an audience and scope preface, as in the Catala preface,
     plus a list of listings.
   - Body.
   - Sources.
   - Appendix A, "Listings explained", generated from the explanations.
   - Appendix B, the case study.
   - Appendix C, the language reference, included from the repo at the commit.
7. **Render.** HTML site, PDF, and the fold-and-staple booklet (reuse
   `~/hanskellsen_docs/build_booklet.py`), plus plain text.
8. **Report.** Per-section status (draft / review / final), word counts,
   readability, TODOs and listing results, written to `out/report.md`.

### Additional features (the "what else")

- Expected outputs pinned and diffed; `expect-error` listings for error
  examples.
- Includes from the real repo at a pinned commit, so examples cannot drift
  from the implementation.
- Fragments with a hidden setup module.
- The tool versions and the Residuum commit printed in the colophon.
- A template check for the series structure, including the 12 criteria in
  order with verdicts.
- Cross-reference and link checking; a bibliography (BibTeX/CSL); a glossary
  built from owner sections; an index built from marked terms.
- Per-section status, word counts and a TODO report.
- Snippets executed under Residuum's resource limits.
- Diagrams as text (Graphviz/Mermaid) rendered at build time, with alt text
  required.
- A local pre-commit check: the tests, the spine check and a draft build
  (which re-runs changed listings through the launcher) must pass before a
  commit. No remote CI: listings run only through Residuum's launcher, which
  needs this machine's systemd session; GitHub runners lack it.

## Plan

Each phase ends with its acceptance check passing.

| Phase | Work | Accepted when |
|---|---|---|
| 0 | Settle the open decisions; `git init`; pin the commit; add `guidelines/` from the hanskellsen lineamientos | `spine.yaml` has `pinned_commit`; the guidelines file exists |
| 1 | Build core: collect, number, cross-references, list of listings, Appendix A, HTML output | A two-section sample builds with renumbering after reordering the spine |
| 2 | Listing runner: launcher at the pinned commit, `expect-error`, `include`, hidden setup, cache, `expected/` diffs | A changed output fails the build with a diff |
| 3 | Checks: structure, `covers` anchors, verdicts, word budget, plain language, terms, citations, placeholders | Each check has a failing and a passing fixture |
| 4 | Render PDF and booklet; colophon; report | The booklet prints from the sample |
| 5 | Local pre-commit check (no remote CI) | A commit with a broken listing is refused |
| 6 | Writing: one pilot section first (suggested `s6.8`, residuation, the hardest and most central), reviewed against its brief; then the rest in parallel, one section per branch | The pilot passes the build and the owner's review |

## Notes for whoever continues

- **Build state:** phases 0-3 accepted on 2026-11-19 (`python3 -m pytest
  build/tests`; `./book build --draft`). Hidden setups live in
  `setup/<name>.res` (`setup=<name>` on a fence). The pinned commit is run from
  a read-only `git archive` export in `.cache/residuum-<commit>/`, never a
  worktree; a cold compile there took 16 s at 637 MiB, inside the runner's
  limits.
- **Spine flow lists:** an unquoted comma inside `[a, b]` splits an item.
  `./book check-spine` catches unbalanced parentheses and null keys, not every
  split; quote any item that contains a comma.

- **Residuum's own rules apply** when running its code: launcher or bounded
  runner only, no direct `cargo test`, limits unchanged.
- **Event times:** after `@`, a time is a name or `after` plus a name. Nested
  `after(...)` is only valid as an argument. This was found while writing the
  language reference and is easy to get wrong in listings.
- **Rule reading direction:** `A <= C` reads "A implies C". Listings have got
  this backwards before.
- **The HAnSKELLsen PL book's flaws to avoid:**
  - PDF footer artifacts repeated in the text;
  - cross-references copied from another chapter ("see Listing 5");
  - unfinished final parts;
  - placeholder citations.
