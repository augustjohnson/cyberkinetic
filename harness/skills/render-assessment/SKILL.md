---
name: render-assessment
description: Use when a challenged cyberkinetic assessment needs its claims and verdicts rendered into a human-readable, access-controlled view for curation.
---

# Render Assessment

## Overview

Produce the human-readable output: each claim with its resolvable citation and its
`challenge-claim` verdict, for a human to curate. Findings are **unranked** — each carries
a short story, and ordering is a human judgment, not an algorithm. See `docs/adr/0006`.

<HARD-GATE>
1. The rendered output MUST NOT be published to the public internet. It is an attack-path
   document. Write it to an access-controlled or unpublished location only.
2. Do NOT rank or score findings. Do NOT surface `source_severity` as a ranking. Present
   unranked, with consequence dimensions stated so a human can sort.
3. Every rendered finding MUST show its citation (resolvable to the exact SHA/line) and
   its verdict (including `uncertain`).
</HARD-GATE>

## When to use

- Claims are `challenged` and no current render exists.
- Symptoms: "render the report", "produce the findings view", "let me see the results".

## What each rendered finding shows

- The claim's assertion and verbatim tool detail.
- Its citation as a resolvable git coordinate (repo, sha, path, lines).
- Its verdict: `likely_true_positive` / `likely_false_positive` / `uncertain`, with the
  verdict's cited rationale.
- Its recorded `source_severity` — labeled as the tool's opinion, NOT as a ranking.
- Grouping by rule is allowed for readability (presentation only; the model stays granular).

## Checklist

1. **Read** claims + citations + verdicts for the assessment.
2. **Render** the unranked view (group by rule for readability if desired).
3. **Write** the output to an access-controlled path; record it in `render_output`.
4. **Advance** `status` to `rendered`.

## Implementation

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/render_assessment.py" --db "$ASSESSMENT_DB" --assessment "$ASSESSMENT_ID" \
  --out "$RENDER_DIR"
```

The stub echoes the claims+verdicts it would render and the access-controlled path it
would write to.

## Postconditions

- A rendered artifact at an access-controlled path, referenced in `render_output`.
- Findings unranked, each showing citation + verdict + consequence context.
- `status='rendered'`.

## Common mistakes

| Mistake | Why it bites |
|---|---|
| Publishing to GitHub Pages / a public repo | Leaks attack paths against real products. |
| Sorting by `source_severity` | Reintroduces the CVSS-shaped ranking we rejected. |
| Hiding `uncertain` verdicts | Those are exactly the ones a human most needs to review. |
