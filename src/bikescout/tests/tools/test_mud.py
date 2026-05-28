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

    @patch("bikescout.tools.mud.elevation")
    def test_solar_altitude_exception(self, mock_elevation):
        mock_elevation.side_effect = Exception("Mocked astral error")
        from bikescout.tools.mud import get_solar_altitude

        result = get_solar_altitude(45.0, 9.0, datetime.now())
        assert result == 0.0

    @patch("requests.get")
    def test_target_date_and_predictive_forecast(self, mock_get, mock_weather_response):
        mock_get.return_value.json.return_value = mock_weather_response
        mock_get.return_value.status_code = 200

        future_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        result = get_mud_risk_analysis(45.0, 9.0, target_date=future_date)

        assert result["status"] == "Success"
        assert result["metadata"]["is_predictive"] is True

        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert "forecast" in called_url

    @patch("requests.get")
    def test_empty_api_data_raises_value_error(self, mock_get):
        mock_get.return_value.json.return_value = {"hourly": {}}
        mock_get.return_value.status_code = 200

        result = get_mud_risk_analysis(45.0, 9.0)

        assert result["status"] == "Error"
        assert "No hourly weather data returned" in result["message"]

    def test_southern_hemisphere_seasonal_bias(self):
        winter_dt = datetime(2026, 7, 15)
        summer_dt = datetime(2026, 1, 15)

        m_winter = _get_seasonal_saturation_bias(winter_dt, -30.0)
        m_summer = _get_seasonal_saturation_bias(summer_dt, -30.0)

        assert m_winter == 20.0
        assert m_summer == 0.0

    @patch("requests.get")
    def test_completely_dry_state_ready_now(self, mock_get, mock_weather_response):
        mock_get.return_value.json.return_value = mock_weather_response
        mock_get.return_value.status_code = 200

        with patch("bikescout.tools.mud._get_seasonal_saturation_bias", return_value=0.0):
            result = get_mud_risk_analysis(45.0, 9.0, surface_type="asphalt")

        analysis = result["tactical_analysis"]
        assert analysis["mud_risk_score"] == "Low"
        assert analysis["traction_risk"]["level"] == "Low"
        assert analysis["trail_damage_risk"]["level"] == "Low"
        assert analysis["dry_time_eta"] == "Ready Now"

    @patch("requests.get")
    def test_global_label_high_risk_line_201(self, mock_get, mock_weather_response):
        local_tz = zoneinfo.ZoneInfo("Europe/Rome")
        end_date = datetime.now(local_tz)
        start_date = end_date - timedelta(hours=72)

        mock_times = []
        current = start_date
        while current <= end_date:
            mock_times.append(current.strftime("%Y-%m-%dT%H:%M:%S"))
            current += timedelta(hours=1)

        total_hours = len(mock_times)

        precip_data = [0.0] * total_hours
        precip_data[-1] = 15.0

        mock_weather_response["hourly"] = {
            "time": mock_times,
            "precipitation": precip_data,
            "temperature_2m": [20.0] * total_hours,
            "wind_speed_10m": [10.0] * total_hours,
            "cloudcover": [0] * total_hours
        }

        mock_get.return_value.json.return_value = mock_weather_response
        mock_get.return_value.status_code = 200

        with patch("bikescout.tools.mud._get_seasonal_saturation_bias", return_value=0.0):
            result = get_mud_risk_analysis(45.0, 9.0, surface_type="dirt")

        assert result["status"] == "Success"
        assert result["tactical_analysis"]["mud_risk_score"] == "High"