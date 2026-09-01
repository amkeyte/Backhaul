"""Roadmap node frontmatter schema and validation, on top of foundation.frontmatter's generic
parse/serialize. Mirrors services/ticket/schema.py's shape (TicketFrontmatter ->
RoadmapNodeFrontmatter), adapted for two node kinds with different status vocabularies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backhaul.foundation.identity import NumberedIdentity

#: A node's Kind is set once at creation and never changes (per node-format-spec.md).
KINDS = ("work", "convergence")

#: Work nodes are terminal once left "open" — "resolved"/"superseded" are permanent.
WORK_STATES = ("open", "resolved", "superseded")
#: Convergence nodes are the one place status is genuinely reversible.
CONVERGENCE_STATES = ("WIP", "reached")

#: Statuses that still count as "not yet settled" for a given kind — used by graph.py's
#: frontier/actionable computation (work: open; convergence: WIP).
OPEN_STATUS = {"work": "open", "convergence": "WIP"}
#: Statuses that satisfy a DependsOn entry pointing at this node (work: resolved;
#: convergence: reached).
SATISFYING_STATUS = {"work": "resolved", "convergence": "reached"}

_REQUIRED_FIELDS = ("uid", "number", "kind", "status", "title", "owner")


class RoadmapValidationError(ValueError):
    """Raised when a roadmap node's frontmatter is missing required fields or has an invalid
    kind/status/status-for-kind combination."""


@dataclass
class RoadmapNodeFrontmatter:
    uid: str
    number: int
    kind: str
    status: str
    title: str
    owner: str
    id: str = ""
    depends_on: list[str] = field(default_factory=list)
    created: str | None = None
    superseded_by: str | None = None
    ticket: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(NumberedIdentity(uid=self.uid, number=self.number))


def validate(frontmatter: dict[str, Any]) -> RoadmapNodeFrontmatter:
    """Validate a raw frontmatter dict against the roadmap node schema, raising on missing
    fields, an unknown kind, or a status that isn't valid for that kind."""
    missing = [
        f for f in _REQUIRED_FIELDS if f not in frontmatter or frontmatter[f] in (None, "")
    ]
    if missing:
        raise RoadmapValidationError(
            f"roadmap node frontmatter missing required field(s): {', '.join(missing)}"
        )

    kind = frontmatter["kind"]
    if kind not in KINDS:
        raise RoadmapValidationError(f"roadmap node kind {kind!r} is not one of {KINDS}")

    status = frontmatter["status"]
    valid_states = WORK_STATES if kind == "work" else CONVERGENCE_STATES
    if status not in valid_states:
        raise RoadmapValidationError(
            f"roadmap node status {status!r} is not valid for kind {kind!r} (expected one of {valid_states})"
        )

    if status == "superseded" and not frontmatter.get("superseded_by"):
        raise RoadmapValidationError(
            "roadmap node status is 'superseded' but 'superseded_by' is not set"
        )

    try:
        number = int(frontmatter["number"])
    except (TypeError, ValueError) as e:
        raise RoadmapValidationError(
            f"roadmap node 'number' must be an integer, got {frontmatter['number']!r}"
        ) from e

    depends_on = frontmatter.get("depends_on") or []
    if not isinstance(depends_on, list) or not all(isinstance(d, str) for d in depends_on):
        raise RoadmapValidationError("roadmap node 'depends_on' must be a list of ID strings")

    return RoadmapNodeFrontmatter(
        uid=str(frontmatter["uid"]),
        number=number,
        kind=kind,
        status=status,
        title=str(frontmatter["title"]),
        owner=str(frontmatter["owner"]),
        id=str(frontmatter.get("id") or ""),
        depends_on=list(depends_on),
        created=frontmatter.get("created"),
        superseded_by=frontmatter.get("superseded_by"),
        ticket=frontmatter.get("ticket"),
    )
