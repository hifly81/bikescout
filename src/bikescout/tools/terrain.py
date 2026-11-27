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

import math
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

import numpy as np


@dataclass(frozen=True)
class TerrainConfig:
    """Tunable parameters for the offline elevation-processing pipeline.

    Values are documented heuristic defaults, not empirically calibrated
    constants. They are exposed for tests and controlled tuning.
    """

    smoothing_window: int = 5  # odd moving-average window over elevation samples
    base_noise_floor_m: float = 0.5  # minimum hysteresis for dense DEM profiles
    short_segment_threshold_m: float = 5.0  # spacing below which jitter is amplified
    jitter_noise_multiplier: float = 0.1  # extra noise floor per meter below threshold
    max_noise_floor_m: float = 2.0  # cap adaptive hysteresis
    max_step_up_m: float = 25.0  # reject implausible DEM/bridge spikes upward
    max_step_down_m: float = 25.0  # reject implausible DEM/tunnel spikes downward
    min_ascent_gain_m: float = 3.0  # minimum gain counted toward total ascent
    min_ascent_gradient_percent: float = 1.5  # minimum grade for ascent accounting
    min_climb_gain_m: float = 10.0  # minimum gain for a named climb segment
    min_climb_gradient_percent: float = 3.0  # minimum average grade for climb
    min_climb_length_m: float = 100.0  # minimum length for climb segmentation
    min_profile_points: int = 4  # minimum samples for meaningful terrain analysis


# Minimum climb length with a dedicated altimetry chart in the local planner.
CLIMB_PROFILE_MIN_LENGTH_M = 1000.0

_SURFACE_TECH_HINTS: dict[str, int] = {
    "0": 0,
    "1": 0,
    "2": 1,
    "3": 0,
    "5": 1,
    "11": 2,
    "14": 0,
}

_WAYTYPE_TECH_HINTS: dict[str, int] = {
    "0": 0,
    "1": 0,
    "2": 1,
    "3": 0,
    "4": 1,
    "5": 2,
    "6": 2,
    "7": 3,
    "8": 3,
    "9": 4,
    "10": 1,
}

_FIETS_CATEGORIES: tuple[tuple[float, str], ...] = (
    (6.5, "Hors Catégorie (HC)"),
    (5.0, "C1 - Brutal Ascent"),
    (3.5, "C2 - Hard Climb"),
    (2.0, "C3 - Challenging"),
    (0.5, "C4 - Short Burner"),
)


_EARTH_RADIUS_M = 6371000.0


def segment_distances_m(geometry: list[Any]) -> list[float]:
    """
    Compute ground distances between consecutive GeoJSON coordinates.

    Uses the Haversine formula on WGS84 mean spherical radius. This is more
    accurate than equirectangular approximation for non-trivial routes and
    matches the public documentation claim.

    Args:
        geometry: Coordinate triplets in [lon, lat, elevation] order.
    Returns:
        One distance in meters per consecutive pair; invalid pairs yield 0.0.
    """
    distances: list[float] = []
    for first, second in pairwise(geometry):
        try:
            lon1, lat1 = float(first[0]), float(first[1])
            lon2, lat2 = float(second[0]), float(second[1])
        except (TypeError, ValueError, IndexError, KeyError):
            distances.append(0.0)
            continue

        deg_to_rad = math.pi / 180.0
        lat1_rad = lat1 * deg_to_rad
        lat2_rad = lat2 * deg_to_rad
        delta_lat = (lat2 - lat1) * deg_to_rad
        delta_lon = (lon2 - lon1) * deg_to_rad
        a = (
            math.sin(delta_lat / 2.0) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2.0) ** 2
        )
        distances.append(2.0 * _EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, a))))
    return distances


def _extract_profile(
    geometry: list[Any], config: TerrainConfig
) -> tuple[list[float], list[float], int, list[Any]]:
    """
    Extract a numeric elevation series and cap implausible jumps.

    Args:
        geometry: Coordinate triplets in [lon, lat, elevation] order.
        config: Terrain processing parameters.
    Returns:
        A tuple of (step-capped elevations, segment distances, capped-step count,
        usable coordinates). The coordinate list aligns with the elevation list.
    """
    elevations: list[float] = []
    usable_points: list[Any] = []
    for point in geometry:
        try:
            if len(point) > 2 and isinstance(point[2], (int, float)):
                elevations.append(float(point[2]))
                usable_points.append(point)
        except (TypeError, KeyError):
            continue

    distances = segment_distances_m(usable_points)
    if not elevations:
        return [], [], 0, []

    cleaned = [elevations[0]]
    capped_steps = 0
    for elevation in elevations[1:]:
        previous = cleaned[-1]
        delta = elevation - previous
        if delta > config.max_step_up_m:
            elevation = previous + config.max_step_up_m
            capped_steps += 1
        elif delta < -config.max_step_down_m:
            elevation = previous - config.max_step_down_m
            capped_steps += 1
        cleaned.append(elevation)
    return cleaned, distances, capped_steps, usable_points


def _edge_slope(segment: np.ndarray) -> float:
    """Estimate the local slope at a profile edge using a least-squares fit."""
    if len(segment) < 2:
        return 0.0
    positions = np.arange(len(segment), dtype=float)
    try:
        return float(np.polyfit(positions, segment, 1)[0])
    except (TypeError, ValueError, np.linalg.LinAlgError):
        return float(segment[-1] - segment[0]) / (len(segment) - 1)


def _extrapolate_edges(values: np.ndarray, half_window: int) -> np.ndarray:
    """Pad a profile by continuing its edge slopes instead of mirroring values."""
    if half_window == 0 or len(values) < 2:
        return values

    left_slope = _edge_slope(values[: min(half_window, len(values))])
    right_slope = _edge_slope(values[-min(half_window, len(values)) :])
    left_pad = [values[0] - left_slope * step for step in range(half_window, 0, -1)]
    right_pad = [values[-1] + right_slope * step for step in range(1, half_window + 1)]
    return np.concatenate([np.asarray(left_pad), values, np.asarray(right_pad)])


def _smooth_profile(elevations: list[float], window_size: int) -> np.ndarray:
    """
    Apply a slope-preserving moving average that keeps the input length.

    Args:
        elevations: Step-capped elevation series.
        window_size: Requested odd window width; clamped to the profile length.
    Returns:
        Smoothed series with exactly the same number of samples as the input.
    """
    count = len(elevations)
    if count == 0:
        return np.array([], dtype=float)

    window = max(1, min(int(window_size), count if count % 2 == 1 else count - 1))
    if window % 2 == 0:
        window -= 1
    window = max(1, window)

    values = np.asarray(elevations, dtype=float)
    padded = _extrapolate_edges(values, window // 2)
    weights = np.ones(window) / window
    return np.convolve(padded, weights, mode="valid")


def _noise_floor(distances: list[float], config: TerrainConfig) -> float:
    """
    Scale the hysteresis threshold to the median spacing of the elevation grid.

    Args:
        distances: Ground distances between profile samples.
        config: Terrain processing parameters.
    Returns:
        Adaptive noise floor in meters.
    """
    positive = [distance for distance in distances if distance > 0]
    median_spacing = float(np.median(positive)) if positive else config.short_segment_threshold_m
    if median_spacing < config.short_segment_threshold_m:
        extra = (config.short_segment_threshold_m - median_spacing) * config.jitter_noise_multiplier
    else:
        extra = 0.0
    return round(min(config.base_noise_floor_m + extra, config.max_noise_floor_m), 3)


def _detect_segments(smoothed: np.ndarray, noise_floor_m: float) -> list[tuple[int, int]]:
    """
    Locate contiguous ascending runs using peak/valley hysteresis.

    Args:
        smoothed: Length-preserving smoothed elevation profile.
        noise_floor_m: Minimum reversal required to end a run.
    Returns:
        List of (start_index, end_index) pairs for every ascending run.
    """
    if len(smoothed) < 2:
        return []

    segments: list[tuple[int, int]] = []
    valley = 0
    peak = 0
    climbing = True

    for index in range(1, len(smoothed)):
        elevation = float(smoothed[index])
        if climbing:
            if elevation > float(smoothed[peak]):
                peak = index
            elif elevation < float(smoothed[peak]) - noise_floor_m:
                if peak > valley:
                    segments.append((valley, peak))
                valley = index
                climbing = False
        else:
            if elevation < float(smoothed[valley]):
                valley = index
            elif elevation > float(smoothed[valley]) + noise_floor_m:
                climbing = True
                peak = index

    if climbing and peak > valley:
        segments.append((valley, peak))
    return segments


def _refine_turn_index(elevations: list[float], index: int, radius: int, find_max: bool) -> int:
    """Find the raw-profile valley or peak near a smoothed turning point.

    The light smoothing pass removes GPS jitter but slightly shifts extrema.
    Looking back at the capped raw profile keeps the reported gain faithful to
    the measured elevations instead of to the filtered shape.
    """
    low = max(0, index - radius)
    high = min(len(elevations) - 1, index + radius)
    window = elevations[low : high + 1]
    if not window:
        return index
    offset = (
        max(range(len(window)), key=window.__getitem__)
        if find_max
        else min(range(len(window)), key=window.__getitem__)
    )
    return low + offset


def _cumulative_distances(distances: list[float], sample_count: int) -> list[float]:
    """Build a cumulative distance array aligned with the elevation samples."""
    cumulative = [0.0]
    for distance in distances[: max(0, sample_count - 1)]:
        cumulative.append(cumulative[-1] + max(0.0, distance))
    while len(cumulative) < sample_count:
        cumulative.append(cumulative[-1])
    return cumulative


def _segment_gradient(
    elevations: list[float], cumulative: list[float], start: int, end: int
) -> float:
    """Return the steepest positive gradient inside a segment, capped at 45%."""
    steepest = 0.0
    for index in range(start + 1, end + 1):
        step = cumulative[index] - cumulative[index - 1]
        if step > 0:
            gradient = (elevations[index] - elevations[index - 1]) / step * 100.0
            steepest = max(steepest, gradient)
    return round(min(steepest, 45.0), 1)


def _route_max_gradient(elevations: list[float], cumulative: list[float]) -> float:
    """Return the steepest positive gradient found anywhere on the route."""
    if len(elevations) < 2:
        return 0.0
    return _segment_gradient(elevations, cumulative, 0, len(elevations) - 1)


def _fiets_category(fiets_index: float) -> str:
    """Map a FIETS index to a pro-cycling climb category."""
    for threshold, label in _FIETS_CATEGORIES:
        if fiets_index >= threshold:
            return label
    return "C5 - Gentle Rise"


def _dominant_extra_value(extra: Any) -> Any:
    """Read the most represented value from an ORS extra-info summary."""
    if not isinstance(extra, dict):
        return None
    summary = extra.get("summary") or []
    if not isinstance(summary, list) or not summary:
        return None
    try:
        return max(summary, key=lambda item: item.get("distance", item.get("amount", 0)))["value"]
    except (TypeError, KeyError, ValueError):
        return None


def infer_technical_difficulty(
    extras: dict[str, Any] | None, max_gradient: float = 0.0
) -> dict[str, Any]:
    """
    Derive a technical grade from OSM tags, with an explicit confidence score.

    Args:
        extras: OpenRouteService extra-info block (surface, waytype, optional tags).
        max_gradient: Steepest pitch measured on the profile.
    Returns:
        Dict with label, confidence and source. Missing tags never yield a
        high-confidence rating.
    """
    extra_info = extras or {}
    for key in ("mtb_scale", "traildifficulty", "technical_difficulty"):
        tagged = _dominant_extra_value(extra_info.get(key))
        if tagged is not None:
            return {"label": f"S{tagged}", "confidence": 0.9, "source": f"osm:{key}"}

    surface_value = _dominant_extra_value(extra_info.get("surface"))
    waytype_value = _dominant_extra_value(extra_info.get("waytype"))
    if surface_value is None and waytype_value is None and max_gradient < 15.0:
        return {"label": "Unknown", "confidence": 0.0, "source": "missing"}

    hint = _SURFACE_TECH_HINTS.get(str(surface_value), 0)
    hint += _WAYTYPE_TECH_HINTS.get(str(waytype_value), 0)
    if max_gradient >= 15.0:
        hint += 1

    labels = {
        0: "S0 - Easy",
        1: "S1 - Moderate",
        2: "S2 - Technical",
        3: "S3 - Difficult",
    }
    label = labels.get(min(hint, 3), "S4+ - Expert")
    has_tags = surface_value is not None or waytype_value is not None
    confidence = 0.55 if has_tags else 0.3
    return {
        "label": label,
        "confidence": confidence,
        "source": "inferred:surface+waytype" if has_tags else "inferred:gradient",
    }


def _data_confidence(
    sample_count: int, distances: list[float], capped_steps: int, config: TerrainConfig
) -> float:
    """Score how trustworthy the derived terrain metrics are (0.0 to 1.0).

    Heuristic score, not a statistical confidence interval. It combines
    sample density and step-stability; it does not measure DEM absolute error.
    """
    if sample_count < config.min_profile_points:
        return 0.0
    positive = [distance for distance in distances if distance > 0]
    median_spacing = float(np.median(positive)) if positive else config.short_segment_threshold_m
    density_score = max(0.0, 1.0 - max(0.0, median_spacing - 10.0) / 90.0)
    stability_score = max(0.0, 1.0 - capped_steps / max(1, sample_count - 1))
    return round(min(1.0, (density_score + stability_score) / 2.0), 2)


CONFIDENCE_BASIS = (
    "Heuristic score from sample density and step stability; not a statistical "
    "confidence interval or DEM vertical-error bound."
)


class TerrainService:
    """Offline elevation filtering and true-climb segmentation service."""

    def __init__(self, config: TerrainConfig | None = None) -> None:
        self.config = config or TerrainConfig()

    def analyze_profile(
        self,
        geometry: list[Any],
        bike_type: str = "",
        extras: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Derive ascent, gradients and significant climbs from an elevation profile.

        Args:
            geometry: GeoJSON coordinates [lon, lat, elevation].
            bike_type: Discipline label, used only for presentation wording.
            extras: ORS extra-info block used for technical grading.
        Returns:
            Dictionary with geometry-derived terrain metrics. Always contains
            the same keys, including for short or invalid profiles.
        """
        elevations, distances, capped_steps, usable_points = _extract_profile(geometry, self.config)
        sample_count = len(elevations)
        max_gradient = 0.0
        if sample_count >= 2:
            cumulative = _cumulative_distances(distances, sample_count)
            max_gradient = _route_max_gradient(elevations, cumulative)
        technical = infer_technical_difficulty(extras, max_gradient)

        if sample_count < self.config.min_profile_points:
            return {
                "total_ascent_m": 0.0,
                "max_gradient": 0.0,
                "avg_gradient": 0.0,
                "avg_climb_gradient": 0.0,
                "profile_length_m": 0.0,
                "climbs": [],
                "climb_profile_coordinates": [],
                "climb_category": "Flat / Rolling",
                "data_confidence": 0.0,
                "data_confidence_basis": CONFIDENCE_BASIS,
                "technical_difficulty": technical,
                "profile_points": sample_count,
                "noise_floor_m": self.config.base_noise_floor_m,
                "micro_spikes": False,
                "warnings": [],
            }

        cumulative = _cumulative_distances(distances, sample_count)
        smoothed = _smooth_profile(elevations, self.config.smoothing_window)
        noise_floor = _noise_floor(distances, self.config)
        profile_length_m = round(cumulative[-1], 1)

        climbs: list[dict[str, Any]] = []
        climb_profile_coordinates: list[list[list[float]] | None] = []
        total_ascent = 0.0
        radius = max(1, self.config.smoothing_window // 2)
        previous_end = 0

        for start, end in _detect_segments(smoothed, noise_floor):
            raw_start = max(
                previous_end, _refine_turn_index(elevations, start, radius, find_max=False)
            )
            raw_end = _refine_turn_index(elevations, end, radius, find_max=True)
            if raw_end <= raw_start:
                continue
            previous_end = raw_end

            gain = max(0.0, elevations[raw_end] - elevations[raw_start])
            length = cumulative[raw_end] - cumulative[raw_start]
            if gain <= 0 or length <= 0:
                continue
            avg_gradient = gain / length * 100.0
            if (
                gain >= self.config.min_ascent_gain_m
                and avg_gradient >= self.config.min_ascent_gradient_percent
            ):
                total_ascent += gain
            if (
                gain < self.config.min_climb_gain_m
                or avg_gradient < self.config.min_climb_gradient_percent
                or length < self.config.min_climb_length_m
            ):
                continue

            summit_elevation = float(elevations[raw_end])
            fiets_index = gain**2 / (length * 10.0) + max(0.0, (summit_elevation - 1000.0) / 1000.0)
            climbs.append(
                {
                    "start_index": raw_start,
                    "end_index": raw_end,
                    "length_m": round(length, 1),
                    "gain_m": round(gain, 1),
                    "avg_gradient": round(avg_gradient, 1),
                    "max_gradient": _segment_gradient(elevations, cumulative, raw_start, raw_end),
                    "summit_elevation_m": round(summit_elevation, 1),
                    "fiets_index": round(fiets_index, 2),
                    "category": _fiets_category(fiets_index),
                }
            )
            if length >= CLIMB_PROFILE_MIN_LENGTH_M:
                climb_profile_coordinates.append(
                    [
                        [float(point[0]), float(point[1]), float(elevations[index])]
                        for index, point in enumerate(usable_points)
                        if raw_start <= index <= raw_end
                    ]
                )
            else:
                climb_profile_coordinates.append(None)

        total_ascent = round(total_ascent, 1)
        avg_gradient = total_ascent / profile_length_m * 100.0 if profile_length_m > 0 else 0.0
        climb_length = sum(climb["length_m"] for climb in climbs)
        climb_gain = sum(climb["gain_m"] for climb in climbs)
        avg_climb_gradient = climb_gain / climb_length * 100.0 if climb_length > 0 else 0.0
        max_gradient = round(max_gradient, 1)

        if climbs:
            hardest = max(climbs, key=lambda climb: climb["fiets_index"])
            climb_category = hardest["category"]
        else:
            climb_category = "Flat / Rolling"
        if "enduro" in str(bike_type).lower() and climb_category != "Flat / Rolling":
            climb_category = f"Enduro Tech: {climb_category}"

        warnings: list[str] = []
        if max_gradient >= 20.0:
            warnings.append(
                f"Micro-pitch up to {max_gradient}%: expect hike-a-bike or high battery drain."
            )

        return {
            "total_ascent_m": total_ascent,
            "max_gradient": max_gradient,
            "avg_gradient": round(avg_gradient, 2),
            "avg_climb_gradient": round(avg_climb_gradient, 2),
            "profile_length_m": profile_length_m,
            "climbs": climbs,
            "climb_profile_coordinates": climb_profile_coordinates,
            "climb_category": climb_category,
            "data_confidence": _data_confidence(sample_count, distances, capped_steps, self.config),
            "data_confidence_basis": CONFIDENCE_BASIS,
            "technical_difficulty": technical,
            "profile_points": sample_count,
            "noise_floor_m": noise_floor,
            "micro_spikes": max_gradient >= 20.0,
            "warnings": warnings,
        }


service = TerrainService()


def analyze_terrain_profile(
    geometry: list[Any],
    bike_type: str = "",
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Analyze a GeoJSON elevation profile using the shared terrain service.

    Args:
        geometry: GeoJSON coordinates [lon, lat, elevation].
        bike_type: Discipline label used for climb-category wording.
        extras: ORS extra-info block used for technical grading.
    Returns:
        Geometry-derived terrain metrics with a "total_ascent_m" key.
    """
    return service.analyze_profile(geometry=geometry, bike_type=bike_type, extras=extras)
