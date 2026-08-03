"""Generic collection over a folder of frontmatter docs: walk, filter, group only.

Rendering the collected result into a board table (BHT) or a category index (BHW) is
deliberately NOT shared — each service renders its own output. See
migration/FOUNDATION_DESIGN.md §6 ("Rendering: decided, not shared") for why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


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
    """
    raise NotImplementedError("stub — see migration/FOUNDATION_DESIGN.md")
