#!/usr/bin/env python3
"""document_to_markdown.py - convert documents of many formats into Markdown, fully offline.

Supported (auto-detected by extension):
    .pdf                 digital text layer + Tesseract OCR for scanned pages
    .docx                Word (mammoth)      .pptx  PowerPoint (python-pptx)
    .xlsx / .xlsm        Excel (openpyxl)    .epub  e-books (ebooklib)
    .html/.htm/.xhtml    web pages           .csv/.tsv  delimiter tables
    .png .jpg .jpeg .webp .bmp .tif .tiff    images -> OCR (Tesseract)
    .txt / .log / .md    plain text          .json/.xml/.yaml  fenced code blocks
    .rtf .odt .ods .odp                      via pandoc, if installed
    .doc .xls .ppt                           via LibreOffice (soffice), if installed

First run (creates .venv next to this skill and installs the Python deps):
    python scripts/document_to_markdown.py --setup
Then run with the venv python:
    .venv/Scripts/python scripts/document_to_markdown.py book.pdf     (Windows)
    .venv/bin/python     scripts/document_to_markdown.py book.pdf     (macOS/Linux)

Every output is one .md file; paginated inputs (PDF/PPTX) get "## Page N" / "## Slide N"
sections, spreadsheets get "## Sheet: name" sections, everything else keeps its own
heading structure. See --help for all options.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import misc_engine
import office_engine
import pdf_engine
import web_engine
from ocr_engine import ensure_langs, find_tesseract, tesseract_version

SKILL_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = SKILL_DIR / ".venv"
IS_WIN = os.name == "nt"
VENV_PY = VENV_DIR / ("Scripts/python.exe" if IS_WIN else "bin/python")

DEPS = ["pymupdf", "mammoth", "markdownify", "beautifulsoup4",
        "python-pptx", "openpyxl", "ebooklib", "pillow"]
DEP_MODULES = {"pymupdf": "pymupdf", "mammoth": "mammoth", "markdownify": "markdownify",
               "beautifulsoup4": "bs4", "python-pptx": "pptx", "openpyxl": "openpyxl",
               "ebooklib": "ebooklib", "pillow": "PIL"}

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
TEXT_EXTS = {".txt", ".log", ".rst"}
MD_EXTS = {".md", ".markdown"}
CSV_EXTS = {".csv", ".tsv"}
FENCE_EXTS = {".json": "json", ".xml": "xml", ".yaml": "yaml", ".yml": "yaml"}
MODERN_EXTS = ({".pdf", ".docx", ".pptx", ".xlsx", ".xlsm", ".html", ".htm", ".xhtml", ".epub"}
               | IMAGE_EXTS | TEXT_EXTS | MD_EXTS | CSV_EXTS | set(FENCE_EXTS))
SUPPORTED_EXTS = MODERN_EXTS | misc_engine.RTF_ODF_EXTS | set(misc_engine.BINARY_OFFICE_EXTS)


# ------------------------------------------------------------------ env setup

def find_system_python() -> list[str] | None:
    if IS_WIN:
        py = shutil.which("py")
        if py:
            return [py, "-3"]
    for name in ("python3", "python"):
        p = shutil.which(name)
        if p:
            return [p]
    return None


def missing_deps() -> list[str]:
    missing = []
    for pkg, module in DEP_MODULES.items():
        if pkg == "pymupdf" and (importlib.util.find_spec("pymupdf")
                                 or importlib.util.find_spec("fitz")):
            continue
        if importlib.util.find_spec(module) is None:
            missing.append(pkg)
    return missing


def cmd_setup() -> int:
    print(f"skill dir : {SKILL_DIR}")

    if not VENV_PY.exists():
        base = find_system_python()
        if not base:
            print("ERROR: no system Python found. Install Python 3.9+ first:\n"
                  "  Windows: winget install Python.Python.3.12\n"
                  "  or https://www.python.org/downloads/", file=sys.stderr)
            return 1
        print(f"creating venv: {VENV_DIR}")
        r = subprocess.run(base + ["-m", "venv", str(VENV_DIR)], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"ERROR: venv creation failed:\n{r.stderr.strip()[-1000:]}", file=sys.stderr)
            return 1

    probe = ("import pymupdf, mammoth, markdownify, bs4, pptx, openpyxl, ebooklib, PIL; "
             "print('deps ok')")
    r = subprocess.run([str(VENV_PY), "-c", probe], capture_output=True, text=True)
    if r.returncode == 0:
        print(f"venv      : ok ({VENV_DIR})")
        print("deps      : all installed")
    else:
        print(f"installing dependencies: {', '.join(DEPS)} ...")
        r = subprocess.run([str(VENV_PY), "-m", "pip", "install",
                            "--disable-pip-version-check", "-q", *DEPS],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"ERROR: pip install failed:\n{r.stderr.strip()[-1000:]}", file=sys.stderr)
            return 1
        r = subprocess.run([str(VENV_PY), "-c", probe], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"ERROR: dependencies still not importable:\n{r.stderr.strip()[-500:]}",
                  file=sys.stderr)
            return 1
        print("deps      : installed")

    tess = find_tesseract()
    if tess:
        print(f"tesseract : {tess}")
        print(f"            {tesseract_version(tess)}")
    else:
        print("tesseract : NOT FOUND - OCR (scanned PDFs, images) will not work.")
        print("            Windows: winget install --id UB-Mannheim.TesseractOCR -e")
        print("            macOS  : brew install tesseract")
        print("            Linux  : apt install tesseract-ocr")

    pandoc = misc_engine.find_pandoc()
    if pandoc:
        print(f"pandoc    : {pandoc}  (enables .rtf/.odt/.ods/.odp)")
    else:
        print("pandoc    : not found (optional; needed for .rtf/.odt/.ods/.odp)")
        print("            Windows: winget install --id JohnMacFarlane.Pandoc -e")
    soffice = misc_engine.find_soffice()
    if soffice:
        print(f"libreoffice: {soffice}  (enables .doc/.xls/.ppt)")
    else:
        print("libreoffice: not found (optional; needed for .doc/.xls/.ppt)")
        print("            Windows: winget install --id TheDocumentFoundation.LibreOffice -e")

    print("\nsetup complete. Convert with:")
    print(f'  "{VENV_PY}" "{Path(__file__).resolve()}" "file.pdf"')
    return 0


# ------------------------------------------------------------------ conversion

def convert_modern(src: Path, ext: str, args, tess, extra_args: list[str], log=print):
    """Return (sections, stats, title) for the natively supported formats."""
    if ext == ".pdf":
        title = pdf_engine.pdf_title(src) or src.stem
        sections, stats = pdf_engine.convert_pdf(
            src, start=args.start, end=args.end, dpi=args.dpi, lang=args.lang,
            mode=args.mode, tess=tess, extra_args=extra_args, log=log)
        return sections, stats, title
    if ext == ".docx":
        sections, stats = office_engine.convert_docx(src, log=log)
        return sections, stats, src.stem
    if ext == ".pptx":
        sections, stats = office_engine.convert_pptx(src, start=args.start, end=args.end, log=log)
        return sections, stats, src.stem
    if ext in (".xlsx", ".xlsm"):
        sections, stats = office_engine.convert_xlsx(src, log=log)
        return sections, stats, src.stem
    if ext in (".html", ".htm", ".xhtml"):
        sections, stats = web_engine.convert_html(src, log=log)
        return sections, stats, src.stem
    if ext == ".epub":
        sections, stats = web_engine.convert_epub(src, log=log)
        return sections, stats, src.stem
    if ext in IMAGE_EXTS:
        sections, stats = misc_engine.convert_image(
            src, lang=args.lang, tess=tess, extra_args=extra_args, log=log)
        return sections, stats, src.stem
    if ext in TEXT_EXTS or ext in MD_EXTS:
        sections, stats = misc_engine.convert_text(src, log=log)
        return sections, stats, src.stem
    if ext in CSV_EXTS:
        sections, stats = misc_engine.convert_csv(src, log=log)
        return sections, stats, src.stem
    if ext in FENCE_EXTS:
        sections, stats = misc_engine.convert_fenced(src, FENCE_EXTS[ext], log=log)
        return sections, stats, src.stem
    raise RuntimeError(f"unsupported format: {ext}")


def _same_source(path: Path, src: Path) -> bool:
    """True if `path` looks like previous output of this tool for the same input file."""
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:400]
    except OSError:
        return False
    return f"> Source: {src.name} ->" in head


def resolve_out(args, src: Path) -> Path:
    if args.out is not None:
        out = args.out.expanduser().resolve()
        if not out.is_dir():
            out.parent.mkdir(parents=True, exist_ok=True)
            return out  # explicit file path: write exactly there
        base = out
    else:
        base = src.parent
    target = base / (src.stem + ".md")
    if not target.exists() or _same_source(target, src):
        return target
    # target belongs to a different source: keep it, fall back to <stem>.<ext>.md
    ext = src.suffix.lstrip(".")
    alt = base / f"{src.stem}.{ext}.md"
    n = 2
    while alt.exists() and not _same_source(alt, src):
        alt = base / f"{src.stem}.{ext}.{n}.md"
        n += 1
    return alt


def convert(args) -> int:
    src = Path(args.file).expanduser().resolve()
    if not src.is_file():
        print(f"ERROR: no such file: {src}", file=sys.stderr)
        return 1
    ext = src.suffix.lower()
    if ext not in SUPPORTED_EXTS:
        known = ", ".join(sorted(SUPPORTED_EXTS))
        print(f"ERROR: unsupported format '{ext or src.name}'. Supported: {known}", file=sys.stderr)
        return 1

    needs_tess = (ext in IMAGE_EXTS) or (ext == ".pdf" and args.mode != "digital")
    tess = None
    extra_args: list[str] = []
    if needs_tess:
        tess = find_tesseract()
        if tess is None:
            print("ERROR: Tesseract not found (needed for scanned PDFs and images).\n"
                  "Install it, or use --mode digital for text-layer-only PDFs:\n"
                  "  Windows: winget install --id UB-Mannheim.TesseractOCR -e\n"
                  "  macOS  : brew install tesseract\n"
                  "  Linux  : apt install tesseract-ocr", file=sys.stderr)
            return 1
        extra_args = ensure_langs(tess, args.lang)

    try:
        if ext in misc_engine.BINARY_OFFICE_EXTS:
            soffice = misc_engine.find_soffice()
            if soffice is None:
                print(f"ERROR: {ext} needs LibreOffice (soffice) to convert.\n"
                      "  Windows: winget install --id TheDocumentFoundation.LibreOffice -e\n"
                      "  macOS  : brew install --cask libreoffice", file=sys.stderr)
                return 1
            with tempfile.TemporaryDirectory(prefix="doc2md_") as td:
                converted = misc_engine.convert_binary_office(src, soffice, Path(td))
                cext = converted.suffix.lower()
                sections, stats, title = convert_modern(
                    converted, cext, args, tess, extra_args)
                stats["detail"] = f"{stats['detail']} ({ext} via LibreOffice)"
        elif ext in misc_engine.RTF_ODF_EXTS:
            pandoc = misc_engine.find_pandoc()
            if pandoc is None:
                print(f"ERROR: {ext} needs pandoc to convert.\n"
                      "  Windows: winget install --id JohnMacFarlane.Pandoc -e\n"
                      "  macOS  : brew install pandoc", file=sys.stderr)
                return 1
            sections, stats = misc_engine.convert_with_pandoc(src, pandoc)
            title = src.stem
        else:
            sections, stats, title = convert_modern(src, ext, args, tess, extra_args)
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: conversion failed: {e}", file=sys.stderr)
        return 1

    out = resolve_out(args, src)
    lines = [
        f"# {title}",
        "",
        f"> Source: {src.name} -> Markdown ({stats.get('detail', '')}).",
        "",
    ]
    for heading, body in sections:
        if heading:
            lines.append(f"## {heading}")
            lines.append("")
        lines.append(body.strip() if body.strip() else "(no text found)")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")

    failures = stats.get("failures", [])
    print(f"done: {len(sections)} section(s) "
          f"({stats.get('detail', '')}) -> {out} ({out.stat().st_size:,} bytes)")
    if failures:
        print("failed: " + ", ".join(f"page {p} ({e})" for p, e in failures))
        return 1
    return 0


# ------------------------------------------------------------------------- main

def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="Convert a document (PDF, DOCX, PPTX, XLSX, images, HTML, EPUB, "
                    "CSV, JSON, TXT, and more) to Markdown.")
    ap.add_argument("file", nargs="?", help="input file to convert")
    ap.add_argument("--setup", action="store_true",
                    help="create the skill venv, install Python deps, check Tesseract/pandoc/LibreOffice, then exit")
    ap.add_argument("--start", type=int, default=1, help="first page/slide, 1-based (PDF, PPTX)")
    ap.add_argument("--end", type=int, help="last page/slide, inclusive (PDF, PPTX)")
    ap.add_argument("--dpi", type=int, default=300, help="render DPI for OCR (PDF; default 300)")
    ap.add_argument("--lang", default="eng",
                    help="Tesseract language(s) for OCR, e.g. eng or eng+chi_tra (default eng)")
    ap.add_argument("--mode", choices=["auto", "digital", "ocr"], default="auto",
                    help="PDF page routing: auto detects scanned pages (default)")
    ap.add_argument("--out", type=Path, help="output .md file or existing directory (default: next to input)")
    args = ap.parse_args(argv)
    if not args.setup and not args.file:
        ap.error("an input file is required (or use --setup)")
    return args


def main() -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    args = parse_args()
    if args.setup:
        return cmd_setup()
    missing = missing_deps()
    if missing:
        print(f"Missing Python packages: {', '.join(missing)}\n"
              "First run the setup with a system Python 3.9+:\n"
              f'  python "{Path(__file__).resolve()}" --setup\n'
              f'then use the venv python:\n  "{VENV_PY}"', file=sys.stderr)
        return 1
    return convert(args)


if __name__ == "__main__":
    sys.exit(main())
