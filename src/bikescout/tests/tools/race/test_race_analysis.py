from io import StringIO
from pathlib import Path

import requests

import bikescout.tools.race.analysis as analysis_module
from bikescout.tools.race.analysis import (
    RaceAnalysisConfig,
    RaceAnalysisService,
    _calculate_aero_risks,
    _calculate_performance,
    _detect_uci_climbs,
    _estimate_ride_duration,
    _finalize_climb_data,
    _generate_elevation_plot,
    _identify_tactical_zones,
    _process_segments,
    analyze_track,
)


GPX_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="pytest" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>Sample</name>
    <trkseg>
      <trkpt lat="45.0000" lon="10.0000"><ele>100</ele></trkpt>
      <trkpt lat="45.0003" lon="10.0003"><ele>110</ele></trkpt>
      <trkpt lat="45.0006" lon="10.0006"><ele>125</ele></trkpt>
      <trkpt lat="45.0009" lon="10.0009"><ele>140</ele></trkpt>
      <trkpt lat="45.0012" lon="10.0012"><ele>155</ele></trkpt>
      <trkpt lat="45.0015" lon="10.0015"><ele>170</ele></trkpt>
      <trkpt lat="45.0018" lon="10.0018"><ele>182</ele></trkpt>
      <trkpt lat="45.0021" lon="10.0021"><ele>195</ele></trkpt>
      <trkpt lat="45.0024" lon="10.0024"><ele>210</ele></trkpt>
      <trkpt lat="45.0027" lon="10.0027"><ele>225</ele></trkpt>
      <trkpt lat="45.0030" lon="10.0030"><ele>240</ele></trkpt>
      <trkpt lat="45.0033" lon="10.0033"><ele>255</ele></trkpt>
    </trkseg>
  </trk>
</gpx>
"""


class FakeResponse:
    def __init__(self, text="", raise_exc=None):
        self.text = text
        self.raise_exc = raise_exc

    def raise_for_status(self):
        if self.raise_exc:
            raise self.raise_exc


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.calls = []

    def get(self, url, timeout=None):
        self.calls.append({"url": url, "timeout": timeout})
        if self.exc:
            raise self.exc
        return self.response


def test_estimate_ride_duration_standard():
    duration, speed = _estimate_ride_duration(50.0, 500.0, "intermediate", "road")
    assert duration > 0
    assert speed > 0


def test_estimate_ride_duration_speed_floor():
    duration, speed = _estimate_ride_duration(10.0, 5000.0, "beginner", "mtb")
    assert speed == 8.0
    assert duration == 10.0 / 8.0


def test_process_segments_road():
    points = [
        {"lat": 45.0 + i * 0.0003, "lon": 10.0 + i * 0.0003, "ele": 100 + i * 5, "time": None}
        for i in range(15)
    ]
    result = _process_segments(points, "road")
    assert len(result) > 0
    assert "bearing" in result[0]


def test_process_segments_mtb():
    points = [
        {"lat": 45.0 + i * 0.0002, "lon": 10.0 + i * 0.0002, "ele": 100 + i * 4, "time": None}
        for i in range(15)
    ]
    result = _process_segments(points, "mtb")
    assert len(result) > 0


def test_finalize_climb_data_discarded():
    climbs = []
    current = [
        {"dist": 800, "ele_start": 100, "ele_end": 120, "grade": 2.0},
        {"dist": 700, "ele_start": 120, "ele_end": 140, "grade": 2.0},
    ]
    _finalize_climb_data(current, current, climbs)
    assert climbs == []


def test_finalize_climb_data_adds_climb():
    climbs = []
    all_segments = [
        {"dist": 1000, "ele_start": 100, "ele_end": 180, "grade": 8.0},
        {"dist": 1000, "ele_start": 180, "ele_end": 260, "grade": 8.0},
    ]
    _finalize_climb_data(all_segments, all_segments, climbs)
    assert len(climbs) == 1


def test_detect_uci_climbs():
    segments = [
        {"dist": 900, "grade": 2.0, "ele_start": 100, "ele_end": 140},
        {"dist": 900, "grade": 4.0, "ele_start": 140, "ele_end": 200},
        {"dist": 1200, "grade": 0.5, "ele_start": 200, "ele_end": 205},
    ]
    climbs = _detect_uci_climbs(segments)
    assert isinstance(climbs, list)


def test_identify_tactical_zones():
    segments = [
        {"dist": 1000, "grade": 15.0, "bearing": 90, "ele_start": 100, "ele_end": 250},
        {"dist": 1000, "grade": -12.0, "bearing": 100, "ele_start": 250, "ele_end": 130},
        {"dist": 1000, "grade": 11.0, "bearing": 110, "ele_start": 130, "ele_end": 240},
    ]
    climbs = [{"km_start": 5.0, "dist_km": 3.2, "avg_grade": 8.5, "category": "HC"}]
    result = _identify_tactical_zones(segments, climbs, 30.0)

    assert "pre_climb_positioning" in result
    assert "action_zones" in result
    assert len(result["pre_climb_positioning"]) == 1


def test_calculate_performance():
    climbs = [{"km_start": 10.0, "dist_km": 5.0, "gain_m": 400.0, "avg_grade": 8.0, "category": "Cat 1"}]
    result = _calculate_performance(climbs, 75.0, 8.0, 1.2, 30.0, 20.0)
    assert len(result) == 1
    assert result[0]["weather_adjusted_wkg"] >= result[0]["target_wkg"]


def test_calculate_aero_risks_low_wind():
    assert _calculate_aero_risks([], 90, 10) == []


def test_calculate_aero_risks_detects_crosswind():
    segments = [{"dist": 1000, "bearing": 180} for _ in range(100)]
    result = _calculate_aero_risks(segments, 90, 25)
    assert len(result) >= 1


def test_load_gpx_content_local(tmp_path):
    file_path = tmp_path / "sample.gpx"
    file_path.write_text(GPX_SAMPLE, encoding="utf-8")

    service = RaceAnalysisService()
    content = service._load_gpx_content(str(file_path))
    assert "<gpx" in content


def test_load_gpx_content_remote():
    session = FakeSession(response=FakeResponse(text=GPX_SAMPLE))
    service = RaceAnalysisService(requests_session=session, config=RaceAnalysisConfig())

    content = service._load_gpx_content("https://example.com/file.gpx")
    assert "<gpx" in content
    assert session.calls[0]["timeout"] == 20.0


def test_extract_points():
    import gpxpy
    gpx = gpxpy.parse(GPX_SAMPLE)
    points = RaceAnalysisService._extract_points(gpx)
    assert len(points) == 12


def test_intensity_score():
    service = RaceAnalysisService()
    assert service._intensity_score(100.0, 100.0, 1.0) == 1
    assert service._intensity_score(10.0, 30.0, 1.0) == 2
    assert service._intensity_score(10.0, 50.0, 1.0) == 3
    assert service._intensity_score(10.0, 70.0, 1.0) == 4
    assert service._intensity_score(10.0, 100.0, 1.0) == 5


def test_generate_elevation_plot(tmp_path, monkeypatch):
    monkeypatch.setattr(analysis_module.os.path, "expanduser", lambda _: str(tmp_path))
    segments = [
        {"dist": 1000, "ele_end": 100},
        {"dist": 1000, "ele_end": 150},
    ]
    result = _generate_elevation_plot(segments, "2026-06-03")
    assert Path(result).exists()


def test_analyze_track_success_road(tmp_path):
    file_path = tmp_path / "sample.gpx"
    file_path.write_text(GPX_SAMPLE, encoding="utf-8")

    service = RaceAnalysisService(
        weather_getter=lambda lat, lon, t_date: {
            "status": "Success",
            "reference_conditions": {"temp": 22.0, "wind_speed": 20.0, "wind_dir_degrees": 90},
        },
        weather_windowing=lambda data, s, e: data,
        mud_analyzer=lambda *args, **kwargs: {"status": "Success"},
        nutrition_getter=lambda *args, **kwargs: {"status": "Success", "mission_nutrition_briefing": {}},
        date_provider=lambda: "2026-06-03",
    )

    result = service.analyze_track(str(file_path), activity_type="road")

    assert result["status"] == "Success"
    assert result["mode"] == "ROAD"
    assert result["planning_tools"]["mud_risk"] is None


def test_analyze_track_success_offroad_with_mud(tmp_path):
    file_path = tmp_path / "sample.gpx"
    file_path.write_text(GPX_SAMPLE, encoding="utf-8")

    service = RaceAnalysisService(
        weather_getter=lambda lat, lon, t_date: {"status": "Error"},
        weather_windowing=lambda data, s, e: data,
        mud_analyzer=lambda *args, **kwargs: {"status": "Success", "tactical_analysis": {}},
        nutrition_getter=lambda *args, **kwargs: {"status": "Success", "mission_nutrition_briefing": {}},
        date_provider=lambda: "2026-06-03",
    )

    result = service.analyze_track(str(file_path), activity_type="mtb")

    assert result["status"] == "Success"
    assert result["planning_tools"]["mud_risk"]["status"] == "Success"


def test_analyze_track_with_report(tmp_path):
    file_path = tmp_path / "sample.gpx"
    file_path.write_text(GPX_SAMPLE, encoding="utf-8")

    service = RaceAnalysisService(
        weather_getter=lambda lat, lon, t_date: {"status": "Error"},
        weather_windowing=lambda data, s, e: data,
        mud_analyzer=lambda *args, **kwargs: {"status": "Success"},
        nutrition_getter=lambda *args, **kwargs: {"status": "Success", "mission_nutrition_briefing": {}},
        date_provider=lambda: "2026-06-03",
        plot_generator=lambda segments, t_date: "/tmp/fake_plot.png",
        pdf_generator=lambda data, plot_path: "/tmp/fake_report.pdf",
    )

    result = service.analyze_track(str(file_path), activity_type="road", report=True)

    assert result["status"] == "Success"
    assert result["report_path"] == "/tmp/fake_report.pdf"


def test_analyze_track_insufficient_points(tmp_path):
    short_gpx = """<?xml version="1.0" encoding="UTF-8"?>
    <gpx version="1.1" creator="pytest" xmlns="http://www.topografix.com/GPX/1/1">
      <trk><trkseg>
        <trkpt lat="45.0" lon="10.0"><ele>100</ele></trkpt>
        <trkpt lat="45.1" lon="10.1"><ele>110</ele></trkpt>
      </trkseg></trk>
    </gpx>"""
    file_path = tmp_path / "short.gpx"
    file_path.write_text(short_gpx, encoding="utf-8")

    service = RaceAnalysisService()
    result = service.analyze_track(str(file_path))

    assert result == {"status": "Error", "message": "Insufficient data points in GPX."}


def test_analyze_track_exception_writes_stderr():
    stderr = StringIO()
    session = FakeSession(exc=requests.exceptions.RequestException("network down"))
    service = RaceAnalysisService(
        requests_session=session,
        stderr_writer=stderr,
    )

    result = service.analyze_track("https://example.com/file.gpx")

    assert result["status"] == "Error"
    assert "network down" in result["message"]
    assert "ANALYSIS FAILURE:" in stderr.getvalue()


def test_module_level_wrapper(monkeypatch):
    class FakeService:
        def __init__(self):
            self.calls = []

        def analyze_track(self, **kwargs):
            self.calls.append(kwargs)
            return {"status": "Success"}

    fake_service = FakeService()
    monkeypatch.setattr(analysis_module, "service", fake_service)

    result = analyze_track("test.gpx")

    assert result == {"status": "Success"}
    assert len(fake_service.calls) == 1

def test_detect_uci_climbs_final_current_branch():
    segments = [
        {"dist": 1000, "grade": 4.0, "ele_start": 100, "ele_end": 180},
        {"dist": 1000, "grade": 5.0, "ele_start": 180, "ele_end": 280},
        {"dist": 1000, "grade": 4.0, "ele_start": 280, "ele_end": 380},
    ]

    climbs = _detect_uci_climbs(segments)

    assert len(climbs) >= 1

def test_calculate_aero_risks_angle_wrap_branch():
    segments = [{"dist": 1000, "bearing": 350} for _ in range(100)]
    result = _calculate_aero_risks(segments, wind_dir=100, wind_speed=25)

    assert isinstance(result, list)

def test_generate_pdf_report_no_zones_plot_exists(tmp_path, monkeypatch):
    plot_path = tmp_path / "plot.png"
    plot_path.write_bytes(b"fakepng")

    report_dir = tmp_path / "race"
    report_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(analysis_module.os.path, "expanduser", lambda _: str(tmp_path))
    monkeypatch.setattr(analysis_module.uuid, "uuid4", lambda: type("U", (), {"hex": "abcdef123456"})())

    class FakeFPDF:
        def __init__(self):
            self.lines = []

        def add_page(self): pass
        def set_font(self, *args, **kwargs): pass
        def cell(self, *args, **kwargs): pass
        def ln(self, *args, **kwargs): pass
        def image(self, *args, **kwargs): pass
        def get_y(self): return 20
        def set_y(self, *args, **kwargs): pass
        def multi_cell(self, *args, **kwargs): pass
        def set_text_color(self, *args, **kwargs): pass
        def output(self, path):
            Path(path).write_text("pdf", encoding="utf-8")

    monkeypatch.setattr(analysis_module, "FPDF", FakeFPDF)

    data = {
        "target_date": "2026-06-03",
        "track_metrics": {"distance_km": 100.0, "total_ascent": 500.0},
        "tactical_action_zones": [],
        "planning_tools": {"weather_forecast": {"reference_conditions": {"temp": 20, "wind_speed": 10}}},
    }

    result = analysis_module._generate_pdf_report(data, str(plot_path))

    assert result.endswith(".pdf")
    assert Path(result).exists()

def test_generate_pdf_report_xc_circuit_plot_missing(tmp_path, monkeypatch):
    report_dir = tmp_path / "race"
    report_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(analysis_module.os.path, "expanduser", lambda _: str(tmp_path))
    monkeypatch.setattr(analysis_module.uuid, "uuid4", lambda: type("U", (), {"hex": "123456abcdef"})())

    class FakeFPDF:
        def add_page(self): pass
        def set_font(self, *args, **kwargs): pass
        def cell(self, *args, **kwargs): pass
        def ln(self, *args, **kwargs): pass
        def image(self, *args, **kwargs): pass
        def get_y(self): return 20
        def set_y(self, *args, **kwargs): pass
        def multi_cell(self, *args, **kwargs): pass
        def set_text_color(self, *args, **kwargs): pass
        def output(self, path):
            Path(path).write_text("pdf", encoding="utf-8")

    monkeypatch.setattr(analysis_module, "FPDF", FakeFPDF)

    data = {
        "target_date": "2026-06-03",
        "track_metrics": {"distance_km": 10.0, "total_ascent": 200.0},
        "tactical_action_zones": [
            {"km": 2.0, "type": "Explosive Wall / Attack Point", "grade": 14.0, "difficulty": "high"}
        ],
        "planning_tools": {"weather_forecast": {"reference_conditions": {"temp": 29, "wind_speed": 12}}},
    }

    result = analysis_module._generate_pdf_report(data, str(tmp_path / "missing_plot.png"))

    assert result.endswith(".pdf")
    assert Path(result).exists()

def test_generate_pdf_report_brutal_mountain_high_wind(tmp_path, monkeypatch):
    plot_path = tmp_path / "plot.png"
    plot_path.write_bytes(b"fakepng")

    report_dir = tmp_path / "race"
    report_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(analysis_module.os.path, "expanduser", lambda _: str(tmp_path))
    monkeypatch.setattr(analysis_module.uuid, "uuid4", lambda: type("U", (), {"hex": "fedcba654321"})())

    class FakeFPDF:
        def add_page(self): pass
        def set_font(self, *args, **kwargs): pass
        def cell(self, *args, **kwargs): pass
        def ln(self, *args, **kwargs): pass
        def image(self, *args, **kwargs): pass
        def get_y(self): return 20
        def set_y(self, *args, **kwargs): pass
        def multi_cell(self, *args, **kwargs): pass
        def set_text_color(self, *args, **kwargs): pass
        def output(self, path):
            Path(path).write_text("pdf", encoding="utf-8")

    monkeypatch.setattr(analysis_module, "FPDF", FakeFPDF)

    data = {
        "target_date": "2026-06-03",
        "track_metrics": {"distance_km": 100.0, "total_ascent": 2500.0},
        "tactical_action_zones": [
            {"km": 80.0, "type": "Explosive Wall / Attack Point", "grade": 16.0, "difficulty": "high"}
        ],
        "planning_tools": {"weather_forecast": {"reference_conditions": {"temp": 15, "wind_speed": 25}}},
    }

    result = analysis_module._generate_pdf_report(data, str(plot_path))

    assert result.endswith(".pdf")
    assert Path(result).exists()

def test_generate_pdf_report_rolling_cold(tmp_path, monkeypatch):
    plot_path = tmp_path / "plot.png"
    plot_path.write_bytes(b"fakepng")

    report_dir = tmp_path / "race"
    report_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(analysis_module.os.path, "expanduser", lambda _: str(tmp_path))
    monkeypatch.setattr(analysis_module.uuid, "uuid4", lambda: type("U", (), {"hex": "aa11bb22cc33"})())

    class FakeFPDF:
        def add_page(self): pass
        def set_font(self, *args, **kwargs): pass
        def cell(self, *args, **kwargs): pass
        def ln(self, *args, **kwargs): pass
        def image(self, *args, **kwargs): pass
        def get_y(self): return 20
        def set_y(self, *args, **kwargs): pass
        def multi_cell(self, *args, **kwargs): pass
        def set_text_color(self, *args, **kwargs): pass
        def output(self, path):
            Path(path).write_text("pdf", encoding="utf-8")

    monkeypatch.setattr(analysis_module, "FPDF", FakeFPDF)

    data = {
        "target_date": "2026-06-03",
        "track_metrics": {"distance_km": 80.0, "total_ascent": 1000.0},
        "tactical_action_zones": [
            {"km": 20.0, "type": "Explosive Wall / Attack Point", "grade": 12.0, "difficulty": "medium"}
        ],
        "planning_tools": {"weather_forecast": {"reference_conditions": {"temp": 5, "wind_speed": 10}}},
    }

    result = analysis_module._generate_pdf_report(data, str(plot_path))

    assert result.endswith(".pdf")
    assert Path(result).exists()

def test_generate_pdf_report_flat_long_day(tmp_path, monkeypatch):
    plot_path = tmp_path / "plot.png"
    plot_path.write_bytes(b"fakepng")

    report_dir = tmp_path / "race"
    report_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(analysis_module.os.path, "expanduser", lambda _: str(tmp_path))
    monkeypatch.setattr(analysis_module.uuid, "uuid4", lambda: type("U", (), {"hex": "112233445566"})())

    class FakeFPDF:
        def add_page(self): pass
        def set_font(self, *args, **kwargs): pass
        def cell(self, *args, **kwargs): pass
        def ln(self, *args, **kwargs): pass
        def image(self, *args, **kwargs): pass
        def get_y(self): return 20
        def set_y(self, *args, **kwargs): pass
        def multi_cell(self, *args, **kwargs): pass
        def set_text_color(self, *args, **kwargs): pass
        def output(self, path):
            Path(path).write_text("pdf", encoding="utf-8")

    monkeypatch.setattr(analysis_module, "FPDF", FakeFPDF)

    data = {
        "target_date": "2026-06-03",
        "track_metrics": {"distance_km": 180.0, "total_ascent": 800.0},
        "tactical_action_zones": [],
        "planning_tools": {"weather_forecast": {"reference_conditions": {"temp": 20, "wind_speed": 10}}},
    }

    result = analysis_module._generate_pdf_report(data, str(plot_path))

    assert result.endswith(".pdf")
    assert Path(result).exists()

def test_generate_pdf_report_cleans_matching_climb_files(tmp_path, monkeypatch):
    plot_path = tmp_path / "plot.png"
    plot_path.write_bytes(b"fakepng")

    report_dir = tmp_path / ".bikescout" / "race"
    report_dir.mkdir(parents=True, exist_ok=True)
    climb_file = report_dir / "climb_test_abcdef.png"
    climb_file.write_bytes(b"x")

    monkeypatch.setattr(analysis_module.os.path, "expanduser", lambda _: str(tmp_path))
    monkeypatch.setattr(analysis_module.uuid, "uuid4", lambda: type("U", (), {"hex": "abcdef123456"})())

    class FakeFPDF:
        def add_page(self): pass
        def set_font(self, *args, **kwargs): pass
        def cell(self, *args, **kwargs): pass
        def ln(self, *args, **kwargs): pass
        def image(self, *args, **kwargs): pass
        def get_y(self): return 20
        def set_y(self, *args, **kwargs): pass
        def multi_cell(self, *args, **kwargs): pass
        def set_text_color(self, *args, **kwargs): pass
        def output(self, path):
            Path(path).write_text("pdf", encoding="utf-8")

    monkeypatch.setattr(analysis_module, "FPDF", FakeFPDF)

    data = {
        "target_date": "2026-06-03",
        "track_metrics": {"distance_km": 100.0, "total_ascent": 2000.0},
        "tactical_action_zones": [],
        "planning_tools": {"weather_forecast": {"reference_conditions": {"temp": 20, "wind_speed": 10}}},
    }

    result = analysis_module._generate_pdf_report(data, str(plot_path))

    assert Path(result).exists()
    assert not climb_file.exists()
