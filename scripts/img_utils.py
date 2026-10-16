"""Shared helpers for --images: save embedded images next to the output .md.

Images land in a `<output stem>_images/` folder beside the markdown file and
are referenced with relative paths (image1.png, image2.jpg, ...).
"""
from __future__ import annotations

import hashlib
from itertools import count
from pathlib import Path
from urllib.parse import quote

MIME_EXT = {
    "image/png": "png", "image/jpeg": "jpg", "image/jpg": "jpg",
    "image/gif": "gif", "image/bmp": "bmp", "image/tiff": "tiff",
    "image/webp": "webp", "image/x-emf": "emf", "image/emf": "emf",
    "image/x-wmf": "wmf", "image/wmf": "wmf",
}
EXT_ALIASES = {"jpeg": "jpg", "tif": "tiff", "svg+xml": "svg"}


def ext_from_mime(mime: str) -> str:
    """'image/png' -> 'png'; unknown types fall back to a sanitized subtype."""
    mime = (mime or "").lower().strip()
    if mime in MIME_EXT:
        return MIME_EXT[mime]
    ext = mime.rsplit("/", 1)[-1]
    ext = "".join(c for c in ext if c.isalnum() or c == "+")
    return EXT_ALIASES.get(ext, ext) or "bin"


def norm_ext(ext: str) -> str:
    """Normalize a bare extension ('jpeg' -> 'jpg', '.PNG' -> 'png')."""
    ext = (ext or "").lower().lstrip(".")
    return EXT_ALIASES.get(ext, ext) or "png"


class ImageSink:
    """Writes images into `dir` as imageN.<ext>; returns markdown-relative srcs.

    Identical bytes are stored once (hash dedup) and the link is URL-encoded,
    so folders with spaces or non-ASCII names still produce valid markdown.
    """

    def __init__(self, images_dir: Path, prefix: str):
        self.dir = Path(images_dir)
        self.prefix = prefix
        self.saved = 0
        self._n = count(1)
        self._by_hash: dict[str, str] = {}

    def save(self, data: bytes, ext: str) -> str:
        key = hashlib.md5(data).hexdigest()
        existing = self._by_hash.get(key)
        if existing:
            return existing
        ext = norm_ext(ext)
        self.dir.mkdir(parents=True, exist_ok=True)
        name = f"image{next(self._n)}.{ext}"
        (self.dir / name).write_bytes(data)
        self.saved += 1
        src = quote(f"{self.prefix}/{name}", safe="/")
        self._by_hash[key] = src
        return src

    def save_mime(self, data: bytes, mime: str) -> str:
        return self.save(data, ext_from_mime(mime))
