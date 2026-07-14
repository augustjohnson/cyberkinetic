---
name: run-static-analysis
description: Use when a cyberkinetic assessment has code checked out and needs its configured static-analysis tool run to produce SARIF for claim extraction.
---

# Run Static Analysis

## Overview

Run **the configured static-analysis tool** over each checked-out repository and store
the raw SARIF output, keyed to the `(repo, sha)` it was produced from. Pure retrieval —
this skill produces the tool's output verbatim; it does not interpret it. Interpretation
is `extract-claims`; correctness judgment is `challenge-claim`.

The tool is treated as a **black box**: code in, SARIF out. Phase 1 uses **Semgrep** as a
fast, reasonably-available stand-in for a distinct internal tool this project intends to
plug in later (see ADR-0014). Nothing about this skill's contract is Semgrep-specific —
swapping tools should mean changing `run_static_analysis.py`'s internals, not this
SKILL.md or the schema.

<HARD-GATE>
Do NOT run unless `status='analyzing'` and every `in_scope_repo` row for this assessment
has a `checkout_path` (i.e. `collect-code` has fully completed — see its all-or-nothing
HARD-GATE). Store the SARIF exactly as produced. Do NOT filter, dedup, or rank results
here — every transformation happens in a later, auditable skill. Record the tool version.

Like `collect-code`, this step is **all-or-nothing**: if analysis fails for any repo,
abort before writing anything to the DB. `status` stays `analyzing` either way — this
skill never advances `status` itself. Advancing to `extracted` is `extract-claims`' job,
not this one's.
</HARD-GATE>

## When to use

- Code is collected (`status='analyzing'`) and no `analysis_run` exists yet for the
  in-scope repos.
- Symptoms: "run static analysis", "generate the SARIF", moving from collection to
  extraction.

## Checklist

1. **Read** the checkout paths from `in_scope_repo`; require `status='analyzing'` and
   every row to have a `checkout_path`.
2. **For each repo**: run the configured tool (Semgrep), capture SARIF.
3. **If analysis fails for any repo**, abort — do not write anything to the DB.
4. **Once every repo succeeds**: store an `analysis_run` row per repo (tool name/version,
   raw `sarif_blob`, its sha256, the `(repo, sha)`) and mark the matching
   `declared_source` row `processed=1`. `status` is left at `analyzing`.

## Implementation

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run_static_analysis.py" \
  --data-dir "$CYBERKINETIC_DATA_DIR" \
  --assessment "$ASSESSMENT_ID"
```

`--semgrep-config` overrides the ruleset (default `p/security-audit`) — see ADR-0014 for
why this isn't pinned to a specific ruleset version (an accepted, named determinism gap,
not solved here). Requires `semgrep` on `PATH`.

A repo with nothing the tool recognizes (e.g. a Buildroot/shell-heavy repo) still
produces a legitimate `analysis_run` with a near-empty SARIF — that's "the tool ran and
found nothing to report," not a special not-applicable state, and needs no special
handling.

## Postconditions

- One `analysis_run` per repo with raw SARIF + hash + tool version — **all of them, or
  none of them**.
- Matching `declared_source` rows marked processed.
- `status` unchanged (`analyzing`).

## Common mistakes

| Mistake | Why it bites |
|---|---|
| Pre-filtering "noise" before storage | Destroys auditability; suppression must be a later, recorded step. |
| Not recording tool version | Tool version is part of the source-reliability provenance for every derived claim. |
| Advancing `status` to `extracted` from this script | That's `extract-claims`' job — it verifies citations first. Doing it here lets `extract-claims` run on nothing. |
| Writing partial `analysis_run` rows as repos complete | This step is all-or-nothing, same as `collect-code` — write nothing until every repo has succeeded. |
| Hardcoding "CodeQL" (or "Semgrep") into the skill's contract | The tool is swappable by design (ADR-0014); keep the skill's language tool-agnostic even when a concrete tool is plugged in. |
