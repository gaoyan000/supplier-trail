"""Pure helpers: dates, names, slugs, identity keys and record hashes."""
import hashlib
import json
import re
import unicodedata
from datetime import date, datetime, timedelta

EARLIEST_PLAUSIBLE = date(1970, 1, 1)
FUTURE_TOLERANCE = timedelta(days=1)  # FDA timestamps vs our timezone
SLUG_MAX = 80

_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y%m%d")


def parse_fda_date(raw: str | None) -> date | None:
    """Parse the date formats FDA sources use; None when missing or invalid."""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def check_date(value: date | None, *, today: date) -> str | None:
    """Return a quarantine reason, or None when the date is usable."""
    if value is None:
        return "missing_date"
    if value > today + FUTURE_TOLERANCE:
        return "future_date"
    if value < EARLIEST_PLAUSIBLE:
        return "implausible_date"
    return None


def _ascii_fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def normalize_name(name: str) -> str:
    """Lower-case, ASCII, '&'→'and', punctuation→space, single spaces."""
    text = _ascii_fold(name).lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def normalize_address(address: str | None) -> str:
    return normalize_name(address or "")


def slugify(text: str) -> str:
    slug = normalize_name(text).replace(" ", "-")[:SLUG_MAX].strip("-")
    return slug or "firm"


def short_hash(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:20]


def identity_key(*, fei: str | None, name: str, address: str | None = None, country: str | None = None) -> str:
    """'fei:<n>' when FDA gave an FEI, else a hash of normalized name + address + country."""
    if fei:
        return f"fei:{fei.strip()}"
    if not normalize_name(name or ""):
        raise ValueError("a firm without FEI needs a name")
    return "name:" + short_hash(normalize_name(name), normalize_address(address), (country or "").strip().lower())


def record_hash(source: str, record: dict) -> str:
    """Stable content hash used to de-duplicate events across runs."""
    payload = json.dumps(record, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(f"{source}|{payload}".encode()).hexdigest()
