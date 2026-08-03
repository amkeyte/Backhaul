"""Version tracking, in exactly two places: a single VERSION marker file, and a git-diff
safety check that warns if the repo's checked-out version doesn't match what a machine's
config.local.json last recorded (catches "you pulled updates but didn't re-sync config").

See migration/MIGRATION_PLAN.md §6.
"""

from __future__ import annotations

from pathlib import Path


def read_version(repo_root: str | Path) -> str:
    """Read the VERSION file at the repo root."""
    raise NotImplementedError("stub — see migration/MIGRATION_PLAN.md §6")


def check_version_drift(repo_root: str | Path, config: dict) -> bool:
    """Return True if the repo's VERSION matches what's recorded in config, False if drifted."""
    raise NotImplementedError("stub — see migration/MIGRATION_PLAN.md §6")
