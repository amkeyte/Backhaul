---
id: BH_004
uid: BH
number: 4
client: BH
status: done
title: Port doc-lint into Backhaul as bhw lint
context: Generalize LunaFlow's doc-lint.py into a project-agnostic lint command. See
  ticket body.
priority: low
opened: '2026-08-13'
closed: '2026-08-14'
---

## Summary

Port doc-lint into Backhaul as bhw lint

## Full report

Feature request: generalize LunaFlow_A's doc-lint skill (currently a bespoke,
LunaFlow-specific Python script) into a project-agnostic lint command inside Backhaul itself --
something like `bhw lint` or `backhaul lint` -- so any Backhaul-tracked project gets the same
drift/consistency auditing for free, not just LunaFlow_A.

Source
Documents/ClaudeWiki/Tools/doc-lint.py in LunaFlow_A (254 lines, stdlib only, no install step),
wrapped by the `doc-lint` Claude Code skill. Audits LunaFlow's Documents/ tree against
Documents/ClaudeWiki/Processes/wiki-style.md's conventions. Companion skill `doc-scaffold`
generates new docs that pass these checks from the start -- worth keeping in mind since a
Backhaul-native lint command might eventually want a matching "scaffold correctly the first
time" story too, though that's arguably already `bht open`/`bhw new`/`bhrole new`'s job.

What it checks today (LunaFlow-specific implementation)
1. Status drift -- a `**Status:**` free-text field found outside the three legitimate homes
   (Roadmap/, Handoffs/, Specs/) per wiki-style.md's "Where status lives."
2. Orphaned docs -- a .md file under Documents/ that no other doc links to (exempt: index.md /
   README* files, and Roadmap/CodePlans as a whole directory).
3. Missing Decision section -- a handoff ticket whose status isn't `open` but has no
   `## Decision` heading.
4. Incomplete deprecation -- a doc with an ALL-CAPS DEPRECATED marker but no link to the current
   pattern within the next 10 lines.
5. Broken links -- a markdown link whose target file doesn't exist, resolved relative to the
   linking file.

Supports `--check <name>` to run one check at a time, `--format json` for machine-readable
output, and exits 0 (clean) / 1 (findings, informational) / 2 (script error). No auto-fix mode
by design -- every finding needs editorial judgment, so it reports rather than rewrites.

Why this isn't a drop-in port
LunaFlow's checks are written directly against LunaFlow's own conventions, not Backhaul's
generic model:
- Status drift assumes status lives in free-text `**Status:**` lines outside three hardcoded
  folder names. Backhaul already structures status in YAML frontmatter (ticket status, wiki
  page status, role status, roadmap node status vocab) -- the free-text-drift problem doesn't
  really exist the same way here, but a Backhaul-native equivalent might still be useful: e.g.
  flagging a `status:` value that's not in the field's allowed vocabulary, or a status
  mentioned in prose that contradicts the frontmatter (a page whose body says "draft" while
  frontmatter says "verified").
- Missing Decision section is LunaFlow-ticket-specific (Convention 4, a `## Decision` heading
  requirement that doesn't exist in Backhaul's ticket.md.tmpl). A Backhaul equivalent would need
  to be configurable per project or dropped in favor of Backhaul's own template-shape
  conventions (e.g. a closed ticket missing a meaningful Log entry).
- Orphaned-docs and broken-links are the two checks that port over almost directly -- both are
  generic markdown-graph problems, not LunaFlow-specific, and both are relevant across BHW wiki
  pages, BHT tickets, BHRM roadmap nodes, and BHRole role pages. These are the strongest
  candidates for a first Backhaul-native lint pass.
- Deprecation-marker checking assumes a convention (ALL-CAPS DEPRECATED + link within 10 lines)
  that doesn't exist in Backhaul today and would need to be invented or made optional.

Suggested shape (not a full design -- flagging the direction, not committing to it)
- A new command, likely `bhw lint` (wiki-scoped) or top-level `backhaul lint` (cross-service --
  tickets, wiki, roadmap, roles all have markdown bodies with links), stdlib-only like the
  original, no new dependency.
- Start with the two directly-portable checks (orphaned pages, broken links) as v1, since they
  need no project-specific convention knowledge -- just each service's own known content root
  and link-resolution rules (a generalization of what host_paths.py/handler_uri.py already do
  once each for a different purpose).
- Respect the `--project`/`--config` selection Backhaul already threads through every other
  command, so it runs against whichever project's content the rest of the CLI is pointed at.

Priority: low -- future feature, not blocking anything currently in flight. Filed to capture the
idea before it's forgotten, not as a commitment to build it soon.

## Design (locked 2026-08-14)

Command home: **`backhaul lint`**, not `bhw lint` — cross-service on purpose, since both v1
checks below need to walk tickets/wiki/roadmap/roles together, not just wiki content. Lives in
`backhaul/cli.py` alongside `dashboard`/`projects`.

V1 checks — exactly the two the ticket's own analysis flagged as directly portable, nothing
LunaFlow-specific:
1. **Orphaned pages** — any `.md` file under an enabled content root that nothing else links
   to. Exempt: the generated entry points (`BOARD.md`, `WIKI_INDEX.md`, `ROADMAP_INDEX.md`,
   `ROLES_INDEX.md`, `BACKHAUL.md`).
2. **Broken links** — a relative markdown link whose target doesn't resolve from the linking
   file. Skips `http(s)://`, `mailto:`, `editmd:`, `openfolder:`, `claude:` — none of those are
   local paths to check.

Status-drift, missing-Decision, and deprecation-marker checks (LunaFlow-specific, no direct
Backhaul equivalent per the ticket's own analysis) are explicitly out of scope for v1, not
forgotten.

Implementation: new `foundation/lint.py`, stdlib-only, no new dependency. Walks every content
root this project's config has (not just wiki), respects `--project`/`--config` like the rest
of the CLI. `--check <name>`, `--format text|json`, exit 0 (clean) / 1 (findings) / 2 (script
error) — same convention as the source tool. No auto-fix — deciding where to link an orphan
from is an editorial call, not a mechanical one.

Scope: `foundation/lint.py` (new), `backhaul/cli.py` (new `lint` subcommand), tests (fixture
content root with a deliberate orphan + a deliberate broken link + a clean control set,
asserting exact findings), `wiki/meta/bhw.md` or a new `wiki/meta/backhaul.md` cheatsheet entry.

## Log

- 2026-08-13: Ticket opened.
- 2026-08-14: Design locked — see Design section above. Not yet implemented.
- 2026-08-14: Implemented per the Design section — `foundation/lint.py`, `backhaul lint`
  subcommand, tests (`tests/test_lint.py`, CLI tests in `tests/test_dashboard.py`), docs
  (`wiki/meta/backhaul.md`, new). Full suite green (296 passed). Closed.
<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../BACKHAUL.md) · [Board](../BOARD.md) · [Folder](openfolder:///C:/_local/source/Backhaul)
<!-- bh-header:end -->
