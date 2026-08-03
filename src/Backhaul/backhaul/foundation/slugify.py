"""Slug generation shared by wiki page paths and any other slug-keyed naming."""

from __future__ import annotations


def slugify(text: str) -> str:
    """Lowercase, hyphenate, and strip a human title into a filesystem/URL-safe slug."""
    raise NotImplementedError("stub — see migration/FOUNDATION_DESIGN.md")
