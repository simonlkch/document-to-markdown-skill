# document-to-markdown-skill

[English](README.md) | [繁體中文](README_zh.md) | [简体中文](README_cn.md)

一个 [Agent Skill](https://agentskills.io)（也可作为独立 CLI 使用），能把**任何文档**转换成干净的 Markdown，方便交给 AI 使用——PDF（数字版或扫描版）、Word、PowerPoint、Excel、图片、HTML、EPUB、CSV、JSON 等等。

- **每份文档输出一个 `.md`**——PDF 每一页是 `## Page N` 章节、幻灯片每一张是 `## Slide N`、表格每个工作表是 `## Sheet: 名称`、EPUB 每一章是 `## 标题`。
- **数字版与扫描版 PDF 一次完成**——数字页面直接提取文字层；扫描页面自动检测并进行 OCR。
- **自我完备**——首次运行自动创建专属 `.venv` 并安装依赖；缺少的 OCR 语言数据会自动下载。
- **完全离线运行**——不调用云端 API、不上传任何文件。

支持 Claude Code、OpenAI Codex CLI、opencode、pi、Qoder——任何读得懂 [SKILL.md](https://agentskills.io) 格式的工具。

## 支持的格式

| 格式 | 转换引擎 |
|---|---|
| PDF（数字版） | 通过 PyMuPDF 提取文字层 |
| PDF（扫描版） | 逐页自动检测 → Tesseract OCR |
| DOCX | mammoth（标题、表格） |
| PPTX | python-pptx（幻灯片、项目符号、备注、表格） |
| XLSX | openpyxl（每个工作表一个 `## Sheet: 名称` 章节） |
| PNG / JPG / TIFF / BMP / WebP | Tesseract OCR（多页 TIFF 变成 `## Page N`） |
| HTML / EPUB | beautifulsoup4 + markdownify / ebooklib |
| CSV / TSV | Markdown 表格 |
| TXT / MD | 直接处理（MD 原样保留） |
| JSON / XML | 格式化后放入代码块 |
| DOC / XLS / PPT、RTF、ODT / ODS / ODP | 通过 LibreOffice（可选）或 pandoc（可选），需已安装 |

## 安装

### 安装到你的 AI coding CLI（推荐）

```bash
git clone https://github.com/<your-github-username>/document-to-markdown-skill.git
cd document-to-markdown-skill
python install.py
```

`install.py` 会自动检测你安装了哪些 CLI，并把技能装进对应的 skills 目录。也可以明确指定：

| 工具 | `--target` | 安装位置 |
|---|---|---|
| Claude Code | `claude` | `~/.claude/skills/document-to-markdown-skill/` |
| OpenAI Codex CLI | `codex` | `~/.codex/skills/document-to-markdown-skill/`（会读取 `$CODEX_HOME`） |
| opencode | `opencode` | `~/.config/opencode/skills/document-to-markdown-skill/` |
| pi | `pi` | `~/.agents/skills/document-to-markdown-skill/`（共享的 skills 目录） |
| Qoder | `qoder` | `~/.qoder/skills/document-to-markdown-skill/` |

```bash
python install.py --target all        # 所有支持的 CLI
python install.py --link              # 建立符号链接，多个 CLI 共用同一份（共用同一个 venv）
python install.py --list              # 显示安装路径与检测状态
python install.py --target-dir /path/to/repo/.claude/skills/document-to-markdown-skill   # 项目级／自定义位置
```

### 通过社区安装器

```bash
npx skills add <your-github-username>/document-to-markdown-skill
```

[skills.sh](https://skills.sh) 可以一次安装到 75 个以上的 agent（第三方工具）。

### 作为普通 CLI 使用

```bash
python scripts/document_to_markdown.py --setup                       # 一次性：创建 .venv、安装依赖
.venv/Scripts/python scripts/document_to_markdown.py report.docx     # Windows
.venv/bin/python     scripts/document_to_markdown.py report.docx     # macOS / Linux
```

## 使用方式

### 作为技能（推荐）

安装完成后（见上文），直接用自然语言吩咐你的 agent 即可，技能会自动触发：

> “把 report.docx 转换成 Markdown。”
>
> “把这份扫描 PDF 的文字提取成一个 .md 文件。”
>
> "Convert sales.xlsx to Markdown."

首次使用时，agent 会自动帮你完成环境设置：创建技能专属的 `.venv`、安装依赖、检查 Tesseract。如果缺少 Tesseract（只有扫描版 PDF 与图片才需要），它会提供一行安装命令让你执行。

你也可以明确调用这个技能：`/document-to-markdown-skill`（Qoder、Claude Code）、`$document-to-markdown-skill`（Codex）、`/skill:document-to-markdown-skill`（pi）。

转换结果：输入文件旁边会生成一个 Markdown 文件，并附带自我说明的文件头——可直接交给任何 AI。

### 作为 CLI 使用

独立运行时的选项：

| 选项 | 默认 | 说明 |
|---|---|---|
| `--start N` / `--end N` | 整份文档 | 范围（从 1 开始，含首尾；适用于 PDF 页码、PPTX 幻灯片） |
| `--out FILE_OR_DIR` | `<输入文件所在目录>/<文件名>.md` | 输出 Markdown 的路径 |
| `--lang eng+chi_tra` | `eng` | Tesseract 语言；缺少的语言数据会自动下载 |
| `--mode auto\|digital\|ocr` | `auto` | PDF 页面处理方式：auto = 逐页自动检测 |
| `--dpi N` | `300` | OCR 页面的渲染分辨率（DPI） |

## 系统要求

- **Python 3.9+**——仅用于首次环境设置与运行脚本。
- **Tesseract**——只有扫描版 PDF 与图片文件才需要（数字版 PDF、Office 文件等无需安装）：
  - Windows：`winget install --id UB-Mannheim.TesseractOCR -e`
  - macOS：`brew install tesseract`
  - Linux：`apt install tesseract-ocr`
- **可选**：[pandoc](https://pandoc.org/) 用于 RTF / ODT / ODS / ODP；LibreOffice 用于旧版 `.doc` / `.xls` / `.ppt`。缺少时脚本会提示安装命令。

## 工作原理

1. 根据扩展名选择转换引擎：PyMuPDF（PDF）、mammoth（DOCX）、python-pptx（PPTX）、openpyxl（XLSX）、Tesseract（图片）、bs4/markdownify（HTML）、ebooklib（EPUB）、直接解析（CSV/JSON/XML/TXT）。
2. PDF 会逐页检查是否有可用的文字层。文字充足时直接提取；否则将该页以 300 DPI 渲染后交给 Tesseract 进行 OCR。
3. 所有内容组合成同一个 Markdown 文件，并附上使用说明的文件头，让文件交给 AI 时能够自我说明。

## 卸载

把技能目录从 CLI 的 skills 文件夹删除即可，例如 `~/.claude/skills/document-to-markdown-skill/` 或 `~/.qoder/skills/document-to-markdown-skill/`。

## 许可

[MIT](LICENSE)
