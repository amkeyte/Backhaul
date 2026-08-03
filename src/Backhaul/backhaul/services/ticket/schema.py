"""Ticket-specific frontmatter schema and validation: required fields (uid, number, client,
status, title, context, opened/closed dates, etc.) on top of foundation.frontmatter's generic
parse/serialize.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TicketFrontmatter:
    uid: str
    number: int
    client: str
    status: str
    title: str


def validate(frontmatter: dict[str, Any]) -> TicketFrontmatter:
    """Validate a raw frontmatter dict against the ticket schema, raising on missing fields."""
    raise NotImplementedError("stub — mirrors current Aaron K _passdown ticket fields")
