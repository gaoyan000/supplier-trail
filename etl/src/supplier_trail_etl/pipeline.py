"""Sync jobs: fetch → archive raw → transform → upsert → events. One commit per page/alert."""
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import psycopg

from .db import insert_event, upsert_firm
from .fda.apis import DashboardClient, IresClient
from .fda.http import FdaHttp
from .fda.import_alerts import LIST_URL, PAGE_URL, parse_alert_index, parse_red_list
from .normalize import identity_key
from .redlist import SnapshotDropError, apply_red_list_snapshot, upsert_alert
from .transform import (
    EventRecord,
    compliance_to_event,
    inspection_to_event,
    recall_to_event,
    refusal_to_event,
)

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DashboardJob:
    endpoint: str
    filters: dict
    sort: str
    mapper: Callable[..., EventRecord]


DASHBOARD_JOBS = {
    "refusals": DashboardJob("import_refusals", {"ProductCategory": ["Human Foods"]}, "RefusalDate", refusal_to_event),
    "compliance": DashboardJob("compliance_actions", {"ProductType": ["Food/Cosmetics"]}, "ActionTakenDate",
                               compliance_to_event),
    "inspections": DashboardJob("inspections_classifications", {"ProductType": ["Food/Cosmetics"]},
                                "InspectionEndDate", inspection_to_event),
}


@dataclass
class RunStats:
    fetched: int = 0
    new: int = 0
    quarantined: int = 0
    skipped: int = 0

    def as_dict(self) -> dict:
        return dict(fetched=self.fetched, new=self.new, quarantined=self.quarantined, skipped=self.skipped)


def _start_run(conn, source: str) -> int:
    with conn.cursor() as cur:
        cur.execute("INSERT INTO ingest_runs (source) VALUES (%s) RETURNING id", (source,))
        run_id = cur.fetchone()[0]
    conn.commit()
    return run_id


def _finish_run(conn, run_id: int, stats: RunStats, status: str, error: str | None = None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE ingest_runs SET finished_at=now(), status=%s, rows_fetched=%s, rows_new=%s, "
            "rows_quarantined=%s, error=%s WHERE id=%s",
            (status, stats.fetched, stats.new, stats.quarantined, error, run_id),
        )
    conn.commit()


LOCK_RETRY_ERRORS = (psycopg.errors.DeadlockDetected, psycopg.errors.SerializationFailure)


def retry_on_lock_conflict(conn, work: Callable, *, attempts: int = 3, backoff_s: float = 2.0):
    """Run work(); on a deadlock/serialization failure roll back and retry (concurrent jobs share firms)."""
    for attempt in range(1, attempts + 1):
        try:
            return work()
        except LOCK_RETRY_ERRORS:
            conn.rollback()
            if attempt == attempts:
                raise
            log.warning("lock conflict, retrying page (attempt %d/%d)", attempt + 1, attempts)
            time.sleep(backoff_s * attempt)


@dataclass(frozen=True)
class PageResult:
    new: int
    quarantined: int
    skipped: int
    firm_ids: dict


def _load_page(conn, raws: list[dict], mapper, today: date, known_firms: dict) -> PageResult:
    """Map, upsert firms in sorted key order (consistent lock order across jobs), insert events, commit."""
    mapped, skipped = [], 0
    for raw in raws:
        try:
            ev = mapper(raw, today=today)
        except ValueError as exc:
            skipped += 1
            log.debug("skipped record: %s", exc)
            continue
        key = identity_key(fei=ev.firm.fei, name=ev.firm.name, address=ev.firm.address,
                           country=ev.firm.country_code or ev.firm.country)
        mapped.append((key, ev))
    firm_by_key = {}
    for key, ev in sorted(mapped, key=lambda pair: pair[0]):
        if key not in known_firms and key not in firm_by_key:
            firm_by_key[key] = upsert_firm(conn, ev.firm, seen_on=today)
    new = quarantined = 0
    for key, ev in mapped:
        if insert_event(conn, known_firms.get(key) or firm_by_key[key], ev):
            new += 1
            quarantined += ev.quarantine_reason is not None
    conn.commit()
    return PageResult(new=new, quarantined=quarantined, skipped=skipped, firm_ids=firm_by_key)


def _run(conn, source: str, pages, mapper, http: FdaHttp, today: date, incremental: bool) -> RunStats:
    stats, known_firms = RunStats(), {}
    run_id = _start_run(conn, source)
    try:
        for n, raws in pages:
            http.archive(source, f"page_{n:04d}", raws)
            result = retry_on_lock_conflict(conn, lambda: _load_page(conn, raws, mapper, today, known_firms))
            known_firms.update(result.firm_ids)  # only after commit: rolled-back ids never enter the cache
            stats.fetched += len(raws)
            stats.new += result.new
            stats.quarantined += result.quarantined
            stats.skipped += result.skipped
            page_new = result.new
            log.info("%s page %d: %d rows, %d new (total new %d)", source, n, len(raws), page_new, stats.new)
            if incremental and page_new == 0:
                log.info("%s: page with no new rows, stopping incremental sync", source)
                break
    except Exception as exc:
        conn.rollback()
        _finish_run(conn, run_id, stats, "failed", repr(exc))
        raise
    _finish_run(conn, run_id, stats, "ok")
    return stats


def sync_dashboard(conn: psycopg.Connection, client: DashboardClient, http: FdaHttp, name: str, *, today: date,
                   incremental: bool, max_pages: int | None = None) -> RunStats:
    job = DASHBOARD_JOBS[name]
    pages = client.iter_pages(job.endpoint, filters=job.filters, sort=job.sort, max_pages=max_pages)
    return _run(conn, f"dashboard.{job.endpoint}", pages, job.mapper, http, today, incremental)


def sync_recalls(conn: psycopg.Connection, client: IresClient, http: FdaHttp, *, today: date, incremental: bool,
                 max_pages: int | None = None) -> RunStats:
    pages = client.iter_pages(center="CFSAN", max_pages=max_pages)
    return _run(conn, "ires.recalls", pages, recall_to_event, http, today, incremental)


def sync_red_lists(conn: psycopg.Connection, http: FdaHttp, *, today: date, only: list[str] | None = None) -> dict:
    run_id = _start_run(conn, "import_alerts.red_list")
    totals = {"alerts": 0, "added": 0, "removed": 0, "refused_drops": [], "errors": []}
    try:
        index_html = http.request("GET", LIST_URL).text
        http.archive("import_alerts", "index", {"html": index_html})
        alerts = [a for a in parse_alert_index(index_html) if not only or a.number in only]
        for alert in alerts:
            try:
                html = http.request("GET", PAGE_URL.format(page=alert.page)).text
                http.archive("import_alerts", alert.number, {"html": html})
                upsert_alert(conn, alert)
                added, removed = apply_red_list_snapshot(
                    conn, alert.number, parse_red_list(html, alert_number=alert.number), today=today)
                conn.commit()
                totals["alerts"] += 1
                totals["added"] += added
                totals["removed"] += removed
                log.info("alert %s: +%d -%d", alert.number, added, removed)
            except SnapshotDropError as exc:
                conn.rollback()
                totals["refused_drops"].append(str(exc))
                log.warning("%s", exc)
            except Exception as exc:  # one bad page must not stop the other alerts
                conn.rollback()
                totals["errors"].append(f"{alert.number}: {exc!r}")
                log.exception("alert %s failed", alert.number)
    except Exception as exc:
        _finish_run(conn, run_id, RunStats(), "failed", repr(exc))
        raise
    stats = RunStats(fetched=totals["alerts"], new=totals["added"])
    _finish_run(conn, run_id, stats, "ok" if not totals["errors"] else "failed",
                "; ".join(totals["errors"]) or None)
    return totals
