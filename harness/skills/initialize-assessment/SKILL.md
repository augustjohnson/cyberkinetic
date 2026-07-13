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
2. The issue is labeled `repo-scope-resolved`. This is the only valid signal that
   `.github/workflows/resolve-assessment-scope.yml` has run and succeeded — do not
   proceed on comment-presence alone, and do not proceed on an issue labeled
   `needs-maintainer` (resolution failed) or carrying no resolution label at all.
3. At least one in-scope repository is declared WITH a pinned commit SHA (not a branch,
   tag, or floating ref). Read this from the issue's `cyberkinetic:resolved-scope`
   comment, never from the raw issue body — the requester's textarea accepts unresolved
   branches, tags, and bare repo URLs, and only the workflow's comment carries a
   verified pinned SHA.
4. If an `assessment` row already exists for this issue (check `issue_ref`): re-running
   is allowed ONLY while it is still `status='initialized'` — overwrite its
   `in_scope_repo`/`declared_source` rows with the corrected scope, reusing the same
   `assessment_id`. Once `status` has advanced past `initialized`, reject; downstream
   state (checkouts, claims) already depends on the original scope.
5. The expected data sources are declared (Phase 1: one `sarif` source per repo,
   derived — see Inputs).
If any is missing, stop and get it from the requester. An assessment with vague scope
produces an assessment whose gaps are indistinguishable from real absences.
</HARD-GATE>

## When to use

- A new assessment is requested and no `assessment` row exists yet.
- Symptoms: "assess product X", a filed issue using the assessment template, "start a run".

## Inputs

| Field | Source | Notes |
|---|---|---|
| product | requester, issue body | free text, e.g. "Example Controller v3" |
| repos | **derived** — `cyberkinetic:resolved-scope` comment | `repo_url` + `resolved_sha` pairs; never the requester's raw textarea |
| declared sources | **derived** — script | one `codeql:<repo_url>@<resolved_sha>` row per resolved repo; there is no requester-facing field for this, because the key embeds a SHA the requester cannot know at submission time |
| issue_ref | derived | the issue's URL, used as the assessment's dedup key |

The requester's own input (the "In-scope repositories" textarea) accepts a bare repo URL,
a `/tree/<branch-or-tag>` URL, or a `/commit/<sha>` URL, one per line — `declared_ref` in
the resolved-scope comment records exactly what they typed, for provenance. The
`resolve-assessment-scope` workflow resolves each line to a `resolved_sha` on submission
and records the result as a `cyberkinetic:resolved-scope` issue comment, labeling the
issue `repo-scope-resolved`; an issue that fails resolution is auto-closed and labeled
`needs-maintainer` before this skill ever sees it.

## Checklist

Create a task for each and complete in order:

1. **Verify scope** against the HARD-GATE: `repo-scope-resolved` label present, product
   name present, no existing assessment for this `issue_ref`.
2. **Create the assessment row** (`status='initialized'`).
3. **Record each in-scope repo** in `in_scope_repo` (repo_url, commit_sha — from
   `resolved_sha`, not `declared_ref`).
4. **Record each declared source** in `declared_source` (`processed=0`), derived from the
   same resolved repo list.
5. **Confirm** the recorded scope back to the requester before handing off.

## Implementation

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/initialize_assessment.py" \
  --db "$ASSESSMENT_DB" \
  --issue-repo "owner/repo" \
  --issue 42
```

This script is a real implementation, not a stub (unlike its five siblings — see
`docs/DESIGN.md` §7 and the "Stub status" note in `using-cyberkinetic`). It fetches the
issue via `gh`, enforces the HARD-GATE itself, and exits non-zero with a `REJECT:`
message on any gate failure — it does not silently proceed on partial scope.

## Postconditions

- `assessment` row exists, `status='initialized'`.
- `in_scope_repo` has one row per repo with a pinned SHA.
- `declared_source` has one row per expected source, `processed=0`.

## Common mistakes

| Mistake | Why it bites |
|---|---|
| Accepting a branch/tag instead of a SHA | Non-reproducible; citations later can't be verified against a moving target. |
| Parsing the raw issue body for repo refs | The requester's textarea can hold an unresolved branch/tag/bare-repo URL; only the `cyberkinetic:resolved-scope` comment is verified and pinned. |
| Proceeding on comment-presence without checking the `repo-scope-resolved` label | An edited issue can carry a stale comment from a prior resolution attempt; the label is the authoritative "resolution succeeded" signal. |
| Re-running on an issue whose assessment already advanced past `initialized` | Downstream steps already consumed the old scope; overwriting it now would silently invalidate their state. Reject instead. |
| Skipping declared sources "to save time" | Breaks the Phase 2 "collection-complete" check; an empty slot can't be trusted as a real absence. |
| Inferring scope instead of asking | A guessed scope silently mis-frames every downstream claim. |

## Red flags — STOP

- "The SHA is probably fine, I'll use the branch head" → resolve and pin the SHA first.
- "I'll declare sources later" → declare them now; it's the checkable-completeness contract.
- "The comment looks right, I don't need to check the label" → check the label; the
  comment alone doesn't distinguish a fresh success from a stale failed attempt.
