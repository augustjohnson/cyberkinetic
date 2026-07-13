# ADR-0002: Two-axis claim confidence (Admiralty), extended to four with two deferred

**Status:** Accepted
**Deciders:** August

## Context
A single "confidence %" conflates two independent questions — how much we trust the
source vs. how firmly the source asserts the claim — and on LLM output a percentage is
false precision. We also need to express whether a claim bears on the product at all,
and on this specific instance.

## Decision
Adopt the Admiralty/NATO two-axis model (source reliability × information credibility)
and extend with two assessment-relative axes (applicability, scope-match). Keep all
four visibly separate to the finding. Phase 1 populates the two collection-time axes
(reliability, applicability) and stores the two evaluation-time axes as `unset`.

## Options Considered
- **Single scalar confidence.** Rejected: conflates source vs. assertion; fake
  precision on LLM output; cannot drive distinct routing.
- **Two axes only.** Good, but cannot express product-relevance or instance-scope.
- **Four axes, two deferred** (chosen). Distinct routing per axis (better source /
  confirm vague source / drop irrelevant / suppress scope-conflict); intrinsic vs.
  evaluative split is explicit.

## Consequences
- Easier: interview/verification routing falls out of *which* axis is low.
- Harder: four fields to reason about; two are LLM-produced (Phase 2).
- Requires: an explicit `unset` state so deferred axes never masquerade as computed.
- Note: reliability+applicability are cacheable across runs; credibility+scope-match are
  recomputed per assessment.
