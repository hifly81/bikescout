import base64
import os
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

from bikescout.tools.altimetry import (
    AltimetryConfig,
    AltimetryError,
    AltimetryService,
    get_elevation_profile_image,
)


@dataclass
class DummyGeometry:
    coordinates: list


@pytest.fixture
def service(tmp_path):
    return AltimetryService(AltimetryConfig(storage_dir=tmp_path / "altimetry"))


@pytest.fixture
def valid_geometry_3d():
    return [
        [10.0, 45.0, 100.0],
        [10.01, 45.01, 120.0],
        [10.02, 45.02, 110.0],
    ]


@pytest.fixture
def valid_geometry_2d():
    return [
        [10.0, 45.0],
        [10.01, 45.01],
        [10.02, 45.02],
    ]


def test_normalize_geometry_accepts_2d(service, valid_geometry_2d):
    result = service._normalize_geometry(valid_geometry_2d)
    assert result.shape == (3, 3)
    assert np.allclose(result[:, 2], [0.0, 0.0, 0.0])


def test_normalize_geometry_accepts_3d(service, valid_geometry_3d):
    result = service._normalize_geometry(valid_geometry_3d)
    assert result.shape == (3, 3)
    assert result[1, 2] == 120.0


def test_normalize_geometry_filters_invalid_rows(service):
    geometry = [
        ["x", 45.0, 10.0],
        [10.0, 95.0, 20.0],
        [10.0, 45.0, 30.0],
        [10.1, 45.1, 40.0],
    ]
    result = service._normalize_geometry(geometry)
    assert result.shape == (2, 3)
    assert np.allclose(result[:, :2], np.array([[10.0, 45.0], [10.1, 45.1]]))


def test_normalize_geometry_raises_with_too_few_valid_points(service):
    with pytest.raises(AltimetryError):
        service._normalize_geometry([[10.0, 45.0]])


def test_interpolate_invalid_all_invalid(service):
    values = np.array([10000.0, 20000.0, 30000.0])
    valid_mask = np.array([False, False, False])
    result = service._interpolate_invalid(values, valid_mask)
    assert np.allclose(result, [0.0, 0.0, 0.0])


def test_interpolate_invalid_middle_gap(service):
    values = np.array([100.0, 5000.0, 120.0])
    valid_mask = np.array([True, False, True])
    result = service._interpolate_invalid(values, valid_mask)
    assert result[1] == pytest.approx(110.0)


def test_clean_elevations_removes_non_physical_values(service):
    elevations = np.array([100.0, 99999.0, 120.0])
    segment_distances = np.array([100.0, 100.0])
    result = service._clean_elevations(elevations, segment_distances)
    assert result[0] == 100.0
    assert result[1] == pytest.approx(110.0)
    assert result[2] == 120.0


def test_clean_elevations_removes_local_spike(service):
    elevations = np.array([100.0, 2000.0, 105.0])
    segment_distances = np.array([10.0, 10.0])
    result = service._clean_elevations(elevations, segment_distances)
    assert result[1] == pytest.approx(102.5)


def test_haversine_segment_distances_shape_and_positive(service):
    lons = np.array([10.0, 10.1, 10.2])
    lats = np.array([45.0, 45.1, 45.2])
    result = service._haversine_segment_distances_m(lons, lats)
    assert result.shape == (2,)
    assert np.all(result > 0)


def test_compute_segment_grades_percent_clips(service):
    elevations = np.array([100.0, 200.0])
    segment_distances = np.array([1.0])
    grades = service._compute_segment_grades_percent(elevations, segment_distances)
    assert grades.shape == (1,)
    assert grades[0] == 25.0


@pytest.mark.parametrize("style", ["sparkline", "filled", "bars"])
def test_generate_plot_for_all_styles(service, valid_geometry_3d, style):
    result = service.generate_plot(valid_geometry_3d, style=style)
    assert result.total_distance_km > 0
    decoded = base64.b64decode(result.image_base64)
    assert decoded.startswith(b"\x89PNG")


def test_generate_plot_rejects_invalid_style(service, valid_geometry_3d):
    with pytest.raises(AltimetryError):
        service.generate_plot(valid_geometry_3d, style="invalid")  # type: ignore[arg-type]


@pytest.mark.parametrize("width,height", [(0, 3), (8, 0), (-1, 2)])
def test_generate_plot_rejects_invalid_dimensions(service, valid_geometry_3d, width, height):
    with pytest.raises(AltimetryError):
        service.generate_plot(valid_geometry_3d, width=width, height=height)


def test_build_profile_arrays(service, valid_geometry_3d):
    distances_m, elevations = service._build_profile_arrays(valid_geometry_3d)
    assert len(distances_m) == len(elevations) == 3
    assert distances_m[0] == 0.0
    assert distances_m[-1] > 0.0


def test_sanitize_filename_component(service):
    assert service._sanitize_filename_component("abc") == "abc"
    assert service._sanitize_filename_component("a/b:c*d?e") == "a_b_c_d_e"
    assert service._sanitize_filename_component("") == "profile"
    assert service._sanitize_filename_component(None) == "profile"


def test_create_profile_image_success(service, valid_geometry_3d):
    geometry = DummyGeometry(coordinates=valid_geometry_3d)
    result = service.create_profile_image(geometry, "test-id", style="filled")
    assert result["status"] == "Success"
    assert result["style_applied"] == "filled"
    assert Path(result["file_location"]).exists()


def test_create_profile_image_handles_2d(service, valid_geometry_2d):
    geometry = DummyGeometry(coordinates=valid_geometry_2d)
    result = service.create_profile_image(geometry, "twod")
    assert result["status"] == "Success"
    assert result["total_distance_km"] > 0


def test_create_profile_image_rejects_missing_coordinates(service):
    class BadGeometry:
        pass

    result = service.create_profile_image(BadGeometry(), "x")
    assert result["status"] == "Error"
    assert "coordinates" in result["message"]


def test_create_profile_image_sanitizes_uuid(service, valid_geometry_3d):
    geometry = DummyGeometry(coordinates=valid_geometry_3d)
    result = service.create_profile_image(geometry, "bad/id:value")
    assert result["status"] == "Success"
    assert "bad_id_value" in result["file_location"]


def test_cleanup_old_png_files_removes_stale_files(service):
    storage_dir = service.storage_dir
    storage_dir.mkdir(parents=True, exist_ok=True)

    stale = storage_dir / "old.png"
    fresh = storage_dir / "new.png"

    stale.write_bytes(b"x")
    fresh.write_bytes(b"y")

    old_time = time.time() - (service.config.cleanup_max_age_seconds + 10)
    os.utime(stale, (old_time, old_time))

    service.cleanup_old_png_files(storage_dir)

    assert not stale.exists()
    assert fresh.exists()


def test_cleanup_old_png_files_ignores_non_png(service):
    storage_dir = service.storage_dir
    storage_dir.mkdir(parents=True, exist_ok=True)

    txt = storage_dir / "note.txt"
    txt.write_text("hello")

    service.cleanup_old_png_files(storage_dir)

    assert txt.exists()


def test_module_level_wrapper(valid_geometry_3d, tmp_path, monkeypatch):
    monkeypatch.setattr("bikescout.tools.altimetry.Path.home", lambda: tmp_path)

    geometry = DummyGeometry(coordinates=valid_geometry_3d)
    result = get_elevation_profile_image(geometry, "wrapper-test")
    assert result["status"] == "Success"


def test_duplicate_points_do_not_crash(service):
    geometry = [
        [10.0, 45.0, 100.0],
        [10.0, 45.0, 101.0],
        [10.01, 45.01, 110.0],
    ]
    result = service.generate_plot(geometry)
    assert result.total_distance_km > 0


def test_all_invalid_elevations_become_zero(service):
    geometry = [
        [10.0, 45.0, 99999.0],
        [10.01, 45.01, 99999.0],
        [10.02, 45.02, 99999.0],
    ]
    distances_m, elevations = service._build_profile_arrays(geometry)
    assert len(distances_m) == 3
    assert np.allclose(elevations, [0.0, 0.0, 0.0])


def test_none_elevation_becomes_zero(service):
    geometry = [
        [10.0, 45.0, None],
        [10.01, 45.01, 10.0],
    ]
    result = service._normalize_geometry(geometry)
    assert result[0, 2] == 0.0

def test_generate_plot_uses_default_dimensions_when_none(service, valid_geometry_3d):
    result = service.generate_plot(valid_geometry_3d, width=None, height=None)
    assert result.total_distance_km > 0
    assert isinstance(result.image_base64, str)
    assert len(result.image_base64) > 0

def test_interpolate_invalid_with_empty_array(service):
    values = np.array([], dtype=float)
    valid_mask = np.array([], dtype=bool)

    result = service._interpolate_invalid(values, valid_mask)

    assert isinstance(result, np.ndarray)
    assert result.size == 0


def test_haversine_segment_distances_empty_when_single_point(service):
    lons = np.array([10.0])
    lats = np.array([45.0])

    result = service._haversine_segment_distances_m(lons, lats)

    assert isinstance(result, np.ndarray)
    assert result.size == 0


def test_compute_segment_grades_percent_empty_when_less_than_two_points(service):
    elevations = np.array([100.0])
    segment_distances = np.array([], dtype=float)

    result = service._compute_segment_grades_percent(elevations, segment_distances)

    assert isinstance(result, np.ndarray)
    assert result.size == 0


def test_render_plot_bars_with_single_point_uses_fallback_color_and_width(service):
    distances_m = np.array([0.0])
    elevations = np.array([100.0])

    image_b64 = service._render_plot(
        distances_m=distances_m,
        elevations=elevations,
        width=8,
        height=3,
        style="bars",
    )

    decoded = base64.b64decode(image_b64)
    assert decoded.startswith(b"\x89PNG")


def test_sanitize_filename_component_truncates_long_values(service):
    raw = "a" * 200

    result = service._sanitize_filename_component(raw)

    assert len(result) == 64
    assert result == "a" * 64


def test_cleanup_old_png_files_ignores_oserror(service, monkeypatch):
    storage_dir = service.storage_dir
    storage_dir.mkdir(parents=True, exist_ok=True)

    target = storage_dir / "old.png"
    target.write_bytes(b"x")

    old_time = time.time() - (service.config.cleanup_max_age_seconds + 100)
    os.utime(target, (old_time, old_time))

    from pathlib import Path
    original_unlink = Path.unlink

    def fake_unlink(self):
        if self.name == "old.png":
            raise OSError("cannot delete")
        return original_unlink(self)

    monkeypatch.setattr(Path, "unlink", fake_unlink)

    service.cleanup_old_png_files(storage_dir)

    assert target.exists()


def test_create_profile_image_unexpected_exception_branch(service, monkeypatch, valid_geometry_3d):
    geometry = type("DummyGeometry", (), {"coordinates": valid_geometry_3d})()

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(service, "generate_plot", boom)

    result = service.create_profile_image(geometry, "x")

    assert result["status"] == "Error"
    assert "Altimetry home-storage failed: boom" == result["message"]


def test_generate_plot_with_none_dimensions_uses_defaults(service, valid_geometry_3d):
    result = service.generate_plot(valid_geometry_3d, width=None, height=None, style="filled")

    assert result.total_distance_km > 0
    assert len(result.image_base64) > 0

def test_render_plot_bars_uses_fallback_colors_when_grades_empty(service):
    distances_m = np.array([0.0])
    elevations = np.array([100.0])

    result = service._render_plot(
        distances_m=distances_m,
        elevations=elevations,
        width=8,
        height=3,
        style="bars",
    )

    decoded = base64.b64decode(result)
    assert decoded.startswith(b"\x89PNG")