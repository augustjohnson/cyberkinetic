---
name: run-static-analysis
description: Use when a cyberkinetic assessment has code checked out and needs CodeQL run to produce SARIF for claim extraction.
---

# Run Static Analysis

## Overview

Run CodeQL over each checked-out repository and store the raw SARIF output, keyed to the
`(repo, sha)` it was produced from. Pure retrieval — this skill produces the tool's
output verbatim; it does not interpret it. Interpretation is `extract-claims`; correctness
judgment is `challenge-claim`.

<HARD-GATE>
Do NOT run unless the repositories are checked out (`in_scope_repo.checkout_path` set).
Store the SARIF exactly as produced. Do NOT filter, dedup, or rank results here — every
transformation happens in a later, auditable skill. Record the tool version.
</HARD-GATE>

## When to use

- Code is collected and no `analysis_run` exists yet for the in-scope repos.
- Symptoms: "run CodeQL", "generate the SARIF", moving from collection to extraction.

## Checklist

1. **Read** the checkout paths from `in_scope_repo`.
2. **For each repo**: run CodeQL, capture SARIF.
3. **Store** an `analysis_run` row: tool name/version, the raw `sarif_blob`, its sha256,
   and the `(repo, sha)`.
4. **Mark** the matching `declared_source` row `processed=1`.
5. **Advance** `status` to `analyzing`.

## Implementation

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run_static_analysis.py" --db "$ASSESSMENT_DB" --assessment "$ASSESSMENT_ID" \
  --cache-dir "$CHECKOUT_CACHE"
```

The stub echoes the CodeQL invocation it would run per repo and the `analysis_run` row it
would write.

## Postconditions

- One `analysis_run` per repo with raw SARIF + hash + tool version.
- Matching `declared_source` rows marked processed.
- `status='analyzing'`.

## Common mistakes

| Mistake | Why it bites |
|---|---|
| Pre-filtering "noise" before storage | Destroys auditability; suppression must be a later, recorded step. |
| Not recording tool version | Tool version is part of the source-reliability provenance for every derived claim. |
