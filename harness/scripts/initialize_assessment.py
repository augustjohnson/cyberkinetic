#!/usr/bin/env python3
"""STUB for skill: initialize-assessment. See skills/initialize-assessment/SKILL.md."""
import argparse
from _stub import announce


def main():
    p = argparse.ArgumentParser(description="Initialize a cyberkinetic assessment (STUB)")
    p.add_argument("--db", required=True, help="path to assessment SQLite file")
    p.add_argument("--product", required=True, help="product name")
    p.add_argument("--repo", action="append", default=[],
                   help="repo_url@commit_sha (pinned SHA required); repeatable")
    p.add_argument("--source", action="append", default=[],
                   help="declared source key, e.g. codeql:<repo>@<sha>; repeatable")
    p.add_argument("--issue-ref", default=None, help="originating GitHub issue")
    args = p.parse_args()

    # A real implementation would enforce the HARD-GATE here: product present,
    # >=1 repo with a PINNED sha (reject floating refs), >=1 declared source.
    announce(
        "initialize-assessment",
        "parse scoping request into initial DB state",
        args,
        [
            f"INSERT assessment(product={args.product!r}, status='initialized', "
            f"issue_ref={args.issue_ref!r})",
            *[f"INSERT in_scope_repo({r}) after verifying SHA is pinned" for r in args.repo],
            *[f"INSERT declared_source({s}, processed=0)" for s in args.source],
            "REJECT if any repo ref is a branch/tag rather than a resolvable SHA",
        ],
    )


if __name__ == "__main__":
    main()
