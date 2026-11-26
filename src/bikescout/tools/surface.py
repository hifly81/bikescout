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

from dataclasses import dataclass
from typing import Any

import requests

from bikescout.tools.battery import calculate_battery_drain
from bikescout.tools.bike_setup import analyze_compatibility, get_tire_setup
from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.terrain import analyze_terrain_profile, segment_distances_m

ORS_DIRECTIONS_URL = "https://api.heigit.org/openrouteservice/v2/directions"

# TAEL moisture is expressed in millimeters; 20mm is the Extreme threshold.
MUD_NORMALIZATION_MAX_MM = 20.0


def _normalize_mud_index(raw_mud_mm: Any) -> float:
    """Convert a raw TAEL moisture reading into a 0.0-1.0 mud severity index."""
    try:
        value = float(raw_mud_mm)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(value / MUD_NORMALIZATION_MAX_MM, 1.0))


@dataclass(frozen=True)
class SurfaceAnalyzerConfig:
    ors_timeout_seconds: float = 7.0


def _extract_dominant_surface(surface_extra, surface_map):
    if not surface_extra or "summary" not in surface_extra:
        return "Unknown"

    dominant_val = max(surface_extra["summary"], key=lambda x: x["distance"])["value"]
    return surface_map.get(dominant_val, "Unknown")


class SurfaceAnalyzerService:
    def __init__(
        self,
        config: SurfaceAnalyzerConfig | None = None,
        http_session: Any | None = None,
        mud_analyzer=None,
        compatibility_analyzer=None,
        tire_setup_getter=None,
        battery_drain_calculator=None,
    ) -> None:
        self.config = config or SurfaceAnalyzerConfig()
        self.http_session = http_session or requests
        self.mud_analyzer = mud_analyzer or get_mud_risk_analysis
        self.compatibility_analyzer = compatibility_analyzer or analyze_compatibility
        self.tire_setup_getter = tire_setup_getter or get_tire_setup
        self.battery_drain_calculator = battery_drain_calculator or calculate_battery_drain

    def get_surface_analyzer(
        self,
        api_key,
        lat,
        lon,
        rider,
        bike,
        mission,
        target_date: str | None = None,
        route_feature: dict[str, Any] | None = None,
    ):
        """
        Analyze surface, terrain and mechanical setup for a cycling route.

        When ``route_feature`` is supplied (as the orchestrator does with the
        route it already selected), its geometry and extra info are analyzed
        directly. No second ORS request is made, so the reported distance,
        ascent and climb metrics always describe the very same geometry that is
        exported to GPX, map and altimetry. Without a provided feature the
        service keeps its standalone behavior and requests a route from ORS.

        Args:
            api_key: OpenRouteService API key.
            lat: Starting latitude, used for mud intelligence on the standalone path.
            lon: Starting longitude, used for mud intelligence on the standalone path.
            rider: Rider profile.
            bike: Bike setup.
            mission: Mission constraints.
            target_date: Optional target date for mud analysis.
            route_feature: Optional ORS route feature to analyze instead of
                requesting a new route from ORS.
        Returns:
            A structured surface analysis report with status "Success" or "Error".
        """
        safe_complexity = self._safe_complexity(getattr(mission, "complexity", 10))
        safe_length = self._safe_length_m(getattr(mission, "total_length_km", 0))
        if route_feature is not None:
            attempts = [(str(getattr(mission, "profile", "cycling-regular")), [])]
        else:
            attempts = self._attempts_for_profile(getattr(mission, "profile", "cycling-regular"))

        last_error = ""
        for current_profile, requested_extras in attempts:
            try:
                if route_feature is not None:
                    data = {"features": [route_feature]}
                else:
                    url = f"{ORS_DIRECTIONS_URL}/{current_profile}/geojson"
                    headers = {"Authorization": api_key, "Content-Type": "application/json"}

                    body = self._request_body(
                        lat=lat,
                        lon=lon,
                        mission=mission,
                        safe_length=safe_length,
                        safe_complexity=safe_complexity,
                        requested_extras=requested_extras,
                    )

                    res = self.http_session.post(
                        url, json=body, headers=headers, timeout=self.config.ors_timeout_seconds
                    )

                    if res.status_code != 200:
                        try:
                            detail = res.json().get("error", {}).get("message", res.text)
                        except Exception:
                            detail = res.text

                        last_error = f"ORS {res.status_code}: {detail}"
                        continue

                    data = res.json()

                feature = data["features"][0]
                props = feature.get("properties", {})
                geometry = feature.get("geometry", {}).get("coordinates", [])
                extras = props.get("extras", {})

                terrain = analyze_terrain_profile(
                    geometry,
                    bike_type=bike.bike_type,
                    extras=extras,
                )
                clean_ascent = terrain["total_ascent_m"]
                real_dist_m = terrain["profile_length_m"] or self._geometry_distance_m(geometry)

                surface_map = {
                    0: "Unknown",
                    1: "Asphalt",
                    2: "Unpaved",
                    3: "Paved",
                    5: "Gravel",
                    11: "Grass",
                    14: "Concrete",
                }
                dominant_surface = _extract_dominant_surface(extras.get("surface", {}), surface_map)

                breakdown, warnings, compatible = self.compatibility_analyzer(
                    bike.bike_type,
                    bike.tire_width_mm,
                    extras,
                    surface_map,
                    getattr(bike, "rim_internal_width_mm", None),
                )

                mud_analysis = self.mud_analyzer(lat, lon, dominant_surface, target_date)
                t_analysis = mud_analysis.get("tactical_analysis") or {}
                raw_mud = t_analysis.get("mud_risk_numeric")
                mud_score_val = float(raw_mud) if raw_mud is not None else 0.0
                mud_index = _normalize_mud_index(mud_score_val)

                tire_display = self.tire_setup_getter(
                    bike_type=bike.bike_type,
                    tire_size_option=bike.tire_size,
                    mud_index=mud_index,
                    surface_type=dominant_surface,
                    rider_weight_kg=rider.weight_kg,
                    tire_width_mm=getattr(bike, "tire_width_mm", None),
                    rim_internal_width_mm=getattr(bike, "rim_internal_width_mm", None),
                    casing_type=getattr(bike, "casing_type", "trail"),
                    tubeless=getattr(bike, "tubeless", True),
                    technical_difficulty=terrain.get("technical_difficulty"),
                    ascent_m=clean_ascent,
                    surface_analysis=breakdown,
                )

                climb_cat = terrain["climb_category"]
                avg_grad = terrain["avg_climb_gradient"]
                setup_warnings = self._tire_setup_warnings(tire_display)
                tactical_warnings = list(warnings) + list(terrain["warnings"]) + setup_warnings

                emtb_analysis = self._emtb_analysis(
                    bike=bike,
                    rider=rider,
                    mission=mission,
                    clean_ascent=clean_ascent,
                    real_dist_m=real_dist_m,
                    breakdown=breakdown,
                    mud_score_val=mud_score_val,
                )

                avg_gradient_total = terrain["avg_gradient"]

                return {
                    "status": "Success",
                    "profile_used": current_profile,
                    "metadata": {
                        "analyzed_date": mud_analysis.get("metadata", {}).get("target_date"),
                        "api_extras": list(extras.keys()),
                        "elevation_source": "ORS geometry elevation (offline terrain engine)",
                    },
                    "tactical_briefing": {
                        "distance_km": round(real_dist_m / 1000, 2),
                        "elevation_gain_m": round(clean_ascent),
                        "climb_category": climb_cat,
                        "avg_gradient": f"{round(avg_gradient_total, 1)}%",
                        "avg_climb_gradient": f"{round(avg_grad, 1)}%",
                        "terrain_analysis": terrain,
                        "max_gradient": terrain["max_gradient"],
                        "data_confidence": terrain["data_confidence"],
                        "technical_difficulty": terrain["technical_difficulty"],
                        "mud_intelligence": {
                            "score": mud_score_val,
                            "label": t_analysis.get("mud_risk_score", "Unknown"),
                            "traction_risk": t_analysis.get("traction_risk", {}).get(
                                "level", "Unknown"
                            ),
                            "trail_damage_risk": t_analysis.get("trail_damage_risk", {}).get(
                                "level", "Unknown"
                            ),
                            "dry_time_eta": t_analysis.get("dry_time_eta", "N/A"),
                        },
                    },
                    "mechanical_setup": {
                        "compatible": compatible,
                        "setup_details": tire_display,
                        "bike_type": bike.bike_type,
                        "safety_warnings": tactical_warnings,
                    },
                    "surface_breakdown": breakdown,
                    "emtb_tactical": emtb_analysis,
                }

            except Exception as e:
                last_error = f"Local processing error: {e!s}"
                continue

        return {"status": "Error", "message": f"Global failure: {last_error}"}

    @staticmethod
    def _tire_setup_warnings(tire_setup: Any) -> list[str]:
        """Extract setup warnings from a structured recommendation or legacy tuple."""
        if hasattr(tire_setup, "warnings"):
            return list(tire_setup.warnings or [])
        if isinstance(tire_setup, dict):
            return list(tire_setup.get("warnings") or [])
        return []

    @staticmethod
    def _safe_complexity(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = 10
        return max(3, min(parsed, 30))

    @staticmethod
    def _safe_length_m(total_length_km: Any) -> int:
        try:
            km = float(total_length_km)
        except (TypeError, ValueError):
            km = 0.0
        return int(km * 1000)

    @staticmethod
    def _attempts_for_profile(requested_profile: str) -> list[tuple[str, list[str]]]:
        if requested_profile == "cycling-electric":
            requested_profile = "cycling-mountain"

        if requested_profile == "cycling-mountain":
            return [
                ("cycling-mountain", ["surface", "waytype"]),
                ("cycling-regular", ["surface"]),
            ]
        if requested_profile == "cycling-road":
            return [
                ("cycling-road", ["surface", "waytype"]),
                ("cycling-regular", ["surface"]),
            ]
        return [
            ("cycling-regular", ["surface", "waytype"]),
            ("cycling-regular", ["surface"]),
        ]

    def _request_body(self, lat, lon, mission, safe_length, safe_complexity, requested_extras):
        surface_options = {}
        avoid_features = []

        if getattr(mission, "surface_preference", None) == "avoid_unpaved":
            avoid_features.append("unpaved")

        if getattr(mission, "surface_preference", None) == "prefer_paved":
            surface_options["avoid_polygons"] = {}
            if "unpaved" not in avoid_features:
                avoid_features.append("unpaved")

        if avoid_features:
            surface_options["avoid_features"] = avoid_features

        return {
            "coordinates": [[lon, lat]],
            "elevation": True,
            "extra_info": requested_extras,
            "options": {
                "round_trip": {
                    "length": safe_length,
                    "points": safe_complexity,
                    "seed": int(getattr(mission, "seed", 42)),
                },
                **surface_options,
            },
        }

    @staticmethod
    def _geometry_distance_m(geometry) -> float:
        return sum(segment_distances_m(geometry))

    @staticmethod
    def _flat_surface_breakdown(breakdown) -> dict[str, int]:
        if not isinstance(breakdown, list):
            return {}

        try:
            return {
                item["type"].capitalize(): int(item["percentage"].replace("%", "").strip())
                for item in breakdown
                if "type" in item and "percentage" in item
            }
        except (ValueError, KeyError, AttributeError):
            return {}

    def _emtb_analysis(
        self, bike, rider, mission, clean_ascent, real_dist_m, breakdown, mud_score_val
    ):
        emtb_analysis = None

        bike_type_str = str(getattr(bike, "bike_type", "")).upper()
        battery_cap = getattr(bike, "battery_wh", 0)

        if not isinstance(battery_cap, (int, float)):
            battery_cap = 0

        is_emtb = "E-" in bike_type_str and battery_cap > 0
        flat_surface_breakdown = self._flat_surface_breakdown(breakdown)

        if is_emtb:
            try:
                emtb_analysis = self.battery_drain_calculator(
                    battery_wh=battery_cap,
                    assist_level=getattr(mission, "assist_mode", "Trail"),
                    weight_kg=float(getattr(rider, "weight_kg", 80)) + 24,
                    ascent_m=clean_ascent,
                    distance_km=real_dist_m / 1000,
                    surface_breakdown=flat_surface_breakdown,
                    mud_index=mud_score_val,
                )
            except Exception:
                emtb_analysis = {"error": "Battery calculation failed"}

        return emtb_analysis


service = SurfaceAnalyzerService()


def get_surface_analyzer(
    api_key,
    lat,
    lon,
    rider,
    bike,
    mission,
    target_date: str | None = None,
    route_feature: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return service.get_surface_analyzer(
        api_key=api_key,
        lat=lat,
        lon=lon,
        rider=rider,
        bike=bike,
        mission=mission,
        target_date=target_date,
        route_feature=route_feature,
    )
