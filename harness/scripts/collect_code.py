#!/usr/bin/env python3
"""collect-code. See skills/collect-code/SKILL.md.

Shallow-clones each in-scope repo at its pinned commit_sha into the checkout cache.
All-or-nothing: if any repo fails to check out, the whole run aborts before touching
the DB, so `status` stays 'initialized' and a retry is unambiguous. `status` only ever
advances straight to 'analyzing' once every repo is collected — there is no partial
'collecting' state to observe between separate runs.

Requires `gh` to be authenticated (`gh auth status`); this script runs
`gh auth setup-git` itself so plain `git` commands against github.com are authenticated,
rather than assuming that one-time setup already happened.
"""
import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path


def require_gh():
    out = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"REJECT: gh is not authenticated (required for git access to github.com): "
                  f"{out.stderr.strip()}")
    setup = subprocess.run(["gh", "auth", "setup-git"], capture_output=True, text=True)
    if setup.returncode != 0:
        sys.exit(f"REJECT: gh auth setup-git failed: {setup.stderr.strip()}")


def parse_repo_path(repo_url):
    owner, name = repo_url.rstrip("/").split("/")[-2:]
    return owner, name


def run_git(*args, cwd):
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout.strip()


def clone_at_sha(repo_url, sha, dest):
    if dest.exists():
        shutil.rmtree(dest)  # disposable cache; always safe to redo
    dest.mkdir(parents=True)
    run_git("init", "-q", cwd=dest)
    run_git("remote", "add", "origin", repo_url, cwd=dest)
    run_git("fetch", "--depth", "1", "origin", sha, cwd=dest)
    run_git("checkout", "-q", "FETCH_HEAD", cwd=dest)
    head = run_git("rev-parse", "HEAD", cwd=dest)
    if head != sha:
        raise RuntimeError(f"checked out {head}, expected {sha}")


def main():
    p = argparse.ArgumentParser(description="Check out in-scope repos at their pinned SHAs")
    p.add_argument("--data-dir", default=os.environ.get("CYBERKINETIC_DATA_DIR", "./cyberkinetic-assessments"),
                   help="base directory holding one subdirectory per assessment id; "
                        "defaults to $CYBERKINETIC_DATA_DIR")
    p.add_argument("--assessment", required=True, help="assessment id (its directory name under --data-dir)")
    p.add_argument("--checkout-cache", default=None,
                   help="override the checkout cache location; defaults to "
                        "<data-dir>/<assessment>/checkouts")
    args = p.parse_args()

    db_path = Path(args.data_dir) / args.assessment / "assessment.db"
    if not db_path.exists():
        sys.exit(f"REJECT: no assessment database at {db_path}")

    checkout_cache = (
        Path(args.checkout_cache) if args.checkout_cache
        else Path(args.data_dir) / args.assessment / "checkouts"
    )

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")

    row = con.execute("SELECT status FROM assessment WHERE id = ?", (args.assessment,)).fetchone()
    if row is None:
        sys.exit(f"REJECT: no assessment row with id {args.assessment!r} in {db_path}")
    status = row[0]
    if status != "initialized":
        sys.exit(f"REJECT: assessment {args.assessment} has status {status!r}, expected 'initialized'")

    repos = con.execute(
        "SELECT repo_url, commit_sha FROM in_scope_repo WHERE assessment_id = ?",
        (args.assessment,),
    ).fetchall()
    if not repos:
        sys.exit(f"REJECT: no in_scope_repo rows for assessment {args.assessment}")

    require_gh()

    checkout_cache.mkdir(parents=True, exist_ok=True)
    collected = []
    for repo_url, sha in repos:
        owner, name = parse_repo_path(repo_url)
        dest = checkout_cache / owner / name
        print(f"[collect-code] checking out {repo_url} @ {sha} -> {dest}")
        try:
            clone_at_sha(repo_url, sha, dest)
        except RuntimeError as e:
            sys.exit(f"REJECT: failed to check out {repo_url}@{sha}: {e}")
        collected.append((repo_url, sha, str(dest)))

    # Every repo succeeded — write back and advance status in one step.
    for repo_url, sha, dest in collected:
        con.execute(
            "UPDATE in_scope_repo SET checkout_path = ?, collected_at = datetime('now') "
            "WHERE assessment_id = ? AND repo_url = ? AND commit_sha = ?",
            (dest, args.assessment, repo_url, sha),
        )
    con.execute("UPDATE assessment SET status = 'analyzing' WHERE id = ?", (args.assessment,))
    con.commit()
    con.close()

    print(f"[collect-code] collected {len(collected)} repo(s) for assessment "
          f"{args.assessment}; status=analyzing")


if __name__ == "__main__":
    main()
