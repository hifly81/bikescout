from datetime import datetime
import zoneinfo

import pytest
import requests

import bikescout.tools.weather as weather_module
from bikescout.tools.weather import (
    WeatherConfig,
    WeatherService,
    apply_weather_windowing,
    get_safety_advice,
    get_weather_forecast,
)


class FakeTimezoneFinder:
    def __init__(self, tz_name="UTC"):
        self.tz_name = tz_name

    def timezone_at(self, lng, lat):
        return self.tz_name


class FakeResponse:
    def __init__(self, payload=None, raise_exc=None):
        self.payload = payload if payload is not None else {}
        self.raise_exc = raise_exc

    def raise_for_status(self):
        if self.raise_exc:
            raise self.raise_exc

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
        return datetime(2026, 6, 3, 11, 30, 0, tzinfo=tz)
    return _now


@pytest.fixture
def service(fixed_now):
    return WeatherService(
        config=WeatherConfig(),
        requests_session=FakeSession(),
        timezone_finder=FakeTimezoneFinder("UTC"),
        now_func=fixed_now,
    )


def test_get_safety_advice_not_recommended():
    result = get_safety_advice(app_temp=10, rain_prob=10, rain_mm=12.0, wind_speed=20, wind_gusts=20)
    assert result["status"] == "? [NOT RECOMMENDED]"


def test_get_safety_advice_caution():
    result = get_safety_advice(app_temp=10, rain_prob=10, rain_mm=3.0, wind_speed=20, wind_gusts=20)
    assert result["status"] == "? [CAUTION]"


def test_get_safety_advice_watch():
    result = get_safety_advice(app_temp=10, rain_prob=40, rain_mm=0.0, wind_speed=20, wind_gusts=20)
    assert result["status"] == "? [WATCH]"


def test_get_safety_advice_go_and_gear_ranges():
    cold = get_safety_advice(app_temp=0, rain_prob=0, rain_mm=0.0, wind_speed=5, wind_gusts=5)
    mild = get_safety_advice(app_temp=10, rain_prob=0, rain_mm=0.0, wind_speed=5, wind_gusts=5)
    warm = get_safety_advice(app_temp=20, rain_prob=0, rain_mm=0.0, wind_speed=5, wind_gusts=5)
    hot = get_safety_advice(app_temp=30, rain_prob=0, rain_mm=0.0, wind_speed=5, wind_gusts=5)

    assert cold["gear_advice"].startswith("Deep Winter")
    assert mild["gear_advice"].startswith("Spring/Fall")
    assert warm["gear_advice"].startswith("Standard")
    assert hot["gear_advice"].startswith("High Summer")
    assert warm["status"] == "? [GO]"


def test_resolve_timezone_name(service):
    assert service._resolve_timezone_name(45.0, 10.0) == "UTC"


def test_resolve_timezone_name_fallback_to_utc(fixed_now):
    service = WeatherService(
        config=WeatherConfig(),
        requests_session=FakeSession(),
        timezone_finder=FakeTimezoneFinder(None),
        now_func=fixed_now,
    )
    assert service._resolve_timezone_name(45.0, 10.0) == "UTC"


def test_target_datetime_with_target_date(service):
    tz = zoneinfo.ZoneInfo("UTC")
    result = service._target_datetime(tz, "2026-06-10", 9)
    assert result == datetime(2026, 6, 10, 9, 0, 0, tzinfo=tz)


def test_target_datetime_without_target_date(service, fixed_now):
    tz = zoneinfo.ZoneInfo("UTC")
    result = service._target_datetime(tz, None, 9)
    assert result == datetime(2026, 6, 3, 9, 0, 0, tzinfo=tz)


def test_build_forecast_params(service):
    tz_name = "UTC"
    dt = datetime(2026, 6, 3, 9, 0, 0)
    params = service._build_forecast_params(45.0, 10.0, tz_name, dt)

    assert params["latitude"] == 45.0
    assert params["longitude"] == 10.0
    assert params["timezone"] == "UTC"
    assert params["start_date"] == "2026-06-03"
    assert params["end_date"] == "2026-06-03"


def test_reference_index_found(service):
    hourly = {"time": ["2026-06-03T08:00", "2026-06-03T09:00"]}
    target = datetime(2026, 6, 3, 9, 0, 0)
    assert service._reference_index(hourly, target) == 1


def test_reference_index_fallback(service):
    hourly = {"time": ["2026-06-03T08:00"]}
    target = datetime(2026, 6, 3, 9, 0, 0)
    assert service._reference_index(hourly, target) == 0


def test_forecast_summary(service):
    hourly = {
        "time": ["2026-06-03T09:00"],
        "temperature_2m": [20],
        "apparent_temperature": [19],
        "precipitation_probability": [30],
        "precipitation": [0.5],
        "windspeed_10m": [12],
        "windgusts_10m": [20],
        "winddirection_10m": [180],
    }

    result = service._forecast_summary(hourly)

    assert result == [
        {
            "time": "09:00",
            "temp": "20�C",
            "app_temp": "19�C",
            "rain_prob": "30%",
            "rain_mm": "0.5 mm",
            "wind": "12 km/h",
            "gusts": "20 km/h",
            "wind_direction": "180�",
        }
    ]


def test_forecast_summary_uses_shortest_length(service):
    hourly = {
        "time": ["2026-06-03T09:00", "2026-06-03T10:00"],
        "temperature_2m": [20],
        "apparent_temperature": [19],
        "precipitation_probability": [30],
        "precipitation": [0.5],
        "windspeed_10m": [12],
        "windgusts_10m": [20],
        "winddirection_10m": [180],
    }
    result = service._forecast_summary(hourly)
    assert len(result) == 1


def test_coerce_float(service):
    assert service._coerce_float("12.5", 0.0) == 12.5
    assert service._coerce_float("bad", 1.0) == 1.0


def test_normalize_target_hour(service):
    assert service._normalize_target_hour(9) == 9
    assert service._normalize_target_hour(-1) == 0
    assert service._normalize_target_hour(30) == 23
    assert service._normalize_target_hour("bad") == 9


def test_get_weather_forecast_success(service, fixed_now):
    payload = {
        "hourly": {
            "time": ["2026-06-03T09:00", "2026-06-03T10:00"],
            "temperature_2m": [20, 22],
            "apparent_temperature": [19, 21],
            "precipitation_probability": [10, 20],
            "precipitation": [0.0, 0.2],
            "windspeed_10m": [12, 14],
            "windgusts_10m": [20, 25],
            "winddirection_10m": [180, 190],
            "weathercode": [1, 2],
        }
    }
    session = FakeSession(response=FakeResponse(payload=payload))
    service = WeatherService(
        config=WeatherConfig(),
        requests_session=session,
        timezone_finder=FakeTimezoneFinder("UTC"),
        now_func=fixed_now,
    )

    result = service.get_weather_forecast(45.0, 10.0, None, 9)

    assert result["status"] == "Success"
    assert result["metadata"]["local_timezone"] == "UTC"
    assert result["metadata"]["target_time_local"] == "09:00"
    assert result["reference_conditions"]["temp_actual"] == 20
    assert result["reference_conditions"]["temp_max"] == 22
    assert session.calls[0]["url"] == weather_module.OPEN_METEO_URL


def test_get_weather_forecast_with_target_date(service, fixed_now):
    payload = {
        "hourly": {
            "time": ["2026-06-10T15:00"],
            "temperature_2m": [28],
            "apparent_temperature": [31],
            "precipitation_probability": [50],
            "precipitation": [3.0],
            "windspeed_10m": [30],
            "windgusts_10m": [40],
            "winddirection_10m": [200],
            "weathercode": [3],
        }
    }
    session = FakeSession(response=FakeResponse(payload=payload))
    service = WeatherService(
        config=WeatherConfig(),
        requests_session=session,
        timezone_finder=FakeTimezoneFinder("UTC"),
        now_func=fixed_now,
    )

    result = service.get_weather_forecast(45.0, 10.0, "2026-06-10", 15)

    assert result["status"] == "Success"
    assert result["metadata"]["date_analyzed"] == "2026-06-10"
    assert result["reference_conditions"]["reference_hour_local"] == "15:00"


def test_get_weather_forecast_no_hourly_data(service, fixed_now):
    session = FakeSession(response=FakeResponse(payload={}))
    service = WeatherService(
        config=WeatherConfig(),
        requests_session=session,
        timezone_finder=FakeTimezoneFinder("UTC"),
        now_func=fixed_now,
    )

    result = service.get_weather_forecast(45.0, 10.0, None, 9)

    assert result == {"status": "Error", "message": "No hourly data returned from provider."}


def test_get_weather_forecast_request_exception(service, fixed_now):
    session = FakeSession(exc=requests.exceptions.RequestException("network down"))
    service = WeatherService(
        config=WeatherConfig(),
        requests_session=session,
        timezone_finder=FakeTimezoneFinder("UTC"),
        now_func=fixed_now,
    )

    result = service.get_weather_forecast(45.0, 10.0, None, 9)

    assert result["status"] == "Error"
    assert "Weather API Connection Error: network down" == result["message"]


def test_get_weather_forecast_unexpected_exception(service, fixed_now):
    service = WeatherService(
        config=WeatherConfig(),
        requests_session=FakeSession(response=FakeResponse(payload={"hourly": None})),
        timezone_finder=FakeTimezoneFinder("UTC"),
        now_func=fixed_now,
    )

    result = service.get_weather_forecast(45.0, 10.0, None, 9)

    assert result["status"] == "Error"
    assert "Unexpected Weather Engine Error" in result["message"]


def test_get_weather_forecast_reference_index_fallback_to_zero(service, fixed_now):
    payload = {
        "hourly": {
            "time": ["2026-06-03T08:00"],
            "temperature_2m": [20],
            "apparent_temperature": [19],
            "precipitation_probability": [10],
            "precipitation": [0.0],
            "windspeed_10m": [12],
            "windgusts_10m": [20],
            "winddirection_10m": [180],
            "weathercode": [1],
        }
    }
    session = FakeSession(response=FakeResponse(payload=payload))
    service = WeatherService(
        config=WeatherConfig(),
        requests_session=session,
        timezone_finder=FakeTimezoneFinder("UTC"),
        now_func=fixed_now,
    )

    result = service.get_weather_forecast(45.0, 10.0, None, 9)

    assert result["status"] == "Success"
    assert result["reference_conditions"]["temp_actual"] == 20


def test_get_weather_forecast_empty_temperature_max(service, fixed_now):
    payload = {
        "hourly": {
            "time": ["2026-06-03T09:00"],
            "temperature_2m": [],
            "apparent_temperature": [19],
            "precipitation_probability": [10],
            "precipitation": [0.0],
            "windspeed_10m": [12],
            "windgusts_10m": [20],
            "winddirection_10m": [180],
            "weathercode": [1],
        }
    }
    session = FakeSession(response=FakeResponse(payload=payload))
    service = WeatherService(
        config=WeatherConfig(),
        requests_session=session,
        timezone_finder=FakeTimezoneFinder("UTC"),
        now_func=fixed_now,
    )

    result = service.get_weather_forecast(45.0, 10.0, None, 9)

    assert result["status"] == "Error" or result["reference_conditions"]["temp_max"] == "N/A"


def test_apply_weather_windowing_updates_reference_conditions():
    weather_data = {
        "tactical_forecast": [
            {"time": "08:00", "temp": "18�C", "wind": "10 km/h", "wind_direction": "180�"},
            {"time": "09:00", "temp": "20�C", "wind": "12 km/h", "wind_direction": "190�"},
            {"time": "10:00", "temp": "22�C", "wind": "14 km/h", "wind_direction": "200�"},
        ],
        "reference_conditions": {},
    }

    result = apply_weather_windowing(weather_data, 9, 10)

    assert len(result["tactical_forecast"]) == 2
    assert result["reference_conditions"]["temp"] == 21.0
    assert result["reference_conditions"]["wind_speed"] == 13.0
    assert result["reference_conditions"]["wind_dir_degrees"] == 195
    assert result["reference_conditions"]["reference_hour"] == "Calculated window 09-10"


def test_apply_weather_windowing_creates_reference_conditions_if_missing():
    weather_data = {
        "tactical_forecast": [
            {"time": "09:00", "temp": "20�C", "wind": "12 km/h", "wind_direction": "190�"},
        ]
    }

    result = apply_weather_windowing(weather_data, 9, 9)

    assert "reference_conditions" in result
    assert result["reference_conditions"]["temp"] == 20.0


def test_apply_weather_windowing_skips_bad_rows():
    weather_data = {
        "tactical_forecast": [
            {"time": "bad", "temp": "20�C", "wind": "12 km/h", "wind_direction": "190�"},
            {"time": "09:00", "temp": "bad", "wind": "12 km/h", "wind_direction": "190�"},
            {"time": "10:00", "temp": "22�C", "wind": "14 km/h", "wind_direction": "200�"},
            {"temp": "22�C", "wind": "14 km/h", "wind_direction": "200�"},
        ],
        "reference_conditions": {},
    }

    result = apply_weather_windowing(weather_data, 9, 10)

    assert len(result["tactical_forecast"]) == 2
    assert result["reference_conditions"]["temp"] == 22.0


def test_module_level_wrapper(monkeypatch):
    class FakeService:
        def __init__(self):
            self.calls = []

        def get_weather_forecast(self, **kwargs):
            self.calls.append(kwargs)
            return {"status": "Success", "metadata": {}, "tactical_forecast": [], "reference_conditions": {}, "safety_advice": {}}

    fake_service = FakeService()
    monkeypatch.setattr(weather_module, "service", fake_service)

    result = get_weather_forecast(45.0, 10.0, None, 9)

    assert result["status"] == "Success"
    assert len(fake_service.calls) == 1