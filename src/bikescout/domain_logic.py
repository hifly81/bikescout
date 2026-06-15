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

import re
from typing import Any


def ext_cast(val: Any, to_type, default):
    if val in [None, "", "None", "null"]:
        return default

    if isinstance(val, str):
        match = re.search(r"[-+]?\d*\.?\d+", val)
        if match and to_type in (float, int):
            val = match.group()
        elif to_type == bool:
            return val.strip().lower() in ["true", "1", "t", "y", "yes"]
        elif not match and to_type in (float, int):
            return default

    try:
        if to_type == bool:
            return str(val).lower() in ["true", "1", "t", "y", "yes"]
        if to_type == int:
            return int(float(val))
        return to_type(val)
    except (ValueError, TypeError):
        return default


def extract_location_hint(text: str) -> str | None:
    if not text:
        return None

    patterns = [
        r"(?i)\bnear(?:by)?\s+([^.;,\n]+)",
        r"(?i)\b(?:around|in|at)\s+([^.;,\n]+)",
        r"(?i)\b(?:vicino a|intorno a|da)\s+([^.;,\n]+)",
    ]

    for pat in patterns:
        match = re.search(pat, text.strip())
        if match:
            hint = match.group(1).strip()
            hint = re.split(r"(?i)\s+i'm\b|\s+add\b|\s+with\b", hint)[0].strip()
            if len(hint) >= 3:
                return hint
    return None


def extract_point_to_point(user_input: str) -> tuple[str, str] | None:
    if not user_input:
        return None

    patterns = [
        r"(?i)\bfrom\s+(.+?)\s+to\s+(.+?)(?:\.|,| with | and |$)",
        r"(?i)\bda\s+(.+?)\s+a\s+(.+?)(?:\.|,| con | e |$)",
        r"(?i)^(.+?)\s*->\s*(.+?)$",
    ]

    for pat in patterns:
        match = re.search(pat, user_input.strip())
        if match:
            start, end = match.group(1).strip(), match.group(2).strip()
            if len(start) >= 2 and len(end) >= 2:
                return start, end
    return None


def resolve_route_mode(args: dict, user_input: str) -> str:
    mode = (args.get("route_mode") or "").lower()
    if mode in ("point_to_point", "a_to_b", "a-b"):
        return "point_to_point"

    if extract_point_to_point(user_input):
        return "point_to_point"

    return "round_trip"


def normalize_bike_type(raw_bike: str | None) -> tuple[str, bool]:
    raw = str(raw_bike or "").lower()
    if any(word in raw for word in ["electric", "e-mtb", "emtb", "ebike"]):
        return "e-mtb", True
    if "road" in raw:
        return "road", False
    if "gravel" in raw:
        return "gravel", False
    if "enduro" in raw or "downhill" in raw:
        return "enduro", False
    return "mtb", False

def normalize_tire_size(raw_tire_size: str | None, bike_type: str) -> str:
    allowed = {"32", "29", "27.5", "700c", "650b"}

    raw = str(raw_tire_size or "").strip().lower()

    aliases = {
        "28": "700c",
        "28c": "700c",
        "30": "700c",
        "30c": "700c",
        "32c": "32",
        "33": "700c",
        "35": "700c",
        "38": "700c",
        "40": "700c",
        "42": "700c",
        "45": "700c",
        "622": "700c",
        "700": "700c",
        "700c": "700c",
        "29er": "29",
        "29-inch": "29",
        "29in": "29",
        "29": "29",
        "27.5": "27.5",
        "27,5": "27.5",
        "27.5-inch": "27.5",
        "27.5in": "27.5",
        "650b": "650b",
        "32": "32",
    }

    normalized = aliases.get(raw)
    if normalized in allowed:
        return normalized

    if bike_type == "road":
        return "700c"
    if bike_type == "gravel":
        return "700c"
    if bike_type in {"mtb", "enduro", "e-mtb"}:
        return "29"

    return "29"



def resolve_profile(final_bike: str) -> str:
    if final_bike in {"mtb", "enduro", "downhill", "gravel"}:
        return "cycling-mountain"
    if final_bike == "road":
        return "cycling-road"
    if final_bike == "e-mtb":
        return "cycling-electric"
    return "cycling-regular"


def wants_overlay(user_input: str, llm_value, keywords: tuple[str, ...]) -> bool:
    if llm_value is True:
        return True
    if user_input:
        text = user_input.lower()
        return any(k in text for k in keywords)
    return bool(llm_value)


def clamp_complexity(raw_complexity: Any) -> int:
    try:
        value = int(raw_complexity)
    except (TypeError, ValueError):
        return 3

    return max(1, min(5, value))


def build_mission_snapshot(
        *,
        location_name: str,
        lat: float,
        lon: float,
        args: dict,
        distance_km: float,
        route_mode: str = "round_trip",
        destination_name: str | None = None,
        dest_lat: float | None = None,
        dest_lon: float | None = None,
) -> dict:
    ctx = {
        "route_mode": route_mode,
        "location_name": location_name,
        "latitude": lat,
        "longitude": lon,
        "distance_km": distance_km,
        "bike_type": args.get("bike_type"),
        "tire_size": args.get("tire_size"),
    }

    if route_mode == "point_to_point":
        ctx["destination_name"] = destination_name
        ctx["dest_latitude"] = dest_lat
        ctx["dest_longitude"] = dest_lon
    else:
        ctx["destination_name"] = None
        ctx["dest_latitude"] = None
        ctx["dest_longitude"] = None

    return ctx


def summarize_mission(ctx: dict) -> str:
    if not ctx or not ctx.get("location_name"):
        return "No active mission"

    if ctx.get("route_mode") == "point_to_point" and ctx.get("destination_name"):
        return (
            f"{ctx['location_name']} → {ctx['destination_name']} · "
            f"{ctx.get('bike_type', 'mtb')}"
        )

    return (
        f"{ctx['location_name']} · "
        f"{ctx.get('distance_km', '?')} km · "
        f"{ctx.get('bike_type', 'mtb')}"
    )