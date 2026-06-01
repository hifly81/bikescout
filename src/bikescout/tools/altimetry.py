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

import base64
import io
import logging
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Sequence

import matplotlib
matplotlib.use("Agg")

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np



PlotStyle = Literal["sparkline", "filled", "bars"]


class AltimetryError(Exception):
    """Domain-specific altimetry error."""


@dataclass(frozen=True)
class AltimetryConfig:
    storage_dir: Path | None = None
    cleanup_max_age_seconds: int = 3 * 86400
    abs_min_elevation_m: float = -450.0
    abs_max_elevation_m: float = 9000.0
    spike_grade_ratio_threshold: float = 0.60
    min_grade_distance_m: float = 3.0
    default_width_in: int = 8
    default_height_in: int = 3
    dpi: int = 100
    title_prefix: str = "Tactical Elevation Profile"


@dataclass(frozen=True)
class AltimetryPlotResult:
    image_base64: str
    total_distance_km: float


@dataclass(frozen=True)
class AltimetryStorageResult:
    status: str
    message: str
    mcp_resource_uri: str
    file_location: str
    style_applied: PlotStyle
    dimensions: str
    total_distance_km: float


class AltimetryService:
    def __init__(self, config: AltimetryConfig | None = None, logger: logging.Logger | None = None) -> None:
        self.config = config or AltimetryConfig()
        self.logger = logger or logging.getLogger(__name__)

    @property
    def storage_dir(self) -> Path:
        if self.config.storage_dir is not None:
            return self.config.storage_dir
        return Path.home() / ".bikescout" / "altimetry"

    def generate_plot(
            self,
            geometry: Iterable[Sequence[object]],
            width: int | None = None,
            height: int | None = None,
            style: PlotStyle = "filled",
    ) -> AltimetryPlotResult:
        effective_width = self.config.default_width_in if width is None else width
        effective_height = self.config.default_height_in if height is None else height

        self._validate_dimensions(effective_width, effective_height)
        self._validate_style(style)

        distances_m, elevations = self._build_profile_arrays(geometry)
        image_base64 = self._render_plot(
            distances_m=distances_m,
            elevations=elevations,
            width=effective_width,
            height=effective_height,
            style=style,
        )
        return AltimetryPlotResult(
            image_base64=image_base64,
            total_distance_km=float(distances_m[-1] / 1000.0),
    )

    def create_profile_image(
            self,
            geometry_obj: object,
            uuid_input: str | None,
            width: int | None = None,
            height: int | None = None,
            style: PlotStyle = "filled",
    ) -> dict[str, object]:
        try:
            if not hasattr(geometry_obj, "coordinates"):
                raise AltimetryError("Geometry object has no 'coordinates' attribute.")

            effective_width = self.config.default_width_in if width is None else width
            effective_height = self.config.default_height_in if height is None else height

            coordinates = geometry_obj.coordinates
            result = self.generate_plot(
                geometry=coordinates,
                width=effective_width,
                height=effective_height,
                style=style,
            )

            storage_dir = self.storage_dir
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.cleanup_old_png_files(storage_dir)

            unique_id = self._sanitize_filename_component(
                uuid_input,
                fallback=uuid.uuid4().hex[:12],
            )
            filename = f"bs_altimetry_{unique_id}.png"
            file_path = storage_dir / filename
            file_path.write_bytes(base64.b64decode(result.image_base64))

            return {
                "status": "Success",
                "message": "Elevation profile image created.",
                "mcp_resource_uri": f"bikescout://altimetry/{filename}",
                "file_location": str(file_path),
                "style_applied": style,
                "dimensions": f"{effective_width}x{effective_height} in",
                "total_distance_km": round(result.total_distance_km, 2),
            }
        except AltimetryError as exc:
            return {"status": "Error", "message": str(exc)}
        except Exception as exc:
            self.logger.exception("Unexpected altimetry failure")
            return {"status": "Error", "message": f"Altimetry home-storage failed: {exc}"}

    def cleanup_old_png_files(self, directory: Path) -> None:
        now = time.time()
        for file_path in directory.glob("*.png"):
            try:
                if file_path.is_file() and (now - file_path.stat().st_mtime) > self.config.cleanup_max_age_seconds:
                    file_path.unlink()
            except OSError:
                self.logger.debug("Could not remove stale PNG: %s", file_path, exc_info=True)

    def _build_profile_arrays(self, geometry: Iterable[Sequence[object]]) -> tuple[np.ndarray, np.ndarray]:
        coords = self._normalize_geometry(geometry)
        lons = coords[:, 0]
        lats = coords[:, 1]
        raw_elevations = coords[:, 2]

        segment_distances_m = self._haversine_segment_distances_m(lons, lats)
        cumulative_distances_m = np.concatenate(([0.0], np.cumsum(segment_distances_m)))
        elevations = self._clean_elevations(raw_elevations, segment_distances_m)
        return cumulative_distances_m, elevations

    def _normalize_geometry(self, geometry: Iterable[Sequence[object]]) -> np.ndarray:
        points: list[list[float]] = []

        for point in geometry:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue

            try:
                lon = float(point[0])
                lat = float(point[1])
                ele = float(point[2]) if len(point) > 2 and point[2] is not None else 0.0
            except (TypeError, ValueError):
                continue

            if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
                continue

            points.append([lon, lat, ele])

        if len(points) < 2:
            raise AltimetryError("Geometry must contain at least two valid coordinates.")

        return np.array(points, dtype=float)

    def _clean_elevations(self, elevations: np.ndarray, segment_distances_m: np.ndarray) -> np.ndarray:
        cleaned = elevations.astype(float).copy()
        valid_mask = (
                (cleaned >= self.config.abs_min_elevation_m)
                & (cleaned <= self.config.abs_max_elevation_m)
        )

        if len(cleaned) >= 3 and len(segment_distances_m) >= 2:
            prev_delta = np.abs(cleaned[1:-1] - cleaned[:-2])
            next_delta = np.abs(cleaned[2:] - cleaned[1:-1])

            prev_dist = np.maximum(segment_distances_m[:-1], 1.0)
            next_dist = np.maximum(segment_distances_m[1:], 1.0)

            prev_grade_ratio = prev_delta / prev_dist
            next_grade_ratio = next_delta / next_dist

            spike_mask = (
                    (prev_grade_ratio > self.config.spike_grade_ratio_threshold)
                    & (next_grade_ratio > self.config.spike_grade_ratio_threshold)
            )
            valid_mask[1:-1] &= ~spike_mask

        return self._interpolate_invalid(cleaned, valid_mask)

    @staticmethod
    def _interpolate_invalid(values: np.ndarray, valid_mask: np.ndarray) -> np.ndarray:
        if len(values) == 0:
            return values.copy()

        if not np.any(valid_mask):
            return np.zeros_like(values, dtype=float)

        xp = np.flatnonzero(valid_mask)
        fp = values[valid_mask]
        return np.interp(np.arange(len(values)), xp, fp)

    def _compute_segment_grades_percent(
            self,
            elevations: np.ndarray,
            segment_distances_m: np.ndarray,
    ) -> np.ndarray:
        if len(elevations) < 2:
            return np.array([], dtype=float)

        elevation_deltas = np.diff(elevations)
        safe_distances = np.maximum(segment_distances_m, self.config.min_grade_distance_m)
        grades = (elevation_deltas / safe_distances) * 100.0
        return np.clip(grades, -25.0, 25.0)

    def _render_plot(
            self,
            distances_m: np.ndarray,
            elevations: np.ndarray,
            width: int,
            height: int,
            style: PlotStyle,
    ) -> str:
        dist_km = distances_m / 1000.0
        segment_distances_m = np.diff(distances_m)
        grades = self._compute_segment_grades_percent(elevations, segment_distances_m)

        fig, ax = plt.subplots(figsize=(width, height), dpi=self.config.dpi)

        cmap = mcolors.LinearSegmentedColormap.from_list(
            "altimetry_grade",
            ["#2ecc71", "#f1c40f", "#e74c3c"],
        )
        norm = mcolors.Normalize(vmin=0, vmax=12)

        min_ele = float(np.min(elevations))
        baseline = min_ele - 20.0

        if style == "sparkline":
            ax.plot(dist_km, elevations, color="#2c3e50", linewidth=2.0)
            ax.axis("off")

        elif style == "bars":
            widths = np.diff(
                dist_km,
                append=dist_km[-1] + max(float(dist_km[-1]) * 1e-6, 1e-6),
            )
            widths = np.maximum(widths, 1e-4)

            if len(grades) > 0:
                colors = cmap(norm(np.abs(np.append(grades, grades[-1]))))
            else:
                colors = ["#95a5a6"] * len(dist_km)

            ax.bar(
                dist_km,
                elevations - baseline,
                width=widths,
                bottom=baseline,
                color=colors,
                align="edge",
                linewidth=0,
                )
            ax.plot(dist_km, elevations, color="#2c3e50", linewidth=0.7, alpha=0.7)

        else:
            for i in range(len(dist_km) - 1):
                x = dist_km[i:i + 2]
                y = elevations[i:i + 2]
                grade = abs(grades[i]) if i < len(grades) else 0.0
                ax.fill_between(x, y, baseline, color=cmap(norm(grade)), alpha=0.8)
            ax.plot(dist_km, elevations, color="#2c3e50", linewidth=1.5)

        if style != "sparkline":
            ax.set_facecolor("#ffffff")
            ax.set_title(f"{self.config.title_prefix} ({style.capitalize()})", fontsize=10, fontweight="bold")
            ax.set_xlabel("Distance (km)", fontsize=8)
            ax.set_ylabel("Elevation (m)", fontsize=8)
            ax.grid(True, linestyle="--", alpha=0.3)

        fig.tight_layout()

        buffer = io.BytesIO()
        try:
            fig.savefig(buffer, format="png", bbox_inches="tight")
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode("utf-8")
        finally:
            buffer.close()
            plt.close(fig)

    @staticmethod
    def _haversine_segment_distances_m(lons: np.ndarray, lats: np.ndarray) -> np.ndarray:
        if len(lons) < 2:
            return np.array([], dtype=float)

        r = 6_371_000.0

        lon1 = np.radians(lons[:-1])
        lat1 = np.radians(lats[:-1])
        lon2 = np.radians(lons[1:])
        lat2 = np.radians(lats[1:])

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
        c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
        return r * c

    @staticmethod
    def _sanitize_filename_component(value: str | None, fallback: str = "profile") -> str:
        raw = (value or "").strip()
        if not raw:
            return fallback
        cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", raw)
        return (cleaned[:64] or fallback)

    @staticmethod
    def _validate_dimensions(width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            raise AltimetryError("Width and height must be positive.")

    @staticmethod
    def _validate_style(style: str) -> None:
        if style not in {"sparkline", "filled", "bars"}:
            raise AltimetryError(f"Unsupported style: {style}")


def get_elevation_profile_image(
        geometry: object,
        uuid_input: str | None,
        width: int = 8,
        height: int = 3,
        style: PlotStyle = "filled",
) -> dict[str, object]:
    service = AltimetryService()
    return service.create_profile_image(
        geometry_obj=geometry,
        uuid_input=uuid_input,
        width=width,
        height=height,
        style=style,
    )