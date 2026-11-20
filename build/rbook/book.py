"""Collect sections in spine order, number everything and resolve references."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .parse import Figure, Heading, Listing, TableCaption, parse_section, SEC_LABEL

# Back-matter entries the build generates instead of reading sections/<id>.md.
LISTINGS_APPENDIX = "appendix-a"
SOURCES = "sources"
REFERENCE = "appendix-c"   # filled from the Residuum repository by reference.py
LATER_GENERATED = {}
LISTINGS_APPENDIX_TITLE = "Listados explicados"
APPENDIX_PREFIX_RE = re.compile(r"^(?:appendix|apéndice)\s+[A-Z]\s*[:.\-–—]\s*", re.IGNORECASE)
REF_RE = re.compile(r"(?P<code>`+[^`\n]*?`+)|(?<![\w@])@(?P<kind>[Ss]ec|[Ll]st|[Ff]ig|[Tt]bl):(?P<label>"
                    + SEC_LABEL + r")")
REF_WORDS = {"sec": "sección", "lst": "listado", "fig": "figura", "tbl": "tabla"}


class BuildFailed(Exception):
    def __init__(self, errors):
        super().__init__("\n".join(errors))
        self.errors = errors


@dataclass
class Part:
    id: str
    title: str
    number: int
    anchor: str
    sections: list = field(default_factory=list)


@dataclass
class Entry:
    id: str
    title: str
    spine: dict
    part: Part | None
    number: str = ""        # "6.8", "B" or ""
    heading: str = ""       # "6.8 Title", "Apéndice B: Title"
    ref: str = ""           # "sección 6.8", "apéndice B", "Title"
    anchor: str = ""
    path: Path | None = None
    blocks: list = field(default_factory=list)
    placeholder: str | None = None
    generated: str | None = None   # "listings" for Appendix A


@dataclass
class Book:
    root: Path
    spine_path: Path
    spine: dict
    title: str
    commit: str | None
    parts: list
    back: list
    draft: bool
    front: list = field(default_factory=list)     # unnumbered, before the table of contents
    authors: list = field(default_factory=list)   # book.authors, in spine order
    listings: list = field(default_factory=list)
    figures: list = field(default_factory=list)
    tables: list = field(default_factory=list)
    refs: dict = field(default_factory=dict)      # kind -> label -> (text, anchor)
    warnings: list = field(default_factory=list)
    bib: dict = field(default_factory=dict)       # key -> bib.Entry
    cited: list = field(default_factory=list)     # cited keys, first-citation order

    def entries(self):
        yield from self.front
        for part in self.parts:
            yield from part.sections
        yield from self.back


def load_spine(path, errors):
    try:
        spine = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise BuildFailed([f"{path}: no se puede leer el spine: {error}"])
    if not isinstance(spine, dict) or not isinstance(spine.get("parts"), list):
        raise BuildFailed([f"{path}: el spine necesita una lista `parts`"])
    seen = set()

    def check(item, where):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            errors.append(f"{path}: {where}: falta `id`")
            return False
        if not re.fullmatch(SEC_LABEL, item["id"]):
            errors.append(f"{path}: id no válido: {item['id']}")
        if item["id"] in seen:
            errors.append(f"{path}: id repetido: {item['id']}")
        seen.add(item["id"])
        if not isinstance(item.get("title"), str):
            errors.append(f"{path}: {item['id']}: falta `title`")
            return False
        return True

    front = spine.get("front_matter") or []
    if not isinstance(front, list):
        errors.append(f"{path}: `front_matter` debe ser una lista")
        spine["front_matter"] = front = []
    for k, item in enumerate(front, 1):
        check(item, f"front_matter {k}")
    for n, part in enumerate(spine["parts"], 1):
        if check(part, f"parte {n}") and not isinstance(part.get("sections"), list):
            errors.append(f"{path}: {part['id']}: falta la lista `sections`")
            part["sections"] = []
        for k, section in enumerate(part.get("sections") or [], 1) if isinstance(part, dict) else []:
            check(section, f"parte {n}, sección {k}")
    back = spine.get("back_matter") or []
    if not isinstance(back, list):
        errors.append(f"{path}: `back_matter` debe ser una lista")
        spine["back_matter"] = back = []
    for k, item in enumerate(back, 1):
        check(item, f"back_matter {k}")
    if errors:
        raise BuildFailed(errors)
    return spine


def collect(spine_path, draft=False):
    """Load and number the book. Returns (book, errors)."""
    errors = []
    spine_path = Path(spine_path).resolve()
    spine = load_spine(spine_path, errors)
    root = spine_path.parent
    meta = spine.get("book") or {}
    commit = meta.get("pinned_commit")
    book = Book(root=root, spine_path=spine_path, spine=spine, title=str(meta.get("title", "")),
                commit=str(commit) if commit is not None else None, parts=[], back=[], draft=draft)
    authors = meta.get("authors") or []
    if isinstance(authors, str):
        authors = [authors]
    if not isinstance(authors, list) or not all(isinstance(a, str) and a.strip() for a in authors):
        errors.append(f"{spine_path.name}: book.authors debe ser una lista de nombres")
        authors = []
    book.authors = [a.strip() for a in authors]
    sections_dir = root / "sections"

    for item in spine.get("front_matter") or []:
        # Unnumbered: the heading and @sec: reference are the title itself.
        book.front.append(Entry(item["id"], item["title"], item, None, heading=item["title"],
                                ref=item["title"], anchor=f"sec-{item['id']}"))
    for n, part_spine in enumerate(spine["parts"], 1):
        part = Part(part_spine["id"], part_spine["title"], n, f"sec-{part_spine['id']}")
        book.parts.append(part)
        for k, section_spine in enumerate(part_spine["sections"], 1):
            number = f"{n}.{k}"
            entry = Entry(section_spine["id"], section_spine["title"], section_spine, part, number,
                          f"{number} {section_spine['title']}", f"sección {number}",
                          f"sec-{section_spine['id']}")
            part.sections.append(entry)
    letter = 0
    for item in spine.get("back_matter") or []:
        entry = Entry(item["id"], item["title"], item, None, anchor=f"sec-{item['id']}")
        if item["id"].startswith("appendix"):
            code = chr(ord("A") + letter)
            letter += 1
            title = LISTINGS_APPENDIX_TITLE if item["id"] == LISTINGS_APPENDIX \
                else APPENDIX_PREFIX_RE.sub("", item["title"])
            entry.title = title
            entry.number = code
            entry.heading = f"Apéndice {code}: {title}"
            entry.ref = f"apéndice {code}"
        else:
            entry.heading = entry.ref = item["title"]
        if item["id"] == LISTINGS_APPENDIX:
            entry.generated = "listings"
        elif item["id"] == SOURCES:
            entry.generated = "sources"
        elif item["id"] == REFERENCE:
            entry.generated = "reference"
        book.back.append(entry)

    # Files.
    known = {entry.id for entry in book.entries()}
    if sections_dir.is_dir():
        for path in sorted(sections_dir.glob("*.md")):
            if path.stem not in known:
                errors.append(f"{path}: no hay ninguna entrada «{path.stem}» en {spine_path.name}")
    for entry in book.entries():
        path = sections_dir / f"{entry.id}.md"
        if entry.generated:
            if path.exists():
                errors.append(f"{path}: «{entry.id}» lo genera el build; borra el fichero")
            continue
        if not path.exists() and entry.id in LATER_GENERATED:
            entry.placeholder = LATER_GENERATED[entry.id]
            book.warnings.append(f"{entry.id}: pendiente; {entry.placeholder}")
            continue
        if not path.exists():
            if draft:
                entry.placeholder = f"Sección pendiente: falta sections/{entry.id}.md."
                book.warnings.append(f"{entry.id}: falta sections/{entry.id}.md (marcador de borrador)")
            else:
                errors.append(f"{entry.id}: falta sections/{entry.id}.md")
            continue
        entry.path = path
        rel = path.relative_to(root)
        entry.blocks = parse_section(path.read_text(encoding="utf-8"), entry.id, rel, errors).blocks

    _number(book, errors)
    return book, errors


def _number(book, errors):
    refs = {"sec": {}, "lst": {}, "fig": {}, "tbl": {}}
    book.refs = refs

    def define(kind, label, text, anchor, where):
        if label in refs[kind]:
            errors.append(f"{where}: etiqueta repetida: {kind}:{label}")
            return False
        refs[kind][label] = (text, anchor)
        return True

    for part in book.parts:
        define("sec", part.id, f"parte {part.number}", part.anchor, book.spine_path.name)
    for entry in book.entries():
        define("sec", entry.id, entry.ref, entry.anchor, book.spine_path.name)
    for entry in book.entries():
        sub = subsub = unnumbered = 0
        for block in entry.blocks:
            where = f"{entry.path.relative_to(book.root) if entry.path else entry.id}:{getattr(block, 'line', 0)}"
            if isinstance(block, Heading):
                if block.level == 2 and entry.number:
                    sub, subsub = sub + 1, 0
                    block.number = f"{entry.number}.{sub}"
                elif block.level == 3 and entry.number:
                    if sub == 0:
                        errors.append(f"{where}: ### sin un ## anterior")
                    subsub += 1
                    block.number = f"{entry.number}.{sub}.{subsub}"
                unnumbered += 1
                suffix = block.number[len(entry.number) + 1:] if block.number else f"h{unnumbered}"
                block.anchor = f"sec-{block.label}" if block.label else f"sec-{entry.id}-{suffix}"
                if block.label:
                    text = f"sección {block.number}" if block.number else block.title
                    define("sec", block.label, text, block.anchor, where)
            elif isinstance(block, Listing):
                if define("lst", block.label, "", f"lst-{block.label}", where):
                    book.listings.append(block)
                    block.number = len(book.listings)
                    refs["lst"][block.label] = (f"listado {block.number}", f"lst-{block.label}")
            elif isinstance(block, Figure):
                if define("fig", block.label, "", f"fig-{block.label}", where):
                    book.figures.append(block)
                    block.number = len(book.figures)
                    refs["fig"][block.label] = (f"figura {block.number}", f"fig-{block.label}")
            elif isinstance(block, TableCaption):
                if define("tbl", block.label, "", f"tbl-{block.label}", where):
                    book.tables.append(block)
                    block.number = len(book.tables)
                    refs["tbl"][block.label] = (f"tabla {block.number}", f"tbl-{block.label}")


def resolve_refs(text, refs, where, errors, link=True):
    """Replace @kind:label outside inline code. ``link`` makes Markdown links."""

    def replace(match):
        if match.group("code"):
            return match.group("code")
        kind = match.group("kind").lower()
        label = match.group("label")
        target = refs.get(kind, {}).get(label)
        if target is None:
            errors.append(f"{where}: referencia sin resolver: @{kind}:{label}")
            return match.group(0)
        words, anchor = target
        if match.group("kind")[0].isupper():
            words = words[:1].upper() + words[1:]
        return f"[{words}](#{anchor})" if link else words

    return REF_RE.sub(replace, text)
