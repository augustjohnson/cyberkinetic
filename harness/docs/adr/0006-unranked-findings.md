# ADR-0006: Findings unranked with a consequence story; no ordinal severity scale

**Status:** Accepted
**Deciders:** August

## Context
CVSS is confidentiality-weighted and context-free; it misranks OT/physical-consequence
issues (ambient data "exposure" scores like a real breach). But consequence categories
alone
("loss of control") are not orderable, so triage has no defined operation.

## Decision
Present findings unranked, each with a short story carrying its consequence dimensions
(impact, remoteness, persistence, stealth, scale, safety). Ranking is a human curation
layer. Record any tool-provided CVSS/severity as a source attribute only; never triage
on it.

## Options Considered
- **CVSS-driven ranking.** Rejected: false precision, wrong frame for OT.
- **New ordinal consequence scale.** Rejected for now: reintroduces scoring
  subjectivity we were avoiding.
- **Unranked + story + human curation** (chosen).

## Consequences
- Easier: no fabricated ordering; the curator sorts on stated properties.
- Harder/accepted: no automatic "what first" — deliberately a human judgment.
- Requires: render must surface the consequence dimensions, not just the assertion.
