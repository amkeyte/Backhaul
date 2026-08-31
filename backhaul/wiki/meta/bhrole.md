---
id: meta/bhrole
category: meta
slug: bhrole
title: BHRole — Agent Role Conventions
summary: Role page ID scheme, why bootstrap prompts must stay evergreen, the Launch
  link mechanism, and CLI cheatsheet.
keywords: null
status: draft
updated: '2026-08-11'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · meta
<!-- bh-header:end -->

# BHRole — Agent Role Conventions

Role page ID scheme, why bootstrap prompts must stay evergreen, the Launch link mechanism, and
CLI cheatsheet.

BHRole (`bhrole`) is the agent-role module — optional, gated by `enabled_modules`. Each project
using it curates its own short, hand-named list of role pages (PM, Architect, Dev, QA, ...) —
who's on the team, what they own, and a paste-in session bootstrap prompt for standing up a
fresh agent session in that role.

## Roles are not status pages — point at one, don't become one

**A role file describes a stable job description, not what's happening right now.** It's
tempting to bake in whatever's true today — "read these three specific files," "X is currently
in draft, that's your first task," "as of 2026-08-11, Y was removed" — because it feels helpful
in the moment. It rots immediately: the next time this role gets launched, the bootstrap prompt
still says to read files that may be resolved, closed, renamed, or gone, and nobody's job is to
remember to go back and edit the role file when that happens.

The fix: **role files point at `BACKHAUL.md`** (the root status point — Work Board, Wiki Index,
Roadmap, Team, all in one place) **instead of duplicating what's in it.** A bootstrap prompt
should say "read BACKHAUL.md and follow its links" and "check the Wiki Index for anything marked
`draft` in a category you own," not "read `fixture.md`, it's draft as of today." The former is
evergreen — it stays correct no matter what's actually draft or open when the role is next
launched. The latter is a snapshot with an expiration date.

This means `BACKHAUL.md` itself has to actually be current, which is the other half of this:
**run `backhaul dashboard` as part of any refresh, not just `bht`/`bhw`/`bhrm`/`bhrole`
individually.** Refreshing the sub-indexes without refreshing the root dashboard is how
`BACKHAUL.md` silently goes stale while everything underneath it looks fine.

What's fine to keep in a role file: authority boundaries, what the role does in general terms,
who it hands off to, and *links* to specific tickets/wiki pages/roadmap nodes when a human
explicitly assigns one for the session ("I will tell you which" — a placeholder, not a filled-in
answer). What doesn't belong: dated narratives, "as of" status snapshots, or anything that would
need active maintenance to stay true.

## ID scheme

A role's ID is just its `slug` (e.g. `qa`, `dev-test`) — no numbering, no category nesting, no
shared registry file, unlike BHT/BHW/BHRM. A project's role set is a short, hand-curated list,
not a growing tree, so the ceremony a registry buys elsewhere isn't worth it here. Filenames are
`<roles_root>/<slug>.md`.

## The Launch link

Every role page can carry a `## Session bootstrap prompt` heading followed by a fenced code
block with the literal paste-in text for that role. `bhrole index`/`refresh` extract that block
verbatim and build a `claude://cowork/new?q=<prompt>` link — clicking it opens a new Cowork
session with the bootstrap prompt already in the composer, ready to review and send. A role
page with no bootstrap-prompt section just gets no Launch link — never a hard error.

**A role can open Claude Code instead of Cowork (BH_003).** Set `launch_target: code` in a role
page's frontmatter (`--launch-target code` at `bhrole new`) and its Launch link builds
`claude://code/new?q=<prompt>` instead — same prompt-extraction and preamble logic either way,
just a different `claude://` host segment. Defaults to `cowork` (this module's only prior
behavior), so every existing role page is unaffected until it opts in.

Keep the fenced block as the literal text you want pasted in; don't wrap it in extra prose,
since `bhrole` extracts it byte-for-byte.

**No `folder=` param — on purpose.** The link deliberately does not auto-attach the project
folder. Observed on Windows (2026-08-11): `q` alone reliably lands in the composer, but `q`
combined with `folder` makes the composer flash the prefilled text and then silently clear
itself before it can be sent — the folder-confirmation step appears to reset composer state.
Instead, when a project root is known, `bhrole` prepends a plain sentence to the prompt itself
("This role's project folder is `<path>`. If you don't already have file access to it, call your
folder-request tool now to prompt me for it — don't just tell me you don't have access.") so the
role still knows what to ask for, without fighting that reset. If Claude Desktop's handling of
`q`+`folder` together changes, this is the place to revisit auto-attaching.

**Wording matters here, not just presence.** An earlier, softer version of this line ("ask me to
attach it") was observed being satisfied by a launched role just typing "I don't have access" in
chat, rather than calling the tool that actually surfaces a permission prompt to the human — the
human then had to notice that and attach the folder manually anyway, defeating the point of the
preamble. The current wording explicitly names the action (call the tool) and explicitly
disallows the failure mode (don't just say so) for exactly that reason.

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

## Status vocabulary

`active` — currently staffed/in use. `retired` — kept on file but not currently launched.
Informational only, same as BHW; nothing gates on it.

## Title length

`ROLES_INDEX.md` renders each role's title as a table column — same reasoning as BHT's length
standard (see `meta/bht.md`). Role titles are short by nature ("PM", "Architect", "Lead Dev"),
so this rarely comes up, but the same ≤ ~40 character target applies if a role ever gets a
longer name.

## Frontmatter fields

`slug`, `title` (required); `persona`, `purpose`, `authority`, `reports_to`, `status`
(`active`/`retired`), `launch_target` (`cowork`/`code`, see above), `updated`. Only `active`
roles count toward the dashboard's `Team` line.

## CLI cheatsheet

```
bhrole new --title "..." [--slug slug] [--persona name] [--purpose "..."] [--authority "..."] [--reports-to slug] [--status active|retired] [--launch-target cowork|code]
bhrole index [--output PATH] [--title "..."]   # rebuild ROLES_INDEX.md
bhrole refresh                                  # recompute headers + rebuild the roster
bhrole projects
```

`--project <name>` / `--config <path>` selects the project. Every subcommand except `projects`
refuses to run if `"roles"` isn't in that project's `enabled_modules`.

## Related pages

- [BHT — Ticket Conventions](../meta/bht.md)
- [BHW — Wiki Conventions](../meta/bhw.md)
- [BHRM — Roadmap Conventions](../meta/bhrm.md)
- [Backhaul — Cross-Service Command Conventions](../meta/backhaul.md)
