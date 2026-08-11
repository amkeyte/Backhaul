"""Wiki page creation (replacement for new_page.py): identity is just the category/slug path
— no registry, no numbering (unlike BHT) — so this mostly renders the template and writes the
file. Frontmatter is built directly from WikiFrontmatter (not templated as raw YAML text),
same reasoning as services/ticket/create.py: templating.py only renders the body.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from pathlib import Path

from backhaul.foundation import filesafety, frontmatter as _frontmatter
from backhaul.foundation import slugify, templating

from .schema import WikiFrontmatter

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "page.md.tmpl"


def create_page(
    *,
    wiki_root: str | Path,
    category: str,
    title: str,
    slug: str | None = None,
    summary: str | None = None,
    keywords: str | None = None,
    status: str = "draft",
    today: date | None = None,
) -> Path:
    """Create a new wiki page under wiki_root/<category>/<slug>.md and return its path.

    category may be nested (e.g. "reference/conventions") — each segment becomes a real
    subdirectory, since the path *is* the identity for BHW (no registry, unlike BHT's UID
    scheme). Refuses to overwrite an existing page (foundation.filesafety.safe_write's
    default behavior).
    """
    wiki_root = Path(wiki_root)
    category = category.strip("/")
    slug = slug or slugify.slugify(title)

    page_dir = wiki_root / category if category else wiki_root
    page_path = page_dir / f"{slug}.md"

    page_date = (today or date.today()).isoformat()
    page = WikiFrontmatter(
        category=category,
        slug=slug,
        title=title,
        summary=summary,
        keywords=keywords,
        status=status,
        updated=page_date,
    )

    body = templating.render_template(_TEMPLATE_PATH, {"TITLE": title, "SUMMARY": summary or ""})

    fm = dict(asdict(page))
    # Field order in the file: id first (human-scannable), then the rest as declared.
    fm = {"id": fm.pop("id"), **fm}

    content = _frontmatter.serialize(_frontmatter.ParsedDoc(frontmatter=fm, body=body))
    filesafety.safe_write(page_path, content, overwrite=False)
    return page_path
