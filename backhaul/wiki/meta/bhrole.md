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
