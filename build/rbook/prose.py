"""Split a section file into prose units and sentences, for the checks.

Prose is what the reader reads as running text. Not prose: fenced code and
listings, listing outputs, headings, tables and their captions, figures,
HTML comments (``<!-- covers: n -->`` anchors among them). Explanation
blocks are prose, but they are kept apart (kind ``explanation``) because
they move to Appendix A and do not count against the section's words.

A unit is one paragraph (``para``), one list item (``item``) or one
explanation block (``explanation``). Inside a unit, inline code, links,
cross-references and citations are masked before sentences are split, so a
period inside them never ends a sentence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .parse import EXPLANATION_CLOSE_RE, EXPLANATION_OPEN_RE, FENCE_RE, HEADING_LABEL_RE, HEADING_RE

COMMENT_RE = re.compile(r"<!--(?P<body>.*?)-->", re.S)
COVERS_RE = re.compile(r"^\s*covers\s*:\s*(?P<items>.*?)\s*$", re.S)
LIST_ITEM_RE = re.compile(r"^(?P<indent>\s*)(?:[-*+]|\d+[.)])\s+(?P<text>.*)$")
TABLE_LINE_RE = re.compile(r"^\s*\|")
TABLE_CAPTION_LINE_RE = re.compile(r"^:\s+.*\{#tbl:")
FIGURE_LINE_RE = re.compile(r"^!\[.*\]\(.*\)")
INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)+?\1")
LINK_RE = re.compile(r"!?\[(?P<text>[^\]]*)\]\([^)\s]*\)")
REF_TOKEN_RE = re.compile(r"(?<![\w@])@(?:[Ss]ec|[Ll]st|[Ff]ig|[Tt]bl):[A-Za-z0-9_-]+(?:[.:][A-Za-z0-9_-]+)*")
BRACKET_CITE_RE = re.compile(r"\[(?=[^\]]*@)[^\]]*\]")
CITE_TOKEN_RE = re.compile(r"(?<![\w@])@[A-Za-z0-9_](?:\w|[:.#$%&+?<>~/-](?=\w))*")
URL_RE = re.compile(r"\bhttps?://\S+")
EMPH_RE = re.compile(r"(\*\*|__|\*|_)(?=\S)(.+?)(?<=\S)\1")

# A word: letters or digits, with inner apostrophes, hyphens, periods or
# commas ("6.8", "1,5", "semi-naive").
WORD_RE = re.compile(r"[^\W_]+(?:[.,'’\-][^\W_]+)*")

# Abbreviations whose period does not end a sentence.
ABBREVIATIONS = ("p. ej.", "ej.", "etc.", "Sr.", "Sra.", "Dr.", "Dra.", "núm.", "pág.", "págs.",
                 "cap.", "caps.", "cf.", "vs.", "art.", "arts.", "aprox.", "fig.", "i. e.",
                 "e. g.", "sec.", "vol.", "ed.", "eds.", "et al.")
_ABBR_RE = re.compile(r"(?<![\w.])(?:" + "|".join(re.escape(a) for a in sorted(ABBREVIATIONS, key=len, reverse=True))
                      + r")")
# A sentence ends at . ! ? or … (possibly repeated), optionally followed by
# closing quotes or brackets, then space and a capital, ¿, ¡, a digit, an
# opening quote/bracket, a masked token, or the end of the unit.
SENTENCE_END_RE = re.compile(r"[.!?…]+[\"'”’»)\]]*(?=\s+[¿¡\"'“«(\[A-ZÁÉÍÓÚÜÑ0-9]|\s*$)")
MASK = ""   # stands for one masked token (code, reference, citation)


@dataclass
class Heading:
    level: int
    title: str
    line: int


@dataclass
class Unit:
    kind: str            # para | item | explanation
    line: int            # first line (1-based)
    text: str            # raw text, lines joined with "\n"
    after_heading: int = 0   # index into Doc.headings of the last heading before it (-1: none)


@dataclass
class ListingMark:
    lang: str
    kind: str | None
    line: int
    after_heading: int


@dataclass
class Doc:
    units: list = field(default_factory=list)
    headings: list = field(default_factory=list)
    listings: list = field(default_factory=list)
    anchors: list = field(default_factory=list)     # (value, line)
    comments: list = field(default_factory=list)    # (text, line), non-anchor comments


@dataclass
class Sentence:
    text: str            # masked text
    raw: str             # raw excerpt
    line: int


def read_doc(text):
    """Return the prose structure of one section file."""
    doc = Doc()
    lines = text.splitlines()
    current = None

    def end():
        nonlocal current
        if current is not None:
            current.text = "\n".join(current.text)
            if current.text.strip():
                doc.units.append(current)
        current = None

    def start(kind, n, first):
        nonlocal current
        end()
        current = Unit(kind, n + 1, [first], len(doc.headings) - 1)

    i = 0
    in_comment = None   # (start line, collected text)
    while i < len(lines):
        line = lines[i]
        if in_comment is not None:
            if "-->" in line:
                body, rest = line.split("-->", 1)
                _comment(doc, in_comment[1] + "\n" + body, in_comment[0])
                in_comment = None
                line = rest
                if not line.strip():
                    i += 1
                    continue
            else:
                in_comment = (in_comment[0], in_comment[1] + "\n" + line)
                i += 1
                continue
        fence = FENCE_RE.match(line)
        if fence:
            end()
            marker = fence.group("fence")
            close_re = re.compile(r"^ {0,3}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}\s*$")
            info = fence.group("info").strip()
            j = i + 1
            while j < len(lines) and not close_re.match(lines[j]):
                j += 1
            if "{" in info:
                lang = info[:info.index("{")].strip()
                run = re.search(r"\brun=(\S+?)(?=[\s}])", info)
                doc.listings.append(ListingMark(lang, run.group(1) if run else None, i + 1,
                                                len(doc.headings) - 1))
                k = j + 1
                while k < len(lines) and not lines[k].strip():
                    k += 1
                if k < len(lines) and EXPLANATION_OPEN_RE.match(lines[k]):
                    m = k + 1
                    while m < len(lines) and not EXPLANATION_CLOSE_RE.match(lines[m]):
                        m += 1
                    body = lines[k + 1:m]
                    unit = Unit("explanation", k + 2, "\n".join(body), len(doc.headings) - 1)
                    if unit.text.strip():
                        doc.units.append(unit)
                    i = m + 1
                    continue
            i = j + 1
            continue
        if EXPLANATION_OPEN_RE.match(line):   # stray; the parser reports it
            end()
            i += 1
            while i < len(lines) and not EXPLANATION_CLOSE_RE.match(lines[i]):
                i += 1
            i += 1
            continue
        # HTML comments: anchors and notes, never prose.
        if "<!--" in line:
            pieces, pos = [], 0
            for match in COMMENT_RE.finditer(line):
                pieces.append(line[pos:match.start()])
                _comment(doc, match.group("body"), i + 1)
                pos = match.end()
            rest = line[pos:]
            if "<!--" in rest:
                before, after = rest.split("<!--", 1)
                pieces.append(before)
                in_comment = (i + 1, after)
            else:
                pieces.append(rest)
            line = "".join(pieces)
            if not line.strip():
                i += 1
                continue
        heading = HEADING_RE.match(line)
        if heading:
            end()
            title = heading.group("title").rstrip("#").rstrip()
            label = HEADING_LABEL_RE.search(title)
            if label:
                title = title[:label.start()].rstrip()
            doc.headings.append(Heading(len(heading.group("hashes")), title, i + 1))
            i += 1
            continue
        if not line.strip() or TABLE_LINE_RE.match(line) or TABLE_CAPTION_LINE_RE.match(line) \
                or FIGURE_LINE_RE.match(line) or re.match(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", line):
            end()
            i += 1
            continue
        item = LIST_ITEM_RE.match(line)
        if item:
            start("item", i, item.group("text"))
            i += 1
            continue
        text = re.sub(r"^\s*>\s?", "", line)
        if current is None:
            start("para", i, text)
        else:
            current.text.append(text.strip() if current.kind == "item" else text)
        i += 1
    end()
    return doc


def _comment(doc, body, line):
    match = COVERS_RE.match(body)
    if match:
        for value in re.split(r"[,\s]+", match.group("items").strip()):
            if value:
                doc.anchors.append((value, line))
    else:
        doc.comments.append((body.strip(), line))


def mask(text):
    """Mask inline code, links' targets, references, citations and URLs."""
    text = INLINE_CODE_RE.sub(MASK, text)
    text = LINK_RE.sub(lambda m: m.group("text"), text)
    text = URL_RE.sub(MASK, text)
    text = BRACKET_CITE_RE.sub(MASK, text)
    text = REF_TOKEN_RE.sub(MASK, text)
    text = CITE_TOKEN_RE.sub(MASK, text)
    text = EMPH_RE.sub(lambda m: m.group(2), text)
    return text


def words(masked):
    """Words of a masked text; each masked token counts as one word."""
    return WORD_RE.findall(masked) + [MASK] * masked.count(MASK)


def sentences(unit):
    """Split a unit into sentences; line numbers point into the file."""
    masked = mask(unit.text)
    # Hide abbreviation periods so they cannot end a sentence.
    hidden = _ABBR_RE.sub(lambda m: m.group(0).replace(".", ""), masked)
    out, pos = [], 0
    for match in SENTENCE_END_RE.finditer(hidden):
        _add(out, hidden[pos:match.end()], masked, unit, pos)
        pos = match.end()
    _add(out, hidden[pos:], masked, unit, pos)
    return out


def _add(out, piece, masked, unit, offset):
    stripped = piece.strip()
    if not WORD_RE.search(stripped) and MASK not in stripped:
        return
    lead = len(piece) - len(piece.lstrip())
    start = offset + lead
    line = unit.line + masked[:start].count("\n")
    text = stripped.replace("", ".")
    out.append(Sentence(" ".join(text.split()), _excerpt(text), line))


def _excerpt(text, limit=90):
    text = " ".join(text.replace(MASK, "…").split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


def excerpt(text, limit=90):
    return _excerpt(mask(text), limit)
