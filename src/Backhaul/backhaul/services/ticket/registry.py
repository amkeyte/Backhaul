"""client-uids.md registry: maps short UID codes (GEN, UW, ...) to client display names.

BHT's identity.NumberedIdentity scopes ticket numbering per UID; this registry is where a UID
gets minted the first time a client is seen, and looked up on every ticket after that. Mirrors
the role of the current Aaron K `_passdown/client-uids.md` file (per migration/MIGRATION_PLAN.md
§4) but lives under each machine's configured tickets content root, not in this repo.
"""

from __future__ import annotations

import re
from pathlib import Path

_ENTRY_RE = re.compile(r"^-\s*([A-Za-z0-9]+):\s*(.+?)\s*$")
_DEFAULT_HEADER = (
    "# Client UIDs\n\n"
    "UID -> client display name. One entry per line: `- UID: Client Name`.\n\n"
)


class RegistryError(Exception):
    """Raised on a malformed or ambiguous client-uids.md registry."""


def load_registry(registry_path: str | Path) -> dict[str, str]:
    """Return {uid: client_name} from client-uids.md. Empty dict if the file doesn't exist yet."""
    p = Path(registry_path)
    if not p.is_file():
        return {}

    registry: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        match = _ENTRY_RE.match(line)
        if not match:
            continue
        uid, name = match.groups()
        if uid in registry:
            raise RegistryError(f"{p}: duplicate UID {uid!r}")
        registry[uid] = name
    return registry


def find_uid(registry_path: str | Path, client_name: str) -> str | None:
    """Return the UID already registered for client_name (case-insensitive), or None."""
    target = client_name.strip().lower()
    for uid, name in load_registry(registry_path).items():
        if name.strip().lower() == target:
            return uid
    return None


def register_uid(registry_path: str | Path, uid: str, client_name: str) -> None:
    """Append a new `uid: client_name` entry, creating the registry file if needed.

    Idempotent: a no-op if the uid is already registered to the same client. Raises
    RegistryError if the uid is already registered to a *different* client.
    """
    p = Path(registry_path)
    existing = load_registry(p)

    if uid in existing:
        if existing[uid].strip().lower() != client_name.strip().lower():
            raise RegistryError(
                f"{p}: UID {uid!r} is already registered to {existing[uid]!r}, not {client_name!r}"
            )
        return

    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(_DEFAULT_HEADER, encoding="utf-8")

    with p.open("a", encoding="utf-8") as f:
        f.write(f"- {uid}: {client_name}\n")


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


def suggest_uid(client_name: str) -> str:
    """Auto-suggest a UID from a client name — initials of significant words, uppercased.

    e.g. "University of Washington" -> "UW", "General" -> "GEN". Per FOUNDATION_DESIGN.md's
    note that NumberedIdentity carries a `suggest_prefix`-style auto-suggest+confirm UX — this
    is the suggestion half; confirming/overriding is the caller's job (the CLI's --uid flag).
    """
    stopwords = {"of", "the", "and"}
    words = [w for w in re.findall(r"[A-Za-z0-9]+", client_name) if w.lower() not in stopwords]
    if not words:
        raise RegistryError(f"cannot derive a UID from client name {client_name!r}")
    if len(words) == 1:
        return words[0][:3].upper()
    return "".join(w[0] for w in words).upper()
