---
id: meta/bhrole
category: meta
slug: bhrole
title: BHRole — Roles Conventions
summary: Role page ID scheme (flat slug, no registry), the Launch link mechanism,
  and CLI cheatsheet.
keywords: null
status: draft
updated: '2026-08-11'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · meta
<!-- bh-header:end -->

# BHRole — Roles Conventions

Role page ID scheme (flat slug, no registry), the Launch link mechanism, and CLI cheatsheet.

BHRole (`bhrole`) is the agent-role module — optional, gated by `enabled_modules`. Each project
using it curates its own short, hand-named list of role pages (PM, Architect, Dev, QA, ...) —
who's on the team, what they own, and a paste-in session bootstrap prompt for standing up a
fresh agent session in that role.

## Identity — flat slug, no registry

Unlike BHT/BHW/BHRM, role pages use a **flat slug identity**: a role's `id` is just its `slug`
(e.g. `qa`, `dev-test`) — no numbering, no category nesting, no shared registry file. A
project's role set is a short, hand-curated list, not a growing tree, so the ceremony a registry
buys elsewhere isn't worth it here. Filenames are `<roles_root>/<slug>.md`.

## The Launch link

Every role page can carry a `## Session bootstrap prompt` heading followed by a fenced code
block with the literal paste-in text for that role. `bhrole index`/`refresh` extract that block
verbatim and build a `claude://cowork/new?q=<prompt>` link — clicking it opens a new Cowork
session with the bootstrap prompt already in the composer, ready to review and send. A role
page with no bootstrap-prompt section just gets no Launch link — never a hard error.

Keep the fenced block as the literal text you want pasted in; don't wrap it in extra prose,
since `bhrole` extracts it byte-for-byte.

**No `folder=` param — on purpose.** The link deliberately does not auto-attach the project
folder. Observed on Windows (2026-08-11): `q` alone reliably lands in the composer, but `q`
combined with `folder` makes the composer flash the prefilled text and then silently clear
itself before it can be sent — the folder-confirmation step appears to reset composer state.
Instead, when a project root is known, `bhrole` prepends a plain sentence to the prompt itself
("This role's project folder is `<path>` — if you don't already have file access to it, ask me
to attach it before reading anything.") so the role still knows what to ask for, without
fighting that reset. If Claude Desktop's handling of `q`+`folder` together changes, this is the
place to revisit auto-attaching.

**Getting the CLI into a fresh session.** A launched Cowork session is a bare sandbox with only
the project folder attached — not Backhaul's own source, and nothing pip-installed. Without
something to fix that, the role can't run `bht`/`bhw`/`bhrm`/`bhrole` at all. Set `repo_url` in
that project's `config.local.json` (this checkout's own git remote, e.g.
`"https://github.com/amkeyte/Backhaul"`) and every Launch link gets a `pip install
"git+<repo_url>.git#subdirectory=src/Backhaul" --break-system-packages` line prepended to the
prompt, ahead of the project-folder line — the role installs its own CLI as step one, then asks
for folder access, then does whatever its own bootstrap prompt says. This re-installs from
`origin/master` every session (a fresh sandbox has nothing cached), so it only sees changes
that have actually been committed and pushed — a local, unpushed edit to `bhrole` itself won't
show up in a newly launched session until it's pushed. Omit `repo_url` to leave the install
line out of Launch links entirely.

**Where the project-folder line's path comes from.** That "This role's project folder is
`<path>`" line is computed from `content_roots` at runtime by default — correct when `bhrole`
runs on the real machine, wrong when it runs inside a role's own Cowork sandbox (a Linux VM
mounting the project under a different path than its real one). Same root cause as the Edit
link on `ROLES_INDEX.md`: both bake in wherever the CLI happened to execute unless told
otherwise. Set `host_root` in `config.local.json` (the project's real root, e.g.
`"C:\\_local\\mcRepos"`) and both get corrected — the project-folder line names `host_root`
directly, and every Edit link is re-rooted onto it. See the README's "Running from somewhere
other than the real machine" section for the general mechanism (it applies to `bht`/`bhw` too,
not just roles).

**Making the launched session's own CLI actually work.** `host_root` only fixes what gets
*printed* into links — it doesn't help the sandbox's own `bht`/`bhw`/`bhrole` calls, which still
read `content_roots` as configured (real Windows paths) and, unpatched, would silently no-op or
write stray files at cwd. A launched role should `export BACKHAUL_LOCAL_ROOT=<wherever the
project folder actually got mounted in this session>` once, right after installing the CLI and
before running any other command — every `content_roots` value then gets re-rooted onto that for
the rest of the session. See the README's "BACKHAUL_LOCAL_ROOT" section for the full mechanism.

## Frontmatter fields

`slug`, `title` (required); `persona`, `purpose`, `authority`, `reports_to`, `status`
(`active`/`retired`), `updated`. Only `active` roles count toward the dashboard's `Team` line.

## CLI cheatsheet

```
bhrole new --title "..." [--slug slug] [--persona name] [--purpose "..."] [--authority "..."] [--reports-to slug] [--status active|retired]
bhrole index [--output PATH] [--title "..."]
bhrole refresh
bhrole projects
```

`--project <name>` / `--config <path>` selects the project. Every subcommand except `projects`
refuses to run if `"roles"` isn't in that project's `enabled_modules`.

## Related pages

- [BHT — Ticket Conventions](../meta/bht.md)
- [BHW — Wiki Conventions](../meta/bhw.md)
- [BHRM — Roadmap Conventions](../meta/bhrm.md)
