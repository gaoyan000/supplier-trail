"""Red-list entry -> FEI through FDA's FEI API (design §2). Two phases:

lookup_entries: ask FDA once per entry and store the answer (fei_api_lookups is the cache).
apply_lookups:  turn found answers into verified links; §10 Rule 1 accepts the FEI API as verification.
"""
import logging
from collections import Counter
from datetime import date

import psycopg
from psycopg.types.json import Jsonb

from .db import upsert_firm
from .fda.fei_api import FeiApiClient, build_fei_payload
from .resolve import build_country_index, country_code_for, verify_candidate
from .transform import FirmRecord

log = logging.getLogger(__name__)
FIRM_PROFILE_URL = "https://datadashboard.fda.gov/oii/firmprofile.htm?FEIi={fei}"
REVIEWER = "fei_api"
MIN_AGREEMENT = 0.98  # design §2: stop if the API disagrees with exact-name matches more often than this
MIN_COMPARED = 50

# Food and dietary-supplement industry codes (design §1 MVP scope) plus 99 (multi-industry, e.g. 99-19 Salmonella).
FOOD_ALERT = """(e.alert_number ~ '^[0-9]+-' AND (split_part(e.alert_number, '-', 1)::int BETWEEN 2 AND 41
                 OR split_part(e.alert_number, '-', 1)::int BETWEEN 45 AND 47
                 OR split_part(e.alert_number, '-', 1)::int IN (50, 52, 53, 54, 99)))"""


class AgreementTooLowError(RuntimeError):
    pass


def _pending(conn, limit: int) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT e.id, e.fda_name, e.fda_address, e.country,
                   coalesce(array_agg(f.fei) FILTER (WHERE c.match_method = 'exact_name'), '{{}}')
            FROM red_list_entries e
            LEFT JOIN red_list_candidates c ON c.entry_id = e.id
            LEFT JOIN firms f ON f.id = c.firm_id
            WHERE e.active AND e.firm_id IS NULL AND {FOOD_ALERT}
              AND NOT EXISTS (SELECT 1 FROM fei_api_lookups l WHERE l.entry_id = e.id)
            GROUP BY e.id
            ORDER BY e.date_published DESC NULLS LAST, e.id
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()


def _store(conn, entry_id: int, status: str, payload: dict | None, exact_feis: list[str], result=None) -> None:
    m = result.match if result else None
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO fei_api_lookups (entry_id, status, fei, legal_name, address, city, country_code, merged,
                                         exact_feis, request, response)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (entry_id, status, m and m.fei, m and m.legal_name, m and m.address, m and m.city, m and m.country_code,
             m and m.merged, exact_feis, Jsonb(payload) if payload else None, Jsonb(result.raw) if result else None),
        )
    conn.commit()


def lookup_entries(conn: psycopg.Connection, client: FeiApiClient, *, limit: int, archive=None) -> dict:
    """Look up to `limit` unlinked food red-list entries. FdaBlockedError propagates: stop, keep what is stored."""
    index = build_country_index(conn)
    stats = Counter()
    for entry_id, name, address, country, exact_feis in _pending(conn, limit):
        payload = build_fei_payload(name, address, country, country_code_for(country, None, index))
        if payload is None:
            _store(conn, entry_id, "unsupported", None, exact_feis)
            stats["unsupported"] += 1
        else:
            result = client.find(payload)
            if archive:
                archive("fei_api", f"entry_{entry_id}", {"request": payload, "response": result.raw})
            _store(conn, entry_id, result.status, payload, exact_feis, result)
            stats[result.status] += 1
            if result.status != "found":
                log.info("entry %s: %s", entry_id, result.status)
        stats["looked_up"] += 1
    return {"looked_up": 0, "found": 0, "not_found": 0, **stats}


def agreement(conn: psycopg.Connection) -> dict:
    """How often a found FEI is one of our exact-name candidates, over entries that had one."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT l.entry_id, e.alert_number, e.fda_name, l.fei, l.exact_feis, l.fei = ANY(l.exact_feis)
            FROM fei_api_lookups l JOIN red_list_entries e ON e.id = l.entry_id
            WHERE l.status = 'found' AND cardinality(l.exact_feis) > 0
            ORDER BY l.entry_id
            """
        )
        rows = cur.fetchall()
    agree = sum(1 for r in rows if r[5])
    return {
        "compared": len(rows),
        "agree": agree,
        "rate": round(agree / len(rows), 4) if rows else None,
        "disagreements": [{"entry_id": r[0], "alert": r[1], "fda_name": r[2], "api_fei": r[3], "exact_feis": r[4]}
                          for r in rows if not r[5]],
    }


def _country_name(conn, code: str | None) -> str | None:
    if not code:
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT country FROM firms WHERE country_code = %s AND country IS NOT NULL "
                    "GROUP BY country ORDER BY count(*) DESC LIMIT 1", (code,))
        row = cur.fetchone()
    return row[0] if row else None


def _firm_for(conn, lookup: tuple, today: date) -> tuple[int, bool]:
    _, fei, name, address, city, code = lookup
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM firms WHERE fei = %s", (fei,))
        row = cur.fetchone()
    if row:
        return row[0], False  # keep the name FDA's other datasets gave this firm
    record = FirmRecord(fei=fei, name=name, address=address, city=city, country_code=code,
                        country=_country_name(conn, code))
    return upsert_firm(conn, record, seen_on=today), True


def apply_lookups(conn: psycopg.Connection, *, today: date, min_agreement: float = MIN_AGREEMENT,
                  min_compared: int = MIN_COMPARED) -> dict:
    """Publish found FEIs as verified links, unless agreement with exact-name matches is too low to trust."""
    report = agreement(conn)
    if report["compared"] >= min_compared and report["rate"] < min_agreement:
        raise AgreementTooLowError(f"FEI API agrees with exact-name matches on {report['agree']}/{report['compared']}"
                                   f" ({report['rate']:.1%} < {min_agreement:.0%}); review `fei-report` first")
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT l.entry_id, l.fei, l.legal_name, l.address, l.city, l.country_code
            FROM fei_api_lookups l JOIN red_list_entries e ON e.id = l.entry_id
            WHERE l.status = 'found' AND l.applied_at IS NULL AND e.active AND e.firm_id IS NULL
            ORDER BY l.entry_id
            """
        )
        pending = cur.fetchall()
    applied = new_firms = 0
    for lookup in pending:
        entry_id, fei = lookup[0], lookup[1]
        firm_id, created = _firm_for(conn, lookup, today)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO red_list_candidates (entry_id, firm_id, match_method, match_confidence)
                VALUES (%s, %s, 'fei_api', 1.0)
                ON CONFLICT (entry_id, firm_id) DO UPDATE SET match_method = 'fei_api', match_confidence = 1.0
                """,
                (entry_id, firm_id),
            )
        verify_candidate(conn, entry_id=entry_id, firm_id=firm_id, reviewer=REVIEWER,
                         evidence_url=FIRM_PROFILE_URL.format(fei=fei))
        with conn.cursor() as cur:
            cur.execute("UPDATE fei_api_lookups SET applied_at = now() WHERE entry_id = %s", (entry_id,))
        conn.commit()
        applied += 1
        new_firms += created
    return {"applied": applied, "new_firms": new_firms}
