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
import sys
import time
import traceback
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import requests

from bikescout.schemas import BikeSetup, MissionConstraints, RiderProfile, RouteGeometry
from bikescout.tools.altimetry import create_climb_profile_images, get_elevation_profile_image
from bikescout.tools.maps import save_local_tactical_map
from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.nutrition import get_nutrition_plan
from bikescout.tools.poi import get_poi_scout
from bikescout.tools.surface import get_surface_analyzer
from bikescout.tools.weather import apply_weather_windowing, get_weather_forecast

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
ORS_BASE_URL = "https://api.heigit.org/openrouteservice/v2/directions"
EARTH_METERS_PER_DEGREE = 111_320.0


@dataclass(frozen=True)
class TrailScoutConfig:
    routing_timeout_seconds: float = 15.0


_DIFFICULTY_LABELS = (
    "Beginner (Short and relatively flat, ideal for everyone)",
    "Moderate (Accessible for regular cyclists)",
    "Advanced (Requires good fitness and stamina)",
    "Expert (Challenging distance or very steep climbs)",
)
_COMPLEXITY_MIN_LEVEL = {4: 2, 5: 3}
_AVG_CLIMB_ADVANCED_PERCENT = 7.0
_AVG_CLIMB_EXPERT_PERCENT = 10.0

# ORS surface values that represent rideable off-road surfaces.
_OFFROAD_SURFACE_IDS = frozenset({2, 5, 10, 11, 12})
_OFFROAD_SURFACE_TOKENS = (
    "unpaved",
    "dirt",
    "gravel",
    "grass",
    "earth",
    "compact",
    "trail",
    "sand",
)
_OFFROAD_PENALTY_M = 4000.0
_OFFROAD_TARGET_SHARE = 0.6


def calculate_detailed_difficulty(
    dist_km: float,
    ascent_m: float,
    complexity: int = 3,
    avg_climb_gradient: float = 0.0,
) -> str:
    """
    Rate mission difficulty from distance, ascent, climb pitch and intent.

    Distance/ascent define the physical baseline. The sustained climb gradient
    (not GPS micro-spikes) and an explicitly requested high complexity can only
    raise that baseline, so a "very hard" request is never reported as moderate.

    Args:
        dist_km: Route distance in kilometers.
        ascent_m: Cumulative elevation gain in meters.
        complexity: Requested difficulty intent on the 1..5 scale.
        avg_climb_gradient: Weighted gradient of significant climbs in percent.
    Returns:
        One of the four canonical difficulty labels, or "Unknown".
    """
    if dist_km == 0:
        return "Unknown"

    avg_gradient = (ascent_m / (dist_km * 1000)) * 100

    if dist_km > 50 or ascent_m > 1000 or avg_gradient > 7:
        level = 3
    elif dist_km > 30 or ascent_m > 600 or avg_gradient > 4:
        level = 2
    elif dist_km > 15 or ascent_m > 300:
        level = 1
    else:
        level = 0

    try:
        climb_gradient = float(str(avg_climb_gradient or 0.0).replace("%", "").strip())
    except (TypeError, ValueError):
        climb_gradient = 0.0
    if climb_gradient >= _AVG_CLIMB_EXPERT_PERCENT:
        level = max(level, 3)
    elif climb_gradient >= _AVG_CLIMB_ADVANCED_PERCENT:
        level = max(level, 2)

    try:
        requested_complexity = int(complexity)
    except (TypeError, ValueError):
        requested_complexity = 3
    requested_level = _COMPLEXITY_MIN_LEVEL.get(requested_complexity, 0)
    return _DIFFICULTY_LABELS[max(level, requested_level)]


def generate_tactical_gpx(filename_part, geojson_data, amenities=[]):
    try:
        home_dir = Path.home() / ".bikescout" / "gpx"
        home_dir.mkdir(parents=True, exist_ok=True)

        now = time.time()
        for f in home_dir.glob("tactical_route_*.gpx"):
            if f.is_file() and (now - f.stat().st_mtime) > (14 * 86400):
                try:
                    f.unlink()
                except Exception:
                    pass

        if hasattr(geojson_data, "coordinates"):
            coords = geojson_data.coordinates
        elif isinstance(geojson_data, dict) and "features" in geojson_data:
            feature = geojson_data["features"][0]
            coords = feature["geometry"]["coordinates"]
        else:
            coords = geojson_data

        healed_coords = []
        points_fixed_count = 0
        for i in range(len(coords)):
            lon, lat, ele = coords[i]
            is_anomaly = ele <= 0 or (i > 0 and abs(ele - coords[i - 1][2]) > 200)

            if is_anomaly and i > 0:
                ele = coords[i - 1][2]
                points_fixed_count += 1

            healed_coords.append([lon, lat, ele])

        coords = healed_coords

        max_track_points = 1500
        step = max(1, len(coords) // max_track_points)
        optimized_coords = coords[::step]

        gpx_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        gpx_xml += (
            '<gpx version="1.1" creator="BikeScout" xmlns="http://www.topografix.com/GPX/1/1">\n'
        )

        waypoints = ""

        for poi in amenities:
            name = poi.get("name", "Cycling POI")
            loc = poi.get("location", {})
            p_lat, p_lon = loc.get("lat"), loc.get("lon")

            if p_lat and p_lon:
                waypoints += f'  <wpt lat="{p_lat}" lon="{p_lon}">\n'
                waypoints += f"    <name>{name}</name>\n"
                waypoints += "    <sym>Watering Hole</sym>\n"
                waypoints += "  </wpt>\n"

        if coords and len(coords[0]) > 2:
            peak = max(coords, key=lambda x: x[2])
            waypoints += f'  <wpt lat="{peak[1]}" lon="{peak[0]}">\n'
            waypoints += f"    <name>SUMMIT: {int(peak[2])}m</name>\n"
            waypoints += "    <sym>Summit</sym>\n"
            waypoints += "  </wpt>\n"

        last_wall_index = -50
        for i in range(5, len(coords) - 10, 10):
            if i < last_wall_index + 40:
                continue

            p1, p2 = coords[i], coords[i + 10]
            d_lat = (p2[1] - p1[1]) * 111139
            d_lon = (p2[0] - p1[0]) * 111139 * 0.7
            dist = (d_lat**2 + d_lon**2) ** 0.5

            if dist > 60:
                grade = ((p2[2] - p1[2]) / dist) * 100
                if 10 < grade < 45:
                    waypoints += f'  <wpt lat="{p1[1]}" lon="{p1[0]}">\n'
                    waypoints += f"    <name>WALL: {int(grade)}%</name>\n"
                    waypoints += "    <sym>Danger Area</sym>\n"
                    waypoints += "  </wpt>\n"
                    last_wall_index = i

        track = "  <trk>\n    <name>BikeScout Tactical Route</name>\n    <trkseg>\n"
        for lon, lat, ele in optimized_coords:
            track += f'      <trkpt lat="{lat}" lon="{lon}"><ele>{ele}</ele></trkpt>\n'
        track += "    </trkseg>\n  </trk>\n"

        full_content = gpx_xml + waypoints + track + "</gpx>"
        filename = f"tactical_route_{filename_part}.gpx"
        file_path = home_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        mcp_uri = f"bikescout://gpx/{filename}"

        return {
            "status": "Success",
            "message": "Tactical GPX file successfully exported and cleaned.",
            "mcp_resource_uri": mcp_uri,
            "file_location": str(file_path),
            "tactical_stats": {
                "total_points": len(coords),
                "healed_points": points_fixed_count,
                "waypoints_count": waypoints.count("<wpt"),
            },
        }

    except Exception as e:
        return {
            "status": "Error",
            "message": f"GPX Generation failed: {e!s}",
        }


class TrailScoutService:
    def __init__(
        self,
        config: TrailScoutConfig | None = None,
        http_session: Any | None = None,
        map_saver=None,
        weather_getter=None,
        weather_windowing=None,
        surface_analyzer=None,
        poi_scout=None,
        mud_analyzer=None,
        altimetry_getter=None,
        climb_altimetry_getter=None,
        nutrition_getter=None,
        gpx_generator=None,
        uuid_func=None,
    ) -> None:
        self.config = config or TrailScoutConfig()
        self.http_session = http_session or requests
        self.map_saver = map_saver or save_local_tactical_map
        self.weather_getter = weather_getter or get_weather_forecast
        self.weather_windowing = weather_windowing or apply_weather_windowing
        self.surface_analyzer = surface_analyzer or get_surface_analyzer
        self.poi_scout = poi_scout or get_poi_scout
        self.mud_analyzer = mud_analyzer or get_mud_risk_analysis
        self.altimetry_getter = altimetry_getter or get_elevation_profile_image
        self.climb_altimetry_getter = climb_altimetry_getter or create_climb_profile_images
        self.nutrition_getter = nutrition_getter or get_nutrition_plan
        self.gpx_generator = gpx_generator or generate_tactical_gpx
        self.uuid_func = uuid_func or (lambda: uuid.uuid4().hex[:6])

    def get_complete_trail_scout(
        self,
        api_key,
        latitude: float,
        longitude: float,
        rider: RiderProfile,
        bike: BikeSetup,
        mission: MissionConstraints,
        dest_latitude: float | None = None,
        dest_longitude: float | None = None,
        style: Literal["sparkline", "filled", "bars"] = "sparkline",
        target_date: str | None = None,
        include_gpx: bool = True,
        include_map: bool = False,
        include_poi: bool = False,
        include_altimetry: bool = False,
        include_weather: bool = False,
        include_mud_analysis: bool = False,
        include_nutrition_plan: bool = False,
        sweat_rate_ml_per_hour: float | None = None,
    ) -> dict[str, Any]:
        routing_payload = self._routing_payload(
            latitude=latitude,
            longitude=longitude,
            mission=mission,
            dest_latitude=dest_latitude,
            dest_longitude=dest_longitude,
        )

        preferred_anchor = routing_payload.pop("preferred_anchor", None)

        try:
            data = self._select_best_route_candidate(
                api_key=api_key,
                mission=mission,
                bike=bike,
                payload=routing_payload,
                anchor=preferred_anchor,
            )

            feature = data["features"][0]
            props = feature["properties"]
            route_geo = RouteGeometry(coordinates=feature["geometry"]["coordinates"])

            summary = props.get("summary", {})
            dist_km = round(summary.get("distance", 0) / 1000, 2)
            ascent_m = round(props.get("ascent", 0), 0)
            dominant_surface = "Unknown"

            max_temp: float | str = "N/A"
            estimated_hours = 0.0
            intensity_score = 0
            amenities = []
            terrain: dict[str, Any] = {}

            response_payload = self._base_response_payload(
                dist_km=dist_km,
                ascent_m=ascent_m,
                dest_latitude=dest_latitude,
                dest_longitude=dest_longitude,
            )

            perf = calculate_performance_metrics(dist_km, ascent_m, rider, bike)
            estimated_hours = perf["estimated_hours"]
            intensity_score = perf["intensity_score"]
            estimated_speed_kmh = float(perf.get("applied_base_speed", 18.0))

            ambient_temp_c: float | None = None
            weather_report: dict[str, Any] | None = None
            if include_weather:
                try:
                    weather_report = self.weather_getter(latitude, longitude, target_date)
                    if weather_report.get("status") == "Success":
                        ref = weather_report.get("reference_conditions", {})
                        temp_candidate = ref.get(
                            "temp_actual", ref.get("temp", ref.get("temp_max"))
                        )
                        try:
                            ambient_temp_c = float(temp_candidate)
                        except (TypeError, ValueError):
                            ambient_temp_c = None
                    else:
                        weather_report = None
                except Exception as e:
                    response_payload["conditions"]["weather_error"] = f"Technical bypass: {e!s}"
                    weather_report = None

            mud_analysis: dict[str, Any] | None = None
            if include_mud_analysis:
                try:
                    # Precompute once; reuse in surface analyzer and response.
                    pre_mud = self.mud_analyzer(
                        latitude,
                        longitude,
                        dominant_surface,
                        target_date,
                    )
                    if isinstance(pre_mud, dict) and pre_mud.get("status") == "Success":
                        mud_analysis = pre_mud
                except Exception:
                    mud_analysis = None

            surface_report: dict[str, Any]
            try:
                try:
                    surface_report = self.surface_analyzer(
                        api_key,
                        latitude,
                        longitude,
                        rider,
                        bike,
                        mission,
                        target_date,
                        route_feature=feature,
                        estimated_speed_kmh=estimated_speed_kmh,
                        intensity_score=intensity_score,
                        ambient_temp_c=ambient_temp_c,
                        mud_analysis=mud_analysis,
                    )
                except TypeError as te:
                    if "unexpected keyword argument" not in str(te):
                        raise
                    try:
                        surface_report = self.surface_analyzer(
                            api_key,
                            latitude,
                            longitude,
                            rider,
                            bike,
                            mission,
                            target_date,
                            route_feature=feature,
                        )
                    except TypeError:
                        surface_report = self.surface_analyzer(
                            api_key,
                            latitude,
                            longitude,
                            rider,
                            bike,
                            mission,
                            target_date,
                        )
            except Exception as e:
                surface_report = {"status": "Error", "message": f"Surface Analysis failed: {e!s}"}

            if surface_report.get("status") == "Success":
                offroad_share = self._offroad_share_from_route(data)
                offroad_percent = round(offroad_share * 100.0, 1)
                metadata = surface_report.get("metadata")
                if not isinstance(metadata, dict):
                    metadata = {}
                    surface_report["metadata"] = metadata
                metadata["offroad_share_percent"] = offroad_percent
                if self._prefers_offroad(mission, bike):
                    target_met = offroad_share >= _OFFROAD_TARGET_SHARE
                    metadata["offroad_request_status"] = "met" if target_met else "not_met"
                    metadata["offroad_request_note"] = (
                        f"Selected route is {offroad_percent}% off-road (target: >=60%)."
                        if target_met
                        else (
                            f"Only {offroad_percent}% off-road; ORS returned mostly paved roads "
                            "in this area. Try another seed, direction bias or starting point."
                        )
                    )

                t_brief = surface_report.get("tactical_briefing", {})
                dist_km = t_brief.get("distance_km")
                ascent_m = t_brief.get("elevation_gain_m")
                terrain = t_brief.get("terrain_analysis") or {}

                breakdown = surface_report.get("surface_breakdown", [])

                dominant_surface = self._dominant_surface_from_breakdown(breakdown)

                response_payload["info"]["distance_km"] = dist_km
                response_payload["info"]["ascent_m"] = ascent_m
                response_payload["info"]["difficulty"] = calculate_detailed_difficulty(
                    dist_km,
                    ascent_m,
                    complexity=getattr(mission, "complexity", 3),
                    avg_climb_gradient=terrain.get("avg_climb_gradient", 0.0),
                )
                response_payload["info"]["surface_analysis"] = surface_report
                response_payload["info"]["max_gradient"] = t_brief.get(
                    "max_gradient", terrain.get("max_gradient")
                )
                response_payload["info"]["climb_list"] = t_brief.get("climb_list") or terrain.get(
                    "climbs"
                )
                response_payload["info"]["data_confidence"] = t_brief.get(
                    "data_confidence", terrain.get("data_confidence")
                )

            if include_weather and weather_report is not None:
                try:
                    weather_report = self.weather_windowing(weather_report, start=9, end=19)
                    weather_list = self._weather_snapshot_list(weather_report)
                    max_temp = weather_report.get("reference_conditions", {}).get("temp_max", "N/A")
                    response_payload["conditions"]["max_temp_detected"] = f"{max_temp}"
                    response_payload["conditions"]["weather"] = (
                        weather_list if weather_list else None
                    )

                    safety_advice = weather_report.get("safety_advice", None)
                    if safety_advice:
                        response_payload["conditions"]["safety_advice"] = safety_advice
                except Exception as e:
                    response_payload["conditions"]["weather_error"] = f"Technical bypass: {e!s}"
            elif include_weather and "weather_error" not in response_payload["conditions"]:
                response_payload["conditions"]["weather_status"] = "Unavailable"

            if include_mud_analysis:
                avg_slope_pct = terrain.get("avg_gradient")
                max_slope_pct = terrain.get("max_gradient")
                mud_for_response = mud_analysis
                needs_slope_rerun = mud_for_response is None or (
                    (avg_slope_pct is not None or max_slope_pct is not None)
                    and not (
                        (mud_for_response.get("metadata") or {}).get("avg_slope_pct") is not None
                        or (mud_for_response.get("metadata") or {}).get("max_slope_pct") is not None
                    )
                )
                if needs_slope_rerun:
                    mud_for_response = self.mud_analyzer(
                        latitude,
                        longitude,
                        dominant_surface,
                        target_date,
                        avg_slope_pct=avg_slope_pct,
                        max_gradient_pct=max_slope_pct,
                    )
                if (
                    isinstance(mud_for_response, dict)
                    and mud_for_response.get("status") == "Success"
                ):
                    response_payload["conditions"]["mud_risk"] = mud_for_response

            if include_nutrition_plan:
                nutrition_temp: Any = max_temp
                nutrition_temp_reliable = isinstance(max_temp, (int, float))
                if weather_report and isinstance(weather_report, dict):
                    ref = weather_report.get("reference_conditions", {})
                    candidate = ref.get("temp_max", ref.get("temp_actual", max_temp))
                    if isinstance(candidate, (int, float)):
                        nutrition_temp = float(candidate)
                        nutrition_temp_reliable = True
                    else:
                        nutrition_temp_reliable = False
                if not isinstance(nutrition_temp, (int, float)):
                    nutrition_temp = 20.0
                    nutrition_temp_reliable = False

                nutrition_plan = self.nutrition_getter(
                    estimated_hours,
                    float(nutrition_temp),
                    intensity_score,
                    rider.weight_kg,
                    rider.gender,
                    rider.sweat_profile,
                    sweat_rate_ml_per_hour,
                )
                if nutrition_plan.get("status") == "Success":
                    if not nutrition_temp_reliable:
                        briefing = nutrition_plan.get("mission_nutrition_briefing")
                        if isinstance(briefing, dict):
                            inputs_used = briefing.get("inputs_used")
                            if not isinstance(inputs_used, dict):
                                inputs_used = {}
                                briefing["inputs_used"] = inputs_used
                            inputs_used["temperature_assumed_c"] = 20.0
                            inputs_used["temperature_reliable"] = False
                            inputs_used["temperature_basis"] = (
                                "fallback_assumed_no_reliable_weather"
                            )

                            uncertainty = str(briefing.get("uncertainty_note") or "").strip()
                            assumption_note = (
                                "Temperature unavailable/unreliable; nutrition used a conservative "
                                "20C assumption for calculation only. Weather was not fabricated."
                            )
                            briefing["uncertainty_note"] = (
                                f"{uncertainty} {assumption_note}".strip()
                                if uncertainty
                                else assumption_note
                            )

                            advice = briefing.get("tactical_advice")
                            if not isinstance(advice, list):
                                advice = []
                                briefing["tactical_advice"] = advice
                            assumption_alert = (
                                "ASSUMPTION: No reliable temperature available; hydration/electrolyte "
                                "targets calculated with 20C fallback. Adjust for actual conditions."
                            )
                            if assumption_alert not in advice:
                                advice.append(assumption_alert)

                    self._ensure_logistics(response_payload)
                    response_payload["logistics"]["nutrition_plan"] = nutrition_plan
                else:
                    response_payload["nutrition_error"] = str(
                        nutrition_plan.get("error_message")
                        or nutrition_plan.get("message")
                        or "Nutrition plan unavailable."
                    )

            if include_poi:
                try:
                    poi_res = self.poi_scout(
                        api_key,
                        latitude,
                        longitude,
                        mission.total_length_km,
                        route_geometry=data.get("features", [{}])[0]
                        .get("geometry", {})
                        .get("coordinates"),
                    )
                    amenities = (
                        poi_res.get("amenities", []) if poi_res.get("status") == "Success" else []
                    )
                    if poi_res.get("status") == "Success":
                        self._ensure_logistics(response_payload)
                        response_payload["logistics"]["nearby_amenities"] = amenities
                except Exception:
                    amenities = []

            filename_part = self.uuid_func()

            if include_map:
                map_payload = self.map_saver(filename_part, data)
                if map_payload["status"] == "Success":
                    response_payload["map_path"] = map_payload["file_location"]
                    response_payload["mcp_resource_uri_map"] = map_payload["mcp_resource_uri"]
                    if map_payload.get("style_applied"):
                        response_payload["map_style_applied"] = map_payload["style_applied"]
                    if map_payload.get("attribution"):
                        response_payload["map_attribution"] = map_payload["attribution"]

            if include_gpx:
                try:
                    gpx_report = self.gpx_generator(
                        filename_part, geojson_data=route_geo, amenities=amenities
                    )
                    if gpx_report["status"] == "Success":
                        response_payload["gpx_export_path"] = gpx_report["file_location"]
                        response_payload["mcp_resource_uri_gpx"] = gpx_report["mcp_resource_uri"]
                except Exception as e:
                    response_payload["gpx_error"] = f"GPX failed: {e!s}"

            if include_altimetry:
                try:
                    altimetry_report = self.altimetry_getter(
                        geometry=route_geo, uuid_input=filename_part, style=style
                    )
                    if altimetry_report.get("status") == "Success":
                        response_payload["elevation_profile_path"] = altimetry_report[
                            "file_location"
                        ]
                        response_payload["mcp_resource_uri_elevation_profile"] = altimetry_report[
                            "mcp_resource_uri"
                        ]
                        for key in (
                            "elevation_source",
                            "elevation_samples_total",
                            "elevation_samples_interpolated",
                            "elevation_uncertainty",
                        ):
                            if key in altimetry_report:
                                response_payload[key] = altimetry_report[key]
                        climb_profiles = terrain.get("climb_profile_coordinates") or []
                        if climb_profiles:
                            self.climb_altimetry_getter(
                                profiles=climb_profiles,
                                uuid_input=filename_part,
                                style=style,
                            )
                    else:
                        response_payload["elevation_error"] = str(
                            altimetry_report.get("message") or "Altimetry failed."
                        )
                except Exception as e:
                    response_payload["elevation_error"] = f"Altimetry failed: {e!s}"

            return response_payload

        except Exception as e:
            sys.stderr.write(f"Master Orchestrator failed: {e!s}\n")
            traceback.print_exc(file=sys.stderr)
            return {
                "status": "Error",
                "error_message": f"Master Orchestrator failed: {e!s}",
                "error_traceback": traceback.format_exc(),
            }

    @staticmethod
    def _normalize_direction_bias(direction_bias) -> list[str]:
        if not direction_bias:
            return []
        allowed = {"north", "south", "east", "west"}
        normalized = []
        for item in direction_bias:
            item_str = str(item).strip().lower()
            if item_str in allowed and item_str not in normalized:
                normalized.append(item_str)
        return normalized

    @staticmethod
    def _bias_anchor_offset_km(mission) -> float:
        base_distance_km = float(getattr(mission, "total_length_km", 30) or 30)
        priority_mode = str(getattr(mission, "priority_mode", "balanced")).strip().lower()

        if priority_mode == "distance_first":
            ratio = 0.18
        elif priority_mode == "ride_character_first":
            ratio = 0.28
        else:
            ratio = 0.22

        anchor_km = base_distance_km * ratio
        return max(3.0, min(anchor_km, 20.0))

    @staticmethod
    def _build_directional_anchor(latitude: float, longitude: float, mission):
        direction_bias = TrailScoutService._normalize_direction_bias(
            getattr(mission, "direction_bias", []) or []
        )
        if not direction_bias:
            return None

        offset_km = TrailScoutService._bias_anchor_offset_km(mission)
        offset_m = offset_km * 1000.0

        lat_shift = 0.0
        lon_shift = 0.0

        if "north" in direction_bias:
            lat_shift += offset_m / EARTH_METERS_PER_DEGREE
        if "south" in direction_bias:
            lat_shift -= offset_m / EARTH_METERS_PER_DEGREE

        lon_scale = EARTH_METERS_PER_DEGREE * max(math.cos(math.radians(latitude)), 0.2)
        if "east" in direction_bias:
            lon_shift += offset_m / lon_scale
        if "west" in direction_bias:
            lon_shift -= offset_m / lon_scale

        anchor_lat = latitude + lat_shift
        anchor_lon = longitude + lon_shift

        return {
            "latitude": round(anchor_lat, 6),
            "longitude": round(anchor_lon, 6),
            "offset_km": round(offset_km, 2),
            "direction_bias": direction_bias,
        }

    @staticmethod
    def _extract_route_distance_km(route_data: dict) -> float:
        try:
            return round(
                float(route_data["features"][0]["properties"]["summary"]["distance"]) / 1000.0,
                2,
            )
        except Exception:
            return 0.0

    @staticmethod
    def _distance_to_anchor_m(route_data: dict, anchor: dict) -> float:
        try:
            coords = route_data["features"][0]["geometry"]["coordinates"]
        except Exception:
            return float("inf")

        if not coords or not anchor:
            return float("inf")

        anchor_lat = float(anchor["latitude"])
        anchor_lon = float(anchor["longitude"])
        lon_scale = EARTH_METERS_PER_DEGREE * max(math.cos(math.radians(anchor_lat)), 0.2)

        best_m = float("inf")
        for point in coords:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue

            lon, lat = float(point[0]), float(point[1])
            dy = (lat - anchor_lat) * EARTH_METERS_PER_DEGREE
            dx = (lon - anchor_lon) * lon_scale
            dist_m = math.sqrt((dx * dx) + (dy * dy))

            best_m = min(best_m, dist_m)

        return best_m

    @staticmethod
    def _offroad_share_from_route(route_data: dict) -> float:
        """Return the off-road fraction of a route from ORS surface extras.

        Only the route already returned by ORS is inspected, so candidate
        selection never triggers an additional routing request.
        """
        try:
            features = route_data.get("features") or []
            if not features:
                return 0.0
            extras = (features[0].get("properties") or {}).get("extras") or {}
            summary = (extras.get("surface") or {}).get("summary") or []
        except (AttributeError, TypeError):
            return 0.0

        total_m = 0.0
        offroad_m = 0.0
        for item in summary:
            if not isinstance(item, dict):
                continue
            try:
                segment_m = float(item.get("amount") or item.get("distance") or 0.0)
            except (TypeError, ValueError):
                continue
            total_m += segment_m

            value = item.get("value")
            label = str(value).lower()
            is_offroad = value in _OFFROAD_SURFACE_IDS or any(
                token in label for token in _OFFROAD_SURFACE_TOKENS
            )
            if is_offroad:
                offroad_m += segment_m

        if total_m <= 0.0:
            return 0.0
        return max(0.0, min(1.0, offroad_m / total_m))

    @staticmethod
    def _prefers_offroad(mission, bike) -> bool:
        """Read bike_type from BikeSetup: MissionConstraints has no such field."""
        bike_type = str(getattr(bike, "bike_type", "") or "").strip().lower()
        if bike_type not in {"mtb", "enduro", "e-mtb"}:
            return False
        if not (getattr(mission, "avoid_urban", False) and getattr(mission, "prefer_rural", False)):
            return False
        return (
            str(getattr(mission, "priority_mode", "balanced")).strip().lower()
            == "ride_character_first"
        )

    @staticmethod
    def _route_candidate_score(route_data: dict, mission, anchor: dict | None, bike=None) -> float:
        target_km = float(getattr(mission, "total_length_km", 0) or 0)
        actual_km = TrailScoutService._extract_route_distance_km(route_data)
        distance_error_km = abs(actual_km - target_km)

        priority_mode = str(getattr(mission, "priority_mode", "balanced")).strip().lower()

        if priority_mode == "distance_first":
            distance_weight = 3.0
            anchor_weight = 1.0
        elif priority_mode == "ride_character_first":
            distance_weight = 1.0
            anchor_weight = 3.0
        else:
            distance_weight = 2.0
            anchor_weight = 2.0

        anchor_distance_m = 0.0
        if anchor:
            anchor_distance_m = TrailScoutService._distance_to_anchor_m(route_data, anchor)

        score = (distance_error_km * distance_weight * 1000.0) + (anchor_distance_m * anchor_weight)
        if TrailScoutService._prefers_offroad(mission, bike):
            offroad_share = TrailScoutService._offroad_share_from_route(route_data)
            score += (1.0 - offroad_share) * _OFFROAD_PENALTY_M
        return score

    @staticmethod
    def _normalize_profile(profile: Any, bike: BikeSetup | None = None) -> str:
        value = str(profile or "").strip().lower()
        if value == "cycling-electric":
            return "cycling-mountain"
        if value in {"cycling-mountain", "cycling-road", "cycling-regular"}:
            return value
        bike_type = str(getattr(bike, "bike_type", "") or "").strip().lower()
        if bike_type in {"e-mtb", "emtb"}:
            return "cycling-mountain"
        return "cycling-mountain"

    @staticmethod
    def _is_transient_route_error(exc: Exception) -> bool:
        if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
            return True
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)
        return isinstance(status, int) and (status == 429 or status >= 500)

    def _request_route_candidate(self, api_key: str, mission, payload: dict, bike=None) -> dict:
        profile = self._normalize_profile(getattr(mission, "profile", ""), bike)
        endpoint = f"{ORS_BASE_URL}/{profile}/geojson"
        headers = {"Authorization": api_key, "Content-Type": "application/json"}

        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                response = self.http_session.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.config.routing_timeout_seconds,
                )
                response.raise_for_status()
                return response.json()
            except Exception as exc:  # noqa: BLE001 - retry boundary
                last_exc = exc
                if attempt == 0 and self._is_transient_route_error(exc):
                    continue
                raise
        assert last_exc is not None
        raise last_exc

    def _select_best_route_candidate(
        self, api_key: str, mission, payload: dict, anchor: dict | None, bike=None
    ) -> dict:
        base_seed = int(getattr(mission, "seed", 42) or 42)

        if not anchor:
            return self._request_route_candidate(api_key, mission, payload, bike=bike)

        candidate_payloads = []
        for seed_offset in (0, 17, 43):
            candidate = dict(payload)
            candidate_options = dict(candidate.get("options", {}))
            round_trip = dict(candidate_options.get("round_trip", {}))
            round_trip["seed"] = base_seed + seed_offset
            candidate_options["round_trip"] = round_trip
            candidate["options"] = candidate_options
            candidate_payloads.append(candidate)

        best_data = None
        best_score = float("inf")

        for candidate_payload in candidate_payloads:
            try:
                route_data = self._request_route_candidate(
                    api_key, mission, candidate_payload, bike=bike
                )
                score = self._route_candidate_score(route_data, mission, anchor, bike)
                if score < best_score:
                    best_score = score
                    best_data = route_data
            except Exception:
                continue

        if best_data is None:
            return self._request_route_candidate(api_key, mission, payload, bike=bike)

        return best_data

    @staticmethod
    def _routing_payload(latitude, longitude, mission, dest_latitude, dest_longitude):
        if dest_latitude is not None and dest_longitude is not None:
            return {
                "coordinates": [[longitude, latitude], [dest_longitude, dest_latitude]],
                "elevation": "true",
                "extra_info": ["surface", "steepness"],
            }

        effective_length_m = TrailScoutService._effective_round_trip_length_m(mission)
        directional_anchor = TrailScoutService._build_directional_anchor(
            latitude, longitude, mission
        )

        round_trip_options = {
            "length": effective_length_m,
            "seed": mission.seed,
            "points": mission.complexity,
        }

        payload = {
            "coordinates": [[longitude, latitude]],
            "options": {
                "round_trip": round_trip_options,
            },
            "elevation": "true",
            "extra_info": ["surface", "steepness"],
        }

        if directional_anchor:
            payload["preferred_anchor"] = directional_anchor

        return payload

    @staticmethod
    def _base_response_payload(dist_km, ascent_m, dest_latitude, dest_longitude):
        return {
            "status": "Success",
            "info": {
                "route_type": "A to B" if (dest_latitude and dest_longitude) else "Round Trip",
                "distance_km": dist_km,
                "ascent_m": ascent_m,
                "difficulty": "N/A",
            },
            "conditions": {
                "max_temp_detected": "N/A",
            },
        }

    @staticmethod
    def _dominant_surface_from_breakdown(breakdown):
        dominant_surface = "Unknown"
        if breakdown:
            try:
                dominant_item = max(
                    breakdown,
                    key=lambda x: float(str(x.get("percentage", "0%")).replace("%", "").strip()),
                )
                dominant_surface = dominant_item.get("type", "Unknown")
            except (ValueError, KeyError, TypeError, AttributeError):
                dominant_surface = "Unknown"
        return dominant_surface

    @staticmethod
    def _effective_round_trip_length_m(mission) -> float:
        base_length_m = float(mission.total_length_km) * 1000.0
        flex_percent = max(0, min(30, int(getattr(mission, "distance_flex_percent", 10))))
        priority_mode = str(getattr(mission, "priority_mode", "balanced")).strip().lower()
        avoid_urban = bool(getattr(mission, "avoid_urban", False))
        prefer_rural = bool(getattr(mission, "prefer_rural", False))
        direction_bias = list(getattr(mission, "direction_bias", []) or [])

        if priority_mode == "distance_first":
            multiplier = 1.0
        elif priority_mode == "ride_character_first":
            multiplier = 1.0 - (flex_percent / 100.0)
        else:
            multiplier = 1.0 - (flex_percent / 200.0)

        if avoid_urban or prefer_rural or direction_bias:
            multiplier = min(multiplier, 0.95)

        effective_length_m = base_length_m * multiplier
        return max(5000.0, round(effective_length_m, 0))

    @staticmethod
    def _weather_snapshot_list(weather_report):
        """Convert the numeric weather payload into public WeatherSnapshot values."""
        weather_list = []
        for entry in weather_report.get("tactical_forecast", []):
            snapshot = {
                "time": str(entry.get("hour", entry.get("time", "N/A"))),
                "temp": entry.get("temp"),
                "app_temp": entry.get("app_temp", entry.get("temp")),
                "rain_prob": entry.get("rain_prob", 0),
                "rain_mm": entry.get("rain_mm", 0.0),
                "wind": entry.get("wind", 0.0),
                "gusts": entry.get("gusts", 0.0),
                "wind_direction": entry.get("wind_direction", 0),
                "weather_code": entry.get("weather_code"),
                "condition": entry.get("condition"),
            }
            weather_list.append(snapshot)
        return weather_list

    @staticmethod
    def _ensure_logistics(response_payload):
        if "logistics" not in response_payload or response_payload["logistics"] is None:
            response_payload["logistics"] = {}


def calculate_performance_metrics(
    dist_km: float, ascent_m: float, rider: RiderProfile, bike: BikeSetup
) -> dict:
    bike_speeds = {
        "road": 25.0,
        "gravel": 20.0,
        "mtb": 15.0,
        "enduro": 13.0,
        "e-mtb": 18.0,
    }

    fitness_vam = {
        "beginner": 400.0,
        "intermediate": 700.0,
        "pro": 1000.0,
    }

    b_type = bike.bike_type.lower()
    f_level = rider.fitness_level.lower()

    base_speed = bike_speeds.get(b_type, 16.0)
    vam = fitness_vam.get(f_level, 700.0)

    if bike.is_ebike:
        vam = max(vam, 850.0)
        if b_type in ["mtb", "enduro", "e-mtb"]:
            base_speed += 3.0

    estimated_hours = (dist_km / base_speed) + (ascent_m / vam)
    intensity_threshold = 1200 if f_level == "pro" else 600
    intensity_score = 3 if (ascent_m > intensity_threshold or dist_km > 60) else 2

    return {
        "estimated_hours": round(estimated_hours, 2),
        "intensity_score": intensity_score,
        "applied_vam": vam,
        "applied_base_speed": base_speed,
    }


def _map_surface_id(s_id):
    mapping = {1: "asphalt", 2: "unpaved", 5: "gravel", 10: "dirt", 11: "grass", 12: "compact"}
    return mapping.get(s_id, "dirt")


service = TrailScoutService()


def get_complete_trail_scout(
    api_key,
    latitude: float,
    longitude: float,
    rider: RiderProfile,
    bike: BikeSetup,
    mission: MissionConstraints,
    dest_latitude: float | None = None,
    dest_longitude: float | None = None,
    style: Literal["sparkline", "filled", "bars"] = "sparkline",
    target_date: str | None = None,
    include_gpx: bool = True,
    include_map: bool = False,
    include_poi: bool = False,
    include_altimetry: bool = False,
    include_weather: bool = False,
    include_mud_analysis: bool = False,
    include_nutrition_plan: bool = False,
    sweat_rate_ml_per_hour: float | None = None,
) -> dict[str, Any]:
    return service.get_complete_trail_scout(
        api_key=api_key,
        latitude=latitude,
        longitude=longitude,
        rider=rider,
        bike=bike,
        mission=mission,
        dest_latitude=dest_latitude,
        dest_longitude=dest_longitude,
        style=style,
        target_date=target_date,
        include_gpx=include_gpx,
        include_map=include_map,
        include_poi=include_poi,
        include_altimetry=include_altimetry,
        include_weather=include_weather,
        include_mud_analysis=include_mud_analysis,
        include_nutrition_plan=include_nutrition_plan,
        sweat_rate_ml_per_hour=sweat_rate_ml_per_hour,
    )
