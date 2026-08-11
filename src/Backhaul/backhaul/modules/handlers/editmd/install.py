"""Registers the editmd: URL protocol in HKEY_CURRENT_USER, so clicking an editmd:/// link
rendered in Chrome (via BHT's board.py) launches Notepad++.

HKCU, not HKLM — no admin rights needed, and it's a per-user setting anyway. Safe to re-run;
each key is just overwritten with the same values.

Run once per machine:
    bht-install-editmd
or:
    python -m backhaul.modules.handlers.editmd.install
"""

from __future__ import annotations

import sys
from pathlib import Path

_VBS_PATH = Path(__file__).parent / "editmd.vbs"


def registry_command() -> str:
    """The shell\\open\\command value: launches editmd.vbs via wscript, passing the clicked URL."""
    return f'wscript.exe "{_VBS_PATH}" "%1"'


def install() -> None:
    if sys.platform != "win32":
        raise RuntimeError(
            "editmd protocol registration only applies on Windows — run this on the machine "
            "that will actually click editmd:// links, not in a dev/CI sandbox."
        )

    import winreg  # noqa: PLC0415 — Windows-only import, deliberately deferred

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\editmd") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:editmd Protocol")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")

    command_path = r"Software\Classes\editmd\shell\open\command"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_path) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, registry_command())


def main(argv: list[str] | None = None) -> int:
    try:
        install()
    except RuntimeError as e:
        print(f"FAIL: {e}")
        return 1
    print(f"OK: registered editmd: protocol -> {registry_command()}")
    print("Chrome will prompt to confirm launching an external protocol the first time you")
    print("click an editmd:// link — that's expected, allow it (optionally 'always allow').")
    return 0


if __name__ == "__main__":
    sys.exit(main())
