# Working in residuum-book

This repository builds one book, *The Residuum Programming Language*. Read
this file, then `HANDOFF.md`, then the entry for your section in
`spine.yaml`, before doing anything.

## Sources of truth

- **`spine.yaml` decides scope.** It is the table of contents and the writing
  brief: for each section it gives `purpose`, `covers`, `excludes`,
  `evidence`, `listings` and `words`, and the `owners` map gives every concept
  exactly one owning section. Do not change it to fit what you wrote; propose
  the change to the owner instead.
- **The Residuum repository at `book.pinned_commit` decides facts.** Evidence
  paths in the spine are relative to that repository
  (`/home/maitreya/residuum`, GitHub `Sollen-ai/residuum`). Read files at the
  pinned commit (`git -C ../residuum show <commit>:<path>`), not the working
  tree.
- **The build decides numbers and outputs.** Never type a section, listing,
  figure or table number, and never paste program output.

## Writing a section

1. Answer the section's `purpose`. Cover every `covers` item; write nothing
   from `excludes`.
2. For a concept owned by another section (see `owners`), write at most two
   sentences and a cross-reference (`@sec:<id>`).
3. Write only from the listed `evidence`, `docs/language-reference.md` of the
   Residuum repo, and cited literature. Never describe a feature, flag,
   message or behaviour the pinned commit does not have. If the evidence is
   not enough, stop and say what is missing; do not fill the gap.
4. Use the repo's claim classes where its docs do: THEOREM, MODEL RESULT,
   EXPERIMENTAL OBSERVATION, IMPLEMENTED + TESTED, NOT IMPLEMENTED.
5. State limitations plainly. Promise no future work beyond what a Residuum
   doc marks as pending.
6. Part 2 sections follow the series pattern: generic definition of the
   criterion, what it means for Residuum, numbered listings with at least one
   contrast language, and a closing verdict sentence ("Under this criterion,
   Residuum performs ...").
7. Define each term once, in its owner section. Use the series' criterion
   names and Residuum's own terms (Known, closure, residual requirement,
   seeds, premises, Program, RuleUse, default, effect, FOUR least model)
   consistently.
8. Stay within ±15 % of `words`.

## Listings

- A listing is a fenced block with a label, a caption, a run kind and an
  explanation, for example:

  ````text
  ```res {#lst:sale caption="A sale and its consequence" run=query}
  module Sale
  ...
  ```
  ::: explanation
  What the reader should notice, in two to five sentences.
  :::
  ````

- Run kinds: `run`, `query`, `explain`, `execute` (the Residuum CLI
  commands), `expect-error` (must fail; the error is shown), `include`
  (`include=residuum@<commit>:<path>[#Lstart-Lend]`, quoted from the repo),
  `none` (shown, not run).
- Every `res` listing is a complete module, or a fragment with a declared
  hidden setup, so the build can run it.
- The build inserts the real output after the listing, pins it under
  `expected/`, and fails when it changes. Review the diff; never edit
  `expected/` by hand to make a build pass.
- Explanations are written next to the listing and moved by the build to
  Appendix A, "Listings explained".

## Plain language

The build enforces the rules in `guidelines/` (from
`~/hanskellsen_docs/lineamientos_lenguaje_llano.txt`): short sentences, active
voice, subject–verb–details order, lists instead of comma runs, no filler,
brief paragraphs. Hard limits: 38 words per sentence, 100 words per
paragraph, 4 or more commas means "make it a list". Readability is reported
per section (Flesch–Kincaid for English). Terms in `guidelines/terms.txt` are
exempt from the jargon check.

## Running Residuum

- Run Residuum only through its launcher or bounded runner
  (`../residuum/residuum <command> <file>`,
  `python3 ../residuum/scripts/test_safe.py ...`). Never run its binaries or
  `cargo test` directly; the runner enforces 1324 MiB, no swap, one job, one
  thread and timeouts (Residuum `AGENTS.md`). Do not change those limits.
- Never edit the Residuum repository from here. Report what the book needs
  from it instead.

## Changes and review

- One section, or one build feature, per branch. A section is finished when
  the build passes with it (snippets, references, plain language, template)
  and its status in `spine.yaml` is set by the owner.
- Commit and push only when the owner asks.

## Shell notes

- `cp` is aliased to `cp -i` and hangs on overwrite; use `command cp -f`.
- Guard variables in destructive commands (`"${dir:?}"/...`), or use literal
  paths. Prefer not deleting at all.
- `grep` is `ugrep` here, and some options differ; prefer Python for scans.
