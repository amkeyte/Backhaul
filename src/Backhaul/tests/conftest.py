"""Shared pytest fixtures.

The one thing every test in this suite needs, unconditionally: BACKHAUL_LOCAL_ROOT stripped
from the environment before it runs.

BH_028: that env var re-roots content_roots onto wherever it points, applied by each CLI's own
`_load_config()` at the real entry point (see foundation/config.py's own docstring for why
`load_config()` itself no longer reads it directly). Tests that drive the CLI through `main()`
— the correct way to test CLI behavior — go through that same entry point, so removing the read
from `load_config()` alone isn't enough to make them hermetic; a developer session that runs
`export BACKHAUL_LOCAL_ROOT=...` and then `pytest` in the same shell (exactly the normal,
documented way to point this CLI at a sandbox-mounted project) would otherwise silently redirect
every test's own tmp_path content_roots onto wherever that env var points instead. That's
exactly what happened: two full-suite runs under that combination corrupted 125 files in this
repo's own tracked `content/`/`Fronthaul/` fixture data before anyone noticed, because the
redirected writes looked like normal successful test runs — nothing failed, files just landed
in the wrong, real place.

Function-scoped and autouse: applies fresh before every single test (not just once per session,
in case a test itself sets the env var), and no test file needs to remember to request it — it
can't be skipped by adding a new test that forgets to ask for it.
"""

import pytest


@pytest.fixture(autouse=True)
def _no_local_root_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BACKHAUL_LOCAL_ROOT", raising=False)
