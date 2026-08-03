"""Wiki-page-specific frontmatter schema: category, slug, title, breadcrumb parent, on top
of foundation.frontmatter's generic parse/serialize.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class WikiFrontmatter:
    category: str
    slug: str
    title: str


def validate(frontmatter: dict[str, Any]) -> WikiFrontmatter:
    """Validate a raw frontmatter dict against the wiki page schema."""
    raise NotImplementedError("stub — mirrors current Aaron K Wiki page frontmatter")
