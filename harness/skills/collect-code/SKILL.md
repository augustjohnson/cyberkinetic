---
name: collect-code
description: Use when an initialized cyberkinetic assessment needs its in-scope repositories checked out at their pinned commits before static analysis.
---

# Collect Code

## Overview

Materialize each in-scope repository at its pinned commit into a disposable filesystem
checkout cache. Pure retrieval — no judgment. The checkout is a **cache**, not state:
it is losslessly reconstructible from `(repo_url, commit_sha)`, which are the durable
truth in the database. Code is never copied into the database; only referenced by
coordinate later.

<HARD-GATE>
Do NOT run unless the assessment `status='initialized'` and `in_scope_repo` has at least
one row with a pinned `commit_sha`. Do NOT check out a floating ref. If a declared SHA
does not resolve in the remote, stop and report it — do not substitute the branch head.

This step is **all-or-nothing**: if ANY repo fails to check out, abort before writing
anything to the DB. `status` stays `initialized` and no `in_scope_repo` row gets a
`checkout_path` — a retry is then unambiguous. There is no partial/in-progress status to
observe between separate runs; `status` only ever advances straight to `analyzing` once
every repo in this assessment is collected.
</HARD-GATE>

## When to use

- Assessment is `initialized` and code has not yet been checked out.
- Symptoms: "collect the code", "clone the repos", moving from init to analysis.

## Checklist

1. **Read** `in_scope_repo` for this assessment; require `status='initialized'`.
2. **For each repo**: shallow-fetch (`git fetch --depth 1 origin <sha>`) and check out
   exactly the pinned SHA into the cache; verify `git rev-parse HEAD` matches.
3. **If any repo fails**, abort immediately — do not write anything to the DB.
4. **Once every repo succeeds**: record `checkout_path`/`collected_at` on each
   `in_scope_repo` row and advance `status` directly to `analyzing`, in one commit.

## Implementation

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/collect_code.py" \
  --data-dir "$CYBERKINETIC_DATA_DIR" \
  --assessment "$ASSESSMENT_ID"
```

`--checkout-cache` overrides where checkouts land; it defaults to
`<data-dir>/<assessment>/checkouts` (see the "Data layout" section of
`using-cyberkinetic/SKILL.md`) — there is no separate `--db`/`--cache-dir` pair to wire up
by hand. Checkouts are shallow (`--depth 1` at the exact pinned SHA, not the branch tip) —
this is not a full clone. Requires `gh` to be authenticated; the script itself runs
`gh auth setup-git` so plain `git` against `github.com` is authenticated, rather than
assuming that one-time setup already happened elsewhere.

## Postconditions

- Each `in_scope_repo` row has a `checkout_path` and `collected_at` — **all of them, or
  none of them**; there is no partially-collected assessment left behind.
- Working trees exist under the checkout cache at the pinned SHAs (shallow, depth 1).
- `status='analyzing'`.

## Notes

- The cache is disposable. Deleting it and re-running this skill must produce the same
  result. Never store anything here that isn't reconstructible. An existing checkout
  directory for a repo is removed and redone from scratch on every run, never reused
  in place.
- Not yet addressed: repeated testing against the same large repo re-clones it from
  scratch each time (no shared object cache across assessments). Acceptable for now;
  revisit if this becomes a real cost.

## Common mistakes

| Mistake | Why it bites |
|---|---|
| Treating the checkout as durable state | It's a cache; the SHA is the truth. Don't back it up or depend on it persisting. |
| Silently falling back to branch head on a bad SHA | Breaks reproducibility and citation verification downstream. Report instead. |
| Writing partial `in_scope_repo` rows as repos complete | This step is all-or-nothing — write nothing until every repo has succeeded. |
| A full clone instead of a shallow fetch | Wastes time/disk on repos like `home-assistant/core`; fetch depth 1 at the exact SHA only. |
