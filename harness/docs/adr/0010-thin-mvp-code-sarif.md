# ADR-0010: Phase 1 MVP is thin, straight-through, code + SARIF only

**Status:** Accepted
**Deciders:** August

## Context
The designed system (cyclic cascade, fusion, review loops, exposure projection, index
repo) is far larger than a first deliverable. Risk: build the framework forever and
never assess a product; infra is more fun than characterization.

## Decision
Phase 1 is a single straight-through pass over source code at pinned commits + CodeQL
SARIF, with no loops, no fusion, no interviews, no floor. Six plugins. "End-to-end"
means the shortest path from artifact to a human reading a cited, challenged claim.

## Options Considered
- **Full cascade as run one.** Rejected: months to first result; the core assumption
  (extraction quality) untested until after the structure is built.
- **Thin straight-through spine** (chosen). Cascade machinery layers onto a working
  spine afterward.

## Consequences
- Easier: a real result on real code early; the extraction-quality assumption is tested
  first.
- Discipline: only DESIGN.md may mention Phase 2+, and only by name. Schema, plan,
  skills, README are Phase-1-only.
- SARIF is a shrewd first artifact: it is a structured claim-with-citation already, has
  mechanical citation verification, and carries tool provenance for free.
