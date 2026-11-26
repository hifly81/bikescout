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

import os
import re
from typing import Any

import streamlit as st

from bikescout.tools.bike_setup import (
    default_casing_type,
    default_rim_internal_width_mm,
    default_tire_width_mm,
)


def ext_cast(val: Any, to_type, default):
    if val in [None, "", "None", "null"]:
        return default

    if isinstance(val, str):
        match = re.search(r"[-+]?\d*\.?\d+", val)
        if match and to_type in (float, int):
            val = match.group()
        elif to_type is bool:
            return val.strip().lower() in ["true", "1", "t", "y", "yes"]
        elif not match and to_type in (float, int):
            return default

    try:
        if to_type is bool:
            return str(val).lower() in ["true", "1", "t", "y", "yes"]
        if to_type is int:
            return int(float(val))
        return to_type(val)
    except (ValueError, TypeError):
        return default


def extract_location_hint(text: str | None) -> str | None:
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


def extract_direction_bias_from_text(user_input: str) -> list[str]:
    text = (user_input or "").lower()
    bias = []

    if "south" in text:
        bias.append("south")
    if "north" in text:
        bias.append("north")
    if "east" in text:
        bias.append("east")
    if "west" in text:
        bias.append("west")

    return list(dict.fromkeys(bias))


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


def difficulty_to_waypoints(raw_difficulty: Any) -> int:
    """
    Map the UI difficulty scale (1-5) to valid MissionConstraints waypoint counts.

    The tool exposes 3-10 ORS waypoints, while the UI and planner use a 1-5
    difficulty scale. Difficulty 4 and 5 are preserved as 4 and 5 so the
    existing difficulty boost in scouting keeps working; 1-3 map to the
    default of 3 waypoints. This keeps the tool's public schema unchanged.

    Args:
        raw_difficulty: Difficulty value coming from the UI or the planner.

    Returns:
        An integer in the 3-5 range accepted by trail_scout_simple.
    """
    return max(3, clamp_complexity(raw_difficulty))


_WHEEL_SIZE_PATTERNS = (
    r'\b29\s*-?\s*(?:er\b|"|inch(?:es)?\b|in\b|pollici\b)',
    r'\b27[.,]5\s*-?\s*(?:er\b|"|inch(?:es)?\b|in\b|pollici\b)',
    r"\b650\s*b\b",
)

_COMPLEXITY_PATTERNS = (
    (
        r"\bvery\s+hard\b|\bextreme(?:ly)?\b|\bmolto\s+difficile\b|\bdifficilissim[oa]\b",
        5,
    ),
    (r"\bhard\b|\bdifficile\b|\bimpegnativ[oa]\b", 4),
    (r"\bmoderat[eo]\b", 3),
    (r"\beasy\b|\bfacile\b", 2),
)


def extract_bike_type_from_text(user_input: str) -> str | None:
    """
    Infer a bike discipline from explicit names, then from wheel-size hints.

    Explicit disciplines always win over wheel size, so a "29-inch road bike"
    stays a road bike. A bare 29"/27.5"/650b reference implies an MTB.

    Args:
        user_input: The natural-language mission request.
    Returns:
        A normalized discipline name, or None when the text gives no hint.
    """
    text = str(user_input or "").lower().replace("”", '"')

    if any(
        keyword in text
        for keyword in (
            "e-mtb",
            "emtb",
            "e bike",
            "e-bike",
            "ebike",
            "electric bike",
            "bici elettrica",
        )
    ):
        return "e-mtb"
    if "downhill" in text or "enduro" in text:
        return "enduro"
    if "gravel" in text:
        return "gravel"
    if any(keyword in text for keyword in ("road bike", "road cycling", "bici da corsa")):
        return "road"
    if any(keyword in text for keyword in ("mountain bike", "mtb")):
        return "mtb"
    if any(re.search(pattern, text) for pattern in _WHEEL_SIZE_PATTERNS):
        return "mtb"
    return None


def extract_complexity_from_text(user_input: str) -> int | None:
    """
    Map difficulty wording to the 1..5 complexity scale.

    Args:
        user_input: The natural-language mission request.
    Returns:
        The mapped complexity value, or None when no difficulty is stated.
    """
    text = str(user_input or "").lower()
    for pattern, value in _COMPLEXITY_PATTERNS:
        if re.search(pattern, text):
            return value
    return None


def apply_text_overrides(args: dict[str, Any], user_input: str) -> dict[str, Any]:
    """
    Override LLM-generated arguments with deterministic text-derived values.

    Args:
        args: Tool arguments produced by the planner.
        user_input: The original natural-language request.
    Returns:
        A new argument dictionary with bike_type, is_ebike, complexity and
        off-road routing preferences corrected when stated explicitly.
    """
    overrides: dict[str, Any] = {}

    if extract_prefer_offroad_from_text(user_input):
        overrides["avoid_urban"] = True
        overrides["prefer_rural"] = True
        overrides["priority_mode"] = "ride_character_first"

    bike_type = extract_bike_type_from_text(user_input)
    if bike_type is not None:
        final_bike, is_ebike = normalize_bike_type(bike_type)
        overrides["bike_type"] = final_bike
        overrides["is_ebike"] = is_ebike

    complexity = extract_complexity_from_text(user_input)
    if complexity is not None:
        overrides["complexity"] = clamp_complexity(complexity)

    if not overrides:
        return dict(args)

    return {**args, **overrides}


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
        "tire_width_mm": args.get("tire_width_mm"),
        "rim_internal_width_mm": args.get("rim_internal_width_mm"),
        "casing_type": args.get("casing_type"),
        "tubeless": args.get("tubeless"),
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
        return f"{ctx['location_name']} → {ctx['destination_name']} · {ctx.get('bike_type', 'mtb')}"

    return (
        f"{ctx['location_name']} · {ctx.get('distance_km', '?')} km · {ctx.get('bike_type', 'mtb')}"
    )


def resolve_location_query(args: dict, user_input: str) -> str | None:
    return (
        args.get("location_name")
        or st.session_state.get("last_location_query")
        or extract_location_hint(user_input)
        or (st.session_state.get("mission_context") or {}).get("location_name")
    )


def compute_readiness_score(
    info: dict, conditions: dict, logistics: dict
) -> tuple[int, str, list[str]]:
    score = 82
    badges: list[str] = []

    difficulty = str(info.get("difficulty", "")).lower()
    if "hard" in difficulty or "expert" in difficulty:
        score -= 12
        badges.append("Hard route")
    elif "moderate" in difficulty:
        score -= 5
        badges.append("Moderate load")

    mud = ((conditions or {}).get("mud_risk") or {}).get("tactical_analysis", {})
    mud_score = str(mud.get("mud_risk_score", "")).lower()
    if "high" in mud_score:
        score -= 18
        badges.append("High mud risk")
    elif "moderate" in mud_score:
        score -= 9
        badges.append("Moderate mud")

    safety = (conditions or {}).get("safety_advice") or {}
    wind_risk = ext_cast(safety.get("wind_risk_score"), int, 0)
    if wind_risk >= 8:
        score -= 15
        badges.append("Strong wind")
    elif wind_risk >= 5:
        score -= 7
        badges.append("Wind caution")

    pois = (logistics or {}).get("nearby_amenities") or []
    if pois:
        score += 4
        badges.append("Support points nearby")

    score = max(0, min(100, score))
    if score >= 80:
        status = "Go"
    elif score >= 60:
        status = "Caution"
    else:
        status = "Risk"

    return score, status, badges


def compute_mission_intensity(info: dict, conditions: dict, logistics: dict) -> tuple[str, str]:
    difficulty = ext_cast(info.get("difficulty"), float, 0)
    ascent = ext_cast(info.get("ascent_m"), float, 0)
    distance = ext_cast(info.get("distance_km"), float, 0)
    route_type = str(info.get("route_type", "")).lower()

    surface_analysis = info.get("surface_analysis", {}) or {}
    tactical = surface_analysis.get("tactical_briefing", {}) or {}
    climb_category = str(tactical.get("climb_category", "")).lower()

    mud_data = conditions.get("mud_risk", {}) or {}
    tactical_mud = mud_data.get("tactical_analysis", {}) or {}
    mud_score_raw = str(tactical_mud.get("mud_risk_score", "0")).strip().lower()

    if "high" in mud_score_raw:
        mud_score = 3
    elif "medium" in mud_score_raw:
        mud_score = 2
    elif "low" in mud_score_raw:
        mud_score = 1
    else:
        mud_score = ext_cast(mud_score_raw, float, 0)

    intensity_score = 0
    intensity_score += difficulty * 1.5
    intensity_score += 2 if distance >= 80 else 1 if distance >= 45 else 0
    intensity_score += 2 if ascent >= 1800 else 1 if ascent >= 800 else 0
    intensity_score += 1 if "point" in route_type else 0
    intensity_score += 1 if "cat" in climb_category or "steep" in climb_category else 0
    intensity_score += 1 if mud_score >= 2 else 0

    if intensity_score <= 2:
        return "RECOVERY", "#38bdf8"
    if intensity_score <= 4:
        return "ENDURANCE", "#22c55e"
    if intensity_score <= 6:
        return "ADVENTURE", "#f59e0b"
    if intensity_score <= 8:
        return "TECHNICAL", "#ef4444"
    return "EXPEDITION", "#a855f7"


def extract_avoid_urban_from_text(user_input: str) -> bool:
    text = (user_input or "").lower()
    patterns = [
        "avoid urban",
        "avoid the city",
        "avoid city",
        "avoid urban streets",
        "stay out of the city",
        "less urban",
        "non-urban",
    ]
    return any(p in text for p in patterns)


def extract_prefer_rural_from_text(user_input: str) -> bool:
    text = (user_input or "").lower()
    patterns = [
        "prefer countryside",
        "countryside roads",
        "prefer rural",
        "rural roads",
        "open countryside",
        "quieter roads",
        "quiet roads",
        "country roads",
        "scenic roads",
    ]
    return any(p in text for p in patterns)


def extract_prefer_offroad_from_text(user_input: str) -> bool:
    """Detect an explicit request for off-road / singletrack riding."""
    text = (user_input or "").lower()
    patterns = [
        "singletrack",
        "single track",
        "off-road",
        "off road",
        "mtb trails",
        "mountain bike trails",
        "dirt trails",
        "trail riding",
        "avoid paved",
        "avoid asphalt",
        "no asphalt",
        "mostly trails",
        "sentieri",
        "fuoristrada",
    ]
    return any(p in text for p in patterns)


def extract_distance_flex_from_text(user_input: str) -> tuple[int, str | None]:
    text = (user_input or "").lower()

    if any(
        p in text
        for p in [
            "exactly",
            "as close as possible",
            "precisely",
            "exact distance",
        ]
    ):
        return 0, "distance_first"

    if any(
        p in text
        for p in [
            "doesn't have to be exact",
            "does not have to be exact",
            "roughly",
            "around",
            "about",
            "approximately",
        ]
    ):
        return 10, "balanced"

    if any(
        p in text
        for p in [
            "ride character matters more",
            "vibe matters more",
            "more about the ride quality",
            "prefer the character of the ride",
        ]
    ):
        return 15, "ride_character_first"

    return 10, None


def extract_distance_km_from_text(user_input: str):
    text = user_input or ""
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*km\b", text.lower())
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def normalize_direction_bias(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        value = [value]

    allowed = {"north", "south", "east", "west"}
    normalized = []

    for item in value:
        item_str = str(item).strip().lower()
        if item_str in allowed and item_str not in normalized:
            normalized.append(item_str)

    return normalized


def init_session_state() -> None:
    defaults = {
        "messages": [],
        "mission_context": {},
        "mission_history": [],
        "ors_api_key": os.getenv("ORS_API_KEY", ""),
        "last_location_query": None,
        "last_raw_distance": 25.0,
        "current_tab": "Plan a Ride",
        "workspace_tab_selector": "Plan a Ride",
        "pending_tab_redirect": None,
        "pending_chat_prompt": None,
        "pending_chat_hidden": False,
        "pending_plan_request": None,
        "rider_profile": {
            "bike_type": "mtb",
            "tire_size": "29",
            "tire_width_mm": default_tire_width_mm("mtb"),
            "rim_internal_width_mm": default_rim_internal_width_mm("mtb"),
            "casing_type": default_casing_type("mtb"),
            "tubeless": True,
            "fitness_level": "intermediate",
            "weight_kg": 75.0,
            "gender": "male",
            "sweat_rate_ml_per_hour": None,
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def update_mission_context(
    location_name: str,
    lat: float,
    lon: float,
    args: dict,
    distance_km: float,
    route_mode: str = "round_trip",
    destination_name: str | None = None,
    dest_lat: float | None = None,
    dest_lon: float | None = None,
):
    st.session_state["last_location_query"] = location_name
    ctx = build_mission_snapshot(
        location_name=location_name,
        lat=lat,
        lon=lon,
        args=args,
        distance_km=distance_km,
        route_mode=route_mode,
        destination_name=destination_name,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
    )
    st.session_state["mission_context"] = ctx

    history = st.session_state.get("mission_history", [])
    history = [summarize_mission(ctx)] + history[:4]
    st.session_state["mission_history"] = history


VALID_CASING_TYPES = {"xc", "trail", "enduro", "dh"}


def setup_args_from_request(request: dict, profile: dict, bike_type: str) -> dict[str, Any]:
    """Resolve tire/rim/casing inputs from a plan request and rider defaults."""
    casing = (
        str(
            request.get("casing_type")
            or profile.get("casing_type")
            or default_casing_type(bike_type)
        )
        .strip()
        .lower()
    )
    if casing not in VALID_CASING_TYPES:
        casing = default_casing_type(bike_type)

    return {
        "tire_width_mm": ext_cast(
            request.get("tire_width_mm", profile.get("tire_width_mm")),
            int,
            default_tire_width_mm(bike_type),
        ),
        "rim_internal_width_mm": ext_cast(
            request.get("rim_internal_width_mm", profile.get("rim_internal_width_mm")),
            int,
            default_rim_internal_width_mm(bike_type),
        ),
        "casing_type": casing,
        "tubeless": ext_cast(request.get("tubeless", profile.get("tubeless", True)), bool, True),
    }


def append_mission_summary(text: str) -> str:
    ctx = st.session_state.get("mission_context") or {}
    if not ctx:
        return text
    return f"{text}\n\n[{summarize_mission(ctx)}]"
