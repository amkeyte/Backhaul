"""Slug generation shared by wiki page paths and any other slug-keyed naming."""

from __future__ import annotations

import re

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str, maxlen: int = 40) -> str:
    """Lowercase, hyphenate, and strip a human title into a filesystem/URL-safe slug.

    Non-alphanumeric runs collapse to a single '-', leading/trailing '-' is trimmed, and the
    result is capped at maxlen characters (trimmed again after truncation so it never ends on
    a dangling hyphen).
    """
    slug = _NON_ALNUM_RE.sub("-", text.strip().lower()).strip("-")
    if maxlen and len(slug) > maxlen:
        slug = slug[:maxlen].rstrip("-")
    return slug
