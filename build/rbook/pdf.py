"""PDF output with WeasyPrint (installed in ``.venv/``; see build/README.md).

The print stylesheet lives in the HTML page itself (``render.PRINT_CSS``),
so the PDF is the HTML book laid out on A5 pages.
"""

from __future__ import annotations


class PdfUnavailable(Exception):
    pass


def require():
    """Import WeasyPrint and pypdf, or explain in Spanish how to get them."""
    try:
        import weasyprint  # noqa: F401
        import pypdf  # noqa: F401
    except ImportError as error:
        raise PdfUnavailable(
            f"falta {error.name}: el PDF y el folleto necesitan el entorno virtual. Créalo con\n"
            "  python3 -m venv .venv && .venv/bin/pip install -r build/requirements.txt\n"
            "y vuelve a ejecutar ./book build --pdf (./book usa .venv/bin/python por sí solo).")


def write_pdf(page, base_url, dest):
    """Render the HTML text ``page`` to ``dest``; return the page count.

    Title, author and language come from the page's ``<title>``,
    ``<meta name="author">`` and ``<html lang>``; the outline (bookmarks)
    from the ``bookmark-level`` rules of ``render.PRINT_CSS``. The PDF is
    tagged (``pdf_tags``: a structure tree for screen readers).
    """
    import logging

    import weasyprint

    # WeasyPrint logs every unsupported CSS property of the screen styles.
    logging.getLogger("weasyprint").setLevel(logging.ERROR)
    document = weasyprint.HTML(string=page, base_url=str(base_url)).render(pdf_tags=True)
    document.write_pdf(str(dest), pdf_tags=True)
    return len(document.pages)
