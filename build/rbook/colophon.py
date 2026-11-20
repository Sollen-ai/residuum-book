"""The colophon: front matter after the title page, in Spanish.

Everything in it is deterministic for a given checkout and environment
except the build date, which is today's date (UTC) or, when set,
``SOURCE_DATE_EPOCH``.
"""

from __future__ import annotations

import datetime
import os
import platform
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

from . import gitinfo

TOOL_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Colophon:
    title: str
    commit: str            # as written in the spine
    full_commit: str       # full sha, or "" when the repository cannot be read
    commit_date: str       # ISO date, or ""
    tool: str              # the build tool's git state
    python: str
    weasyprint: str
    pypdf: str
    date: str              # YYYY-MM-DD
    draft: bool
    authors: tuple = ()    # book.authors
    edition: str = ""      # book.edition
    license: str = ""      # book.license
    license_url: str = ""  # book.license_url
    source: str = ""       # book.source

    def lines(self):
        """(label, value) rows, in display order."""
        if self.full_commit:
            residuum = f"commit {self.full_commit}, del {self.commit_date}"
        elif self.commit:
            residuum = f"commit {self.commit} (no se encontró en el repositorio)"
        else:
            residuum = "sin commit fijado"
        authors = [("Autores" if len(self.authors) > 1 else "Autor", ", ".join(self.authors))] \
            if self.authors else []
        edition = [("Edición", self.edition)] if self.edition else []
        if self.license:
            text = self.license + (f" ({self.license_url})" if self.license_url else "")
            text += (". Los fragmentos citados del repositorio de Residuum, incluida su referencia"
                     " del lenguaje, conservan la licencia MIT de ese repositorio.")
            edition.append(("Licencia", text))
        if self.source:
            edition.append(("Fuentes del libro", self.source))
        return authors + edition + [
            ("Residuum", residuum),
            ("Herramienta de build", f"rbook, {self.tool}"),
            ("Python", self.python),
            ("WeasyPrint", self.weasyprint),
            ("pypdf", self.pypdf),
            ("Fecha del build", self.date),
            ("Modo", "borrador (--draft)" if self.draft else "final"),
        ]


def _version(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "no instalado en este Python"


def build_date():
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.strip().isdigit():
        moment = datetime.datetime.fromtimestamp(int(epoch), datetime.timezone.utc)
    else:
        moment = datetime.datetime.now(datetime.timezone.utc)
    return moment.date().isoformat()


def make_colophon(book, residuum, tool_root=TOOL_ROOT):
    full = date = ""
    if book.commit:
        try:
            full, iso = gitinfo.commit_info(residuum, book.commit)
            date = iso[:10]
        except gitinfo.GitError:
            pass
    return Colophon(title=book.title, commit=book.commit or "", full_commit=full, commit_date=date,
                    tool=gitinfo.tool_state(tool_root), python=platform.python_version(),
                    weasyprint=_version("weasyprint"), pypdf=_version("pypdf"), date=build_date(),
                    draft=book.draft, authors=tuple(book.authors), edition=book.edition,
                    license=book.license, license_url=book.license_url, source=book.source)
