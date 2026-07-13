---
name: challenge-claim
description: Use when extracted cyberkinetic code claims need an independent judgment of whether each is a likely true or false positive before human curation.
---

# Challenge Claim

## Overview

For each code claim, reason about whether the underlying finding is actually right or a
false positive, and write a **verdict** back. This is the one LLM skill in the Phase 1
spine — its value is judgment a script cannot do: reading the surrounding code and
assessing whether the flagged issue holds up.

**Two verification axes, and this is the second one:**
- `extract-claims` verified the claim is *faithful to the tool* (does the line resolve).
- `challenge-claim` verifies the claim is *substantively right* (is it a false positive).

A verdict is **another claim** (`kind='verdict'`), with its own `source_reliability='llm'`
(lower than tool-derived) and its own citations. It is a **recommendation to a curator**,
not a truth oracle and not an auto-suppression.

<HARD-GATE>
1. Every verdict MUST cite the specific lines that justify it (the upstream validation,
   the parameterized sink, the dead path). A verdict with no citation is rejected, exactly
   like any uncited claim.
2. `uncertain` is a first-class outcome and MUST be used whenever the code alone does not
   settle it. Do NOT force a true/false call to look decisive.
3. Verdicts are scoped to CODE-LEVEL correctness only. You have NO exposure/product
   context in Phase 1. Do NOT claim a finding is "not a product risk" or "not exploitable
   in deployment" — only whether it looks like a real code-level issue.
</HARD-GATE>

## When to use

- Claims are `extracted` and have no verdicts yet.
- Symptoms: "check these findings", "which of these are false positives", "challenge the
  CodeQL results".

## Outcomes

| Outcome | Meaning |
|---|---|
| `likely_true_positive` | Code supports the finding being real (cite why). |
| `likely_false_positive` | Code shows a concrete reason it's not real — validated input, dead path, parameterized sink (cite it). |
| `uncertain` | Code alone doesn't settle it. A human should look. **Expected to be common.** |

## Checklist

1. **For each claim**: pull the cited location PLUS surrounding context from the checkout
   (the function, caller, relevant source/sink definitions).
2. **Reason** about true-vs-false positive using only what the code shows.
3. **Write a verdict claim** (`kind='verdict'`, `source_reliability='llm'`) with rationale
   and citations, and a `verdict` row linking it to the target claim with the outcome.
4. **Default to `uncertain`** when the code doesn't decide it.
5. **Advance** `status` to `challenged`.

## Implementation

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/challenge_claim.py" --db "$ASSESSMENT_DB" --assessment "$ASSESSMENT_ID" \
  --cache-dir "$CHECKOUT_CACHE"
```

The stub echoes, per claim: the context it would gather, and a placeholder
`uncertain` verdict with a cited rationale — so the cascade runs before the real LLM
reasoning is wired in.

## Health signal

Track the share of `uncertain` verdicts. If it is near zero, the skill is overconfident
and its verdicts should be distrusted — an LLM pushed to rule on everything will
confabulate. A healthy run has a substantial `uncertain` fraction.

## Common mistakes

| Mistake | Why it bites |
|---|---|
| Verdict without a cited line | Unfalsifiable opinion; violates the same rule as any uncited claim. |
| Avoiding `uncertain` to seem decisive | Manufactures false confidence on genuinely ambiguous code. |
| Saying "not exploitable in the product" | Out of scope — no exposure model exists in Phase 1. |
| Overwriting the original claim | Verdicts attach; they never mutate the claim they judge. |

## Red flags — STOP

- "I'm fairly sure, I'll call it true positive without pointing to a line" → cite or say
  `uncertain`.
- "Calling things uncertain looks weak" → uncertain is the correct answer for ambiguous
  code and protects the curator.
