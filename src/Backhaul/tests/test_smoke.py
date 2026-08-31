"""Smoke test: confirms the package structure imports cleanly. Real coverage lands as each
foundation primitive and service is implemented (see task #12 follow-ups)."""

import pytest

import backhaul
import backhaul.foundation
import backhaul.services.ticket
import backhaul.services.wiki
import backhaul.modules.docx
import backhaul.modules.shortcuts
import backhaul.modules.handlers.editmd
import backhaul.modules.handlers.openfolder


def test_version_is_set():
    # Not pinned to a literal: __version__ is expected to move independently of this test as
    # part of the branch-identification convention (wiki/design/version-branch-convention.md) —
    # master carries a clean release number, any unreleased branch carries a `.devN` suffix.
    # This just confirms the attribute exists and looks like a version string.
    import re

    assert re.match(r"^\d+\.\d+\.\d+(\.dev\d+)?$", backhaul.__version__)


def test_shortcuts_imports_without_pylnk3_installed(monkeypatch: pytest.MonkeyPatch):
    """Regression test for BH_027: `backhaul.modules.shortcuts` used to `import pylnk3` at
    module level (via its own `__init__.py`'s eager `from .lnk import ...`), so a bare `import
    backhaul.modules.shortcuts` — exactly what this file does above — crashed the whole test
    session at collection time on any environment that installed `pip install -e
    "src/Backhaul[dev]"` per the test checklist's own step 3, since `pylnk3` lives in the
    separate `shortcuts` extra, not `dev`. `docx` already deferred its own heavy optional
    import the same way `shortcuts` now does; this pins that fix so it can't regress silently
    even in an environment (like this one) where pylnk3 happens to already be installed.

    Blocks `pylnk3` via sys.meta_path rather than relying on it being genuinely absent, so this
    test is meaningful regardless of what's actually installed in the environment running it.
    """
    import importlib
    import sys

    class _BlockPylnk3:
        def find_module(self, name, path=None):
            if name == "pylnk3":
                return self

        def load_module(self, name):
            raise ModuleNotFoundError(f"No module named {name!r} (blocked for this test)")

    blocker = _BlockPylnk3()
    monkeypatch.delitem(sys.modules, "pylnk3", raising=False)  # clear any stale cached import
    sys.meta_path.insert(0, blocker)
    try:
        for mod in ("backhaul.modules.shortcuts", "backhaul.modules.shortcuts.lnk"):
            sys.modules.pop(mod, None)
        module = importlib.import_module("backhaul.modules.shortcuts")
        spec = module.LnkSpec(target=r"C:\x", out=r"C:\y")  # dataclass construction needs no pylnk3
        with pytest.raises(ModuleNotFoundError):
            module.build(spec)
    finally:
        sys.meta_path.remove(blocker)
        for mod in ("backhaul.modules.shortcuts", "backhaul.modules.shortcuts.lnk"):
            sys.modules.pop(mod, None)
