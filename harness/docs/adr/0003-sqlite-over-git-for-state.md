# ADR-0003: Local SQLite as assessment state, not a git-per-assessment repo

**Status:** Accepted
**Deciders:** August

## Context
An early sketch used a Jekyll repo per assessment that committed collected data and
served portions via Pages. The relational nature of the model (claims, citations,
assumptions, verdicts, axes) fights a document/file store, and git offers no
transactions, single-writer discipline, or query.

## Decision
Use a local SQLite file as the assessment's stateful store, with a disposable
filesystem checkout cache alongside it.

## Options Considered
| Option | Complexity | Query | Concurrency | Fit |
|---|---|---|---|---|
| git-per-assessment | Med | poor (grep) | last-write-wins, no txns | poor |
| Hosted DB | High | good | good | violates no-server/no-provisioning |
| **SQLite** (chosen) | Low | good (SQL) | single-writer, WAL | strong |

## Consequences
- Easier: the model is relational and SQL answers "findings whose support set contains a
  sub-threshold assumption" trivially.
- Easier: single-file, no server, no permissions, copyable — matches constraints.
- Harder: no free history/diff like git; concurrent blob collection must serialize the
  DB write (WAL + single writer merge).
- Note: for dev velocity, direct SQL access by a small number of humans is allowed
  (ADR-0004 sets the provenance bar that makes this acceptable).
