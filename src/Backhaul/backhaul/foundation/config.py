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

#: The config *schema*'s own version — bumped only when config.local.json's required shape
#: changes in a breaking way (a required key added/renamed/removed). NOT the same axis as
#: pyproject.toml's package version, which can move for unrelated reasons (bug fixes, new
#: optional modules) without invalidating any existing config. Adding a new *optional* key
#: (e.g. content_roots.roadmap) is backward compatible and does not require a bump here.
CONFIG_SCHEMA_VERSION = "0.1.0"


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

    if config["version"] != CONFIG_SCHEMA_VERSION:
        raise ConfigError(
            f"{p}: config \"version\" is {config['version']!r}, but this checkout's config "
            f"schema is {CONFIG_SCHEMA_VERSION!r}. See config/config.schema.json for what "
            f"changed, reconcile this config against it, then update its \"version\" field."
        )

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


def get_project_name(config: dict[str, Any]) -> str:
    """Return the display name shown in every piece of content's normalized header
    (foundation/header.py). Falls back to content_roots.tickets's grandparent folder name
    (the project's true root, per the backhaul/ subfolder convention — tickets_root is
    .../<project>/backhaul/tickets) when "project_name" isn't set, so older configs and
    synthetic test fixtures without it still get a sensible label instead of an error.
    """
    name = config.get("project_name")
    if name:
        return str(name)
    tickets_root = Path(config["content_roots"]["tickets"])
    return tickets_root.parent.parent.name or "Backhaul"
