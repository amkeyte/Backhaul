"""Wiki-page-specific frontmatter schema: category, slug, title, breadcrumb parent, on top
of foundation.frontmatter's generic parse/serialize.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backhaul.foundation.identity import PathIdentity

#: Lifecycle states, per migration/ARCHITECTURE.md: draft -> verified/published.
#: Informational only — unlike ticket status, this never gates inclusion in the index.
STATES = ("draft", "verified", "published")

_REQUIRED_FIELDS = ("category", "slug", "title")


class WikiValidationError(ValueError):
    """Raised when a wiki page's frontmatter is missing required fields or has a bad status."""


@dataclass
class WikiFrontmatter:
    category: str
    slug: str
    title: str
    id: str = ""
    summary: str | None = None
    keywords: str | None = None
    status: str = "draft"
    updated: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(PathIdentity(category=self.category, slug=self.slug))


def validate(frontmatter: dict[str, Any]) -> WikiFrontmatter:
    """Validate a raw frontmatter dict against the wiki page schema, raising on missing fields."""
    missing = [
        f for f in _REQUIRED_FIELDS if f not in frontmatter or frontmatter[f] in (None, "")
    ]
    if missing:
        raise WikiValidationError(
            f"wiki page frontmatter missing required field(s): {', '.join(missing)}"
        )

    status = frontmatter.get("status") or "draft"
    if status not in STATES:
        raise WikiValidationError(f"wiki page status {status!r} is not one of {STATES}")

    return WikiFrontmatter(
        category=str(frontmatter["category"]),
        slug=str(frontmatter["slug"]),
        title=str(frontmatter["title"]),
        id=str(frontmatter.get("id") or ""),
        summary=frontmatter.get("summary") or None,
        keywords=frontmatter.get("keywords") or None,
        status=status,
        updated=frontmatter.get("updated"),
    )
