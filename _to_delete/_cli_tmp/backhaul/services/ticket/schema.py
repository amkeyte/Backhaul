"""Ticket-specific frontmatter schema and validation: required fields (uid, number, client,
status, title, context, opened/closed dates, etc.) on top of foundation.frontmatter's generic
parse/serialize.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backhaul.foundation.identity import NumberedIdentity

#: Lifecycle states, per migration/ARCHITECTURE.md: open -> in-progress|blocked -> done.
STATES = ("open", "in-progress", "blocked", "done")
#: Statuses that stay on the board. "done" tickets are excluded but stay on disk.
OPEN_STATES = ("open", "in-progress", "blocked")

_REQUIRED_FIELDS = ("uid", "number", "client", "status", "title")


class TicketValidationError(ValueError):
    """Raised when a ticket's frontmatter is missing required fields or has an invalid status."""


@dataclass
class TicketFrontmatter:
    uid: str
    number: int
    client: str
    status: str
    title: str
    id: str = ""
    context: str | None = None
    priority: str = "normal"
    opened: str | None = None
    closed: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(NumberedIdentity(uid=self.uid, number=self.number))


def validate(frontmatter: dict[str, Any]) -> TicketFrontmatter:
    """Validate a raw frontmatter dict against the ticket schema, raising on missing fields."""
    missing = [
        f for f in _REQUIRED_FIELDS if f not in frontmatter or frontmatter[f] in (None, "")
    ]
    if missing:
        raise TicketValidationError(
            f"ticket frontmatter missing required field(s): {', '.join(missing)}"
        )

    status = frontmatter["status"]
    if status not in STATES:
        raise TicketValidationError(f"ticket status {status!r} is not one of {STATES}")

    try:
        number = int(frontmatter["number"])
    except (TypeError, ValueError) as e:
        raise TicketValidationError(
            f"ticket 'number' must be an integer, got {frontmatter['number']!r}"
        ) from e

    return TicketFrontmatter(
        uid=str(frontmatter["uid"]),
        number=number,
        client=str(frontmatter["client"]),
        status=status,
        title=str(frontmatter["title"]),
        id=str(frontmatter.get("id") or ""),
        context=frontmatter.get("context") or None,
        priority=str(frontmatter.get("priority") or "normal"),
        opened=frontmatter.get("opened"),
        closed=frontmatter.get("closed"),
    )
