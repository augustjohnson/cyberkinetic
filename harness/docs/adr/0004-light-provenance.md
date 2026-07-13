# ADR-0004: Snapshot-and-hash provenance, not append-only audit

**Status:** Accepted
**Deciders:** August

## Context
An earlier design argued for append-only, supersede-by-insert, actor-attributed audit
logs to make suppression tamper-evident. The actual requirement is weaker.

## Decision
The provenance bar is: "the source said port 80 was open when collected, even if it
doesn't now," plus supporting evidence. Meet it with snapshot-and-hash at collection
time. Do not require append-only tables, supersede pointers, or prevention of custom
SQL. Normal UPDATEs are fine; nothing must *prevent* direct SQL.

## Options Considered
- **Append-only + audit log.** Rejected as over-engineered for a non-legal bar; costly
  to retrofit onto direct-access dev workflow.
- **Snapshot-and-hash** (chosen). Delivers the stated requirement at minimal cost.

## Consequences
- Easier: dev can hand-edit rows while riffing without ceremony.
- Harder/accepted: no tamper-evidence; a hand-edit leaves no trace. Acceptable at this
  trust level.
- Requires: store retrieved content + hash on collect; code claims lean on the commit
  SHA (stronger than a hash, reproducible).
