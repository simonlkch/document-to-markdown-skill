# document-to-markdown-skill

[English](README.md) | [繁體中文](README_zh.md) | [简体中文](README_cn.md)

一個 [Agent Skill](https://agentskills.io)（亦可作為獨立 CLI 使用），能把**任何文件**轉換成乾淨的 Markdown，方便交給 AI 使用——PDF（數位版或掃描版）、Word、PowerPoint、Excel、圖片、HTML、EPUB、CSV、JSON 等等。

- **每份文件輸出一個 `.md`**——PDF 每一頁是 `## Page N` 章節、簡報每一張是 `## Slide N`、試算表每個工作表是 `## Sheet: 名稱`、EPUB 每一章是 `## 標題`。
- **數位版與掃描版 PDF 一次完成**——數位頁面直接抽取文字層；掃描頁面自動偵測並進行 OCR。
- **自我完備**——首次執行自動建立專屬 `.venv` 並安裝相依套件；缺少的 OCR 語言資料會自動下載。
- **完全離線執行**——不呼叫雲端 API、不上傳任何檔案。

支援 Claude Code、OpenAI Codex CLI、opencode、pi、Qoder——任何讀得懂 [SKILL.md](https://agentskills.io) 格式的工具。

## 支援的格式

| 格式 | 轉換引擎 |
|---|---|
| PDF（數位版） | 透過 PyMuPDF 抽取文字層 |
| PDF（掃描版） | 逐頁自動偵測 → Tesseract OCR |
| DOCX | mammoth（標題、表格） |
| PPTX | python-pptx（投影片、項目符號、備忘稿、表格） |
| XLSX | openpyxl（每個工作表一個 `## Sheet: 名稱` 章節） |
| PNG / JPG / TIFF / BMP / WebP | Tesseract OCR（多頁 TIFF 變成 `## Page N`） |
| HTML / EPUB | beautifulsoup4 + markdownify / ebooklib |
| CSV / TSV | Markdown 表格 |
| TXT / MD | 直接處理（MD 原樣保留） |
| JSON / XML | 格式化後放入程式碼區塊 |
| DOC / XLS / PPT、RTF、ODT / ODS / ODP | 透過 LibreOffice（選用）或 pandoc（選用），需已安裝 |

## 安裝

### 安裝到你的 AI coding CLI（推薦）

```bash
git clone https://github.com/<your-github-username>/document-to-markdown-skill.git
cd document-to-markdown-skill
python install.py
```

`install.py` 會自動偵測你安裝了哪些 CLI，並把技能裝進對應的 skills 目錄。也可以明確指定：

| 工具 | `--target` | 安裝位置 |
|---|---|---|
| Claude Code | `claude` | `~/.claude/skills/document-to-markdown-skill/` |
| OpenAI Codex CLI | `codex` | `~/.codex/skills/document-to-markdown-skill/`（會讀取 `$CODEX_HOME`） |
| opencode | `opencode` | `~/.config/opencode/skills/document-to-markdown-skill/` |
| pi | `pi` | `~/.agents/skills/document-to-markdown-skill/`（共用的 skills 目錄） |
| Qoder | `qoder` | `~/.qoder/skills/document-to-markdown-skill/` |

```bash
python install.py --target all        # 所有支援的 CLI
python install.py --link              # 建立符號連結，多個 CLI 共用同一份（共用同一個 venv）
python install.py --list              # 顯示安裝路徑與偵測狀態
python install.py --target-dir /path/to/repo/.claude/skills/document-to-markdown-skill   # 專案層級／自訂位置
```

### 透過社群安裝器

```bash
npx skills add <your-github-username>/document-to-markdown-skill
```

[skills.sh](https://skills.sh) 可以一次安裝到 75 個以上的 agent（第三方工具）。

### 作為一般 CLI 使用

```bash
python scripts/document_to_markdown.py --setup                       # 一次性：建立 .venv、安裝相依套件
.venv/Scripts/python scripts/document_to_markdown.py report.docx     # Windows
.venv/bin/python     scripts/document_to_markdown.py report.docx     # macOS / Linux
```

## 使用方式

### 作為技能（推薦）

安裝完成後（見上文），直接用自然語言吩咐你的 agent 即可，技能會自動觸發：

> 「把 report.docx 轉成 Markdown。」
>
> 「將這份掃描 PDF 的文字抽取成一個 .md 檔。」
>
> "Convert sales.xlsx to Markdown."

首次使用時，agent 會自動幫你完成環境設定：建立技能專屬的 `.venv`、安裝相依套件、檢查 Tesseract。如果缺少 Tesseract（只有掃描版 PDF 與圖片才需要），它會提供一行安裝指令讓你執行。

你也可以明確叫用這個技能：`/document-to-markdown-skill`（Qoder、Claude Code）、`$document-to-markdown-skill`（Codex）、`/skill:document-to-markdown-skill`（pi）。

轉換結果：輸入檔旁邊會產生一個 Markdown 檔，並附有自我說明的標頭——可直接交給任何 AI。

### 作為 CLI 使用

獨立執行時的選項：

| 選項 | 預設 | 說明 |
|---|---|---|
| `--start N` / `--end N` | 整份文件 | 範圍（從 1 開始，含頭尾；適用 PDF 頁碼、PPTX 投影片） |
| `--out FILE_OR_DIR` | `<輸入檔所在目錄>/<檔名>.md` | 輸出 Markdown 的路徑 |
| `--lang eng+chi_tra` | `eng` | Tesseract 語言；缺少的語言資料會自動下載 |
| `--mode auto\|digital\|ocr` | `auto` | PDF 頁面處理方式：auto = 逐頁自動偵測 |
| `--dpi N` | `300` | OCR 頁面的算圖解析度（DPI） |

## 系統需求

- **Python 3.9+**——僅用於首次環境設定與執行腳本。
- **Tesseract**——只有掃描版 PDF 與圖片檔才需要（數位版 PDF、Office 檔等不需安裝）：
  - Windows：`winget install --id UB-Mannheim.TesseractOCR -e`
  - macOS：`brew install tesseract`
  - Linux：`apt install tesseract-ocr`
- **選用**：[pandoc](https://pandoc.org/) 用於 RTF / ODT / ODS / ODP；LibreOffice 用於舊版 `.doc` / `.xls` / `.ppt`。缺少時腳本會提示安裝指令。

## 運作原理

1. 依副檔名選擇轉換引擎：PyMuPDF（PDF）、mammoth（DOCX）、python-pptx（PPTX）、openpyxl（XLSX）、Tesseract（圖片）、bs4/markdownify（HTML）、ebooklib（EPUB）、直接解析（CSV/JSON/XML/TXT）。
2. PDF 會逐頁檢查是否有可用的文字層。文字充足時直接抽取；否則將該頁以 300 DPI 算圖後交由 Tesseract 進行 OCR。
3. 所有內容組合成同一個 Markdown 檔，並附上使用說明的標頭，讓檔案交給 AI 時能自我說明。

## 卸載

把技能目錄從 CLI 的 skills 資料夾刪除即可，例如 `~/.claude/skills/document-to-markdown-skill/` 或 `~/.qoder/skills/document-to-markdown-skill/`。

## 授權

[MIT](LICENSE)
