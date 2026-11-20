"""Parse one section file into blocks: Markdown text, headings, listings,
figures and table captions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

RUN_KINDS = ("run", "query", "explain", "execute", "expect-error", "include", "none")
CLI_COMMANDS = ("run", "query", "explain", "execute")
LABEL = r"[A-Za-z0-9_-]+"
SEC_LABEL = r"[A-Za-z0-9_-]+(?:[.:][A-Za-z0-9_-]+)*"

FENCE_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})[ \t]+(?P<title>.*?)[ \t]*$")
HEADING_LABEL_RE = re.compile(r"\s*\{#sec:(?P<label>" + SEC_LABEL + r")\}\s*$")
FIGURE_RE = re.compile(r"^!\[(?P<caption>[^\]]*)\]\((?P<src>[^)\s]+)\)\{#fig:(?P<label>" + LABEL + r")\}\s*$")
TABLE_CAPTION_RE = re.compile(r"^:\s+(?P<caption>.*?)\s*\{#tbl:(?P<label>" + LABEL + r")\}\s*$")
EXPLANATION_OPEN_RE = re.compile(r"^:::\s*explanation\s*$")
EXPLANATION_CLOSE_RE = re.compile(r"^:::\s*$")
ATTR_TOKEN_RE = re.compile(
    r'\s*(?:#(?P<id>\S+)|(?P<key>[A-Za-z][\w-]*)=(?:"(?P<quoted>(?:[^"\\]|\\.)*)"|(?P<bare>[^\s"]+)))')
INCLUDE_RE = re.compile(
    r"^residuum@(?P<commit>[0-9a-fA-F]{4,40}):(?P<path>[^#\s]+)(?:#L(?P<start>\d+)(?:-L(?P<end>\d+))?)?$")


@dataclass
class Heading:
    level: int            # 2 = subsection, 3 = sub-subsection, 4+ unnumbered
    title: str
    label: str | None
    line: int
    number: str = ""
    anchor: str = ""


@dataclass
class Listing:
    label: str
    caption: str
    kind: str
    lang: str
    body: str
    explanation: str
    section_id: str
    path: str
    line: int
    setup: str | None = None
    cmd: str | None = None
    include: dict | None = None
    steps: int | None = None   # launcher --steps N (1..4096)
    trace: bool = False        # launcher --trace
    number: int = 0
    shown: str = ""          # the text shown in the book
    result: object = None    # runner.Result, set by the runner


@dataclass
class Figure:
    label: str
    caption: str
    src: str
    line: int
    number: int = 0


@dataclass
class TableCaption:
    label: str
    caption: str
    line: int
    number: int = 0


@dataclass
class Parsed:
    blocks: list = field(default_factory=list)   # str | Heading | Listing | Figure | TableCaption


def parse_attrs(text):
    """Parse ``#lst:x key=value key="quoted"``; return (id, dict) or raise ValueError."""
    ident, attrs, pos = None, {}, 0
    text = text.strip()
    while pos < len(text):
        match = ATTR_TOKEN_RE.match(text, pos)
        if not match or match.end() == pos:
            raise ValueError(f"atributo no válido cerca de «{text[pos:].strip()}»")
        if match.group("id"):
            if ident is not None:
                raise ValueError("más de un identificador #...")
            ident = match.group("id")
        else:
            key = match.group("key")
            if key in attrs:
                raise ValueError(f"atributo repetido: {key}")
            value = match.group("quoted")
            if value is not None:
                value = re.sub(r"\\(.)", r"\1", value)
            else:
                value = match.group("bare")
            attrs[key] = value
        pos = match.end()
    return ident, attrs


def parse_section(text, section_id, path, errors):
    """Split a section file into blocks. Problems are appended to ``errors``."""
    lines = text.splitlines()
    parsed = Parsed()
    buffer = []

    def where(n):
        return f"{path}:{n + 1}"

    def flush():
        if buffer:
            parsed.blocks.append("\n".join(buffer) + "\n")
            buffer.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group("fence")
            close_re = re.compile(r"^ {0,3}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}\s*$")
            j = i + 1
            while j < len(lines) and not close_re.match(lines[j]):
                j += 1
            if j >= len(lines):
                errors.append(f"{where(i)}: bloque de código sin cerrar")
                break
            info = fence.group("info").strip()
            body = "\n".join(lines[i + 1:j])
            if "{" in info:
                listing, i = _listing(info, body, lines, i, j, section_id, path, errors)
                if listing:
                    flush()
                    parsed.blocks.append(listing)
                continue
            if info.split()[:1] == ["res"]:
                errors.append(f"{where(i)}: bloque res sin etiqueta; un listado necesita "
                              "{#lst:etiqueta caption=\"...\" run=...}")
            buffer.extend(lines[i:j + 1])
            i = j + 1
            continue
        if EXPLANATION_OPEN_RE.match(line):
            errors.append(f"{where(i)}: bloque ::: explanation que no sigue a un listado")
            i += 1
            while i < len(lines) and not EXPLANATION_CLOSE_RE.match(lines[i]):
                i += 1
            i += 1
            continue
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group("hashes"))
            title = heading.group("title").rstrip("#").rstrip()
            label = None
            match = HEADING_LABEL_RE.search(title)
            if match:
                label = match.group("label")
                title = title[:match.start()].rstrip()
            if level == 1:
                errors.append(f"{where(i)}: el título de nivel 1 lo pone spine.yaml; "
                              "usa ## para las subsecciones")
            else:
                flush()
                parsed.blocks.append(Heading(level, title, label, i + 1))
            i += 1
            continue
        figure = FIGURE_RE.match(line)
        if figure:
            if not figure.group("caption").strip():
                errors.append(f"{where(i)}: la figura {figure.group('label')} no tiene pie (texto alternativo)")
            flush()
            parsed.blocks.append(Figure(figure.group("label"), figure.group("caption").strip(),
                                        figure.group("src"), i + 1))
            i += 1
            continue
        table = TABLE_CAPTION_RE.match(line)
        if table:
            if not table.group("caption"):
                errors.append(f"{where(i)}: la tabla {table.group('label')} no tiene pie")
            flush()
            parsed.blocks.append(TableCaption(table.group("label"), table.group("caption"), i + 1))
            i += 1
            continue
        if "{#fig:" in line or "{#tbl:" in line:
            errors.append(f"{where(i)}: etiqueta de figura o tabla mal formada")
        buffer.append(line)
        i += 1
    flush()
    return parsed


def _listing(info, body, lines, start, close, section_id, path, errors):
    """Parse a labelled fence at lines[start..close]; return (Listing|None, next line)."""
    where = f"{path}:{start + 1}"
    brace = info.index("{")
    lang = info[:brace].strip()
    if not info.endswith("}"):
        errors.append(f"{where}: los atributos del listado deben acabar en }}")
        return None, close + 1
    try:
        ident, attrs = parse_attrs(info[brace + 1:-1])
    except ValueError as error:
        errors.append(f"{where}: {error}")
        return None, close + 1
    nxt = close + 1
    # The explanation block must follow, after optional blank lines.
    k = nxt
    while k < len(lines) and not lines[k].strip():
        k += 1
    explanation = None
    if k < len(lines) and EXPLANATION_OPEN_RE.match(lines[k]):
        m = k + 1
        while m < len(lines) and not EXPLANATION_CLOSE_RE.match(lines[m]):
            m += 1
        if m >= len(lines):
            errors.append(f"{path}:{k + 1}: bloque ::: explanation sin cerrar")
            return None, len(lines)
        explanation = "\n".join(lines[k + 1:m]).strip()
        nxt = m + 1
    if not ident or not ident.startswith("lst:") or not re.fullmatch(LABEL, ident[4:]):
        errors.append(f"{where}: el listado necesita una etiqueta #lst:<etiqueta> "
                      "(letras, dígitos, _ o -)")
        return None, nxt
    label = ident[4:]
    problems = []
    caption = attrs.pop("caption", None)
    kind = attrs.pop("run", None)
    if not caption or not caption.strip():
        problems.append("falta caption")
    if kind is None:
        problems.append("falta run=<tipo>")
    elif kind not in RUN_KINDS:
        problems.append(f"run={kind} no es un tipo válido ({', '.join(RUN_KINDS)})")
    if not explanation:
        problems.append("falta el bloque ::: explanation (o está vacío)")
    setup = attrs.pop("setup", None)
    cmd = attrs.pop("cmd", None)
    include_spec = attrs.pop("include", None)
    steps_spec = attrs.pop("steps", None)
    trace_spec = attrs.pop("trace", None)
    for key in attrs:
        problems.append(f"atributo desconocido: {key}")
    if setup is not None:
        if kind not in CLI_COMMANDS + ("expect-error",):
            problems.append("setup= solo vale para listados que se ejecutan")
        elif not re.fullmatch(LABEL, setup):
            problems.append(f"setup={setup}: nombre no válido")
    if cmd is not None:
        if kind != "expect-error":
            problems.append("cmd= solo vale para run=expect-error")
        elif cmd not in CLI_COMMANDS:
            problems.append(f"cmd={cmd} no es una orden de Residuum ({', '.join(CLI_COMMANDS)})")
    steps, trace = None, False
    if steps_spec is not None or trace_spec is not None:
        if kind not in CLI_COMMANDS + ("expect-error",):
            problems.append("steps= y trace= solo valen para listados que se ejecutan")
    if steps_spec is not None:
        if not (steps_spec.isascii() and steps_spec.isdecimal() and 1 <= int(steps_spec) <= 4096):
            problems.append(f"steps={steps_spec}: se espera un entero entre 1 y 4096")
        else:
            steps = int(steps_spec)
    if trace_spec is not None:
        if trace_spec not in ("true", "false"):
            problems.append(f"trace={trace_spec}: se espera true o false")
        trace = trace_spec == "true"
    include = None
    if kind == "include":
        if include_spec is None:
            problems.append("run=include necesita include=residuum@<commit>:<ruta>[#La-Lb]")
        else:
            match = INCLUDE_RE.match(include_spec)
            if not match:
                problems.append(f"include={include_spec}: forma no válida; "
                                "se espera residuum@<commit>:<ruta>[#La-Lb]")
            else:
                include = dict(spec=include_spec, commit=match.group("commit"), path=match.group("path"),
                               start=int(match.group("start")) if match.group("start") else None,
                               end=int(match.group("end")) if match.group("end") else None)
                if include["end"] is None and include["start"] is not None:
                    include["end"] = include["start"]
        if body.strip():
            problems.append("un listado include no lleva cuerpo; el texto se copia del repositorio")
    elif include_spec is not None:
        problems.append("include= solo vale con run=include")
    if problems:
        errors.append(f"{where}: listado {label}: " + "; ".join(problems))
        return None, nxt
    return Listing(label=label, caption=caption.strip(), kind=kind, lang=lang, body=body,
                   explanation=explanation, section_id=section_id, path=str(path), line=start + 1,
                   setup=setup, cmd=cmd, include=include, steps=steps, trace=trace), nxt
