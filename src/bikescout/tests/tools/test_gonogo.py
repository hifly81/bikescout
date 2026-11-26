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

from unittest.mock import patch

import pytest

from bikescout.tools.gonogo import _duration_slots, calculate_ride_windows, _clean_weather_value


class TestPlanner:
    @pytest.fixture
    def mock_weather_data(self):
        return {
            "status": "Success",
            "tactical_forecast": [
                {"time": f"{h:02d}:00", "rain_prob": "0%", "wind": "10 km/h", "temp": "20C"}
                for h in range(24)
            ],
        }

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_perfect_day_go_verdict(self, mock_mud, mock_weather, mock_weather_data):
        mock_weather.return_value = mock_weather_data
        mock_mud.return_value = {
            "status": "Success",
            "tactical_analysis": {"mud_risk_numeric": 0.0},
            "metadata": {"model_confidence": "low"},
        }

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2, surface_type="asphalt")

        assert result["status"] == "Success"
        assert result["planner_report"]["verdict"] == "GO"
        assert result["planner_report"]["tactical_color"] == "GREEN"
        mock_mud.assert_called_once_with(41.9, 12.4, "asphalt", target_date=None)

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_night_ride_no_go(self, mock_mud, mock_weather, mock_weather_data):
        mock_weather.return_value = mock_weather_data
        mock_mud.return_value = {
            "status": "Success",
            "tactical_analysis": {"mud_risk_numeric": 0.0},
        }

        result = calculate_ride_windows(45.0, 9.0, ride_duration_hours=12, target_date="2026-12-21")

        assert result["planner_report"]["verdict"] == "NO-GO"
        assert "No safe daylight" in result["planner_report"]["environmental_briefing"]["message"]

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_extreme_weather_penalties(self, mock_mud, mock_weather):
        mock_weather.return_value = {
            "status": "Success",
            "tactical_forecast": [
                {"time": f"{h:02d}:00", "rain_prob": 90, "wind": 50, "temp": 2} for h in range(24)
            ],
        }
        mock_mud.return_value = {
            "status": "Success",
            "tactical_analysis": {"mud_risk_numeric": 20.0},
        }

        result = calculate_ride_windows(45.0, 9.0, ride_duration_hours=2, surface_type="dirt")

        assert result["planner_report"]["tactical_color"] == "RED"
        assert result["planner_report"]["verdict"] == "NO-GO"
        assert result["planner_report"]["mud_risk_impact"] == "20.0mm"

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_mud_penalty_is_applied(self, mock_mud, mock_weather, mock_weather_data):
        mock_weather.return_value = mock_weather_data
        mock_mud.return_value = {
            "status": "Success",
            "tactical_analysis": {"mud_risk_numeric": 80.0},
        }

        result = calculate_ride_windows(45.0, 9.0, ride_duration_hours=2, surface_type="dirt")

        assert result["planner_report"]["verdict"] == "CAUTION"
        assert result["planner_report"]["mud_risk_impact"] == "80.0mm"

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_mud_error_downgrades_go_to_caution(self, mock_mud, mock_weather, mock_weather_data):
        mock_weather.return_value = mock_weather_data
        mock_mud.return_value = {"status": "Error", "message": "mud unavailable"}

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2, surface_type="dirt")

        assert result["planner_report"]["verdict"] == "CAUTION"
        assert result["planner_report"]["mud_risk_impact"] == "Unavailable"
        assert result["planner_report"]["environmental_briefing"]["mud_available"] is False

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    def test_weather_error_returns_actionable_error(self, mock_weather):
        mock_weather.return_value = {"status": "Error", "message": "provider down"}

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2)

        assert result["status"] == "Error"
        assert "Weather forecast unavailable" in result["message"]
        assert result["next_step"]

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_duration_is_rounded_up(self, mock_mud, mock_weather, mock_weather_data):
        mock_weather.return_value = mock_weather_data
        mock_mud.return_value = {
            "status": "Success",
            "tactical_analysis": {"mud_risk_numeric": 0.0},
        }

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2.5, surface_type="asphalt")

        assert result["status"] == "Success"
        assert result["metadata"]["requested_duration_hours"] == 2.5
        # 2.5h should require 3 hourly slots, so window spans 2 hours difference in labels.
        start, end = result["planner_report"]["best_window"].split(" - ")
        assert int(end.split(":")[0]) - int(start.split(":")[0]) == 2

    def test_duration_slots_helper(self):
        assert _duration_slots(2.5, 24) == 3
        assert _duration_slots(0, 24) == 1
        assert _duration_slots(99, 5) == 5

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
        mock_mud.return_value = {
            "status": "Success",
            "tactical_analysis": {"mud_risk_numeric": 0.0},
        }

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2, surface_type="asphalt")

        assert result["status"] == "Success"
        assert result["metadata"]["solar_window"] == "7:00 - 18:00"

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_malformed_forecast_hour_skips(self, mock_mud, mock_weather):
        malformed_forecast = {
            "tactical_forecast": [
                {"time": "ORARIO_NON_VALIDO", "rain_prob": 0, "wind": 10, "temp": 20},
                {"time": "12:00", "rain_prob": 0, "wind": 10, "temp": 20},
                {"time": "13:00", "rain_prob": 0, "wind": 10, "temp": 20},
            ]
        }
        mock_weather.return_value = malformed_forecast
        mock_mud.return_value = {"tactical_analysis": {"mud_risk_numeric": 0.0}}

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2, surface_type="asphalt")

        assert result["status"] == "Success"
        assert result["planner_report"]["best_window"] == "12:00 - 13:00"

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_scoring_extreme_cold(self, mock_mud, mock_weather):
        freezing_weather = {
            "tactical_forecast": [
                {"time": f"{h:02d}:00", "rain_prob": 0, "wind": 10, "temp": -5} for h in range(24)
            ]
        }
        mock_weather.return_value = freezing_weather
        mock_mud.return_value = {"tactical_analysis": {"mud_risk_numeric": 0.0}}

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2, surface_type="asphalt")

        assert result["status"] == "Success"
        assert result["planner_report"]["tactical_color"] in ["YELLOW", "RED"]

    @patch("bikescout.tools.gonogo.get_weather_forecast")
    @patch("bikescout.tools.gonogo.get_mud_risk_analysis")
    def test_scoring_extreme_heat(self, mock_mud, mock_weather):
        scorching_weather = {
            "tactical_forecast": [
                {"time": f"{h:02d}:00", "rain_prob": 0, "wind": 10, "temp": 38} for h in range(24)
            ]
        }
        mock_weather.return_value = scorching_weather
        mock_mud.return_value = {"tactical_analysis": {"mud_risk_numeric": 0.0}}

        result = calculate_ride_windows(41.9, 12.4, ride_duration_hours=2, surface_type="asphalt")

        assert result["status"] == "Success"
        assert result["planner_report"]["tactical_color"] in ["YELLOW", "RED"]

    def test_calculate_ride_windows_global_exception(self):
        result = calculate_ride_windows(41.9, 12.4, target_date="not-a-valid-date-string")

        assert result["status"] == "Error"
        assert "Tactical Planner failed" in result["message"]
