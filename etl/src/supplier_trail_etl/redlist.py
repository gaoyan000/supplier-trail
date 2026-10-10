"""Store import-alert red-list snapshots and emit listed/removed events."""
from datetime import date

import psycopg

from .db import insert_event
from .fda.import_alerts import PAGE_URL, AlertIndexRow, RedListEntry, diff_red_list
from .normalize import check_date, record_hash
from .transform import EventRecord, FirmRecord

MAX_DROP_RATIO = 0.2   # design §9: a >20% drop is treated as a scraper failure
MIN_SIZE_FOR_GUARD = 10


class SnapshotDropError(RuntimeError):
    pass


def upsert_alert(conn: psycopg.Connection, alert: AlertIndexRow) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO import_alerts (number, alert_type, title, page_url, last_published)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (number) DO UPDATE SET alert_type = EXCLUDED.alert_type, title = EXCLUDED.title,
                page_url = EXCLUDED.page_url, last_published = EXCLUDED.last_published, updated_at = now()
            """,
            (alert.number, alert.alert_type, alert.title, PAGE_URL.format(page=alert.page), alert.last_published),
        )


def _alert_event(entry_name: str, entry_key: str, alert_number: str, etype: str, occurred: date | None,
                 summary: str, today: date, url: str | None) -> EventRecord:
    payload = {"entry_key": entry_key, "alert": alert_number, "type": etype, "on": str(occurred)}
    return EventRecord(
        firm=FirmRecord(fei=None, name=entry_name), type=etype, occurred_on=occurred, summary=summary,
        source="import_alerts.red_list", source_record_id=entry_key,
        source_record_hash=record_hash("import_alerts.red_list", payload),
        quarantine_reason=check_date(occurred, today=today), alert_number=alert_number, source_url=url,
        details=payload,
    )


def apply_red_list_snapshot(conn: psycopg.Connection, alert_number: str, entries: list[RedListEntry],
                            *, today: date) -> tuple[int, int]:
    """Diff today's parsed red list against active rows. Returns (added, removed)."""
    with conn.cursor() as cur:
        cur.execute("SELECT entry_key, id, fda_name, firm_id FROM red_list_entries WHERE alert_number=%s AND active",
                    (alert_number,))
        active = {row[0]: row[1:] for row in cur.fetchall()}
        cur.execute("SELECT page_url FROM import_alerts WHERE number=%s", (alert_number,))
        url = cur.fetchone()[0]

    current = {e.entry_key: e for e in entries}
    if len(active) >= MIN_SIZE_FOR_GUARD and len(current) < len(active) * (1 - MAX_DROP_RATIO):
        raise SnapshotDropError(f"{alert_number}: {len(active)} → {len(current)} entries; refusing to apply")

    added, removed = diff_red_list(previous=set(active), current=set(current))
    with conn.cursor() as cur:
        for key in sorted(added):
            e = current[key]
            cur.execute(
                """
                INSERT INTO red_list_entries (alert_number, entry_key, fda_name, fda_address, country, date_published,
                    product_codes, problems, fei_in_text, slug, first_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (entry_key) DO UPDATE SET active = true, removed_on = NULL
                RETURNING id
                """,
                (alert_number, key, e.fda_name, e.fda_address, e.country, e.date_published, list(e.product_codes),
                 list(e.problems), list(e.fei_in_text), e.slug, today),
            )
            entry_id = cur.fetchone()[0]
            ev = _alert_event(e.fda_name, key, alert_number, "alert_listed", e.date_published,
                              f"Added to red list, Import Alert {alert_number}", today, url)
            insert_event(conn, None, ev, red_list_entry_id=entry_id)
        for key in sorted(set(current) & set(active)):
            e = current[key]
            cur.execute(
                "UPDATE red_list_entries SET product_codes=%s, problems=%s, fei_in_text=%s, date_published=%s "
                "WHERE id=%s",
                (list(e.product_codes), list(e.problems), list(e.fei_in_text), e.date_published, active[key][0]),
            )
        for key in sorted(removed):
            entry_id, name, firm_id = active[key]
            cur.execute("UPDATE red_list_entries SET active = false, removed_on = %s WHERE id = %s", (today, entry_id))
            ev = _alert_event(name, key, alert_number, "alert_removed", today,
                              f"No longer on red list, Import Alert {alert_number} (as of {today})", today, url)
            insert_event(conn, firm_id, ev, red_list_entry_id=entry_id)
    return len(added), len(removed)
