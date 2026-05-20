from unittest.mock import patch, MagicMock
from bikescout.mcp_server import geocode_location, trail_scout_simple, hydration_scout, analyze_gpx_track


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
            "place_type": "mountain"
        }

        response = geocode_location("Passo Gardena")

        assert response.status == "Success"
        assert response.lat == 46.54

    @patch("bikescout.mcp_server.get_complete_trail_scout")
    def test_trail_scout_simple(self, m_scout):
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
                            "safety_advice": "Perfect grip"
                        }
                    },
                    "mechanical_setup": {
                        "tire_pressure_psi": 25.0,
                        "compatible": True,
                        "setup_details": ["Check brakes", "Lube chain"],
                        "bike_type": "mtb"
                    },
                    "surface_breakdown": [
                        {"type": "dirt", "percentage": "80%"},
                        {"type": "gravel", "percentage": "20%"}
                    ],
                    "safety_warnings": []
                }
            },
            "conditions": {
                "reference_conditions": {"temp": 20.0, "wind_speed": 10.0},
                "tactical_forecast": [],
                "max_temp_detected": "20.0°C"
            },
            "logistics": {
                "nutrition_plan": {
                    "status": "Success",
                    "mission_nutrition_briefing": {
                        "fluids": {"ml_per_hour": 500},
                        "carbohydrates": {"grams_per_hour": 60},
                        "electrolytes": {"tablets_per_hour": 1},
                        "tactical_advice": ["Drink often"]
                    }
                },
                "water_points": []
            },
            "gpx_stats": {"points": 150, "healed_segments": 0},
            "map_path": "map.png",
            "gpx_export_path": "route.gpx",
            "elevation_profile_path": "profile.png",
            "mcp_resource_uri_map": "bikescout://maps/map.png",
            "mcp_resource_uri_gpx": "bikescout://gpx/route.gpx",
            "mcp_resource_uri_elevation_profile": "bikescout://altimetry/profile.png"
        }

        response = trail_scout_simple(
            latitude=45.0,
            longitude=9.0,
            total_length_km=30
        )

        print(response)

        assert response.status == "Success"
        assert response.info.distance_km == 30.0

    @patch("bikescout.mcp_server.get_weather_forecast")
    @patch("bikescout.mcp_server.get_nutrition_plan")
    def test_hydration_scout_flow(self, m_nut, m_weather):
        m_weather.return_value = {
            "tactical_forecast": [{"temp": "28.0°C"}],
            "metadata": {"date_analyzed": "2026-06-15"}
        }

        m_nut.return_value = {
            "status": "Success",
            "mission_nutrition_briefing": {
                "fluids": {
                    "total_ml": 1600,
                    "ml_per_hour": 800
                },
                "carbohydrates": {
                    "total_grams": 180,
                    "grams_per_hour": 90
                },
                "electrolytes": {
                    "salts_mg": 1200,
                    "tablets_per_hour": 1
                },
                "tactical_advice": [
                    "Drink early and often due to 28°C heat.",
                    "Pre-hydrate with 500ml of electrolytes 1 hour before start."
                ]
            }
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
            "track_metrics": {
                "distance_km": 50.5,
                "total_ascent": 800
            },
            "climb_analysis": [],
            "performance_simulation": [],
            "tactical_alerts": [],
            "planning_tools": {
                "weather": {"temp": "20°C"},
                "nutrition": "Standard Plan",
                "mud_risk": "None"
            },
            "pre_climb_positioning": [],
            "tactical_action_zones": [],
            "report_path": "/tmp/race_report.pdf"
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
            report=True
        )

    def test_trail_scout_simple_error_handling(self):
        with patch("bikescout.mcp_server.RiderProfile", side_effect=Exception("Validation Error")):
            response = trail_scout_simple(latitude=45.0, longitude=9.0)
            assert response.status == "Error"