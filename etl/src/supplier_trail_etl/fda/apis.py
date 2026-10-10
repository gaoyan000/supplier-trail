"""FDA Data Dashboard API and accessdata REST APIs (iRES). Request shapes verified in spike/ (design §2)."""
import itertools
import json
import time
from collections.abc import Iterator

from .http import FdaHttp

DASHBOARD_URL = "https://api-datadashboard.fda.gov/v1/{endpoint}"
ACCESSDATA_URL = "https://www.accessdata.fda.gov/rest/{path}?signature={sig}"
DASHBOARD_PAGE_MAX = 5000
IRES_PAGE = 1000
DASHBOARD_OK = "Success."
DASHBOARD_EMPTY = "No results found."

_sig = itertools.count()


class FdaApiError(RuntimeError):
    pass


class DashboardClient:
    def __init__(self, http: FdaHttp, *, user: str, key: str):
        self._http = http
        self._headers = {"Content-Type": "application/json", "Authorization-User": user, "Authorization-Key": key}

    def page(self, endpoint: str, *, filters: dict, sort: str, start: int, rows: int = DASHBOARD_PAGE_MAX,
             order: str = "DESC", columns: list[str] | None = None) -> list[dict]:
        body = {"start": start, "rows": rows, "sort": sort, "sortorder": order,
                "filters": filters, "columns": columns or []}
        resp = self._http.request("POST", DASHBOARD_URL.format(endpoint=endpoint), headers=self._headers, json=body)
        data = resp.json()
        message = data.get("message")
        if message == DASHBOARD_EMPTY:
            return []
        if message != DASHBOARD_OK:
            # The body's statuscode is not an HTTP status: 400 = success, 412 = empty (spike finding).
            raise FdaApiError(f"{endpoint}: {message} ({data.get('statuscode')})")
        return data.get("result") or []

    def iter_pages(self, endpoint: str, *, filters: dict, sort: str, order: str = "DESC",
                   max_pages: int | None = None) -> Iterator[tuple[int, list[dict]]]:
        for n in itertools.count():
            if max_pages is not None and n >= max_pages:
                return
            rows = self.page(endpoint, filters=filters, sort=sort, order=order, start=1 + n * DASHBOARD_PAGE_MAX)
            if not rows:
                return
            yield n, rows
            if len(rows) < DASHBOARD_PAGE_MAX:
                return


class IresClient:
    """Enforcement Reports (recalls). Each call needs a unique signature or the server returns a cached reply."""

    COLUMNS = ("productid,recalleventid,recallnum,firmlegalnam,firmfeinum,firmcountrynam,firmcitynam,"
               "firmline1adr,centercd,centerclassificationtypetxt,productdescriptiontxt,productshortreasontxt,"
               "recallinitiationdt,terminationdt,phasetxt,eventlmd")

    def __init__(self, http: FdaHttp, *, user: str, key: str):
        self._http = http
        self._headers = {"Content-Type": "application/x-www-form-urlencoded",
                         "Authorization-User": user, "Authorization-Key": key}

    def page(self, *, center: str, start: int, rows: int = IRES_PAGE) -> tuple[int, list[dict]]:
        payload = {"displaycolumns": self.COLUMNS, "filter": f"[{{'centercd':['{center}']}}]",
                   "start": start, "rows": rows, "sort": "productid", "sortorder": "desc"}
        url = ACCESSDATA_URL.format(path="iresapi/recalls/", sig=f"{int(time.time() * 1000)}{next(_sig)}")
        data = self._http.request("POST", url, headers=self._headers, data={"payload": json.dumps(payload)}).json()
        if str(data.get("MESSAGE", "")).lower() != "success":
            raise FdaApiError(f"iRES: {data.get('MESSAGE')} ({data.get('STATUSCODE')})")
        return int(data.get("RESULTCOUNT") or 0), data.get("RESULT") or []

    def iter_pages(self, *, center: str, max_pages: int | None = None) -> Iterator[tuple[int, list[dict]]]:
        for n in itertools.count():
            if max_pages is not None and n >= max_pages:
                return
            _, rows = self.page(center=center, start=1 + n * IRES_PAGE)
            if not rows:
                return
            yield n, rows
            if len(rows) < IRES_PAGE:
                return
