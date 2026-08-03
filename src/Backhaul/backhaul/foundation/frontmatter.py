"""YAML frontmatter + markdown body parsing, shared by tickets and wiki pages.

Both BHT (passdown tickets) and BHW (wiki pages) are `--- yaml ---` + markdown body files.
This module owns the generic split/parse/serialize logic; domain-specific field validation
(e.g. required ticket fields vs. required wiki fields) lives in services/ticket/schema.py
and services/wiki/schema.py respectively.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.DOTALL)


class FrontmatterError(ValueError):
    """Raised when a file doesn't start with a valid `---yaml---` frontmatter block."""


@dataclass
class ParsedDoc:
    frontmatter: dict[str, Any] = field(default_factory=dict)
    body: str = ""
    path: Path | None = None


def parse(path: str | Path) -> ParsedDoc:
    """Read a markdown file and split it into frontmatter dict + body text.

    Raises FrontmatterError if the file doesn't open with a `---` delimited YAML block.
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")

    match = _FM_RE.match(text)
    if not match:
        raise FrontmatterError(f"{p}: no leading '---' YAML frontmatter block found")

    raw_yaml, body = match.groups()
    fm = yaml.safe_load(raw_yaml) or {}
    if not isinstance(fm, dict):
        raise FrontmatterError(f"{p}: frontmatter block did not parse to a mapping")

    return ParsedDoc(frontmatter=fm, body=body, path=p)


def serialize(doc: ParsedDoc) -> str:
    """Render a ParsedDoc back to `---\\nyaml\\n---\\nbody` text."""
    raw_yaml = yaml.safe_dump(
        doc.frontmatter, sort_keys=False, default_flow_style=False, allow_unicode=True
    ).rstrip("\n")
    body = doc.body if doc.body.startswith("\n") else "\n" + doc.body
    return f"---\n{raw_yaml}\n---\n{body}"


def write(doc: ParsedDoc) -> None:
    """Serialize and write a ParsedDoc back to its own path."""
    if doc.path is None:
        raise FrontmatterError("cannot write a ParsedDoc with no path set")
    doc.path.write_text(serialize(doc), encoding="utf-8")
