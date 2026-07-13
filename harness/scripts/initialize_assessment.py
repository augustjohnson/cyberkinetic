#!/usr/bin/env python3
"""initialize-assessment. See skills/initialize-assessment/SKILL.md.

Reads a resolved cyberkinetic assessment-request issue and writes the assessment's
initial DB state. The product name and repo list are read from the issue itself; the
pinned commit for each repo is read from the `cyberkinetic:resolved-scope` comment left
by `.github/workflows/resolve-assessment-scope.yml` — never from the issue's raw
"In-scope repositories" text, which may name an unresolved branch, tag, or bare repo.
"""
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import uuid

RESOLVED_LABEL = "repo-scope-resolved"
MARKER = "<!-- cyberkinetic:resolved-scope -->"


def fetch_issue(issue_repo, issue_number):
    out = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", issue_repo,
         "--json", "url,body,labels,comments"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"REJECT: could not fetch issue {issue_repo}#{issue_number}: {out.stderr.strip()}")
    return json.loads(out.stdout)


def extract_field(body, label):
    m = re.search(rf"### {re.escape(label)}\n\n(.*?)(?:\n### |\Z)", body, re.S)
    if not m:
        return ""
    text = m.group(1).strip()
    return "" if text == "_No response_" else text


def extract_resolved_scope(comments):
    for comment in reversed(comments):  # most recent resolution wins
        if MARKER in comment["body"]:
            m = re.search(r"```json\n(.*?)\n```", comment["body"], re.S)
            if m:
                return json.loads(m.group(1))
    return None


def main():
    p = argparse.ArgumentParser(description="Initialize a cyberkinetic assessment from a resolved issue")
    p.add_argument("--db", required=True, help="path to assessment SQLite file")
    p.add_argument("--issue-repo", default=os.environ.get("GITHUB_REPOSITORY"),
                   help="owner/repo the assessment-request issue lives in "
                        "(defaults to $GITHUB_REPOSITORY)")
    p.add_argument("--issue", required=True, type=int, help="assessment-request issue number")
    args = p.parse_args()

    if not args.issue_repo:
        sys.exit("REJECT: --issue-repo not given and $GITHUB_REPOSITORY is not set")

    issue = fetch_issue(args.issue_repo, args.issue)

    labels = {l["name"] for l in issue["labels"]}
    if RESOLVED_LABEL not in labels:
        sys.exit(f"REJECT: issue {issue['url']} is not labeled '{RESOLVED_LABEL}'")

    product = extract_field(issue["body"], "Product")
    if not product:
        sys.exit(f"REJECT: no product name found in {issue['url']}")

    scope = extract_resolved_scope(issue["comments"])
    if not scope or not scope.get("resolved_repos"):
        sys.exit(f"REJECT: no {MARKER} comment found on {issue['url']}")

    con = sqlite3.connect(args.db)
    con.execute("PRAGMA foreign_keys = ON")

    existing = con.execute(
        "SELECT id FROM assessment WHERE issue_ref = ?", (issue["url"],)
    ).fetchone()
    if existing:
        sys.exit(f"REJECT: assessment {existing[0]} already exists for {issue['url']}")

    assessment_id = str(uuid.uuid4())
    con.execute(
        "INSERT INTO assessment (id, product, issue_ref, status) VALUES (?, ?, ?, 'initialized')",
        (assessment_id, product, issue["url"]),
    )

    for repo in scope["resolved_repos"]:
        con.execute(
            "INSERT INTO in_scope_repo (assessment_id, repo_url, commit_sha) VALUES (?, ?, ?)",
            (assessment_id, repo["repo_url"], repo["resolved_sha"]),
        )
        source_key = f"codeql:{repo['repo_url']}@{repo['resolved_sha']}"
        con.execute(
            "INSERT INTO declared_source (assessment_id, source_key, source_type, processed) "
            "VALUES (?, ?, 'sarif', 0)",
            (assessment_id, source_key),
        )

    con.commit()
    con.close()

    print(f"[initialize-assessment] created assessment {assessment_id} for {product!r} "
          f"({len(scope['resolved_repos'])} repo(s)) from {issue['url']}")


if __name__ == "__main__":
    main()
