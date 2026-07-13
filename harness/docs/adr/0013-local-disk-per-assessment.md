# ADR-0013: Assessment state on local disk, one directory per assessment; blob storage deferred

**Status:** Accepted
**Deciders:** August

## Context
The cascade's six skills are invoked as **separate GitHub Actions runs spread over
time** — e.g. `initialize-assessment` fires when an issue is labeled
`repo-scope-resolved`, and `collect-code` may run hours or days later once someone (or
something) triggers it. GitHub-hosted runners are ephemeral: nothing on their disk
survives between separate job runs. Something has to hold the assessment's SQLite file
(and its checkout cache, and its rendered output) across that gap.

GitHub itself has no service that behaves like real blob storage: committing the `.db`
file to the repo re-introduces exactly what ADR-0003 rejected (git-tracked state,
monotonic blob growth, no clean redaction of sensitive data from history);
`actions/cache` is an LRU-evicted best-effort cache, not a durable store; `actions/upload-artifact`
is retention-limited and immutable per run; GitHub Release assets can be made to work
(download/modify/re-upload) but repurpose a feature meant for versioned software and give
no real locking.

## Decision
For now, assume the cascade's Actions runs execute on **the assessor's own (self-hosted)
machine**, not GitHub-hosted ephemeral runners. Assessment state lives on that machine's
local disk, one directory per assessment:

```
<data-dir>/<assessment_id>/
  assessment.db
  checkouts/
  render/
```

`<data-dir>` defaults to `$CYBERKINETIC_DATA_DIR`, or `./cyberkinetic-assessments` if
unset. `initialize-assessment` mints the assessment's directory and bootstraps
`assessment.db` from `schema/schema.sql` on first use. There is no shared index of
assessments — a script that needs to find an existing one (e.g. to detect a re-run
against the same issue) scans `<data-dir>/*/assessment.db` for a matching `issue_ref`.

Moving this to networked/blob storage (so the cascade can run on ordinary GitHub-hosted
runners) is explicit future work, not implemented now.

## Options Considered

### Azure Blob Storage (or S3/GCS) (deferred, not rejected)
Would work — each job downloads the current db, does its local SQLite work, re-uploads
it — since the cascade is sequential per assessment (no concurrent writers). But it's a
new hosted third-party service, which this project's operating stance (`docs/DESIGN.md`
§8: "no server, no provisioned storage") and the author's general house rules on hosted
services (default-deny; a new service must clear a bar and be a named, conscious
exception) both push back on adopting by default. Worth revisiting if/when the
self-hosted-runner assumption stops holding.

### Self-hosted runner + local disk (chosen for now)
Adds no new hosted dependency — the assessor already needs a machine to run this from.
Keeps SQLite on local disk, which is where it's meant to live (SQLite over a networked
filesystem, which is effectively what a blob-storage-as-mount would be, is a known
corruption risk given SQLite's locking assumptions). The cost is that it only works
because a real, persistent machine is assumed to exist and be reachable by the triggering
workflow — this is a real constraint on deployment, not a free lunch.

### GitHub Release assets as the store (considered, not chosen)
Would also add no new hosted service, reusing `GITHUB_TOKEN`. Rejected for now in favor
of local disk because the self-hosted-runner assumption already provides a persistent
disk directly — there's no gap left for Release assets to fill today. Worth reconsidering
if the self-hosted-runner assumption is dropped before blob storage is built.

## Consequences
- Nothing here is portable across machines yet: if the runner triggering `collect-code`
  isn't the same machine (or doesn't share the same `<data-dir>`) as the one that ran
  `initialize-assessment`, the assessment won't be found. This is accepted for now.
- This also resolves a standing gap noted during implementation: nothing previously
  bootstrapped `assessment.db` from `schema/schema.sql`. `initialize-assessment` now
  owns that, since it's the step that mints an assessment's identity in the first place.
- Revisit this ADR before running the cascade on GitHub-hosted (non-self-hosted) runners,
  or before more than one assessor's machine needs to share assessment state.
