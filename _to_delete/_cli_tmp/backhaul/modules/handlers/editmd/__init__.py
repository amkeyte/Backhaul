"""editmd: protocol handler — opens a markdown file in Notepad++ from a rendered link.

Three pieces: editmd.vbs (decodes the URI, shells out to Notepad++), install.py (registers
the protocol under HKCU — run once per machine), and the build_uri/decode_uri wrappers below
(thin re-exports of foundation.handler_uri, scoped to this module's scheme).

Note: services/ticket/board.py builds these links directly via foundation.handler_uri with
the literal "editmd" scheme string, not by importing this package — services depend on
foundation only, not on modules (see migration/ARCHITECTURE.md). These wrappers are for
anything else (scripts, other modules, a future BHW) that wants an editmd: link without
duplicating the scheme string.
"""

from __future__ import annotations

from pathlib import Path

from backhaul.foundation.handler_uri import build_uri as _build_uri
from backhaul.foundation.handler_uri import decode_uri as _decode_uri

SCHEME = "editmd"


def build_uri(path: str | Path) -> str:
    """Build an editmd:/// URI for an absolute file path."""
    return _build_uri(SCHEME, path)


def decode_uri(uri: str) -> str:
    """Decode an editmd:/// URI back to a Windows path."""
    return _decode_uri(SCHEME, uri)
