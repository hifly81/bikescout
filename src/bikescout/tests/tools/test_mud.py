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

import zoneinfo
from datetime import datetime
from typing import Any, cast

import pytest

import bikescout.tools.mud as mud_module
from bikescout.tools.mud import (
    MudAnalysisConfig,
    MudAnalysisService,
    _get_seasonal_saturation_bias,
    get_mud_risk_analysis,
    get_solar_altitude,
)


class FakeTimezoneFinder:
    def __init__(self, tz_name="UTC"):
        self.tz_name = tz_name

    def timezone_at(self, lng, lat):
        return self.tz_name


class FakeResponse:
    def __init__(self, payload=None, exc=None):
        self.payload = payload if payload is not None else {}
        self.exc = exc

    def raise_for_status(self):
        if self.exc:
            raise self.exc

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        if self.exc:
            raise self.exc
        return self.response


@pytest.fixture
def fixed_now():
    def _now(tz):
        return datetime(2026, 6, 3, 12, 0, 0, tzinfo=tz)

    return _now


@pytest.fixture
def service(fixed_now):
    return MudAnalysisService(
        config=MudAnalysisConfig(),
        requests_session=FakeSession(),
        timezone_finder=FakeTimezoneFinder("UTC"),
        solar_altitude_func=lambda lat, lon, dt: 30.0,
        now_func=fixed_now,
    )


def test_get_solar_altitude_returns_float():
    result = get_solar_altitude(45.0, 10.0, datetime(2026, 6, 3, 12, 0, 0))
    assert isinstance(result, float)


def test_resolve_timezone_name(service):
    assert service._resolve_timezone_name(45.0, 10.0) == "UTC"


def test_resolve_timezone_name_fallback_to_utc(fixed_now):
    service = MudAnalysisService(
        config=MudAnalysisConfig(),
        requests_session=FakeSession(),
        timezone_finder=FakeTimezoneFinder(cast(Any, None)),
        solar_altitude_func=lambda lat, lon, dt: 0.0,
        now_func=fixed_now,
    )
    assert service._resolve_timezone_name(45.0, 10.0) == "UTC"


def test_reference_date_with_target_date(service):
    tz = zoneinfo.ZoneInfo("UTC")
    result = service._reference_date(tz, "2026-06-10")
    assert result == datetime(2026, 6, 10, 0, 0, 0, tzinfo=tz)


def test_reference_date_without_target_date(service, fixed_now):
    tz = zoneinfo.ZoneInfo("UTC")
    result = service._reference_date(tz, None)
    assert result == fixed_now(tz)


def test_build_weather_params(service):
    tz = "UTC"
    start = datetime(2026, 6, 1, 0, 0, 0)
    end = datetime(2026, 6, 3, 0, 0, 0)
    params = service._build_weather_params(45.0, 10.0, start, end, tz)

    assert params["latitude"] == 45.0
    assert params["longitude"] == 10.0
    assert params["start_date"] == "2026-06-01"
    assert params["end_date"] == "2026-06-03"
    assert params["timezone"] == "UTC"


def test_base_drainage_coefficient(service):
    assert service._base_drainage_coefficient("asphalt") == 0.50
    assert service._base_drainage_coefficient("sand") == 0.30
    assert service._base_drainage_coefficient("gravel") == 0.15
    assert service._base_drainage_coefficient("grass") == 0.10
    assert service._base_drainage_coefficient("dirt") == 0.08
    assert service._base_drainage_coefficient("earth") == 0.08
    assert service._base_drainage_coefficient("clay") == 0.04
    assert service._base_drainage_coefficient("weird") == 0.08


def test_normalize_surface_type(service):
    assert service._normalize_surface_type(" Clay ") == "clay"
    assert service._normalize_surface_type("") == "dirt"
    assert service._normalize_surface_type(None) == "dirt"


def test_normalize_display_surface_labels(service):
    assert service._normalize_surface_type(" Paved ") == "asphalt"
    assert service._normalize_surface_type("Asphalt") == "asphalt"
    assert service._normalize_surface_type("Concrete") == "asphalt"
    assert service._normalize_surface_type("Unpaved") == "dirt"
    assert service._normalize_surface_type("Unmapped/Mixed") == "dirt"
    assert service._normalize_surface_type("Unknown") == "dirt"


def test_coerce_float(service):
    assert service._coerce_float("12.5", 0.0) == 12.5
    assert service._coerce_float("bad", 1.0) == 1.0


def test_iter_hourly_points(service):
    tz = zoneinfo.ZoneInfo("UTC")
    rows = list(
        service._iter_hourly_points(
            ["2026-06-03T10:00"],
            [1.0],
            [20.0],
            [10.0],
            [30.0],
            tz,
        )
    )

    assert len(rows) == 1
    current_dt, rain, temp, wind, cloud = rows[0]
    assert current_dt == datetime(2026, 6, 3, 10, 0, tzinfo=tz)
    assert rain == 1.0
    assert temp == 20.0
    assert wind == 10.0
    assert cloud == 30.0


def test_dry_time_eta_ready_now(service):
    assert service._dry_time_eta(1.0, 0.08, 1.0, "dirt") == 0


def test_dry_time_eta_positive(service):
    result = service._dry_time_eta(10.0, 0.08, 1.0, "dirt")
    assert result > 0


def test_dry_time_eta_clay_branch(service):
    result = service._dry_time_eta(20.0, 0.04, 1.0, "clay")
    assert result > 0


def test_traction_risk(service):
    assert service._traction_risk(1.0)[0] == "Low"
    assert service._traction_risk(3.0)[0] == "Medium"
    assert service._traction_risk(10.0)[0] == "High"


def test_traction_risk_on_hard_surfaces_never_reports_mud_packing(service):
    assert service._traction_risk(1.0, "asphalt") == (
        "Low",
        "Firm tarmac grip. Minimal slip risk.",
    )
    assert service._traction_risk(3.0, "concrete")[0] == "Medium"

    level, advice = service._traction_risk(10.0, "asphalt")
    assert level == "Medium"
    assert "aquaplaning" in advice.lower()
    assert "pack" not in advice.lower()


def test_damage_risk(service):
    assert service._damage_risk(2.0)[0] == "Low"
    assert service._damage_risk(10.0)[0] == "Medium"
    assert service._damage_risk(20.0)[0] == "Extreme"


def test_global_mud_label(service):
    assert service._global_mud_label(2.0) == "Low"
    assert service._global_mud_label(10.0) == "Medium"
    assert service._global_mud_label(15.0) == "High"
    assert service._global_mud_label(25.0) == "Extreme"


def test_get_seasonal_saturation_bias_northern():
    dt = datetime(2026, 1, 1)
    assert _get_seasonal_saturation_bias(dt, 45.0) == 20.0


def test_get_seasonal_saturation_bias_southern():
    dt = datetime(2026, 7, 1)
    assert _get_seasonal_saturation_bias(dt, -33.0) == 20.0


def test_get_mud_risk_analysis_success_archive(fixed_now):
    payload = {
        "hourly": {
            "time": [
                "2026-06-02T10:00",
                "2026-06-03T08:00",
                "2026-06-03T12:00",
            ],
            "precipitation": [0.0, 2.0, 1.0],
            "temperature_2m": [18.0, 20.0, 22.0],
            "wind_speed_10m": [8.0, 10.0, 12.0],
            "cloudcover": [50.0, 40.0, 30.0],
        }
    }
    session = FakeSession(response=FakeResponse(payload=payload))
    service = MudAnalysisService(
        config=MudAnalysisConfig(),
        requests_session=session,
        timezone_finder=FakeTimezoneFinder("UTC"),
        solar_altitude_func=lambda lat, lon, dt: 30.0,
        now_func=fixed_now,
    )

    result = service.get_mud_risk_analysis(45.0, 10.0, "dirt", None)

    assert result["status"] == "Success"
    assert result["metadata"]["timezone"] == "UTC"
    assert result["metadata"]["is_predictive"] is False
    assert result["metadata"]["model"] == "TAEL® v3.2"
    assert result["tactical_analysis"]["surface_type"] == "dirt"
    assert session.calls[0]["url"] == mud_module.ARCHIVE_URL


def test_get_mud_risk_analysis_maps_paved_to_asphalt(fixed_now):
    payload = {
        "hourly": {
            "time": ["2026-06-03T10:00"],
            "precipitation": [12.0],
            "temperature_2m": [20.0],
            "wind_speed_10m": [10.0],
            "cloudcover": [30.0],
        }
    }
    service = MudAnalysisService(
        config=MudAnalysisConfig(),
        requests_session=FakeSession(response=FakeResponse(payload=payload)),
        timezone_finder=FakeTimezoneFinder("UTC"),
        solar_altitude_func=lambda lat, lon, dt: 30.0,
        now_func=fixed_now,
    )

    result = service.get_mud_risk_analysis(45.0, 10.0, "Paved", None)

    assert result["status"] == "Success"
    assert result["tactical_analysis"]["surface_type"] == "asphalt"
    traction = result["tactical_analysis"]["traction_risk"]
    assert traction["level"] == "Medium"
    assert "aquaplaning" in traction["advice"].lower()


def test_get_mud_risk_analysis_success_forecast(fixed_now):
    payload = {
        "hourly": {
            "time": ["2026-06-10T00:00"],
            "precipitation": [1.0],
            "temperature_2m": [20.0],
            "wind_speed_10m": [10.0],
            "cloudcover": [20.0],
        }
    }
    session = FakeSession(response=FakeResponse(payload=payload))
    service = MudAnalysisService(
        config=MudAnalysisConfig(),
        requests_session=session,
        timezone_finder=FakeTimezoneFinder("UTC"),
        solar_altitude_func=lambda lat, lon, dt: 10.0,
        now_func=fixed_now,
    )

    result = service.get_mud_risk_analysis(45.0, 10.0, "clay", "2026-06-10")

    assert result["status"] == "Success"
    assert result["metadata"]["is_predictive"] is True
    assert session.calls[0]["url"] == mud_module.FORECAST_URL


def test_get_mud_risk_analysis_handles_missing_hourly_data(fixed_now):
    payload = {"hourly": {"time": []}}
    session = FakeSession(response=FakeResponse(payload=payload))
    service = MudAnalysisService(
        config=MudAnalysisConfig(),
        requests_session=session,
        timezone_finder=FakeTimezoneFinder("UTC"),
        solar_altitude_func=lambda lat, lon, dt: 0.0,
        now_func=fixed_now,
    )

    result = service.get_mud_risk_analysis(45.0, 10.0, "dirt", None)

    assert result["status"] == "Error"
    assert "No hourly weather data returned" in result["message"]
    assert "not treated as dry" in result["message"]
    assert result["next_step"]
    assert result["tactical_analysis"] is None


def test_get_mud_risk_analysis_rejects_invalid_coords(fixed_now):
    service = MudAnalysisService(
        config=MudAnalysisConfig(),
        requests_session=FakeSession(response=FakeResponse(payload={})),
        timezone_finder=FakeTimezoneFinder("UTC"),
        solar_altitude_func=lambda lat, lon, dt: 0.0,
        now_func=fixed_now,
    )

    result = service.get_mud_risk_analysis(999, 10.0, "dirt", None)

    assert result["status"] == "Error"
    assert "lat must be between -90 and 90" in result["message"]
    assert result["next_step"]


def test_get_mud_risk_analysis_rejects_inconsistent_hourly_arrays(fixed_now):
    payload = {
        "hourly": {
            "time": ["2026-06-03T12:00", "2026-06-03T13:00"],
            "precipitation": [0.0],
            "temperature_2m": [20.0, 21.0],
            "wind_speed_10m": [10.0, 10.0],
            "cloudcover": [0.0, 0.0],
        }
    }
    service = MudAnalysisService(
        config=MudAnalysisConfig(),
        requests_session=FakeSession(response=FakeResponse(payload=payload)),
        timezone_finder=FakeTimezoneFinder("UTC"),
        solar_altitude_func=lambda lat, lon, dt: 0.0,
        now_func=fixed_now,
    )

    result = service.get_mud_risk_analysis(45.0, 10.0, "dirt", None)

    assert result["status"] == "Error"
    assert "Inconsistent hourly weather arrays" in result["message"]


def test_get_mud_risk_analysis_rejects_missing_weather_value(fixed_now):
    payload = {
        "hourly": {
            "time": ["2026-06-03T12:00"],
            "precipitation": [None],
            "temperature_2m": [20.0],
            "wind_speed_10m": [10.0],
            "cloudcover": [0.0],
        }
    }
    service = MudAnalysisService(
        config=MudAnalysisConfig(),
        requests_session=FakeSession(response=FakeResponse(payload=payload)),
        timezone_finder=FakeTimezoneFinder("UTC"),
        solar_altitude_func=lambda lat, lon, dt: 0.0,
        now_func=fixed_now,
    )

    result = service.get_mud_risk_analysis(45.0, 10.0, "dirt", None)

    assert result["status"] == "Error"
    assert "Missing weather value" in result["message"]


def test_get_mud_risk_analysis_handles_request_failure(fixed_now):
    session = FakeSession(exc=RuntimeError("network down"))
    service = MudAnalysisService(
        config=MudAnalysisConfig(),
        requests_session=session,
        timezone_finder=FakeTimezoneFinder("UTC"),
        solar_altitude_func=lambda lat, lon, dt: 0.0,
        now_func=fixed_now,
    )

    result = service.get_mud_risk_analysis(45.0, 10.0, "dirt", None)

    assert result["status"] == "Error"
    assert "network down" in result["message"]


def test_get_mud_risk_analysis_invalid_coords_do_not_fallback_to_null_island(fixed_now):
    service = MudAnalysisService(
        config=MudAnalysisConfig(),
        requests_session=FakeSession(response=FakeResponse(payload={})),
        timezone_finder=FakeTimezoneFinder("UTC"),
        solar_altitude_func=lambda lat, lon, dt: 25.0,
        now_func=fixed_now,
    )

    result = service.get_mud_risk_analysis(cast(Any, "bad"), cast(Any, "bad"), "dirt", None)

    assert result["status"] == "Error"
    assert "lat and lon must be valid numbers" in result["message"]


def test_module_level_wrapper(monkeypatch):
    class FakeService:
        def __init__(self):
            self.calls = []

        def get_mud_risk_analysis(self, **kwargs):
            self.calls.append(kwargs)
            return {
                "status": "Success",
                "metadata": {},
                "environmental_context": {},
                "tactical_analysis": {},
            }

    fake_service = FakeService()
    monkeypatch.setattr(mud_module, "service", fake_service)

    result = get_mud_risk_analysis(45.0, 10.0, "dirt", None)

    assert result["status"] == "Success"
    assert len(fake_service.calls) == 1
