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


_REQUIRED_TOP_LEVEL = ("version", "content_roots")
_REQUIRED_CONTENT_ROOTS = ("tickets", "wiki")


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Load and return the local machine config as a dict.

    Raises ConfigError if the file is missing, not valid JSON, or fails the minimal shape
    check against config/config.schema.json (required keys only — full JSON Schema
    validation is planned but not yet implemented here).
    """
    p = Path(config_path)
    if not p.is_file():
        raise ConfigError(
            f"{p}: no config.local.json here. Copy config/config.local.example.json to "
            f"config/config.local.json and point content_roots at this machine's content."
        )

    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigError(f"{p}: could not read config file: {e}") from e

    try:
        config = json.loads(text)
    except json.JSONDecodeError as e:
        raise ConfigError(f"{p}: not valid JSON: {e}") from e

    if not isinstance(config, dict):
        raise ConfigError(f"{p}: top level of config must be a JSON object")

    missing = [k for k in _REQUIRED_TOP_LEVEL if k not in config]
    if missing:
        raise ConfigError(f"{p}: missing required key(s): {', '.join(missing)}")

    content_roots = config["content_roots"]
    if not isinstance(content_roots, dict):
        raise ConfigError(f"{p}: content_roots must be an object")
    missing_roots = [k for k in _REQUIRED_CONTENT_ROOTS if k not in content_roots]
    if missing_roots:
        raise ConfigError(f"{p}: content_roots missing required key(s): {', '.join(missing_roots)}")

    return config


def get_enabled_modules(config: dict[str, Any]) -> list[str]:
    """Return the list of optional module ids enabled in this config.

    Note: BHT and BHW are baseline/always-present services, not gated by this list.
    See migration/ARCHITECTURE.md.
    """
    modules = config.get("enabled_modules", [])
    if not isinstance(modules, list):
        raise ConfigError("enabled_modules must be a list of module id strings")
    return list(modules)
