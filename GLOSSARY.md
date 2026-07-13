# cyberkinetic — Glossary

Companion to [DESIGN.md](DESIGN.md). These terms have specific meanings in this system
that do not always match their generic usage.

**Assessment** — one run of the harness against one product at a defined scope (a set
of repos at pinned commits, and a declared set of data sources). Backed by one SQLite
file plus its checkout cache.

**Plugin / Skill** — a composable unit of the pipeline, defined by a SKILL.md with a
trigger, a gate, and defined read/write state. Used interchangeably. A plugin reads the
assessment state, does bounded work, and writes results back.

**Claim** — one assertion *about the corpus* ("the corpus asserts X"), never an
assertion that X is true in the world. Carries a citation and confidence axes. Phase 1:
one claim per static-analysis result.

**Citation** — the pointer from a claim to its source. Either a **document snapshot**
(content-hash reference to stored bytes) or a **git coordinate**
(`repo_url, commit_sha, path, line_range`).

**Git coordinate** — a precise, reproducible source pointer into version-controlled
code. The commit SHA is itself the snapshot; no code bytes are copied into the model.

**Snapshot-and-hash** — storing the source content as read plus its hash, so a claim
references the exact version it was based on. Meets the provenance bar ("said X when
collected") without heavier audit machinery.

**`citation_verified`** — a mechanical (non-LLM) flag on code claims: does the cited
line range exist and match at the cited SHA? The strongest firewall in Phase 1.

**Faithful extraction** — verification that a source *really asserted* a claim (syntactic,
deterministic). Distinct from substantive correctness.

**Substantive correctness** — verification that a claim is *actually right* (semantic,
judgment). The job of `challenge-claim`.

**Verdict** — a `challenge-claim` output attached to a claim:
`likely-true-positive` / `likely-false-positive` / `uncertain`, with rationale and its
own citations. Modeled as a new claim with its own (LLM-tier) reliability — a
recommendation to a curator, not a truth oracle and not an auto-suppression.

**Assumption** — a claim that another claim depends on. The set of a claim's
assumptions is its **support set**. Made explicit so confidence propagates and
high-**fan-in** assumptions (many claims depend on them) can be prioritized.

**Correlated collapse** — the failure where many claims share a wrong assumption and so
all fail together *without conflicting*. The reason fan-in matters more than surface
conflict.

**Confidence axes** — the four per-claim ratings. **Source reliability** and
**applicability** are collection-time / claim-intrinsic (Phase 1). **Information
credibility** and **scope-match** are evaluation-time / assessment-relative (Phase 2).

**`unset`** — an explicit axis state meaning "not evaluated," distinct from "evaluated
and unknown." Prevents the model from implying it knows something it never computed.

**Applicability / relevance** — does a claim bear on *this product's* surface at all.

**Scope-match** (Phase 2) — does a claim apply to *this instance* (variant, version,
deployment): `matches` / `conflicts` / `unknown`. `conflicts` suppresses; `unknown`
triggers interview.

**Finding** — a claim or claim-set elevated to "this matters for the product," with a
consequence story. Phase 1 does not implement elevation; it surfaces claims + verdicts.

**Consequence class** — the physical-world impact category of a finding: loss of view,
loss of control, safety impact, service disruption, lateral pivot. The consequence-first
alternative to CVSS.

**Discriminators** — the axes on which a finding may beat a baseline: persistence,
remoteness, stealth, scale, safety. Used per-axis, not as a scalar.

**Dominance floor** (Phase 2) — suppression of findings no worse than a trivial
adversary baseline (the "hammer attack"). Parameterized by exposure; inverts with it.

**Exposure profile** (Phase 2) — the product's exposure along axes (physical
accessibility, network exposure, tenancy/ownership, multiplicity), derived as a
projection over collected claims. Parameterizes the floor.

**Slot** (Phase 2) — a position in the model that the exposure profile says *should*
hold a claim. An empty required slot is a **gap**.

**Gap** (Phase 2) — a required slot with no claim, or only a low-tier claim. Two kinds:
*absence* (no claim) and *provenance* (low-confidence claim needing promotion).

**Collection-complete** (Phase 2) — the checkable condition that all *declared* data
sources have been processed, which makes an empty slot a trustworthy absence rather than
a retrieval miss.

**`challenge-claim`** — Phase 1 LLM plugin. Attacks findings that *are* present: is this
one a false positive? Per-claim, reads code, writes verdicts.

**`adversarial-review`** (Phase 2) — attacks what is *absent*: completeness and
dismissed-set audit. Over the whole model. Distinct from `challenge-claim`.
