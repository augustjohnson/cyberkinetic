#!/usr/bin/env python3
"""STUB for skill: challenge-claim. See skills/challenge-claim/SKILL.md.

This is the one LLM skill. The stub emits a placeholder 'uncertain' verdict (with a
cited rationale) per claim so the cascade runs before real reasoning is wired in.
"""
import argparse
from _stub import announce


def main():
    p = argparse.ArgumentParser(description="Judge claims true/false positive (STUB)")
    p.add_argument("--db", required=True)
    p.add_argument("--assessment", required=True)
    p.add_argument("--cache-dir", required=True,
                   help="checkout cache, for reading surrounding code context")
    args = p.parse_args()

    announce(
        "challenge-claim",
        "attach an independent code-level verdict to each claim",
        args,
        [
            "SELECT claims (kind='code_finding') for this assessment",
            "for each: read cited location + surrounding context from the cache",
            "reason true-vs-false-positive using ONLY what the code shows",
            "INSERT verdict claim(kind='verdict', source_reliability='llm') "
            "with cited rationale",
            "INSERT verdict(target_claim_id, outcome in "
            "{likely_true_positive, likely_false_positive, uncertain})",
            "STUB default outcome: 'uncertain' (real skill: uncertain when code "
            "doesn't settle it; must remain a common outcome)",
            "scope: CODE-LEVEL only; never claim product (un)exploitability",
            "UPDATE assessment SET status='challenged'",
        ],
    )


if __name__ == "__main__":
    main()
