# document-to-markdown-skill

[English](README.md) | [繁體中文](README_zh.md) | [简体中文](README_cn.md)

An [Agent Skill](https://agentskills.io) (and standalone CLI) that converts **any document into clean Markdown for AI ingestion** — PDF (digital or scanned), Word, PowerPoint, Excel, images, HTML, EPUB, CSV, JSON and more.

- **One `.md` per document** — ready to feed to any AI. PDF pages keep `## Page N` sections, slides `## Slide N`, sheets `## Sheet: name`, EPUB chapters `## 標題`.
- **Digital + scanned PDFs in one pass** — digital pages use the embedded text layer; scanned pages are auto-detected and OCR'd with Tesseract.
- **Self-contained** — first run creates its own `.venv` and installs the Python dependencies; missing OCR language data downloads on demand.
- **Runs fully offline** — no cloud APIs, no uploads.

Works with Claude Code, OpenAI Codex CLI, opencode, pi, Qoder — anything that reads the [SKILL.md](https://agentskills.io) format.

## Supported formats

| Format | Engine |
|---|---|
| PDF (digital) | text layer via PyMuPDF |
| PDF (scanned) | auto-detected per page → Tesseract OCR |
| DOCX | mammoth (headings, tables) |
| PPTX | python-pptx (slides, bullets, speaker notes, tables) |
| XLSX | openpyxl (one `## Sheet: name` section per sheet) |
| PNG / JPG / TIFF / BMP / WebP | Tesseract OCR (multi-frame TIFF becomes `## Page N`) |
| HTML / EPUB | beautifulsoup4 + markdownify / ebooklib |
| CSV / TSV | Markdown table |
| TXT / MD | direct (MD passes through verbatim) |
| JSON / XML | pretty-printed in a fenced code block |
| DOC / XLS / PPT, RTF, ODT / ODS / ODP | via LibreOffice (optional) or pandoc (optional), if installed |

## Install

### Into your AI coding CLI (recommended)

```bash
git clone https://github.com/simonlkch/document-to-markdown-skill.git
cd document-to-markdown-skill
python install.py
```

`install.py` auto-detects which CLIs you have and installs the skill into each. Or pick explicitly:

| Tool | `--target` | Installs to |
|---|---|---|
| Claude Code | `claude` | `~/.claude/skills/document-to-markdown-skill/` |
| OpenAI Codex CLI | `codex` | `~/.codex/skills/document-to-markdown-skill/` (respects `$CODEX_HOME`) |
| opencode | `opencode` | `~/.config/opencode/skills/document-to-markdown-skill/` |
| pi | `pi` | `~/.agents/skills/document-to-markdown-skill/` (shared skills dir) |
| Qoder | `qoder` | `~/.qoder/skills/document-to-markdown-skill/` |

```bash
python install.py --target all        # every supported CLI
python install.py --link              # symlink one shared copy (single venv)
python install.py --list              # show targets + detection status
python install.py --target-dir /path/to/repo/.claude/skills/document-to-markdown-skill   # project-level / custom
```

### Via the community skills installer

```bash
npx skills add simonlkch/document-to-markdown-skill
```

[skills.sh](https://skills.sh) installs into 75+ agents at once (third-party tool).

### As a plain CLI

```bash
python scripts/document_to_markdown.py --setup --install-system   # once: create .venv, install deps + Tesseract/pandoc
.venv/Scripts/python scripts/document_to_markdown.py report.docx     # Windows
.venv/bin/python     scripts/document_to_markdown.py report.docx     # macOS / Linux
```

## Usage

### As a skill (recommended)

Install it (above), then just ask your agent in natural language — the skill triggers automatically:

> "Convert report.docx to Markdown."
>
> "Extract the text of this scanned PDF into one .md file."
>
> "幫我將 sales.xlsx 轉做 markdown。"
>
> "把這份簡報 PPT 轉成 Markdown。"

On first use the agent sets up the environment for you: it creates the skill's own `.venv`, installs the Python dependencies, and checks the system tools (Tesseract, pandoc, LibreOffice). Missing Tesseract/pandoc are auto-installed when possible (winget / brew / apt-get); if that fails you get a one-line command to run.

You can also invoke the skill explicitly by name: `/document-to-markdown-skill` (Qoder, Claude Code), `$document-to-markdown-skill` (Codex), `/skill:document-to-markdown-skill` (pi).

The result is a single Markdown file next to your input, with a `> Source:` header recording the original file — ready to feed to any AI.

### As a CLI

Standalone options:

| Option | Default | Meaning |
|---|---|---|
| `--start N` / `--end N` | whole file | 1-based inclusive range (PDF pages, PPTX slides) |
| `--out FILE_OR_DIR` | `<input dir>/<stem>.md` | output markdown path; never overwrites a file from a different source (falls back to `<stem>.<ext>.md`) |
| `--images` | off | extract embedded images into `<output stem>_images/` and link them with relative URLs (DOCX/PPTX/XLSX/PDF); without it images stay as `*[image]*` placeholders |
| `--lang eng+chi_tra` | `eng` | Tesseract languages; missing language data auto-downloads |
| `--mode auto\|digital\|ocr` | `auto` | PDF page routing: auto = per-page detection |
| `--dpi N` | `300` | render DPI for OCR pages |

## Requirements

- **Python 3.9+** — only for the first-run setup and to run the script.
- **Tesseract** — needed only for scanned PDFs and image files (digital PDFs, Office files, etc. work without it). `--setup --install-system` tries to install it automatically; manual fallback:
  - Windows: `winget install --id UB-Mannheim.TesseractOCR -e`
  - macOS: `brew install tesseract`
  - Linux: `apt install tesseract-ocr`
- **Optional**: [pandoc](https://pandoc.org/) for RTF / ODT / ODS / ODP (also auto-installed by `--install-system`); LibreOffice for legacy `.doc` / `.xls` / `.ppt` (never auto-installed). The script prints install hints if they are missing.

## How it works

1. The input extension picks a converter: PyMuPDF (PDF), mammoth (DOCX), python-pptx (PPTX), openpyxl (XLSX), Tesseract (images), bs4/markdownify (HTML), ebooklib (EPUB), direct parsing (CSV/JSON/XML/TXT).
2. PDF pages are tested for a usable text layer. Enough text → extracted directly; otherwise the page is rendered at 300 DPI and OCR'd.
3. Everything is assembled into one Markdown file with a `> Source:` header recording the original file.

## Uninstall

Delete the skill directory from your CLI's skills folder, e.g. `~/.claude/skills/document-to-markdown-skill/` or `~/.qoder/skills/document-to-markdown-skill/`.

## License

[MIT](LICENSE)
