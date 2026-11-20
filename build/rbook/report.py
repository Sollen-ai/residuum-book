"""out/report.md: per-section status and every finding, in Spanish."""

from __future__ import annotations


def _status(entry):
    if entry.spine.get("status"):
        return str(entry.spine["status"])
    if entry.generated:
        return "generada"
    if entry.path is None:
        return "pendiente"
    return "borrador"


def _cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def write_report(book, path, findings, stats, other_errors, draft, formula_name):
    rows = []
    for entry in book.entries():
        stat = stats.get(entry.id)
        listings = [l for l in book.listings if l.section_id == entry.id]
        ok = sum(1 for l in listings if getattr(l, "status", "ok") == "ok")
        failed = sum(1 for l in listings if getattr(l, "status", "") == "fallido")
        unpinned = sum(1 for l in listings if getattr(l, "status", "") == "sin expected")
        here = stat.findings if stat else []
        hard = sum(1 for f in here if f.policy == "hard" and f.category in ("language", "terms"))
        advisory = sum(1 for f in here if f.policy == "advisory")
        todo = sum(1 for f in here if f.category == "placeholder")
        errors = sum(1 for f in here if f.policy == "error")
        if stat and stat.budget:
            words = f"{stat.words} / {stat.budget}"
        elif stat:
            words = str(stat.words)
        else:
            words = f"0 / {entry.spine['words']}" if isinstance(entry.spine.get("words"), int) else "—"
        ease = f"{stat.readability:.1f}" if stat and stat.readability is not None else "—"
        number = entry.number or ""
        rows.append(f"| {_cell(number)} | {_cell(entry.id)} | {_cell(entry.title)} | {_cell(_status(entry))} | "
                    f"{words} | {ease} | {errors} | {hard} | {advisory} | {todo} | "
                    f"{len(listings)} ({ok} / {failed} / {unpinned}) |")
    mode = "borrador (--draft)" if draft else "final"
    lines = [
        f"# Informe del build: {book.title}",
        "",
        f"- Modo: {mode}.",
        f"- Commit de Residuum: {book.commit or '—'}.",
        f"- Legibilidad: {formula_name} (más alto es más fácil; sólo se informa).",
        f"- Palabras: prosa de la sección (sin código, listados, salidas, explicaciones ni anclas) "
        "frente al objetivo del spine (±15 %).",
        "- Listados: total (ok / fallidos / sin expected).",
        "",
        "## Secciones",
        "",
        "| Nº | Id | Título | Estado | Palabras | Legibilidad | Errores | Duras | Consejos | TODO | Listados |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
        *rows,
        "",
        "## Hallazgos",
        "",
    ]
    if not findings:
        lines.append("Ninguno.")
    else:
        lines += ["| Lugar | Regla | Tipo | Mensaje | Extracto |", "|---|---|---|---|---|"]
        kinds = {"error": "error", "hard": "dura", "advisory": "consejo"}
        for f in findings:
            where = f"{f.path}:{f.line}" if f.line else f.path
            lines.append(f"| {_cell(where)} | {_cell(f.rule)} | {kinds[f.policy]} | {_cell(f.message)} | "
                         f"{_cell(f.excerpt)} |")
    if other_errors:
        lines += ["", "## Otros errores del build", ""]
        lines += [f"- {_cell(e.splitlines()[0])}" for e in other_errors]
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
