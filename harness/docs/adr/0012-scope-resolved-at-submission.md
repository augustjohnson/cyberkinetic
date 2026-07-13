# ADR-0012: Repo refs resolved to a SHA at issue-submission time, by a bot

**Status:** Accepted
**Deciders:** August

## Context
`initialize-assessment`'s HARD-GATE requires every in-scope repo to be pinned to a
commit SHA — no branches, tags, or floating refs — because citation verification
(`extract-claims`) and reproducibility depend on an immutable target. But requiring the
*requester* to hand-type a SHA is bad ergonomics: they usually know a branch or tag, not
a SHA, and typing one by hand invites typos and stale pins.

Two points in the pipeline could own resolving a human-friendly ref (branch, tag, or
bare repo meaning "default branch") down to a SHA:

1. **At `collect-code` time**, when the repo is actually checked out.
2. **At issue-submission time**, automatically, before any assessment exists.

## Decision
Resolve at **issue-submission time**, automatically. The `assessment-request` issue form
(`.github/ISSUE_TEMPLATE/assessment-request.yml`) accepts a flexible, human-friendly repo
reference per line — a bare repo URL, a `/tree/<branch-or-tag>` URL, or a `/commit/<sha>`
URL. A workflow (`.github/workflows/resolve-assessment-scope.yml`), triggered on
`issues: opened`/`edited`, resolves each line to an exact commit SHA via the GitHub API
and records the result as a `cyberkinetic:resolved-scope` JSON comment, labeling the
issue `repo-scope-resolved`. `initialize-assessment` reads pinned SHAs only from that
comment — never from the requester's raw text — and refuses to proceed unless the
`repo-scope-resolved` label is present.

If a reference fails to resolve (typo, deleted branch, private repo), the workflow
comments with the failure reason, labels the issue `needs-maintainer`, and closes it
(`state_reason: not_planned`) — no silent fallback to a floating ref, and no assessment
is ever created from an unresolved issue.

## Options Considered

### Resolve at `collect-code` time (rejected)
The ref would need to live in `in_scope_repo` unresolved until checkout, which meant:
dropping `commit_sha` from `in_scope_repo`'s primary key (it's `NOT NULL` today and part
of the PK), adding a column for the declared-but-unresolved ref, and moving `collect-code`'s
HARD-GATE from "verify an already-pinned SHA" to "resolve a ref, then pin it." It also
means reproducibility depends on *when* `collect-code` happens to run relative to the
issue being filed — an assessment sitting `initialized` for days could silently resolve
to a different commit than the requester saw at filing time, with nothing surfacing that
drift to a human.

### Resolve at issue-submission time (chosen)
No schema change: `in_scope_repo.commit_sha` stays `NOT NULL` and in the primary key
exactly as originally designed, because by the time `initialize-assessment` ever reads an
issue, the SHA is already pinned. `initialize-assessment`'s original HARD-GATE wording
("reject floating refs, require a resolvable SHA") stays correct as written — the human
never manually produces the SHA, a bot does it for them immediately, and the moment of
resolution is recorded permanently as a comment.

## Consequences
- `in_scope_repo`, `collect-code`, and the rest of the pipeline needed **no changes** —
  this decision only touches the issue-intake layer.
- Requesters can paste whatever GitHub URL they have on hand (branch, tag, bare repo, or
  commit) instead of looking up and typing a SHA.
- A failed resolution is caught and reported within seconds of submission, not
  discovered later when `initialize-assessment` or `collect-code` runs.
- `initialize-assessment` must treat the `repo-scope-resolved` label — not just the
  presence of a `cyberkinetic:resolved-scope` comment — as the authoritative signal,
  since an edited issue can carry a stale comment from a prior failed attempt.
