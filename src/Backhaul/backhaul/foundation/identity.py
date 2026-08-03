"""Identity schemes for addressing docs.

Two flavors, per migration/FOUNDATION_DESIGN.md:
- NumberedIdentity: UID + sequential number, e.g. ticket "UW_002" (client-code + counter).
- PathIdentity: category/slug path, e.g. wiki "knowledge-base/clients/university-of-washington".

BHT uses NumberedIdentity (new_ticket.py-style counters per client UID).
BHW uses PathIdentity (category-based slugs, breadcrumbs).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NumberedIdentity:
    uid: str
    number: int

    def __str__(self) -> str:
        return f"{self.uid}_{self.number:03d}"


@dataclass(frozen=True)
class PathIdentity:
    category: str
    slug: str

    def __str__(self) -> str:
        return f"{self.category}/{self.slug}"


def next_number(uid: str, existing_numbers: list[int]) -> int:
    """Return the next sequential number for a given UID given the numbers already in use.

    `uid` isn't consulted for the arithmetic (existing_numbers is expected to already be
    scoped to that UID by the caller) — it's accepted for symmetry with NumberedIdentity
    and to keep call sites self-documenting.
    """
    if not existing_numbers:
        return 1
    return max(existing_numbers) + 1
