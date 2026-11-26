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

import copy
import logging
import math
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable

import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = "BikeScout_Tactical_Engine/2.0 (https://github.com/hifly81/bikescout)"
AMBIGUITY_SCORE_MARGIN = 0.1


class GeocodingError(Exception):
    """Domain-specific geocoding error."""


class GeocodingValidationError(GeocodingError):
    """Invalid provider data that must not be retried."""


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
    user_agent: str = NOMINATIM_USER_AGENT
    nominatim_url: str = NOMINATIM_URL
    cache_ttl_seconds: float = 86400.0
    cache_max_entries: int = 128
    max_alternatives: int = 4


class NominatimProvider(GeocodingProvider):
    def __init__(
        self,
        config: GeocodingConfig | None = None,
        session: requests.sessions.Session | None = None,
    ):
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


def _score_result(item: dict[str, Any]) -> float:
    """Score a Nominatim hit with cycling-specific category bonuses."""
    try:
        score = float(item.get("importance", 0) or 0)
    except (TypeError, ValueError):
        score = 0.0

    category = str(item.get("class", "") or "")
    sub_type = str(item.get("type", "") or "")

    if category in {"tourism", "leisure"} and sub_type in {
        "trail",
        "track",
        "park",
        "nature_reserve",
    }:
        score += 0.5
    elif category == "place" and sub_type in {"village", "town", "city"}:
        score += 0.3
    elif category in {"shop", "office", "building"}:
        score -= 0.4

    return score


def _parse_coordinate(value: Any, label: str, low: float, high: float) -> float:
    """Parse a coordinate and reject booleans, non-finite numbers and out-of-range values."""
    if isinstance(value, bool):
        raise GeocodingValidationError(
            f"Best geocoding result has an invalid {label}: {value!r} (expected {low} to {high})."
        )
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise GeocodingValidationError(
            f"Best geocoding result has an invalid {label}: {value!r} (expected {low} to {high})."
        ) from exc
    if not math.isfinite(number) or not low <= number <= high:
        raise GeocodingValidationError(
            f"Best geocoding result has an invalid {label}: {value!r} (expected {low} to {high})."
        )
    return number


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
        self._cache: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}
        self._cache_lock = threading.RLock()

    @staticmethod
    def _cache_key(query: str, lang: str) -> tuple[str, str]:
        return (query.strip().casefold(), lang.casefold())

    def _cache_get(self, key: tuple[str, str]) -> dict[str, Any] | None:
        if self.config.cache_ttl_seconds <= 0:
            return None
        with self._cache_lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            stored_at, payload = entry
            if self.time_func() - stored_at >= self.config.cache_ttl_seconds:
                self._cache.pop(key, None)
                return None
            return copy.deepcopy(payload)

    def _cache_put(self, key: tuple[str, str], payload: dict[str, Any]) -> None:
        if self.config.cache_ttl_seconds <= 0 or self.config.cache_max_entries <= 0:
            return
        with self._cache_lock:
            self._cache.pop(key, None)
            self._cache[key] = (self.time_func(), copy.deepcopy(payload))
            while len(self._cache) > self.config.cache_max_entries:
                self._cache.pop(next(iter(self._cache)))

    def _wait_for_slot(self) -> None:
        elapsed = self.time_func() - self.last_request_time
        if elapsed < self.config.min_interval_seconds:
            self.sleep_func(self.config.min_interval_seconds - elapsed)
        self.last_request_time = self.time_func()

    def _ranked_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(results, key=_score_result, reverse=True)

    def _rank_results(self, results: list[dict[str, Any]]) -> dict[str, Any] | None:
        ranked = self._ranked_results(results)
        return ranked[0] if ranked else None

    def _log_ambiguity(self, ranked: list[dict[str, Any]]) -> None:
        if len(ranked) < 2:
            return
        margin = _score_result(ranked[0]) - _score_result(ranked[1])
        if margin <= AMBIGUITY_SCORE_MARGIN:
            self.logger.warning(
                "Ambiguous geocoding result: %r and %r scored within %.2f; "
                "alternatives are diagnostic only.",
                ranked[0].get("display_name"),
                ranked[1].get("display_name"),
                margin,
            )

    def _build_alternatives(
        self, ranked: list[dict[str, Any]], best_match: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Build diagnostic candidates; they stay out of the public MCP response schema."""
        alternatives: list[dict[str, Any]] = []
        for item in ranked:
            if item is best_match:
                continue
            try:
                lat = _parse_coordinate(item.get("lat"), "latitude", -90.0, 90.0)
                lon = _parse_coordinate(item.get("lon"), "longitude", -180.0, 180.0)
            except GeocodingValidationError:
                continue
            alternatives.append(
                {
                    "display_name": str(item.get("display_name") or ""),
                    "lat": lat,
                    "lon": lon,
                    "class": str(item.get("class") or ""),
                    "type": str(item.get("type") or ""),
                    "importance": _score_result(item),
                }
            )
            if len(alternatives) >= self.config.max_alternatives:
                break
        return alternatives

    def _build_success_result(self, best_match: dict[str, Any]) -> dict[str, Any]:
        lat = _parse_coordinate(best_match.get("lat"), "latitude", -90.0, 90.0)
        lon = _parse_coordinate(best_match.get("lon"), "longitude", -180.0, 180.0)
        try:
            importance = float(best_match.get("importance") or 0)
        except (TypeError, ValueError):
            importance = 0.0
        if not math.isfinite(importance):
            importance = 0.0

        return {
            "status": "Success",
            "lat": lat,
            "lon": lon,
            "display_name": str(best_match.get("display_name") or ""),
            "class": str(best_match.get("class") or ""),
            "type": str(best_match.get("type") or ""),
            "importance": importance,
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

        cache_key = self._cache_key(location_name, effective_lang)
        cached = self._cache_get(cache_key)
        if cached is not None:
            self.logger.debug("Geocoding cache hit for %r", location_name)
            return cached

        last_error = "Max retries exceeded for geocoding service."
        for attempt in range(effective_retries):
            try:
                self._wait_for_slot()
                raw_results = self.provider.geocode(location_name, effective_lang)

                ranked = self._ranked_results(raw_results)
                if not ranked:
                    return {"status": "Error", "message": f"Location '{location_name}' not found."}

                self._log_ambiguity(ranked)
                best_match = ranked[0]
                result = self._build_success_result(best_match)
                result["alternatives"] = self._build_alternatives(ranked, best_match)
                self._cache_put(cache_key, result)
                return result

            except GeocodingValidationError as exc:
                self.logger.warning("Invalid geocoding payload: %s", exc)
                return {"status": "Error", "message": str(exc)}

            except GeocodingError as exc:
                last_error = f"Geocoding service failed after {attempt + 1} attempt(s): {exc}"
                self.logger.debug("Geocoding attempt %s failed: %s", attempt + 1, exc)
                if attempt < effective_retries - 1:
                    self.sleep_func(2**attempt)

            except Exception as exc:
                last_error = f"Unexpected geocoding failure after {attempt + 1} attempt(s): {exc}"
                self.logger.exception("Unexpected geocoding failure")
                if attempt < effective_retries - 1:
                    self.sleep_func(2**attempt)

        return {"status": "Error", "message": last_error}


engine = GeoEngine(NominatimProvider())


def get_coordinates(location_name: str, lang: str = "en") -> dict[str, Any]:
    """Look up coordinates through the shared cached engine.

    Success payloads carry an ``alternatives`` diagnostic list; the MCP response
    schema intentionally ignores it, so only the ranked best match is public.
    """
    return engine.get_coordinates(location_name, lang=lang)
