# ADR-0005: Store document blobs in SQLite during dev; reference code by git coordinate

**Status:** Accepted
**Deciders:** August

## Context
Evidence splits into two kinds: opaque document snapshots (few, write-once) and source
code (huge, navigable, already versioned). During dev, fast iteration on prompts/tools
matters more than storage purity.

## Decision
Store document snapshot bytes as BLOBs in SQLite during the dev/local phase, keyed by
content hash so externalization later is a migration, not a redesign. Do NOT store code
in the DB — reference it by git coordinate `(repo, sha, path, line_range)` and treat the
filesystem checkout as a disposable cache reconstructible from coordinates.

## Options Considered
- **Blobs external from day one.** More correct long-term; slower to iterate now.
- **Code in DB.** Rejected: fights navigation, bloats the file, discards git's native
  content-addressing and reproducibility.
- **Blobs in DB (dev), code by reference** (chosen).

## Consequences
- Easier: single-file portability for the dev phase.
- Harder/accepted: the file is sensitive (contains attack paths) and must be held in
  controlled custody, not shared freely; it grows monotonically; once code is referenced
  the DB is no longer fully self-contained (a reviewer needs repo access at the SHAs).
- Requires: hash-referenced blobs so "move bytes to files, keep the hash" stays a
  migration. Revisit when someone first needs a redacted/evidence-free export.
