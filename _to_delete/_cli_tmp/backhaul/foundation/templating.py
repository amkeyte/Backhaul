"""Minimal template rendering for `.tmpl` files (e.g. page.md.tmpl, ticket templates).

Kept intentionally simple — plain `{{ placeholder }}` substitution, not a full templating
engine, to match the existing hand-rolled scripts this is replacing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class TemplateError(Exception):
    """Raised when a template references a key not present in the given context."""


def render_template(template_path: str | Path, context: dict[str, Any]) -> str:
    """Load a `.tmpl` file and substitute `{{ key }}` placeholders from context.

    Raises TemplateError if the template references a key that isn't in context — a silently
    unfilled placeholder in a generated ticket/wiki page is worse than a loud failure here.
    """
    text = Path(template_path).read_text(encoding="utf-8")

    def _sub(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            raise TemplateError(f"{template_path}: template references unknown key '{key}'")
        return str(context[key])

    return _PLACEHOLDER_RE.sub(_sub, text)
