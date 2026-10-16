import pytest
import requests

from supplier_trail_etl.fda.apis import FdaApiError
from supplier_trail_etl.fda.fei_api import FdaBlockedError, FeiApiClient, build_fei_payload


class TestBuildPayload:
    def test_foreign_address_splits_street_city_province(self):
        assert build_fei_payload("DELMAR COMMODITIES LTD", "2-265 Perry St, Winkler, Manitoba CANADA", "CANADA", "CA") == {
            "firmname": "DELMAR COMMODITIES LTD", "firmaddress1": "2-265 Perry St", "firmaddress2": "",
            "firmcity": "Winkler", "firmstate": "", "firmprovince": "Manitoba", "firmcountry": "CA", "firmzip": "",
        }

    def test_long_street_keeps_all_leading_parts(self):
        p = build_fei_payload("X", "No. 9 Buwen Road Anhui, China, Anqing, Anhui CHINA", "CHINA", "CN")
        assert (p["firmaddress1"], p["firmcity"], p["firmprovince"]) == ("No. 9 Buwen Road Anhui, China", "Anqing", "Anhui")

    def test_us_address_takes_state_and_zip(self):
        p = build_fei_payload("X", "2550 E 25th St, Vernon, CA 90058-1211 UNITED STATES", "UNITED STATES", "US")
        assert (p["firmaddress1"], p["firmcity"], p["firmstate"], p["firmzip"], p["firmprovince"]) == (
            "2550 E 25th St", "Vernon", "CA", "90058-1211", "")

    def test_two_part_address(self):
        p = build_fei_payload("X", "Rui'An Lin Yang Health, Wenzhou, CHINA", "CHINA", "CN")
        assert (p["firmaddress1"], p["firmcity"], p["firmprovince"]) == ("Rui'An Lin Yang Health", "Wenzhou", "")

    @pytest.mark.parametrize("address,country,code", [
        (None, "CHINA", "CN"),
        ("", "CHINA", "CN"),
        ("Somewhere, CHINA", "CHINA", "CN"),          # no city
        ("1 Main St, Springfield UNITED STATES", "UNITED STATES", "US"),  # no state
        ("1 Main St, Winkler, Manitoba CANADA", "CANADA", None),          # unknown country code
    ])
    def test_unusable_addresses_return_none(self, address, country, code):
        assert build_fei_payload("X", address, country, code) is None


class FakeResponse:
    def __init__(self, body=None, *, url="https://www.accessdata.fda.gov/rest/feiapi/firmdata/feidata", history=(),
                 text=None):
        self._body, self.url, self.history = body, url, list(history)
        self.text = text if text is not None else str(body)

    def json(self):
        if self._body is None:
            raise ValueError("not json")
        return self._body


class FakeHttp:
    def __init__(self, response):
        self.response, self.calls = response, []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.response


FOUND = {"MESSAGE": "Success", "STATUSCODE": 400, "RESULT": {
    "FEINUMBER": "3000000001", "LEGALNAME": "DELMAR COMMODITIES LTD", "MERGEDFIRMINDICATOR": False,
    "physicaladdress": {"FIRMADDRESS1": "2-265 Perry St", "FIRMADDRESS2": None, "FIRMCITY": "Winkler",
                        "FIRMSTATE": None, "FIRMPROVINCE": "Manitoba", "FIRMCOUNTRY": "CA", "FIRMZIP": "R6W 4A9"}}}
PAYLOAD = {"firmname": "DELMAR COMMODITIES LTD", "firmcountry": "CA"}


def client(response):
    http = FakeHttp(response)
    return FeiApiClient(http, user="user@example.com", key="k"), http


class TestFeiApiClient:
    def test_found_returns_the_match_and_sends_auth_and_a_unique_signature(self):
        c, http = client(FakeResponse(FOUND))
        result = c.find(PAYLOAD)
        assert result.status == "found"
        assert result.match.fei == "3000000001"
        assert result.match.legal_name == "DELMAR COMMODITIES LTD"
        assert (result.match.city, result.match.country_code, result.match.merged) == ("Winkler", "CA", False)
        assert result.match.address == "2-265 Perry St"
        method, url, kwargs = http.calls[0]
        assert method == "POST" and "feiapi/firmdata/feidata" in url and "signature=" in url
        assert kwargs["headers"]["Authorization-User"] == "user@example.com"
        assert '"firmname": "DELMAR COMMODITIES LTD"' in kwargs["data"]["payLoad"]
        c.find(PAYLOAD)
        assert http.calls[0][1] != http.calls[1][1]

    def test_single_item_list_counts_as_found(self):
        body = {**FOUND, "RESULT": [FOUND["RESULT"]]}
        assert client(FakeResponse(body))[0].find(PAYLOAD).status == "found"

    def test_several_firms_are_ambiguous_and_never_linked(self):
        other = {**FOUND["RESULT"], "FEINUMBER": "3000000002"}
        result = client(FakeResponse({**FOUND, "RESULT": [FOUND["RESULT"], other]}))[0].find(PAYLOAD)
        assert result.status == "ambiguous" and result.match is None

    def test_no_results(self):
        result = client(FakeResponse({"MESSAGE": "No results found", "STATUSCODE": 412}))[0].find(PAYLOAD)
        assert result.status == "not_found" and result.match is None

    @pytest.mark.parametrize("code", [403, 405, 406, 420, 435])
    def test_input_errors_are_recorded_for_that_entry_only(self, code):
        result = client(FakeResponse({"MESSAGE": "bad", "STATUSCODE": code}))[0].find(PAYLOAD)
        assert result.status == "invalid_input"

    @pytest.mark.parametrize("code", [401, 413, 430])
    def test_auth_outage_and_quota_stop_the_run(self, code):
        with pytest.raises(FdaBlockedError):
            client(FakeResponse({"MESSAGE": "x", "STATUSCODE": code}))[0].find(PAYLOAD)

    def test_redirect_to_fda_block_page_stops_the_run(self):
        page = FakeResponse(None, url="https://www.accessdata.fda.gov/apology_objects/abuse-detection-apology.html",
                            history=[object()], text="<html>FDA Apology</html>")
        with pytest.raises(FdaBlockedError):
            client(page)[0].find(PAYLOAD)

    def test_http_403_from_fda_stops_the_run(self):
        class Refusing:
            def request(self, *a, **k):
                resp = requests.Response()
                resp.status_code = 403
                raise requests.HTTPError(response=resp)
        with pytest.raises(FdaBlockedError):
            FeiApiClient(Refusing(), user="u", key="k").find(PAYLOAD)

    def test_empty_body_stops_the_run(self):
        # Seen during FDA's 2026-10-15 outage: HTTP 200 with "{}".
        with pytest.raises(FdaBlockedError):
            client(FakeResponse({}))[0].find(PAYLOAD)

    def test_unknown_status_is_an_error(self):
        with pytest.raises(FdaApiError):
            client(FakeResponse({"MESSAGE": "?", "STATUSCODE": 999}))[0].find(PAYLOAD)
