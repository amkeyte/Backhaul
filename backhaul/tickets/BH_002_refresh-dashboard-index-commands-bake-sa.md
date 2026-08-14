---
id: BH_002
uid: BH
number: 2
client: BH
status: done
title: refresh/dashboard/index commands bake sandboxed filesystem paths into generated
  links when content_roots is a cross-machine config
context: 'Summary

  When a Backhaul project''s config.local.json is authored on one machine (e.g. Windows,
  with content_roots as C:\... paths) but the CLI is invoked from a different execution
  environment where the same project directory is mounted at a different absolute
  path (e.g. a Linux container/sandbox with the project mounted at /mnt/...), there''s
  currently no way to run any command that regenerates links -- refresh, dashboard,
  index -- without corrupting every generated cross-reference link in the project
  with the sandbox''s local path instead of the canonical one.


  Background

  Backhaul''s config has a portability guard: if content_roots paths aren''t absolute
  on the machine currently running the CLI, every command refuses to proceed with
  a ConfigError ("this usually means the config was written for a different OS/machine
  ... refusing to proceed rather than silently write to the wrong place or no-op").
  That guard is correct and should stay -- but it leaves no supported path forward
  for the legitimate case where a project''s files are genuinely reachable at two
  different absolute paths from two different execution contexts (host machine vs.
  a sandboxed/containerized agent session, a WSL mount, a CI runner, etc.) but are
  the same underlying files.


  The only way to get unblocked today is to hand-write a second config with content_roots
  (and host_root, client_folders) rewritten to whatever path the current execution
  environment sees. That gets the CLI running, but it has a side effect: every command
  that regenerates links -- bht refresh/board, bhw refresh/index, bhrm refresh/index,
  bhrole refresh/index, backhaul dashboard -- derives those links from the same content_roots/host_root
  values used for file I/O. So the sandbox-local path leaks into:

  - openfolder:///... and editmd:///... links in every ticket''s/wiki page''s/role''s
  bh-header

  - The Folder/Edit columns in generated tables (BOARD.md, WIKI_INDEX.md, ROLES_INDEX.md)

  - The "This role''s project folder is ..." text embedded in each role''s generated
  claude://cowork/new?q=... Launch URL


  These links are only valid inside that one sandboxed session. Once the generated
  files are viewed from the actual host machine (or a fresh session with a different
  mount path), every one of them is broken.


  Steps to reproduce

  1. Have a Backhaul project with config.local.json written on Machine A (e.g. Windows),
  content_roots pointing at C:\Projects\example\backhaul\{tickets,wiki,roadmap,roles}.

  2. From Machine/Environment B, where the same project directory is mounted at a
  different absolute path (e.g. /mnt/example), run any Backhaul command (bht board,
  bhrm frontier, etc.) using the original config.

  3. Observe: command fails immediately with ConfigError: content_roots has path(s)
  that aren''t absolute on this machine.

  4. To proceed, write a second config (config.b.json) with content_roots/host_root/client_folders
  rewritten to Environment B''s paths (e.g. /mnt/example/backhaul/...).

  5. Run bht refresh (or bhw refresh, bhrm refresh, bhrole refresh, backhaul dashboard)
  with --config config.b.json.

  6. Observe: command succeeds, but every regenerated link in BOARD.md, WIKI_INDEX.md,
  ROLES_INDEX.md, and every individual ticket/role file''s bh-header now contains
  /mnt/example/... instead of C:\Projects\example\....

  7. Repeat step 5 at any later point (even after manually patching the paths back)
  -- the corruption recurs every time, since it''s regenerated fresh from config on
  every refresh.


  Expected behavior

  Either:

  - The CLI should support specifying the file I/O path and the canonical/display
  path separately, so a config can say "read and write files at /mnt/example/...,
  but generate all editmd://, openfolder://, and Launch-URL links using C:\Projects\example\..."
  -- with the display path defaulting to the content_root path when unset, preserving
  today''s single-machine behavior with zero config changes for the common case.

  Or, at minimum:

  - Some documented, supported way to run link-regenerating commands from a secondary
  execution environment without permanently corrupting the project''s generated files
  -- rather than the only escape hatch (a fully-translated config) being one that
  actively writes wrong data everywhere it touches.


  Actual behavior

  No supported path exists for this case. The only way to get the CLI running from
  a secondary environment is a workaround that corrupts every link-bearing generated
  file, and that corruption reoccurs on every subsequent refresh from that environment
  -- it''s not a one-time fixable event, it''s structural to how the config is used.


  Impact

  Every refresh/dashboard/index run from a secondary environment requires a manual,
  error-prone find-and-replace pass across every generated file afterward to restore
  correct paths. In one session working against a real project, this happened three
  separate times (each triggered by an otherwise-unrelated refresh call), and it''s
  easy to miss a file since the set of affected files isn''t obviously enumerable
  in advance (it''s "every file that happens to embed a content_roots- or host_root-derived
  absolute link," which varies by which sub-commands ran).


  Suggested fix

  Add an optional display_root (or similarly named) field alongside content_roots/host_root
  in config.local.json, used exclusively for generating editmd://openfolder:// links
  and Launch-URL text, distinct from the paths used for actual file reads/writes.
  Falls back to the existing behavior (display path = content root) when not set,
  so this is additive and non-breaking.


  TRIAGE NOTE (not yet investigated): this may already be addressed by host_root (separates
  display path from content_roots for links) + BACKHAUL_LOCAL_ROOT (separates the
  I/O path from content_roots, applied before the absolute-path guard) landed in tasks
  #75/#77 -- both already shipped. Needs review to confirm whether this report predates
  that work, describes a config that set host_root incorrectly (translated it along
  with content_roots instead of leaving it as the real machine''s path), or is hitting
  a real remaining gap. No action taken yet per explicit request -- open only.'
priority: high
opened: '2026-08-11'
closed: '2026-08-11'
---

<!-- board:start -->
<!-- board:end -->

## Summary

refresh/dashboard/index commands bake sandboxed filesystem paths into generated links when content_roots is a cross-machine config

## Log

- 2026-08-11: Ticket opened.
- 2026-08-11: Transferred to mcRepos (the live testbed for this class of bug) as BKHL_001, under a new `BKHL` (Backhaul) client namespace added to mcRepos's ticket registry specifically for Backhaul-tool-itself bugs. Closing here to avoid a duplicate open item — see mcRepos/backhaul/tickets/BKHL_001_refresh-dashboard-index-commands-bake-sa.md for the live copy and any further triage/resolution.
