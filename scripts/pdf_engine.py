"""PDF -> sections. Digital pages use the embedded text layer; scanned pages are OCR'd."""
from __future__ import annotations

from pathlib import Path

from md_utils import tidy
from ocr_engine import png_bytes_to_text

MIN_TEXT_CHARS = 40  # a text layer shorter than this => treat the page as scanned


def pymupdf():
    """Import PyMuPDF under its new name, falling back to the legacy `fitz`."""
    try:
        import pymupdf
        return pymupdf
    except ImportError:
        import fitz
        return fitz


def pdf_title(path: Path) -> str:
    try:
        fitz = pymupdf()
        doc = fitz.open(str(path))
        title = ((doc.metadata or {}).get("title") or "").strip()
        doc.close()
        return title if 0 < len(title) < 150 else ""
    except Exception:
        return ""


def _page_image_refs(doc, page, sink, seen: set) -> list[str]:
    """First-occurrence refs for the page's embedded images (xref-deduped)."""
    refs: list[str] = []
    try:
        infos = page.get_images(full=True)
    except Exception:
        return refs
    for info in infos:
        xref = info[0]
        if xref in seen:
            continue
        try:
            extracted = doc.extract_image(xref)
        except Exception:
            seen.add(xref)
            continue
        seen.add(xref)
        if extracted.get("width", 0) * extracted.get("height", 0) < 1024:
            continue  # tiny decorations / spacers
        refs.append(f"![]({sink.save(extracted['image'], extracted.get('ext', 'png'))})")
    return refs


def convert_pdf(path: Path, *, start: int = 1, end: int | None = None, dpi: int = 300,
                lang: str = "eng", mode: str = "auto", tess=None,
                extra_args: list[str] | None = None, log=print,
                progress_every: int = 25, sink=None):
    """Return (sections, stats). sections: list[(heading, body)] with heading = 'Page N'."""
    extra_args = extra_args or []
    fitz = pymupdf()
    doc = fitz.open(str(path))
    if doc.needs_pass:
        raise RuntimeError("the PDF is password-protected")
    total = doc.page_count
    start = max(1, start)
    end = min(end or total, total)
    if start > end:
        raise RuntimeError(f"page range {start}-{end} is empty (PDF has {total} pages)")

    n = end - start + 1
    digital = ocr = 0
    failures: list[tuple[int, str]] = []
    sections: list[tuple[str, str]] = []
    seen_images: set[int] = set()
    for i, pno in enumerate(range(start - 1, end), 1):
        pnum = pno + 1
        try:
            page = doc.load_page(pno)
            text, used = "", "digital"
            if mode in ("auto", "digital"):
                text = page.get_text("text").strip()
            if mode == "ocr" or (mode == "auto" and len(text) < MIN_TEXT_CHARS):
                if tess is None:
                    raise RuntimeError("Tesseract not found (needed for scanned pages)")
                pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
                text = png_bytes_to_text(pix.tobytes("png"), tess, lang, extra_args)
                used = "ocr"
            if used == "ocr":
                ocr += 1
            else:
                digital += 1
            body = tidy(text)
            if sink is not None:
                refs = _page_image_refs(doc, page, sink, seen_images)
                if refs:
                    joined = "\n\n".join(refs)
                    body = f"{body}\n\n{joined}" if body else joined
            sections.append((f"Page {pnum}", body))
        except Exception as e:
            failures.append((pnum, str(e)))
            sections.append((f"Page {pnum}", ""))
            log(f"  page {pnum}: FAILED ({e})")
        if i % progress_every == 0 and i != n:
            log(f"  page {pnum}/{end} ... ({digital} digital, {ocr} OCR so far)")
    doc.close()

    stats = {
        "detail": f"{n} pages; digital text layer + Tesseract OCR for scanned pages",
        "failures": failures,
    }
    return sections, stats
