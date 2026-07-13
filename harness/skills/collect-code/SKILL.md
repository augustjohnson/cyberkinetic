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

1. **Read** `in_scope_repo` for this assessment.
2. **For each repo**: clone/fetch and check out exactly the pinned SHA into the cache.
3. **Record** the checkout path and `collected_at` on the `in_scope_repo` row.
4. **Advance** `status` to `collecting` (or `analyzing` when all repos are present).

## Implementation

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/collect_code.py" --db "$ASSESSMENT_DB" --assessment "$ASSESSMENT_ID" \
  --cache-dir "$CHECKOUT_CACHE"
```

The stub echoes each repo+SHA it would check out and the cache path it would use.

## Postconditions

- Each `in_scope_repo` row has a `checkout_path` and `collected_at`.
- Working trees exist under the cache dir at the pinned SHAs.
- `status` advanced.

## Notes

- The cache is disposable. Deleting it and re-running this skill must produce the same
  result. Never store anything here that isn't reconstructible.
- Parallel fetching is fine; if a later skill writes blobs concurrently, that write — not
  this checkout — is the serialization point (WAL + single writer). See `docs/adr/0003`.

## Common mistakes

| Mistake | Why it bites |
|---|---|
| Treating the checkout as durable state | It's a cache; the SHA is the truth. Don't back it up or depend on it persisting. |
| Silently falling back to branch head on a bad SHA | Breaks reproducibility and citation verification downstream. Report instead. |
