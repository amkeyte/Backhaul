"""Generic `<scheme>:///<path>` URI building for Windows custom-protocol handlers
(editmd:, openfolder:, ...) that let Chrome-rendered markdown launch local Windows programs.

Pure string manipulation — no OS-specific path resolution (no Path.resolve(), no filesystem
checks) — so it produces the same result whether generated on Windows or in a Linux dev
sandbox, and is honestly unit-testable without a real Windows machine.

The actual OS integration (registry entry + VBScript that decodes this URI and shells out to
notepad++.exe / explorer.exe) lives in modules/handlers/<name>/ — this module only builds and
parses the URI text both sides agree on. Kept in foundation (not a module) because it's a
generic primitive any service's renderer can use, not something specific to BHT or BHW; see
migration/ARCHITECTURE.md — services depend on foundation, not on modules.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, unquote


def build_uri(scheme: str, path: str | Path) -> str:
    """Build a `<scheme>:///<forward-slash-path>` URI for an absolute Windows path.

    Mirrors the `file:///C:/...` convention: backslashes become forward slashes, then the
    whole thing is percent-encoded except for `/` and `:` (so `C:/Program Files/...` stays
    readable but a literal space still round-trips through a browser-rendered link).
    """
    forward = str(path).replace("\\", "/")
    encoded = quote(forward, safe="/:")
    return f"{scheme}:///{encoded}"


def decode_uri(scheme: str, uri: str) -> str:
    """Inverse of build_uri — decode a `<scheme>:///...` URI back to a Windows path.

    Exists so the encode/decode round-trip has real test coverage; the decoding that
    actually matters on a user's machine happens in modules/handlers/<name>/<name>.vbs
    (VBScript has no built-in URL-decode, so that copy is hand-rolled — keep it in sync with
    this function's semantics if either changes).
    """
    prefix = f"{scheme}:///"
    if not uri.startswith(prefix):
        raise ValueError(f"not a {scheme}: URI: {uri!r}")
    forward = unquote(uri[len(prefix):])
    return forward.replace("/", "\\")
