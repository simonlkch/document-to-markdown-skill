---
name: pdf-to-markdown
description: Convert PDF files into Markdown (.md) for AI ingestion, including scanned/image-only PDFs via Tesseract OCR. Use when the user asks to convert, extract, or turn a PDF into Markdown or text ("PDF 轉 Markdown", "轉成 md", "將個 PDF 變做 markdown", "extract text from this PDF", "OCR this scanned PDF"). Handles digital and scanned PDFs automatically, manages its own Python environment (venv + PyMuPDF) and Tesseract language data.
---

# PDF → Markdown

Convert any PDF (digital or scanned) into one Markdown file with `## Page N` separators per page, ready to feed to an AI. Digital pages use the embedded text layer; scanned pages are auto-detected per page and OCR'd with Tesseract.

## Workflow

1. **First time only — setup** (creates `.venv/` inside this skill folder, pip-installs PyMuPDF, checks Tesseract):
   ```
   python "<skill dir>/scripts/pdf_to_markdown.py" --setup
   ```
   Use any system Python 3.9+ (`py -3` or `python` on Windows, `python3` elsewhere).
   - If Tesseract is missing, setup prints the install command (`winget install --id UB-Mannheim.TesseractOCR -e` on Windows). Hand it to the user to run; then re-run `--setup` to verify. Digital-only PDFs still work without Tesseract (`--mode digital`).
   - Skip this step if `<skill dir>/.venv` already exists.

2. **Convert** (always use the skill venv python so PyMuPDF is importable):
   ```
   "<skill dir>/.venv/Scripts/python.exe" "<skill dir>/scripts/pdf_to_markdown.py" "book.pdf" [options]
   ```
   macOS/Linux: `<skill dir>/.venv/bin/python`.

   Options:
   - `--start N` / `--end N` — 1-based inclusive page range (default: whole PDF)
   - `--out FILE_OR_DIR` — output `.md` (default: `<pdf folder>/<stem>.md`)
   - `--lang eng+chi_tra` — OCR languages; missing tessdata auto-downloads into `<skill dir>/tessdata/`
   - `--mode auto|digital|ocr` — page routing (default auto)
   - `--dpi N` — render DPI for OCR pages (default 300)

3. **Report** to the user: link the output `.md`, page counts (digital / OCR / failed), and any failed pages.

## Notes

- The `<skill dir>` is the folder containing this SKILL.md — resolve it before running scripts.
- OCR is slow (~1–3 s/page at 300 DPI). For large books run in the background or with a generous timeout; the script prints progress every 25 pages.
- A failed page does not abort the run; the script exits 1 and lists failed page numbers.
- Output header includes a usage line: feed the `.md` to an AI and say 「每頁以 ## Page N 分隔」.
