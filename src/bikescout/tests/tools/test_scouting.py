from unittest.mock import patch, MagicMock
from bikescout.tools.scouting import calculate_detailed_difficulty, generate_tactical_gpx, get_complete_trail_scout, calculate_performance_metrics

class TestMasterOrchestrator:

    def test_difficulty_grading(self):
        assert "Expert" in calculate_detailed_difficulty(10, 1000)
        assert "Beginner" in calculate_detailed_difficulty(5, 50)

    def test_gpx_elevation_healing(self):
        bad_coords = [[9.0, 45.0, 100.0], [9.1, 45.1, 105.0], [9.2, 45.2, 0.0], [9.3, 45.3, 110.0]]

        with patch("builtins.open", MagicMock()):
            report = generate_tactical_gpx("test_uuid", bad_coords)

        assert report["status"] == "Success"
        assert report["tactical_stats"]["healed_points"] == 1

    @patch("bikescout.tools.scouting.requests.post")
    def test_complete_scout_fallback(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "features": [{
                "geometry": {"coordinates": [[9.0, 45.0, 100], [9.1, 45.1, 200]]},
                "properties": {
                    "summary": {"distance": 50000}, # 50km
                    "ascent": 1200
                }
            }]
        }

        m_rider = MagicMock()
        m_rider.weight_kg = 70.0
        m_rider.fitness_level = "pro"
        m_rider.gender = "M"
        m_rider.sweat_profile = "normal"

        m_bike = MagicMock()
        m_bike.bike_type = "road"
        m_bike.is_ebike = False

        m_mission = MagicMock()
        m_mission.total_length_km = 50.0
        m_mission.profile = "cycling-road"
        m_mission.seed = 42

        with patch("bikescout.tools.scouting.get_weather_forecast", side_effect=Exception("Weather Down")):
            with patch("bikescout.tools.scouting.get_surface_analyzer") as mock_surface:
                mock_surface.return_value = {"status": "Error", "message": "Surface service down"}

                result = get_complete_trail_scout("api_key", 45.0, 9.0, m_rider, m_bike, m_mission,
                                                  include_weather=True, include_gpx=False)

        assert result["status"] == "Success", f"Errore rilevato: {result.get('error_message')}"
        assert result["info"]["distance_km"] == 50.0

    @patch("bikescout.tools.scouting.requests.post")
    @patch("bikescout.tools.scouting.get_weather_forecast")
    @patch("bikescout.tools.scouting.get_surface_analyzer")
    @patch("bikescout.tools.scouting.get_mud_risk_analysis")
    @patch("bikescout.tools.scouting.get_nutrition_plan")
    @patch("bikescout.tools.scouting.generate_tactical_gpx")
    @patch("bikescout.tools.scouting.get_elevation_profile_image")
    def test_complete_scout_full_integration(self, m_alt, m_gpx, m_nut, m_mud, m_surf, m_weath, m_post):

        # Setup Mock ORS
        m_post.return_value.status_code = 200
        m_post.return_value.json.return_value = {
            "features": [{
                "geometry": {"coordinates": [[9,45,100], [9.1,45.1,200]]},
                "properties": {"summary": {"distance": 10000}, "ascent": 500}
            }]
        }

        m_weath.return_value = {
            "status": "Success",
            "tactical_forecast": [{"temp": "22°C", "condition": "Sunny"}],
            "reference_conditions": {"temp_actual": 22.0}
        }
        m_surf.return_value = {"status": "Success", "tactical_briefing": {"distance_km": 10, "elevation_gain_m": 500}}
        m_mud.return_value = {"status": "Success", "risk_level": "Low"}
        m_nut.return_value = {"status": "Success", "plan": "2 gels per hour"}
        m_gpx.return_value = {"status": "Success", "file_location": "/tmp/test.gpx", "mcp_resource_uri": "..."}
        m_alt.return_value = {"status": "Success", "file_location": "/tmp/test.png", "mcp_resource_uri": "..."}

        rider = MagicMock(weight_kg=75, fitness_level="intermediate", gender="M", sweat_profile="high")
        bike = MagicMock(bike_type="gravel", is_ebike=True, battery_wh=500)
        mission = MagicMock(total_length_km=10, profile="cycling-gravel", seed=123)

        result = get_complete_trail_scout(
            "key", 45.0, 9.0, rider, bike, mission,
            include_weather=True,
            include_mud_analysis=True,
            include_nutrition_plan=True,
            include_gpx=True,
            include_altimetry=True,
            include_poi=True
        )

        assert result["status"] == "Success"
        assert "nutrition_plan" in result["logistics"]
        assert "gpx_export_path" in result

    @patch("bikescout.tools.scouting.requests.post")
    def test_scouting_a_to_b_and_edge_cases(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "features": [{
                "geometry": {"coordinates": [[9,45,100], [10,46,200]]},
                "properties": {"summary": {"distance": 100000}, "ascent": 2000}
            }]
        }

        m_rider = MagicMock(weight_kg=80, fitness_level="intermediate", gender="M", sweat_profile="low")
        m_bike = MagicMock(bike_type="mtb", is_ebike=False)
        m_mission = MagicMock(total_length_km=100, profile="cycling-mountain", seed=999)

        result = get_complete_trail_scout(
            "key", 45.0, 9.0, m_rider, m_bike, m_mission,
            dest_latitude=46.0, dest_longitude=10.0, # Trigger A -> B logic
            include_weather=True
        )

        assert result["info"]["route_type"] == "A to B"
        assert result["status"] == "Success"

    def test_performance_metrics_extremes(self):

        m_rider_pro = MagicMock(fitness_level="pro")
        m_bike_alien = MagicMock(bike_type="unicycle", is_ebike=False)

        perf = calculate_performance_metrics(100, 2000, m_rider_pro, m_bike_alien)

        assert perf["applied_vam"] == 1000.0
        assert perf["applied_base_speed"] == 16.0

    @patch("bikescout.tools.scouting.requests.post")
    @patch("bikescout.tools.scouting.get_weather_forecast")
    @patch("bikescout.tools.scouting.get_surface_analyzer")
    @patch("bikescout.tools.scouting.get_poi_scout")
    @patch("bikescout.tools.scouting.generate_tactical_gpx")
    @patch("bikescout.tools.scouting.get_elevation_profile_image")
    @patch("bikescout.tools.scouting.save_local_tactical_map")
    def test_scouting_ultimate_coverage(self, m_map, m_alt, m_gpx, m_poi, m_surf, m_weath, m_post):
        m_post.return_value.status_code = 200
        m_post.return_value.json.return_value = {
            "features": [{
                "geometry": {"coordinates": [[9,45,100], [10,46,200]]},
                "properties": {"summary": {"distance": 65000}, "ascent": 1500}
            }]
        }

        m_weath.return_value = {
            "status": "Success",
            "tactical_forecast": [{"temp": " 28.5 °C ", "condition": "Hot"}], # Spazi e °C per il .strip().replace()
            "reference_conditions": {"temp_actual": 28.5},
            "safety_advice": "Stay hydrated"
        }

        m_surf.return_value = {"status": "Success", "tactical_briefing": {"distance_km": 65, "elevation_gain_m": 1500}}
        m_poi.return_value = {"status": "Success", "amenities": [{"name": "Fountain", "location": {"lat": 45.1, "lon": 9.1}}]}
        m_gpx.return_value = {"status": "Success", "file_location": "/tmp/test.gpx", "mcp_resource_uri": "uri://gpx"}
        m_alt.return_value = {"status": "Success", "file_location": "/tmp/test.png", "mcp_resource_uri": "uri://alt"}
        m_map.return_value = {"status": "Success", "file_location": "/tmp/map.html", "mcp_resource_uri": "uri://map"}

        rider = MagicMock(weight_kg=70, fitness_level="pro", gender="F", sweat_profile="high")
        bike = MagicMock(bike_type="alien_bike", is_ebike=True)
        mission = MagicMock(total_length_km=65, profile="cycling-road", seed=1)

        result = get_complete_trail_scout(
            "key", 45.0, 9.0, rider, bike, mission,
            dest_latitude=46.0, dest_longitude=10.0, 
            include_weather=True, include_gpx=True, include_altimetry=True,
            include_map=True, include_poi=True
        )

        assert result["status"] == "Success"
        assert "gpx_export_path" in result
        assert "elevation_profile_path" in result
        assert result["info"]["route_type"] == "A to B"