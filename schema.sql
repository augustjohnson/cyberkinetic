-- cyberkinetic — SQLite schema
-- Phase 1. Tables and columns not used in Phase 1 are marked DEFERRED and are
-- present only where their later absence would force a migration.
--
-- Conventions:
--   * Confidence axes use an explicit 'unset' state, distinct from a null/unknown
--     evaluation. Phase 1 populates reliability + applicability; credibility +
--     scope_match are stored 'unset'.
--   * One claim per static-analysis result (see DESIGN.md 4.1).
--   * Code is referenced by git coordinate, never embedded. Document bytes may be
--     stored as blobs during the dev phase (ADR-0005).
--   * Provenance bar is snapshot-and-hash, not append-only audit (ADR-0004).

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;      -- tolerate the one concurrent case (blob collection)

-- ---------------------------------------------------------------------------
-- Assessment scope
-- ---------------------------------------------------------------------------

CREATE TABLE assessment (
    id              TEXT PRIMARY KEY,           -- ulid/uuid
    product         TEXT NOT NULL,              -- e.g. 'Example Controller v3'
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    issue_ref       TEXT,                       -- GitHub issue that initiated this run
    status          TEXT NOT NULL DEFAULT 'initialized',
                    -- initialized | collecting | analyzing | extracted
                    -- | challenged | rendered
    notes           TEXT
);

CREATE TABLE in_scope_repo (
    assessment_id   TEXT NOT NULL REFERENCES assessment(id),
    repo_url        TEXT NOT NULL,
    commit_sha      TEXT NOT NULL,              -- pinned; no floating refs
    checkout_path   TEXT,                       -- disposable cache location, nullable
    collected_at    TEXT,
    PRIMARY KEY (assessment_id, repo_url, commit_sha)
);

-- Declared expected data sources. Phase 1 will typically be one row per repo's
-- SARIF run. Exists now so 'collection-complete' becomes checkable in Phase 2.
CREATE TABLE declared_source (
    assessment_id   TEXT NOT NULL REFERENCES assessment(id),
    source_key      TEXT NOT NULL,              -- e.g. 'codeql:<repo>@<sha>'
    source_type     TEXT NOT NULL,              -- 'code' | 'sarif' | (Phase 2: 'sbom', 'confluence', ...)
    processed        INTEGER NOT NULL DEFAULT 0, -- 0/1
    processed_at    TEXT,
    PRIMARY KEY (assessment_id, source_key)
);

-- ---------------------------------------------------------------------------
-- Raw artifacts
-- ---------------------------------------------------------------------------

-- Static-analysis runs (Phase 1: CodeQL). Raw SARIF stored for reproducibility.
CREATE TABLE analysis_run (
    id              TEXT PRIMARY KEY,
    assessment_id   TEXT NOT NULL REFERENCES assessment(id),
    repo_url        TEXT NOT NULL,
    commit_sha      TEXT NOT NULL,
    tool_name       TEXT NOT NULL,              -- 'CodeQL'
    tool_version    TEXT,
    sarif_blob      BLOB,                        -- raw SARIF; externalizable later
    sarif_sha256    TEXT,
    ran_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Document snapshots (Phase 1: unused for the code+SARIF spine, present for the
-- citation model's second source-type). Bytes in-DB during dev; reference by hash
-- so externalization is a migration, not a redesign.
CREATE TABLE snapshot (               -- DEFERRED payload use; schema present now
    content_sha256  TEXT PRIMARY KEY,
    media_type      TEXT,
    retrieved_at    TEXT NOT NULL DEFAULT (datetime('now')),
    source_uri      TEXT,
    bytes           BLOB
);

-- ---------------------------------------------------------------------------
-- Claims
-- ---------------------------------------------------------------------------

CREATE TABLE claim (
    id              TEXT PRIMARY KEY,
    assessment_id   TEXT NOT NULL REFERENCES assessment(id),
    kind            TEXT NOT NULL,              -- 'code_finding' (Phase 1)
                                                -- | 'verdict' (challenge output)
    assertion       TEXT NOT NULL,              -- corpus-relative statement
    detail          TEXT,                       -- tool message / rationale, verbatim

    -- Confidence axes -------------------------------------------------------
    -- Collection-time / claim-intrinsic:
    source_reliability TEXT NOT NULL DEFAULT 'unset',  -- e.g. 'tool' | 'llm' | 'unset'
    applicability      TEXT NOT NULL DEFAULT 'unset',  -- Phase 1: 'applicable' | 'unset'
    -- Evaluation-time / assessment-relative (DEFERRED — stored 'unset' in Phase 1):
    credibility        TEXT NOT NULL DEFAULT 'unset',
    scope_match        TEXT NOT NULL DEFAULT 'unset',  -- matches | conflicts | unknown | unset

    -- Source-attribute provenance (NOT our severity — recorded, never triaged on):
    source_severity TEXT,                       -- e.g. SARIF level / security-severity
    dedup_key       TEXT,                        -- SARIF fingerprint or composite

    created_by      TEXT NOT NULL,              -- plugin name
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_claim_assessment ON claim(assessment_id);
CREATE UNIQUE INDEX idx_claim_dedup ON claim(assessment_id, dedup_key)
    WHERE dedup_key IS NOT NULL;

-- Citations: a claim may have one or more. Exactly one source-type populated.
CREATE TABLE citation (
    id              TEXT PRIMARY KEY,
    claim_id        TEXT NOT NULL REFERENCES claim(id),
    source_type     TEXT NOT NULL,              -- 'git' | 'snapshot'

    -- git coordinate:
    repo_url        TEXT,
    commit_sha      TEXT,
    path            TEXT,
    line_start      INTEGER,
    line_end        INTEGER,
    citation_verified INTEGER,                  -- 1/0/null: line resolves at SHA?

    -- snapshot coordinate:
    snapshot_sha256 TEXT REFERENCES snapshot(content_sha256),
    quote_start     INTEGER,                    -- char offset into snapshot, nullable
    quote_end       INTEGER
);

CREATE INDEX idx_citation_claim ON citation(claim_id);

-- Assumption edges: claim -> claim it depends on (support set / fan-in).
-- Phase 1: sparsely used (SARIF claims have few explicit assumptions); present so
-- the dependency graph exists from the start.
CREATE TABLE assumption_edge (
    claim_id        TEXT NOT NULL REFERENCES claim(id),  -- the dependent claim
    depends_on      TEXT NOT NULL REFERENCES claim(id),  -- the assumption
    PRIMARY KEY (claim_id, depends_on)
);

-- Verdicts link a challenge result to the claim it challenges. The verdict itself
-- is a row in `claim` (kind='verdict'); this table records the target + outcome so
-- render can join efficiently.
CREATE TABLE verdict (
    verdict_claim_id TEXT NOT NULL REFERENCES claim(id),   -- the challenge claim
    target_claim_id  TEXT NOT NULL REFERENCES claim(id),   -- the claim being judged
    outcome          TEXT NOT NULL,   -- likely_true_positive | likely_false_positive | uncertain
    PRIMARY KEY (verdict_claim_id, target_claim_id)
);

CREATE INDEX idx_verdict_target ON verdict(target_claim_id);

-- ---------------------------------------------------------------------------
-- Rendered output pointer (the human-readable artifact lives on disk, not in-DB)
-- ---------------------------------------------------------------------------
CREATE TABLE render_output (
    assessment_id   TEXT NOT NULL REFERENCES assessment(id),
    path            TEXT NOT NULL,              -- access-controlled / unpublished
    rendered_at     TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (assessment_id, path)
);
