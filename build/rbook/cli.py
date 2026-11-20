"""Command line: ./book build | check-spine | accept | warm."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import DEFAULT_RESIDUUM
from . import bib as bibmod
from .book import BuildFailed, collect
from .colophon import make_colophon
from .diagrams import render_figures
from .reference import load_reference
from .checks import check_book, load_rules
from .readability import FORMULAS
from .render import render_book
from .report import write_report
from .spinecheck import check_spine
from .runner import PINNED_KINDS, RunError, Runner, compare, expected_path, normalise, unified_diff

REPO_ROOT = Path(__file__).resolve().parents[2]
WARM_EXAMPLE = "examples/experiments/four_counterexample.res"


def say(message=""):
    print(message, file=sys.stderr)


def make_runner(book, args):
    return Runner(book.root, book.commit, args.residuum, launcher=args.launcher, log=say, cache=args.cache)


def run_listings(book, runner, errors, only=None):
    """Fill listing.shown / listing.result and compare with expected/."""
    for listing in book.listings:
        where = f"{listing.path}:{listing.line}: listado {listing.label}"
        listing.shown = listing.body + "\n"
        listing.status = "ok"
        if listing.kind == "none":
            continue
        if listing.kind == "include":
            try:
                listing.shown = runner.include(listing.include)
            except RunError as error:
                listing.status = "fallido"
                errors.append(f"{where}: {error}")
            continue
        result = runner.run(listing)
        listing.result = result
        if result.error:
            listing.status = "fallido"
            errors.append(f"{where}: {result.error}")
            continue
        status, diff = compare(book.root, listing, result.text)
        if status != "same":
            listing.status = "fallido" if status == "differs" else "sin expected"
        if status == "differs":
            errors.append(f"{where}: la salida no coincide con expected/{listing.label}.out "
                          f"(revisa el diff; si es correcta: ./book accept {listing.label})\n{diff}")
        elif status == "missing":
            listing.unpinned = True
            message = (f"{where}: falta expected/{listing.label}.out; revisa la salida y "
                       f"ejecuta ./book accept {listing.label}")
            if book.draft:
                book.warnings.append(message)
            else:
                errors.append(message)
    pinned = {listing.label for listing in book.listings if listing.kind in PINNED_KINDS}
    directory = book.root / "expected"
    if directory.is_dir():
        for path in sorted(directory.glob("*.out")):
            if path.stem not in pinned:
                book.warnings.append(f"expected/{path.name}: ningún listado ejecutable con esa etiqueta")


def guidelines_dir(args, root):
    if args.guidelines:
        return args.guidelines
    local = root / "guidelines"
    return local if local.is_dir() else REPO_ROOT / "guidelines"


def load_bib(root, errors):
    """Read every bib/*.bib file (one per writer avoids edit conflicts).

    A key defined in two files is an error, as within one file.
    """
    merged, origin = {}, {}
    for path in sorted((root / "bib").glob("*.bib")):
        name = f"bib/{path.name}"
        try:
            entries = bibmod.read_bib(path.read_text(encoding="utf-8"))
        except bibmod.BibError as error:
            errors.append(f"{name}: {error}")
            continue
        for key, entry in entries.items():
            if key in merged:
                errors.append(f"{name}: clave repetida: {key} (ya está en {origin[key]})")
                continue
            merged[key], origin[key] = entry, name
    return merged


def cmd_check_spine(args):
    spine, errors, checked = check_spine(args.spine, args.residuum)
    if errors:
        return fail(errors)
    count = (len(spine.get("front_matter") or []) + sum(len(p["sections"]) for p in spine["parts"])
             + len(spine.get("back_matter") or []))
    commit = (spine.get("book") or {}).get("pinned_commit")
    say(f"spine correcto: {count} entradas, {len(spine.get('owners') or {})} dueños, "
        f"{checked} evidencias resueltas en {commit}")
    return 0


def cmd_build(args):
    _, spine_errors, _ = check_spine(args.spine, args.residuum)
    try:
        book, errors = collect(args.spine, draft=args.draft)
    except BuildFailed as failure:
        return fail(spine_errors + [e for e in failure.errors if e not in spine_errors])
    errors[:0] = spine_errors
    try:
        rules = load_rules(guidelines_dir(args, book.root))
    except BuildFailed as failure:
        return fail(failure.errors)
    book.bib = load_bib(book.root, errors)
    findings, stats, book.cited = check_book(book, rules, book.bib)
    other = list(errors)
    load_reference(book, args.residuum, errors)
    run_listings(book, make_runner(book, args), errors)
    render_figures(book, Path(args.cache).resolve() if args.cache else book.root / ".cache", errors)
    colophon = make_colophon(book, args.residuum)
    page = render_book(book, errors, colophon)
    other += errors[len(other):]
    failing = [f for f in findings if f.policy == "error" or (f.policy == "hard" and not book.draft)]
    reported = [f for f in findings if f.policy == "hard" and book.draft]
    advisory = [f for f in findings if f.policy == "advisory"]
    for warning in book.warnings:
        say(f"aviso: {warning}")
    for finding in reported:
        say(f"aviso: {finding.text()}")
    out = book.root / "out"
    report = out / "report.md"
    write_report(book, report, findings, stats, other, book.draft, FORMULAS[rules.formula])
    say(f"informe: {report} ({len(failing)} hallazgos que fallan, {len(reported)} duros en borrador, "
        f"{len(advisory)} consejos)")
    errors += [f.text() for f in failing]
    if errors:
        return fail(errors)
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(page, encoding="utf-8")
    ran = [l for l in book.listings if l.result is not None]
    cached = sum(1 for l in ran if l.result.cached)
    say(f"{'borrador' if book.draft else 'build final'}: {sum(len(p.sections) for p in book.parts)} secciones, "
        f"{len(book.listings)} listados ({len(ran)} ejecutados, {cached} de la caché) -> "
        f"{out / 'index.html'}")
    return write_outputs(book, page, colophon, out, args)


def write_outputs(book, page, colophon, out, args):
    """The optional outputs: plain text, PDF and booklet."""
    if args.txt:
        from .text import render_text
        path = out / "residuum.txt"
        path.write_text(render_text(book, colophon), encoding="utf-8")
        say(f"texto: {path}")
    if args.pdf or args.booklet:
        from . import pdf
        try:
            pdf.require()
        except pdf.PdfUnavailable as error:
            return fail([str(error)])
        path = out / "residuum.pdf"
        pages = pdf.write_pdf(page, out, path)
        say(f"pdf: {path} ({pages} páginas)")
        if args.booklet:
            from .booklet import impose_pdf
            booklet = out / "residuum-booklet.pdf"
            sides, pages = impose_pdf(path, booklet)
            say(f"folleto: {booklet} ({sides} caras, {sides // 2} hojas, {pages} páginas más "
                f"{sides * 2 - pages} en blanco); imprime a doble cara, volteo por el borde corto, "
                "dobla y grapa por el centro")
    return 0


def cmd_accept(args):
    try:
        book, errors = collect(args.spine, draft=True)
    except BuildFailed as failure:
        return fail(failure.errors)
    for error in errors:
        say(f"aviso (no impide accept): {error}")
    runnable = {l.label: l for l in book.listings if l.kind in PINNED_KINDS}
    if args.all:
        targets = list(runnable.values())
    else:
        unknown = [label for label in args.labels if label not in runnable]
        if unknown:
            return fail([f"{label}: no hay ningún listado ejecutable con esa etiqueta" for label in unknown])
        targets = [runnable[label] for label in args.labels]
    runner = make_runner(book, args)
    problems = []
    for listing in targets:
        result = runner.run(listing)
        if result.error:
            problems.append(f"{listing.path}:{listing.line}: listado {listing.label}: {result.error}")
            continue
        status, diff = compare(book.root, listing, result.text)
        if status == "same":
            say(f"{listing.label}: sin cambios")
            continue
        if status == "missing":
            diff = unified_diff("", result.text, "/dev/null", f"expected/{listing.label}.out")
        say(diff.rstrip("\n"))
        path = expected_path(book.root, listing.label)
        path.parent.mkdir(exist_ok=True)
        path.write_text(result.text, encoding="utf-8")
        say(f"{listing.label}: escrito expected/{listing.label}.out")
    if problems:
        return fail(problems)
    return 0


def cmd_warm(args):
    """One compile-and-run of the launcher at the pinned commit (no cache)."""
    try:
        book, _ = collect(args.spine, draft=True)
    except BuildFailed as failure:
        return fail(failure.errors)
    runner = make_runner(book, args)
    try:
        launcher = runner.launcher_path()
    except RunError as error:
        return fail([str(error)])
    fixture = Path(args.file).resolve() if args.file else launcher.parent / WARM_EXAMPLE
    status, out, err = runner.invoke(launcher, args.command_name, fixture)
    say(normalise(err).rstrip("\n"))
    print(normalise(out), end="")
    return status


def fail(errors):
    for error in errors:
        say(f"error: {error}")
    say(f"{len(errors)} error(es); el build falla")
    return 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="book", description="Build de «The Residuum Programming Language».")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--spine", type=Path, default=REPO_ROOT / "spine.yaml",
                        help="spine del libro; su carpeta es la raíz del proyecto (por defecto ./spine.yaml)")
    common.add_argument("--residuum", type=Path, default=Path(DEFAULT_RESIDUUM),
                        help="repositorio de Residuum, sólo lectura (por defecto %(default)s)")
    common.add_argument("--launcher", type=Path, default=None,
                        help="otro launcher (sólo para tests); por defecto el de la exportación del commit fijado")
    common.add_argument("--cache", type=Path, default=None,
                        help="carpeta de caché y de la exportación (por defecto <raíz>/.cache)")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", parents=[common], help="construye out/index.html y out/report.md")
    build.add_argument("--draft", action="store_true",
                       help="admite secciones y salidas pendientes; los hallazgos duros sólo se informan")
    build.add_argument("--pdf", action="store_true", help="también out/residuum.pdf (necesita .venv/)")
    build.add_argument("--booklet", action="store_true",
                       help="también out/residuum-booklet.pdf, para doblar y grapar (necesita .venv/)")
    build.add_argument("--txt", action="store_true", help="también out/residuum.txt, el libro en texto plano")
    build.add_argument("--all", action="store_true", help="--pdf, --booklet y --txt")
    build.add_argument("--guidelines", type=Path, default=None,
                       help="carpeta de reglas (por defecto <raíz>/guidelines, o la del repositorio del libro)")
    build.set_defaults(func=cmd_build)
    spine_cmd = sub.add_parser("check-spine", parents=[common],
                               help="comprueba el spine y resuelve sus evidencias en el commit fijado")
    spine_cmd.set_defaults(func=cmd_check_spine)
    accept = sub.add_parser("accept", parents=[common], help="muestra el diff y escribe expected/<label>.out")
    accept.add_argument("labels", nargs="*")
    accept.add_argument("--all", action="store_true")
    accept.set_defaults(func=cmd_accept)
    warm = sub.add_parser("warm", parents=[common],
                          help="compila y ejecuta una vez el launcher en la exportación (calienta la caché de Cargo)")
    warm.add_argument("--cmd", dest="command_name", default="query", choices=("run", "query", "explain", "execute"),
                      help="orden de Residuum (por defecto query)")
    warm.add_argument("file", nargs="?", help=f"fichero .res (por defecto {WARM_EXAMPLE} de la exportación)")
    warm.set_defaults(func=cmd_warm)
    args = parser.parse_args(argv)
    if args.command == "accept" and bool(args.all) == bool(args.labels):
        parser.error("accept necesita etiquetas o --all, no ambas")
    if args.command == "build" and args.all:
        args.pdf = args.booklet = args.txt = True
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
