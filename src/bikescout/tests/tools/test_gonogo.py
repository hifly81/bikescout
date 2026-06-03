import pytest
from datetime import date
from unittest.mock import patch
from bikescout.tools.gonogo import calculate_ride_windows, _clean_weather_value

class TestPlanner:

    @pytest.fixture
    def mock_weather_data(self):
        """Genera 24 ore di meteo perfetto."""
        forecast = []
        for h in range(24):
            forecast.append({
                "time": f"{h:02d}:00",
                "rain_prob": "0%",
                "wind": "10 km/h",
                "temp": "20C"
            })
        return {"tactical_forecast": forecast}

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_perfect_day_go_verdict(self, mock_mud, mock_weather, mock_weather_data):
        mock_weather.return_value = mock_weather_data
        mock_mud.return_value = {"mud_risk_score": 0}

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2, surface_type="asphalt")

        assert result["status"] == "Success"
        assert result["planner_report"]["verdict"] == "GO"
        assert result["planner_report"]["tactical_color"] == "GREEN"

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_night_ride_no_go(self, mock_mud, mock_weather, mock_weather_data):
        mock_weather.return_value = mock_weather_data
        mock_mud.return_value = {"mud_risk_score": 0}

        result = calculate_ride_windows(45.0, 9.0, ride_duration_hours=12, target_date="2026-12-21")

        assert result["planner_report"]["verdict"] == "NO-GO"
        assert "No safe daylight" in result["planner_report"]["environmental_briefing"]["message"]

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_extreme_weather_penalties(self, mock_mud, mock_weather):
        bad_weather = {"tactical_forecast": [
            {"time": f"{h:02d}:00", "rain_prob": 90, "wind": 50, "temp": 2} for h in range(24)
        ]}
        mock_weather.return_value = bad_weather
        mock_mud.return_value = {"mud_risk_score": 80}

        result = calculate_ride_windows(45.0, 9.0, ride_duration_hours=2, surface_type="dirt")

        assert result["planner_report"]["tactical_color"] == "RED"
        assert result["planner_report"]["verdict"] == "NO-GO"

    def test_weather_cleaning_utility(self):
        assert _clean_weather_value("25°C") == 25.0
        assert _clean_weather_value("10%") == 10.0
        assert _clean_weather_value("15 km/h") == 15.0
        assert _clean_weather_value(None) == 0.0
        assert _clean_weather_value("Invalid") == 0.0

    @patch("bikescout.tools.gonogo.sun")
    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_solar_visibility_exception(self, mock_mud, mock_weather, mock_sun, mock_weather_data):
        mock_sun.side_effect = Exception("Astral calculation failed")
        mock_weather.return_value = mock_weather_data
        mock_mud.return_value = {"tactical_analysis": {"mud_risk_numeric": 0.0}}

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2, surface_type="asphalt")

        assert result["status"] == "Success"
        assert result["metadata"]["solar_window"] == "7:00 - 18:00"

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_malformed_forecast_hour_skips(self, mock_mud, mock_weather):
        malformed_forecast = {"tactical_forecast": [
            {"time": "ORARIO_NON_VALIDO", "rain_prob": 0, "wind": 10, "temp": 20},
            {"time": "12:00", "rain_prob": 0, "wind": 10, "temp": 20},
            {"time": "13:00", "rain_prob": 0, "wind": 10, "temp": 20}
        ]}
        mock_weather.return_value = malformed_forecast
        mock_mud.return_value = {"tactical_analysis": {"mud_risk_numeric": 0.0}}

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2, surface_type="asphalt")

        assert result["status"] == "Success"
        assert result["planner_report"]["best_window"] == "12:00 - 13:00"

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_scoring_extreme_cold(self, mock_mud, mock_weather):
        freezing_weather = {"tactical_forecast": [
            {"time": f"{h:02d}:00", "rain_prob": 0, "wind": 10, "temp": -5} for h in range(24)
        ]}
        mock_weather.return_value = freezing_weather
        mock_mud.return_value = {"tactical_analysis": {"mud_risk_numeric": 0.0}}

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2, surface_type="asphalt")

        assert result["status"] == "Success"
        assert result["planner_report"]["tactical_color"] in ["YELLOW", "RED"]

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_scoring_extreme_heat(self, mock_mud, mock_weather):
        scorching_weather = {"tactical_forecast": [
            {"time": f"{h:02d}:00", "rain_prob": 0, "wind": 10, "temp": 38} for h in range(24)
        ]}
        mock_weather.return_value = scorching_weather
        mock_mud.return_value = {"tactical_analysis": {"mud_risk_numeric": 0.0}}

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2, surface_type="asphalt")

        assert result["status"] == "Success"
        assert result["planner_report"]["tactical_color"] in ["YELLOW", "RED"]

    def test_calculate_ride_windows_global_exception(self):
        result = calculate_ride_windows(41.9, 12.4, target_date="not-a-valid-date-string")

        assert result["status"] == "Error"
        assert "Tactical Planner failed" in result["message"]