-- 001: data-pipeline tables (design §4). App tables (users, watches, ...) come in a later migration.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS firms (
    id              BIGSERIAL PRIMARY KEY,
    fei             TEXT UNIQUE,                 -- NULL only for firms known solely by name
    identity_key    TEXT NOT NULL UNIQUE,        -- 'fei:<n>' or 'name:<hash>'
    canonical_name  TEXT NOT NULL,
    norm_name       TEXT NOT NULL,
    slug            TEXT NOT NULL,
    address         TEXT,
    city            TEXT,
    country_code    TEXT,
    country         TEXT,
    first_seen      DATE,
    last_event_at   DATE,
    risk_status     TEXT NOT NULL DEFAULT 'clear',   -- on_red_list | recent_refusals | clear (§4, factual)
    indexable       BOOLEAN NOT NULL DEFAULT false,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS firms_norm_name_trgm ON firms USING gin (norm_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS firms_country ON firms (country_code);

CREATE TABLE IF NOT EXISTS firm_aliases (
    id               BIGSERIAL PRIMARY KEY,
    firm_id          BIGINT NOT NULL REFERENCES firms(id) ON DELETE CASCADE,
    name             TEXT NOT NULL,
    address          TEXT,
    source           TEXT NOT NULL,
    match_method     TEXT NOT NULL,              -- fei | exact_name | fuzzy_name | fei_api | manual
    match_confidence REAL NOT NULL,
    link_status      TEXT NOT NULL DEFAULT 'unverified',  -- verified | unverified | disputed | rejected (§10)
    verified_by      TEXT,
    verified_at      TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (firm_id, name, source)
);

CREATE TABLE IF NOT EXISTS import_alerts (
    number          TEXT PRIMARY KEY,            -- 'NN-NN' or 'NN-NNN'
    alert_type      TEXT,
    title           TEXT NOT NULL,
    page_url        TEXT NOT NULL,
    last_published  DATE,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS red_list_entries (
    id              BIGSERIAL PRIMARY KEY,
    alert_number    TEXT NOT NULL REFERENCES import_alerts(number),
    entry_key       TEXT NOT NULL,               -- hash(alert + norm name + norm address)
    fda_name        TEXT NOT NULL,
    fda_address     TEXT,
    country         TEXT,
    date_published  DATE,
    product_codes   TEXT[] NOT NULL DEFAULT '{}',
    problems        TEXT[] NOT NULL DEFAULT '{}',
    fei_in_text     TEXT[] NOT NULL DEFAULT '{}', -- FEIs FDA wrote in the entry's notes
    slug            TEXT NOT NULL,
    firm_id         BIGINT REFERENCES firms(id),  -- set ONLY for a verified link (§10 Rule 1)
    active          BOOLEAN NOT NULL DEFAULT true,
    first_seen      DATE NOT NULL,
    removed_on      DATE,
    UNIQUE (entry_key)
);
CREATE INDEX IF NOT EXISTS red_list_alert ON red_list_entries (alert_number);

CREATE TABLE IF NOT EXISTS red_list_candidates (
    entry_id        BIGINT NOT NULL REFERENCES red_list_entries(id) ON DELETE CASCADE,
    firm_id         BIGINT NOT NULL REFERENCES firms(id) ON DELETE CASCADE,
    match_method    TEXT NOT NULL,
    match_confidence REAL NOT NULL,
    link_status     TEXT NOT NULL DEFAULT 'unverified',
    verified_by     TEXT,
    verified_at     TIMESTAMPTZ,
    evidence_url    TEXT,
    PRIMARY KEY (entry_id, firm_id)
);

CREATE TABLE IF NOT EXISTS events (
    id                 BIGSERIAL PRIMARY KEY,
    firm_id            BIGINT REFERENCES firms(id),
    red_list_entry_id  BIGINT REFERENCES red_list_entries(id),
    type               TEXT NOT NULL,   -- refusal | recall | warning_letter | compliance_action |
                                        -- inspection_nai | inspection_vai | inspection_oai |
                                        -- alert_listed | alert_removed
    occurred_on        DATE,
    product_code       TEXT,
    alert_number       TEXT,
    summary            TEXT NOT NULL,
    details            JSONB NOT NULL DEFAULT '{}',
    source             TEXT NOT NULL,
    source_url         TEXT,
    source_record_id   TEXT,
    source_record_hash TEXT NOT NULL UNIQUE,
    quarantined        BOOLEAN NOT NULL DEFAULT false,
    quarantine_reason  TEXT,
    ingested_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS events_firm ON events (firm_id, occurred_on DESC);
CREATE INDEX IF NOT EXISTS events_type_date ON events (type, occurred_on DESC);

CREATE TABLE IF NOT EXISTS ingest_runs (
    id            BIGSERIAL PRIMARY KEY,
    source        TEXT NOT NULL,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at   TIMESTAMPTZ,
    status        TEXT NOT NULL DEFAULT 'running',  -- running | ok | failed
    rows_fetched  INTEGER NOT NULL DEFAULT 0,
    rows_new      INTEGER NOT NULL DEFAULT 0,
    rows_quarantined INTEGER NOT NULL DEFAULT 0,
    raw_path      TEXT,
    error         TEXT
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version    TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
