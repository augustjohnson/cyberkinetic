#!/usr/bin/env python3
"""initialize-assessment. See skills/initialize-assessment/SKILL.md.

Reads a resolved cyberkinetic assessment-request issue and writes the assessment's
initial DB state. The product name and repo list are read from the issue itself; the
pinned commit for each repo is read from the `cyberkinetic:resolved-scope` comment left
by `.github/workflows/resolve-assessment-scope.yml` — never from the issue's raw
"In-scope repositories" text, which may name an unresolved branch, tag, or bare repo.

Each assessment gets its own SQLite file at `<data-dir>/<assessment_id>/assessment.db`
(local disk, on the assessor's machine — see the "Data layout" section of
skills/using-cyberkinetic/SKILL.md; blob storage is future work, not implemented here).
There is no shared index of assessments, so re-runs are found by scanning `<data-dir>`
for a db whose `assessment.issue_ref` matches this issue.
"""
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

RESOLVED_LABEL = "repo-scope-resolved"
MARKER = "<!-- cyberkinetic:resolved-scope -->"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "schema.sql"


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


def find_existing_assessment(data_dir, issue_url):
    """Scan `<data-dir>/*/assessment.db` for a prior run against this issue."""
    base = Path(data_dir)
    if not base.exists():
        return None
    for entry in sorted(base.iterdir()):
        db_path = entry / "assessment.db"
        if not db_path.exists():
            continue
        con = sqlite3.connect(db_path)
        row = con.execute(
            "SELECT id, status FROM assessment WHERE issue_ref = ?", (issue_url,)
        ).fetchone()
        con.close()
        if row:
            return {"assessment_id": row[0], "status": row[1], "db_path": db_path}
    return None


def open_db(db_path):
    fresh = not db_path.exists()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    if fresh:
        con.executescript(SCHEMA_PATH.read_text())
    return con


def main():
    p = argparse.ArgumentParser(description="Initialize a cyberkinetic assessment from a resolved issue")
    p.add_argument("--data-dir", default=os.environ.get("CYBERKINETIC_DATA_DIR", "./cyberkinetic-assessments"),
                   help="base directory holding one subdirectory per assessment id "
                        "(assessment.db, checkouts/, render/); defaults to "
                        "$CYBERKINETIC_DATA_DIR")
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

    existing = find_existing_assessment(args.data_dir, issue["url"])
    if existing and existing["status"] != "initialized":
        sys.exit(
            f"REJECT: assessment {existing['assessment_id']} for {issue['url']} has "
            f"already advanced past 'initialized' (status={existing['status']!r}); "
            f"correct scope on a new issue instead of re-running initialize-assessment here"
        )

    assessment_id = existing["assessment_id"] if existing else str(uuid.uuid4())
    db_path = Path(args.data_dir) / assessment_id / "assessment.db"
    con = open_db(db_path)

    if existing:
        # Not yet consumed downstream — safe to overwrite with the corrected scope.
        con.execute("UPDATE assessment SET product = ? WHERE id = ?", (product, assessment_id))
        con.execute("DELETE FROM in_scope_repo WHERE assessment_id = ?", (assessment_id,))
        con.execute("DELETE FROM declared_source WHERE assessment_id = ?", (assessment_id,))
    else:
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

    verb = "updated" if existing else "created"
    print(f"[initialize-assessment] {verb} assessment {assessment_id} for {product!r} "
          f"({len(scope['resolved_repos'])} repo(s)) from {issue['url']}")
    print(f"[initialize-assessment] db: {db_path}")


if __name__ == "__main__":
    main()
