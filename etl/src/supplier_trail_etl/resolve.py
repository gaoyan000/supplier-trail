"""Red-list entry → FEI firm matching (design §2). Produces UNVERIFIED candidates only;
a link becomes public solely through verify_candidate() after a human check (design §10 Rule 1)."""
import psycopg

from .normalize import normalize_name

FUZZY_MIN_SIMILARITY = 0.6
EXACT_CONFIDENCE = 0.95
FEI_TEXT_CONFIDENCE = 0.5  # FDA notes often name a *different* firm (packer, shipper)

# Red-list headings (older ISO short names) that FDA's datasets never spell the same way.
NAME_ALIASES = {
    "syrian arab republic": "SY",
    "tanzania united republic of": "TZ",
    "surinam": "SR",
    "west bank": "PS",
    "gambia the": "GM",
    "burma": "MM",
    "kampuchea": "KH",
    "brunei darussalam": "BN",
    "korea the republic of": "KR",
    "korea the democratic people s republic of": "KP",
    "hong kong sar": "HK",
}


def build_country_index(conn: psycopg.Connection) -> dict[str, str]:
    """Normalized country name → ISO code, learned from FDA records that carry both."""
    with conn.cursor() as cur:
        cur.execute("SELECT country, country_code, count(*) FROM firms WHERE country IS NOT NULL "
                    "AND country_code IS NOT NULL GROUP BY 1, 2 ORDER BY 3 DESC")
        index: dict[str, str] = {}
        for name, code, _ in cur.fetchall():
            index.setdefault(normalize_name(name), code.upper())
    return index


def country_code_for(name: str | None, code: str | None, index: dict[str, str]) -> str | None:
    if code and code.strip():
        return code.strip().upper()
    key = normalize_name(name or "")
    return NAME_ALIASES.get(key) or index.get(key)


def _add_candidate(cur, entry_id: int, firm_id: int, method: str, confidence: float) -> None:
    cur.execute(
        """
        INSERT INTO red_list_candidates (entry_id, firm_id, match_method, match_confidence)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (entry_id, firm_id) DO UPDATE
            SET match_method = EXCLUDED.match_method, match_confidence = EXCLUDED.match_confidence
            WHERE red_list_candidates.link_status = 'unverified'
              AND red_list_candidates.match_confidence < EXCLUDED.match_confidence
        """,
        (entry_id, firm_id, method, confidence),
    )


def resolve_red_list(conn: psycopg.Connection) -> dict:
    """Find candidates for active, unlinked entries: exact name+country, fuzzy name+country, FEI in FDA notes."""
    index = build_country_index(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT id, fda_name, country, fei_in_text FROM red_list_entries WHERE active AND firm_id IS NULL")
        pending = cur.fetchall()
        for entry_id, name, country, feis in pending:
            target = normalize_name(name)
            country_key = country_code_for(country, None, index)
            cur.execute(
                """
                SELECT id, norm_name, similarity(norm_name, %s) AS sim, country, country_code
                FROM firms
                WHERE fei IS NOT NULL AND norm_name %% %s AND similarity(norm_name, %s) >= %s
                ORDER BY sim DESC LIMIT 10
                """,
                (target, target, target, FUZZY_MIN_SIMILARITY),
            )
            for firm_id, firm_norm, sim, firm_country, firm_code in cur.fetchall():
                if country_key is None or country_code_for(firm_country, firm_code, index) != country_key:
                    continue
                if firm_norm == target:
                    _add_candidate(cur, entry_id, firm_id, "exact_name", EXACT_CONFIDENCE)
                else:
                    _add_candidate(cur, entry_id, firm_id, "fuzzy_name", round(float(sim), 3))
            if feis:
                cur.execute("SELECT id FROM firms WHERE fei = ANY(%s)", (list(feis),))
                for (firm_id,) in cur.fetchall():
                    _add_candidate(cur, entry_id, firm_id, "fei_in_text", FEI_TEXT_CONFIDENCE)
        cur.execute(
            """
            SELECT count(*) FILTER (WHERE n > 0), count(*) FILTER (WHERE n_exact = 1), count(*) FILTER (WHERE n = 0)
            FROM (SELECT e.id, count(c.firm_id) n, count(c.firm_id) FILTER (WHERE c.match_method='exact_name') n_exact
                  FROM red_list_entries e LEFT JOIN red_list_candidates c ON c.entry_id = e.id
                  WHERE e.active AND e.firm_id IS NULL GROUP BY e.id) s
            """
        )
        with_cands, single_exact, none = cur.fetchone()
    return {"pending_entries": len(pending), "entries_with_candidates": with_cands,
            "single_exact_match": single_exact, "no_candidate": none}


def verify_candidate(conn: psycopg.Connection, *, entry_id: int, firm_id: int, reviewer: str, evidence_url: str) -> None:
    """Record a human-checked link (FDA firm profile lists the same alert). Makes the link public."""
    if not reviewer or not evidence_url:
        raise ValueError("a verified link needs a reviewer and an evidence URL")
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE red_list_candidates SET link_status = 'verified', verified_by = %s, verified_at = now(),
                evidence_url = %s
            WHERE entry_id = %s AND firm_id = %s
            RETURNING match_method, match_confidence
            """,
            (reviewer, evidence_url, entry_id, firm_id),
        )
        found = cur.fetchone()
        if found is None:
            raise ValueError("no such candidate")
        method, confidence = found
        cur.execute("UPDATE red_list_entries SET firm_id = %s WHERE id = %s RETURNING fda_name, fda_address",
                    (firm_id, entry_id))
        name, address = cur.fetchone()
        cur.execute("UPDATE events SET firm_id = %s WHERE red_list_entry_id = %s", (firm_id, entry_id))
        cur.execute(
            """
            INSERT INTO firm_aliases (firm_id, name, address, source, match_method, match_confidence,
                                      link_status, verified_by, verified_at)
            VALUES (%s, %s, %s, 'import_alerts.red_list', %s, %s, 'verified', %s, now())
            ON CONFLICT (firm_id, name, source) DO UPDATE SET link_status = 'verified',
                verified_by = EXCLUDED.verified_by, verified_at = EXCLUDED.verified_at
            """,
            (firm_id, name, address, method, confidence, reviewer),
        )
