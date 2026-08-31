<!-- bh-header:start -->
**Backhaul** — [Dashboard](../BACKHAUL.md)
<!-- bh-header:end -->

# Wiki Index

## design

| Title | Status | Summary | Edit |
|---|---|---|---|
| [Architecture — Foundation, Services, Modules](wiki/design/architecture.md) | published | Why BHT and BHW are services on one shared foundation, and what a new service vs. module costs. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/design/architecture.md) |
| [BH_010-021 Implementation Architecture](wiki/design/bh010-021-architecture.md) | draft | Shared foundation-layer primitives and build order for the twelve tickets filed off tonight's BKHL audit. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/design/bh010-021-architecture.md) |
| [Dev Branch Handoff -- 2026-08-30](wiki/design/dev-branch-handoff.md) | draft | Orients a fresh agent picking up the dev branch cold: what's on it, why, verification status, what's still open, and whether a version bump is needed. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/design/dev-branch-handoff.md) |
| [Dev Branch Test Checklist -- 2026-08-31](wiki/design/dev-branch-test-checklist.md) | draft | Copy-pasteable checklist for an agent on a fresh test machine to exercise before this branch goes further -- especially the new --version/branch-identification mechanism, which has only been tested from this repo's own editable dogfooding install so far. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/design/dev-branch-test-checklist.md) |
| [Foundation Design — the Engine BHT and BHW Specialize](wiki/design/foundation-design.md) | published | The primitive toolkit (frontmatter, identity, templating, rollup, refs) BHT and BHW each wire together. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/design/foundation-design.md) |
| [Backhaul Migration Plan](wiki/design/migration-plan.md) | published | The Aaron K -> Backhaul migration: goals, phases, config/versioning design, decisions log. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/design/migration-plan.md) |
| [Module System — the Poor Man's Plugin Design](wiki/design/module-system.md) | published | The enabled_modules design — foundation/services/modules layering and module packaging. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/design/module-system.md) |
| [Python Project Setup — Backhaul.sln](wiki/design/python-project-setup.md) | published | The Python package layout, VS2022 project setup, and .gitignore additions. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/design/python-project-setup.md) |
| [Solution Layout — What Lives in Backhaul.sln](wiki/design/solution-layout.md) | published | What lives in Backhaul.sln — the four Solution Explorer groupings. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/design/solution-layout.md) |
| [Version & Branch Identification Convention](wiki/design/version-branch-convention.md) | verified | Locked convention: how a package version signals which branch you're running, so a wrong-branch checkout is never silent. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/design/version-branch-convention.md) |
| [Version & Schema Compatibility Plan](wiki/design/version-compat.md) | draft | How framework/module/instance versions interact: schema_version stamped per file, explicit migrate command, hard-fail on unmigratable drift. Supersedes the git-diff drift-check sketch in migration-plan.md §6. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/design/version-compat.md) |

## meta

| Title | Status | Summary | Edit |
|---|---|---|---|
| [Backhaul — Cross-Service Command Conventions](wiki/meta/backhaul.md) | draft | The top-level backhaul CLI: dashboard, lint, projects — commands that span every service instead of belonging to one. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/meta/backhaul.md) |
| [BHRM — Roadmap Conventions](wiki/meta/bhrm.md) | draft | Roadmap node ID scheme, why short slugs matter here, and CLI cheatsheet. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/meta/bhrm.md) |
| [BHRole — Agent Role Conventions](wiki/meta/bhrole.md) | draft | Role page ID scheme, why bootstrap prompts must stay evergreen, the Launch link mechanism, and CLI cheatsheet. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/meta/bhrole.md) |
| [BHT — Ticket Conventions](wiki/meta/bht.md) | draft | Ticket ID scheme, slug convention, and CLI cheatsheet. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/meta/bht.md) |
| [BHW — Wiki Conventions](wiki/meta/bhw.md) | draft | Wiki page ID scheme, slug convention, and CLI cheatsheet. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/meta/bhw.md) |

## overview

| Title | Status | Summary | Edit |
|---|---|---|---|
| [Backhaul — Glossary](wiki/overview/glossary.md) | published | Terminology used across Backhaul: services, modules, config, identity, and roadmap concepts. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/overview/glossary.md) |
| [Backhaul — System Overview](wiki/overview/readme.md) | published | Setup, project registry, module usage, and repo layout overview. | [Edit](editmd:///C:/_local/source/Backhaul/backhaul/wiki/overview/readme.md) |
