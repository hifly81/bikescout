import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from bikescout.tools.maps import save_local_tactical_map, _get_gradient_color

class TestMaps:

    @pytest.fixture
    def valid_3d_geojson(self):
        """GeoJSON coordinate 3D (Lon, Lat, Ele)."""
        return {
            "features": [{
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [9.18, 45.46, 100], # Milan
                        [9.19, 45.47, 150],
                        [9.20, 45.48, 120]
                    ]
                }
            }]
        }

    @patch("staticmap.StaticMap.render")
    @patch("pathlib.Path.mkdir")
    def test_save_map_success_gradient(self, mock_mkdir, mock_render, valid_3d_geojson):
        mock_image = MagicMock()
        mock_render.return_value = mock_image

        result = save_local_tactical_map("test_route", valid_3d_geojson, use_gradient=True)

        assert result["status"] == "Success"
        assert result["style_applied"] == "gradient"

        mock_render.assert_called_once()

        mock_image.save.assert_called_once()

    def test_invalid_geojson_handling(self):
        bad_data = {"features": []}
        result = save_local_tactical_map("fail", bad_data)
        assert result["status"] == "Error"
        assert "No features found" in result["message"]

    @patch("staticmap.StaticMap.render")
    @patch("PIL.Image.Image.save")
    def test_2d_fallback(self, mock_save, mock_render):
        geojson_2d = {
            "features": [{
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[9.1, 45.1], [9.2, 45.2]]
                }
            }]
        }
        result = save_local_tactical_map("2d_test", geojson_2d, use_gradient=True)

        assert result["style_applied"] == "solid"
        assert result["status"] == "Success"

    def test_gradient_color_logic(self):
        flat = _get_gradient_color(0.0)
        steep = _get_gradient_color(15.0)

        assert flat != steep
        assert flat.startswith("#")