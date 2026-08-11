"""Generic collection over a folder of frontmatter docs: walk, filter, group only.

Rendering the collected result into a board table (BHT) or a category index (BHW) is
deliberately NOT shared — each service renders its own output. See
migration/FOUNDATION_DESIGN.md §6 ("Rendering: decided, not shared") for why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from . import frontmatter as _frontmatter

_PATH_KEY = "_path"


@dataclass
class CollectSpec:
    root: Path
    glob: str = "**/*.md"
    filter_fn: Callable[[dict[str, Any]], bool] | None = None
    group_by: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def collect(spec: CollectSpec) -> dict[str, list[dict[str, Any]]] | list[dict[str, Any]]:
    """Walk spec.root, parse frontmatter of matching files, apply filter_fn, and group_by
    the given field if set (returns a dict of group -> list) or a flat list otherwise.

    Files that don't parse as valid frontmatter documents (e.g. a stray README caught by a
    broad glob) are silently skipped — this is a rollup over a known content collection, not
    a strict validator; services/ticket and services/wiki own validation via their own
    schema.validate(). Each returned dict carries the source path under the "_path" key so a
    renderer can build Edit/Folder links without re-deriving them.
    """
    root = Path(spec.root)
    items: list[dict[str, Any]] = []

    for path in sorted(root.glob(spec.glob)):
        if not path.is_file():
            continue
        try:
            doc = _frontmatter.parse(path)
        except _frontmatter.FrontmatterError:
            continue

        item = dict(doc.frontmatter)
        item[_PATH_KEY] = path
        if spec.filter_fn is not None and not spec.filter_fn(item):
            continue
        items.append(item)

    if spec.group_by is None:
        return items

    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        key = str(item.get(spec.group_by, ""))
        grouped.setdefault(key, []).append(item)
    return grouped
