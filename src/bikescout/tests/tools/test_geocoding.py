import pytest
import requests

import bikescout.tools.geocoding as geocoding_module
from bikescout.tools.geocoding import (
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
        user_agent="BikeScout_Tactical_Engine/2.0",
    )


def test_nominatim_provider_success(config):
    response = FakeResponse(payload=[{"lat": "45.0", "lon": "10.0"}])
    session = FakeSession(response=response)
    provider = NominatimProvider(config=config, session=session)

    result = provider.geocode("Verona", "it")

    assert result == [{"lat": "45.0", "lon": "10.0"}]
    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["params"]["q"] == "Verona"
    assert call["params"]["limit"] == 5
    assert call["headers"]["Accept-Language"] == "it"
    assert call["headers"]["User-Agent"] == "BikeScout_Tactical_Engine/2.0"


def test_nominatim_provider_rejects_empty_query(config):
    provider = NominatimProvider(config=config, session=FakeSession())

    with pytest.raises(GeocodingError):
        provider.geocode("", "en")


def test_nominatim_provider_wraps_request_exception(config):
    session = FakeSession(exc=requests.RequestException("network down"))
    provider = NominatimProvider(config=config, session=session)

    with pytest.raises(GeocodingError, match="Geocoding request failed"):
        provider.geocode("Verona", "en")


def test_nominatim_provider_wraps_http_error(config):
    response = FakeResponse(status_exc=requests.HTTPError("500 error"))
    session = FakeSession(response=response)
    provider = NominatimProvider(config=config, session=session)

    with pytest.raises(GeocodingError, match="Geocoding request failed"):
        provider.geocode("Verona", "en")


def test_nominatim_provider_wraps_invalid_json(config):
    response = FakeResponse(json_exc=ValueError("bad json"))
    session = FakeSession(response=response)
    provider = NominatimProvider(config=config, session=session)

    with pytest.raises(GeocodingError, match="invalid JSON"):
        provider.geocode("Verona", "en")


def test_nominatim_provider_rejects_non_list_payload(config):
    response = FakeResponse(payload={"lat": "45.0", "lon": "10.0"})
    session = FakeSession(response=response)
    provider = NominatimProvider(config=config, session=session)

    with pytest.raises(GeocodingError, match="unexpected payload format"):
        provider.geocode("Verona", "en")


def test_nominatim_provider_filters_non_dict_items(config):
    response = FakeResponse(payload=[{"lat": "45.0", "lon": "10.0"}, "bad-item", 123])
    session = FakeSession(response=response)
    provider = NominatimProvider(config=config, session=session)

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

    assert best["display_name"] == "Trail"


def test_rank_results_handles_invalid_importance(config):
    engine = GeoEngine(provider=FakeProvider(results=[]), config=config)

    results = [
        {"importance": "not-a-number", "class": "place", "type": "town", "display_name": "Town"},
        {"importance": 0.1, "class": "shop", "type": "mall", "display_name": "Shop"},
    ]

    best = engine._rank_results(results)

    assert best["display_name"] == "Town"


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

    with pytest.raises(GeocodingError, match="missing valid lat/lon"):
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

    engine = GeoEngine(provider=provider, config=config, sleep_func=lambda _: None, time_func=lambda: 100.0)
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

    assert result == {"status": "Error", "message": "Max retries exceeded for geocoding service."}
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
    assert result["message"] == "Unexpected geocoding failure: boom"
    assert sleeps == [1, 1.1]


def test_get_coordinates_returns_max_retries_when_best_match_has_invalid_lat_lon(config):
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

    assert result == {"status": "Error", "message": "Max retries exceeded for geocoding service."}
    assert len(sleeps) == 2
    assert 1 in sleeps
    assert 1.1 in sleeps

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