"""Cross-service lint: orphaned pages and broken links, walked across every content root a
project actually has configured (tickets, wiki, roadmap, roles) — not just one service's own
root, since a link written in a ticket can point at a wiki page and vice versa. See BH_004 and
its Design section for the full rationale on why this lives here (not `services/wiki`) and why
only these two checks ship in v1.

Read-only. Never writes, never guesses a fix — deciding where to link an orphan from, or what a
broken link should point at instead, is an editorial call this module can't make. Report the
findings; let the human (or the agent working the ticket) decide.

Two checks, both fully generic markdown-graph problems — no project-specific convention
knowledge required, unlike the LunaFlow-specific checks (status drift, missing Decision
sections, deprecation markers) this deliberately leaves out of v1.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from . import config as _config

#: `[text](target)` or `[text](target "title")` — the two markdown link forms this repo's
#: content actually uses. Doesn't match reference-style `[text][ref]` links; none of this
#: project's templates or generated output use that form.
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

#: Link schemes that are never a local file path to check — external URLs, mail links, and this
#: project's own protocol-handler links (editmd:, openfolder:, claude:).
_NON_LOCAL_SCHEMES = frozenset({"http", "https", "mailto", "editmd", "openfolder", "claude"})

#: A link immediately followed (same line) by this HTML comment is a deliberate reference to
#: something that may no longer resolve — e.g. a ticket link left in a wiki page's "see also"
#: after the ticket closed, on purpose, as a paper trail. `find_broken_links()` skips it (see
#: BH_015). Matches this project's existing marker idiom (`<!-- board:start -->`,
#: `<!-- bh-header:start -->`) rather than a markdown title attribute (`[text](target "historical")`),
#: which some viewers render as hover text — that would look like a broken tooltip, not an
#: intentional marker. Deliberately scoped to `find_broken_links()` only, not `find_orphaned()` —
#: a historical link is still a real link for orphan-detection purposes, just one that's allowed
#: to point at a target that's gone.
_HISTORICAL_LINK_MARKER = "<!-- historical-link -->"

#: client-uids.md (content_roots.tickets/client-uids.md, shared by BHT and BHRM) is
#: infrastructure a reader finds by convention, not by following a link — same reasoning
#: LunaFlow's doc-lint exempts index.md/README* for. Note the *other* generated aggregate files
#: (BOARD.md, WIKI_INDEX.md, ROADMAP_INDEX.md, ROLES_INDEX.md, BACKHAUL.md) don't need an
#: entry here at all: each lives one directory *above* its content root (a sibling of
#: tickets/wiki/roadmap/roles, not inside any of them), so lint's per-root walk never reaches
#: them in the first place — this exemption set only needs to cover files that actually live
#: inside a scanned root.
_EXEMPT_FILENAMES = frozenset({"client-uids.md"})

CHECKS = ("orphaned", "links")


class LintError(ValueError):
    """Raised for a bad --check name — an expected CLI failure, not a finding."""


@dataclass(frozen=True)
class Finding:
    check: str
    path: Path
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"check": self.check, "file": str(self.path), "message": self.message}

    def __str__(self) -> str:
        return f"{self.check}: {self.path} — {self.message}"


def _content_roots(config: dict[str, Any]) -> dict[str, Path]:
    """Every content root this project's config actually has. Tickets/wiki are always present
    (baseline services); roadmap/roles only count when both a content_roots entry *and* the
    module are enabled — same gating dashboard.py's own cross-cutting build already uses, so
    lint never walks a folder the rest of the CLI would refuse to touch."""
    content_roots = config.get("content_roots", {})
    enabled = set(_config.get_enabled_modules(config))

    roots: dict[str, Path] = {}
    if "tickets" in content_roots:
        roots["tickets"] = Path(content_roots["tickets"])
    if "wiki" in content_roots:
        roots["wiki"] = Path(content_roots["wiki"])
    if "roadmap" in content_roots and "roadmap" in enabled:
        roots["roadmap"] = Path(content_roots["roadmap"])
    if "roles" in content_roots and "roles" in enabled:
        roots["roles"] = Path(content_roots["roles"])
    return roots


def _all_md_files(roots: dict[str, Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots.values():
        if root.is_dir():
            files.extend(root.rglob("*.md"))
    return sorted(set(files))


def _is_local_path(target: str) -> bool:
    """True for a target this module should try to resolve as a file on disk — a relative (or
    absolute) filesystem path, not an anchor-only fragment or a non-local scheme."""
    if not target or target.startswith("#"):
        return False
    return urlsplit(target).scheme == ""


def _resolve_target(source: Path, target: str) -> Path | None:
    """Resolve a local link target relative to the file that contains it. Strips a trailing
    `#fragment` (an in-page anchor, not part of the path) and an empty path-with-fragment
    (`"#top"` already excluded by _is_local_path, but `"file.md#section"` needs the fragment
    stripped before resolving). Returns None for a target that's empty once the fragment is
    stripped — nothing to check."""
    path_part = target.split("#", 1)[0]
    if not path_part:
        return None
    return (source.parent / path_part).resolve()


def find_orphaned(roots: dict[str, Path]) -> list[Finding]:
    """A .md file under any given root that no other file (in any root) links to."""
    files = _all_md_files(roots)
    linked: set[Path] = set()

    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for target in _LINK_RE.findall(text):
            if not _is_local_path(target):
                continue
            resolved = _resolve_target(f, target)
            if resolved is not None:
                linked.add(resolved)

    findings = []
    for f in files:
        if f.name in _EXEMPT_FILENAMES:
            continue
        if f.resolve() not in linked:
            findings.append(Finding("orphaned", f, "no other file links to this page"))
    return findings


def _is_marked_historical(text: str, match_end: int) -> bool:
    """True when `<!-- historical-link -->` appears on the same line, anywhere after the link
    itself (allows other trailing text before the marker, not just immediately after)."""
    newline = text.find("\n", match_end)
    rest_of_line = text[match_end:newline] if newline != -1 else text[match_end:]
    return _HISTORICAL_LINK_MARKER in rest_of_line


def find_broken_links(roots: dict[str, Path]) -> list[Finding]:
    """A relative markdown link whose target doesn't exist, resolved from the linking file.

    Skips a link marked `<!-- historical-link -->` on the same line (see BH_015) — a
    deliberate reference to something that's gone, not a mistake to flag.
    """
    files = _all_md_files(roots)
    findings = []

    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in _LINK_RE.finditer(text):
            target = m.group(1)
            if not _is_local_path(target):
                continue
            if _is_marked_historical(text, m.end()):
                continue
            resolved = _resolve_target(f, target)
            if resolved is None:
                continue
            if not resolved.exists():
                findings.append(
                    Finding("links", f, f"broken link -> {target!r} (resolved: {resolved})")
                )
    return findings


_CHECK_FUNCS = {"orphaned": find_orphaned, "links": find_broken_links}


def run_lint(config: dict[str, Any], *, checks: list[str] | None = None) -> list[Finding]:
    """Run the given checks (default: all of CHECKS) against every content root this project's
    config has. Raises LintError on an unknown check name."""
    selected = checks if checks is not None else list(CHECKS)
    unknown = [c for c in selected if c not in _CHECK_FUNCS]
    if unknown:
        raise LintError(f"unknown check(s): {', '.join(unknown)} (known: {', '.join(CHECKS)})")

    roots = _content_roots(config)
    findings: list[Finding] = []
    for name in selected:
        findings.extend(_CHECK_FUNCS[name](roots))
    return sorted(findings, key=lambda fnd: (str(fnd.path), fnd.check))
