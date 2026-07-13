# ADR-0009: Deterministic work in scripts; LLM only for judgment

**Status:** Accepted
**Deciders:** August

## Context
Reproducibility and testability improve as work becomes deterministic. LLM calls are
nondeterministic and harder to test headless.

## Decision
Any work that yields the same output from the same input is a script the agent invokes.
The LLM layer is reserved for reasoning over ambiguity. A skill's SKILL.md is the
interface + gate; a called script is the deterministic core. Judgment skills
(`challenge-claim`, and Phase 2 interview/adversarial-review) keep reasoning agent-side.

## Options Considered
- **Agent does the work directly.** Rejected: nondeterministic, hard to test, no headless
  runs.
- **Scripts for deterministic work, thin agent wrapper** (chosen).

## Consequences
- Easier: pipeline runs and is testable outside the agent; local runs during tuning.
- Test: any LLM surface that could be a script is an accepted nondeterminism we must be
  able to justify (Phase 1: only `challenge-claim` qualifies as legitimately LLM).
