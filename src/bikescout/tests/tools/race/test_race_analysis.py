import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
from bikescout.tools.race.analysis import analyze_track, _estimate_ride_duration, _calculate_aero_risks, _load_gpx_content

class TestRaceAnalysis:

    @pytest.fixture
    def mock_gpx_content(self):
        header = '<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="BikeScout"><trk><trkseg>'
        points = ""
        for i in range(20):
            lat = 45.0 + (i * 0.001)
            ele = 100 + (i * 10)
            points += f'<trkpt lat="{lat}" lon="9.0"><ele>{ele}</ele></trkpt>'
        footer = '</trkseg></trk></gpx>'
        return header + points + footer

    @patch("bikescout.tools.race.analysis._load_gpx_content")
    @patch("bikescout.tools.race.analysis.get_weather_forecast")
    @patch("bikescout.tools.race.analysis.get_nutrition_plan")
    @patch("bikescout.tools.race.analysis._generate_elevation_plot")
    @patch("bikescout.tools.race.analysis._generate_pdf_report")
    def test_analyze_track_road_success(self, m_pdf, m_plot, m_nut, m_weather, m_load, mock_gpx_content):
        m_load.return_value = mock_gpx_content
        m_weather.return_value = {
            "status": "Success",
            "reference_conditions": {"temp": 22.0, "wind_speed": 5.0, "wind_dir_degrees": 0}
        }
        m_nut.return_value = {"status": "Success", "plan": "Test nutrition"}
        m_plot.return_value = "dummy_plot.png"
        m_pdf.return_value = "dummy_report.pdf"

        result = analyze_track(
            gpx_url="https://path/to/race.gpx",
            activity_type="road",
            report=True
        )

        assert result["status"] == "Success"
        assert result["mode"] == "ROAD"
        assert "climb_analysis" in result
        assert "report_path" in result
        assert len(result["climb_analysis"]) > 0

    @patch("bikescout.tools.race.analysis._load_gpx_content")
    @patch("bikescout.tools.race.analysis.get_mud_risk_analysis")
    def test_analyze_track_mtb_with_mud(self, m_mud, m_load, mock_gpx_content):
        m_load.return_value = mock_gpx_content
        m_mud.return_value = {"status": "Success", "risk_level": "High"}

        with patch("bikescout.tools.race.analysis.get_weather_forecast", return_value={"status": "Error"}):
            result = analyze_track(gpx_url="test.gpx", activity_type="mtb")

        assert result["status"] == "Success"
        assert result["planning_tools"]["mud_risk"]["risk_level"] == "High"

    def test_echelon_risk_detection(self):

        segments = [
            {'dist': 1000, 'bearing': 0, 'grade': 0},
            {'dist': 1000, 'bearing': 0, 'grade': 0}
        ]

        wind_dir = 90
        wind_speed = 25.0
        alerts = _calculate_aero_risks(segments, wind_dir, wind_speed)
        assert len(alerts) > 0
        assert alerts[0]["type"] == "ECHELON RISK"

        alerts_low_wind = _calculate_aero_risks(segments, wind_dir, 10.0)
        assert len(alerts_low_wind) == 0

    def test_estimate_ride_duration_climbing_penalty(self):
        _, speed_flat = _estimate_ride_duration(50.0, 0, "intermediate", "road")

        _, speed_climb = _estimate_ride_duration(50.0, 2000, "intermediate", "road")

        assert speed_climb < speed_flat
        _, speed_extreme = _estimate_ride_duration(10.0, 5000, "beginner", "road")
        assert speed_extreme == 8.0

    @patch("requests.get")
    def test_load_gpx_exception(self, mock_get):
        mock_get.side_effect = Exception("Network Down")

        with pytest.raises(Exception):
            _load_gpx_content("https://bad-url.gpx")

    @patch("bikescout.tools.race.analysis.get_weather_forecast")
    @patch("bikescout.tools.race.analysis._load_gpx_content")
    def test_pdf_briefing_logic_branches(self, m_load, m_weather, mock_gpx_content):
        m_load.return_value = mock_gpx_content

        m_weather.return_value = {
            "status": "Success",
            "reference_conditions": {"temp": 35.0, "wind_speed": 25.0, "wind_dir_degrees": 90}
        }

        result = analyze_track(
            "dummy.gpx",
            activity_type="road",
            report=True,
            rider_fitness_level="pro"
        )

        assert "report_path" in result
        assert os.path.exists(result["report_path"])

        if os.path.exists(result["report_path"]):
            os.remove(result["report_path"])