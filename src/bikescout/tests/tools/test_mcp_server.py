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
from unittest.mock import patch

import pytest

from bikescout.mcp_server import (
    analyze_gpx_track,
    check_trail_weather,
    geocode_location,
    hydration_scout,
    ride_window_planner,
    trail_scout,
    trail_scout_simple,
)
from bikescout.schemas import (
    BikeSetup,
    FullMissionBriefingResponse,
    MissionConstraints,
    RiderProfile,
)


class TestMcpServer:
    @patch("bikescout.mcp_server.get_coordinates")
    def test_geocode_location(self, m_geo):
        m_geo.return_value = {
            "status": "Success",
            "lat": 46.54,
            "lon": 11.67,
            "display_name": "Passo Gardena",
            "importance": 0.8,
            "place_class": "peak",
            "place_type": "mountain",
        }

        response = geocode_location("Passo Gardena")

        assert response.status == "Success"
        assert response.lat == 46.54

    @patch("bikescout.mcp_server.get_complete_trail_scout")
    @patch("bikescout.mcp_server.ORS_API_KEY", "mocked_valid_api_key")
    def test_trail_scout_simple_success(self, m_scout):
        m_scout.return_value = {
            "status": "Success",
            "info": {
                "distance_km": 30.0,
                "ascent_m": 500,
                "difficulty": "Moderate",
                "route_type": "circular",
                "surface_analysis": {
                    "mud_risk": "Low",
                    "traction_level": "High",
                    "profile_used": "cycling-mountain",
                    "metadata": {"source": "ORS"},
                    "tactical_briefing": {
                        "status": "Optimal",
                        "description": "Dry and fast conditions expected.",
                        "distance_km": 30.0,
                        "elevation_gain_m": 500.0,
                        "climb_category": "HC",
                        "avg_gradient": "5.5%",
                        "avg_climb_gradient": "7.2%",
                        "mud_intelligence": {
                            "status": "Dry",
                            "saturation_level": "None",
                            "briefing": "No saturation detected",
                            "score": 0.0,
                            "label": "Dusty",
                            "traction_risk": "Low",
                            "trail_damage_risk": "None",
                            "dry_time_eta": "0h",
                            "safety_advice": "Perfect grip",
                        },
                    },
                    "mechanical_setup": {
                        "compatible": True,
                        "setup_details": {
                            "wheel_label": '29"',
                            "tire_width_mm": 58,
                            "rim_internal_width_mm": 25,
                            "casing_type": "trail",
                            "tubeless": True,
                            "psi_front": 19.9,
                            "psi_rear": 25.4,
                            "bar_front": 1.37,
                            "bar_rear": 1.75,
                            "strategy": "Standard",
                            "load_split": {"front": 0.4, "rear": 0.6},
                            "knob_choice": "All-Terrain / Trail",
                            "tactical_display": '29" wheels | F: 19.9 PSI | R: 25.4 PSI',
                        },
                        "bike_type": "mtb",
                        "safety_warnings": [],
                    },
                    "surface_breakdown": [
                        {"type": "dirt", "percentage": "80%"},
                        {"type": "gravel", "percentage": "20%"},
                    ],
                },
            },
            "conditions": {
                "reference_conditions": {"temp": 20.0, "wind_speed": 10.0},
                "tactical_forecast": [],
                "max_temp_detected": "20.0°C",
            },
            "logistics": {
                "nutrition_plan": {
                    "status": "Success",
                    "mission_nutrition_briefing": {
                        "fluids": {"ml_per_hour": 500},
                        "carbohydrates": {"grams_per_hour": 60},
                        "electrolytes": {"tablets_per_hour": 1},
                        "tactical_advice": ["Drink often"],
                    },
                },
                "water_points": [],
            },
            "gpx_stats": {"points": 150, "healed_segments": 0},
            "map_path": "map.png",
            "gpx_export_path": "route.gpx",
            "elevation_profile_path": "profile.png",
            "mcp_resource_uri_map": "bikescout://maps/map.png",
            "mcp_resource_uri_gpx": "bikescout://gpx/route.gpx",
            "mcp_resource_uri_elevation_profile": "bikescout://altimetry/profile.png",
        }

        response = trail_scout(
            latitude=45.0,
            longitude=9.0,
            rider=cast(Any, None),
            bike=cast(Any, None),
            mission=cast(Any, None),
        )

        assert response.status == "Success"
        assert response.info is not None
        assert response.info.distance_km == 30.0

    @patch("bikescout.mcp_server.get_complete_trail_scout")
    @patch("bikescout.mcp_server.ORS_API_KEY", None)
    def test_trail_scout_missing_api_key_error(self, m_scout):

        response = trail_scout(
            latitude=45.0,
            longitude=9.0,
            rider=cast(Any, None),
            bike=cast(Any, None),
            mission=cast(Any, None),
        )

        m_scout.assert_not_called()
        assert response.status == "Error"

    @patch("bikescout.mcp_server.get_weather_forecast")
    @patch("bikescout.mcp_server.get_nutrition_plan")
    def test_hydration_scout_flow(self, m_nut, m_weather):
        m_weather.return_value = {
            "tactical_forecast": [{"temp": "28.0°C"}],
            "metadata": {"date_analyzed": "2026-06-15"},
        }

        m_nut.return_value = {
            "status": "Success",
            "mission_nutrition_briefing": {
                "fluids": {"total_ml": 1600, "ml_per_hour": 800},
                "carbohydrates": {"total_grams": 180, "grams_per_hour": 90},
                "electrolytes": {"salts_mg": 1200, "tablets_per_hour": 1},
                "tactical_advice": [
                    "Drink early and often due to 28°C heat.",
                    "Pre-hydrate with 500ml of electrolytes 1 hour before start.",
                ],
            },
        }

        response = hydration_scout(lat=45.0, lon=9.0, duration_hours=2.0)

        assert response.weather_context.max_temp_detected == "28.0°C"
        assert "Drink early" in response.mission_nutrition_briefing.tactical_advice[0]

    @patch("bikescout.mcp_server.analyze_track")
    def test_analyze_gpx_track(self, m_analyze):
        m_analyze.return_value = {
            "status": "Success",
            "mode": "ROAD",
            "target_date": "2026-05-08",
            "track_metrics": {"distance_km": 50.5, "total_ascent": 800},
            "climb_analysis": [],
            "performance_simulation": [],
            "tactical_alerts": [],
            "planning_tools": {
                "weather": {"temp": "20°C"},
                "nutrition": "Standard Plan",
                "mud_risk": "None",
            },
            "pre_climb_positioning": [],
            "tactical_action_zones": [],
            "report_path": "/tmp/race_report.pdf",
        }

        response = analyze_gpx_track(gpx_url="https://tour.com/stage1.gpx", report=True)

        assert response.status == "Success"
        assert response.track_metrics["distance_km"] == 50.5
        assert response.mode == "ROAD"

        m_analyze.assert_called_once_with(
            gpx_url="https://tour.com/stage1.gpx",
            rider_weight_kg=75,
            rider_gender="male",
            rider_fitness_level="intermediate",
            sweat_profile="standard",
            bike_weight_kg=8.5,
            pro_intensity=1.3,
            activity_type="road",
            target_date=None,
            start_hour=None,
            end_hour=None,
            report=True,
        )

    def test_trail_scout_simple_error_handling(self, capsys):
        with patch(
            "bikescout.mcp_server.RiderProfile",
            side_effect=ValueError("Validation Error"),
        ):
            response = trail_scout_simple(latitude=45.0, longitude=9.0)

        assert response.status == "Error"
        captured = capsys.readouterr()
        assert "status=Error" in captured.err
        assert "Traceback (most recent call last)" in captured.err
        assert "Validation Error" in captured.err

    @patch("bikescout.mcp_server.trail_scout")
    def test_trail_scout_simple_returns_delegated_error(self, m_trail_scout, capsys):
        m_trail_scout.return_value = FullMissionBriefingResponse.model_validate(
            {"payload_version": "1.0", "status": "Error"}
        )

        response = trail_scout_simple(latitude=45.0, longitude=9.0)

        assert response.status == "Error"
        assert capsys.readouterr().err == ""

    @patch("bikescout.mcp_server.get_complete_trail_scout")
    @patch("bikescout.mcp_server.ORS_API_KEY", "mocked_valid_api_key")
    def test_trail_scout_simple_logs_service_error_reason(self, m_scout, capsys):
        m_scout.return_value = {
            "status": "Error",
            "error_message": "Master Orchestrator failed: network down",
            "error_traceback": "Traceback (most recent call last): network down",
        }

        response = trail_scout_simple(latitude=45.0, longitude=9.0)

        assert response.status == "Error"
        captured = capsys.readouterr()
        assert "status=Error" in captured.err
        assert "Reason: Master Orchestrator failed: network down" in captured.err

    @pytest.mark.parametrize(
        ("service_target", "tool_call", "tool_name", "message"),
        [
            (
                "bikescout.mcp_server.get_coordinates",
                lambda: geocode_location("Nowhere"),
                "geocode_location",
                "Location not found.",
            ),
            (
                "bikescout.mcp_server.get_weather_forecast",
                lambda: check_trail_weather(lat=45.0, lon=9.0),
                "check_trail_weather",
                "Weather API down.",
            ),
            (
                "bikescout.mcp_server.calculate_ride_windows",
                lambda: ride_window_planner(lat=45.0, lon=9.0),
                "ride_window_planner",
                "No daylight available.",
            ),
            (
                "bikescout.mcp_server.get_weather_forecast",
                lambda: hydration_scout(lat=45.0, lon=9.0),
                "hydration_scout",
                "Weather API down.",
            ),
            (
                "bikescout.mcp_server.analyze_track",
                lambda: analyze_gpx_track(gpx_url="bad.gpx"),
                "analyze_gpx_track",
                "Invalid GPX file.",
            ),
        ],
    )
    def test_tools_log_service_error_reason(
        self, service_target, tool_call, tool_name, message, capsys
    ):
        with patch(service_target, return_value={"status": "Error", "message": message}):
            response = tool_call()

        assert response.status == "Error"
        captured = capsys.readouterr()
        assert f"{tool_name} failed with status=Error" in captured.err
        assert f"Reason: {message}" in captured.err

    @pytest.mark.parametrize(
        ("service_target", "tool_call", "tool_name"),
        [
            (
                "bikescout.mcp_server.get_coordinates",
                lambda: geocode_location("Somewhere"),
                "geocode_location",
            ),
            (
                "bikescout.mcp_server.get_weather_forecast",
                lambda: check_trail_weather(lat=45.0, lon=9.0),
                "check_trail_weather",
            ),
            (
                "bikescout.mcp_server.calculate_ride_windows",
                lambda: ride_window_planner(lat=45.0, lon=9.0),
                "ride_window_planner",
            ),
            (
                "bikescout.mcp_server.get_weather_forecast",
                lambda: hydration_scout(lat=45.0, lon=9.0),
                "hydration_scout",
            ),
            (
                "bikescout.mcp_server.analyze_track",
                lambda: analyze_gpx_track(gpx_url="bad.gpx"),
                "analyze_gpx_track",
            ),
        ],
    )
    def test_tools_log_exception_traceback(self, service_target, tool_call, tool_name, capsys):
        with patch(service_target, side_effect=RuntimeError("boom")):
            response = tool_call()

        assert response.status == "Error"
        captured = capsys.readouterr()
        assert f"{tool_name} failed with status=Error" in captured.err
        assert "Traceback (most recent call last)" in captured.err
        assert "RuntimeError: boom" in captured.err

    @patch("bikescout.mcp_server.get_complete_trail_scout")
    @patch("bikescout.mcp_server.ORS_API_KEY", "mocked_valid_api_key")
    def test_trail_scout_logs_exception_traceback(self, m_scout, capsys):
        m_scout.side_effect = RuntimeError("routing exploded")

        response = trail_scout(
            latitude=45.0,
            longitude=9.0,
            rider=RiderProfile(
                weight_kg=75.0,
                gender="male",
                fitness_level="intermediate",
                sweat_profile="standard",
            ),
            bike=BikeSetup(
                bike_type="mtb",
                tire_size="29",
                tire_width_mm=54,
                rim_internal_width_mm=25,
                casing_type="trail",
                tubeless=True,
                is_ebike=False,
                battery_wh=625,
            ),
            mission=MissionConstraints(
                total_length_km=30,
                profile="cycling-mountain",
                surface_preference="neutral",
                complexity=3,
                seed=42,
                assist_mode="Eco",
                direction_bias=[],
                avoid_urban=False,
                prefer_rural=False,
                distance_flex_percent=10,
                priority_mode="balanced",
            ),
        )

        assert response.status == "Error"
        captured = capsys.readouterr()
        assert "trail_scout failed with status=Error" in captured.err
        assert "Traceback (most recent call last)" in captured.err
        assert "RuntimeError: routing exploded" in captured.err
