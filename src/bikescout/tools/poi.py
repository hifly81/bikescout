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
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Any

import requests

ORS_POIS_URL = "https://api.heigit.org/openpoiservice/v0/pois"


class PoiScoutError(Exception):
    """Domain-specific POI scout error."""


@dataclass(frozen=True)
class PoiScoutConfig:
    ors_pois_url: str = ORS_POIS_URL
    request_timeout_seconds: float = 10.0
    min_buffer_m: int = 1
    max_buffer_m: int = 2000
    result_limit: int = 20
    target_categories: tuple[int, ...] = (162, 372, 371, 331, 332)
    route_sample_spacing_m: int = 2000
    max_route_samples: int = 15


class PoiScoutService:
    def __init__(
        self,
        config: PoiScoutConfig | None = None,
        session: requests.sessions.Session | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.config = config or PoiScoutConfig()
        self.session = session or requests
        self.logger = logger or logging.getLogger(__name__)

    def get_poi_scout(
        self,
        api_key: str,
        lat: float,
        lon: float,
        total_length_km: float,
        route_geometry: list[list[float]] | None = None,
    ) -> dict[str, Any]:
        try:
            self._validate_inputs(api_key, lat, lon, total_length_km)

            safe_buffer = self._compute_safe_buffer_m(total_length_km)
            headers = self._build_headers(api_key)
            sample_points = self._sample_route_points(lat, lon, route_geometry)
            route_search = len(sample_points) > 1

            raw_amenities: list[dict[str, Any]] = []
            for point in sample_points:
                body = self._build_request_body(point["lat"], point["lon"], safe_buffer)
                response = self.session.post(
                    self.config.ors_pois_url,
                    json=body,
                    headers=headers,
                    timeout=self.config.request_timeout_seconds,
                )

                if not response.ok:
                    self.logger.warning(
                        "ORS POI error: %s - %s", response.status_code, response.text
                    )
                    return {
                        "status": "Error",
                        "message": f"ORS POI API error {response.status_code}. Retry later or verify ORS_API_KEY.",
                    }

                try:
                    data = response.json()
                except ValueError as exc:
                    raise PoiScoutError("ORS returned invalid JSON.") from exc

                raw_amenities.extend(self._extract_amenities(data, point))

            amenities = self._dedupe_amenities(raw_amenities)

            return {
                "status": "Success",
                "search_km": round(safe_buffer / 1000.0, 3),
                "search_radius_m": safe_buffer,
                "search_strategy": "route_sampled" if route_search else "start_radius",
                "sample_points": len(sample_points),
                "total_found": len(amenities),
                "amenities": sorted(
                    amenities,
                    key=lambda x: (
                        x.get("route_km") is None,
                        float(x["route_km"])
                        if isinstance(x.get("route_km"), (int, float))
                        else 10**9,
                        x.get("distance_m", 10**9),
                    ),
                ),
            }

        except PoiScoutError as exc:
            return {"status": "Error", "message": str(exc)}
        except requests.exceptions.RequestException as exc:
            self.logger.warning("POI provider request failed", exc_info=exc)
            return {
                "status": "Error",
                "message": f"POI provider error: {exc}. Retry later or verify connectivity.",
            }
        except Exception as exc:
            self.logger.exception("Unexpected POI scout failure")
            return {
                "status": "Error",
                "message": f"Internal POI engine failure: {str(exc)}",
            }

    def _validate_inputs(
        self, api_key: str, lat: float, lon: float, total_length_km: float
    ) -> None:
        if not api_key or not api_key.strip():
            raise PoiScoutError("API key must not be empty.")

        try:
            lat_f = float(lat)
            lon_f = float(lon)
            total_f = float(total_length_km)
        except (TypeError, ValueError) as exc:
            raise PoiScoutError(
                "Latitude, longitude, and total_length_km must be numeric."
            ) from exc

        if not (-90.0 <= lat_f <= 90.0):
            raise PoiScoutError("Latitude must be between -90 and 90.")
        if not (-180.0 <= lon_f <= 180.0):
            raise PoiScoutError("Longitude must be between -180 and 180.")
        if total_f < 0:
            raise PoiScoutError("total_length_km must be non-negative.")

    def _compute_safe_buffer_m(self, total_length_km: float) -> int:
        # Buffer is a local search radius around sampled points, not the full route length.
        meters = int(max(float(total_length_km) * 100.0, self.config.min_buffer_m))
        return min(max(meters, 500), self.config.max_buffer_m)

    def _sample_route_points(
        self, lat: float, lon: float, route_geometry: list[list[float]] | None
    ) -> list[dict[str, float]]:
        if not route_geometry:
            return [{"lat": float(lat), "lon": float(lon), "route_km": 0.0}]

        coords: list[tuple[float, float]] = []
        for point in route_geometry:
            if not isinstance(point, (list, tuple)) or len(point) < 2:
                continue
            try:
                plon, plat = float(point[0]), float(point[1])
            except (TypeError, ValueError):
                continue
            if not (-90.0 <= plat <= 90.0 and -180.0 <= plon <= 180.0):
                continue
            coords.append((plat, plon))
        if len(coords) < 2:
            return [{"lat": float(lat), "lon": float(lon), "route_km": 0.0}]

        samples: list[dict[str, float]] = [
            {"lat": coords[0][0], "lon": coords[0][1], "route_km": 0.0}
        ]
        acc = 0.0
        total_m = 0.0
        last = coords[0]
        spacing = max(500, int(self.config.route_sample_spacing_m))
        for cur in coords[1:]:
            step = self.haversine_distance(last[0], last[1], cur[0], cur[1])
            acc += step
            total_m += step
            if acc >= spacing:
                samples.append(
                    {"lat": cur[0], "lon": cur[1], "route_km": round(total_m / 1000.0, 2)}
                )
                acc = 0.0
            last = cur
        end_km = round(total_m / 1000.0, 2)
        if (
            not samples
            or samples[-1]["lat"] != coords[-1][0]
            or samples[-1]["lon"] != coords[-1][1]
        ):
            samples.append({"lat": coords[-1][0], "lon": coords[-1][1], "route_km": end_km})

        max_samples = max(2, int(self.config.max_route_samples))
        if len(samples) > max_samples:
            idxs = [round(i * (len(samples) - 1) / (max_samples - 1)) for i in range(max_samples)]
            samples = [samples[i] for i in idxs]
        return samples

    def _build_headers(self, api_key: str) -> dict[str, str]:
        return {
            "Authorization": api_key,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json, application/geo+json",
        }

    def _build_request_body(self, lat: float, lon: float, safe_buffer: int) -> dict[str, Any]:
        return {
            "request": "pois",
            "geometry": {
                "geojson": {
                    "type": "Point",
                    "coordinates": [float(lon), float(lat)],
                },
                "buffer": safe_buffer,
            },
            "filters": {
                "category_ids": list(self.config.target_categories),
            },
            "limit": self.config.result_limit,
            "sortby": "distance",
        }

    def _extract_amenities(
        self, data: dict[str, Any], sample_point: dict[str, float] | None = None
    ) -> list[dict[str, Any]]:
        if not isinstance(data, dict):
            raise PoiScoutError("ORS returned unexpected payload format.")

        features = data.get("features", [])
        if not isinstance(features, list):
            raise PoiScoutError("ORS returned invalid features payload.")

        all_amenities: list[dict[str, Any]] = []

        for feature in features:
            if not isinstance(feature, dict):
                continue

            props = feature.get("properties", {})
            geometry = feature.get("geometry", {})

            if not isinstance(props, dict) or not isinstance(geometry, dict):
                continue

            coords = geometry.get("coordinates", [])
            if not isinstance(coords, list) or len(coords) < 2:
                continue

            try:
                lon = float(coords[0])
                lat = float(coords[1])
            except (TypeError, ValueError):
                continue

            category_ids = props.get("category_ids", {})
            label = self._label_from_category_ids(category_ids)

            osm_tags = props.get("osm_tags", {})
            if not isinstance(osm_tags, dict):
                osm_tags = {}

            distance_raw = props.get("distance", 0)
            try:
                distance_m = round(float(distance_raw))
            except (TypeError, ValueError):
                distance_m = 0

            name = (
                osm_tags.get("name") or osm_tags.get("amenity") or osm_tags.get("operator") or label
            )
            opening_hours = osm_tags.get("opening_hours")
            drinking_water = osm_tags.get("drinking_water")
            water_source = osm_tags.get("water_source") or osm_tags.get("fountain")
            potability = self._potability_hint(label, osm_tags)

            route_km = (sample_point or {}).get("route_km")
            all_amenities.append(
                {
                    "name": name,
                    "type": label,
                    "distance_m": distance_m,
                    "location": {"lat": lat, "lon": lon},
                    "opening_hours": str(opening_hours) if opening_hours else None,
                    "drinking_water": str(drinking_water) if drinking_water else None,
                    "water_source": str(water_source) if water_source else None,
                    "potability": potability,
                    "route_km": round(float(route_km), 2)
                    if isinstance(route_km, (int, float))
                    else None,
                    "sample_lat": (sample_point or {}).get("lat"),
                    "sample_lon": (sample_point or {}).get("lon"),
                }
            )

        return all_amenities

    @staticmethod
    def _potability_hint(label: str, osm_tags: dict[str, Any]) -> str | None:
        if label != "Water Fountain":
            return None
        drinking_water = str(osm_tags.get("drinking_water", "")).lower()
        if drinking_water in {"yes", "potable"}:
            return "potable_tagged"
        if drinking_water in {"no"}:
            return "not_potable_tagged"
        return "unknown_verify"

    def _dedupe_amenities(self, amenities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        for amenity in amenities:
            loc = amenity.get("location") or {}
            lat = loc.get("lat")
            lon = loc.get("lon")
            if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                deduped.append(amenity)
                continue

            match_idx = None
            for idx, prev in enumerate(deduped):
                prev_loc = prev.get("location") or {}
                plat = prev_loc.get("lat")
                plon = prev_loc.get("lon")
                if not isinstance(plat, (int, float)) or not isinstance(plon, (int, float)):
                    continue
                if prev.get("type") != amenity.get("type"):
                    continue
                dist_m = self.haversine_distance(float(lat), float(lon), float(plat), float(plon))
                same_name = (
                    str(prev.get("name", "")).strip().lower()
                    == str(amenity.get("name", "")).strip().lower()
                )
                threshold = 100.0 if same_name else 20.0
                if dist_m <= threshold:
                    match_idx = idx
                    break

            if match_idx is None:
                deduped.append(amenity)
                continue

            prev = deduped[match_idx]
            prev_dist = prev.get("distance_m", 10**9)
            cur_dist = amenity.get("distance_m", 10**9)
            better = dict(prev)
            if cur_dist < prev_dist:
                better["distance_m"] = cur_dist
                better["location"] = amenity.get("location", prev.get("location"))
            for field in ("opening_hours", "drinking_water", "water_source", "potability", "name"):
                if not better.get(field) and amenity.get(field):
                    better[field] = amenity[field]
            if better.get("route_km") is None and amenity.get("route_km") is not None:
                better["route_km"] = amenity["route_km"]
            deduped[match_idx] = better

        for amenity in deduped:
            amenity.pop("sample_lat", None)
            amenity.pop("sample_lon", None)
        return deduped

    def _label_from_category_ids(self, category_ids: Any) -> str:
        if isinstance(category_ids, dict):
            found_cats = set(str(k) for k in category_ids.keys())
        elif isinstance(category_ids, list):
            found_cats = set(str(x) for x in category_ids)
        else:
            found_cats = set()

        if "162" in found_cats:
            return "Water Fountain"
        if "372" in found_cats or "371" in found_cats:
            return "Bike Support"
        if "331" in found_cats or "332" in found_cats:
            return "Rest Area"
        return "Point of Interest"

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371000.0
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return 2 * r * asin(sqrt(a))


service = PoiScoutService()


def get_poi_scout(
    api_key: str,
    lat: float,
    lon: float,
    total_length_km: float,
    route_geometry: list[list[float]] | None = None,
) -> dict[str, Any]:
    return service.get_poi_scout(api_key, lat, lon, total_length_km, route_geometry=route_geometry)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return PoiScoutService.haversine_distance(lat1, lon1, lat2, lon2)
