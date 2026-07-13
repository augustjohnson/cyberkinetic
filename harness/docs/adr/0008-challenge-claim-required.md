# ADR-0008: `challenge-claim` is a Phase 1 required plugin

**Status:** Accepted
**Deciders:** August

## Context
Without a substantive-correctness pass, the Phase 1 deliverable is a list of CodeQL hits
with citations — obtainable from a SARIF viewer. False-positive triage is where a
product-security team's time actually goes.

## Decision
Promote `challenge-claim` (per-claim false-positive reasoning) into the required Phase 1
spine. It is the single required LLM surface in an otherwise script-only pipeline.

## Options Considered
- **Defer to Phase 2.** Rejected: leaves the MVP no better than the underlying tool.
- **Require in Phase 1** (chosen).

## Consequences
- Easier: the MVP produces something a SARIF viewer cannot — an independent second
  opinion per finding.
- Harder/accepted: first nondeterministic surface enters the required path.
- Requires: verdicts are claims-with-citations, gated like any other; `uncertain` is a
  first-class and common output (track the uncertain-rate as a health signal); MVP
  verdicts are scoped to *code-level* false positives, NOT product-reachability (no
  exposure profile yet), and verdict language must not overclaim.
- Distinct from `adversarial-review` (Phase 2), which attacks *absence*/completeness,
  not present findings.
