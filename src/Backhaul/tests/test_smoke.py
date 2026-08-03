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
    assert backhaul.__version__ == "0.1.0"
