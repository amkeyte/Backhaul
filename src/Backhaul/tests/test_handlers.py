"""Tests for modules/handlers/{editmd,openfolder}'s Python side (URI wrappers, install.py's
non-Windows guard). The actual OS integration (registry + .vbs) can't be exercised outside a
real Windows machine — see the module docstrings for manual verification steps.
"""

import sys

import pytest

from backhaul.modules.handlers import editmd, openfolder
from backhaul.modules.handlers.editmd import install as editmd_install
from backhaul.modules.handlers.openfolder import install as openfolder_install


def test_editmd_build_and_decode_uri_round_trip():
    path = r"C:\_local\Fronthaul\tickets\ARR_001_clean-the-car.md"
    uri = editmd.build_uri(path)
    assert uri.startswith("editmd:///")
    assert editmd.decode_uri(uri) == path


def test_openfolder_build_and_decode_uri_round_trip():
    path = r"C:\_local\Fronthaul"
    uri = openfolder.build_uri(path)
    assert uri.startswith("openfolder:///")
    assert openfolder.decode_uri(uri) == path


@pytest.mark.skipif(sys.platform == "win32", reason="guard only fires off-Windows")
def test_editmd_install_refuses_off_windows():
    with pytest.raises(RuntimeError):
        editmd_install.install()


@pytest.mark.skipif(sys.platform == "win32", reason="guard only fires off-Windows")
def test_openfolder_install_refuses_off_windows():
    with pytest.raises(RuntimeError):
        openfolder_install.install()


def test_editmd_registry_command_points_at_vbs_via_wscript():
    command = editmd_install.registry_command()
    assert command.startswith("wscript.exe ")
    assert "editmd.vbs" in command
    assert command.endswith('"%1"')


def test_openfolder_registry_command_points_at_vbs_via_wscript():
    command = openfolder_install.registry_command()
    assert command.startswith("wscript.exe ")
    assert "openfolder.vbs" in command
    assert command.endswith('"%1"')
