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


def resolve_client_folder(config: dict, uid: str, tickets_root: str | Path) -> Path:
    """Resolve the project folder associated with a client UID, for the ticket header's
    Folder link (opened via the openfolder: protocol handler — see modules/handlers/openfolder).

    Looks up config["client_folders"][uid] if present; otherwise falls back to the parent
    directory of tickets_root (e.g. content_roots.tickets = ".../Fronthaul/tickets" falls
    back to ".../Fronthaul") — the sane default for a client with no dedicated project folder
    configured yet.

    Neither branch calls .resolve() — tickets_root and client_folders entries are expected to
    already be correct, absolute paths as configured (config.local.json's docstring requires
    real machine paths), so this returns them as given rather than re-deriving them against
    whatever filesystem this code happens to be executing on right now.
    """
    folders = config.get("client_folders", {})
    if uid in folders:
        return Path(folders[uid])
    return Path(tickets_root).parent
