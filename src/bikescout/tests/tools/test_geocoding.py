# BikeScout - Tactical Intelligence for Cyclists
# Copyright (C) 2026 hifly81 (https://github.com/hifly81/bikescout)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import logging
from typing import Any, cast

import pytest
import requests

import bikescout.tools.geocoding as geocoding_module
from bikescout.tools.geocoding import (
    NOMINATIM_USER_AGENT,
    GeocodingConfig,
    GeocodingError,
    GeoEngine,
    GeocodingProvider,
    NominatimProvider,
    get_coordinates,
)


class FakeResponse:
    def __init__(self, payload=None, status_exc=None, json_exc=None):
        self._payload = payload
        self._status_exc = status_exc
        self._json_exc = json_exc

    def raise_for_status(self):
        if self._status_exc:
            raise self._status_exc

    def json(self):
        if self._json_exc:
            raise self._json_exc
        return self._payload


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append(
            {
                "url": url,
                "params": params,
                "headers": headers,
                "timeout": timeout,
            }
        )
        if self.exc:
            raise self.exc
        return self.response


class FakeProvider(GeocodingProvider):
    def __init__(self, results=None, exc=None):
        self.results = results if results is not None else []
        self.exc = exc
        self.calls = []

    def geocode(self, query: str, lang: str):
        self.calls.append((query, lang))
        if self.exc:
            raise self.exc
        return self.results


@pytest.fixture
def config():
    return GeocodingConfig(
        request_timeout_seconds=10.0,
        min_interval_seconds=1.1,
        max_results=5,
        default_language="en",
        max_retries=3,
        user_agent=NOMINATIM_USER_AGENT,
    )


def test_nominatim_provider_success(config):
    response = FakeResponse(payload=[{"lat": "45.0", "lon": "10.0"}])
    session = FakeSession(response=response)
    provider = NominatimProvider(config=config, session=cast(Any, session))

    result = provider.geocode("Verona", "it")

    assert result == [{"lat": "45.0", "lon": "10.0"}]
    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["params"]["q"] == "Verona"
    assert call["params"]["limit"] == 5
    assert call["headers"]["Accept-Language"] == "it"
    assert call["headers"]["User-Agent"] == NOMINATIM_USER_AGENT


def test_default_user_agent_includes_contact_url():
    assert "github.com/hifly81/bikescout" in GeocodingConfig().user_agent


def test_nominatim_provider_rejects_empty_query(config):
    provider = NominatimProvider(config=config, session=cast(Any, FakeSession()))

    with pytest.raises(GeocodingError):
        provider.geocode("", "en")


def test_nominatim_provider_wraps_request_exception(config):
    session = FakeSession(exc=requests.RequestException("network down"))
    provider = NominatimProvider(config=config, session=cast(Any, session))

    with pytest.raises(GeocodingError, match="Geocoding request failed"):
        provider.geocode("Verona", "en")


def test_nominatim_provider_wraps_http_error(config):
    response = FakeResponse(status_exc=requests.HTTPError("500 error"))
    session = FakeSession(response=response)
    provider = NominatimProvider(config=config, session=cast(Any, session))

    with pytest.raises(GeocodingError, match="Geocoding request failed"):
        provider.geocode("Verona", "en")


def test_nominatim_provider_wraps_invalid_json(config):
    response = FakeResponse(json_exc=ValueError("bad json"))
    session = FakeSession(response=response)
    provider = NominatimProvider(config=config, session=cast(Any, session))

    with pytest.raises(GeocodingError, match="invalid JSON"):
        provider.geocode("Verona", "en")


def test_nominatim_provider_rejects_non_list_payload(config):
    response = FakeResponse(payload={"lat": "45.0", "lon": "10.0"})
    session = FakeSession(response=response)
    provider = NominatimProvider(config=config, session=cast(Any, session))

    with pytest.raises(GeocodingError, match="unexpected payload format"):
        provider.geocode("Verona", "en")


def test_nominatim_provider_filters_non_dict_items(config):
    response = FakeResponse(payload=[{"lat": "45.0", "lon": "10.0"}, "bad-item", 123])
    session = FakeSession(response=response)
    provider = NominatimProvider(config=config, session=cast(Any, session))

    result = provider.geocode("Verona", "en")

    assert result == [{"lat": "45.0", "lon": "10.0"}]


def test_wait_for_slot_sleeps_when_called_too_soon(config):
    slept = []

    class FakeClock:
        def __init__(self):
            self.now = 100.0

        def time(self):
            return self.now

        def sleep(self, seconds):
            slept.append(seconds)
            self.now += seconds

    clock = FakeClock()
    engine = GeoEngine(
        provider=FakeProvider(results=[]),
        config=config,
        sleep_func=clock.sleep,
        time_func=clock.time,
    )

    engine.last_request_time = 99.5
    engine._wait_for_slot()

    assert slept == [pytest.approx(0.6)]
    assert engine.last_request_time == pytest.approx(100.6)


def test_wait_for_slot_does_not_sleep_when_slot_available(config):
    slept = []

    class FakeClock:
        def __init__(self):
            self.now = 100.0

        def time(self):
            return self.now

        def sleep(self, seconds):
            slept.append(seconds)

    clock = FakeClock()
    engine = GeoEngine(
        provider=FakeProvider(results=[]),
        config=config,
        sleep_func=clock.sleep,
        time_func=clock.time,
    )

    engine.last_request_time = 90.0
    engine._wait_for_slot()

    assert slept == []
    assert engine.last_request_time == 100.0


def test_rank_results_returns_none_for_empty_results(config):
    engine = GeoEngine(provider=FakeProvider(results=[]), config=config)

    assert engine._rank_results([]) is None


def test_rank_results_prefers_trail_over_shop(config):
    engine = GeoEngine(provider=FakeProvider(results=[]), config=config)

    results = [
        {"importance": 0.8, "class": "shop", "type": "bicycle", "display_name": "Bike Shop"},
        {"importance": 0.5, "class": "leisure", "type": "trail", "display_name": "Trail"},
    ]

    best = engine._rank_results(results)

    assert cast(dict[str, Any], best)["display_name"] == "Trail"


def test_rank_results_handles_invalid_importance(config):
    engine = GeoEngine(provider=FakeProvider(results=[]), config=config)

    results = [
        {"importance": "not-a-number", "class": "place", "type": "town", "display_name": "Town"},
        {"importance": 0.1, "class": "shop", "type": "mall", "display_name": "Shop"},
    ]

    best = engine._rank_results(results)

    assert cast(dict[str, Any], best)["display_name"] == "Town"


def test_build_success_result_success(config):
    engine = GeoEngine(provider=FakeProvider(results=[]), config=config)

    result = engine._build_success_result(
        {
            "lat": "45.4384",
            "lon": "10.9916",
            "display_name": "Verona, Veneto, Italia",
            "class": "place",
            "type": "city",
            "importance": 0.8,
        }
    )

    assert result["status"] == "Success"
    assert result["lat"] == 45.4384
    assert result["lon"] == 10.9916
    assert result["display_name"] == "Verona, Veneto, Italia"


def test_build_success_result_raises_for_invalid_lat_lon(config):
    engine = GeoEngine(provider=FakeProvider(results=[]), config=config)

    with pytest.raises(GeocodingError, match="invalid latitude"):
        engine._build_success_result({"lat": "bad", "lon": "10.0"})


def test_get_coordinates_success(config):
    provider = FakeProvider(
        results=[
            {
                "lat": "45.4384",
                "lon": "10.9916",
                "display_name": "Verona",
                "class": "place",
                "type": "city",
                "importance": 0.7,
            }
        ]
    )
    slept = []

    engine = GeoEngine(
        provider=provider,
        config=config,
        sleep_func=lambda x: slept.append(x),
        time_func=lambda: 100.0,
    )

    result = engine.get_coordinates("Verona", lang="it", retries=3)

    assert result["status"] == "Success"
    assert result["lat"] == 45.4384
    assert result["lon"] == 10.9916
    assert provider.calls == [("Verona", "it")]
    assert slept == []


def test_get_coordinates_uses_default_language_and_retries(config):
    provider = FakeProvider(
        results=[
            {
                "lat": "45.0",
                "lon": "10.0",
                "display_name": "X",
                "class": "place",
                "type": "town",
                "importance": 0.5,
            }
        ]
    )

    engine = GeoEngine(
        provider=provider, config=config, sleep_func=lambda _: None, time_func=lambda: 100.0
    )
    result = engine.get_coordinates("X", lang=None, retries=None)

    assert result["status"] == "Success"
    assert provider.calls == [("X", "en")]


def test_get_coordinates_rejects_empty_location(config):
    engine = GeoEngine(provider=FakeProvider(results=[]), config=config)

    result = engine.get_coordinates("", lang="en", retries=3)

    assert result == {"status": "Error", "message": "Location name must not be empty."}


def test_get_coordinates_rejects_non_positive_retries(config):
    engine = GeoEngine(provider=FakeProvider(results=[]), config=config)

    result = engine.get_coordinates("Verona", retries=0)

    assert result == {"status": "Error", "message": "Retries must be a positive integer."}


def test_get_coordinates_returns_not_found_when_no_results(config):
    engine = GeoEngine(
        provider=FakeProvider(results=[]),
        config=config,
        sleep_func=lambda _: None,
        time_func=lambda: 100.0,
    )

    result = engine.get_coordinates("Nowhere")

    assert result["status"] == "Error"
    assert "not found" in result["message"]


def test_get_coordinates_retries_and_then_returns_max_retries(config):
    provider = FakeProvider(exc=GeocodingError("temporary failure"))
    sleeps = []

    engine = GeoEngine(
        provider=provider,
        config=config,
        sleep_func=lambda seconds: sleeps.append(seconds),
        time_func=lambda: 100.0,
    )

    result = engine.get_coordinates("Verona", retries=3)

    assert result["status"] == "Error"
    assert "temporary failure" in result["message"]
    assert "after 3 attempt(s)" in result["message"]
    assert provider.calls == [("Verona", "en"), ("Verona", "en"), ("Verona", "en")]
    assert sleeps == [1, 1.1, 2, 1.1]


def test_get_coordinates_retries_on_unexpected_exception_and_returns_error(config):
    class BadProvider(GeocodingProvider):
        def geocode(self, query: str, lang: str):
            raise RuntimeError("boom")

    sleeps = []

    engine = GeoEngine(
        provider=BadProvider(),
        config=config,
        sleep_func=lambda seconds: sleeps.append(seconds),
        time_func=lambda: 100.0,
    )

    result = engine.get_coordinates("Verona", retries=2)

    assert result["status"] == "Error"
    assert result["message"] == "Unexpected geocoding failure after 2 attempt(s): boom"
    assert sleeps == [1, 1.1]


def test_get_coordinates_rejects_invalid_coordinates_without_retrying(config):
    provider = FakeProvider(
        results=[
            {
                "lat": "bad",
                "lon": "10.0",
                "display_name": "Broken",
                "class": "place",
                "type": "town",
                "importance": 0.5,
            }
        ]
    )
    sleeps = []

    engine = GeoEngine(
        provider=provider,
        config=config,
        sleep_func=lambda seconds: sleeps.append(seconds),
        time_func=lambda: 100.0,
    )

    result = engine.get_coordinates("Broken", retries=2)

    assert result["status"] == "Error"
    assert "invalid latitude" in result["message"]
    assert provider.calls == [("Broken", "en")]
    assert sleeps == []


class FakeClock:
    def __init__(self, now: float = 100.0):
        self.now = now

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def _valid_result(display_name: str = "Verona") -> dict[str, Any]:
    return {
        "lat": "45.4384",
        "lon": "10.9916",
        "display_name": display_name,
        "class": "place",
        "type": "city",
        "importance": 0.7,
    }


def test_get_coordinates_reuses_cached_result(config):
    provider = FakeProvider(results=[_valid_result()])
    clock = FakeClock()
    engine = GeoEngine(
        provider=provider, config=config, sleep_func=clock.sleep, time_func=clock.time
    )

    first = engine.get_coordinates("Verona", lang="it")
    second = engine.get_coordinates("Verona", lang="it")

    assert first == second
    assert provider.calls == [("Verona", "it")]


def test_cache_key_ignores_case_and_surrounding_whitespace(config):
    provider = FakeProvider(results=[_valid_result()])
    engine = GeoEngine(
        provider=provider,
        config=config,
        sleep_func=lambda _: None,
        time_func=lambda: 100.0,
    )

    engine.get_coordinates("Verona", lang="it")
    engine.get_coordinates("  verona  ", lang="IT")

    assert provider.calls == [("Verona", "it")]


def test_cache_expires_after_ttl(config):
    provider = FakeProvider(results=[_valid_result()])
    clock = FakeClock()
    short_ttl = GeocodingConfig(cache_ttl_seconds=10.0)
    engine = GeoEngine(
        provider=provider, config=short_ttl, sleep_func=clock.sleep, time_func=clock.time
    )

    engine.get_coordinates("Verona")
    clock.now += 11.0
    engine.get_coordinates("Verona")

    assert len(provider.calls) == 2


def test_cache_evicts_oldest_entry_when_full(config):
    provider = FakeProvider(results=[_valid_result()])
    small_cache = GeocodingConfig(cache_max_entries=1)
    engine = GeoEngine(
        provider=provider,
        config=small_cache,
        sleep_func=lambda _: None,
        time_func=lambda: 100.0,
    )

    engine.get_coordinates("Verona")
    engine.get_coordinates("Rome")
    engine.get_coordinates("Verona")

    assert len(engine._cache) == 1
    assert len(provider.calls) == 3


def test_error_responses_are_not_cached(config):
    class FlakyProvider(GeocodingProvider):
        def __init__(self):
            self.calls = 0

        def geocode(self, query: str, lang: str):
            self.calls += 1
            if self.calls == 1:
                raise GeocodingError("temporary outage")
            return [_valid_result()]

    provider = FlakyProvider()
    engine = GeoEngine(
        provider=provider,
        config=config,
        sleep_func=lambda _: None,
        time_func=lambda: 100.0,
    )

    first = engine.get_coordinates("Verona", retries=1)
    second = engine.get_coordinates("Verona", retries=1)

    assert first["status"] == "Error"
    assert second["status"] == "Success"
    assert provider.calls == 2


def test_get_coordinates_exposes_diagnostic_alternatives(config, caplog):
    results = [
        _valid_result("Verona"),
        {
            "lat": "45.1",
            "lon": "10.1",
            "display_name": "Verona Alta",
            "class": "place",
            "type": "town",
            "importance": 0.68,
        },
        {
            "lat": "bad",
            "lon": "10.1",
            "display_name": "Broken",
            "class": "place",
            "type": "town",
            "importance": 0.6,
        },
    ]
    provider = FakeProvider(results=results)
    engine = GeoEngine(
        provider=provider,
        config=config,
        sleep_func=lambda _: None,
        time_func=lambda: 100.0,
    )

    with caplog.at_level(logging.WARNING, logger="bikescout.tools.geocoding"):
        result = engine.get_coordinates("Verona")

    assert result["status"] == "Success"
    assert result["lat"] == 45.4384
    assert [alt["display_name"] for alt in result["alternatives"]] == ["Verona Alta"]
    assert "Ambiguous geocoding result" in caplog.text


@pytest.mark.parametrize(
    ("lat", "lon", "expected"),
    [
        ("91", "10", "latitude"),
        ("45", "-181", "longitude"),
        ("nan", "10", "latitude"),
        ("45", "inf", "longitude"),
        (True, "10", "latitude"),
    ],
)
def test_get_coordinates_rejects_out_of_range_coordinates(config, lat, lon, expected):
    provider = FakeProvider(
        results=[
            {
                "lat": lat,
                "lon": lon,
                "display_name": "Broken",
                "class": "place",
                "type": "town",
                "importance": 0.5,
            }
        ]
    )
    slept = []
    engine = GeoEngine(
        provider=provider,
        config=config,
        sleep_func=lambda seconds: slept.append(seconds),
        time_func=lambda: 100.0,
    )

    result = engine.get_coordinates("Broken", retries=2)

    assert result["status"] == "Error"
    assert expected in result["message"]
    assert len(provider.calls) == 1
    assert slept == []


def test_build_success_result_normalizes_optional_fields(config):
    engine = GeoEngine(provider=FakeProvider(results=[]), config=config)

    result = engine._build_success_result({"lat": "45.0", "lon": "10.0", "importance": "bad"})

    assert result["importance"] == 0.0
    assert result["display_name"] == ""
    assert result["class"] == ""
    assert result["type"] == ""


def test_module_level_wrapper(monkeypatch):
    class FakeEngine:
        def __init__(self):
            self.calls = []

        def get_coordinates(self, location_name, lang="en"):
            self.calls.append((location_name, lang))
            return {"status": "Success", "lat": 1.0, "lon": 2.0}

    fake_engine = FakeEngine()
    monkeypatch.setattr(geocoding_module, "engine", fake_engine)

    result = get_coordinates("Verona", "it")

    assert result == {"status": "Success", "lat": 1.0, "lon": 2.0}
    assert fake_engine.calls == [("Verona", "it")]
