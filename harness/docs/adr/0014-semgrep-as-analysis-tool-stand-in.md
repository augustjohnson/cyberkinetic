# ADR-0014: Semgrep as the Phase 1 static-analysis tool, standing in for a black-box internal tool

**Status:** Accepted
**Deciders:** August

## Context
`run-static-analysis`'s job is narrow by design: run a static-analysis tool over each
checked-out repo and store its raw SARIF, verbatim (see the skill's HARD-GATE — no
filtering, no dedup, no ranking). The skill was originally specified assuming CodeQL, but
CodeQL brings problems that are really about *this specific tool*, not about the skill's
job: a compiled-database build step per language, non-trivial CLI/version provisioning on
a self-hosted runner, and — concretely, in the first real test against
`home-assistant/operating-system` — no supported language at all for a repo that's mostly
Buildroot/shell/Docker config.

Separately: the long-term intent is to plug in a distinct, internal static-analysis tool
(at JCI) that this project treats as a **black box** — code goes in, SARIF comes out,
nothing about its internals is this project's concern. That tool isn't available for
Phase 1 testing.

## Decision
Use **Semgrep** as the Phase 1 stand-in for "the configured static-analysis tool." It has
no compiled-database step (it's a direct rule-based scanner over the source tree), is
light to provision (`pip install semgrep`, vs. CodeQL's multi-hundred-MB per-language
bundle), natively emits SARIF (`--sarif`), and degrades gracefully on files/languages it
doesn't recognize — it skips what it can't parse rather than requiring a "supported
language" precondition, which resolves the `operating-system` problem without any
per-repo special-casing.

`run-static-analysis` is written and documented as invoking "the configured
static-analysis tool" — Semgrep today — not as a CodeQL-specific skill. Swapping in the
JCI tool later should mean replacing this one script's internals (still code-in,
SARIF-out, same `analysis_run` shape), not redesigning the skill or its HARD-GATE.

## Options Considered

### CodeQL (original assumption, rejected for now)
Would need per-repo language detection and a real decision about what to do with a
repo that has no CodeQL-supported language, a compiled-database build step (real
runtime cost, unaddressed timeout question), and CLI/version provisioning on the
runner. None of these are wrong to eventually solve — they're just not worth solving for
a tool this project doesn't intend to keep using long-term once the JCI tool is
available.

### Wait for the JCI tool before implementing this skill (rejected)
Blocks all Phase 1 end-to-end testing on an internal tool's availability. The skill's
contract (code in, SARIF out, store verbatim) doesn't depend on which tool sits behind
it, so there's no reason implementation has to wait.

### Semgrep (chosen)
Fast, genuinely reasonably available, no database-build step, native SARIF, and its
graceful degradation on unrecognized files is a real practical win for a
multi-language, non-uniform product like Home Assistant's repo set.

## Consequences
- `tool_name`/`tool_version` in `analysis_run` record `Semgrep` and its version for
  now; this is provenance, not a permanent identity — expect it to say something else
  once the JCI tool is wired in.
- **Determinism gap, accepted for now**: the Semgrep ruleset (`--config p/security-audit`
  by default) is fetched from Semgrep's registry and is not pinned to a specific version
  — the same assessment re-run later could see a different rule set. This is the same
  *class* of gap as an unpinned CodeQL version would have been; not solved here, just
  named per this project's own deferral discipline (`DESIGN.md` §2.8).
- A repo with nothing Semgrep recognizes (e.g. `operating-system`) still gets a
  legitimate `analysis_run` row with a near-empty SARIF and `processed=1` — that's
  interpreted as "the tool ran and found nothing to report," not a special
  "not-applicable" state. No schema or skill change needed for this case.
- Revisit this ADR when the JCI tool is actually available for integration.
