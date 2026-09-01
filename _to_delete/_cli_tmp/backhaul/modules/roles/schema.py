"""Role-page frontmatter schema, on top of foundation.frontmatter's generic parse/serialize.
Mirrors services/wiki/schema.py's shape (flat slug identity, no numbering, no registry) —
a project's role set is a short, hand-curated list, not something that needs a counter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: Lifecycle states — informational only, same convention wiki page status uses (never gates
#: inclusion in the roster; a "retired" role just reads as such in ROLES_INDEX.md).
STATES = ("active", "retired")

_REQUIRED_FIELDS = ("slug", "title")


class RoleValidationError(ValueError):
    """Raised when a role page's frontmatter is missing required fields or has a bad status."""


@dataclass
class RoleFrontmatter:
    slug: str
    title: str
    id: str = ""
    persona: str | None = None
    purpose: str | None = None
    authority: str | None = None
    reports_to: str | None = None
    status: str = "active"
    updated: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = self.slug


def validate(frontmatter: dict[str, Any]) -> RoleFrontmatter:
    """Validate a raw frontmatter dict against the role-page schema, raising on missing
    fields or an invalid status."""
    missing = [
        f for f in _REQUIRED_FIELDS if f not in frontmatter or frontmatter[f] in (None, "")
    ]
    if missing:
        raise RoleValidationError(
            f"role page frontmatter missing required field(s): {', '.join(missing)}"
        )

    status = frontmatter.get("status") or "active"
    if status not in STATES:
        raise RoleValidationError(f"role page status {status!r} is not one of {STATES}")

    return RoleFrontmatter(
        slug=str(frontmatter["slug"]),
        title=str(frontmatter["title"]),
        id=str(frontmatter.get("id") or ""),
        persona=frontmatter.get("persona") or None,
        purpose=frontmatter.get("purpose") or None,
        authority=frontmatter.get("authority") or None,
        reports_to=frontmatter.get("reports_to") or None,
        status=status,
        updated=frontmatter.get("updated"),
    )
