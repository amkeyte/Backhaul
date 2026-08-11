---
id: design/foundation-design
category: design
slug: foundation-design
title: Foundation Design — the Engine BHT and BHW Specialize
summary: The primitive toolkit (frontmatter, identity, templating, rollup, refs) BHT
  and BHW each wire together.
keywords: null
status: published
updated: '2026-08-11'
---

<!-- bh-header:start -->
**Backhaul** — [Dashboard](../../../BACKHAUL.md) · [Wiki Index](../../WIKI_INDEX.md) · design
<!-- bh-header:end -->

# Foundation Design — the engine BHT and BHW specialize

**Status:** Draft.
**Depends on:** `ARCHITECTURE.md` (layer model this fills in). Referenced by `services/ticket`
and `services/wiki` once they're built (`MIGRATION_PLAN.md` §9, phases 2–3).

## 0. Why this isn't one `Collection` class

Working `ARCHITECTURE.md`'s claim through against the real legacy scripts (`new_ticket.py`,
`build_board.py`, `new_page.py`, `build_index.py`) shows tickets and wiki pages share a lot,
but not everything:

| | Ticket (BHT) | Wiki (BHW) |
|---|---|---|
| Identity | Numbered: `<UID>_<NNN>[_slug]` — needs a registry (`client-uids.md`) to assign UIDs and scan a directory to find the next number | Path-based: `<category>/<slug>` — no registry, no numbering, the path *is* the identity |
| Rollup | One document (the board), filtered to open states only | Two kinds (a master index + one per category), includes everything regardless of status |
| Nav block | `board:start`/`board:end` — Work Board link + Edit + Folder links | `breadcrumb:start`/`breadcrumb:end` — parent-category trail |

Different enough that forcing both through a single `Collection(schema)` class would mean
that class either grows a pile of ticket-only and wiki-only special cases, or wiki gets a
fake numbering scheme it doesn't need. Instead: **a toolkit of independent primitives**, each
handling one mechanic, that a service wires together according to its own shape. This also
makes each primitive independently unit-testable, which the loose legacy scripts weren't —
`first_next()`'s regex and the frontmatter-parsing regex, for instance, currently only get
exercised as a side effect of running the whole script against real files.

## 1. The primitives (`foundation/`)

```python
# frontmatter.py
def parse(text: str) -> tuple[dict, str]:
    """Split a file into (frontmatter dict, body). Raises on malformed/missing frontmatter."""

def render(frontmatter: dict, body: str) -> str:
    """Inverse of parse() — used when a service needs to rewrite a file's frontmatter
    (e.g. status change, updated date) without hand-editing the block."""
```

```python
# slugify.py
def slugify(s: str, maxlen: int = 40) -> str:
    """Same behavior as both legacy slugify()s — lowercase, non-alnum -> '-', trimmed."""
```

```python
# identity.py
class NumberedIdentity:
    """UID + sequential number, e.g. PREC_003. Used by BHT."""
    def __init__(self, registry_path: Path, prefix_for: Callable[[str], str]): ...
    def next_id(self, context: str, existing_dir: Path) -> str: ...
    def suggest_prefix(self, context: str) -> str: ...  # auto-suggest + confirm, per existing UX

class PathIdentity:
    """category/slug, e.g. reference/das-project-lifecycle. Used by BHW. No registry."""
    def make_id(self, category: str, slug: str) -> str: ...
```

```python
# templating.py
def render_template(tmpl_path: Path, tokens: dict[str, str]) -> str:
    """%%TOKEN%% substitution — same mechanism both legacy .md.tmpl files already use."""
```

```python
# filesafety.py
def write_new(path: Path, content: str, force: bool = False) -> None:
    """Refuses to overwrite an existing file unless force=True. Identical rule in both
    new_ticket.py and new_page.py today — one implementation instead of two."""
```

```python
# markers.py
def refresh_marked_block(path: Path, start_marker: str, end_marker: str,
                          block_text: str) -> None:
    """Idempotent insert/replace of a generated block between two HTML-comment markers.
    Generalizes both refresh_board_link() (board:start/end) and the wiki breadcrumb
    rewriter (breadcrumb:start/end) into one function — same operation, different
    marker strings and different block content."""
```

```python
# rollup.py — collect/filter/group only. Rendering is NOT shared (see §6, decided).
@dataclass
class CollectSpec:
    source_dirs: list[Path]
    parse_fn: Callable[[Path], dict | None]
    include_fn: Callable[[dict], bool]      # ticket: status in OPEN_STATES; wiki: always True
    group_fn: Callable[[dict], str] | None   # ticket: by status; wiki: by category

def collect(spec: CollectSpec) -> dict[str, list[dict]]:
    """Walks source_dirs, parses each file's frontmatter, filters, groups. Returns grouped
    items — rendering them into a board table vs. a category index is each service's own
    job (services/ticket/board.py, services/wiki/index.py), not foundation's."""
```

```python
# refs.py
@dataclass
class Ref:
    kind: str    # "ticket" | "wiki"
    id: str      # "PREC_003" | "reference/das-project-lifecycle"

def resolve(ref: Ref, cfg: Config) -> Path | None:
    """Where does this reference point, if it exists?"""

def check_integrity(refs: list[Ref], cfg: Config) -> list[Ref]:
    """Which refs are broken (target doesn't exist)? Powers the link-integrity check
    flagged in ARCHITECTURE.md §3, and doubles as the guard against the two independent
    wikis silently drifting apart."""
```

```python
# version_check.py
def check(repo_version_path: Path, config: Config) -> str | None:
    """Compares VERSION to config.setup_version. Returns None if they match, otherwise a
    git-log-based plain-language summary of what changed (MIGRATION_PLAN.md §6)."""
```

## 2. How BHT wires these together

- **Identity:** `NumberedIdentity` against `client-uids.md`.
- **Template:** `ticket.md.tmpl`, tokens = `ID, CONTEXT, TITLE, STATUS, PRIORITY, DATE, BOARDLINK`.
- **Nav block:** `refresh_marked_block(..., "<!-- board:start -->", "<!-- board:end -->", ...)`
  generating the Work Board / Edit / Folder links.
- **Rollup:** one `CollectSpec` — `include_fn` keeps only `open`/`in-progress`/`blocked`,
  `group_fn` groups by status. `services/ticket/board.py` renders the grouped result into the
  board's markdown table (Ticket/Context/Pri/Title/Next/Edit columns) — table-shaped
  rendering lives here, not in `foundation.rollup`.
- **Lifecycle:** `open -> in-progress|blocked -> done`. `done` tickets excluded from the
  rollup but stay on disk (unchanged behavior from today).

## 3. How BHW wires these together

- **Identity:** `PathIdentity` — category + slug, nested categories supported
  (`knowledge-base/clients/precision`), no registry.
- **Template:** `page.md.tmpl`, tokens = `TITLE, SLUG, CATEGORY, SUMMARY, KEYWORDS, STATUS, DATE, BREADCRUMB`.
- **Nav block:** `refresh_marked_block(..., "<!-- breadcrumb:start -->", "<!-- breadcrumb:end -->", ...)`
  generating the parent-category trail.
- **Rollup:** multiple `CollectSpec` calls — one master index (all pages), one per category
  index. `include_fn` always `True` — wiki doesn't hide pages by status the way tickets hide
  `done`. `services/wiki/index.py` renders the grouped result into its own shape (category
  listings + breadcrumb trail, not a table) — its own renderer, sharing only `collect()`
  with BHT, not any table-rendering code.
- **Lifecycle:** `draft -> verified/published`, informational only — doesn't gate inclusion
  in any rollup, unlike ticket status.

## 4. Cross-references between BHT and BHW

Answers the "can they know about each other" requirement from `ARCHITECTURE.md` §3. A ticket's
frontmatter or body can carry `Ref("wiki", "reference/das-project-lifecycle")`; a wiki page can
carry `Ref("ticket", "PREC_003")`. Both services import `foundation.refs`, neither needs to
know the other's internals — `resolve()` just needs `config.content_root` to find either
tree. `check_integrity()` is the hook for a future pre-commit or periodic check ("does every
referenced ticket/page still exist"), not built as an automated gate yet — noted as a
possible follow-up in `MIGRATION_PLAN.md` §10, not committed to here.

## 5. Testing implications

Each primitive above gets its own `tests/test_<primitive>.py` against small synthetic
fixtures — this is what makes the pytest suite from `MIGRATION_PLAN.md` §8 actually
meaningful rather than "run the whole script and eyeball the output" (today's only real
verification method, per the whole conversation's worth of manual `soffice.py` renders and
`pdftoppm` screenshots for the docx work — fine for one-off changes, not something to rely on
as an ongoing regression check). `services/ticket` and `services/wiki` then get their own
smaller test files that check the *wiring* — schema, lifecycle, identity choice — rather than
re-testing the primitives' internals.

## 6. Rendering: decided, not shared

**Decided (2026-07-31): rendering is separate per service.** `foundation.rollup` only
collects/filters/groups (`CollectSpec` → `collect()`); turning that into an actual document —
a status-grouped table for the board, a category listing with breadcrumbs for the wiki
index — is `services/ticket/board.py` and `services/wiki/index.py` each doing their own
rendering. They share the walk-and-filter step, not the output shape. Simpler than trying to
find one rendering abstraction that honestly fits two visually different documents.
