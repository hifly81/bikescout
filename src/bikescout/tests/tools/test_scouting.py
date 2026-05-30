from unittest.mock import patch, MagicMock
import requests
from bikescout.tools.scouting import calculate_detailed_difficulty, generate_tactical_gpx, get_complete_trail_scout, calculate_performance_metrics, _map_surface_id

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

    def test_gpx_generation_edge_cases_and_anomalies(self):
        # Test GPX with an Object containing a .coordinates attribute (Line 55)
        mock_geo = MagicMock()
        mock_geo.coordinates = [[9.0, 45.0, 100.0], [9.1, 45.1, 105.0]]
        with patch("builtins.open", MagicMock()):
            res_attr = generate_tactical_gpx("attr_test", mock_geo)
        assert res_attr["status"] == "Success"

        # Generate 30 points spaced far enough apart to satisfy dist > 60
        steep_coords = []
        for i in range(30):
            # 0.001 degrees of latitude is roughly 111 meters (satisfying dist > 60)
            lat = 45.0 + (i * 0.002)
            lon = 9.0
            # Elevate steadily to create a steep grade between 10% and 45%
            ele = 100.0 + (i * 30.0)
            steep_coords.append([lon, lat, ele])

        with patch("builtins.open", MagicMock()):
            res_steep = generate_tactical_gpx("steep_test", steep_coords)

        assert res_steep["status"] == "Success"
        assert res_steep["tactical_stats"]["waypoints_count"] > 0

    @patch("bikescout.tools.scouting.requests.post")
    def test_surface_breakdown_fallbacks(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "features": [{"geometry": {"coordinates": [[9,45,100], [9.1,45.1,200]]}, "properties": {"summary": {"distance": 5000}, "ascent": 200}}]
        }

        m_rider = MagicMock(weight_kg=70, fitness_level="intermediate", gender="M", sweat_profile="normal")
        m_bike = MagicMock(bike_type="gravel", is_ebike=False)
        m_mission = MagicMock(total_length_km=5, profile="cycling-gravel", seed=42)

        # Force ValueError boundary by providing an unparseable item inside the collection
        with patch("bikescout.tools.scouting.get_surface_analyzer") as mock_surface:
            mock_surface.return_value = {
                "status": "Success",
                "tactical_briefing": {"distance_km": 5, "elevation_gain_m": 200},
                "info": {
                    "surface_analysis": {
                        # Elements present, but entry string forces lambda conversion crash
                        "surface_breakdown": [{"type": "gravel", "percentage": "broken_value"}]
                    }
                }
            }

            result = get_complete_trail_scout("key", 45.0, 9.0, m_rider, m_bike, m_mission, include_gpx=False)
            assert result["info"]["surface_analysis"]["status"] == "Success"

    @patch("bikescout.tools.scouting.requests.post")
    @patch("bikescout.tools.scouting.get_weather_forecast")
    def test_weather_empty_forecast_and_poi_free(self, m_weath, m_post):
        m_post.return_value.status_code = 200
        m_post.return_value.json.return_value = {
            "features": [{"geometry": {"coordinates": [[9,45,100], [9.1,45.1,200]]}, "properties": {"summary": {"distance": 1000}, "ascent": 10}}]
        }

        m_weath.return_value = {
            "status": "Success",
            "tactical_forecast": [],
            "reference_conditions": {"temp_max": 15.0}
        }

        rider = MagicMock(weight_kg=60, fitness_level="beginner", gender="F", sweat_profile="normal")
        bike = MagicMock(bike_type="mtb", is_ebike=False)
        mission = MagicMock(total_length_km=1, profile="cycling-mountain", seed=1)

        with patch("bikescout.tools.scouting.get_poi_scout_free") as m_poi_free:
            m_poi_free.return_value = {"status": "Success", "amenities": []}

            result = get_complete_trail_scout("", 45.0, 9.0, rider, bike, mission,
                                              include_weather=True, include_poi=True, include_gpx=False)

            assert result["status"] == "Success"
            m_poi_free.assert_called_once()

    @patch("bikescout.tools.scouting.requests.post")
    def test_master_orchestrator_subservice_failures(self, mock_post):
        # Setup valid mapping configuration to parse payload safely up until subservices
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "features": [{
                "geometry": {"coordinates": [[9,45,100], [9.1,45.1,200]]},
                "properties": {"summary": {"distance": 5000}, "ascent": 100}
            }]
        }

        rider = MagicMock(weight_kg=70, fitness_level="intermediate", gender="M", sweat_profile="normal")
        bike = MagicMock(bike_type="road", is_ebike=False)
        mission = MagicMock(total_length_km=5, profile="cycling-road", seed=1)

        # 1. Test handled sub-service exceptions (GPX & Altimetry)
        # include_map is set to False because save_local_tactical_map lacks an internal try/except block
        with patch("bikescout.tools.scouting.generate_tactical_gpx", side_effect=Exception("GPX Writer Crash")), \
                patch("bikescout.tools.scouting.get_elevation_profile_image", side_effect=Exception("Altimetry Engine Crash")):

            result = get_complete_trail_scout(
                "key", 45.0, 9.0, rider, bike, mission,
                include_map=False, include_gpx=True, include_altimetry=True
            )

            # Verify orchestrator survived the safe sub-service failures
            assert result["status"] == "Success"
            assert "gpx_error" in result
            assert "elevation_error" in result

        # 2. Force the global orchestrator routing exception block
        mock_post.side_effect = requests.exceptions.Timeout("Connection Timed Out")
        err_result = get_complete_trail_scout("key", 45.0, 9.0, rider, bike, mission)

        assert err_result["status"] == "Error"
        assert "Master Orchestrator failed" in err_result["error_message"]

    def test_surface_id_mapping_and_gpx_writer_exceptions(self):
        assert _map_surface_id(999) == "dirt"
        assert _map_surface_id(1) == "asphalt"

        malformed_report = generate_tactical_gpx("break", None)
        assert malformed_report["status"] == "Error"
        assert "GPX Generation failed" in malformed_report["message"]

    def test_isolated_utility_and_gpx_branches(self):
        assert calculate_detailed_difficulty(0, 500) == "Unknown"

        assert _map_surface_id(999) == "dirt"
        mock_geojson_dict = {
            "features": [{
                "geometry": {
                    "coordinates": [[9.0, 45.0, 100.0], [9.001, 45.001, 102.0]]
                }
            }]
        }
        with patch("builtins.open", MagicMock()):
            res_dict = generate_tactical_gpx("geojson_dict_test", mock_geojson_dict)
        assert res_dict["status"] == "Success"

        # Needs > 60 total points so that the index math loops cleanly past last_wall_index trackers
        wall_coords = []
        for i in range(80):
            # 0.002 degrees latitude handles the dist > 60 meters check easily
            lat = 45.0 + (i * 0.002)
            lon = 9.0
            # Climbing 25 meters every point ensures an acceptable grade (~11%) inside the 10-45% window
            ele = 100.0 + (i * 25.0)
            wall_coords.append([lon, lat, ele])

        with patch("builtins.open", MagicMock()):
            res_walls = generate_tactical_gpx("wall_test", wall_coords)
        assert res_walls["status"] == "Success"
        assert res_walls["tactical_stats"]["waypoints_count"] > 0

    @patch("bikescout.tools.scouting.requests.post")
    def test_orchestrator_routing_and_subservice_bounds(self, mock_post):
        # Setup reusable standard mock parameter objects
        m_rider = MagicMock(weight_kg=75, fitness_level="intermediate", gender="M", sweat_profile="normal")
        m_bike = MagicMock(bike_type="gravel", is_ebike=False)
        m_mission = MagicMock(total_length_km=20, profile="cycling-gravel", seed=42)

        mock_post.side_effect = requests.exceptions.Timeout("API Connection Lost")
        err_routing = get_complete_trail_scout("key", 45.0, 9.0, m_rider, m_bike, m_mission)
        assert err_routing["status"] == "Error"
        assert "Master Orchestrator failed" in err_routing["error_message"]

        # Restore stable base behavior for the rest of the execution checks
        mock_post.side_effect = None
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "features": [{
                "geometry": {"coordinates": [[9.0, 45.0, 100.0], [9.1, 45.1, 200.0]]},
                "properties": {"summary": {"distance": 10000}, "ascent": 100}
            }]
        }

        with patch("bikescout.tools.scouting.get_poi_scout_free") as mock_poi_free:
            mock_poi_free.return_value = {"status": "Success", "amenities": []}
            # Providing an empty API string hits the free alternative branch
            get_complete_trail_scout("", 45.0, 9.0, m_rider, m_bike, m_mission, include_poi=True, include_gpx=False)
            mock_poi_free.assert_called_once()

        with patch("bikescout.tools.scouting.generate_tactical_gpx", side_effect=Exception("GPX Stream Error")):
            res_gpx_err = get_complete_trail_scout("key", 45.0, 9.0, m_rider, m_bike, m_mission, include_gpx=True)
            assert "gpx_error" in res_gpx_err

        with patch("bikescout.tools.scouting.save_local_tactical_map", side_effect=Exception("Map File Engine Failure")):
            res_fatal = get_complete_trail_scout("key", 45.0, 9.0, m_rider, m_bike, m_mission, include_map=True)
            assert res_fatal["status"] == "Error"
            assert "Master Orchestrator failed" in res_fatal["error_message"]