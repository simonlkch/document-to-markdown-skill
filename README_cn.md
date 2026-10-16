# pdf-to-markdown

[English](README.md) | [繁體中文](README_zh.md) | [简体中文](README_cn.md)

一个 [Agent Skill](https://agentskills.io)（也可作为独立 CLI 使用），能把 PDF 转换成干净的 Markdown，方便交给 AI 使用——**包含扫描版、纯图片的 PDF**（通过 Tesseract OCR）。

- **每个 PDF 输出一个 `.md`**——每一页都是一个 `## Page N` 章节，可直接交给任何 AI。
- **数字版与扫描版一次完成**——数字页面直接提取文字层；扫描页面自动检测并进行 OCR。
- **自我完备**——首次运行自动创建专属 `.venv` 并安装 PyMuPDF；缺少的 OCR 语言数据会自动下载。
- **完全离线运行**——不调用云端 API、不上传任何文件。

支持 Claude Code、OpenAI Codex CLI、opencode、pi、Qoder——任何读得懂 [SKILL.md](https://agentskills.io) 格式的工具。

## 安装

### 安装到你的 AI coding CLI（推荐）

```bash
git clone https://github.com/<your-github-username>/pdf-to-markdown.git
cd pdf-to-markdown
python install.py
```

`install.py` 会自动检测你安装了哪些 CLI，并把技能装进对应的 skills 目录。也可以明确指定：

| 工具 | `--target` | 安装位置 |
|---|---|---|
| Claude Code | `claude` | `~/.claude/skills/pdf-to-markdown/` |
| OpenAI Codex CLI | `codex` | `~/.codex/skills/pdf-to-markdown/`（会读取 `$CODEX_HOME`） |
| opencode | `opencode` | `~/.config/opencode/skills/pdf-to-markdown/` |
| pi | `pi` | `~/.agents/skills/pdf-to-markdown/`（共享的 skills 目录） |
| Qoder | `qoder` | `~/.qoder/skills/pdf-to-markdown/` |

```bash
python install.py --target all        # 所有支持的 CLI
python install.py --link              # 建立符号链接，多个 CLI 共用同一份（共用同一个 venv）
python install.py --list              # 显示安装路径与检测状态
python install.py --target-dir /path/to/repo/.claude/skills/pdf-to-markdown   # 项目级／自定义位置
```

### 通过社区安装器

```bash
npx skills add <your-github-username>/pdf-to-markdown
```

[skills.sh](https://skills.sh) 可以一次安装到 75 个以上的 agent（第三方工具）。

### 作为普通 CLI 使用

```bash
python scripts/pdf_to_markdown.py --setup                       # 一次性：创建 .venv、安装 PyMuPDF
.venv/Scripts/python scripts/pdf_to_markdown.py book.pdf        # Windows
.venv/bin/python     scripts/pdf_to_markdown.py book.pdf        # macOS / Linux
```

## 使用方式

### 作为技能（推荐）

安装完成后（见上文），直接用自然语言吩咐你的 agent 即可，技能会自动触发：

> “把 book.pdf 转换成 Markdown。”
>
> "Convert book.pdf to Markdown."
>
> “把这份扫描 PDF 的文字提取成一个 .md 文件。”

首次使用时，agent 会自动帮你完成环境设置：创建技能专属的 `.venv`、安装 PyMuPDF、检查 Tesseract。如果缺少 Tesseract（只有扫描版 PDF 才需要），它会提供一行安装命令让你执行。

你也可以明确调用这个技能：`/pdf-to-markdown`（Qoder、Claude Code）、`$pdf-to-markdown`（Codex）、`/skill:pdf-to-markdown`（pi）。

转换结果：PDF 旁边会生成一个 Markdown 文件，每一页都是一个 `## Page N` 章节，并附带自我说明的文件头——可直接交给任何 AI。

### 作为 CLI 使用

独立运行时的选项：

| 选项 | 默认 | 说明 |
|---|---|---|
| `--start N` / `--end N` | 整个 PDF | 页码范围（从 1 开始，含首尾） |
| `--out FILE_OR_DIR` | `<pdf 所在目录>/<文件名>.md` | 输出 Markdown 的路径 |
| `--lang eng+chi_tra` | `eng` | Tesseract 语言；缺少的语言数据会自动下载 |
| `--mode auto\|digital\|ocr` | `auto` | 页面处理方式：auto = 逐页自动检测 |
| `--dpi N` | `300` | OCR 页面的渲染分辨率（DPI） |

## 系统要求

- **Python 3.9+**——仅用于首次环境设置与运行脚本。
- **Tesseract**——只有扫描版 PDF 才需要（数字版 PDF 无需安装）：
  - Windows：`winget install --id UB-Mannheim.TesseractOCR -e`
  - macOS：`brew install tesseract`
  - Linux：`apt install tesseract-ocr`

## 工作原理

1. 先检查每一页是否有可用的文字层。文字充足时，直接用 PyMuPDF 提取。
2. 否则将该页以 300 DPI（灰度）渲染，再交给 Tesseract 进行 OCR。
3. 所有页面以 `## Page N` 章节写入同一个 Markdown 文件，并附上使用说明的文件头，让文件交给 AI 时能够自我说明。

## 卸载

把技能目录从 CLI 的 skills 文件夹删除即可，例如 `~/.claude/skills/pdf-to-markdown/` 或 `~/.qoder/skills/pdf-to-markdown/`。

## 许可

[MIT](LICENSE)
