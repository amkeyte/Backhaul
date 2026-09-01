"""Role-page creation: mint roles/<slug>.md from role.md.tmpl and write the frontmatter +
body. No registry, no numbering — identity is just the slug, same reasoning
services/wiki/create.py documents for PathIdentity: a project's role set is a short,
hand-curated list, not something that needs a counter.

Frontmatter is built directly from RoleFrontmatter (not templated as raw YAML text), same
reasoning services/ticket/create.py and modules/roadmap/create.py document — templating.py
only renders the body.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path

from backhaul.foundation import filesafety
from backhaul.foundation import frontmatter as _frontmatter
from backhaul.foundation import slugify, templating

from .schema import RoleFrontmatter

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "role.md.tmpl"


def create_role(
    *,
    roles_root: str | Path,
    title: str,
    slug: str | None = None,
    persona: str | None = None,
    purpose: str | None = None,
    authority: str | None = None,
    reports_to: str | None = None,
    status: str = "active",
    today: date | None = None,
) -> Path:
    """Create a new role page under roles_root/<slug>.md and return its path.

    `slug` defaults to a slugified `title` when omitted — either way it's run through
    slugify() so a hand-typed code can't smuggle spaces/casing into the filename, same
    convention every other content type in Backhaul uses. Refuses to overwrite an existing
    file (foundation.filesafety.safe_write's default behavior).
    """
    roles_root = Path(roles_root)
    roles_root.mkdir(parents=True, exist_ok=True)

    slug = slugify.slugify(slug) if slug else slugify.slugify(title)
    role_path = roles_root / f"{slug}.md"

    role_date = (today or date.today()).isoformat()
    role = RoleFrontmatter(
        slug=slug,
        title=title,
        persona=persona,
        purpose=purpose,
        authority=authority,
        reports_to=reports_to,
        status=status,
        updated=role_date,
    )

    body = templating.render_template(
        _TEMPLATE_PATH,
        {"TITLE": role.title, "PURPOSE": role.purpose or ""},
    )

    fm = dict(asdict(role))
    # Field order in the file: id first (human-scannable), then the rest as declared.
    fm = {"id": fm.pop("id"), **fm}

    content = _frontmatter.serialize(_frontmatter.ParsedDoc(frontmatter=fm, body=body))
    filesafety.safe_write(role_path, content, overwrite=False)
    return role_path
