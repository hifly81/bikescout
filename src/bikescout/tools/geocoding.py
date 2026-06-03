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
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable

import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


class GeocodingError(Exception):
    """Domain-specific geocoding error."""


class GeocodingProvider(ABC):
    """Abstract base class for pluggable geocoding providers."""

    @abstractmethod
    def geocode(self, query: str, lang: str) -> list[dict[str, Any]]:
        raise NotImplementedError


@dataclass(frozen=True)
class GeocodingConfig:
    request_timeout_seconds: float = 10.0
    min_interval_seconds: float = 1.1
    max_results: int = 5
    default_language: str = "en"
    max_retries: int = 3
    user_agent: str = "BikeScout_Tactical_Engine/2.0"
    nominatim_url: str = NOMINATIM_URL


class NominatimProvider(GeocodingProvider):
    def __init__(self, config: GeocodingConfig | None = None, session: requests.sessions.Session | None = None):
        self.config = config or GeocodingConfig()
        self.session = session or requests

    def geocode(self, query: str, lang: str) -> list[dict[str, Any]]:
        if not query or not query.strip():
            raise GeocodingError("Geocoding query must not be empty.")

        headers = {
            "User-Agent": self.config.user_agent,
            "Accept-Language": lang,
        }
        params = {
            "q": query,
            "format": "json",
            "limit": self.config.max_results,
            "addressdetails": 1,
        }

        try:
            response = self.session.get(
                self.config.nominatim_url,
                params=params,
                headers=headers,
                timeout=self.config.request_timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise GeocodingError(f"Geocoding request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise GeocodingError("Geocoding provider returned invalid JSON.") from exc

        if not isinstance(payload, list):
            raise GeocodingError("Geocoding provider returned unexpected payload format.")

        normalized: list[dict[str, Any]] = []
        for item in payload:
            if isinstance(item, dict):
                normalized.append(item)

        return normalized


class GeoEngine:
    def __init__(
            self,
            provider: GeocodingProvider,
            config: GeocodingConfig | None = None,
            logger: logging.Logger | None = None,
            sleep_func: Callable[[float], None] | None = None,
            time_func: Callable[[], float] | None = None,
    ):
        self.provider = provider
        self.config = config or GeocodingConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.sleep_func = sleep_func or time.sleep
        self.time_func = time_func or time.time
        self.last_request_time = 0.0

    def _wait_for_slot(self) -> None:
        elapsed = self.time_func() - self.last_request_time
        if elapsed < self.config.min_interval_seconds:
            self.sleep_func(self.config.min_interval_seconds - elapsed)
        self.last_request_time = self.time_func()

    def _rank_results(self, results: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not results:
            return None

        def scoring_function(item: dict[str, Any]) -> float:
            try:
                score = float(item.get("importance", 0) or 0)
            except (TypeError, ValueError):
                score = 0.0

            category = str(item.get("class", "") or "")
            sub_type = str(item.get("type", "") or "")

            if category in {"tourism", "leisure"} and sub_type in {"trail", "track", "park", "nature_reserve"}:
                score += 0.5
            elif category == "place" and sub_type in {"village", "town", "city"}:
                score += 0.3
            elif category in {"shop", "office", "building"}:
                score -= 0.4

            return score

        ranked = sorted(results, key=scoring_function, reverse=True)
        return ranked[0]

    def _build_success_result(self, best_match: dict[str, Any]) -> dict[str, Any]:
        try:
            lat = float(best_match["lat"])
            lon = float(best_match["lon"])
        except (KeyError, TypeError, ValueError) as exc:
            raise GeocodingError("Best geocoding result is missing valid lat/lon values.") from exc

        return {
            "status": "Success",
            "lat": lat,
            "lon": lon,
            "display_name": best_match.get("display_name", ""),
            "class": best_match.get("class"),
            "type": best_match.get("type"),
            "importance": best_match.get("importance"),
        }

    def get_coordinates(
            self,
            location_name: str,
            lang: str | None = None,
            retries: int | None = None,
    ) -> dict[str, Any]:
        effective_lang = self.config.default_language if lang is None else lang
        effective_retries = self.config.max_retries if retries is None else retries

        if not location_name or not location_name.strip():
            return {"status": "Error", "message": "Location name must not be empty."}

        if effective_retries <= 0:
            return {"status": "Error", "message": "Retries must be a positive integer."}

        for attempt in range(effective_retries):
            try:
                self._wait_for_slot()
                raw_results = self.provider.geocode(location_name, effective_lang)

                best_match = self._rank_results(raw_results)
                if not best_match:
                    return {"status": "Error", "message": f"Location '{location_name}' not found."}

                return self._build_success_result(best_match)

            except GeocodingError as exc:
                self.logger.debug("Geocoding attempt %s failed: %s", attempt + 1, exc)

                if attempt == effective_retries - 1:
                    return {"status": "Error", "message": "Max retries exceeded for geocoding service."}

                wait_time = 2 ** attempt
                self.sleep_func(wait_time)

            except Exception as exc:
                self.logger.exception("Unexpected geocoding failure")

                if attempt == effective_retries - 1:
                    return {"status": "Error", "message": f"Unexpected geocoding failure: {exc}"}

                wait_time = 2 ** attempt
                self.sleep_func(wait_time)

        return {"status": "Error", "message": "Max retries exceeded for geocoding service."}


engine = GeoEngine(NominatimProvider())


def get_coordinates(location_name: str, lang: str = "en") -> dict[str, Any]:
    """Compatibility wrapper for the main orchestrator."""
    return engine.get_coordinates(location_name, lang=lang)