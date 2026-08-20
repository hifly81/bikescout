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
from typing import Any

import numpy as np
import requests

from bikescout.tools.battery import calculate_battery_drain
from bikescout.tools.bike_setup import analyze_compatibility, get_tire_setup
from bikescout.tools.mud import get_mud_risk_analysis


@dataclass(frozen=True)
class SurfaceAnalyzerConfig:
    ors_timeout_seconds: float = 7.0


def _sanitize_elevation_profile(
        geometry,
        window_size=11,
        threshold=3.0,
        max_step_up_m=30.0,
        max_step_down_m=30.0,
):
    elevations = [float(p[2]) for p in geometry if len(p) > 2 and isinstance(p[2], (int, float))]
    if len(elevations) < window_size:
        return 0.0

    cleaned = [elevations[0]]
    for ele in elevations[1:]:
        prev = cleaned[-1]
        delta = ele - prev

        if delta > max_step_up_m:
            ele = prev + max_step_up_m
        elif delta < -max_step_down_m:
            ele = prev - max_step_down_m

        cleaned.append(ele)

    weights = np.ones(window_size) / window_size
    smoothed = np.convolve(cleaned, weights, mode="valid")

    total_ascent = 0.0
    last_valley = smoothed[0]
    last_peak = smoothed[0]
    is_climbing = True

    for ele in smoothed[1:]:
        if is_climbing:
            if ele > last_peak:
                last_peak = ele
            elif ele < last_peak - threshold:
                total_ascent += (last_peak - last_valley)
                is_climbing = False
                last_valley = ele
        else:
            if ele < last_valley:
                last_valley = ele
            elif ele > last_valley + threshold:
                is_climbing = True
                last_peak = ele

    if is_climbing and last_peak > last_valley:
        total_ascent += (last_peak - last_valley)

    return round(total_ascent, 0)

def _cap_implausible_ascent(total_ascent_m: float, total_dist_m: float, bike_type: str) -> float:
    if total_dist_m <= 0:
        return 0.0

    bike_type_low = str(bike_type).lower()
    dist_km = total_dist_m / 1000.0
    ascent_per_km = total_ascent_m / max(dist_km, 1e-6)

    if "enduro" in bike_type_low:
        hard_cap_per_km = 180.0
    elif "mountain" in bike_type_low or "mtb" in bike_type_low:
        hard_cap_per_km = 140.0
    else:
        hard_cap_per_km = 90.0

    hard_cap_total = dist_km * hard_cap_per_km
    return round(min(total_ascent_m, hard_cap_total), 0)


def _categorize_climb(total_ascent: float, total_dist_m: float, bike_type: str):
    bike_type_low = str(bike_type).lower()

    if "enduro" in bike_type_low:
        climbing_ratio = 0.25
        effort_multiplier = 1.6
    elif "mountain" in bike_type_low or "mtb" in bike_type_low:
        climbing_ratio = 0.30
        effort_multiplier = 1.4
    else:
        climbing_ratio = 0.45
        effort_multiplier = 1.0

    climbing_dist = total_dist_m * climbing_ratio
    avg_gradient = (total_ascent / climbing_dist) * 100 if climbing_dist > 0 else 0

    max_display = 25.0 if "enduro" in bike_type_low else 20.0
    display_gradient = min(avg_gradient, max_display)

    scoring_gradient = min(display_gradient, 18.0)
    adjusted_score = total_ascent * (scoring_gradient / 10) * effort_multiplier

    if total_ascent < 50:
        return "Flat / Rolling", display_gradient

    if adjusted_score >= 800 or total_ascent > 1000:
        category = "Hors Catégorie (HC)"
    elif adjusted_score >= 500:
        category = "C1 - Brutal Ascent"
    elif adjusted_score >= 300:
        category = "C2 - Hard Climb"
    elif adjusted_score >= 150:
        category = "C3 - Challenging"
    else:
        category = "C4 - Short Burner"

    if "enduro" in bike_type_low:
        category = f"Enduro Tech: {category}"

    return category, display_gradient


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

    def get_surface_analyzer(self, api_key, lat, lon, rider, bike, mission, target_date: str = None):
        safe_complexity = self._safe_complexity(getattr(mission, "complexity", 10))
        safe_length = self._safe_length_m(getattr(mission, "total_length_km", 0))
        attempts = self._attempts_for_profile(getattr(mission, "profile", "cycling-regular"))

        last_error = ""
        for current_profile, requested_extras in attempts:
            try:
                url = f"https://api.openrouteservice.org/v2/directions/{current_profile}/geojson"
                headers = {"Authorization": api_key, "Content-Type": "application/json"}

                body = self._request_body(
                    lat=lat,
                    lon=lon,
                    mission=mission,
                    safe_length=safe_length,
                    safe_complexity=safe_complexity,
                    requested_extras=requested_extras,
                )

                res = self.http_session.post(url, json=body, headers=headers, timeout=self.config.ors_timeout_seconds)

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

                real_dist_m = self._geometry_distance_m(geometry)
                clean_ascent = _sanitize_elevation_profile(
                    geometry,
                    window_size=11,
                    threshold=3.0,
                    max_step_up_m=25.0,
                    max_step_down_m=25.0,
                )
                clean_ascent = _cap_implausible_ascent(
                    total_ascent_m=clean_ascent,
                    total_dist_m=real_dist_m,
                    bike_type=bike.bike_type,
)

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

                mud_analysis = self.mud_analyzer(lat, lon, dominant_surface, target_date)
                t_analysis = mud_analysis.get("tactical_analysis") or {}
                raw_mud = t_analysis.get("mud_risk_numeric")
                mud_score_val = float(raw_mud) if raw_mud is not None else 0.0

                tire_display = self.tire_setup_getter(
                    bike_type=bike.bike_type,
                    tire_size_option=bike.tire_size,
                    mud_index=mud_score_val,
                    surface_type=dominant_surface,
                    rider_weight_kg=rider.weight_kg,
                )

                climb_cat, avg_grad = _categorize_climb(clean_ascent, real_dist_m, bike.bike_type)
                breakdown, warnings, compatible = self.compatibility_analyzer(
                    bike.bike_type,
                    bike.tire_width_mm,
                    extras,
                    surface_map,
                )

                emtb_analysis = self._emtb_analysis(
                    bike=bike,
                    rider=rider,
                    mission=mission,
                    clean_ascent=clean_ascent,
                    real_dist_m=real_dist_m,
                    breakdown=breakdown,
                    mud_score_val=mud_score_val,
                )

                avg_gradient_total = (clean_ascent / real_dist_m * 100) if real_dist_m > 0 else 0

                return {
                    "status": "Success",
                    "profile_used": current_profile,
                    "metadata": {
                        "analyzed_date": mud_analysis.get("metadata", {}).get("target_date"),
                        "api_extras": list(extras.keys()),
                    },
                    "tactical_briefing": {
                        "distance_km": round(real_dist_m / 1000, 2),
                        "elevation_gain_m": clean_ascent,
                        "climb_category": climb_cat,
                        "avg_gradient": f"{round(avg_gradient_total, 1)}%",
                        "avg_climb_gradient": f"{round(avg_grad, 1)}%",
                        "mud_intelligence": {
                            "score": mud_score_val,
                            "label": t_analysis.get("mud_risk_score", "Unknown"),
                            "traction_risk": t_analysis.get("traction_risk", {}).get("level", "Unknown"),
                            "trail_damage_risk": t_analysis.get("trail_damage_risk", {}).get("level", "Unknown"),
                            "dry_time_eta": t_analysis.get("dry_time_eta", "N/A"),
                        },
                    },
                    "mechanical_setup": {
                        "compatible": compatible,
                        "setup_details": tire_display,
                        "bike_type": bike.bike_type,
                        "safety_warnings": warnings,
                    },
                    "surface_breakdown": breakdown,
                    "emtb_tactical": emtb_analysis,
                }

            except Exception as e:
                last_error = f"Local processing error: {str(e)}"
                continue

        return {"status": "Error", "message": f"Global failure: {last_error}"}

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
        R = 6371000
        deg_to_rad = math.pi / 180
        real_dist_m = 0.0
        step = 1

        for i in range(0, len(geometry) - step, step):
            p1, p2 = geometry[i], geometry[i + step]
            lat1, lon1 = p1[1] * deg_to_rad, p1[0] * deg_to_rad
            lat2, lon2 = p2[1] * deg_to_rad, p2[0] * deg_to_rad
            x = (lon2 - lon1) * math.cos((lat1 + lat2) / 2)
            y = lat2 - lat1
            real_dist_m += math.sqrt(x * x + y * y) * R

        return real_dist_m

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

    def _emtb_analysis(self, bike, rider, mission, clean_ascent, real_dist_m, breakdown, mud_score_val):
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


def get_surface_analyzer(api_key, lat, lon, rider, bike, mission, target_date: str = None):
    return service.get_surface_analyzer(
        api_key=api_key,
        lat=lat,
        lon=lon,
        rider=rider,
        bike=bike,
        mission=mission,
        target_date=target_date,
    )