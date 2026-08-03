"""Minimal template rendering for `.tmpl` files (e.g. page.md.tmpl, ticket templates).

Kept intentionally simple — plain `{{ placeholder }}` substitution, not a full templating
engine, to match the existing hand-rolled scripts this is replacing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def render_template(template_path: str | Path, context: dict[str, Any]) -> str:
    """Load a `.tmpl` file and substitute `{{ key }}` placeholders from context."""
    raise NotImplementedError("stub — see migration/FOUNDATION_DESIGN.md")
