# pdf-to-markdown

[English](README.md) | [繁體中文](README_zh.md) | [简体中文](README_cn.md)

An [Agent Skill](https://agentskills.io) (and standalone CLI) that converts PDFs into clean Markdown for AI ingestion — **including scanned, image-only PDFs** via Tesseract OCR.

- **One `.md` per PDF** — every page under a `## Page N` heading, ready to feed to any AI.
- **Digital + scanned in one pass** — digital pages use the embedded text layer; scanned pages are auto-detected and OCR'd.
- **Self-contained** — first run creates its own `.venv` and installs PyMuPDF; missing OCR language data downloads on demand.
- **Runs fully offline** — no cloud APIs, no uploads.

Works with Claude Code, OpenAI Codex CLI, opencode, pi, Qoder — anything that reads the [SKILL.md](https://agentskills.io) format.

## Install

### Into your AI coding CLI (recommended)

```bash
git clone https://github.com/<your-github-username>/pdf-to-markdown.git
cd pdf-to-markdown
python install.py
```

`install.py` auto-detects which CLIs you have and installs the skill into each. Or pick explicitly:

| Tool | `--target` | Installs to |
|---|---|---|
| Claude Code | `claude` | `~/.claude/skills/pdf-to-markdown/` |
| OpenAI Codex CLI | `codex` | `~/.codex/skills/pdf-to-markdown/` (respects `$CODEX_HOME`) |
| opencode | `opencode` | `~/.config/opencode/skills/pdf-to-markdown/` |
| pi | `pi` | `~/.agents/skills/pdf-to-markdown/` (shared skills dir) |
| Qoder | `qoder` | `~/.qoder/skills/pdf-to-markdown/` |

```bash
python install.py --target all        # every supported CLI
python install.py --link              # symlink one shared copy (single venv)
python install.py --list              # show targets + detection status
python install.py --target-dir /path/to/repo/.claude/skills/pdf-to-markdown   # project-level / custom
```

### Via the community skills installer

```bash
npx skills add <your-github-username>/pdf-to-markdown
```

[skills.sh](https://skills.sh) installs into 75+ agents at once (third-party tool).

### As a plain CLI

```bash
python scripts/pdf_to_markdown.py --setup                       # once: create .venv, install PyMuPDF
.venv/Scripts/python scripts/pdf_to_markdown.py book.pdf        # Windows
.venv/bin/python     scripts/pdf_to_markdown.py book.pdf        # macOS / Linux
```

## Usage

### As a skill (recommended)

Install it (above), then just ask your agent in natural language — the skill triggers automatically:

> "Convert book.pdf to Markdown."
>
> "Extract the text of this scanned PDF into one .md file."
>
> "PDF 轉 Markdown" / "把這個掃描 PDF 轉成 Markdown。"

On first use the agent sets up the environment for you: it creates the skill's own `.venv`, installs PyMuPDF, and checks Tesseract. If Tesseract is missing (only needed for scanned PDFs), it gives you the one-line install command to run.

You can also invoke the skill explicitly by name: `/pdf-to-markdown` (Qoder, Claude Code), `$pdf-to-markdown` (Codex), `/skill:pdf-to-markdown` (pi).

The result is a single Markdown file next to your PDF — every page as a `## Page N` section, with a self-describing header — ready to feed to any AI.

### As a CLI

Standalone options:

| Option | Default | Meaning |
|---|---|---|
| `--start N` / `--end N` | whole PDF | 1-based inclusive page range |
| `--out FILE_OR_DIR` | `<pdf dir>/<stem>.md` | output markdown path |
| `--lang eng+chi_tra` | `eng` | Tesseract languages; missing language data auto-downloads |
| `--mode auto\|digital\|ocr` | `auto` | page routing: auto = per-page detection |
| `--dpi N` | `300` | render DPI for OCR pages |

## Requirements

- **Python 3.9+** — only for the first-run setup and to run the script.
- **Tesseract** — needed only for scanned PDFs (digital PDFs work without it):
  - Windows: `winget install --id UB-Mannheim.TesseractOCR -e`
  - macOS: `brew install tesseract`
  - Linux: `apt install tesseract-ocr`

## How it works

1. Each page is tested for a usable text layer. Enough text → it is extracted directly with PyMuPDF.
2. Otherwise the page is rendered at 300 DPI (grayscale) and OCR'd with Tesseract.
3. Pages are written as `## Page N` sections into one Markdown file — with a usage header so the file is self-describing when fed to an AI.

## Uninstall

Delete the skill directory from your CLI's skills folder, e.g. `~/.claude/skills/pdf-to-markdown/` or `~/.qoder/skills/pdf-to-markdown/`.

## License

[MIT](LICENSE)
