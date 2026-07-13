#!/usr/bin/env python3
"""STUB for skill: collect-code. See skills/collect-code/SKILL.md."""
import argparse
from _stub import announce


def main():
    p = argparse.ArgumentParser(description="Check out in-scope repos at pinned SHAs (STUB)")
    p.add_argument("--db", required=True)
    p.add_argument("--assessment", required=True, help="assessment id")
    p.add_argument("--cache-dir", required=True, help="disposable checkout cache root")
    args = p.parse_args()

    announce(
        "collect-code",
        "materialize pinned checkouts into the disposable cache",
        args,
        [
            "SELECT repo_url, commit_sha FROM in_scope_repo WHERE assessment_id=?",
            "for each repo: git clone/fetch and checkout the EXACT pinned SHA",
            "REJECT / report if a declared SHA does not resolve (no branch-head fallback)",
            "UPDATE in_scope_repo SET checkout_path=?, collected_at=now()",
            "UPDATE assessment SET status='collecting'|'analyzing'",
        ],
    )


if __name__ == "__main__":
    main()
