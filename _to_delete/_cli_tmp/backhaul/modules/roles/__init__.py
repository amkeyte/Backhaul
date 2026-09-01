"""roles module (BHRole) — one page per agent-session role for a project's dev-team-of-chats:
scope, authority, and a "Session bootstrap prompt" a fresh session reads to stand up as that
role. Modeled on LunaFlow_A's Documents/ClaudeWiki/Roles/ (Supreme Leader, Architect, Game
Designer, Dev, Dev-Test, QA), generalized so any project can define its own role set. Depends
only on foundation, never on services/wiki or services/ticket directly — see
migration/ARCHITECTURE.md.

Identity is flat — just a slug (e.g. "qa"), no numbering and no category nesting, since a
project's role set is a short, hand-curated list, not a tree. Same reasoning wiki pages use
PathIdentity for a category tree; roles don't have one to nest into.

The one thing this module has that a plain wiki page doesn't: each role's own "Session
bootstrap prompt" section can be turned into a `claude://cowork/new` deep link (see
modules/roles/launch.py + foundation/claude_link.py) — click it, and Claude Desktop opens a
new Cowork session with that role's bootstrap prompt already in the composer and the project
folder attached, ready to send.
"""
