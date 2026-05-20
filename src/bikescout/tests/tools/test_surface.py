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