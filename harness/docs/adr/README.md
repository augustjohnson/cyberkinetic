# cyberkinetic — Decision Log (ADRs)

Lightweight Nygard-style records of the load-bearing decisions behind this harness.
Each captures the decision, the alternatives rejected, and the consequences — so future
maintainers change these deliberately rather than by accident.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-corpus-not-world-ground-truth.md) | Claims are assertions about the corpus, not truth about the world | Accepted |
| [0002](0002-two-axis-claim-model.md) | Two-axis (Admiralty) claim confidence, extended to four, two deferred | Accepted |
| [0003](0003-sqlite-over-git-for-state.md) | Local SQLite as assessment state, not a git-per-assessment repo | Accepted |
| [0004](0004-light-provenance.md) | Snapshot-and-hash provenance, not append-only audit | Accepted |
| [0005](0005-blobs-in-db-for-dev.md) | Store document blobs in SQLite during the dev phase; reference code by git coordinate | Accepted |
| [0006](0006-unranked-findings.md) | Findings unranked with a consequence story; no ordinal severity scale | Accepted |
| [0007](0007-claim-per-result.md) | One claim per static-analysis result; group at render | Accepted |
| [0008](0008-challenge-claim-required.md) | `challenge-claim` is a Phase 1 required plugin | Accepted |
| [0009](0009-determinism-toward-scripts.md) | Deterministic work in scripts; LLM only for judgment | Accepted |
| [0010](0010-thin-mvp-code-sarif.md) | Phase 1 MVP is thin, straight-through, code + SARIF only | Accepted |
| [0011](0011-project-name.md) | Project is named `cyberkinetic`; not named after its inspiration | Accepted |
| [0012](0012-scope-resolved-at-submission.md) | Repo refs resolved to a SHA at issue-submission time, by a bot, not at checkout | Accepted |
| [0013](0013-local-disk-per-assessment.md) | Assessment state on local disk, one directory per assessment; blob storage deferred | Accepted |
