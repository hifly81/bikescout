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

from typing import Any, cast

import pytest
import requests

import bikescout.tools.poi as poi_module
from bikescout.tools.poi import (
    PoiScoutConfig,
    PoiScoutError,
    PoiScoutService,
    get_poi_scout,
    haversine_distance,
)


class FakeResponse:
    def __init__(self, ok=True, status_code=200, text="", payload=None, json_exc=None):
        self.ok = ok
        self.status_code = status_code
        self.text = text
        self._payload = payload
        self._json_exc = json_exc

    def json(self):
        if self._json_exc:
            raise self._json_exc
        return self._payload


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        if self.exc:
            raise self.exc
        return self.response


@pytest.fixture
def config():
    return PoiScoutConfig(
        request_timeout_seconds=10.0,
        min_buffer_m=1,
        max_buffer_m=2000,
        result_limit=20,
        target_categories=(162, 372, 371, 331, 332),
    )


@pytest.fixture
def service(config):
    return PoiScoutService(config=config, session=cast(Any, FakeSession()))


def test_validate_inputs_accepts_valid_values(service):
    service._validate_inputs("key", 45.0, 10.0, 12.5)


def test_validate_inputs_rejects_empty_api_key(service):
    with pytest.raises(PoiScoutError, match="API key must not be empty"):
        service._validate_inputs("", 45.0, 10.0, 1.0)


def test_validate_inputs_rejects_non_numeric_values(service):
    with pytest.raises(PoiScoutError, match="must be numeric"):
        service._validate_inputs("key", "bad", 10.0, 1.0)


def test_validate_inputs_rejects_invalid_latitude(service):
    with pytest.raises(PoiScoutError, match="Latitude must be between -90 and 90"):
        service._validate_inputs("key", 100.0, 10.0, 1.0)


def test_validate_inputs_rejects_invalid_longitude(service):
    with pytest.raises(PoiScoutError, match="Longitude must be between -180 and 180"):
        service._validate_inputs("key", 45.0, 200.0, 1.0)


def test_validate_inputs_rejects_negative_total_length(service):
    with pytest.raises(PoiScoutError, match="total_length_km must be non-negative"):
        service._validate_inputs("key", 45.0, 10.0, -1.0)


def test_compute_safe_buffer_clamps_to_min(service):
    assert service._compute_safe_buffer_m(0.0) == 500


def test_compute_safe_buffer_scales_normally(service):
    assert service._compute_safe_buffer_m(15.0) == 1500


def test_compute_safe_buffer_clamps_to_max(service):
    assert service._compute_safe_buffer_m(99.0) == 2000


def test_build_headers(service):
    headers = service._build_headers("abc123")
    assert headers["Authorization"] == "abc123"
    assert "application/json" in headers["Content-Type"]
    assert "application/geo+json" in headers["Accept"]


def test_build_request_body(service):
    body = service._build_request_body(45.0, 10.0, 500)

    assert body["request"] == "pois"
    assert body["geometry"]["geojson"]["coordinates"] == [10.0, 45.0]
    assert body["geometry"]["buffer"] == 500
    assert body["filters"]["category_ids"] == [162, 372, 371, 331, 332]
    assert body["limit"] == 20
    assert body["sortby"] == "distance"


def test_label_from_category_ids_dict_water(service):
    assert service._label_from_category_ids({"162": True}) == "Water Fountain"


def test_label_from_category_ids_list_bike_support(service):
    assert service._label_from_category_ids([371]) == "Bike Support"


def test_label_from_category_ids_rest_area(service):
    assert service._label_from_category_ids({"331": True}) == "Rest Area"


def test_label_from_category_ids_unknown(service):
    assert service._label_from_category_ids({"999": True}) == "Point of Interest"


def test_label_from_category_ids_invalid_type(service):
    assert service._label_from_category_ids("bad") == "Point of Interest"


def test_extract_amenities_success(service):
    data = {
        "features": [
            {
                "properties": {
                    "distance": 123.4,
                    "category_ids": {"162": True},
                    "osm_tags": {"name": "Fresh Water"},
                },
                "geometry": {"coordinates": [10.1, 45.1]},
            },
            {
                "properties": {
                    "distance": 50,
                    "category_ids": {"371": True},
                    "osm_tags": {"operator": "Bike Fix"},
                },
                "geometry": {"coordinates": [10.2, 45.2]},
            },
        ]
    }

    amenities = service._extract_amenities(data)

    assert len(amenities) == 2
    assert amenities[0]["name"] == "Fresh Water"
    assert amenities[0]["type"] == "Water Fountain"
    assert amenities[0]["distance_m"] == 123
    assert amenities[0]["location"] == {"lat": 45.1, "lon": 10.1}
    assert amenities[1]["name"] == "Bike Fix"
    assert amenities[1]["type"] == "Bike Support"


def test_extract_amenities_fallback_name_uses_amenity_then_label(service):
    data = {
        "features": [
            {
                "properties": {
                    "distance": "42",
                    "category_ids": {"331": True},
                    "osm_tags": {"amenity": "bench"},
                },
                "geometry": {"coordinates": [10.3, 45.3]},
            },
            {
                "properties": {
                    "distance": None,
                    "category_ids": {"999": True},
                    "osm_tags": {},
                },
                "geometry": {"coordinates": [10.4, 45.4]},
            },
        ]
    }

    amenities = service._extract_amenities(data)

    assert amenities[0]["name"] == "bench"
    assert amenities[0]["type"] == "Rest Area"
    assert amenities[1]["name"] == "Point of Interest"
    assert amenities[1]["distance_m"] == 0


def test_extract_amenities_rejects_non_dict_payload(service):
    with pytest.raises(PoiScoutError, match="unexpected payload format"):
        service._extract_amenities(["bad"])


def test_extract_amenities_rejects_non_list_features(service):
    with pytest.raises(PoiScoutError, match="invalid features payload"):
        service._extract_amenities({"features": "bad"})


def test_extract_amenities_skips_bad_features(service):
    data = {
        "features": [
            "bad",
            {"properties": "bad", "geometry": {}},
            {"properties": {}, "geometry": "bad"},
            {"properties": {}, "geometry": {"coordinates": [10.0]}},
            {"properties": {}, "geometry": {"coordinates": ["bad", 45.0]}},
            {
                "properties": {"category_ids": {"162": True}, "osm_tags": {}},
                "geometry": {"coordinates": [10.0, 45.0]},
            },
        ]
    }

    amenities = service._extract_amenities(data)

    assert len(amenities) == 1
    assert amenities[0]["type"] == "Water Fountain"


def test_get_poi_scout_success(config):
    payload = {
        "features": [
            {
                "properties": {
                    "distance": 200,
                    "category_ids": {"331": True},
                    "osm_tags": {"name": "Picnic Spot"},
                },
                "geometry": {"coordinates": [10.0, 45.0]},
            },
            {
                "properties": {
                    "distance": 50,
                    "category_ids": {"162": True},
                    "osm_tags": {"name": "Water Point", "drinking_water": "yes"},
                },
                "geometry": {"coordinates": [10.1, 45.1]},
            },
        ]
    }

    session = FakeSession(response=FakeResponse(ok=True, payload=payload))
    service = PoiScoutService(config=config, session=cast(Any, session))

    result = service.get_poi_scout("key", 45.0, 10.0, 15.0)

    assert result["status"] == "Success"
    assert result["search_km"] == 1.5
    assert result["search_radius_m"] == 1500
    assert result["search_strategy"] == "start_radius"
    assert result["total_found"] == 2
    assert result["amenities"][0]["distance_m"] == 50
    assert result["amenities"][0]["potability"] == "potable_tagged"
    assert session.calls[0]["url"] == poi_module.ORS_POIS_URL
    assert session.calls[0]["timeout"] == 10.0


def test_get_poi_scout_returns_api_error(config):
    session = FakeSession(response=FakeResponse(ok=False, status_code=429, text="rate limit"))
    service = PoiScoutService(config=config, session=cast(Any, session))

    result = service.get_poi_scout("key", 45.0, 10.0, 1.0)

    assert result["status"] == "Error"
    assert "ORS POI API error 429" in result["message"]


def test_get_poi_scout_returns_domain_error_on_invalid_json(config):
    session = FakeSession(response=FakeResponse(ok=True, json_exc=ValueError("bad json")))
    service = PoiScoutService(config=config, session=cast(Any, session))

    result = service.get_poi_scout("key", 45.0, 10.0, 1.0)

    assert result == {"status": "Error", "message": "ORS returned invalid JSON."}


def test_get_poi_scout_returns_domain_error_on_invalid_input(service):
    result = service.get_poi_scout("", 45.0, 10.0, 1.0)

    assert result == {"status": "Error", "message": "API key must not be empty."}


def test_get_poi_scout_handles_request_exception(config):
    session = FakeSession(exc=requests.RequestException("network boom"))
    service = PoiScoutService(config=config, session=cast(Any, session))

    result = service.get_poi_scout("key", 45.0, 10.0, 1.0)

    assert result["status"] == "Error"
    assert "POI provider error: network boom" in result["message"]


def test_get_poi_scout_samples_route_geometry(config):
    payload = {"features": []}
    session = FakeSession(response=FakeResponse(ok=True, payload=payload))
    service = PoiScoutService(config=config, session=cast(Any, session))
    route = [[10.0, 45.0, 0], [10.02, 45.0, 0], [10.04, 45.0, 0], [10.06, 45.0, 0]]

    result = service.get_poi_scout("key", 45.0, 10.0, 40.0, route_geometry=route)

    assert result["status"] == "Success"
    assert result["search_strategy"] == "route_sampled"
    assert result["sample_points"] >= 2
    assert len(session.calls) == result["sample_points"]


def test_haversine_distance_zero():
    assert haversine_distance(45.0, 10.0, 45.0, 10.0) == 0.0


def test_haversine_distance_positive():
    result = haversine_distance(45.0, 10.0, 45.1, 10.1)
    assert result > 0


def test_service_haversine_distance_staticmethod(service):
    result = service.haversine_distance(45.0, 10.0, 45.1, 10.1)
    assert result > 0


def test_module_level_wrapper(monkeypatch):
    class FakeService:
        def __init__(self):
            self.calls = []

        def get_poi_scout(self, api_key, lat, lon, total_length_km, route_geometry=None):
            self.calls.append((api_key, lat, lon, total_length_km, route_geometry))
            return {"status": "Success", "amenities": []}

    fake_service = FakeService()
    monkeypatch.setattr(poi_module, "service", fake_service)

    result = get_poi_scout("key", 45.0, 10.0, 1.2)

    assert result == {"status": "Success", "amenities": []}
    assert fake_service.calls == [("key", 45.0, 10.0, 1.2, None)]
