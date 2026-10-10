from datetime import date
from pathlib import Path

from supplier_trail_etl.fda.import_alerts import (
    diff_red_list,
    parse_alert_index,
    parse_red_list,
)

FIXTURE = (Path(__file__).parent / "fixtures" / "red_list_99_19_canada.html").read_text()


def entries():
    return parse_red_list(FIXTURE, alert_number="99-19")


def test_parses_every_firm_block_with_country():
    rows = entries()
    assert len(rows) == 6
    assert {r.country for r in rows} == {"CANADA"}


def test_firm_fields():
    first = entries()[0]
    assert first.fda_name == "2129291 Ontario Ltd o/a Live Better Sprouting Innovation"
    assert first.date_published == date(2014, 6, 11)
    assert "Stirling" in first.fda_address and "  " not in first.fda_address


def test_product_codes_and_problems():
    dion = next(r for r in entries() if r.fda_name.startswith("DION HERBS"))
    assert "23K--02" in dion.product_codes
    assert "SALMONELLA" in dion.problems


def test_fei_written_in_fda_notes_is_captured():
    dion = next(r for r in entries() if r.fda_name.startswith("DION HERBS"))
    assert "3003034798" in dion.fei_in_text


def test_entry_keys_unique_and_stable():
    a, b = entries(), entries()
    assert [r.entry_key for r in a] == [r.entry_key for r in b]
    assert len({r.entry_key for r in a}) == len(a)


def test_green_list_section_is_not_red_list():
    html = (
        '<h4>CHINA</h4><div class="div-info"><div class="div-name floatleft">Red Firm</div>'
        '<div class="div-name floatright">Date Published : 01/02/2024</div><div class="clear">1 Road, City CHINA</div></div>'
        '<h4>Green List</h4><div class="div-info"><div class="div-name floatleft">Green Firm</div>'
        '<div class="div-name floatright">Date Published : 01/02/2024</div><div class="clear">2 Road, City CHINA</div></div>'
    )
    assert [r.fda_name for r in parse_red_list(html, alert_number="99-19")] == ["Red Firm"]


def test_duplicate_firm_blocks_are_merged_not_dropped():
    # FDA sometimes lists the same firm (same name + address) twice on one alert page.
    block = (
        '<div class="div-info"><div class="div-name floatleft">Twice Foods</div>'
        '<div class="div-name floatright">Date Published : {d}</div><div class="clear">1 Road, City INDIA</div></div>'
        '<div><em>{code}</em></div><div class="small">Problems: {p};</div>'
    )
    html = "<h4>INDIA</h4>" + block.format(d="05/01/2020", code="28 B - - 08", p="SALMONELLA") \
        + block.format(d="01/01/2015", code="28 B - - 15", p="FILTH")
    rows = parse_red_list(html, alert_number="99-19")
    assert len(rows) == 1
    assert set(rows[0].product_codes) == {"28B--08", "28B--15"}
    assert set(rows[0].problems) == {"SALMONELLA", "FILTH"}
    assert rows[0].date_published == date(2015, 1, 1)


def test_diff_detects_added_and_removed():
    added, removed = diff_red_list(previous={"a", "b"}, current={"b", "c"})
    assert added == {"c"} and removed == {"a"}


def test_diff_first_run_has_no_removals():
    added, removed = diff_red_list(previous=set(), current={"a"})
    assert added == {"a"} and removed == set()


def test_alert_index_parsing():
    html = (
        "<table><tr><th>Number</th></tr>"
        '<tr><td>99-19</td><td>DWPE</td><td>10/06/2026</td><td>"Detention Without Physical Examination of Food"</td>'
        '<td><a href="importalert_263.html">x</a></td></tr>'
        '<tr><td>16-105</td><td>DWPE</td><td>bad</td><td>Fish</td><td><a href="importalert_9.html">x</a></td></tr></table>'
    )
    alerts = parse_alert_index(html)
    assert [a.number for a in alerts] == ["99-19", "16-105"]
    assert alerts[0].last_published == date(2026, 10, 6)
    assert alerts[0].title == "Detention Without Physical Examination of Food"
    assert alerts[1].last_published is None
