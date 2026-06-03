import os
import time
from pathlib import Path

import pytest

import bikescout.tools.maps as maps_module
from bikescout.tools.maps import TacticalMapConfig, TacticalMapError, TacticalMapService


class DummyImage:
    def __init__(self):
        self.saved_to = None

    def save(self, path):
        self.saved_to = path
        Path(path).write_bytes(b"fake-image-bytes")


class DummyStaticMap:
    def __init__(self, width, height, url_template=None):
        self.width = width
        self.height = height
        self.url_template = url_template
        self.lines = []
        self.markers = []

    def add_line(self, line):
        self.lines.append(line)

    def add_marker(self, marker):
        self.markers.append(marker)

    def render(self):
        return DummyImage()


@pytest.fixture
def service(tmp_path):
    return TacticalMapService(
        TacticalMapConfig(
            storage_dir=tmp_path / "maps",
            image_width_px=800,
            image_height_px=600,
            default_line_color="red",
            default_line_width=7,
        )
    )


@pytest.fixture
def geojson_linestring_3d():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [10.0, 45.0, 100.0],
                        [10.01, 45.01, 120.0],
                        [10.02, 45.02, 110.0],
                    ],
                },
                "properties": {},
            }
        ],
    }


@pytest.fixture
def geojson_linestring_2d():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [10.0, 45.0],
                        [10.01, 45.01],
                        [10.02, 45.02],
                    ],
                },
                "properties": {},
            }
        ],
    }


@pytest.fixture
def patched_staticmap(monkeypatch):
    monkeypatch.setattr(maps_module, "StaticMap", DummyStaticMap)


def test_extract_linestring_points_accepts_3d(service, geojson_linestring_3d):
    points = service._extract_linestring_points(geojson_linestring_3d)

    assert len(points) == 3
    assert points[0] == (10.0, 45.0, 100.0)
    assert points[1] == (10.01, 45.01, 120.0)


def test_extract_linestring_points_accepts_2d(service, geojson_linestring_2d):
    points = service._extract_linestring_points(geojson_linestring_2d)

    assert len(points) == 3
    assert points[0] == (10.0, 45.0, None)
    assert points[2] == (10.02, 45.02, None)


def test_extract_linestring_points_rejects_non_dict(service):
    with pytest.raises(TacticalMapError):
        service._extract_linestring_points(["not-a-dict"])


def test_extract_linestring_points_rejects_missing_features(service):
    with pytest.raises(TacticalMapError):
        service._extract_linestring_points({"type": "FeatureCollection"})


def test_extract_linestring_points_rejects_empty_features(service):
    with pytest.raises(TacticalMapError):
        service._extract_linestring_points({"type": "FeatureCollection", "features": []})


def test_extract_linestring_points_rejects_missing_linestring(service):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [10.0, 45.0]}}
        ],
    }

    with pytest.raises(TacticalMapError):
        service._extract_linestring_points(geojson_data)


def test_extract_linestring_points_uses_first_valid_linestring(service):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [10.0, 45.0]}},
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [10.0, 45.0, 100.0],
                        [10.01, 45.01, 110.0],
                    ],
                },
            },
        ],
    }

    points = service._extract_linestring_points(geojson_data)

    assert len(points) == 2
    assert points[0] == (10.0, 45.0, 100.0)


def test_extract_linestring_points_rejects_insufficient_coordinates(service):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[10.0, 45.0, 100.0]]},
            }
        ],
    }

    with pytest.raises(TacticalMapError):
        service._extract_linestring_points(geojson_data)


def test_extract_linestring_points_filters_invalid_coordinates(service):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        ["bad", 45.0, 100.0],
                        [10.0, 95.0, 110.0],
                        [10.0, 45.0, 100.0],
                        [10.01, 45.01, 120.0],
                    ],
                },
            }
        ],
    }

    points = service._extract_linestring_points(geojson_data)

    assert len(points) == 2
    assert points[0] == (10.0, 45.0, 100.0)
    assert points[1] == (10.01, 45.01, 120.0)


def test_extract_linestring_points_rejects_if_too_few_valid_points_remain(service):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        ["bad", 45.0, 100.0],
                        [10.0, 45.0, 100.0],
                    ],
                },
            }
        ],
    }

    with pytest.raises(TacticalMapError):
        service._extract_linestring_points(geojson_data)


def test_should_use_gradient_true_for_complete_3d(service):
    points = [
        (10.0, 45.0, 100.0),
        (10.01, 45.01, 120.0),
    ]

    assert service._should_use_gradient(points, requested=True) is True


def test_should_use_gradient_false_when_not_requested(service):
    points = [
        (10.0, 45.0, 100.0),
        (10.01, 45.01, 120.0),
    ]

    assert service._should_use_gradient(points, requested=False) is False


def test_should_use_gradient_false_for_2d_points(service):
    points = [
        (10.0, 45.0, None),
        (10.01, 45.01, None),
    ]

    assert service._should_use_gradient(points, requested=True) is False


def test_approx_segment_run_m_positive(service):
    p1 = (10.0, 45.0, 100.0)
    p2 = (10.01, 45.01, 120.0)

    run = service._approx_segment_run_m(p1, p2)

    assert run > 0


def test_approx_segment_run_m_zero_for_same_point(service):
    p1 = (10.0, 45.0, 100.0)
    p2 = (10.0, 45.0, 120.0)

    run = service._approx_segment_run_m(p1, p2)

    assert run == 0


def test_compute_segment_grade_percent_positive(service):
    p1 = (10.0, 45.0, 100.0)
    p2 = (10.001, 45.001, 110.0)

    grade = service._compute_segment_grade_percent(p1, p2)

    assert grade > 0


def test_compute_segment_grade_percent_zero_when_missing_elevation(service):
    p1 = (10.0, 45.0, None)
    p2 = (10.001, 45.001, 110.0)

    grade = service._compute_segment_grade_percent(p1, p2)

    assert grade == 0.0


def test_compute_segment_grade_percent_zero_when_run_too_small(service):
    p1 = (10.0, 45.0, 100.0)
    p2 = (10.0, 45.0, 200.0)

    grade = service._compute_segment_grade_percent(p1, p2)

    assert grade == 0.0


def test_get_gradient_color_returns_hex(service):
    color = service._get_gradient_color(8.0)

    assert isinstance(color, str)
    assert color.startswith("#")
    assert len(color) == 7


def test_segment_color_from_points_returns_hex(service):
    p1 = (10.0, 45.0, 100.0)
    p2 = (10.001, 45.001, 110.0)

    color = service._segment_color_from_points(p1, p2)

    assert color.startswith("#")
    assert len(color) == 7


def test_sanitize_filename_component(service):
    assert service._sanitize_filename_component("abc") == "abc"
    assert service._sanitize_filename_component("a/b:c*d?e") == "a_b_c_d_e"
    assert service._sanitize_filename_component("") == "map"
    assert service._sanitize_filename_component(None) == "map"


def test_sanitize_filename_component_truncates_long_value(service):
    raw = "a" * 200
    cleaned = service._sanitize_filename_component(raw)
    assert len(cleaned) == 64


def test_cleanup_old_png_files_removes_stale_files(service):
    storage_dir = service.storage_dir
    storage_dir.mkdir(parents=True, exist_ok=True)

    stale = storage_dir / "old.png"
    fresh = storage_dir / "new.png"

    stale.write_bytes(b"x")
    fresh.write_bytes(b"y")

    old_time = time.time() - (service.config.cleanup_max_age_seconds + 50)
    os.utime(stale, (old_time, old_time))

    service.cleanup_old_png_files(storage_dir)

    assert not stale.exists()
    assert fresh.exists()


def test_cleanup_old_png_files_ignores_non_png(service):
    storage_dir = service.storage_dir
    storage_dir.mkdir(parents=True, exist_ok=True)

    text_file = storage_dir / "note.txt"
    text_file.write_text("hello")

    service.cleanup_old_png_files(storage_dir)

    assert text_file.exists()


def test_cleanup_old_png_files_ignores_oserror(service, monkeypatch):
    storage_dir = service.storage_dir
    storage_dir.mkdir(parents=True, exist_ok=True)

    target = storage_dir / "old.png"
    target.write_bytes(b"x")

    old_time = time.time() - (service.config.cleanup_max_age_seconds + 100)
    os.utime(target, (old_time, old_time))

    original_unlink = Path.unlink

    def fake_unlink(self):
        if self.name == "old.png":
            raise OSError("cannot delete")
        return original_unlink(self)

    monkeypatch.setattr(Path, "unlink", fake_unlink)

    service.cleanup_old_png_files(storage_dir)

    assert target.exists()


def test_build_map_gradient_adds_segment_lines_and_markers(service, patched_staticmap):
    points = [
        (10.0, 45.0, 100.0),
        (10.01, 45.01, 120.0),
        (10.02, 45.02, 110.0),
    ]

    map_obj = service._build_map(points, use_gradient=True, line_color="red", line_width=7)

    assert isinstance(map_obj, DummyStaticMap)
    assert len(map_obj.lines) == 2
    assert len(map_obj.markers) == 4


def test_build_map_solid_adds_one_line_and_markers(service, patched_staticmap):
    points = [
        (10.0, 45.0, None),
        (10.01, 45.01, None),
        (10.02, 45.02, None),
    ]

    map_obj = service._build_map(points, use_gradient=True, line_color="blue", line_width=5)

    assert isinstance(map_obj, DummyStaticMap)
    assert len(map_obj.lines) == 1
    assert len(map_obj.markers) == 4


def test_save_local_tactical_map_success_gradient(service, geojson_linestring_3d, patched_staticmap):
    result = service.save_local_tactical_map(
        filename_part="test-map",
        geojson_data=geojson_linestring_3d,
        use_gradient=True,
        line_color="red",
        line_width=7,
    )

    assert result["status"] == "Success"
    assert result["style_applied"] == "gradient"
    assert Path(result["file_location"]).exists()


def test_save_local_tactical_map_success_solid_for_2d(service, geojson_linestring_2d, patched_staticmap):
    result = service.save_local_tactical_map(
        filename_part="test-map",
        geojson_data=geojson_linestring_2d,
        use_gradient=True,
        line_color="red",
        line_width=7,
    )

    assert result["status"] == "Success"
    assert result["style_applied"] == "solid"
    assert Path(result["file_location"]).exists()


def test_save_local_tactical_map_rejects_non_positive_line_width(service, geojson_linestring_3d):
    result = service.save_local_tactical_map(
        filename_part="bad-width",
        geojson_data=geojson_linestring_3d,
        line_width=0,
    )

    assert result["status"] == "Error"
    assert "Line width must be positive" in result["message"]


def test_save_local_tactical_map_sanitizes_filename(service, geojson_linestring_3d, patched_staticmap):
    result = service.save_local_tactical_map(
        filename_part="bad/name:value",
        geojson_data=geojson_linestring_3d,
    )

    assert result["status"] == "Success"
    assert "bad_name_value" in result["file_location"]


def test_save_local_tactical_map_handles_domain_error(service):
    result = service.save_local_tactical_map(
        filename_part="x",
        geojson_data={"features": []},
    )

    assert result["status"] == "Error"
    assert "No features found" in result["message"]


def test_save_local_tactical_map_handles_unexpected_exception(service, geojson_linestring_3d, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(service, "_build_map", boom)

    result = service.save_local_tactical_map(
        filename_part="boom",
        geojson_data=geojson_linestring_3d,
    )

    assert result["status"] == "Error"
    assert result["message"] == "Local Map Generation Failed: boom"


def test_module_level_wrapper(tmp_path, geojson_linestring_3d, monkeypatch):
    monkeypatch.setattr(maps_module.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(maps_module, "StaticMap", DummyStaticMap)

    result = maps_module.save_local_tactical_map(
        filename_part="wrapper-test",
        geojson_data=geojson_linestring_3d,
    )

    assert result["status"] == "Success"


def test_extract_linestring_points_skips_non_dict_feature_entries(service):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            "not-a-feature",
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [10.0, 45.0, 100.0],
                        [10.01, 45.01, 110.0],
                    ],
                },
            },
        ],
    }

    points = service._extract_linestring_points(geojson_data)

    assert len(points) == 2


def test_extract_linestring_points_skips_bad_coordinate_entries(service):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        None,
                        [10.0, 45.0, 100.0],
                        [10.01, 45.01, 110.0],
                    ],
                },
            }
        ],
    }

    points = service._extract_linestring_points(geojson_data)

    assert len(points) == 2

@pytest.mark.parametrize("line_width", [0, -1, -5])
def test_save_local_tactical_map_rejects_non_positive_line_width(service, geojson_linestring_3d, line_width):
    result = service.save_local_tactical_map(
        filename_part="bad-width",
        geojson_data=geojson_linestring_3d,
        line_width=line_width,
    )

    assert result["status"] == "Error"
    assert "Line width must be positive" in result["message"]

def test_save_local_tactical_map_uses_default_line_width_when_none(service, geojson_linestring_3d, patched_staticmap):
    result = service.save_local_tactical_map(
        filename_part="default-width",
        geojson_data=geojson_linestring_3d,
        line_width=None,
    )

    assert result["status"] == "Success"