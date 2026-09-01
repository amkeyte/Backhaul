"""client-uids.md registry: maps short UID codes (GEN, UW, ...) to client display names.

BHT's identity.NumberedIdentity scopes ticket numbering per UID; this registry is where a UID
gets minted the first time a client is seen, and looked up on every ticket after that. Mirrors
the role of the current Aaron K `_passdown/client-uids.md` file (per migration/MIGRATION_PLAN.md
§4) but lives under each machine's configured tickets content root, not in this repo.

The generic ledger logic (load/find/register/suggest) now lives in
foundation/client_registry.py, since modules/roadmap needs it too and a module can't depend on
a service — see that module's docstring. Re-exported here unchanged so existing BHT code and
tests keep working against `registry.<name>` exactly as before.
"""

from __future__ import annotations

from pathlib import Path

from backhaul.foundation import host_paths
from backhaul.foundation.client_registry import (
    RegistryError,
    find_uid,
    load_registry,
    register_uid,
    suggest_uid,
)

__all__ = [
    "RegistryError",
    "load_registry",
    "find_uid",
    "register_uid",
    "suggest_uid",
    "resolve_client_folder",
]


def resolve_client_folder(
    config: dict, uid: str, tickets_root: str | Path, *, host_root: str | None = None
) -> Path:
    """Resolve the project folder associated with a client UID, for the ticket header's
    Folder link (opened via the openfolder: protocol handler — see modules/handlers/openfolder).

    Looks up config["client_folders"][uid] if present; otherwise falls back to the parent
    directory of tickets_root (e.g. content_roots.tickets = ".../Fronthaul/tickets" falls
    back to ".../Fronthaul") — the sane default for a client with no dedicated project folder
    configured yet.

    An explicit client_folders entry is never touched by `host_root` — it's already expected
    to be a correct, real machine path as configured (config.local.json's docstring requires
    this), unrelated to wherever content_roots currently resolves at runtime. Only the
    *fallback* branch is runtime-rooted (derived from tickets_root), so only it gets translated
    via foundation/host_paths.to_host_path when `host_root` is given — see that module for why.
    """
    folders = config.get("client_folders", {})
    if uid in folders:
        return Path(folders[uid])
    fallback = Path(tickets_root).parent
    if host_root is None:
        return fallback
    runtime_root = Path(tickets_root).parent.parent
    return Path(host_paths.to_host_path(fallback, runtime_root=runtime_root, host_root=host_root))
