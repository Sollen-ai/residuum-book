"""A minimal BibTeX reader and the citation syntax.

Reads ``@type{key, field = {value} | "value" | bare, ...}`` entries.
Lines starting with ``%`` are comments. ``@comment``, ``@preamble`` and
``@string`` blocks are skipped (``@string``
macros are not expanded), and so is any text outside an entry. Braces
inside values are kept balanced and then removed; ``\\&``-style escapes lose
their backslash. Nothing else of LaTeX is interpreted.

Names in ``author`` and ``editor`` are split at ``and`` outside braces. A
name wrapped whole in braces, as in ``author = {{Court of Appeals of New
York}}``, is a corporate name: it is shown whole, never shortened to its
last word.

Citations follow Pandoc: ``[@key]``, ``[@a; @b, p. 3]`` and bare ``@key``.
``@sec:``, ``@lst:``, ``@fig:`` and ``@tbl:`` are cross-references, not
citations.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

SKIPPED = {"comment", "preamble", "string"}
KEY_CHARS = r"[A-Za-z0-9_](?:\w|[:.#$%&+?<>~/-](?=\w))*"
CITE_RE = re.compile(r"(?P<code>`+[^`\n]*?`+)"
                     r"|\[(?P<group>[^\[\]\n]*@[^\[\]\n]*)\]"
                     r"|(?<![\w@])@(?P<key>" + KEY_CHARS + ")")
GROUP_ITEM_RE = re.compile(r"^\s*(?P<prefix>[^@]*?)\s*-?@(?P<key>" + KEY_CHARS + r")\s*(?:,\s*(?P<locator>.*?))?\s*$")
REF_PREFIX_RE = re.compile(r"^(?:sec|lst|fig|tbl):", re.IGNORECASE)


@dataclass
class Entry:
    type: str
    key: str
    fields: dict = field(default_factory=dict)
    line: int = 0
    raw: dict = field(default_factory=dict)      # field values before _clean (braces kept)


class BibError(Exception):
    pass


def read_bib(text):
    """Return {key: Entry}; raise BibError on malformed input."""
    # Lines starting with % are comments (as biber reads them); blank them
    # so line numbers stay right.
    text = "\n".join("" if line.lstrip().startswith("%") else line for line in text.split("\n"))
    entries, pos = {}, 0
    while True:
        at = text.find("@", pos)
        if at < 0:
            return entries
        line = text.count("\n", 0, at) + 1
        match = re.compile(r"@\s*(\w+)\s*([{(])").match(text, at)
        if not match:
            pos = at + 1
            continue
        kind = match.group(1).lower()
        close = "}" if match.group(2) == "{" else ")"
        body_start = match.end()
        end = _matching(text, body_start - 1, match.group(2), close)
        if end is None:
            raise BibError(f"línea {line}: entrada @{kind} sin cerrar")
        pos = end + 1
        if kind in SKIPPED:
            continue
        body = text[body_start:end]
        key, _, rest = body.partition(",")
        key = key.strip()
        if not key or not re.fullmatch(r"[^\s,{}()\"]+", key):
            raise BibError(f"línea {line}: entrada @{kind} sin clave válida")
        if key in entries:
            raise BibError(f"línea {line}: clave repetida: {key}")
        fields, raw = _fields(rest, line)
        entries[key] = Entry(kind, key, fields, line, raw)


def _matching(text, start, open_char, close_char):
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == open_char or (ch == "{" and open_char == "("):
            depth += 1
        elif ch == close_char or (ch == "}" and open_char == "("):
            depth -= 1
            if depth == 0:
                return i
    return None


def _fields(text, line):
    fields, raw, i, n = {}, {}, 0, len(text)
    while i < n:
        match = re.compile(r"\s*,?\s*([A-Za-z][\w-]*)\s*=\s*").match(text, i)
        if not match:
            if text[i:].strip(" \t\r\n,"):
                raise BibError(f"línea {line}: campo no válido cerca de «{text[i:i + 30].strip()}»")
            break
        name = match.group(1).lower()
        i = match.end()
        if i < n and text[i] == "{":
            end = _matching(text, i, "{", "}")
            if end is None:
                raise BibError(f"línea {line}: campo {name} sin cerrar")
            value, i = text[i + 1:end], end + 1
        elif i < n and text[i] == '"':
            end = i + 1
            depth = 0
            while end < n and not (text[end] == '"' and depth == 0):
                depth += {"{": 1, "}": -1}.get(text[end], 0)
                end += 1
            if end >= n:
                raise BibError(f"línea {line}: campo {name} sin cerrar")
            value, i = text[i + 1:end], end + 1
        else:
            bare = re.compile(r"[^,\s]*").match(text, i)
            value, i = bare.group(0), bare.end()
        fields[name] = _clean(value)
        raw[name] = value
    return fields, raw


def _clean(value):
    value = re.sub(r"\\([&%$#_{}])", r"\1", value)
    value = value.replace("{", "").replace("}", "").replace("~", " ").replace("--", "–")
    return " ".join(value.split())


def cited_keys(text):
    """Yield (key, offset) for each citation outside inline code."""
    for match in CITE_RE.finditer(text):
        if match.group("code"):
            continue
        if match.group("group") is not None:
            for item in match.group("group").split(";"):
                parsed = GROUP_ITEM_RE.match(item)
                if parsed and not REF_PREFIX_RE.match(parsed.group("key")):
                    yield parsed.group("key"), match.start()
        elif not REF_PREFIX_RE.match(match.group("key")):
            yield match.group("key"), match.start()


# Rendering ---------------------------------------------------------------

def split_names(value):
    """Split a raw author list at ``and`` outside braces.

    Returns (name, corporate) pairs; ``name`` is cleaned, ``corporate`` is
    true for a name wrapped whole in braces.
    """
    pieces, depth, start = [], 0, 0
    for match in re.finditer(r"[{}]|\s+and\s+", value):
        token = match.group(0)
        if token == "{":
            depth += 1
        elif token == "}":
            depth -= 1
        elif depth == 0:
            pieces.append(value[start:match.start()])
            start = match.end()
    pieces.append(value[start:])
    out = []
    for piece in (p.strip() for p in pieces):
        if not piece:
            continue
        corporate = piece.startswith("{") and _matching(piece, 0, "{", "}") == len(piece) - 1
        out.append((_clean(piece), corporate))
    return out


def full_names(entry):
    """The author (or editor) names, whole, in order."""
    name = "author" if entry.raw.get("author") else "editor"
    return [n for n, _ in split_names(entry.raw.get(name) or "")]


def _names(entry):
    name = "author" if entry.raw.get("author") else "editor"
    names = split_names(entry.raw.get(name) or "")
    return [n if corporate else n.split(",")[0].strip() if "," in n else n.split()[-1]
            for n, corporate in names]


def short_author(entry):
    names = _names(entry)
    if not names:
        return entry.fields.get("title", entry.key)
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} y {names[1]}"
    return f"{names[0]} et al."


def year(entry):
    return entry.fields.get("year", "s. f.")


def resolve_cites(text, bib, link=True):
    """Replace citations of known keys; unknown keys are left as they are
    (the citation check reports them)."""

    def item_text(key, locator, in_text):
        entry = bib[key]
        words = f"{short_author(entry)} ({year(entry)}" if in_text else f"{short_author(entry)}, {year(entry)}"
        if locator:
            words += f", {locator}"
        if in_text:
            words += ")"
        return f"[{words}](#ref-{key})" if link else words

    def replace(match):
        if match.group("code"):
            return match.group("code")
        if match.group("group") is not None:
            items = []
            for item in match.group("group").split(";"):
                parsed = GROUP_ITEM_RE.match(item)
                if not parsed or parsed.group("key") not in bib:
                    return match.group(0)
                prefix = parsed.group("prefix")
                piece = item_text(parsed.group("key"), parsed.group("locator"), False)
                items.append(f"{prefix} {piece}" if prefix else piece)
            return "(" + "; ".join(items) + ")"
        key = match.group("key")
        if REF_PREFIX_RE.match(key) or key not in bib:
            return match.group(0)
        return item_text(key, None, True)

    return CITE_RE.sub(replace, text)


def render_sources(bib, keys):
    """HTML list of the cited entries, sorted by author and year."""
    if not keys:
        return "<p>No hay fuentes citadas.</p>"
    entries = sorted((bib[k] for k in keys), key=lambda e: (short_author(e).lower(), year(e), e.key))
    out = ['<ul class="sources">']
    for entry in entries:
        f = entry.fields
        authors = "; ".join(full_names(entry))
        parts = []
        if authors:
            parts.append(html.escape(authors))
        parts.append(f"({html.escape(year(entry))}).")
        if f.get("title"):
            parts.append(f"<i>{html.escape(f['title'])}</i>.")
        venue = f.get("journal") or f.get("booktitle") or f.get("publisher") or f.get("institution") \
            or f.get("howpublished") or ""
        if venue:
            extra = ", ".join(x for x in (venue, f.get("volume", ""), f.get("pages", "")) if x)
            parts.append(html.escape(extra) + ".")
        if f.get("doi"):
            parts.append(f'<a href="https://doi.org/{html.escape(f["doi"])}">doi:{html.escape(f["doi"])}</a>')
        elif f.get("url"):
            parts.append(f'<a href="{html.escape(f["url"])}">{html.escape(f["url"])}</a>')
        out.append(f'<li id="ref-{html.escape(entry.key)}">{" ".join(parts)}</li>')
    out.append("</ul>")
    return "\n".join(out)
