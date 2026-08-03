"""YAML frontmatter + markdown body parsing, shared by tickets and wiki pages.

Both BHT (passdown tickets) and BHW (wiki pages) are `--- yaml ---` + markdown body files.
This module owns the generic split/parse/serialize logic; domain-specific field validation
(e.g. required ticket fields vs. required wiki fields) lives in services/ticket/schema.py
and services/wiki/schema.py respectively.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ParsedDoc:
    frontmatter: dict[str, Any]
    body: str
    path: Path


def parse(path: str | Path) -> ParsedDoc:
    """Read a markdown file and split it into frontmatter dict + body text."""
    raise NotImplementedError("stub — see migration/FOUNDATION_DESIGN.md")


def serialize(doc: ParsedDoc) -> str:
    """Render a ParsedDoc back to `---\\nyaml\\n---\\nbody` text."""
    raise NotImplementedError("stub — see migration/FOUNDATION_DESIGN.md")


def write(doc: ParsedDoc) -> None:
    """Serialize and write a ParsedDoc back to its own path."""
    raise NotImplementedError("stub — see migration/FOUNDATION_DESIGN.md")
