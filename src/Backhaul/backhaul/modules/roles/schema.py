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

#: Which `claude://` deep link a role's Launch link builds (BH_003) — "cowork" (default, today's
#: only prior behavior) opens a Cowork session; "code" opens Claude Code instead. See
#: modules/roles/launch.py's build_launch_link, which reads this field to pick between
#: foundation.claude_link's build_cowork_link/build_code_link.
LAUNCH_TARGETS = ("cowork", "code")

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
    launch_target: str = "cowork"
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

    launch_target = frontmatter.get("launch_target") or "cowork"
    if launch_target not in LAUNCH_TARGETS:
        raise RoleValidationError(
            f"role page launch_target {launch_target!r} is not one of {LAUNCH_TARGETS}"
        )

    return RoleFrontmatter(
        slug=str(frontmatter["slug"]),
        title=str(frontmatter["title"]),
        id=str(frontmatter.get("id") or ""),
        persona=frontmatter.get("persona") or None,
        purpose=frontmatter.get("purpose") or None,
        authority=frontmatter.get("authority") or None,
        reports_to=frontmatter.get("reports_to") or None,
        status=status,
        launch_target=launch_target,
        updated=frontmatter.get("updated"),
    )
