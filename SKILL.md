---
name: document-to-markdown-skill
description: Convert any document into Markdown (.md) for AI ingestion - PDF (digital or scanned), Word DOCX, PowerPoint PPTX, Excel XLSX, images (PNG/JPG/TIFF, via Tesseract OCR), HTML, EPUB, CSV/JSON/XML/TXT, and legacy .doc/.xls/.ppt/.rtf/.odt. Use when the user asks to convert, extract, or turn any file into Markdown or text ("convert this file to markdown", "document to markdown", "turn this PDF into md", "extract text from this document", "OCR this scanned PDF"). Handles digital and scanned PDFs automatically, manages its own Python environment (venv) and Tesseract language data.
---

# Document → Markdown

Convert any document into one Markdown file, ready to feed to an AI. PDF pages keep `## Page N` separators, slides `## Slide N`, sheets `## Sheet: name`, EPUB chapters use the chapter's own title as the `##` heading.

| Format | Engine |
|---|---|
| PDF (digital) | text layer via PyMuPDF |
| PDF (scanned) | auto-detected per page → Tesseract OCR |
| DOCX | mammoth (headings, tables) |
| PPTX | python-pptx (slides, bullets, notes, tables) |
| XLSX | openpyxl (one `## Sheet: name` per sheet) |
| PNG/JPG/TIFF/... | Tesseract OCR (multi-frame TIFF paginated) |
| HTML / EPUB | bs4 + markdownify / ebooklib |
| CSV / TXT / MD | direct (CSV → Markdown table) |
| JSON / XML | pretty-printed in a fenced block |
| DOC/XLS/PPT, RTF, ODT... | LibreOffice / pandoc (optional, if installed) |

## Workflow

1. **First time only — setup** (creates `.venv/` inside this skill folder, pip-installs the Python deps, checks Tesseract):
   ```
   python "<skill dir>/scripts/document_to_markdown.py" --setup
   ```
   Use any system Python 3.9+ (`py -3` or `python` on Windows, `python3` elsewhere).
   - If Tesseract is missing, setup prints the install command (`winget install --id UB-Mannheim.TesseractOCR -e` on Windows). Hand it to the user to run; then re-run `--setup` to verify. Non-image formats still work without Tesseract.
   - pandoc / LibreOffice are optional; setup reports their status and install hints.
   - Skip this step if `<skill dir>/.venv` already exists.

2. **Convert** (always use the skill venv python):
   ```
   "<skill dir>/.venv/Scripts/python.exe" "<skill dir>/scripts/document_to_markdown.py" "file.docx" [options]
   ```
   macOS/Linux: `<skill dir>/.venv/bin/python`.

   Options:
   - `--start N` / `--end N` — 1-based inclusive range (PDF pages, PPTX slides)
   - `--out FILE_OR_DIR` — output `.md` (default: `<input folder>/<stem>.md`)
   - `--lang eng+chi_tra` — OCR languages; missing tessdata auto-downloads into `<skill dir>/tessdata/`
   - `--mode auto|digital|ocr` — PDF page routing (default auto)
   - `--dpi N` — render DPI for OCR pages (default 300)

3. **Report** to the user: link the output `.md`, what was converted, and any failures (failed pages do not abort the run; the script exits 1 and lists them).

## Notes

- The `<skill dir>` is the folder containing this SKILL.md — resolve it before running scripts.
- OCR is slow (~1–3 s/page at 300 DPI). For large books run in the background; the script prints progress every 25 pages.
- The output starts with `# <title>` and a `> Source: <file> -> Markdown (<detail>).` line recording the original filename and conversion detail.
- Output files are never overwritten silently: if `<stem>.md` already exists from a *different* source file, the tool saves as `<stem>.<ext>.md` instead (re-running the same conversion overwrites its own previous output). An explicit `--out FILE` path is always written as given.
