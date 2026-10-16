"""Tesseract discovery, language-data management, and OCR helpers."""
from __future__ import annotations

import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TESSDATA_DIR = SKILL_DIR / "tessdata"
TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/{lang}.traineddata"
IS_WIN = os.name == "nt"


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


def tesseract_version(tess: Path) -> str:
    r = subprocess.run([str(tess), "--version"], capture_output=True,
                       encoding="utf-8", errors="replace")
    lines = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
    return lines[0].strip() if lines else "unknown"


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
        req = urllib.request.Request(url, headers={"User-Agent": "document-to-markdown-skill"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp, open(dst, "wb") as f:
                shutil.copyfileobj(resp, f)
        except Exception as e:
            raise SystemExit(f"ERROR: could not download language data for '{l}': {e}\n"
                             f"Download it manually from {url}\ninto {TESSDATA_DIR}")
        print(f"  saved {dst.name} ({dst.stat().st_size:,} bytes)")
    return ["--tessdata-dir", str(TESSDATA_DIR)]


def png_bytes_to_text(png: bytes, tess: Path, lang: str, extra_args: list[str]) -> str:
    """OCR a PNG image (bytes) through tesseract stdin/stdout."""
    r = subprocess.run(
        [str(tess), "stdin", "stdout", "-l", lang, "--psm", "3", *extra_args],
        input=png, capture_output=True,
    )
    if r.returncode != 0:
        msg = r.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(msg.splitlines()[-1] if msg else "tesseract failed")
    return r.stdout.decode("utf-8", "replace")
