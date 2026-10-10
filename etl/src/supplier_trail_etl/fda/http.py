"""Polite HTTP: one shared session, fixed pacing, retries with backoff, raw-response archiving."""
import gzip
import json
import logging
import time
from datetime import date
from pathlib import Path

import requests

log = logging.getLogger(__name__)
USER_AGENT = "SupplierTrail data pipeline (contact: hello@suppliertrail.com)"
RETRY_STATUSES = {429, 500, 502, 503, 504}


class FdaHttp:
    def __init__(self, *, interval_s: float, raw_dir: Path | None = None, max_retries: int = 4):
        self._session = requests.Session()
        self._session.headers["User-Agent"] = USER_AGENT
        self._interval = interval_s
        self._last = 0.0
        self._raw_dir = raw_dir
        self._max_retries = max_retries

    def _pace(self) -> None:
        wait = self._interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        for attempt in range(self._max_retries + 1):
            self._pace()
            try:
                resp = self._session.request(method, url, timeout=120, **kwargs)
            except (requests.ConnectionError, requests.Timeout) as exc:
                if attempt == self._max_retries:
                    raise
                log.warning("network error on %s (%s); retrying", url, type(exc).__name__)
            else:
                if resp.status_code not in RETRY_STATUSES or attempt == self._max_retries:
                    resp.raise_for_status()
                    return resp
                log.warning("HTTP %s on %s; retrying", resp.status_code, url)
            time.sleep(2 ** attempt)
        raise RuntimeError("unreachable")

    def archive(self, source: str, name: str, payload) -> Path | None:
        """Keep the raw response (design §5: evidence of what FDA published, and debugging)."""
        if self._raw_dir is None:
            return None
        folder = self._raw_dir / source / date.today().isoformat()
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{name}.json.gz"
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        return path
