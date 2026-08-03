"""shortcuts module — Windows .lnk creation (make_lnk.py, pylnk3-based). Ported from Aaron
K's CLAUDE Stuff/Scripts/make_lnk.py; depends only on foundation.
"""

from .lnk import LnkBuildError, LnkSpec, build, build_and_verify, verify

__all__ = ["LnkSpec", "LnkBuildError", "build", "verify", "build_and_verify"]
