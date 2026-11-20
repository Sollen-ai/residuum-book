"""rbook: the build tool for *The Residuum Programming Language*.

Entry point: ``./book`` at the repository root (see ``build/README.md``).

Project layout (the project root is the directory that holds the spine):

    spine.yaml              table of contents, decides order and numbering
    sections/<id>.md        one file per spine entry (front_matter, then
                            parts -> sections, then back_matter)
    setup/<name>.res        hidden setup modules (see below)
    expected/<label>.out    pinned listing outputs; written only by
                            ``./book accept``
    .cache/                 output cache and the read-only export of the
                            Residuum repository at ``book.pinned_commit``
    out/index.html          the generated book
    out/residuum.pdf, out/residuum-booklet.pdf, out/residuum.txt
                            optional outputs (--pdf, --booklet, --txt, --all)
    out/report.md           the checks report (written on every build)
    bib/references.bib      the bibliography (cited entries form "Fuentes")

Listing syntax (a fenced block followed by an explanation block)::

    ```res {#lst:sale caption="Una venta" run=query}
    module Sale
    ...
    ```
    ::: explanation
    Lo que el lector debe ver.
    :::

Attributes: ``#lst:<label>`` (letters, digits, ``_`` and ``-``),
``caption="..."`` and ``run=<kind>`` are required. Kinds: ``run``, ``query``,
``explain``, ``execute`` (Residuum CLI commands), ``expect-error``,
``include``, ``none``.

Optional attributes:

* ``setup=<name>`` -- hidden setup. The file ``setup/<name>.res`` (relative to
  the project root) is joined with the listing before it runs: the build runs
  the text ``<setup file>`` + newline + ``<listing body>``. Only the listing
  body is shown. The setup is usually ``module X`` plus declarations; the
  listing then holds only the rules and experiments the text discusses.
  Error line numbers in the output count from the start of the setup.
  Allowed on ``run``, ``query``, ``explain``, ``execute`` and
  ``expect-error``.
* ``cmd=<run|query|explain|execute>`` -- the command for ``expect-error``
  (default ``run``).
* ``include=residuum@<commit>:<path>[#L<a>[-L<b>]]`` -- required for, and
  only allowed on, ``run=include``. The fence body must be empty. The commit
  must be ``book.pinned_commit``.

Other syntax: ``## Título {#sec:label}`` (``##`` numbers a subsection,
``###`` a sub-subsection; ``#`` is reserved for the spine title);
``![Pie](src){#fig:label}`` alone on a line; ``: Pie {#tbl:label}`` on the
line after a pipe table. References: ``@sec:``, ``@lst:``, ``@fig:``,
``@tbl:``; a capital first letter (``@Sec:``) capitalises the text.
"""

DEFAULT_RESIDUUM = "/home/maitreya/residuum"
