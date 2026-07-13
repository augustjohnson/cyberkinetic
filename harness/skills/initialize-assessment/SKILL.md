---
name: initialize-assessment
description: Use when starting a new cyberkinetic assessment from a scoping request or GitHub issue form, before any collection or analysis has happened.
---

# Initialize Assessment

## Overview

Turn a scoping request (typically a GitHub issue-form submission) into the assessment's
initial database state: the assessment row, the in-scope repositories at pinned commits,
and the declared data sources. This is the one skill where scope discipline matters most —
everything downstream inherits what is (and isn't) declared here.

<HARD-GATE>
Do NOT proceed to collection, analysis, or any other skill until:
1. A product name is present.
2. At least one in-scope repository is declared WITH a pinned commit SHA (not a branch,
   tag, or floating ref).
3. The expected data sources are declared (Phase 1: one `code`+`sarif` source per repo).
If any is missing, stop and get it from the requester. An assessment with vague scope
produces an assessment whose gaps are indistinguishable from real absences.
</HARD-GATE>

## When to use

- A new assessment is requested and no `assessment` row exists yet.
- Symptoms: "assess product X", a filed issue using the assessment template, "start a run".

## Inputs (from the issue form / requester)

| Field | Required | Notes |
|---|---|---|
| product | yes | free text, e.g. "Example Controller v3" |
| repos | yes | one or more `repo_url @ commit_sha` — SHA pinned, no floating refs |
| declared sources | yes | Phase 1: `codeql:<repo>@<sha>` per repo |
| issue_ref | no | GitHub issue URL/number that initiated the run |

## Checklist

Create a task for each and complete in order:

1. **Verify scope** against the HARD-GATE. Reject floating refs; require a resolvable SHA.
2. **Create the assessment row** (`status='initialized'`).
3. **Record each in-scope repo** in `in_scope_repo` (repo_url, commit_sha).
4. **Record each declared source** in `declared_source` (`processed=0`).
5. **Confirm** the recorded scope back to the requester before handing off.

## Implementation

Invoke the stub script; it echoes the parsed scope and the rows it would write.

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/initialize_assessment.py" \
  --db "$ASSESSMENT_DB" \
  --product "Example Controller v3" \
  --repo "https://github.com/example-org/example-fw@<sha>" \
  --source "codeql:example-fw@<sha>"
```

## Postconditions

- `assessment` row exists, `status='initialized'`.
- `in_scope_repo` has one row per repo with a pinned SHA.
- `declared_source` has one row per expected source, `processed=0`.

## Common mistakes

| Mistake | Why it bites |
|---|---|
| Accepting a branch/tag instead of a SHA | Non-reproducible; citations later can't be verified against a moving target. |
| Skipping declared sources "to save time" | Breaks the Phase 2 "collection-complete" check; an empty slot can't be trusted as a real absence. |
| Inferring scope instead of asking | A guessed scope silently mis-frames every downstream claim. |

## Red flags — STOP

- "The SHA is probably fine, I'll use the branch head" → resolve and pin the SHA first.
- "I'll declare sources later" → declare them now; it's the checkable-completeness contract.
