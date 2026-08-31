"""Backhaul — the shared foundation, plus BHT (ticket) and BHW (wiki) services.

See migration/ARCHITECTURE.md for the foundation/services/modules layer model this package
follows, and migration/FOUNDATION_DESIGN.md for the interface design of everything under
`foundation/`.
"""


# PEP 440 dev-release suffix: `master` always carries a clean release version (currently
# "0.1.0"); any branch that has diverged from the last release and hasn't merged back bumps to
# the next version with a `.devN` suffix, so `__version__`/`pip show`/`--version` differ from
# master on sight. Locked convention — see wiki/design/version-branch-convention.md. Drop the
# `.devN` suffix (and bump to the real next release number if warranted) only when this work
# merges back to master.
__version__ = "0.2.0.dev0"
