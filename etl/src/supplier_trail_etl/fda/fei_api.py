"""FDA FEI API: firm name + address -> FEI (design §2, FEI API). Request shape verified 2026-10-16."""
import itertools
import json
import re
import time
from dataclasses import dataclass

import requests

from .apis import ACCESSDATA_URL, FdaApiError

FIND_PATH = "feiapi/firmdata/feidata"
OK, NO_RESULTS = 400, 412
INPUT_ERRORS = {403, 405, 406, 407, 420, 435}  # bad payload for this one entry
STOP_CODES = {401, 413, 430}                   # denied, service unavailable, hourly limit
_US_STATE_ZIP = re.compile(r"^([A-Z]{2})\b\s*([\d-]*)")
_sig = itertools.count()


class FdaBlockedError(FdaApiError):
    """FDA refused service (outage, quota or bot block). Stop all FDA calls; retry hours later."""


@dataclass(frozen=True)
class FeiMatch:
    fei: str
    legal_name: str
    address: str | None
    city: str | None
    country_code: str | None
    merged: bool


@dataclass(frozen=True)
class FeiResult:
    status: str               # found | not_found | ambiguous | invalid_input
    match: FeiMatch | None
    raw: dict


def build_fei_payload(name: str, address: str | None, country: str | None, country_code: str | None) -> dict | None:
    """Split FDA's red-list address ("street, city, province COUNTRY") into the API's fields; None when unusable."""
    parts = [p.strip() for p in (address or "").split(",") if p.strip()]
    if not country_code or len(parts) < 2:
        return None
    last = re.sub(rf"\s*{re.escape(country or '')}\s*$", "", parts[-1], flags=re.IGNORECASE).strip()
    if len(parts) >= 3:
        street, city, region = ", ".join(parts[:-2]), parts[-2], last
    else:
        street, city, region = parts[0], last, ""
    if not city:
        return None
    state = zip_code = province = ""
    if country_code == "US":
        found = _US_STATE_ZIP.match(region)
        if not found:
            return None
        state, zip_code = found.group(1), found.group(2)
    else:
        province = region
    return {"firmname": name, "firmaddress1": street, "firmaddress2": "", "firmcity": city, "firmstate": state,
            "firmprovince": province, "firmcountry": country_code, "firmzip": zip_code}


def _match(item: dict) -> FeiMatch:
    addr = item.get("physicaladdress") or {}
    street = ", ".join(p for p in (addr.get("FIRMADDRESS1"), addr.get("FIRMADDRESS2")) if p and p.strip())
    return FeiMatch(fei=str(item["FEINUMBER"]), legal_name=str(item.get("LEGALNAME") or "").strip(),
                    address=street or None, city=addr.get("FIRMCITY") or None,
                    country_code=(addr.get("FIRMCOUNTRY") or None), merged=bool(item.get("MERGEDFIRMINDICATOR")))


class FeiApiClient:
    def __init__(self, http, *, user: str, key: str):
        self._http = http
        self._headers = {"Content-Type": "application/x-www-form-urlencoded",
                         "Authorization-User": user, "Authorization-Key": key}

    def find(self, payload: dict) -> FeiResult:
        url = ACCESSDATA_URL.format(path=FIND_PATH, sig=f"{int(time.time() * 1000)}{next(_sig)}")
        try:
            resp = self._http.request("POST", url, headers=self._headers, data={"payLoad": json.dumps(payload)})
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status in (403, 429):
                raise FdaBlockedError(f"FDA refused the request (HTTP {status})") from exc
            raise
        if resp.history or "apology" in resp.url:
            raise FdaBlockedError(f"FDA redirected to its block page: {resp.url}")
        try:
            body = resp.json()
        except ValueError as exc:
            raise FdaBlockedError("FEI API returned a non-JSON page") from exc
        code = body.get("STATUSCODE")
        if not body or code in STOP_CODES:
            raise FdaBlockedError(f"FEI API: {body.get('MESSAGE')!r} ({code})")
        if code == NO_RESULTS:
            return FeiResult("not_found", None, body)
        if code in INPUT_ERRORS:
            return FeiResult("invalid_input", None, body)
        if code != OK:
            raise FdaApiError(f"FEI API: unexpected {body.get('MESSAGE')!r} ({code})")
        result = body.get("RESULT")
        items = result if isinstance(result, list) else [result] if result else []
        feis = {str(i.get("FEINUMBER")) for i in items if i.get("FEINUMBER")}
        if len(feis) != 1:
            return FeiResult("ambiguous" if feis else "not_found", None, body)
        return FeiResult("found", _match(items[0]), body)
