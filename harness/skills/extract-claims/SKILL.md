---
name: extract-claims
description: Use when a cyberkinetic assessment has stored SARIF that needs mapping into claims with verifiable git-coordinate citations.
---

# Extract Claims

## Overview

Map each SARIF **result** into one **claim** with a git-coordinate citation. For Phase 1
this is schema translation, not inference: SARIF already carries the assertion, the
location, and tool provenance. The value this skill adds is the **citation-verification
gate** — the strongest firewall in the pipeline.

**One claim per SARIF result** (not per rule). Precise, independently verifiable citations;
list-noise is handled later at render. See `docs/adr/0007`.

<HARD-GATE>
Before writing ANY claim, verify its citation resolves at the cited SHA: fetch the cited
line range from the actual file at that commit and confirm it exists and matches.
- Resolves → write the claim with `citation_verified=1`.
- Does NOT resolve → do NOT write the claim. Log it as an extraction/tool error. A result
  whose location doesn't exist at its SHA is a pipeline-health signal, not a finding.
Attaching a citation is NOT the same as verifying it. No unverified claim enters the DB.
</HARD-GATE>

## When to use

- `analysis_run` rows exist and claims have not been extracted.
- Symptoms: "turn the SARIF into claims", "extract findings", moving analysis → claims.

## Mapping (per SARIF result → claim)

| SARIF field | Claim field | Note |
|---|---|---|
| `ruleId` + rule short description | `assertion` | corpus-relative statement |
| `message.text` | `detail` | verbatim; do not paraphrase |
| `physicalLocation` (uri, region) | `citation` (repo, sha, path, line_start/end) | git coordinate |
| `tool.driver` name+version | `source_reliability='tool'` | provenance, not judgment |
| `level` / `security-severity` | `source_severity` | recorded ONLY; never our triage signal |
| `fingerprints` / composite | `dedup_key` | so re-runs update, not duplicate |

Axes: set `source_reliability='tool'` and `applicability='applicable'` (Phase 1 trivial).
Leave `credibility` and `scope_match` as `unset` — do not fabricate values for deferred
axes.

## Checklist

1. **Parse** each `analysis_run`'s SARIF.
2. **For each result**: build the candidate claim + git-coordinate citation.
3. **GATE**: verify the citation resolves at the SHA (see HARD-GATE). Reject on failure.
4. **Dedup** on `dedup_key` (update existing rather than insert a duplicate).
5. **Write** surviving claims + citations. Record `source_severity` as an attribute only.
6. **Advance** `status` to `extracted`.

## Implementation

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/extract_claims.py" --db "$ASSESSMENT_DB" --assessment "$ASSESSMENT_ID" \
  --cache-dir "$CHECKOUT_CACHE"
```

The stub echoes, per result: the claim it would write, the citation, and the
verify-at-SHA check it would perform.

## Postconditions

- One claim per surviving SARIF result, each with a `citation_verified=1` citation.
- Rejected results logged (not written as claims).
- `source_severity` stored as provenance; NOT mapped to any finding severity.
- `status='extracted'`.

## Common mistakes

| Mistake | Why it bites |
|---|---|
| Writing claims without the SHA-resolution check | Lets hallucinated/misaligned locations in; defeats the firewall. |
| Mapping SARIF `level` into a finding severity | Reintroduces CVSS-shaped ranking we rejected (adr/0006). |
| Collapsing many results into one per-rule claim | Loses per-instance citation and blocks per-instance verdicts. |
| Filling `credibility`/`scope_match` with a default | A default is indistinguishable from a real value; use `unset`. |

## Red flags — STOP

- "The citation is attached, that's good enough" → attachment ≠ entailment. Resolve it at
  the SHA.
- "This result looks obviously real, skip the check" → the check is mechanical and cheap;
  no exceptions.
