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
| `spine.yaml` | Done: 9 parts, 69 sections plus back matter, about 59,000 words. Checked: parses, unique ids, every owner resolves, every evidence path exists in the Residuum repo |
| `AGENTS.md` | Done: standing rules for agents |
| `HANDOFF.md` | This file |
| Build tool, guidelines, CI | Not started (plan below) |

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

## Open decisions (owner)

1. **Book language:** English (provisional) or Spanish. This decides the
   readability formula (Flesch–Kincaid or Fernández-Huerta) and the
   guidelines file.
2. **Pinned Residuum commit.** Suggested: `d4d2282` (main, language reference
   included). Set `book.pinned_commit` in `spine.yaml`.
3. **Where the repo lives:** local only for now, or `Sollen-ai/residuum-book`.
4. **Source format.** Recommended: Markdown sections plus a small Python build,
   matching `~/hanskellsen_docs` (Python, booklet tools). Alternative: Typst,
   for better PDF and numbering.
5. **Word budget.** About 59,000 words is three times the HAnSKELLsen book. The
   owner may trim `words` per section.

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
- CI: build on every push, fail on any check, upload `out/` as an artifact.

## Plan

Each phase ends with its acceptance check passing.

| Phase | Work | Accepted when |
|---|---|---|
| 0 | Settle the open decisions; `git init`; pin the commit; add `guidelines/` from the hanskellsen lineamientos | `spine.yaml` has `pinned_commit`; the guidelines file exists |
| 1 | Build core: collect, number, cross-references, list of listings, Appendix A, HTML output | A two-section sample builds with renumbering after reordering the spine |
| 2 | Listing runner: launcher at the pinned commit, `expect-error`, `include`, hidden setup, cache, `expected/` diffs | A changed output fails the build with a diff |
| 3 | Checks: structure, `covers` anchors, verdicts, word budget, plain language, terms, citations, placeholders | Each check has a failing and a passing fixture |
| 4 | Render PDF and booklet; colophon; report | The booklet prints from the sample |
| 5 | CI | A pull request with a broken listing fails |
| 6 | Writing: one pilot section first (suggested `s6.8`, residuation, the hardest and most central), reviewed against its brief; then the rest in parallel, one section per branch | The pilot passes the build and the owner's review |

## Notes for whoever continues

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
