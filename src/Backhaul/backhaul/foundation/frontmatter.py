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


class FrontmatterParseError(FrontmatterError):
    """Raised when a file's `---yaml---` block exists but doesn't parse as valid YAML — e.g. an
    unquoted scalar containing `: ` (colon-space), which YAML reads as a second mapping key
    inside the value position. Subclasses FrontmatterError so existing `except FrontmatterError`
    call sites (e.g. the various `_cmd_refresh` per-file loops, which skip a file that doesn't
    parse rather than aborting the whole run) keep working unchanged. See BH_020: a writer going
    through this module's own `serialize()` already can't produce this (yaml.safe_dump quotes
    a colon-space scalar automatically), so this only ever fires on a hand-edited file — the
    point of this class over a bare YAMLError is naming *which* file, since a rollup over dozens
    of files gives no other way to tell."""


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
    try:
        fm = yaml.safe_load(raw_yaml) or {}
    except yaml.YAMLError as e:
        raise FrontmatterParseError(
            f"{p}: frontmatter block is not valid YAML ({e}). A common cause is an unquoted "
            f"value containing ': ' (colon-space) — YAML reads that as a second mapping key. "
            f"Quote the value (e.g. title: 'Border load count: client vs server') and retry."
        ) from e
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
