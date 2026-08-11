"""roadmap module (BHRM) — dependency-graph roadmap tracking, ported from LunaFlow_A's
RoadmapGraph proposal (Documents/ClaudeWiki/RoadmapGraph/) and its scripts/roadmap/
roadmap_graph.py implementation. Depends only on foundation, never on services/ticket or
services/wiki directly — see migration/ARCHITECTURE.md.

Every unit of roadmap-load-bearing work is a node with a stable ID and explicit `depends_on`
edges, replacing a flat phase-number sequence. Two kinds: work nodes (terminal once resolved)
and convergence nodes (milestones, reversible between WIP/reached). See
../../../../intake/roadmap-nodes/design/proposal.md for the full rationale this was built from.

ID scheme (Backhaul's own — not identical to the original LunaFlow prototype's bare "RM-NNNN"):
node IDs reuse foundation.identity.NumberedIdentity, e.g. "RM_ARR_001" — uid = "RM_" + a
client short code (ARR, FRO, SAT, ...), scoped through the same client-uids.md registry BHT
uses (foundation.client_registry). Each UID is a fully independent graph: every query is
scoped to one UID, and a DependsOn entry crossing UIDs is a hard error, not a cross-project
link — "one node system each" per client/mod, enforced mechanically.
"""
