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
import sys
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Any

import requests


ORS_POIS_URL = "https://api.openrouteservice.org/pois"


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


class PoiScoutService:
    def __init__(
            self,
            config: PoiScoutConfig | None = None,
            session: requests.sessions.Session | None = None,
            logger: logging.Logger | None = None,
            stderr=None,
    ) -> None:
        self.config = config or PoiScoutConfig()
        self.session = session or requests
        self.logger = logger or logging.getLogger(__name__)
        self.stderr = stderr if stderr is not None else sys.stderr

    def get_poi_scout(
            self,
            api_key: str,
            lat: float,
            lon: float,
            total_length_km: float,
    ) -> dict[str, Any]:
        try:
            self._validate_inputs(api_key, lat, lon, total_length_km)

            safe_buffer = self._compute_safe_buffer_m(total_length_km)
            headers = self._build_headers(api_key)
            body = self._build_request_body(lat, lon, safe_buffer)

            response = self.session.post(
                self.config.ors_pois_url,
                json=body,
                headers=headers,
                timeout=self.config.request_timeout_seconds,
            )

            if not response.ok:
                print(
                    f"ORS API Error: {response.status_code} - {response.text}",
                    file=self.stderr,
                )
                return {
                    "status": "Error",
                    "message": f"ORS API error {response.status_code}",
                }

            try:
                data = response.json()
            except ValueError as exc:
                raise PoiScoutError("ORS returned invalid JSON.") from exc

            amenities = self._extract_amenities(data)

            return {
                "status": "Success",
                "search_km": f"{safe_buffer}m",
                "total_found": len(amenities),
                "amenities": sorted(amenities, key=lambda x: x["distance_m"]),
            }

        except PoiScoutError as exc:
            return {"status": "Error", "message": str(exc)}
        except Exception as exc:
            print(f"POI Engine Critical Exception: {str(exc)}", file=self.stderr)
            self.logger.exception("Unexpected POI scout failure")
            return {
                "status": "Error",
                "message": f"Internal Engine failure: {str(exc)}",
            }

    def _validate_inputs(self, api_key: str, lat: float, lon: float, total_length_km: float) -> None:
        if not api_key or not api_key.strip():
            raise PoiScoutError("API key must not be empty.")

        try:
            lat_f = float(lat)
            lon_f = float(lon)
            total_f = float(total_length_km)
        except (TypeError, ValueError) as exc:
            raise PoiScoutError("Latitude, longitude, and total_length_km must be numeric.") from exc

        if not (-90.0 <= lat_f <= 90.0):
            raise PoiScoutError("Latitude must be between -90 and 90.")
        if not (-180.0 <= lon_f <= 180.0):
            raise PoiScoutError("Longitude must be between -180 and 180.")
        if total_f < 0:
            raise PoiScoutError("total_length_km must be non-negative.")

    def _compute_safe_buffer_m(self, total_length_km: float) -> int:
        meters = int(float(total_length_km) * 1000)
        return min(max(meters, self.config.min_buffer_m), self.config.max_buffer_m)

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

    def _extract_amenities(self, data: dict[str, Any]) -> list[dict[str, Any]]:
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
                    osm_tags.get("name")
                    or osm_tags.get("amenity")
                    or osm_tags.get("operator")
                    or label
            )

            all_amenities.append(
                {
                    "name": name,
                    "type": label,
                    "distance_m": distance_m,
                    "location": {"lat": lat, "lon": lon},
                }
            )

        return all_amenities

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


def get_poi_scout(api_key: str, lat: float, lon: float, total_length_km: float) -> dict[str, Any]:
    return service.get_poi_scout(api_key, lat, lon, total_length_km)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return PoiScoutService.haversine_distance(lat1, lon1, lat2, lon2)