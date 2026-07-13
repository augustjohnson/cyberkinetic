# ADR-0007: One claim per static-analysis result; group at render

**Status:** Accepted
**Deciders:** August

## Context
CodeQL emits many results per rule. Modeling one claim per rule (with N locations)
yields a cleaner list but a blurry citation; one claim per result yields precise
citations but a noisier list.

## Decision
One claim per SARIF result. The render layer may group by rule for readability. This
aligns with internal triage processes.

## Options Considered
- **Per-rule with N locations.** Rejected: lossy citation; `challenge-claim` cannot
  issue a per-instance verdict; hard to un-collapse.
- **Per-result, grouped at render** (chosen).

## Consequences
- Easier: precise, independently verifiable citations; per-instance verdicts.
- Harder: list noise — handled as a presentation concern in render, not in the model.
- Requires: a `dedup_key` (SARIF fingerprint) so re-runs update rather than duplicate.
