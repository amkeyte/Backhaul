"""Roadmap node creation: mint an identity (RM_<base_uid>_NNN), render the body from
node.md.tmpl, write the frontmatter + body, and register the client's base UID on first use.

Frontmatter is built directly from RoadmapNodeFrontmatter (not templated as raw YAML text) so
title/owner strings with colons, quotes, etc. can't corrupt the YAML block — same reasoning
services/ticket/create.py documents; templating.py only renders the body.
"""

from __future__ import annotations

import re
from dataclasses import asdict
from datetime import date
from pathlib import Path

from backhaul.foundation import client_registry, filesafety
from backhaul.foundation import frontmatter as _frontmatter
from backhaul.foundation import identity, slugify, templating

from .schema import OPEN_STATUS, RoadmapNodeFrontmatter

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "node.md.tmpl"
_ID_PREFIX_RE = re.compile(r"^([A-Za-z0-9_]+)_(\d+)")


def _existing_numbers(nodes_root: Path, uid: str) -> list[int]:
    numbers = []
    for path in nodes_root.glob(f"{uid}_*.md"):
        match = _ID_PREFIX_RE.match(path.name)
        if match and match.group(1) == uid:
            numbers.append(int(match.group(2)))
    return numbers


def create_node(
    *,
    nodes_root: str | Path,
    registry_path: str | Path,
    client: str,
    title: str,
    owner: str,
    kind: str = "work",
    depends_on: list[str] | None = None,
    base_uid: str | None = None,
    slug: str | None = None,
    status: str | None = None,
    today: date | None = None,
) -> Path:
    """Create a new roadmap node file under nodes_root and return its path.

    `base_uid` is the client's short code — by convention the *same* code BHT uses for that
    client (looked up/minted via registry_path, which the CLI points at the same client-uids.md
    tickets already use, so "ARR" means the same client whether it's a ticket or a node). The
    node's own uid is "RM_" + base_uid, so a roadmap graph and a ticket ledger never collide on
    ID space despite sharing one client registry.

    `slug` lets the filename carry a short, easy-to-reference code (e.g. "alma") instead of the
    full title slugified — the recommended convention for roadmap nodes specifically, since a
    long descriptive slug makes DependsOn edges and cross-references harder to type/read than
    tickets' one-off filenames tend to need. Defaults to slugify(title) when omitted; either way
    the value is run through slugify() so a hand-typed code can't smuggle spaces/casing into the
    filename. Refuses to overwrite an existing file (foundation.filesafety.safe_write's default
    behavior).
    """
    nodes_root = Path(nodes_root)
    nodes_root.mkdir(parents=True, exist_ok=True)

    if base_uid is None:
        base_uid = client_registry.find_uid(registry_path, client) or client_registry.suggest_uid(client)
    client_registry.register_uid(registry_path, base_uid, client)

    uid = f"RM_{base_uid}"
    number = identity.next_number(uid, _existing_numbers(nodes_root, uid))
    ident = identity.NumberedIdentity(uid=uid, number=number)
    slug = slugify.slugify(slug) if slug else slugify.slugify(title)
    filename = f"{ident}_{slug}.md" if slug else f"{ident}.md"
    node_path = nodes_root / filename

    node_date = (today or date.today()).isoformat()
    if status is None:
        status = OPEN_STATUS[kind]

    node = RoadmapNodeFrontmatter(
        uid=uid,
        number=number,
        kind=kind,
        status=status,
        title=title,
        owner=owner,
        depends_on=depends_on or [],
        created=node_date,
    )

    body = templating.render_template(
        _TEMPLATE_PATH,
        {
            "ID": node.id,
            "TITLE": node.title,
            "KIND": node.kind,
            "STATUS": node.status,
            "OWNER": node.owner,
            "DATE": node_date,
        },
    )

    fm = {k: v for k, v in asdict(node).items()}
    # Field order in the file: id first (human-scannable), then the rest as declared.
    fm = {"id": fm.pop("id"), **fm}

    content = _frontmatter.serialize(_frontmatter.ParsedDoc(frontmatter=fm, body=body))
    filesafety.safe_write(node_path, content, overwrite=False)
    return node_path
