import pytest
from unittest.mock import patch, MagicMock
import zoneinfo
from datetime import datetime, timedelta, timezone
from bikescout.tools.mud import get_mud_risk_analysis, _get_seasonal_saturation_bias

class TestMud:

    @pytest.fixture
    def mock_weather_response(self):
        times = [(datetime(2026, 5, 8) - timedelta(hours=i)).isoformat() for i in range(73)]
        return {
            "hourly": {
                "time": list(reversed(times)),
                "precipitation": [0.0] * 73,
                "temperature_2m": [20.0] * 73,
                "wind_speed_10m": [10.0] * 73,
                "cloudcover": [0] * 73
            }
        }

    def test_seasonal_bias_logic(self):
        winter_dt = datetime(2026, 1, 15)
        summer_dt = datetime(2026, 7, 15)

        m_winter = _get_seasonal_saturation_bias(winter_dt, 45.0)
        m_summer = _get_seasonal_saturation_bias(summer_dt, 45.0)

        assert m_winter == 20.0
        assert m_summer == 0.0

    @patch("requests.get")
    def test_clay_saturation_penalty(self, mock_get, mock_weather_response):
        local_tz = zoneinfo.ZoneInfo("Europe/Rome")
        end_date = datetime.now(local_tz)
        start_date = end_date - timedelta(hours=72)

        mock_times = []
        current = start_date
        while current <= end_date:
            mock_times.append(current.strftime("%Y-%m-%dT%H:%M:%S"))
            current += timedelta(hours=1)

        total_hours = len(mock_times)

        mock_weather_response["hourly"] = {
            "time": mock_times,
            "precipitation": [10.0] * total_hours,
            "temperature_2m": [5.0] * total_hours,
            "wind_speed_10m": [0.0] * total_hours,
            "cloudcover": [100.0] * total_hours
        }

        mock_get.return_value.json.return_value = mock_weather_response
        mock_get.return_value.status_code = 200

        result = get_mud_risk_analysis(45.0, 9.0, surface_type="clay")

        assert result["tactical_analysis"]["mud_risk_score"] == "Extreme"
        assert "DO NOT RIDE" in result["tactical_analysis"]["trail_damage_risk"]["advice"]


    @patch("requests.get")
    def test_dry_time_eta_projection(self, mock_get, mock_weather_response):
        local_tz = zoneinfo.ZoneInfo("Europe/Rome")
        end_date = datetime.now(local_tz)
        start_date = end_date - timedelta(hours=72)

        mock_times = []
        current = start_date - timedelta(hours=2)
        while current <= end_date + timedelta(hours=2):
            mock_times.append(current.strftime("%Y-%m-%dT%H:%M:%S"))
            current += timedelta(hours=1)

        total_hours = len(mock_times)

        mock_weather_response["hourly"] = {
            "time": mock_times,
            "precipitation": [5.0] * total_hours,
            "temperature_2m": [10.0] * total_hours,
            "wind_speed_10m": [2.0] * total_hours,
            "cloudcover": [100.0] * total_hours
        }

        mock_get.return_value.json.return_value = mock_weather_response
        mock_get.return_value.status_code = 200

        result = get_mud_risk_analysis(45.0, 9.0, surface_type="clay")

        assert "hours" in result["tactical_analysis"]["dry_time_eta"]
        assert result["tactical_analysis"]["mud_risk_score"] in ["High", "Extreme"]

    @patch("requests.get")
    def test_api_failure_handling(self, mock_get):
        mock_get.side_effect = Exception("Network Down")
        result = get_mud_risk_analysis(45.0, 9.0)
        assert result["status"] == "Error"