#!/usr/bin/env python3
"""pdf_to_markdown.py - convert a PDF into Markdown, fully offline.

- Digital pages: text is read from the PDF text layer (PyMuPDF).
- Scanned pages: rendered at --dpi and OCR'd with Tesseract, auto-detected per page.
- Output: one .md file, every page under a "## Page N" heading, ready to feed to an AI.

First run (creates .venv next to this skill and pip-installs PyMuPDF):
    python scripts/pdf_to_markdown.py --setup
Then run with the venv python:
    .venv/Scripts/python scripts/pdf_to_markdown.py book.pdf   (Windows)
    .venv/bin/python     scripts/pdf_to_markdown.py book.pdf   (macOS/Linux)

See --help for all options (--start/--end, --dpi, --lang, --mode, --out).
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = SKILL_DIR / ".venv"
IS_WIN = os.name == "nt"
VENV_PY = VENV_DIR / ("Scripts/python.exe" if IS_WIN else "bin/python")
TESSDATA_DIR = SKILL_DIR / "tessdata"
TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/{lang}.traineddata"
MIN_TEXT_CHARS = 40  # a text layer shorter than this => treat the page as scanned
PROGRESS_EVERY = 25

_MOD = None


def pymupdf():
    """Import PyMuPDF under its new name, falling back to the legacy `fitz`."""
    global _MOD
    if _MOD is None:
        try:
            import pymupdf
            _MOD = pymupdf
        except ImportError:
            import fitz
            _MOD = fitz
    return _MOD


# --------------------------------------------------------------------------- env

def find_system_python() -> list[str] | None:
    """A base Python 3.9+ on PATH, as a command list."""
    if IS_WIN:
        py = shutil.which("py")
        if py:
            return [py, "-3"]
    for name in ("python3", "python"):
        p = shutil.which(name)
        if p:
            return [p]
    return None


def find_tesseract() -> Path | None:
    p = shutil.which("tesseract")
    if p:
        return Path(p)
    if IS_WIN:
        local = os.environ.get("LOCALAPPDATA", "")
        for c in (
            Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
            Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
            Path(local) / "Programs/Tesseract-OCR/tesseract.exe",
            Path(local) / "Tesseract-OCR/tesseract.exe",
        ):
            if c.is_file():
                return c
    return None


def cmd_setup() -> int:
    print(f"skill dir : {SKILL_DIR}")

    # 1) venv + PyMuPDF
    venv_ok = False
    if VENV_PY.exists():
        r = subprocess.run(
            [str(VENV_PY), "-c",
             "import importlib.util as u; "
             "m = __import__('pymupdf') if u.find_spec('pymupdf') else __import__('fitz'); "
             "print('PyMuPDF', m.VersionBind)"],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            print(f"venv      : ok ({VENV_DIR})")
            print(f"            {r.stdout.strip()}")
            venv_ok = True
        else:
            print("venv      : exists but PyMuPDF import failed; recreating")
    if not venv_ok:
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
        print("installing PyMuPDF ...")
        r = subprocess.run(
            [str(VENV_PY), "-m", "pip", "install", "--disable-pip-version-check", "-q", "pymupdf"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(f"ERROR: pip install failed:\n{r.stderr.strip()[-1000:]}", file=sys.stderr)
            return 1
        print("PyMuPDF   : installed")

    # 2) Tesseract (needed only for scanned pages)
    tess = find_tesseract()
    if tess:
        r = subprocess.run([str(tess), "--version"], capture_output=True, encoding="utf-8", errors="replace")
        ver = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
        print(f"tesseract : {tess}")
        if ver:
            print(f"            {ver[0]}")
    else:
        print("tesseract : NOT FOUND - OCR of scanned pages will not work until it is installed.")
        print("            Windows: winget install --id UB-Mannheim.TesseractOCR -e")
        print("            macOS  : brew install tesseract")
        print("            Linux  : apt install tesseract-ocr")
        print("            other  : https://tesseract-ocr.github.io/tessdoc/Installation.html")

    print("\nsetup complete. Convert with:")
    print(f'  "{VENV_PY}" "{Path(__file__).resolve()}" "file.pdf"')
    return 0


def ensure_langs(tess: Path, lang: str) -> list[str]:
    """Make every requested OCR language available; return extra tesseract args."""
    langs = [l for l in lang.split("+") if l]
    sys_tessdata = tess.parent / "tessdata"
    if all((sys_tessdata / f"{l}.traineddata").exists() for l in langs):
        return []
    TESSDATA_DIR.mkdir(exist_ok=True)
    for l in langs:
        dst = TESSDATA_DIR / f"{l}.traineddata"
        if dst.exists():
            continue
        src = sys_tessdata / f"{l}.traineddata"
        if src.exists():
            shutil.copyfile(src, dst)
            continue
        url = TESSDATA_URL.format(lang=l)
        print(f"downloading {l}.traineddata from tessdata_fast ...")
        req = urllib.request.Request(url, headers={"User-Agent": "pdf-to-markdown-skill"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp, open(dst, "wb") as f:
                shutil.copyfileobj(resp, f)
        except Exception as e:
            print(f"ERROR: could not download language data for '{l}': {e}\n"
                  f"Download it manually from {url}\ninto {TESSDATA_DIR}", file=sys.stderr)
            raise SystemExit(1)
        print(f"  saved {dst.name} ({dst.stat().st_size:,} bytes)")
    return ["--tessdata-dir", str(TESSDATA_DIR)]


# ---------------------------------------------------------------------- convert

def tidy(text: str) -> str:
    text = text.replace("\x0c", "\n").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def ocr_page(page, tess: Path, lang: str, dpi: int, extra_args: list[str]) -> str:
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf().csGRAY)
    r = subprocess.run(
        [str(tess), "stdin", "stdout", "-l", lang, "--psm", "3", *extra_args],
        input=pix.tobytes("png"), capture_output=True,
    )
    if r.returncode != 0:
        msg = r.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(msg.splitlines()[-1] if msg else "tesseract failed")
    return r.stdout.decode("utf-8", "replace")


def resolve_out(args, pdf: Path) -> Path:
    if args.out is None:
        return pdf.with_suffix(".md")
    out = args.out.expanduser().resolve()
    if out.is_dir():
        return out / (pdf.stem + ".md")
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def convert(args) -> int:
    fitz = pymupdf()
    pdf = Path(args.pdf).expanduser().resolve()
    if not pdf.is_file():
        print(f"ERROR: no such file: {pdf}", file=sys.stderr)
        return 1
    doc = fitz.open(pdf)
    if doc.needs_pass:
        print("ERROR: the PDF is password-protected.", file=sys.stderr)
        return 1
    total_pages = doc.page_count
    start = max(1, args.start)
    end = min(args.end or total_pages, total_pages)
    if start > end:
        print(f"ERROR: page range {start}-{end} is empty (PDF has {total_pages} pages).", file=sys.stderr)
        return 1

    tess = None
    extra_args: list[str] = []
    if args.mode != "digital":
        tess = find_tesseract()
        if tess is None:
            print("ERROR: Tesseract not found (needed for scanned pages).\n"
                  "Install it, or use --mode digital for text-layer-only PDFs:\n"
                  "  Windows: winget install --id UB-Mannheim.TesseractOCR -e\n"
                  "  macOS  : brew install tesseract\n"
                  "  Linux  : apt install tesseract-ocr", file=sys.stderr)
            return 1
        extra_args = ensure_langs(tess, args.lang)

    meta_title = ""
    try:
        meta_title = ((doc.metadata or {}).get("title") or "").strip()
    except Exception:
        pass
    title = meta_title if 0 < len(meta_title) < 150 else pdf.stem

    n = end - start + 1
    digital = ocr = 0
    failures: list[tuple[int, str]] = []
    sections: list[tuple[int, str]] = []
    for i, pno in enumerate(range(start - 1, end), 1):
        pnum = pno + 1
        try:
            page = doc.load_page(pno)
            text, used = "", "digital"
            if args.mode in ("auto", "digital"):
                text = page.get_text("text").strip()
            if args.mode == "ocr" or (args.mode == "auto" and len(text) < MIN_TEXT_CHARS):
                text, used = ocr_page(page, tess, args.lang, args.dpi, extra_args), "ocr"
            if used == "ocr":
                ocr += 1
            else:
                digital += 1
            sections.append((pnum, tidy(text)))
        except Exception as e:
            failures.append((pnum, str(e)))
            sections.append((pnum, ""))
            print(f"  page {pnum}: FAILED ({e})")
        if i % PROGRESS_EVERY == 0 and i != n:
            print(f"  page {pnum}/{end} ... ({digital} digital, {ocr} OCR so far)")
    doc.close()

    out = resolve_out(args, pdf)
    lines = [
        f"# {title}",
        "",
        f"> Source: {pdf.name} -> Markdown ({n} pages; digital text layer + Tesseract OCR for scanned pages).",
        "> Each section below is one PDF page.",
        "",
        f"**用法：** 上傳 {out.name}，同 AI 講：「每頁以 ## Page N 分隔」。",
        "",
    ]
    for pnum, text in sections:
        lines.append(f"## Page {pnum}")
        lines.append("")
        lines.append(text if text else "(no text found on this page)")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")

    print(f"done: {len(sections)} pages ({digital} digital, {ocr} OCR, {len(failures)} failed) "
          f"-> {out} ({out.stat().st_size:,} bytes)")
    if failures:
        print("failed pages: " + ", ".join(str(p) for p, _ in failures))
        return 1
    return 0


# ------------------------------------------------------------------------- main

def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description="Convert a PDF to Markdown (digital text layer + Tesseract OCR for scanned pages).")
    ap.add_argument("pdf", nargs="?", help="input PDF path")
    ap.add_argument("--setup", action="store_true",
                    help="create the skill venv, install PyMuPDF, check Tesseract, then exit")
    ap.add_argument("--start", type=int, default=1, help="first page, 1-based (default 1)")
    ap.add_argument("--end", type=int, help="last page, inclusive (default: last page)")
    ap.add_argument("--dpi", type=int, default=300, help="render DPI for OCR pages (default 300)")
    ap.add_argument("--lang", default="eng",
                    help="Tesseract language(s), e.g. eng or eng+chi_tra (default eng)")
    ap.add_argument("--mode", choices=["auto", "digital", "ocr"], default="auto",
                    help="page routing: auto detects scanned pages (default), digital = text layer only, ocr = force OCR")
    ap.add_argument("--out", type=Path, help="output .md file or existing directory (default: <pdf dir>/<stem>.md)")
    args = ap.parse_args(argv)
    if not args.setup and not args.pdf:
        ap.error("a PDF path is required (or use --setup)")
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
    try:
        pymupdf()
    except ImportError:
        print("PyMuPDF is not importable in this Python.\n"
              "First run the setup with a system Python 3.9+:\n"
              f"  python \"{Path(__file__).resolve()}\" --setup\n"
              f"then use the venv python:\n  \"{VENV_PY}\"", file=sys.stderr)
        return 1
    return convert(args)


if __name__ == "__main__":
    sys.exit(main())
