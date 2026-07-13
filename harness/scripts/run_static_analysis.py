#!/usr/bin/env python3
"""STUB for skill: run-static-analysis. See skills/run-static-analysis/SKILL.md."""
import argparse
from _stub import announce


def main():
    p = argparse.ArgumentParser(description="Run CodeQL, store raw SARIF (STUB)")
    p.add_argument("--db", required=True)
    p.add_argument("--assessment", required=True)
    p.add_argument("--cache-dir", required=True)
    args = p.parse_args()

    announce(
        "run-static-analysis",
        "produce and store raw SARIF per in-scope repo",
        args,
        [
            "SELECT checkout_path, repo_url, commit_sha FROM in_scope_repo",
            "for each repo: run CodeQL -> SARIF (no filtering, no dedup, no ranking)",
            "INSERT analysis_run(tool_name='CodeQL', tool_version=?, "
            "sarif_blob=<raw>, sarif_sha256=?)",
            "UPDATE declared_source SET processed=1 for the matching source",
            "UPDATE assessment SET status='analyzing'",
        ],
    )


if __name__ == "__main__":
    main()
