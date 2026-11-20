"""Fold-and-staple (saddle-stitch) imposition of the book PDF.

Ported from ``~/hanskellsen_docs/build_booklet.py`` (``spread`` and
``impose``), without its ``bookcfg`` and Chrome dependencies. One change:
that script keeps the last page as the back cover and pads before it; this
book has no back cover, so blank pages are added at the end.

Each sheet has two sides; each side holds two pages, left and right. Sheet
``i`` (0-based) of an ``n``-page booklet carries pages ``n-1-2i | 2i`` on the
front and ``2i+1 | n-2-2i`` on the back. Print double-sided, flip on the
short edge, fold, and staple through the centre.

The booklet keeps the source's metadata, with BOOKLET_SUFFIX added to the
title, so that nobody takes it for the reading edition (``residuum.pdf``).
"""

from __future__ import annotations

from pathlib import Path

BOOKLET_SUFFIX = " (folleto para imprimir)"


def padded_count(pages):
    return pages + (-pages) % 4


def booklet_order(pages):
    """Sides of the imposed booklet as (left, right) 0-based page indices.

    ``None`` is a blank page added to reach a multiple of 4.
    """
    if pages < 1:
        raise ValueError("el PDF no tiene páginas")
    n = padded_count(pages)

    def page(index):
        return index if index < pages else None

    sides = []
    for i in range(n // 4):
        sides.append((page(n - 1 - 2 * i), page(2 * i)))
        sides.append((page(2 * i + 1), page(n - 2 - 2 * i)))
    return sides


def impose_pdf(source, dest):
    """Write the booklet of PDF ``source`` to ``dest``; return (sides, pages)."""
    from pypdf import PageObject, PdfReader, PdfWriter, Transformation

    reader = PdfReader(str(source))
    pages = list(reader.pages)
    src_w = float(pages[0].mediabox.width)
    src_h = float(pages[0].mediabox.height)
    sheet_w, sheet_h = src_w * 2.0, src_h
    half = sheet_w / 2.0

    def place(sheet, src, x):
        sw, sh = float(src.mediabox.width), float(src.mediabox.height)
        scale = min(half / sw, sheet_h / sh)
        tx = x + (half - sw * scale) / 2.0
        ty = (sheet_h - sh * scale) / 2.0
        sheet.merge_transformed_page(src, Transformation().scale(scale, scale).translate(tx, ty))

    writer = PdfWriter()
    order = booklet_order(len(pages))
    for left, right in order:
        sheet = PageObject.create_blank_page(width=sheet_w, height=sheet_h)
        if left is not None:
            place(sheet, pages[left], 0.0)
        if right is not None:
            place(sheet, pages[right], half)
        writer.add_page(sheet)
    metadata = {k: v for k, v in (reader.metadata or {}).items() if isinstance(v, str)}
    title = metadata.get("/Title") or Path(source).stem
    metadata["/Title"] = f"{title}{BOOKLET_SUFFIX}"
    writer.add_metadata(metadata)
    with open(dest, "wb") as handle:
        writer.write(handle)
    return len(order), len(pages)
