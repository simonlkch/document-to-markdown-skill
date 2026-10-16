"""Shared helpers for Markdown assembly."""
from __future__ import annotations

import re


def tidy(text: str) -> str:
    """Normalise whitespace: \r\n -> \n, strip trailing spaces, collapse 3+ blank lines."""
    text = text.replace("\x0c", "\n").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def demote_headings(md: str, levels: int = 1) -> str:
    """Push every ATX heading down `levels` so the document title stays the only H1."""
    def repl(m):
        return "#" * min(len(m.group(1)) + levels, 6) + " "
    return re.sub(r"^(#{1,5}) ", repl, md, flags=re.M)


def md_table(rows: list[list]) -> str:
    """Rows -> GitHub pipe table. The first row is used as the header."""
    if not rows:
        return ""

    def esc(cell) -> str:
        c = "" if cell is None else str(cell)
        return c.replace("|", "\\|").replace("\n", " ").strip()

    header = [esc(c) for c in rows[0]]
    if not header:
        return ""
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("---" for _ in header) + "|"]
    for r in rows[1:]:
        cells = [esc(c) for c in r[:len(header)]]
        cells += [""] * (len(header) - len(cells))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)
