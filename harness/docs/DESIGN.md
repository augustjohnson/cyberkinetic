# cyberkinetic — Design

> A composable harness for assessing the security posture of cyber-physical systems —
> claims, provenance, and real-world consequence.

**Status:** Pre-implementation design. Phase 1 is specified concretely; Phase 2+ is
referenced by name only and is explicitly out of scope for implementation.

**Audience:** The team implementing and operating the harness, and future maintainers
who need to understand *why* it is shaped the way it is before changing it.

---

## 1. What this is

A semi-automated pipeline for assessing the security posture of connected products —
particularly operational-technology and other products whose failures have physical,
real-world consequences. It collects structured and unstructured data about a product,
turns that data into a model of **claims**, and produces a set of **findings** with
their anticipated real-world impact for a human to curate.

The system is a cascade of small, composable **plugins** (skills). Each plugin reads
the current state of an assessment, does a bounded piece of work, and writes its
result back. The shared state is the interface between plugins: no plugin depends on
another plugin's conversation or memory, only on the artifacts committed to the
assessment store.

Phase 1 is deliberately thin and straight-through: source code plus static-analysis
output, no feedback loops, no interviews, no fusion. The goal of Phase 1 is to prove
the pipeline runs end-to-end and produces something a security engineer could not get
from the underlying tool alone.

---

## 2. Core tenets

These are the load-bearing beliefs. Changing one of them is a design change, not an
implementation detail.

### 2.1 Claims are assertions about documentation, not ground truth about the world
A claim is "the corpus asserts X," never "X is true." A claim that is faithfully
extracted from a source but false in reality is **not a harness failure** — it is a
finding (the documentation is wrong, or the product is wrong). This reframe is what
makes the system tractable: we cannot verify truth about the world, but we *can*
verify faithfulness to a source, and faithfulness is checkable.

### 2.2 Provenance is first-class, but only as strong as it needs to be
Every claim carries where it came from and, where cheap, a snapshot of the source as
it was when read. The bar is "the source said port 80 was open when we collected it,
even if it doesn't now," plus supporting evidence — **not** legal-grade tamper
evidence. Snapshot-and-hash meets this bar; append-only audit logs and
supersede-by-insert are explicitly *not* required.

### 2.3 Two verification axes, kept separate
- **Faithful extraction** — did the source really assert this, here? (deterministic,
  script, syntactic; e.g. does a cited code line exist at the cited commit)
- **Substantive correctness** — is the assertion actually right? (judgment, LLM,
  semantic; e.g. is this flagged vulnerability a false positive)

These are different jobs and belong in different plugins. Conflating them loses the
property that most of the pipeline is deterministic.

### 2.4 Determinism where possible; LLM only for judgment
Work that produces the same output from the same input is a script. The LLM layer is
reserved for tasks whose value is reasoning over ambiguity (challenging a finding,
eliciting missing information, adversarial review). Any LLM surface that *could* be a
script is a nondeterminism we are choosing to accept, and we should be able to say
why.

### 2.5 The intermediary artifact is the interface
Plugins are decoupled by the state they read and write, not by calling each other.
This makes each plugin independently testable, resumable, and replaceable, and it lets
a human inspect the assessment between any two steps.

### 2.6 Consequence-first, not confidentiality-first
Many connected/OT products do not live in a confidentiality-first world. Ambient sensor
readings are not secrets; a control setpoint is not PII. Findings are framed by
physical-world consequence
(loss of view, loss of control, safety impact, service disruption, lateral pivot), not
by the CIA triad. CVSS is recorded where a tool provides it, but is never the driver of
triage — it is confidentiality-weighted and context-free and would mislead here.

### 2.7 Findings are unranked; ranking is human curation
Findings are presented unranked, each with a short story describing its consequence
dimensions (impact, remoteness, persistence, stealth, scale, safety). Ordering is a
human judgment, not an algorithm. We deliberately do not import an ordinal severity
scale.

### 2.8 YAGNI and explicit deferral
Complexity is deferred to later phases with stated justification. A deferred feature is
named and marked, not half-built. A stored field that is never populated is marked
`unset` (a distinct state from "evaluated as unknown"), so the model never lies about
what it does and doesn't know.

---

## 3. Inspirations

- **`obra/superpowers` (Jesse Vincent).** The plugin/skill architecture: small
  mandatory SKILL.md documents with hard gates, a cascade of intermediary artifacts
  (brainstorm → spec → plan → execute), fresh-context review, and the discipline that
  *structure* enforces good practice where *persuasion* fails. Two lessons carried in
  directly: low-friction approvals degrade human judgment (avoid one-click gates), and
  the system can be tested against pressure scenarios rather than trusted to behave.
- **Admiralty / NATO intelligence model (STANAG 2511).** The two-axis rating of every
  claim: source reliability × information credibility. Our provenance tier *is* the
  source-reliability axis.
- **CCE (Consequence-driven Cyber-informed Engineering) and MITRE ATT&CK for ICS.**
  Consequence-first framing of impact, and the vocabulary for describing attack paths
  against control systems.
- **IEC 62443.** Zone/conduit and security-level language for industrial systems.
- **Shape Up and the original Agile Manifesto intent; YAGNI.** Appetite-bounded scope,
  deferring complexity, and suspicion of ceremony that does not earn its keep.

---

## 4. The claim model

A **claim** is one assertion about the corpus, with a citation and a set of confidence
axes. Phase 1 populates two axes for real and marks two `unset`.

| Axis | When assigned | Phase 1 |
|---|---|---|
| **Source reliability** | at collection | populated (from tool/source metadata) |
| **Applicability / relevance** | at scoping | populated (does this bear on the product) |
| **Information credibility** | evaluative | `unset` (deferred to Phase 2) |
| **Scope-match** | evaluative | `unset` (deferred to Phase 2) |

Source reliability and applicability are **claim-intrinsic / collection-time**.
Credibility and scope-match are **assessment-relative / evaluation-time** — they are
judgments *about* a claim that can be revisited. This boundary is why the two pairs are
grouped separately in the schema: intrinsic axes are cacheable across runs of the same
product; evaluative axes are recomputed per assessment.

Claims may **cite their assumptions** — other claims they depend on. This makes the
dependency graph explicit, lets confidence propagate (a finding is only as strong as
its weakest load-bearing assumption), and surfaces *correlated collapse*: a
high-fan-in assumption that many claims rest on is the highest-leverage thing to
verify, precisely because nothing conflicts when it is wrong. (Assumption capture is a
floor on visible dependencies, not a guarantee of all of them — an LLM enumerates the
assumptions it noticed, not the ones it made unconsciously.)

### 4.1 Granularity
**One claim per static-analysis result** (not one claim per rule with many locations).
This keeps each citation precise and independently verifiable, lets `challenge-claim`
issue a verdict on each specific instance, and defers list-noise to the rendering
layer, which may group by rule for readability. Model stays granular; grouping is
presentation.

---

## 5. Citations and provenance

A citation points a claim at its source. Two source-types:

- **Document snapshot** — opaque, write-once, referenced by content hash. Bytes stored
  (in-DB for the dev phase; see ADR-0005). Satisfies "the source said X when read."
- **Git coordinate** — `(repo_url, commit_sha, path, line_range)`. Not embedded; the
  commit SHA *is* the snapshot, and is stronger provenance than a hash because it is
  independently reproducible by anyone with repo access. The working checkout is a
  disposable filesystem cache, reconstructible from the coordinate.

Code claims carry a mechanical `citation_verified` flag: does the cited line range
actually exist and match at the cited SHA? This is a non-LLM check and is the strongest
firewall in the system — available to code claims and to nothing else in Phase 1.

---

## 6. Findings and the dominance floor (framing only; Phase 2 for the floor logic)

A **finding** is a claim (or set of claims) elevated to "this matters for the product,"
carrying a consequence story. Phase 1 does *not* implement elevation logic or the
dominance floor — it surfaces code-level claims and their challenge verdicts for human
curation.

The **dominance floor** (Phase 2) is the mechanism that suppresses findings no worse
than a trivial baseline the adversary already has — e.g. a physical-access
availability attack is dominated by simply unplugging or hammering the device. Its key
properties, recorded here so Phase 1 does not foreclose them:

- The floor is **parameterized by the exposure profile**. It *inverts* with exposure:
  for an internet-facing webapp remote reachability is free and physical access is
  expensive; for an adversary-owned camera every physical-access finding is dominated
  by default and what clears the floor is anything that pivots to *other* devices or
  the backend.
- Suppression is a **stated finding**, never a silent filter — "dominated by hammer
  *because* exposure axis X" — so a reviewer can attack the premise.
- Equivalence is **per-axis**, not scalar: a finding clears the floor if it beats the
  baseline on *any* discriminator (persistence, remoteness, stealth, scale, safety),
  even when immediate impact is equivalent.

---

## 7. Phase map

### Phase 1 (this spec) — thin straight-through, code + SARIF
Source code at pinned commits and CodeQL/SARIF output only. One pass, no loops. Six
plugins: `initialize-assessment`, `collect-code`, `run-static-analysis`,
`extract-claims`, `challenge-claim`, `render-assessment`. Five are scripts; one
(`challenge-claim`) is the single required LLM surface. Deliverable: a set of code
claims, each with a resolvable citation and an independent reasoned verdict on whether
it is a likely true/false positive, rendered for human curation.

### Phase 2 (referenced only — do not implement)
- Information-credibility and scope-match axes populated (claim evaluation).
- Additional collection: SBOM/HBOM, other scan formats, structured docs, Jira/Confluence.
- Exposure profile as a derived projection over claims, with conflict routing.
- Gap detection (schema-diff against exposure-required slots; declared-sources make
  "collection-complete" checkable).
- Interview / elicitation (one question at a time, uncertainty first-class, role-routed).
- `adversarial-review` (completeness + dismissed-set audit — distinct from
  `challenge-claim`).
- Findings generation with the dominance floor; consequence-first impact model.
- Diagram/vision extraction (few but occasionally critical; reviewed-elicitation path).

### Phase 3 (referenced only)
Further tooling maturity; details TBD.

---

## 8. Operating environment

GitHub-native where it is cheap (repos, Actions, issue forms, Pages). Local SQLite file
plus a disposable filesystem checkout cache for assessment state during the dev/local
phase — no server, no provisioned storage, no app deployment. See ADR-0005 for the
storage decision and its known costs (sensitivity of the file, monotonic growth,
loss of self-containment once code is referenced).

**Rendered output is not published to the public internet.** For a product-security
assessment the rendered view is an attack-path document; keep it access-controlled or
unpublished. This constraint overrides any convenience argument.
