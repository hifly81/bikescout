import pytest
import requests
from unittest.mock import patch, MagicMock
from bikescout.tools.poi import get_poi_scout_free, get_poi_scout

class TestPOIs:

    @pytest.fixture
    def mock_overpass_data(self):
        return {
            "elements": [
                {
                    "id": 1, "lat": 45.0, "lon": 9.0,
                    "tags": {"amenity": "drinking_water", "name": "Fontanella Alpina"}
                },
                {
                    "id": 2, "lat": 45.1, "lon": 9.1,
                    "tags": {"shop": "bicycle", "operator": "Cicli Rossi"}
                }
            ]
        }

    @patch("requests.post")
    def test_overpass_tactical_labels(self, mock_post, mock_overpass_data):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_overpass_data

        result = get_poi_scout_free(45.0, 9.0, total_length_km=5)

        assert result["status"] == "Success"
        assert result["total_found"] == 2
        assert result["amenities"][0]["type"] == "Water Fountain 💧"
        assert result["amenities"][1]["type"] == "Bike Support 🔧"

    @patch("requests.post")
    def test_ors_buffer_clamping(self, mock_post):
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {"features": []}

        get_poi_scout("fake_key", 45.0, 9.0, total_length_km=10.0)

        called_args, called_kwargs = mock_post.call_args
        assert called_kwargs["json"]["geometry"]["buffer"] == 2000

    @patch("requests.post")
    def test_overpass_server_busy_handling(self, mock_post):
        mock_post.return_value.status_code = 429

        result = get_poi_scout_free(45.0, 9.0, total_length_km=1)

        assert result["status"] == "Error"
        assert "Overpass server busy" in result["message"]

    def test_ors_geojson_format(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {"features": []}

            get_poi_scout("key", lat=45.5, lon=9.2, total_length_km=1)

            coords = mock_post.call_args[1]["json"]["geometry"]["geojson"]["coordinates"]
            assert coords == [9.2, 45.5]

    @patch("requests.post")
    def test_overpass_generic_poi_label(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "elements": [{
                "id": 99, "lat": 1.0, "lon": 1.0,
                "tags": {"tourism": "viewpoint"}
            }]
        }
        result = get_poi_scout_free(1.0, 1.0, 1.0)
        assert result["amenities"][0]["type"] == "Point of Interest"

    @patch("requests.post")
    def test_overpass_critical_exception(self, mock_post):
        mock_post.side_effect = Exception("Connection Interrupted")
        result = get_poi_scout_free(1.0, 1.0, 1.0)
        assert result["status"] == "Error"
        assert "Connection Interrupted" in result["message"]

    @patch("requests.post")
    def test_ors_api_error_response(self, mock_post):
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = 401
        mock_post.return_value.text = "Unauthorized"

        result = get_poi_scout("bad_key", 1.0, 1.0, 1.0)
        assert result["status"] == "Error"
        assert "401" in result["message"]

    @patch("requests.post")
    def test_ors_various_category_labels(self, mock_post):
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {
            "features": [
                {
                    "properties": {"category_ids": {"331": {}}, "distance": 100},
                    "geometry": {"coordinates": [9.0, 45.0]}
                },
                {
                    "properties": {"category_ids": {"999": {}}, "distance": 200},
                    "geometry": {"coordinates": [9.1, 45.1]}
                }
            ]
        }
        result = get_poi_scout("key", 45.0, 9.0, 1.0)
        # 331 -> Rest Area
        assert result["amenities"][0]["type"] == "Rest Area 🧺"
        # 999 -> Point of Interest
        assert result["amenities"][1]["type"] == "Point of Interest"

    @patch("requests.post")
    def test_ors_internal_engine_failure(self, mock_post):
        mock_post.return_value.ok = True
        mock_post.return_value.json.side_effect = ValueError("Malformed JSON")

        result = get_poi_scout("key", 1.0, 1.0, 1.0)
        assert result["status"] == "Error"
        assert "Internal Engine failure" in result["message"]

    @patch("requests.post")
    def test_overpass_rest_area_labels(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "elements": [
                {
                    "id": 10, "lat": 45.0, "lon": 9.0,
                    "tags": {"amenity": "shelter", "name": "Bivacco"}
                },
                {
                    "id": 11, "lat": 45.1, "lon": 9.1,
                    "tags": {"leisure": "picnic_table"}
                }
            ]
        }

        result = get_poi_scout_free(45.0, 9.0, total_length_km=5)

        assert result["status"] == "Success"
        assert result["amenities"][0]["type"] == "Rest Area 🧺"
        assert result["amenities"][1]["type"] == "Rest Area 🧺"

    @patch("requests.post")
    def test_ors_critical_exception_handling(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError("Network down")

        result = get_poi_scout("key", 45.0, 9.0, 1.0)

        assert result["status"] == "Error"
        assert "Internal Engine failure" in result["message"]
        assert "Network down" in result["message"]
