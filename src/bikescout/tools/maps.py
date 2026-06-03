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

import logging
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Sequence

import matplotlib.colors as mcolors
from staticmap import CircleMarker, Line, StaticMap


MapStyle = Literal["gradient", "solid"]


class TacticalMapError(Exception):
    """Domain-specific error for tactical map generation."""


@dataclass(frozen=True)
class TacticalMapConfig:
    storage_dir: Path | None = None
    cleanup_max_age_seconds: int = 3 * 86400
    image_width_px: int = 800
    image_height_px: int = 600
    default_line_color: str = "red"
    default_line_width: int = 7
    tile_url_template: str = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    gradient_min_percent: float = 0.0
    gradient_max_percent: float = 12.0
    zero_run_threshold_m: float = 0.5


@dataclass(frozen=True)
class TacticalMapResult:
    status: str
    message: str
    mcp_resource_uri: str
    file_location: str
    style_applied: MapStyle


class TacticalMapService:
    _GRADE_CMAP = mcolors.LinearSegmentedColormap.from_list(
        "bike_grade",
        ["#2ecc71", "#f1c40f", "#e74c3c"],
    )

    def __init__(self, config: TacticalMapConfig | None = None, logger: logging.Logger | None = None) -> None:
        self.config = config or TacticalMapConfig()
        self.logger = logger or logging.getLogger(__name__)
        self._grade_norm = mcolors.Normalize(
            vmin=self.config.gradient_min_percent,
            vmax=self.config.gradient_max_percent,
        )

    @property
    def storage_dir(self) -> Path:
        if self.config.storage_dir is not None:
            return self.config.storage_dir
        return Path.home() / ".bikescout" / "maps"

    def save_local_tactical_map(
            self,
            filename_part: str,
            geojson_data: dict,
            use_gradient: bool = True,
            line_color: str | None = None,
            line_width: int | None = None,
    ) -> dict[str, object]:
        try:
            normalized_points = self._extract_linestring_points(geojson_data)

            effective_line_color = self.config.default_line_color if line_color is None else line_color
            effective_line_width = self.config.default_line_width if line_width is None else line_width

            if effective_line_width <= 0:
                raise TacticalMapError("Line width must be positive.")

            storage_dir = self.storage_dir
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.cleanup_old_png_files(storage_dir)

            map_obj = self._build_map(
                points=normalized_points,
                use_gradient=use_gradient,
                line_color=effective_line_color,
                line_width=effective_line_width,
            )

            safe_name = self._sanitize_filename_component(filename_part, fallback="map")
            filename = f"tactical_map_{safe_name}_{int(time.time())}.png"
            file_path = storage_dir / filename

            image = map_obj.render()
            image.save(file_path)

            return {
                "status": "Success",
                "message": "Tactical map created successfully.",
                "mcp_resource_uri": f"bikescout://maps/{filename}",
                "file_location": str(file_path),
                "style_applied": "gradient" if self._should_use_gradient(normalized_points, use_gradient) else "solid",
            }

        except TacticalMapError as exc:
            return {"status": "Error", "message": str(exc)}
        except Exception as exc:
            self.logger.exception("Unexpected tactical map failure")
            return {"status": "Error", "message": f"Local Map Generation Failed: {exc}"}

    def cleanup_old_png_files(self, directory: Path) -> None:
        now = time.time()
        for file_path in directory.glob("*.png"):
            try:
                if file_path.is_file() and (now - file_path.stat().st_mtime) > self.config.cleanup_max_age_seconds:
                    file_path.unlink()
            except OSError:
                self.logger.debug("Could not remove stale PNG: %s", file_path, exc_info=True)

    def _build_map(
            self,
            points: list[tuple[float, float, float | None]],
            use_gradient: bool,
            line_color: str,
            line_width: int,
    ) -> StaticMap:
        map_obj = StaticMap(
            self.config.image_width_px,
            self.config.image_height_px,
            url_template=self.config.tile_url_template,
        )

        actual_use_gradient = self._should_use_gradient(points, use_gradient)

        if actual_use_gradient:
            for p1, p2 in zip(points[:-1], points[1:]):
                segment_color = self._segment_color_from_points(p1, p2)
                map_obj.add_line(Line([[p1[0], p1[1]], [p2[0], p2[1]]], segment_color, line_width))
        else:
            clean_coords = [[p[0], p[1]] for p in points]
            map_obj.add_line(Line(clean_coords, line_color, line_width))

        start = points[0]
        end = points[-1]

        map_obj.add_marker(CircleMarker([start[0], start[1]], "white", 10))
        map_obj.add_marker(CircleMarker([start[0], start[1]], "green", 6))

        map_obj.add_marker(CircleMarker([end[0], end[1]], "white", 10))
        map_obj.add_marker(CircleMarker([end[0], end[1]], "black", 6))

        return map_obj

    def _extract_linestring_points(self, geojson_data: dict) -> list[tuple[float, float, float | None]]:
        if not isinstance(geojson_data, dict):
            raise TacticalMapError("GeoJSON payload must be a dictionary.")

        features = geojson_data.get("features")
        if not isinstance(features, list) or not features:
            raise TacticalMapError("No features found in GeoJSON.")

        geometry = None
        for feature in features:
            if not isinstance(feature, dict):
                continue
            candidate = feature.get("geometry")
            if isinstance(candidate, dict) and candidate.get("type") == "LineString":
                geometry = candidate
                break

        if geometry is None:
            raise TacticalMapError("Invalid or missing LineString geometry.")

        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise TacticalMapError("Insufficient coordinates for mapping.")

        points: list[tuple[float, float, float | None]] = []
        for coord in coordinates:
            if not isinstance(coord, (list, tuple)) or len(coord) < 2:
                continue

            try:
                lon = float(coord[0])
                lat = float(coord[1])
                ele = float(coord[2]) if len(coord) > 2 and coord[2] is not None else None
            except (TypeError, ValueError):
                continue

            if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
                continue

            points.append((lon, lat, ele))

        if len(points) < 2:
            raise TacticalMapError("Insufficient valid coordinates for mapping.")

        return points

    def _should_use_gradient(
            self,
            points: Sequence[tuple[float, float, float | None]],
            requested: bool,
    ) -> bool:
        if not requested:
            return False
        return all(point[2] is not None for point in points)

    def _segment_color_from_points(
            self,
            p1: tuple[float, float, float | None],
            p2: tuple[float, float, float | None],
    ) -> str:
        grade = self._compute_segment_grade_percent(p1, p2)
        return self._get_gradient_color(grade)

    def _compute_segment_grade_percent(
            self,
            p1: tuple[float, float, float | None],
            p2: tuple[float, float, float | None],
    ) -> float:
        if p1[2] is None or p2[2] is None:
            return 0.0

        rise = p2[2] - p1[2]
        run = self._approx_segment_run_m(p1, p2)

        if run <= self.config.zero_run_threshold_m:
            return 0.0

        return (rise / run) * 100.0

    @staticmethod
    def _approx_segment_run_m(
            p1: tuple[float, float, float | None],
            p2: tuple[float, float, float | None],
    ) -> float:
        lat_rad = math.radians(p1[1])
        dx = (p2[0] - p1[0]) * math.cos(lat_rad) * 111111.0
        dy = (p2[1] - p1[1]) * 111111.0
        return math.hypot(dx, dy)

    def _get_gradient_color(self, grade: float) -> str:
        color = self._GRADE_CMAP(self._grade_norm(abs(grade)))
        return mcolors.to_hex(color)

    @staticmethod
    def _sanitize_filename_component(value: str | None, fallback: str = "map") -> str:
        raw = (value or "").strip()
        if not raw:
            return fallback
        cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", raw)
        return cleaned[:64] or fallback


def save_local_tactical_map(
        filename_part: str,
        geojson_data: dict,
        use_gradient: bool = True,
        line_color: str = "red",
        line_width: int = 7,
) -> dict[str, object]:
    service = TacticalMapService()
    return service.save_local_tactical_map(
        filename_part=filename_part,
        geojson_data=geojson_data,
        use_gradient=use_gradient,
        line_color=line_color,
        line_width=line_width,
    )