-- 002: FEI API lookups for red-list entries (design §2, FEI API). One row per entry: the cache that keeps
-- every entry from being sent to FDA twice, and the evidence behind fei_api links (§10 Rule 1).
CREATE TABLE IF NOT EXISTS fei_api_lookups (
    entry_id      BIGINT PRIMARY KEY REFERENCES red_list_entries(id) ON DELETE CASCADE,
    looked_up_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    status        TEXT NOT NULL,      -- found | not_found | ambiguous | invalid_input | unsupported
    fei           TEXT,
    legal_name    TEXT,
    address       TEXT,
    city          TEXT,
    country_code  TEXT,
    merged        BOOLEAN,
    exact_feis    TEXT[] NOT NULL DEFAULT '{}',  -- our exact-name candidates when looked up (agreement check)
    request       JSONB,
    response      JSONB,
    applied_at    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS fei_api_lookups_pending ON fei_api_lookups (status) WHERE applied_at IS NULL;
