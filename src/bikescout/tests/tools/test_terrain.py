# BikeScout - Tactical Intelligence for Cyclists
# Copyright (C) 2026 hifly81 (https://github.com/hifly81/bikescout)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import pytest

import bikescout.tools.terrain as terrain_module
from bikescout.tools.terrain import (
    TerrainConfig,
    TerrainService,
    _fiets_category,
    _noise_floor,
    _smooth_profile,
    analyze_terrain_profile,
    infer_technical_difficulty,
    segment_distances_m,
)


def geometry_from_elevations(elevations: list[float], step: float = 0.00045) -> list[list[float]]:
    """Build GeoJSON-like coordinates with roughly 60 m between samples."""
    return [
        [10.0 + index * step, 45.0, float(elevation)] for index, elevation in enumerate(elevations)
    ]


def two_climb_geometry() -> list[list[float]]:
    """Build a profile with two distinct significant climbs."""
    elevations: list[float] = []
    current = 100.0
    for _ in range(10):
        current += 10.0
        elevations.append(current)
    for _ in range(10):
        current -= 10.0
        elevations.append(current)
    for _ in range(8):
        current += 10.0
        elevations.append(current)
    for _ in range(8):
        current -= 10.0
        elevations.append(current)
    return geometry_from_elevations(elevations)


def test_segment_distances_and_short_profile() -> None:
    geometry = geometry_from_elevations([100.0, 101.0])
    distances = segment_distances_m(geometry)

    assert len(distances) == 1
    assert distances[0] > 0

    result = analyze_terrain_profile(geometry)
    assert result["total_ascent_m"] == 0.0
    assert result["data_confidence"] == 0.0
    assert result["climbs"] == []
    assert result["climb_profile_coordinates"] == []
    assert "climb_list" not in result
    assert result["climb_category"] == "Flat / Rolling"


def test_exposes_profile_coordinates_only_for_long_climbs() -> None:
    elevations = [100.0 + index * 10.0 for index in range(20)]
    elevations += [300.0 - index * 10.0 for index in range(20)]

    result = analyze_terrain_profile(geometry_from_elevations(elevations, step=0.0009))

    assert len(result["climbs"]) == 1
    climb = result["climbs"][0]
    coordinates = result["climb_profile_coordinates"][0]
    assert coordinates is not None
    assert len(coordinates) == climb["end_index"] - climb["start_index"] + 1
    assert coordinates[0][2] == pytest.approx(elevations[climb["start_index"]], abs=25.0)


def test_smooth_profile_preserves_length_and_edge_values() -> None:
    elevations = [100.0 + index for index in range(21)]

    smoothed = _smooth_profile(elevations, 11)

    assert len(smoothed) == len(elevations)
    assert smoothed[0] == pytest.approx(100.0, abs=0.2)
    assert smoothed[-1] == pytest.approx(120.0, abs=0.2)
    assert len(_smooth_profile(elevations[:4], 11)) == 4


def test_noise_floor_scales_with_point_density() -> None:
    config = TerrainConfig()

    dense_floor = _noise_floor([1.0] * 10, config)
    sparse_floor = _noise_floor([50.0] * 10, config)

    assert dense_floor > sparse_floor
    assert sparse_floor == config.base_noise_floor_m
    assert dense_floor <= config.max_noise_floor_m


def test_monotonic_rise_ascent_matches_geometry() -> None:
    geometry = geometry_from_elevations([100.0 + index for index in range(21)])

    result = analyze_terrain_profile(geometry)

    assert result["profile_points"] == 21
    assert result["total_ascent_m"] == pytest.approx(20.0, abs=1.0)
    assert result["avg_gradient"] == pytest.approx(
        result["total_ascent_m"] / result["profile_length_m"] * 100.0, rel=0.05
    )
    assert result["data_confidence"] > 0.5


def test_detects_multiple_climbs_with_fiets_categories() -> None:
    result = analyze_terrain_profile(two_climb_geometry())

    assert len(result["climbs"]) == 2
    assert "climb_list" not in result
    assert result["total_ascent_m"] >= 150.0
    for climb in result["climbs"]:
        assert climb["gain_m"] >= 10.0
        assert climb["length_m"] >= 100.0
        assert climb["fiets_index"] > 0
        assert climb["max_gradient"] >= climb["avg_gradient"]
        assert "C" in climb["category"] or "HC" in climb["category"]
    assert result["climb_category"] in {climb["category"] for climb in result["climbs"]}


def test_fiets_category_thresholds() -> None:
    assert _fiets_category(7.0) == "Hors Catégorie (HC)"
    assert _fiets_category(5.2) == "C1 - Brutal Ascent"
    assert _fiets_category(3.6) == "C2 - Hard Climb"
    assert _fiets_category(2.1) == "C3 - Challenging"
    assert _fiets_category(0.6) == "C4 - Short Burner"
    assert _fiets_category(0.1) == "C5 - Gentle Rise"


def test_micro_spike_warning_is_emitted() -> None:
    geometry = geometry_from_elevations([100.0] * 5 + [125.0] * 5 + [100.0] * 5)

    result = analyze_terrain_profile(geometry)

    assert result["max_gradient"] >= 20.0
    assert result["micro_spikes"] is True
    assert any("Micro-pitch" in warning for warning in result["warnings"])


def test_implausible_steps_lower_data_confidence() -> None:
    clean = analyze_terrain_profile(
        geometry_from_elevations([100.0 + index for index in range(21)])
    )
    spiky = analyze_terrain_profile(
        geometry_from_elevations([100.0 if index % 2 == 0 else 500.0 for index in range(21)])
    )

    assert spiky["data_confidence"] < clean["data_confidence"]
    assert spiky["total_ascent_m"] < 21 * 25.0


def test_technical_difficulty_inference_sources() -> None:
    tagged = infer_technical_difficulty({"mtb_scale": {"summary": [{"value": 3, "distance": 100}]}})
    assert tagged == {"label": "S3", "confidence": 0.9, "source": "osm:mtb_scale"}

    inferred = infer_technical_difficulty(
        {
            "surface": {"summary": [{"value": 11, "distance": 100}]},
            "waytype": {"summary": [{"value": 5, "distance": 100}]},
        }
    )
    assert inferred["source"] == "inferred:surface+waytype"
    assert inferred["confidence"] == 0.55

    assert infer_technical_difficulty(None, 0.0)["source"] == "missing"
    assert infer_technical_difficulty(None, 20.0)["source"] == "inferred:gradient"


def test_enduro_category_prefix() -> None:
    result = analyze_terrain_profile(two_climb_geometry(), bike_type="enduro")

    assert result["climb_category"].startswith("Enduro Tech:")


def test_technical_difficulty_is_attached_to_analysis() -> None:
    extras = {"surface": {"summary": [{"value": 5, "distance": 100}]}}

    result = analyze_terrain_profile(two_climb_geometry(), extras=extras)

    assert result["technical_difficulty"]["source"] == "inferred:surface+waytype"
    assert result["noise_floor_m"] == TerrainConfig().base_noise_floor_m


def test_module_wrapper_delegates_to_service(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def analyze_profile(self, **kwargs: object) -> dict[str, object]:
            return {"total_ascent_m": 42, "kwargs": kwargs}

    fake_service = FakeService()
    monkeypatch.setattr(terrain_module, "service", fake_service)

    result = analyze_terrain_profile([[10.0, 45.0, 100.0]], bike_type="gravel")

    assert result["total_ascent_m"] == 42
    assert result["kwargs"]["bike_type"] == "gravel"


def test_custom_config_is_used_by_service() -> None:
    service = TerrainService(config=TerrainConfig(min_profile_points=2))

    result = service.analyze_profile([[10.0, 45.0, 100.0], [10.001, 45.0, 110.0]])

    assert result["profile_points"] == 2
    assert result["data_confidence"] >= 0.0
