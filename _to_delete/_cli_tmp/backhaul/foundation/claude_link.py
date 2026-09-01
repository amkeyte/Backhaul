"""Deep links into Claude Desktop via its `claude://` URL scheme.

Confirmed real and documented: https://support.claude.com/en/articles/14729294 — Claude for
macOS, Windows, and Linux responds to `claude://` the way a browser responds to `https://`.
`claude://cowork/new?q=<prompt>&folder=<path>` opens a new Cowork session with the composer
prefilled and the folder attached (Claude Desktop shows a confirmation dialog before adopting
the folder — safe by design, so embedding a real path here is fine).

No OS-side registration needed on Backhaul's part, unlike `editmd:`/`openfolder:`
(modules/handlers/) — Claude Desktop's own installer already owns this scheme. This module only
builds the URL text; nothing here shells out to anything.

Kept in foundation (not a module) for the same reason handler_uri.py is: a generic primitive
any service's renderer can use, not something specific to one module — see
migration/ARCHITECTURE.md.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

#: Prompt text passed in `q` is truncated by Claude Desktop to roughly 14,000 characters —
#: see the support article above. Not enforced here (a caller with a too-long prompt should
#: know, not be silently truncated a second time); exposed as a constant for callers/tests.
Q_TRUNCATION_LIMIT = 14_000


def build_cowork_link(prompt: str, *, folder: str | Path | None = None) -> str:
    """Build a `claude://cowork/new` deep link that opens a new Cowork session with `prompt`
    prefilled in the composer, and `folder` attached if given.

    `folder` is expected to already be an absolute, real path for the machine that link will
    actually be clicked on — not resolved or validated here, same reasoning as
    handler_uri.build_uri's path handling (this is pure text building, no filesystem access).
    """
    url = f"claude://cowork/new?q={quote(prompt)}"
    if folder is not None:
        url += f"&folder={quote(str(folder))}"
    return url


def build_code_link(prompt: str, *, folder: str | Path | None = None) -> str:
    """Build a `claude://code/new` deep link — same shape as build_cowork_link, but opens a
    Claude Code session instead of a Cowork session. Not used by modules/roles today, but
    kept alongside it since it's the same mechanism with a different host segment."""
    url = f"claude://code/new?q={quote(prompt)}"
    if folder is not None:
        url += f"&folder={quote(str(folder))}"
    return url
