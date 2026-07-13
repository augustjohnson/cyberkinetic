#!/usr/bin/env python3
"""STUB for skill: extract-claims. See skills/extract-claims/SKILL.md.

The load-bearing part of the real implementation is the HARD-GATE: verify each
citation resolves at its SHA before writing the claim. This stub only describes it.
"""
import argparse
from _stub import announce


def main():
    p = argparse.ArgumentParser(description="Map SARIF results to gated claims (STUB)")
    p.add_argument("--db", required=True)
    p.add_argument("--assessment", required=True)
    p.add_argument("--cache-dir", required=True,
                   help="checkout cache, used to verify citations at the SHA")
    args = p.parse_args()

    announce(
        "extract-claims",
        "translate each SARIF result into one gated, cited claim",
        args,
        [
            "SELECT sarif_blob FROM analysis_run WHERE assessment_id=?",
            "for each SARIF result -> candidate claim (assertion, detail) "
            "+ git-coordinate citation (repo, sha, path, line_start/end)",
            "GATE: fetch cited lines at the SHA from the cache; verify they match",
            "  resolves    -> INSERT claim + citation(citation_verified=1)",
            "  unresolved  -> DO NOT write; log as extraction/tool error",
            "set source_reliability='tool', applicability='applicable'; "
            "credibility/scope_match remain 'unset'",
            "record SARIF level/security-severity as source_severity (provenance only)",
            "dedup on fingerprint/dedup_key (update, don't duplicate)",
            "UPDATE assessment SET status='extracted'",
        ],
    )


if __name__ == "__main__":
    main()
