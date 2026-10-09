"""Thin clients for the FDA sources under test. Credentials come from spike/.env and are never printed."""
import itertools
import json
import os
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

UA = {"User-Agent": "Mozilla/5.0 (data-access spike)"}
TIMEOUT = 90
DASHBOARD_URL = "https://api-datadashboard.fda.gov/v1/{endpoint}"
ACCESSDATA_URL = "https://www.accessdata.fda.gov/rest/{path}?signature={sig}"
IMPORT_ALERT_LIST_URL = "https://www.accessdata.fda.gov/cms_ia/ialist.html"
IMPORT_ALERT_URL = "https://www.accessdata.fda.gov/cms_ia/{page}"
OPENFDA_URL = "https://api.fda.gov/food/enforcement.json"

_sig_counter = itertools.count()


def env(name: str) -> str:
    return os.environ.get(name, "").strip()


def dashboard(endpoint: str, *, filters=None, columns=None, rows=10, start=1, sort="FEINumber", order="DESC"):
    """POST to the FDA Data Dashboard API. Returns (http_status, body_dict)."""
    headers = {
        "Content-Type": "application/json",
        "Authorization-User": env("FDA_DASHBOARD_USER"),
        "Authorization-Key": env("FDA_DASHBOARD_KEY"),
    }
    body = {
        "start": start,
        "rows": rows,
        "sort": sort,
        "sortorder": order,
        "filters": filters or {},
        "columns": columns or [],
    }
    r = requests.post(DASHBOARD_URL.format(endpoint=endpoint), headers=headers, json=body, timeout=TIMEOUT)
    return r.status_code, r.json()


def accessdata(path: str, payload, key_var: str):
    """POST to an accessdata.fda.gov REST API (iRES, PCB, FEI). Unique signature defeats server caching."""
    sig = f"{int(time.time() * 1000)}{next(_sig_counter)}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization-User": env("FDA_DASHBOARD_USER"),
        "Authorization-Key": env(key_var),
        **UA,
    }
    data = {"payload": payload if isinstance(payload, str) else json.dumps(payload)}
    r = requests.post(ACCESSDATA_URL.format(path=path, sig=sig), headers=headers, data=data, timeout=TIMEOUT)
    return r.status_code, r.json()


def get_html(url: str) -> str:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def parse_alert_list(html: str):
    """Rows of the import-alert index: number, type, published date, title, page link."""
    soup = BeautifulSoup(html, "lxml")
    alerts = []
    for row in soup.select("table tr"):
        cells = [c.get_text(" ", strip=True) for c in row.find_all("td")]
        link = row.find("a", href=True)
        if len(cells) >= 4 and link:
            alerts.append({"number": cells[0], "type": cells[1], "date": cells[2], "title": cells[3].strip('"'),
                           "page": link["href"]})
    return alerts


def parse_red_list(html: str):
    """Firm blocks on an import-alert page, tagged with the country heading they sit under."""
    soup = BeautifulSoup(html, "lxml")
    firms, country = [], None
    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "div"]):
        if el.name.startswith("h"):
            country = el.get_text(" ", strip=True)
            continue
        if "div-info" not in (el.get("class") or []):
            continue
        names = el.select("div.div-name")
        addr = el.select_one("div.clear")
        firms.append({
            "country": country,
            "name": names[0].get_text(" ", strip=True) if names else "",
            "date_published": names[1].get_text(" ", strip=True).split(":", 1)[-1].strip() if len(names) > 1 else "",
            "address": " ".join(addr.get_text(" ", strip=True).split()) if addr else "",
        })
    return firms
