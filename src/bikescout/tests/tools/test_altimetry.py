import pytest
import base64
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from bikescout.tools.altimetry import get_elevation_profile_image, _generate_altimetry_plot
from bikescout.schemas import RouteGeometry

class TestAltimetry:

    @pytest.fixture
    def mock_geometry(self):
        return RouteGeometry(
            type="LineString",
            coordinates=[
                [9.1, 45.1, 100],
                [9.11, 45.11, 120],
                [9.12, 45.12, 500],
                [9.13, 45.13, 110]
            ]
        )

    def test_generate_altimetry_plot_styles(self, mock_geometry):
        for style in ["filled", "sparkline", "bars"]:
            res = _generate_altimetry_plot(mock_geometry.coordinates, style=style)
            assert res is not None
            img_b64, total_dist = res
            assert isinstance(img_b64, str)
            assert isinstance(total_dist, float)
            assert total_dist > 0

    @patch("pathlib.Path.mkdir")
    def test_get_elevation_profile_success(self, mock_mkdir):
        mock_geometry = MagicMock()
        mock_geometry.coordinates = [
            [9.0, 45.0, 100.0],
            [9.1, 45.1, 150.0],
            [9.2, 45.2, 200.0]
        ]

        with patch.object(Path, "glob") as mock_glob, \
                patch("bikescout.tools.altimetry.open", mock_open(), create=True) as m_open:

            mock_file_old = MagicMock(spec=Path)
            mock_file_old.is_file.return_value = True
            mock_file_old.stat.return_value.img_b64 = None
            mock_file_old.stat.return_value.st_mtime = time.time() - (5 * 86400)
            mock_file_old.unlink.side_effect = Exception("Denied")

            mock_glob.return_value = [mock_file_old]

            result = get_elevation_profile_image(
                geometry=mock_geometry,
                uuid_input="test-uuid",
                style="bars"
            )

            assert result["status"] == "Success"
            assert "bikescout://altimetry/" in result["mcp_resource_uri"]
            assert result["style_applied"] == "bars"

    def test_data_healing_logic_and_glitches(self):
        bad_data_1 = [
            [9.1, 45.1, -9999],
            [9.11, 45.11, 100],
            [9.12, 45.12, 120]
        ]
        assert _generate_altimetry_plot(bad_data_1) is not None

        bad_data_2 = [
            [45.0, 45.0, 100.0],
            [45.0, 45.1, 10100.0],
            [45.0, 45.2, 100.0]
        ]
        assert _generate_altimetry_plot(bad_data_2) is not None

        bad_data_3 = [
            [45.0, 45.0, 100.0],
            [45.0, 45.0, 110.0],
            [45.0, 45.0, 101.0]
        ]
        assert _generate_altimetry_plot(bad_data_3) is not None

    def test_insufficient_geometry(self):
        assert _generate_altimetry_plot([]) is None
        assert _generate_altimetry_plot([[9.1, 45.1, 100]]) is None

    @patch("bikescout.tools.altimetry._generate_altimetry_plot")
    @patch("pathlib.Path.mkdir")
    def test_get_elevation_profile_errors(self, mock_mkdir, mock_plot):
        mock_geometry = MagicMock()
        mock_geometry.coordinates = [[9.0, 45.0, 100.0], [9.1, 45.1, 150.0]]

        mock_plot.return_value = None
        result = get_elevation_profile_image(mock_geometry, uuid_input=None)
        assert result["status"] == "Error"
        assert "No plot data generated" in result["message"]

        mock_plot.return_value = ("", 10.0)
        result = get_elevation_profile_image(mock_geometry, uuid_input=None)
        assert result["status"] == "Error"

    def test_get_elevation_profile_exception(self):
        result = get_elevation_profile_image(None, uuid_input="error-test")
        assert result["status"] == "Error"
        assert "Altimetry home-storage failed" in result["message"]