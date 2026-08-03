"""Config loading.

Every script reads a gitignored `config.local.json` fresh on each invocation — no reliance
on env vars or cwd persistence, since the sandbox does not carry either between calls.

See migration/MIGRATION_PLAN.md §6 (config + versioning design) and
migration/PYTHON_PROJECT_SETUP.md for the resolved layout this reads from
(`config/config.schema.json` for shape, `config/config.local.json` per machine, gitignored).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Raised when config.local.json is missing, unreadable, or fails schema validation."""


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Load and return the local machine config as a dict.

    Raises ConfigError if the file is missing or not valid JSON. Schema validation against
    config/config.schema.json is planned but not yet implemented here.
    """
    raise NotImplementedError("stub — see migration/MIGRATION_PLAN.md §6")


def get_enabled_modules(config: dict[str, Any]) -> list[str]:
    """Return the list of optional module ids enabled in this config.

    Note: BHT and BHW are baseline/always-present services, not gated by this list.
    See migration/ARCHITECTURE.md.
    """
    raise NotImplementedError("stub — see migration/MODULE_SYSTEM.md")
