"""Turns a role page's own "Session bootstrap prompt" section into a clickable
`claude://cowork/new` deep link (foundation/claude_link.py) — click it, Claude Desktop opens a
new Cowork session with that role's bootstrap prompt already in the composer, ready to review
and send.

Deliberately does NOT pass `folder=` on this link. Observed behavior (2026-08-11, Windows,
Claude Desktop): `q` alone reliably lands in the composer, but `q` combined with `folder`
causes the composer to flash the prefilled text and then silently clear itself before the user
can send it — the folder-confirmation step in that flow appears to reset composer state. `q`
without `folder` doesn't have this problem. Rather than auto-attaching the folder, the project
root (when known) is prepended as a plain line inside the prompt text itself, telling the role
which folder it needs and asking it to request that the user attach it — same information,
delivered a way that doesn't fight the composer's reset behavior. If Claude Desktop's handling
of `q`+`folder` together improves, this can revisit auto-attaching again.

Extraction only looks at the first fenced code block following a "## Session bootstrap
prompt" heading (case-insensitive) — the exact shape role.md.tmpl scaffolds. A role page
without that section (or without a fenced block under it) just doesn't get a Launch link;
this is never a hard error, since plenty of legitimate role pages might not have gotten to
writing their bootstrap prompt yet.
"""

from __future__ import annotations

import re
from pathlib import Path

from backhaul.foundation import claude_link
from backhaul.foundation import frontmatter as _frontmatter

_SECTION_RE = re.compile(
    r"^#{1,6}\s*session bootstrap prompt\s*$", re.IGNORECASE | re.MULTILINE
)
_FENCE_RE = re.compile(r"```(?:[^\n]*)\n(.*?)```", re.DOTALL)


def extract_bootstrap_prompt(body: str) -> str | None:
    """Return the literal text of the first fenced code block under a "## Session bootstrap
    prompt" heading, or None if that section (or a fenced block within it) isn't present.
    """
    section_match = _SECTION_RE.search(body)
    if not section_match:
        return None

    remainder = body[section_match.end():]
    fence_match = _FENCE_RE.search(remainder)
    if not fence_match:
        return None

    prompt = fence_match.group(1).strip("\n")
    return prompt or None


def build_launch_link(role_path: str | Path, *, project_root: str | Path | None = None) -> str | None:
    """Read a role page's bootstrap prompt and build its claude://cowork/new launch link, or
    return None if the page has no bootstrap-prompt section to launch from.

    `project_root`, if given, is prepended to the prompt text as a plain instruction naming the
    folder this role needs and asking the agent to request it from the user — NOT passed as the
    link's `folder=` param (see module docstring for why: `q`+`folder` together were observed to
    clear the composer instead of prefilling it). Expected to already be an absolute, real path
    for the machine the link will actually be clicked on — pure text, no filesystem access here.
    """
    doc = _frontmatter.parse(Path(role_path))
    prompt = extract_bootstrap_prompt(doc.body)
    if prompt is None:
        return None
    if project_root is not None:
        prompt = (
            f"This role's project folder is {project_root} — if you don't already have file "
            "access to it, ask me to attach it before reading anything.\n\n"
        ) + prompt
    return claude_link.build_cowork_link(prompt)
