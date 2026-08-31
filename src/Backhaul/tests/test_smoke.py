"""Smoke test: confirms the package structure imports cleanly. Real coverage lands as each
foundation primitive and service is implemented (see task #12 follow-ups)."""

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
