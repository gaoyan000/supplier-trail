"""st-etl: run pipeline jobs.

  st-etl migrate
  st-etl sync refusals|compliance|inspections|recalls [--full] [--max-pages N]
  st-etl sync red-lists [--only 99-19 ...]
  st-etl resolve
  st-etl stats
  st-etl review-export out.csv
"""
import argparse
import csv
import json
import logging
import sys
from datetime import date

from .config import load_settings, require
from .db import MIGRATIONS_DIR, connect, migrate, refresh_firm_aggregates
from .fda.apis import DashboardClient, IresClient
from .fda.http import FdaHttp
from .pipeline import DASHBOARD_JOBS, sync_dashboard, sync_recalls, sync_red_lists
from .resolve import resolve_red_list

PROFILE_URL = "https://datadashboard.fda.gov/oii/firmprofile.htm?FEIi={fei}"


def _stats(conn) -> dict:
    q = {
        "firms": "select count(*) from firms",
        "firms_with_fei": "select count(*) from firms where fei is not null",
        "firms_indexable": "select count(*) from firms where indexable",
        "firms_foreign_indexable": "select count(*) from firms where indexable and coalesce(country_code,'') <> 'US'",
        "events_quarantined": "select count(*) from events where quarantined",
        "red_list_active_entries": "select count(*) from red_list_entries where active",
        "red_list_verified_links": "select count(*) from red_list_entries where firm_id is not null",
        "red_list_with_candidate": "select count(distinct entry_id) from red_list_candidates",
    }
    out = {}
    with conn.cursor() as cur:
        for k, sql in q.items():
            cur.execute(sql)
            out[k] = cur.fetchone()[0]
        cur.execute("select type, count(*) from events group by type order by 2 desc")
        out["events_by_type"] = dict(cur.fetchall())
        cur.execute("select coalesce(country,'?'), count(*) from firms where indexable group by 1 order by 2 desc limit 10")
        out["top_countries_indexable"] = dict(cur.fetchall())
    return out


def _review_export(conn, path: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT e.id, e.alert_number, e.fda_name, e.fda_address, e.country, c.firm_id, f.fei, f.canonical_name,
                   f.address, c.match_method, c.match_confidence
            FROM red_list_candidates c
            JOIN red_list_entries e ON e.id = c.entry_id
            JOIN firms f ON f.id = c.firm_id
            WHERE c.link_status = 'unverified' AND e.active
            ORDER BY c.match_confidence DESC, e.alert_number, e.fda_name
            """
        )
        rows = cur.fetchall()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["entry_id", "alert", "fda_name", "fda_address", "country", "firm_id", "fei", "firm_name",
                    "firm_address", "method", "confidence", "evidence_url", "decision(verified/rejected)"])
        for r in rows:
            w.writerow([*r, PROFILE_URL.format(fei=r[6]), ""])
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="st-etl")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate")
    s = sub.add_parser("sync")
    s.add_argument("job", choices=[*DASHBOARD_JOBS, "recalls", "red-lists"])
    s.add_argument("--full", action="store_true", help="page through everything (default: stop at known rows)")
    s.add_argument("--max-pages", type=int)
    s.add_argument("--only", nargs="*", help="red-lists: only these alert numbers")
    sub.add_parser("resolve")
    sub.add_parser("stats")
    r = sub.add_parser("review-export")
    r.add_argument("path")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    settings = load_settings()
    today = date.today()
    with connect(settings.database_url) as conn:
        if args.cmd == "migrate":
            print("applied:", migrate(conn, MIGRATIONS_DIR) or "nothing new")
            return 0
        if args.cmd == "stats":
            print(json.dumps(_stats(conn), indent=2, default=str))
            return 0
        if args.cmd == "resolve":
            print(json.dumps(resolve_red_list(conn), indent=2))
            refresh_firm_aggregates(conn, today=today)
            conn.commit()
            return 0
        if args.cmd == "review-export":
            print(f"wrote {_review_export(conn, args.path)} candidates to {args.path}")
            return 0

        http = FdaHttp(interval_s=settings.request_interval_s, raw_dir=settings.raw_dir)
        user = require(settings.fda_user, "FDA_DASHBOARD_USER")
        if args.job == "red-lists":
            result = sync_red_lists(conn, http, today=today, only=args.only)
        elif args.job == "recalls":
            client = IresClient(http, user=user, key=require(settings.ires_key, "ENFORCEMENT_REPORTS_KEY"))
            result = sync_recalls(conn, client, http, today=today, incremental=not args.full,
                                  max_pages=args.max_pages).as_dict()
        else:
            client = DashboardClient(http, user=user, key=require(settings.dashboard_key, "FDA_DASHBOARD_KEY"))
            result = sync_dashboard(conn, client, http, args.job, today=today, incremental=not args.full,
                                    max_pages=args.max_pages).as_dict()
        refresh_firm_aggregates(conn, today=today)
        conn.commit()
        print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
