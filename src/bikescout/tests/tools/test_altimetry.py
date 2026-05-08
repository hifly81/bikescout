import pytest
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock
from bikescout.tools.altimetry import get_elevation_profile_image, _generate_altimetry_plot
from bikescout.schemas import RouteGeometry

class TestAltimetry:

    @pytest.fixture
    def mock_geometry(self):
        return RouteGeometry(
            type="LineString",
            coordinates=[
                [9.1, 45.1, 100],
                [9.11, 45.11, 0],
                [9.12, 45.12, 500],
                [9.13, 45.13, 110]
            ]
        )

    def test_generate_altimetry_plot_styles(self, mock_geometry):
        for style in ["filled", "sparkline", "bars"]:
            img_b64 = _generate_altimetry_plot(mock_geometry.coordinates, style=style)
            assert isinstance(img_b64, str)
            assert len(img_b64) > 100

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=MagicMock)
    def test_get_elevation_profile_success(self, mock_open, mock_mkdir, mock_geometry):
        with patch.object(Path, "glob") as mock_glob:
            mock_glob.return_value = []

            result = get_elevation_profile_image(
                geometry=mock_geometry,
                uuid_input="test-uuid",
                style="bars"
            )

            assert result["status"] == "Success"
            assert "mcp_resource_uri" in result
            assert "bikescout://altimetry/" in result["mcp_resource_uri"]
            assert result["style_applied"] == "bars"
            assert result["total_distance_km"] > 0

    def test_data_healing_logic(self):
        bad_data = [
            [0, 0, 100],
            [0, 0, -10],
            [0, 0, 400]
        ]

        img = _generate_altimetry_plot(bad_data)
        assert img is not None

    def test_insufficient_geometry(self):
        short_geo = [[9.1, 45.1, 100]]
        result = _generate_altimetry_plot(short_geo)
        assert result is None