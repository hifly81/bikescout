from datetime import datetime
import zoneinfo

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
        timezone_finder=FakeTimezoneFinder(None),
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
    assert "No hourly weather data returned from API." in result["message"]
    assert result["tactical_analysis"] is None


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


def test_get_mud_risk_analysis_uses_surface_fallback_and_coerced_coords(fixed_now):
    payload = {
        "hourly": {
            "time": ["2026-06-03T12:00"],
            "precipitation": [0.0],
            "temperature_2m": [20.0],
            "wind_speed_10m": [10.0],
            "cloudcover": [0.0],
        }
    }
    session = FakeSession(response=FakeResponse(payload=payload))
    service = MudAnalysisService(
        config=MudAnalysisConfig(),
        requests_session=session,
        timezone_finder=FakeTimezoneFinder("UTC"),
        solar_altitude_func=lambda lat, lon, dt: 25.0,
        now_func=fixed_now,
    )

    result = service.get_mud_risk_analysis("bad", "bad", None, None)

    assert result["status"] == "Success"
    assert result["tactical_analysis"]["surface_type"] == "dirt"


def test_module_level_wrapper(monkeypatch):
    class FakeService:
        def __init__(self):
            self.calls = []

        def get_mud_risk_analysis(self, **kwargs):
            self.calls.append(kwargs)
            return {"status": "Success", "metadata": {}, "environmental_context": {}, "tactical_analysis": {}}

    fake_service = FakeService()
    monkeypatch.setattr(mud_module, "service", fake_service)

    result = get_mud_risk_analysis(45.0, 10.0, "dirt", None)

    assert result["status"] == "Success"
    assert len(fake_service.calls) == 1