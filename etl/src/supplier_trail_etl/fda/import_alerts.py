"""Import-alert pages: index + red-list parsing (HTML scrape) and set diff for listed/removed events."""
import re
from dataclasses import dataclass, replace

from bs4 import BeautifulSoup

from ..normalize import short_hash, normalize_address, normalize_name, parse_fda_date, slugify

LIST_URL = "https://www.accessdata.fda.gov/cms_ia/ialist.html"
PAGE_URL = "https://www.accessdata.fda.gov/cms_ia/{page}"

_TOKEN = re.compile(r'<h[1-6][^>]*>(?P<heading>.*?)</h[1-6]>|class="div-info"', re.S | re.I)
_PRODUCT_CODE = re.compile(r"<em>(.*?)</em>", re.S)
_PROBLEMS = re.compile(r"Problems:\s*([^<]+)", re.S)
_FEI = re.compile(r"FEI\s*(?:#|No\.?|number)?\s*:?\s*(\d{7,10})", re.I)
_NON_RED_HEADINGS = ("green list", "yellow list")


@dataclass(frozen=True)
class AlertIndexRow:
    number: str
    alert_type: str
    last_published: object
    title: str
    page: str


@dataclass(frozen=True)
class RedListEntry:
    alert_number: str
    entry_key: str
    fda_name: str
    fda_address: str
    country: str | None
    date_published: object
    product_codes: tuple[str, ...]
    problems: tuple[str, ...]
    fei_in_text: tuple[str, ...]
    slug: str


def parse_alert_index(html: str) -> list[AlertIndexRow]:
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for tr in soup.select("table tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        link = tr.find("a", href=True)
        if len(cells) >= 4 and link and re.fullmatch(r"\d{2}-\d{2,3}", cells[0]):
            rows.append(AlertIndexRow(cells[0], cells[1], parse_fda_date(cells[2]), cells[3].strip('"'), link["href"]))
    return rows


def _text(fragment: str) -> str:
    return " ".join(BeautifulSoup(fragment, "lxml").get_text(" ").split())


def _parse_block(block: str, *, alert_number: str, country: str | None) -> RedListEntry | None:
    soup = BeautifulSoup(block, "lxml")
    names = soup.select("div.div-name")
    if not names:
        return None
    name = " ".join(names[0].get_text(" ").split())
    published = names[1].get_text(" ", strip=True).split(":", 1)[-1] if len(names) > 1 else ""
    addr_div = soup.select_one("div.clear")
    address = " ".join(addr_div.get_text(" ").split()).replace(" ,", ",") if addr_div else ""
    codes = tuple(dict.fromkeys(_text(c).replace(" ", "") for c in _PRODUCT_CODE.findall(block)))
    problems = tuple(dict.fromkeys(
        p.strip() for raw in _PROBLEMS.findall(block) for p in raw.split(";") if p.strip()
    ))
    feis = tuple(dict.fromkeys(_FEI.findall(_text(block))))
    key = short_hash(alert_number, normalize_name(name), normalize_address(address))
    return RedListEntry(
        alert_number=alert_number, entry_key=key, fda_name=name, fda_address=address, country=country,
        date_published=parse_fda_date(published), product_codes=codes, problems=problems, fei_in_text=feis,
        slug=slugify(name),
    )


def parse_red_list(html: str, *, alert_number: str) -> list[RedListEntry]:
    """Firm blocks under country headings; blocks under green/yellow-list headings are skipped."""
    tokens = list(_TOKEN.finditer(html))
    entries, country, in_red = [], None, True
    for i, tok in enumerate(tokens):
        if tok.group("heading") is not None:
            heading = _text(tok.group("heading"))
            lowered = heading.lower()
            if any(h in lowered for h in _NON_RED_HEADINGS):
                in_red = False
            elif heading.isupper():
                country, in_red = heading, True
            continue
        if not in_red:
            continue
        start = html.rfind("<div", 0, tok.start())
        end = tokens[i + 1].start() if i + 1 < len(tokens) else len(html)
        entry = _parse_block(html[start:end], alert_number=alert_number, country=country)
        if entry:
            entries.append(entry)
    return _merge_duplicates(entries)


def _union(*groups: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(x for g in groups for x in g))


def _merge_duplicates(entries: list[RedListEntry]) -> list[RedListEntry]:
    """FDA sometimes lists one firm twice on a page; keep one entry with the union of its products."""
    merged: dict[str, RedListEntry] = {}
    for e in entries:
        prev = merged.get(e.entry_key)
        if prev is None:
            merged[e.entry_key] = e
            continue
        dates = [d for d in (prev.date_published, e.date_published) if d]
        merged[e.entry_key] = replace(
            prev,
            date_published=min(dates) if dates else None,
            product_codes=_union(prev.product_codes, e.product_codes),
            problems=_union(prev.problems, e.problems),
            fei_in_text=_union(prev.fei_in_text, e.fei_in_text),
        )
    return list(merged.values())


def diff_red_list(*, previous: set[str], current: set[str]) -> tuple[set[str], set[str]]:
    """Return (added, removed) entry keys between two snapshots."""
    return current - previous, previous - current
