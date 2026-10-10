"""Postgres access: migrations, firm/event upserts, firm aggregates."""
from datetime import date
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from .normalize import identity_key, normalize_name, slugify
from .transform import EventRecord, FirmRecord

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "db" / "migrations"
RECENT_REFUSAL_YEARS = 5
INDEXABLE_MIN_EVENTS = 2  # design §3: noindex single-signal suppliers


def connect(url: str) -> psycopg.Connection:
    return psycopg.connect(url)


def migrate(conn: psycopg.Connection, directory: Path) -> list[str]:
    """Apply *.sql files in name order that are not yet recorded. Returns the versions applied."""
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, "
                    "applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
        cur.execute("SELECT version FROM schema_migrations")
        done = {row[0] for row in cur.fetchall()}
    applied = []
    for path in sorted(directory.glob("*.sql")):
        if path.stem in done:
            continue
        with conn.cursor() as cur:
            cur.execute(path.read_text())
            cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
        applied.append(path.stem)
    conn.commit()
    return applied


def upsert_firm(conn: psycopg.Connection, firm: FirmRecord, *, seen_on: date) -> int:
    key = identity_key(fei=firm.fei, name=firm.name, address=firm.address, country=firm.country_code or firm.country)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO firms (fei, identity_key, canonical_name, norm_name, slug, address, city,
                               country_code, country, first_seen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (identity_key) DO UPDATE SET
                canonical_name = EXCLUDED.canonical_name,
                norm_name      = EXCLUDED.norm_name,
                slug           = EXCLUDED.slug,
                address        = COALESCE(EXCLUDED.address, firms.address),
                city           = COALESCE(EXCLUDED.city, firms.city),
                country_code   = COALESCE(EXCLUDED.country_code, firms.country_code),
                country        = COALESCE(EXCLUDED.country, firms.country),
                updated_at     = now()
            RETURNING id
            """,
            (firm.fei, key, firm.name, normalize_name(firm.name), slugify(firm.name), firm.address, firm.city,
             firm.country_code, firm.country, seen_on),
        )
        return cur.fetchone()[0]


def insert_event(conn: psycopg.Connection, firm_id: int | None, ev: EventRecord,
                 *, red_list_entry_id: int | None = None) -> bool:
    """Insert unless the same source record was stored before. True when new."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO events (firm_id, red_list_entry_id, type, occurred_on, product_code, alert_number, summary,
                                details, source, source_url, source_record_id, source_record_hash,
                                quarantined, quarantine_reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_record_hash) DO NOTHING
            RETURNING id
            """,
            (firm_id, red_list_entry_id, ev.type, ev.occurred_on, ev.product_code, ev.alert_number, ev.summary,
             Jsonb(ev.details), ev.source, ev.source_url, ev.source_record_id, ev.source_record_hash,
             ev.quarantine_reason is not None, ev.quarantine_reason),
        )
        return cur.fetchone() is not None


def refresh_firm_aggregates(conn: psycopg.Connection, *, today: date) -> None:
    """Recompute last_event_at, factual risk_status and indexable from non-quarantined events."""
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH agg AS (
                SELECT f.id,
                       min(e.occurred_on) AS first_event,
                       max(e.occurred_on) AS last_event,
                       count(e.id)        AS n_events,
                       bool_or(e.type = 'refusal'
                               AND e.occurred_on >= %(today)s::date - make_interval(years => %(years)s)) AS recent_refusal,
                       EXISTS (SELECT 1 FROM red_list_entries r WHERE r.firm_id = f.id AND r.active) AS on_red_list
                FROM firms f
                LEFT JOIN events e ON e.firm_id = f.id AND NOT e.quarantined
                GROUP BY f.id
            )
            UPDATE firms f SET
                first_seen    = LEAST(f.first_seen, agg.first_event),
                last_event_at = agg.last_event,
                risk_status   = CASE WHEN agg.on_red_list THEN 'on_red_list'
                                     WHEN agg.recent_refusal THEN 'recent_refusals'
                                     ELSE 'clear' END,
                indexable     = agg.n_events >= %(min_events)s OR agg.on_red_list
            FROM agg WHERE agg.id = f.id
            """,
            {"today": today, "years": RECENT_REFUSAL_YEARS, "min_events": INDEXABLE_MIN_EVENTS},
        )
