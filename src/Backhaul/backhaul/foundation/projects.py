"""Named project registry: maps short names to per-project config.local.json paths, so bht
and bhw can be pointed at a project from anywhere via `--project <name>` instead of a raw
`--config <path>`.

Lives at `config/projects.json`, gitignored — per-machine, same as config.local.json, since
it lists absolute paths specific to this machine's checkout layout. This is the "one place"
an agent needs to know about (Backhaul itself) to discover and act on any registered project,
rather than needing a different raw config path memorized per project.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ProjectsError(Exception):
    """Raised when projects.json is malformed or a requested project name isn't registered."""


def load_projects(registry_path: str | Path) -> dict[str, str]:
    """Return {name: config_path} from projects.json. Empty dict if the file doesn't exist yet
    (nothing registered is a normal, unconfigured state — not an error)."""
    p = Path(registry_path)
    if not p.is_file():
        return {}

    try:
        data: Any = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ProjectsError(f"{p}: not valid JSON: {e}") from e

    if not isinstance(data, dict):
        raise ProjectsError(f"{p}: top level must be a JSON object of name -> config path")

    return {str(name): str(path) for name, path in data.items()}


def resolve_project_config(registry_path: str | Path, name: str) -> Path:
    """Resolve a registered project name to its config.local.json path.

    Raises ProjectsError if the name isn't registered, listing what is — so a typo'd
    --project surfaces a clear, actionable error instead of a downstream config-not-found.
    """
    projects = load_projects(registry_path)
    if name not in projects:
        known = ", ".join(sorted(projects)) or "(none registered)"
        raise ProjectsError(f"unknown project {name!r}. Known projects: {known}")
    return Path(projects[name])
