#!/usr/bin/env python3
"""run-static-analysis. See skills/run-static-analysis/SKILL.md.

Runs "the configured static-analysis tool" over each checked-out repo and stores its
raw SARIF, verbatim — no filtering, no dedup, no ranking. That tool is Semgrep for
Phase 1 (see ADR-0014); it's a stand-in for a distinct, internal black-box tool
(code in, SARIF out) not yet available for testing. Swapping tools later should mean
replacing this script's internals, not the skill's contract.

All-or-nothing, like collect-code: if analysis fails for any repo, abort before
touching the DB, so `status` stays 'analyzing' and a retry is unambiguous.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sqlite3
import sys
import uuid
from pathlib import Path

TOOL_NAME = "Semgrep"
DEFAULT_CONFIG = "p/security-audit"


def require_semgrep():
    out = subprocess.run(["semgrep", "--version"], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"REJECT: semgrep is not available: {out.stderr.strip()}")
    return out.stdout.strip()


def run_semgrep(checkout_path, config, out_path):
    result = subprocess.run(
        ["semgrep", "--config", config, "--sarif", "--output", str(out_path),
         "--quiet", "--error", "--no-git-ignore", str(checkout_path)],
        capture_output=True, text=True,
    )
    # semgrep exits non-zero when findings match `--error`'s severity threshold —
    # that's not a run failure, just results. A real failure has no SARIF written.
    if not out_path.exists():
        raise RuntimeError(f"semgrep produced no SARIF output: {result.stderr.strip()}")


def main():
    p = argparse.ArgumentParser(description="Run static analysis, store raw SARIF")
    p.add_argument("--data-dir", default=os.environ.get("CYBERKINETIC_DATA_DIR", "./cyberkinetic-assessments"),
                   help="base directory holding one subdirectory per assessment id; "
                        "defaults to $CYBERKINETIC_DATA_DIR")
    p.add_argument("--assessment", required=True, help="assessment id (its directory name under --data-dir)")
    p.add_argument("--semgrep-config", default=DEFAULT_CONFIG,
                   help=f"semgrep --config value (default: {DEFAULT_CONFIG}); not pinned "
                        f"to a specific ruleset version — see ADR-0014")
    args = p.parse_args()

    db_path = Path(args.data_dir) / args.assessment / "assessment.db"
    if not db_path.exists():
        sys.exit(f"REJECT: no assessment database at {db_path}")

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")

    row = con.execute("SELECT status FROM assessment WHERE id = ?", (args.assessment,)).fetchone()
    if row is None:
        sys.exit(f"REJECT: no assessment row with id {args.assessment!r} in {db_path}")
    status = row[0]
    if status != "analyzing":
        sys.exit(f"REJECT: assessment {args.assessment} has status {status!r}, expected 'analyzing'")

    repos = con.execute(
        "SELECT repo_url, commit_sha, checkout_path FROM in_scope_repo WHERE assessment_id = ?",
        (args.assessment,),
    ).fetchall()
    if not repos:
        sys.exit(f"REJECT: no in_scope_repo rows for assessment {args.assessment}")
    missing = [r for r in repos if not r[2]]
    if missing:
        sys.exit(f"REJECT: {len(missing)} in_scope_repo row(s) have no checkout_path "
                  f"(run collect-code first)")

    tool_version = require_semgrep()

    sarif_dir = Path(args.data_dir) / args.assessment / "sarif"
    sarif_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for repo_url, sha, checkout_path in repos:
        out_path = sarif_dir / f"{uuid.uuid4()}.sarif"
        print(f"[run-static-analysis] scanning {repo_url} @ {sha} ({checkout_path})")
        try:
            run_semgrep(checkout_path, args.semgrep_config, out_path)
        except RuntimeError as e:
            sys.exit(f"REJECT: static analysis failed for {repo_url}@{sha}: {e}")
        sarif_bytes = out_path.read_bytes()
        results.append({
            "repo_url": repo_url,
            "commit_sha": sha,
            "sarif_blob": sarif_bytes,
            "sarif_sha256": hashlib.sha256(sarif_bytes).hexdigest(),
        })

    # Every repo succeeded — write back. `status` stays 'analyzing'; advancing to
    # 'extracted' is extract-claims' job, not this script's (see its SKILL.md).
    for r in results:
        con.execute(
            "INSERT INTO analysis_run (id, assessment_id, repo_url, commit_sha, tool_name, "
            "tool_version, sarif_blob, sarif_sha256) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), args.assessment, r["repo_url"], r["commit_sha"],
             TOOL_NAME, tool_version, r["sarif_blob"], r["sarif_sha256"]),
        )
        source_key = f"sarif:{r['repo_url']}@{r['commit_sha']}"
        con.execute(
            "UPDATE declared_source SET processed = 1, processed_at = datetime('now') "
            "WHERE assessment_id = ? AND source_key = ?",
            (args.assessment, source_key),
        )
    con.commit()
    con.close()

    print(f"[run-static-analysis] analyzed {len(results)} repo(s) for assessment "
          f"{args.assessment}; status remains 'analyzing' (extract-claims advances it next)")


if __name__ == "__main__":
    main()
