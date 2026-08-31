"""Config loading.

Every script reads a gitignored `config.local.json` fresh on each invocation — no reliance
on env vars or cwd persistence, since the sandbox does not carry either between calls. One
deliberate exception: BACKHAUL_LOCAL_ROOT (see load_config's docstring) — a per-*session*, not
per-machine, override, which is exactly why it belongs in an env var rather than the
per-machine config.local.json file.

See migration/MIGRATION_PLAN.md §6 (config + versioning design) and
migration/PYTHON_PROJECT_SETUP.md for the resolved layout this reads from
(`config/config.schema.json` for shape, `config/config.local.json` per machine, gitignored).
"""

from __future__ import annotations

import json
import os
from pathlib import Path, PureWindowsPath
from typing import Any

from . import projects as _projects

#: Env var a session can export to tell every content_roots path where the project's true
#: root actually is *on this process's own filesystem* — the mirror image of host_root (which
#: says where a human should click; this says where the CLI should actually read/write, right
#: now). Deliberately not a CLI flag: a session issues many commands, and exporting this once
#: is far less friction than repeating a flag on every one. Deliberately not stored in
#: config.local.json either: the correct value is different every time a fresh Cowork sandbox
#: mounts the same project at a new, unpredictable path — a per-machine config file can't hold
#: a value that changes every session, so it can't live there.
LOCAL_ROOT_ENV_VAR = "BACKHAUL_LOCAL_ROOT"


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


def _remap_content_roots(content_roots: dict[str, Any], local_root: str) -> dict[str, Any]:
    """Re-root every content_roots value onto local_root instead of wherever it was written
    for — the mirror image of foundation/host_paths.to_host_path.

    Parses each value with PureWindowsPath specifically (not plain Path) so a Windows-style
    string like "C:\\_local\\mcRepos\\backhaul\\tickets" splits into segments correctly even
    though this process itself may be on Linux, where plain Path/os.sep-based splitting can't
    see backslashes as separators at all. Assumes the standard <project>/backhaul/<x>
    convention (the project's Windows-style true root is content_roots["tickets"]'s
    grandparent) — a value that doesn't fall under that root is left unchanged rather than
    guessed at.
    """
    tickets_value = content_roots.get("tickets")
    if not isinstance(tickets_value, str) or not tickets_value:
        return content_roots
    win_root = PureWindowsPath(tickets_value).parent.parent

    remapped = dict(content_roots)
    for key, value in content_roots.items():
        if not isinstance(value, str) or not value:
            continue
        win_path = PureWindowsPath(value)
        try:
            rel_parts = win_path.relative_to(win_root).parts
        except ValueError:
            continue
        remapped[key] = str(Path(local_root, *rel_parts)) if rel_parts else str(Path(local_root))
    return remapped


def load_config(config_path: str | Path, *, local_root: str | None = None) -> dict[str, Any]:
    """Load and return the local machine config as a dict.

    Raises ConfigError if the file is missing, not valid JSON, or fails the minimal shape
    check against config/config.schema.json (required keys only — full JSON Schema
    validation is planned but not yet implemented here).

    `local_root`, if given (or, when omitted, read from the BACKHAUL_LOCAL_ROOT environment
    variable — see that constant's docstring for why an env var and not a config field), tells
    this call where the project's true root actually lives on *this* process's own filesystem,
    and every content_roots value gets remapped onto it before anything else happens —
    specifically so a role's Cowork sandbox, which can't do file I/O against content_roots
    written as the real machine's Windows paths, can point this one call/session at wherever
    it's actually mounted here instead. The absolute-path check below then validates the
    *remapped* values, so a config that would otherwise be rejected as unusable on this
    machine loads and works correctly once local_root corrects it.
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

    if local_root is None:
        local_root = os.environ.get(LOCAL_ROOT_ENV_VAR)
    if local_root:
        content_roots = _remap_content_roots(content_roots, local_root)
        config["content_roots"] = content_roots

    # A content_root written for a different machine/OS than the one running this process
    # doesn't fail — it silently parses as a relative path (e.g. a Windows "C:\..." string,
    # read on Linux, isn't absolute — pathlib treats it as one opaque relative segment,
    # .parent collapses to ".", and every write this config drives lands relative to
    # wherever the CLI happened to be invoked from instead of touching real content at all).
    # Refusing to load is safer than a silent no-op or a stray file dropped at cwd — this
    # exact failure mode is why: see foundation/host_paths.py and the `bhrole` meta wiki page
    # for the fuller story (2026-08-11).
    bad_roots = [
        k for k, v in content_roots.items()
        if isinstance(v, str) and v and not os.path.isabs(v)
    ]
    if bad_roots:
        bad_list = ", ".join(f"{k}={content_roots[k]!r}" for k in bad_roots)
        raise ConfigError(
            f"{p}: content_roots has path(s) that aren't absolute on this machine: {bad_list}. "
            f"This usually means the config was written for a different OS/machine than the one "
            f"running this command right now (e.g. a Windows path loaded inside a Linux sandbox) "
            f"— refusing to proceed rather than silently write to the wrong place or no-op."
        )

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


def get_repo_url(config: dict[str, Any]) -> str | None:
    """Return this checkout's own git remote URL, if configured — e.g.
    "https://github.com/amkeyte/Backhaul". Used by modules/roles/launch.py to tell a freshly
    launched role session (a bare sandbox with only the project folder attached, not Backhaul's
    own source) how to `pip install` the bht/bhw/bhrm/bhrole CLI for itself. Optional — a
    config without it just gets a Launch link with no install instructions, same graceful-omit
    pattern the rest of the optional fields use."""
    url = config.get("repo_url")
    return str(url) if url else None


def find_config_upward(start: Path) -> Path | None:
    """Search `start` and each of its parents for a project's `backhaul/config.local.json`,
    git-`.git`-style. Returns None if nothing is found before reaching the filesystem root.

    Handles both being outside a project's `backhaul/` directory (checks
    `<candidate>/backhaul/config.local.json` at every level) and already being inside one
    (checks `<candidate>/config.local.json` directly when `<candidate>`'s own name is
    "backhaul"). Only searches for the *consumer-project* layout — every real project this
    repo has seen puts config.local.json inside its own backhaul/ folder alongside
    tickets/wiki/roadmap/roles. This repo's own dogfooded config lives at a different relative
    path (config/config.local.json, not backhaul/config.local.json) and is deliberately not
    matched here — see resolve_config_path's docstring and wiki/design/bh010-021-architecture.md
    (BH_019) for why: this search is additive in front of each caller's own hardcoded default,
    not a replacement for it, so the one case that already worked keeps working unchanged.
    """
    candidate = start.resolve()
    while True:
        if candidate.name == "backhaul":
            direct = candidate / "config.local.json"
            if direct.is_file():
                return direct
        nested = candidate / "backhaul" / "config.local.json"
        if nested.is_file():
            return nested
        parent = candidate.parent
        if parent == candidate:
            return None
        candidate = parent


def resolve_config_path(
    args: Any, *, default_config_path: str | Path, projects_path: str | Path
) -> Path:
    """Shared --project / --config / upward-search / default resolution, used by every
    service's own cli.py (bht, bhw, bhrm, bhrole, backhaul) so this logic exists in one place
    instead of five near-identical copies.

    Priority: `--project` (a name from projects.json) > `--config` (a raw path) > an upward
    search from the current directory for a project's `backhaul/config.local.json` (see
    find_config_upward) > the caller's own hardcoded default (this checkout's own config, for
    the case of running Backhaul directly against its own source without installing it).

    The upward search was added specifically so "omit both flags" works for a consumer project
    too — before it, the bare default only ever succeeded for this repo's own dogfooding case,
    which resolves relative to wherever the package is installed, not to cwd (see BH_019). It's
    additive, not a replacement: falling through to default_config_path when nothing is found
    upward preserves today's real behavior exactly for the one case that already worked.
    """
    project = getattr(args, "project", None)
    if project:
        return _projects.resolve_project_config(projects_path, project)

    config_arg = getattr(args, "config", None)
    if config_arg:
        return Path(config_arg)

    found = find_config_upward(Path.cwd())
    if found is not None:
        return found

    return Path(default_config_path)


#: Valid values for config.local.json's optional `build_ready` field (BH_007) — a human-set
#: marker of whether this project is currently in a buildable/playtestable state, rendered on
#: BACKHAUL.md. Omitted entirely (get_build_ready() returns None) shows no marker at all.
BUILD_READY_VALUES = ("ready", "notReady")


def get_build_ready(config: dict[str, Any]) -> str | None:
    """Return this project's manually-set build-ready marker ("ready"/"notReady"), or None if
    unset — the default, meaning `backhaul dashboard` shows no marker line at all. Raises
    ConfigError on a value outside BUILD_READY_VALUES, same "fail loud on a bad value" discipline
    get_enabled_modules already applies, rather than silently treating a typo as unset."""
    value = config.get("build_ready")
    if value is None:
        return None
    value = str(value)
    if value not in BUILD_READY_VALUES:
        raise ConfigError(
            f"config \"build_ready\" is {value!r}, must be one of {BUILD_READY_VALUES} (or omitted)"
        )
    return value


def get_host_root(config: dict[str, Any]) -> str | None:
    """Return this project's "real" root path, if configured — e.g.
    "C:\\_local\\mcRepos", the path a human should actually see and click, independent of
    wherever content_roots currently resolves at runtime (e.g. a Cowork sandbox mount). Used
    by foundation/host_paths.py to re-root absolute-path links (editmd:, openfolder:, and role
    Launch links) so they work on the target machine instead of baking in wherever the CLI
    happened to be running when it built them. Optional — a config without it just gets links
    built straight from content_roots as printed, today's long-standing default behavior."""
    val = config.get("host_root")
    return str(val) if val else None
