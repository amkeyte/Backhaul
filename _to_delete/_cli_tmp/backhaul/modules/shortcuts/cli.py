"""CLI entry point, ported from make_lnk.py's argparse/main(). Kept as a thin wrapper over
lnk.build_and_verify() so the same logic is usable as a library or from the command line.

Console script: `backhaul-lnk` (see pyproject.toml [project.scripts]).
"""

from __future__ import annotations

import argparse
import sys

from .lnk import LnkBuildError, LnkSpec, build_and_verify


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build a Windows .lnk shortcut with correct segment typing.")
    p.add_argument("--target", required=True, help="Literal Windows path embedded in the shortcut (C:\\... or \\\\server\\share).")
    p.add_argument("--out", required=True, help="Filesystem path to write the .lnk to (mount path).")
    p.add_argument("--type", choices=["folder", "file"], default="folder", help="Target type. Default: folder.")
    p.add_argument("--name", default=None, help="Friendly description shown by Windows.")
    p.add_argument("--workdir", default=None, help='"Start in" directory. Defaults to the target dir for folders.')
    p.add_argument("--args", default=None, help="Command-line arguments (used for the Explorer fallback).")
    p.add_argument("--icon", default=None, help="Custom icon source path.")
    p.add_argument("--icon-index", type=int, default=0, dest="icon_index")
    p.add_argument("--force", action="store_true", help="Allow overwriting an existing .lnk.")
    args = p.parse_args(argv)

    spec = LnkSpec(
        target=args.target,
        out=args.out,
        type=args.type,
        name=args.name,
        workdir=args.workdir,
        args=args.args,
        icon=args.icon,
        icon_index=args.icon_index,
        force=args.force,
    )

    try:
        out_path = build_and_verify(spec)
    except LnkBuildError as e:
        print(f"FAIL: {e}")
        return 1

    print(f"OK: wrote '{out_path}' -> '{spec.target}' (all segments correctly typed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
