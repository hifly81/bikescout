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

import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal, Optional

import math
import numpy as np
import requests

from bikescout.schemas import BikeSetup, MissionConstraints, RiderProfile, RouteGeometry
from bikescout.tools.altimetry import get_elevation_profile_image
from bikescout.tools.maps import save_local_tactical_map
from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.nutrition import get_nutrition_plan
from bikescout.tools.poi import get_poi_scout
from bikescout.tools.surface import get_surface_analyzer
from bikescout.tools.weather import apply_weather_windowing, get_weather_forecast


OVERPASS_URL = "https://overpass-api.de/api/interpreter"
ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions"


@dataclass(frozen=True)
class TrailScoutConfig:
    routing_timeout_seconds: float = 15.0


def calculate_detailed_difficulty(dist_km: float, ascent_m: float) -> str:
    if dist_km == 0:
        return "Unknown"

    avg_gradient = (ascent_m / (dist_km * 1000)) * 100

    if dist_km > 50 or ascent_m > 1000 or avg_gradient > 7:
        return "Expert (Challenging distance or very steep climbs)"
    if dist_km > 30 or ascent_m > 600 or avg_gradient > 4:
        return "Advanced (Requires good fitness and stamina)"
    if dist_km > 15 or ascent_m > 300:
        return "Moderate (Accessible for regular cyclists)"
    return "Beginner (Short and relatively flat, ideal for everyone)"


def generate_tactical_gpx(filename_part, geojson_data, amenities=[]):
    try:
        home_dir = Path.home() / ".bikescout" / "gpx"
        home_dir.mkdir(parents=True, exist_ok=True)

        now = time.time()
        for f in home_dir.glob("*.gpx"):
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
        gpx_xml += '<gpx version="1.1" creator="BikeScout" xmlns="http://www.topografix.com/GPX/1/1">\n'

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
            dist = (d_lat ** 2 + d_lon ** 2) ** 0.5

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
            "message": f"GPX Generation failed: {str(e)}",
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
            dest_latitude: Optional[float] = None,
            dest_longitude: Optional[float] = None,
            style: Literal["sparkline", "filled", "bars"] = "sparkline",
            target_date: str = None,
            include_gpx: bool = True,
            include_map: bool = False,
            include_poi: bool = False,
            include_altimetry: bool = False,
            include_weather: bool = False,
            include_mud_analysis: bool = False,
            include_nutrition_plan: bool = False,
    ):
        routing_payload = self._routing_payload(
            latitude=latitude,
            longitude=longitude,
            mission=mission,
            dest_latitude=dest_latitude,
            dest_longitude=dest_longitude,
        )

        try:
            endpoint = f"{ORS_BASE_URL}/{mission.profile}/geojson"
            headers = {"Authorization": api_key, "Content-Type": "application/json"}

            response = self.http_session.post(
                endpoint,
                json=routing_payload,
                headers=headers,
                timeout=self.config.routing_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()

            feature = data["features"][0]
            props = feature["properties"]
            route_geo = RouteGeometry(coordinates=feature["geometry"]["coordinates"])

            summary = props.get("summary", {})
            dist_km = round(summary.get("distance", 0) / 1000, 2)
            ascent_m = round(props.get("ascent", 0), 0)
            dominant_surface = "Unknown"

            max_temp = 20.0
            estimated_hours = 0.0
            intensity_score = 0
            amenities = []

            response_payload = self._base_response_payload(
                dist_km=dist_km,
                ascent_m=ascent_m,
                dest_latitude=dest_latitude,
                dest_longitude=dest_longitude,
            )

            try:
                surface_report = self.surface_analyzer(api_key, latitude, longitude, rider, bike, mission, target_date)
            except Exception as e:
                surface_report = {"status": "Error", "message": f"Surface Analysis failed: {str(e)}"}

            if surface_report.get("status") == "Success":
                t_brief = surface_report.get("tactical_briefing", {})
                dist_km = t_brief.get("distance_km")
                ascent_m = t_brief.get("elevation_gain_m")

                surface_analysis = surface_report.get("info", {}).get("surface_analysis", {})
                breakdown = surface_analysis.get("surface_breakdown", [])

                dominant_surface = self._dominant_surface_from_breakdown(breakdown)

                response_payload["info"]["distance_km"] = dist_km
                response_payload["info"]["ascent_m"] = ascent_m
                response_payload["info"]["difficulty"] = calculate_detailed_difficulty(dist_km, ascent_m)
                response_payload["info"]["surface_analysis"] = surface_report

                perf = calculate_performance_metrics(dist_km, ascent_m, rider, bike)
                estimated_hours = perf["estimated_hours"]
                intensity_score = perf["intensity_score"]

            if include_weather:
                try:
                    weather_report = self.weather_getter(latitude, longitude, target_date)

                    if weather_report.get("status") == "Success":
                        weather_report = self.weather_windowing(weather_report, start=9, end=19)
                        weather_list = self._weather_snapshot_list(weather_report)
                        max_temp = weather_report.get("reference_conditions", {}).get("temp_max", "N/A")
                        response_payload["conditions"]["max_temp_detected"] = f"{max_temp}�C"
                        response_payload["conditions"]["weather"] = weather_list if weather_list else None

                        safety_advice = weather_report.get("safety_advice", None)
                        if safety_advice:
                            response_payload["conditions"]["safety_advice"] = safety_advice
                    else:
                        response_payload["conditions"]["weather_status"] = "Unavailable"

                except Exception as e:
                    response_payload["conditions"]["weather_error"] = f"Technical bypass: {str(e)}"

            if include_mud_analysis:
                mud_analysis = self.mud_analyzer(latitude, longitude, dominant_surface, target_date)
                if mud_analysis.get("status") == "Success":
                    response_payload["conditions"]["mud_risk"] = mud_analysis

            if include_nutrition_plan:
                nutrition_plan = self.nutrition_getter(
                    estimated_hours,
                    max_temp,
                    intensity_score,
                    rider.weight_kg,
                    rider.gender,
                    rider.sweat_profile,
                )
                if nutrition_plan.get("status") == "Success":
                    self._ensure_logistics(response_payload)
                    response_payload["logistics"]["nutrition_plan"] = nutrition_plan

            if include_poi:
                try:
                    poi_res = self.poi_scout(api_key, latitude, longitude, mission.total_length_km)
                    amenities = poi_res.get("amenities", []) if poi_res.get("status") == "Success" else []
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

            if include_gpx:
                try:
                    gpx_report = self.gpx_generator(filename_part, geojson_data=route_geo, amenities=amenities)
                    if gpx_report["status"] == "Success":
                        response_payload["gpx_export_path"] = gpx_report["file_location"]
                        response_payload["mcp_resource_uri_gpx"] = gpx_report["mcp_resource_uri"]
                except Exception as e:
                    response_payload["gpx_error"] = f"GPX failed: {str(e)}"

            if include_altimetry:
                try:
                    altimetry_report = self.altimetry_getter(geometry=route_geo, uuid_input=filename_part, style=style)
                    if altimetry_report["status"] == "Success":
                        response_payload["elevation_profile_path"] = altimetry_report["file_location"]
                        response_payload["mcp_resource_uri_elevation_profile"] = altimetry_report["mcp_resource_uri"]
                except Exception as e:
                    response_payload["elevation_error"] = f"Altimetry failed: {str(e)}"

            return response_payload

        except Exception as e:
            return {"status": "Error", "error_message": f"Master Orchestrator failed: {str(e)}"}

    @staticmethod
    def _routing_payload(latitude, longitude, mission, dest_latitude, dest_longitude):
        if dest_latitude is not None and dest_longitude is not None:
            return {
                "coordinates": [[longitude, latitude], [dest_longitude, dest_latitude]],
                "elevation": "true",
                "extra_info": ["surface", "steepness"],
            }
        return {
            "coordinates": [[longitude, latitude]],
            "options": {"round_trip": {"length": mission.total_length_km * 1000, "seed": mission.seed}},
            "elevation": "true",
            "extra_info": ["surface", "steepness"],
        }

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
                "max_temp_detected": "20.0�C",
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
    def _weather_snapshot_list(weather_report):
        weather_list = []
        for entry in weather_report.get("tactical_forecast", []):
            snapshot = {
                "time": str(entry.get("hour", entry.get("time", "N/A"))),
                "temp": f"{entry.get('temp', 'N/A')}°C",
                "app_temp": f"{entry.get('app_temp', entry.get('temp', 'N/A'))}°C",
                "rain_prob": f"{entry.get('rain_prob', '0')}%",
                "rain_mm": f"{entry.get('rain_mm', '0.0')} mm",
                "wind": f"{entry.get('wind', '0')} km/h",
                "gusts": f"{entry.get('gusts', '0')} km/h",
            }
            weather_list.append(snapshot)
        return weather_list

    @staticmethod
    def _ensure_logistics(response_payload):
        if "logistics" not in response_payload or response_payload["logistics"] is None:
            response_payload["logistics"] = {}


def calculate_performance_metrics(dist_km: float, ascent_m: float, rider: RiderProfile, bike: BikeSetup) -> dict:
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
        dest_latitude: Optional[float] = None,
        dest_longitude: Optional[float] = None,
        style: Literal["sparkline", "filled", "bars"] = "sparkline",
        target_date: str = None,
        include_gpx: bool = True,
        include_map: bool = False,
        include_poi: bool = False,
        include_altimetry: bool = False,
        include_weather: bool = False,
        include_mud_analysis: bool = False,
        include_nutrition_plan: bool = False,
):
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
    )