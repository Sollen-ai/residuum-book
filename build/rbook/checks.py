"""Phase 3 checks on the section files: structure and language.

Every check returns findings. A finding's ``policy`` decides what it does:

* ``error``: fails every build, draft or final (covers anchors, owner
  headings, the Part 2 template, citations);
* ``hard``: fails a final build, reported as a warning in ``--draft``
  (word budget, the ``hard`` plain-language rules, avoided term spellings,
  placeholders);
* ``advisory``: reported in ``out/report.md`` only.

The rules come from ``guidelines/``: ``plain-language.yaml`` (thresholds,
patterns, policies), ``terms.txt`` (exempt terms and avoided spellings) and
``criteria-template.md`` (the verdict heading and the verdict sentence's
opening words). Nothing here repeats their values.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import bib as bibmod
from .book import BuildFailed
from .parse import FENCE_RE
from .prose import MASK, excerpt, mask, read_doc, sentences, words
from .readability import FORMULAS, fernandez_huerta

WORD_TOLERANCE = 0.15            # AGENTS.md rule 8: within ±15 % of `words`
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|FIXME|XXX)\b|\bRespaldar\w*")
COMPARISONS = {">=": lambda a, b: a >= b, ">": lambda a, b: a > b,
               "<=": lambda a, b: a <= b, "<": lambda a, b: a < b}
CHECK_RE = re.compile(r"^\s*(?P<metric>.+?)\s*(?P<op>>=|<=|>|<)\s*thresholds\.(?P<name>\w+)\s*$")
METRICS = {
    "sentence word count": "sentence_words",
    "paragraph word count": "paragraph_words",
    "commas in one sentence": "sentence_commas",
    "consecutive one-sentence paragraphs": "one_sentence_run",
}
DECIMAL_COMMA_RE = re.compile(r"(?<=\d),(?=\d)")


@dataclass
class Finding:
    path: str
    line: int
    rule: str
    policy: str          # error | hard | advisory
    message: str
    excerpt: str = ""
    section: str = ""
    category: str = ""   # language | terms | placeholder | words | structure | citation

    def text(self):
        where = f"{self.path}:{self.line}" if self.line else self.path
        quote = f" «{self.excerpt}»" if self.excerpt else ""
        return f"{where}: [{self.rule}] {self.message}{quote}"


@dataclass
class Rules:
    thresholds: dict
    measures: list = field(default_factory=list)    # (rule, metric, op, threshold)
    patterns: list = field(default_factory=list)    # (rule, [compiled])
    connectors: list = field(default_factory=list)  # (rule, [phrases])
    terms: list = field(default_factory=list)       # exempt spellings
    avoid: dict = field(default_factory=dict)       # variant -> preferred spelling
    terms_policy: str = "hard"
    verdict_heading: str = ""
    verdict_prefix: str = ""
    formula: str = "fernandez-huerta"
    notes: list = field(default_factory=list)


def load_rules(directory):
    """Read guidelines/; raise BuildFailed if a rule file is missing or unusable."""
    directory = Path(directory)
    errors = []
    path = directory / "plain-language.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise BuildFailed([f"{path}: no se pueden leer las reglas: {error}"])
    rules = Rules(thresholds=dict(data.get("thresholds") or {}))
    for rule in data.get("rules") or []:
        ident, policy = rule.get("id"), rule.get("policy")
        if policy not in ("hard", "advisory"):
            errors.append(f"{path}: regla {ident}: policy debe ser hard o advisory")
            continue
        rule = dict(rule)
        if "check" in rule:
            match = CHECK_RE.match(rule["check"])
            if not match or match.group("metric") not in METRICS:
                errors.append(f"{path}: regla {ident}: no sé evaluar «{rule['check']}»")
                continue
            name = match.group("name")
            if name not in rules.thresholds:
                errors.append(f"{path}: regla {ident}: falta thresholds.{name}")
                continue
            rules.measures.append((rule, METRICS[match.group("metric")], match.group("op"),
                                   rules.thresholds[name]))
        elif "patterns" in rule:
            try:
                compiled = [re.compile(p, re.IGNORECASE) for p in rule["patterns"]]
            except re.error as error:
                errors.append(f"{path}: regla {ident}: patrón no válido: {error}")
                continue
            rules.patterns.append((rule, compiled))
        elif "sentence_initial" in rule:
            rules.connectors.append((rule, list(rule["sentence_initial"])))
        else:
            errors.append(f"{path}: regla {ident}: sin check, patterns ni sentence_initial")
    readability = data.get("readability") or {}
    rules.formula = readability.get("formula", rules.formula)
    if rules.formula not in FORMULAS:
        errors.append(f"{path}: readability.formula {rules.formula} no está implementada")
    terms = data.get("terms") or {}
    rules.terms_policy = terms.get("policy", "hard")
    terms_path = directory / (terms.get("file") or "terms.txt")
    try:
        for n, line in enumerate(terms_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            fields = line.split("\t")
            spelling = fields[0].strip()
            rules.terms.append(spelling)
            for extra in fields[4:]:
                extra = extra.strip()
                if extra.startswith("avoid:"):
                    for variant in extra[len("avoid:"):].split(","):
                        if variant.strip():
                            rules.avoid[variant.strip()] = spelling
                elif extra:
                    errors.append(f"{terms_path}:{n}: quinto campo desconocido «{extra}»")
    except OSError as error:
        errors.append(f"{terms_path}: {error}")
    template = directory / "criteria-template.md"
    try:
        rules.verdict_heading, rules.verdict_prefix = _template(template.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        errors.append(f"{template}: {error}")
    if errors:
        raise BuildFailed(errors)
    rules.term_res = [re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)", re.IGNORECASE)
                      for t in sorted(rules.terms, key=len, reverse=True)]
    rules.avoid_res = [(v, p, re.compile(r"(?<!\w)" + re.escape(v) + r"(?!\w)", re.IGNORECASE))
                       for v, p in rules.avoid.items()]
    return rules


def _template(text):
    """Read the verdict heading and sentence opening from the "Checked" list."""
    checked = re.search(r"^## Checked\s*$(?P<body>.*?)(?=^## |\Z)", text, re.M | re.S)
    if not checked:
        raise ValueError("no encuentro la lista «## Checked»")
    item = re.search(r"\*\*Verdict\.\*\*(?P<body>.*?)(?=^\d+\.\s|\Z)", checked.group("body"), re.M | re.S)
    if not item:
        raise ValueError("no encuentro el punto «**Verdict.**» de la lista «Checked»")
    body = item.group("body")
    heading = re.search(r"`(##\s[^`]+)`", body)
    prefix = re.search(r"starts\s+with\s+`([^`]+)`", body)
    if not heading or not prefix:
        raise ValueError("el punto «Verdict» no da el título `## …` ni «starts with `…`»")
    return heading.group(1).strip(), prefix.group(1).strip()


def fold(text):
    """Case- and accent-insensitive form used to compare headings."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^\w\s]", " ", text.casefold())
    return " ".join(text.split())


# ---------------------------------------------------------------------------

@dataclass
class SectionStats:
    words: int = 0
    budget: int | None = None
    readability: float | None = None
    findings: list = field(default_factory=list)


def check_book(book, rules, bib):
    """Run the section checks. Returns (findings, stats by entry id, cited keys)."""
    findings, stats, cited = [], {}, []
    owner_titles = {}
    by_id = {entry.id: entry for entry in book.entries()}
    for concept, owner in (book.spine.get("owners") or {}).items():
        if owner in by_id:
            owner_titles.setdefault(fold(by_id[owner].spine.get("title", "")), []).append((concept, owner))
    for entry in book.entries():
        if entry.path is None:
            continue
        rel = str(entry.path.relative_to(book.root))
        text = entry.path.read_text(encoding="utf-8")
        doc = read_doc(text)
        here = []

        def add(line, rule, policy, message, quote="", category="structure"):
            here.append(Finding(rel, line, rule, policy, message, quote, entry.id, category))

        _covers(entry, doc, add)
        _owners(entry, doc, owner_titles, add)
        if entry.spine.get("verdict") == "required":
            _template_check(entry, doc, rules, add)
        stat = SectionStats()
        _language(doc, rules, add, stat)
        _budget(entry, stat, add, rel)
        _citations(text, bib, add, cited)
        stat.findings = here
        stats[entry.id] = stat
        findings.extend(here)
    return findings, stats, cited


def _covers(entry, doc, add):
    expected = []
    for n, _ in enumerate(entry.spine.get("covers") or [], 1):
        expected.append(str(n))
    for k, sub in enumerate(entry.spine.get("subsections") or [], 1):
        for n, _ in enumerate((sub or {}).get("covers") or [], 1):
            expected.append(f"{k}.{n}")
    seen = {}
    for value, line in doc.anchors:
        if value not in expected:
            add(line, "covers", "error", f"ancla covers: {value} desconocida; el spine da "
                + (", ".join(expected) if expected else "ningún punto covers"))
        elif value in seen:
            add(line, "covers", "error", f"ancla covers: {value} repetida (primera en la línea {seen[value]})")
        else:
            seen[value] = line
    for value in expected:
        if value not in seen:
            item = _covers_item(entry.spine, value)
            add(0, "covers", "error", f"falta el ancla <!-- covers: {value} -->", _short(item))


def _covers_item(spine, value):
    if "." in value:
        k, n = (int(x) for x in value.split("."))
        return str(spine["subsections"][k - 1]["covers"][n - 1])
    return str(spine["covers"][int(value) - 1])


def _short(text, limit=90):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def _owners(entry, doc, owner_titles, add):
    for heading in doc.headings:
        for concept, owner in owner_titles.get(fold(heading.title), []):
            if owner != entry.id:
                add(heading.line, "dueño", "error",
                    f"el título repite el de la sección dueña de «{concept}» ({owner}); "
                    f"remite a ella con @sec:{owner}", heading.title)


def _template_check(entry, doc, rules, add):
    first_sub = next((n for n, h in enumerate(doc.headings) if h.level == 2), None)
    if first_sub is None:
        add(0, "plantilla", "error", "una sección de la Parte 2 necesita subsecciones ## y "
            f"«{rules.verdict_heading}» al final")
    else:
        before = [u for u in doc.units if u.after_heading < first_sub and u.kind != "explanation"]
        if not before:
            add(doc.headings[first_sub].line, "plantilla", "error",
                "falta la definición genérica del criterio antes del primer ##")
        early = [l for l in doc.listings if l.after_heading < first_sub]
        if early:
            add(early[0].line, "plantilla", "error", "un listado antes del primer ##; la sección abre "
                "con la definición genérica")
    if not any(l.lang == "res" for l in doc.listings):
        add(0, "plantilla", "error", "falta un listado res")
    if not any(l.lang and l.lang != "res" and l.kind == "none" for l in doc.listings):
        add(0, "plantilla", "error", "falta un listado de contraste en otro lenguaje con run=none")
    level = len(rules.verdict_heading) - len(rules.verdict_heading.lstrip("#"))
    title = rules.verdict_heading.lstrip("#").strip()
    last = doc.headings[-1] if doc.headings else None
    if last is None or last.level != level or fold(last.title) != fold(title):
        add(last.line if last else 0, "plantilla", "error",
            f"el último título debe ser «{rules.verdict_heading}»", last.title if last else "")
        return
    body = [u for u in doc.units if u.kind != "explanation" and u.after_heading == len(doc.headings) - 1]
    final = sentences(body[-1])[-1] if body else None
    if final is None or not final.raw.startswith(rules.verdict_prefix):
        add(final.line if final else last.line, "plantilla", "error",
            f"la última oración debe empezar por «{rules.verdict_prefix}»", final.raw if final else "")


def _language(doc, rules, add, stat):
    measures = {metric: (rule, op, limit) for rule, metric, op, limit in rules.measures}
    counts = {}
    prose_words, all_words, sentence_count = 0, [], 0
    run = []        # consecutive one-sentence paragraphs

    def measure(metric, value, line, quote, unit_text=""):
        if metric not in measures:
            return
        rule, op, limit = measures[metric]
        if COMPARISONS[op](value, limit):
            add(line, rule["id"], rule["policy"], f"{rule.get('label', rule['id'])}: {value} (límite {op} {limit})",
                quote, "language")

    def close_run():
        if run and "one_sentence_run" in measures:
            measure("one_sentence_run", len(run), run[0].line, excerpt(run[0].text, 60))
        run.clear()

    last_heading = None
    for unit in doc.units:
        if unit.kind != "para" or unit.after_heading != last_heading:
            close_run()
        last_heading = unit.after_heading
        masked = mask(unit.text)
        unit_words = words(masked)
        if unit.kind != "explanation":
            prose_words += len(unit_words)
            all_words.extend(w for w in unit_words if w != MASK)
        measure("paragraph_words", len(unit_words), unit.line, excerpt(unit.text, 60))
        found = sentences(unit)
        if unit.kind != "explanation":
            sentence_count += len(found)
        for sentence in found:
            measure("sentence_words", len(words(sentence.text)), sentence.line, sentence.raw)
            if unit.kind != "item":
                commas = DECIMAL_COMMA_RE.sub("", sentence.text).count(",")
                measure("sentence_commas", commas, sentence.line, sentence.raw)
            _patterns(sentence, rules, add)
            _connectors(sentence, rules, add, counts)
            for variant, preferred, regex in rules.avoid_res:
                if regex.search(sentence.text):
                    add(sentence.line, "términos", rules.terms_policy,
                        f"«{variant}»: el libro escribe «{preferred}»", sentence.raw, "terms")
            for match in PLACEHOLDER_RE.finditer(sentence.text):
                add(sentence.line, "marcador", "hard", f"marcador pendiente «{match.group(0)}»",
                    sentence.raw, "placeholder")
        if unit.kind == "para" and len(found) == 1:
            run.append(unit)
        else:
            close_run()
    close_run()
    stat.words = prose_words
    stat.readability = fernandez_huerta(all_words, sentence_count)


def _patterns(sentence, rules, add):
    exempt = None
    for rule, compiled in rules.patterns:
        for regex in compiled:
            for match in regex.finditer(sentence.text):
                if rule["id"] == "jerga":
                    if exempt is None:
                        exempt = [m.span() for r in rules.term_res for m in r.finditer(sentence.text)]
                    if any(a < match.end() and match.start() < b for a, b in exempt):
                        continue
                add(sentence.line, rule["id"], rule["policy"],
                    f"{rule.get('label', rule['id'])}: «{match.group(0)}»", sentence.raw, "language")


def _connectors(sentence, rules, add, counts):
    text = sentence.text.lstrip("¿¡\"'“«(")
    for rule, phrases in rules.connectors:
        for phrase in phrases:
            if re.match(re.escape(phrase) + r"(?!\w)", text, re.IGNORECASE):
                key = phrase.casefold()
                counts[key] = counts.get(key, 0) + 1
                times = counts[key]
                again = f"; repetido ({times}.ª vez en la sección)" if times > 1 else ""
                add(sentence.line, rule["id"], rule["policy"],
                    f"{rule.get('label', rule['id'])}: abre con «{phrase}»{again}", sentence.raw, "language")
                break


def _budget(entry, stat, add, rel):
    target = entry.spine.get("words")
    if not isinstance(target, int) or target <= 0:
        return
    stat.budget = target
    low, high = round(target * (1 - WORD_TOLERANCE)), round(target * (1 + WORD_TOLERANCE))
    if not low <= stat.words <= high:
        add(0, "palabras", "hard", f"{stat.words} palabras de prosa; el spine pide {target} "
            f"(±{round(WORD_TOLERANCE * 100)} %: {low}-{high})", category="words")


def _citations(text, bib, add, cited):
    """Citations outside fenced code and HTML comments: captions, headings,
    prose, explanations and tables all count."""
    in_fence = None
    for n, line in enumerate(text.splitlines(), 1):
        fence = FENCE_RE.match(line)
        if in_fence:
            if re.match(r"^ {0,3}" + re.escape(in_fence[0]) + "{" + str(len(in_fence)) + r",}\s*$", line):
                in_fence = None
            continue
        if fence:
            in_fence = fence.group("fence")
            line = fence.group("info")   # the caption may cite
        line = re.sub(r"<!--.*?-->", "", line)
        for key, offset in bibmod.cited_keys(line):
            if key not in bib:
                add(n, "cita", "error", f"cita sin entrada en bib/*.bib: @{key}",
                    _short(line.strip()), "citation")
            elif key not in cited:
                cited.append(key)
