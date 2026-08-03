"""Typed cross-references between BHT (tickets) and BHW (wiki pages).

Per migration/ARCHITECTURE.md, the two wikis/services don't deep-link into each other's
internals — a Ref is a lightweight, typed pointer (kind + id) that a service can resolve to
a display string or path without the other service needing to expose more than that.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RefKind = Literal["ticket", "wiki"]


@dataclass(frozen=True)
class Ref:
    kind: RefKind
    id: str

    def __str__(self) -> str:
        return f"{self.kind}:{self.id}"


def resolve(ref: Ref) -> str:
    """Resolve a Ref to a human-readable path or link. Dispatches to the owning service."""
    raise NotImplementedError("stub — see migration/ARCHITECTURE.md")
