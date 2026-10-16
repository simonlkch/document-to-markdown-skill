"""Plain-text-ish formats (txt/md/csv/tsv/json/xml/yaml) and pandoc/LibreOffice fallbacks."""
from __future__ import annotations

import csv as csv_mod
import io
import os
import shutil
import subprocess
from pathlib import Path

from md_utils import md_table, tidy

IS_WIN = os.name == "nt"


# ---------------------------------------------------------------- text-ish

def convert_text(path: Path, log=print):
    """Plain text; markdown files are passed through verbatim."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in (".md", ".markdown"):
        body, detail = raw.strip(), "markdown (verbatim)"
    else:
        body, detail = tidy(raw), f"plain text ({len(raw):,} chars)"
    return [(None, body)], {"detail": detail}


def convert_csv(path: Path, log=print):
    """CSV/TSV -> one pipe table (first row = header)."""
    text = path.read_bytes().decode("utf-8-sig", errors="replace")
    dialect: csv_mod.Dialect = csv_mod.excel
    if path.suffix.lower() != ".tsv":
        try:
            dialect = csv_mod.Sniffer().sniff(text[:4096])
        except csv_mod.Error:
            dialect = csv_mod.excel
    rows = [row for row in csv_mod.reader(io.StringIO(text), dialect)]
    rows = [r for r in rows if any(c.strip() for c in r)]
    body = md_table(rows) if rows else "(empty)"
    return [(None, body)], {"detail": f"{len(rows)} rows ({path.suffix.lstrip('.').lower()})"}


def convert_fenced(path: Path, lang: str, log=print):
    """JSON/XML/YAML -> pretty-printed inside a fenced code block."""
    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    if lang == "json":
        import json
        try:
            raw = json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
        except Exception:
            pass
    elif lang == "xml":
        import xml.dom.minidom
        try:
            raw = xml.dom.minidom.parseString(raw).toprettyxml(indent="  ")
            raw = "\n".join(line for line in raw.splitlines() if line.strip())
        except Exception:
            pass
    body = f"```{lang}\n{raw}\n```"
    return [(None, body)], {"detail": f"{lang.upper()} ({len(raw):,} chars)"}


# ---------------------------------------------------------------- ocr image

def convert_image(path: Path, *, lang: str = "eng", tess=None,
                  extra_args: list[str] | None = None, log=print):
    """Image -> OCR text via Tesseract. Multi-frame files (e.g. TIFF) -> one section per frame."""
    from PIL import Image
    from ocr_engine import png_bytes_to_text

    extra_args = extra_args or []
    sections: list[tuple[str | None, str]] = []
    with Image.open(path) as im:
        frames = getattr(im, "n_frames", 1)
        for i in range(frames):
            im.seek(i)
            buf = io.BytesIO()
            im.convert("RGB").save(buf, format="PNG")
            text = png_bytes_to_text(buf.getvalue(), tess, lang, extra_args)
            heading = f"Page {i + 1}" if frames > 1 else None
            sections.append((heading, tidy(text)))
    return sections, {"detail": f"image OCR via Tesseract ({path.suffix.lstrip('.').lower()})"}


# ---------------------------------------------------------------- legacy

RTF_ODF_EXTS = {".rtf", ".odt", ".ods", ".odp"}
BINARY_OFFICE_EXTS = {".doc": ".docx", ".xls": ".xlsx", ".ppt": ".pptx"}


def find_pandoc() -> Path | None:
    p = shutil.which("pandoc")
    return Path(p) if p else None


def find_soffice() -> Path | None:
    p = shutil.which("soffice")
    if p:
        return Path(p)
    if IS_WIN:
        for c in (Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
                  Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe")):
            if c.is_file():
                return c
    return None


def convert_with_pandoc(path: Path, pandoc: Path, log=print):
    """rtf/odt/ods/odp -> markdown through pandoc (gfm output)."""
    r = subprocess.run([str(pandoc), str(path), "-t", "gfm", "--wrap=none"],
                       capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not (r.stdout or "").strip():
        raise RuntimeError(f"pandoc failed: {(r.stderr or '').strip()[:200]}")
    return [(None, tidy(r.stdout))], {"detail": f"{path.suffix.lstrip('.').lower()} via pandoc"}


def convert_binary_office(path: Path, soffice: Path, tmpdir: Path):
    """Legacy .doc/.xls/.ppt -> modern format via headless LibreOffice.

    Returns the converted file path; the caller re-dispatches on it.
    """
    target = BINARY_OFFICE_EXTS[path.suffix.lower()]
    r = subprocess.run(
        [str(soffice), "--headless", "--convert-to", target.lstrip("."),
         "--outdir", str(tmpdir), str(path)],
        capture_output=True, encoding="utf-8", errors="replace", timeout=300,
    )
    produced = tmpdir / (path.stem + target)
    if r.returncode != 0 or not produced.is_file():
        raise RuntimeError(f"LibreOffice conversion failed: "
                           f"{((r.stderr or '') + (r.stdout or '')).strip()[:200]}")
    return produced
