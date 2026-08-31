"""Append a dated entry to a `## Log` section in a markdown body.

Every real ticket and roadmap node in this project accumulates a `## Log` section over its
lifetime — a bullet per dated event, newest entry first, never rewritten (this project's own
"don't rewrite history" convention). Nothing today inserts into a body at a heading; foundation/
markers.py's refresh_block() replaces a marked *region* wholesale, which is the wrong shape here
since log entries accumulate rather than getting replaced. This module is the insert-after-
heading primitive that shape needs.

Deliberately lives in `foundation`, not `services/ticket/`, even though `bht log` (BH_016) is its
first caller: roadmap nodes carry the identical `## Log` convention, and a future `bhrm log`
should reuse this rather than reimplementing it — see wiki/design/bh010-021-architecture.md.
"""

from __future__ import annotations

import re
from datetime import date

_HEADING_RE_TEMPLATE = r"^{heading}\s*$"


class BodyLogError(ValueError):
    """Raised when the requested heading isn't found in the body."""


def append_log_entry(
    body: str, entry_text: str, *, heading: str = "## Log", today: date | None = None
) -> str:
    """Insert a new `- YYYY-MM-DD: {entry_text}` bullet immediately after `heading`, before
    whatever was already there — this project's own convention is newest-entry-first (confirmed
    by every real ticket log: the most recent dated bullet is always the first one under
    `## Log`).

    `entry_text` may be multi-line/multi-paragraph; continuation lines are indented two spaces
    to nest under the bullet, matching the indentation style already used throughout this
    project's real ticket logs.

    Raises BodyLogError if `heading` doesn't appear in `body` — this never silently appends a
    new heading, since a ticket/node missing `## Log` entirely is itself worth surfacing, not
    quietly working around.
    """
    heading_re = re.compile(_HEADING_RE_TEMPLATE.format(heading=re.escape(heading)), re.MULTILINE)
    match = heading_re.search(body)
    if not match:
        raise BodyLogError(f"no {heading!r} heading found in body")

    entry_date = (today or date.today()).isoformat()
    lines = entry_text.strip("\n").split("\n")
    first, rest = lines[0], lines[1:]
    bullet = f"- {entry_date}: {first}"
    for line in rest:
        bullet += f"\n  {line}" if line else "\n"

    insert_at = match.end()
    # Skip past the heading line's own trailing newline so the new bullet lands on its own line,
    # not appended to the heading text itself.
    if insert_at < len(body) and body[insert_at] == "\n":
        insert_at += 1

    # Skip a single blank line right after the heading (this project's template convention),
    # inserting after it rather than before, so the new bullet doesn't create a second gap.
    if body[insert_at:insert_at + 1] == "\n":
        insert_at += 1

    return body[:insert_at] + bullet + "\n" + body[insert_at:]
