# ADR-0001: Claims are assertions about the corpus, not truth about the world

**Status:** Accepted
**Deciders:** August

## Context
The harness has no ground truth. No test catches a wrong claim, and an LLM-extracted
claim can be confidently wrong. A confidence-labeling system that tracks *where* a
claim came from does not make it *true*.

## Decision
Redefine what a claim asserts. A claim means "the corpus asserts X," never "X is true."
Verification targets faithfulness to the source, which is checkable, rather than truth
about the world, which is not.

## Options Considered
- **Assert world-truth** (naive). Requires ground truth we do not have; every
  extraction error becomes a silent correctness failure.
- **Assert corpus-truth** (chosen). Extraction faithfulness is verifiable; a
  faithful-but-false claim becomes a finding (doc is wrong, or product is wrong), which
  is a legitimate product-security output.

## Consequences
- Easier: verification becomes a citation/entailment check, not a fact check.
- Easier: "the docs say X but reality differs" is now a first-class output.
- Harder: a wrong claim must be disambiguated at review into *doc defect* vs *product
  defect* — it must NOT auto-route to "fix the docs," or real vulnerabilities get buried
  as editorial cleanup.
- Requires: citation-entailment checking (does the cited source actually support the
  claim), separate from merely attaching a citation.
