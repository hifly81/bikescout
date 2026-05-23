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

import requests
import time
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# --- Provider Interface (Strategy Pattern) ---
class GeocodingProvider(ABC):
    """Abstract base class to allow easy swapping between Nominatim, Google, or Mapbox."""
    @abstractmethod
    def geocode(self, query: str, lang: str) -> List[Dict[str, Any]]:
        pass

# --- Nominatim Provider with Tactical Ranking ---
class NominatimProvider(GeocodingProvider):
    USER_AGENT = "BikeScout_Tactical_Engine/2.0"

    def geocode(self, query: str, lang: str = "en") -> List[Dict[str, Any]]:
        headers = {
            'User-Agent': self.USER_AGENT,
            'Accept-Language': lang
        }
        params = {
            'q': query,
            'format': 'json',
            'limit': 5,  # Fetch multiple results for tactical ranking
            'addressdetails': 1
        }

        try:
            response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return []

# --- Resilience: Token Bucket & Exponential Backoff ---
class GeoEngine:
    def __init__(self, provider: GeocodingProvider):
        self.provider = provider
        # Rate limiting: 1 request per second (Nominatim policy)
        self.last_request_time = 0.0
        self.min_interval = 1.1

    def _wait_for_slot(self):
        """Ensures the server never exceeds the 1 request/second limit."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()

    def _rank_results(self, results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Tactical Result Ranking:
        Prioritizes trails, parks, and towns over shops or house numbers.
        Uses Nominatim's 'importance' and 'class/type' tags.
        """
        if not results:
            return None

        def scoring_function(item):
            # Base score from provider importance (0.0 to 1.0)
            score = float(item.get("importance", 0))

            # Classification Boosts
            category = item.get("class", "")
            sub_type = item.get("type", "")

            # Prioritize cycling/nature hubs
            if category in ["tourism", "leisure"] and sub_type in ["trail", "track", "park", "nature_reserve"]:
                score += 0.5
            elif category == "place" and sub_type in ["village", "town", "city"]:
                score += 0.3
            # Penalize irrelevant results for cyclists
            elif category in ["shop", "office", "building"]:
                score -= 0.4

            return score

        # Sort by tactical score descending
        ranked = sorted(results, key=scoring_function, reverse=True)
        return ranked[0]

    def get_coordinates(self, location_name: str, lang: str = "en", retries: int = 3) -> Dict[str, Any]:
        """
        Converts location name to (lat, lon) with exponential backoff and tactical ranking.
        """
        for attempt in range(retries):
            try:
                self._wait_for_slot()
                raw_results = self.provider.geocode(location_name, lang)

                best_match = self._rank_results(raw_results)

                if not best_match:
                    return {"status": "Error", "message": f"Location '{location_name}' not found."}

                return {
                    "status": "Success",
                    "lat": float(best_match["lat"]),
                    "lon": float(best_match["lon"]),
                    "display_name": best_match["display_name"],
                    "class": best_match.get("class"),
                    "type": best_match.get("type"),
                    "importance": best_match.get("importance")
                }

            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s...
                time.sleep(wait_time)

        return {"status": "Error", "message": "Max retries exceeded for geocoding service."}

engine = GeoEngine(NominatimProvider())

def get_coordinates(location_name: str, lang: str = "en"):
    """Compatibility wrapper for the main orchestrator."""
    return engine.get_coordinates(location_name, lang)
