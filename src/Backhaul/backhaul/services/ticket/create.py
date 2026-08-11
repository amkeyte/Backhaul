"""Ticket creation (replacement for new_ticket.py): mint an identity, render the body from
ticket.md.tmpl, write the frontmatter + body, and register the client's UID on first use.

Frontmatter is built directly from TicketFrontmatter (not templated as raw YAML text) so
title/context strings with colons, quotes, etc. can't corrupt the YAML block — templating.py
only renders the body, which foundation.frontmatter then wraps with a proper YAML dump.
"""

from __future__ import annotations

import re
from dataclasses import asdict
from datetime import date
from pathlib import Path

from backhaul.foundation import filesafety, frontmatter as _frontmatter
from backhaul.foundation import identity, slugify, templating

from . import registry
from .schema import TicketFrontmatter

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "ticket.md.tmpl"
_ID_PREFIX_RE = re.compile(r"^([A-Za-z0-9]+)_(\d+)")


def _existing_numbers(tickets_root: Path, uid: str) -> list[int]:
    numbers = []
    for path in tickets_root.glob(f"{uid}_*.md"):
        match = _ID_PREFIX_RE.match(path.name)
        if match and match.group(1) == uid:
            numbers.append(int(match.group(2)))
    return numbers


def create_ticket(
    *,
    tickets_root: str | Path,
    registry_path: str | Path,
    client: str,
    title: str,
    uid: str | None = None,
    context: str | None = None,
    priority: str = "normal",
    today: date | None = None,
) -> Path:
    """Create a new ticket file under tickets_root and return its path.

    If uid isn't given, it's looked up in the client-uids.md registry by client name, or
    auto-suggested and registered if this is the first ticket for that client. Refuses to
    overwrite an existing file (foundation.filesafety.safe_write's default behavior).
    """
    tickets_root = Path(tickets_root)
    tickets_root.mkdir(parents=True, exist_ok=True)

    if uid is None:
        uid = registry.find_uid(registry_path, client) or registry.suggest_uid(client)
    registry.register_uid(registry_path, uid, client)

    number = identity.next_number(uid, _existing_numbers(tickets_root, uid))
    ident = identity.NumberedIdentity(uid=uid, number=number)
    slug = slugify.slugify(title)
    filename = f"{ident}_{slug}.md" if slug else f"{ident}.md"
    ticket_path = tickets_root / filename

    ticket_date = (today or date.today()).isoformat()
    ticket = TicketFrontmatter(
        uid=uid,
        number=number,
        client=client,
        status="open",
        title=title,
        context=context,
        priority=priority,
        opened=ticket_date,
    )

    body = templating.render_template(
        _TEMPLATE_PATH,
        {
            "ID": ticket.id,
            "UID": ticket.uid,
            "NUMBER": ticket.number,
            "CLIENT": ticket.client,
            "TITLE": ticket.title,
            "STATUS": ticket.status,
            "PRIORITY": ticket.priority,
            "CONTEXT": ticket.context or "",
            "DATE": ticket_date,
        },
    )

    fm = {k: v for k, v in asdict(ticket).items()}
    # Field order in the file: id first (human-scannable), then the rest as declared.
    fm = {"id": fm.pop("id"), **fm}

    content = _frontmatter.serialize(_frontmatter.ParsedDoc(frontmatter=fm, body=body))
    filesafety.safe_write(ticket_path, content, overwrite=False)
    return ticket_path
