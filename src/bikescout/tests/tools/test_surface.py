from unittest.mock import patch, MagicMock
from bikescout.tools.surface import _categorize_climb, get_surface_analyzer, _sanitize_elevation_profile, _categorize_climb

class MockObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class TestSurfaceTactics:

    def test_elevation_sanitization(self):
        noisy_geometry = [[0,0,100.1], [0,0,100.2], [0,0,100.1], [0,0,100.3]] * 5
        ascent = _sanitize_elevation_profile(noisy_geometry)
        assert ascent == 0.0

        climb_geometry = [[0,0,100], [0,0,110], [0,0,120], [0,0,130], [0,0,140], [0,0,150], [0,0,170]]
        ascent_real = _sanitize_elevation_profile(climb_geometry, window_size=2)

        assert ascent_real >= 50.0
        assert ascent_real == 55.0

    def test_climb_categorization_enduro(self):
        cat_road, _ = _categorize_climb(500, 10000, "road")
        cat_enduro, _ = _categorize_climb(500, 10000, "enduro")

        assert "Enduro Tech" in cat_enduro
        assert "Category 1" in cat_enduro or "HC" in cat_enduro

    @patch("bikescout.tools.surface.requests.post")
    @patch("bikescout.tools.surface.get_mud_risk_analysis")
    @patch("bikescout.tools.surface.analyze_compatibility")
    def test_get_surface_analyzer_success(self, mock_compat, mock_mud, mock_post):

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "features": [{
                "properties": {
                    "extras": {
                        "surface": {
                            "summary": [{"value": 1, "distance": 1000, "amount": 100.0}],
                            "values": [[0, 10, 1]]
                        }
                    }
                },
                "geometry": {
                    "coordinates": [[9.0, 45.0, 100], [9.1, 45.1, 200], [9.2, 45.2, 300]]
                }
            }]
        }

        mock_compat.return_value = (
            {"Asphalt": 100.0}, # breakdown
            ["Safe route"],      # warnings
            True                # compatible
        )

        mock_mud.return_value = {
            "tactical_analysis": {"mud_risk_numeric": 0.1, "mud_risk_score": "Dry"},
            "metadata": {"target_date": "2026-05-08"}
        }

        rider = MockObj(weight_kg=80.0, fitness_level="intermediate")
        bike = MockObj(bike_type="Road", tire_size="700c", battery_wh=0, tire_width_mm=28)
        mission = MockObj(total_length_km=5.0, profile="cycling-road", complexity=10, seed=42, surface_preference="neutral")

        result = get_surface_analyzer("key", 45.0, 9.0, rider, bike, mission)


        assert result["status"] == "Success"
        assert result["surface_breakdown"]["Asphalt"] == 100.0

    def test_climb_categorization_flat(self):
        cat, grad = _categorize_climb(total_ascent=20, total_dist_m=5000, bike_type="Road")
        assert cat == "Flat / Rolling"

    @patch("bikescout.tools.surface.requests.post")
    def test_surface_analyzer_fallback_mechanism(self, mock_post):
        resp_fail = MagicMock(status_code=400, text="Invalid Profile")
        resp_success = MagicMock(status_code=200)
        resp_success.json.return_value = {
            "features": [{
                "properties": {"extras": {"surface": {"summary": [{"value": 1, "distance": 500, "amount": 100}]}}},
                "geometry": {"coordinates": [[9,45,100], [9.1,45.1,110]]}
            }]
        }
        mock_post.side_effect = [resp_fail, resp_success]

        m_rider = MagicMock(weight_kg=75, fitness_level="intermediate")
        m_bike = MagicMock(bike_type="Gravel", tire_size="700c", battery_wh=0, tire_width_mm=40)
        m_mission = MagicMock(total_length_km=5, profile="cycling-regular", complexity=10)

        result = get_surface_analyzer("key", 45.0, 9.0, m_rider, m_bike, m_mission)

        assert result["status"] == "Success"
        assert result["profile_used"] == "cycling-regular"

    def test_elevation_sanitization_downhill_and_reversal(self):
        valley_geometry = [
            [0,0,200], [0,0,190], [0,0,150], [0,0,100],
            [0,0,101], [0,0,120], [0,0,160]
        ]
        ascent = _sanitize_elevation_profile(valley_geometry, window_size=2, threshold=0.5)
        assert ascent > 0.0

    def test_climb_categorization_all_categories(self):

        # 1. Hors Catégorie (HC) -> adjusted_score >= 800 or total_ascent > 1000
        cat_hc, _ = _categorize_climb(total_ascent=1100, total_dist_m=10000, bike_type="road")
        assert "Hors Cat" in cat_hc

        cat_c1, _ = _categorize_climb(total_ascent=350, total_dist_m=4000, bike_type="road")
        assert "C1" in cat_c1

        cat_c2, _ = _categorize_climb(total_ascent=230, total_dist_m=3000, bike_type="road")
        assert "C2" in cat_c2

        cat_c3, _ = _categorize_climb(total_ascent=150, total_dist_m=2500, bike_type="road")
        assert "C3" in cat_c3

        cat_c4, _ = _categorize_climb(total_ascent=60, total_dist_m=5000, bike_type="road")
        assert "C4" in cat_c4

    @patch("bikescout.tools.surface.requests.post")
    def test_get_surface_analyzer_total_failure_and_invalid_json(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error Raw Text"
        mock_resp.json.side_effect = ValueError("Not a JSON")
        mock_post.return_value = mock_resp

        rider = MockObj(weight_kg=80.0, fitness_level="intermediate")
        bike = MockObj(bike_type="Road", tire_size="700c", battery_wh=0, tire_width_mm=28)
        mission = MockObj(total_length_km=5.0, profile="cycling-road", complexity=10, seed=42, surface_preference="neutral")

        result = get_surface_analyzer("key", 45.0, 9.0, rider, bike, mission)

        assert result["status"] == "Error"
        assert "Global failure" in result["message"]
        assert "ORS 500" in result["message"]

    @patch("bikescout.tools.surface.requests.post")
    @patch("bikescout.tools.surface.get_mud_risk_analysis")
    @patch("bikescout.tools.surface.analyze_compatibility")
    @patch("bikescout.tools.surface.calculate_battery_drain")
    def test_surface_analyzer_malformed_breakdown_and_emtb_exception(
            self, mock_drain, mock_compat, mock_mud, mock_post
    ):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "features": [{
                "properties": {"extras": {"surface": {"summary": [{"value": 1, "distance": 1000}]}}},
                "geometry": {"coordinates": [[9.0, 45.0, 100], [9.1, 45.1, 100]]}
            }]
        }
        mock_mud.return_value = {
            "tactical_analysis": {"mud_risk_numeric": 0.1, "mud_risk_score": "Dry"},
            "metadata": {"target_date": "2026-05-08"}
        }

        malformed_breakdown = [{"missing_type_key": "Asphalt", "percentage": "100%"}]
        mock_compat.return_value = (malformed_breakdown, [], True)

        mock_drain.side_effect = RuntimeError("Battery simulation exploded")

        rider = MockObj(weight_kg=80.0, fitness_level="intermediate")
        bike = MockObj(bike_type="E-MTB", tire_size="29", battery_wh=625, tire_width_mm=60)
        mission = MockObj(total_length_km=5.0, profile="cycling-mountain", complexity=10, seed=42, surface_preference="neutral", assist_mode="Trail")

        result = get_surface_analyzer("key", 45.0, 9.0, rider, bike, mission)

        assert result["status"] == "Success"
        assert result["emtb_tactical"] == {"error": "Battery calculation failed"}

    @patch("bikescout.tools.surface.requests.post")
    def test_surface_analyzer_json_error_and_global_exception(self, mock_post):
        resp_json_error = MagicMock()
        resp_json_error.status_code = 400
        resp_json_error.json.return_value = {"error": {"message": "Invalid coordinates format"}}

        side_effects = [resp_json_error, RuntimeError("Connection dropped abruptly")]
        mock_post.side_effect = side_effects

        rider = MockObj(weight_kg=75.0, fitness_level="beginner")
        bike = MockObj(bike_type="Gravel", tire_size="700c", battery_wh=0, tire_width_mm=38)
        mission = MockObj(total_length_km=10.0, profile="cycling-mountain", complexity=10, seed=42, surface_preference="neutral")

        result = get_surface_analyzer("dummy_key", 45.0, 9.0, rider, bike, mission)

        assert result["status"] == "Error"
        assert "Global failure" in result["message"]
        assert "Connection dropped abruptly" in result["message"]

    @patch("bikescout.tools.surface.requests.post")
    @patch("bikescout.tools.surface.get_mud_risk_analysis")
    @patch("bikescout.tools.surface.analyze_compatibility")
    def test_surface_analyzer_text_fallback_and_exhaustion(self, mock_compat, mock_mud, mock_post):
        resp_json_error = MagicMock()
        resp_json_error.status_code = 400
        resp_json_error.json.return_value = {"error": {"message": "Invalid coordinates"}}

        resp_text_only = MagicMock()
        resp_text_only.status_code = 502
        resp_text_only.text = "Bad Gateway"
        resp_text_only.json.side_effect = ValueError("Not a JSON")

        mock_post.side_effect = [resp_json_error, resp_text_only]

        mock_mud.return_value = {
            "tactical_analysis": {"mud_risk_numeric": 0.0, "mud_risk_score": "Dry"},
            "metadata": {"target_date": "2026-05-30"}
        }
        mock_compat.return_value = ({}, [], True)

        rider = MockObj(weight_kg=75.0, fitness_level="beginner")
        bike = MockObj(bike_type="Gravel", tire_size="700c", battery_wh=0, tire_width_mm=38)

        mission = MockObj(
            total_length_km=5.0,
            profile="cycling-mountain",
            complexity=10,
            seed=42,
            surface_preference="neutral"
        )

        result = get_surface_analyzer("dummy_key", 45.0, 9.0, rider, bike, mission)

        assert result["status"] == "Error"
        assert "ORS 502: Bad Gateway" in result["message"]