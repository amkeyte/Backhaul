"""openfolder: protocol handler — opens a project folder in Explorer from a rendered link.

Mirrors editmd's structure: openfolder.vbs (decodes the URI, shells out to Explorer),
install.py (registers the protocol under HKCU — run once per machine), and the
build_uri/decode_uri wrappers below (thin re-exports of foundation.handler_uri).

Note: services/ticket/board.py builds these links directly via foundation.handler_uri with
the literal "openfolder" scheme string, not by importing this package — services depend on
foundation only, not on modules (see migration/ARCHITECTURE.md).
"""

from __future__ import annotations

from pathlib import Path

from backhaul.foundation.handler_uri import build_uri as _build_uri
from backhaul.foundation.handler_uri import decode_uri as _decode_uri

SCHEME = "openfolder"


def build_uri(path: str | Path) -> str:
    """Build an openfolder:/// URI for an absolute folder path."""
    return _build_uri(SCHEME, path)


def decode_uri(uri: str) -> str:
    """Decode an openfolder:/// URI back to a Windows path."""
    return _decode_uri(SCHEME, uri)
