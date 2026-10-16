"""HTML and EPUB converters (beautifulsoup4 + markdownify + ebooklib)."""
from __future__ import annotations

import re
from pathlib import Path

from md_utils import demote_headings, tidy


def html_to_md(html) -> str:
    """HTML fragment/document -> markdown; drops scripts and inline base64 images."""
    from bs4 import BeautifulSoup
    from bs4 import element
    from markdownify import markdownify

    if isinstance(html, bytes):
        html = html.decode("utf-8", errors="replace")
    html = re.sub(r"^\s*<\?xml[^>]*\?>", "", html)  # EPUB chapters start with this
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    # processing instructions / declarations / CDATA would otherwise render as text
    meta = (element.ProcessingInstruction, element.Declaration, element.CData)
    for node in soup.find_all(string=lambda s: isinstance(s, meta)):
        node.extract()
    for img in soup.find_all("img"):  # auto-generated alt text can contain raw newlines
        alt = img.get("alt")
        if alt:
            img["alt"] = re.sub(r"\s+", " ", alt).strip()
    md = markdownify(str(soup), heading_style="ATX")
    # inline base64 images (mammoth embeds docx images this way) bloat the .md
    md = re.sub(r"!\[[^\]]*\]\(data:[^)]*\)", "*[image]*", md)
    md = re.sub(r"\*{2,}(\*\[image\]\*)\*{2,}", r"\1", md)  # unwrap bold/italic around placeholder
    return tidy(md)


def convert_html(path: Path, log=print):
    """HTML page/file -> markdown, headings demoted so the document title stays H1."""
    md = demote_headings(html_to_md(path.read_bytes()), 1)
    return [(None, md)], {"detail": "HTML"}


def convert_epub(path: Path, log=print):
    """EPUB -> one section per spine document, titled by its first heading."""
    import ebooklib
    from bs4 import BeautifulSoup
    from ebooklib import epub

    book = epub.read_epub(str(path))
    sections: list[tuple[str, str]] = []
    for item_id, _linear in book.spine:
        item = book.get_item_with_id(item_id)
        if item is None or item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        if "nav" in item.get_name().lower():  # skip the EPUB navigation page
            continue
        soup = BeautifulSoup(item.get_content(), "html.parser")
        head = soup.find(["h1", "h2", "h3"])
        title = head.get_text(" ", strip=True) if head else ""
        if head is not None:
            head.extract()  # avoid duplicating it as both heading and body
        body = demote_headings(html_to_md(str(soup)), 1)
        if not title and not body:
            continue
        heading = title or f"Section {len(sections) + 1}"
        sections.append((heading, body))
    if not sections:
        sections = [(None, "(no readable chapters)")]
    return sections, {"detail": f"{len(sections)} chapters (epub)"}
