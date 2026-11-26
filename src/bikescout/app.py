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

import json
import os
import random
import re
from datetime import date
from typing import Any, Literal, cast

import streamlit as st
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

from bikescout.app_helpers import (
    apply_text_overrides,
    build_mission_snapshot,
    clamp_complexity,
    compute_mission_intensity,
    difficulty_to_waypoints,
    compute_readiness_score,
    ext_cast,
    extract_avoid_urban_from_text,
    extract_direction_bias_from_text,
    extract_distance_flex_from_text,
    extract_distance_km_from_text,
    extract_point_to_point,
    extract_prefer_rural_from_text,
    normalize_bike_type,
    normalize_direction_bias,
    normalize_tire_size,
    resolve_location_query,
    resolve_profile,
    resolve_route_mode,
    summarize_mission,
    wants_overlay,
)
from bikescout.app_ui_helpers import (
    build_warning_ribbon,
    get_poi_style,
    get_surface_icon,
    inject_component_styles,
    inject_global_styles,
    metric_card,
    normalize_tire_setup,
    render_empty_state,
    render_mission_intensity_badge,
    render_rider_profile_panel,
    render_score_card,
    render_warning_ribbon,
    render_weather_tiles_native,
    section_intro,
)
from bikescout.mcp_server import (
    analyze_gpx_track,
    geocode_location,
    trail_scout_simple,
)
from bikescout.tools.bike_setup import (
    default_casing_type,
    default_rim_internal_width_mm,
    default_tire_width_mm,
)

AVAILABLE_MODELS = {
    "Qwen3.5-9B": {
        "repo": "unsloth/Qwen3.5-9B-GGUF",
        "file": "Qwen3.5-9B-Q4_K_M.gguf",
        "description": "Size: ~5.7 GB",
    },
    "Ministral-3-8B-Instruct": {
        "repo": "unsloth/Ministral-3-8B-Instruct-2512-GGUF",
        "file": "Ministral-3-8B-Instruct-2512-Q4_K_M.gguf",
        "description": "Size: ~5.2 GB",
    },
    "Qwen2.5-7B-Instruct": {
        "repo": "bartowski/Qwen2.5-7B-Instruct-GGUF",
        "file": "Qwen2.5-7B-Instruct-Q6_K.gguf",
        "description": "Size: ~6.3 GB",
    },
}

LOCAL_MODELS_DIR = "models"

st.set_page_config(
    page_title="BikeScout",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_sidebar() -> tuple[str, int]:
    with st.sidebar:
        st.markdown(
            """
            <div class="bs-sidebar-brand">
                <span class="bs-sidebar-bike">Bike</span><span class="bs-sidebar-scout">Scout</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("AI for tactical cycling intelligence")

        st.subheader("Routing & API")
        ors_key = st.text_input(
            "OpenRouteService key",
            value=st.session_state.get("ors_api_key", ""),
            type="password",
            help="Required for routing, geocoding, and trail analysis.",
        )
        if ors_key:
            st.session_state["ors_api_key"] = ors_key
            os.environ["ORS_API_KEY"] = ors_key

        st.subheader("Local model")
        selected_model_name = cast(str, st.selectbox("Model", list(AVAILABLE_MODELS.keys())))
        st.caption(AVAILABLE_MODELS[selected_model_name]["description"])

        gpu_enabled = st.toggle("GPU acceleration", value=True)
        n_layers = -1 if gpu_enabled else 0

        model_path = get_local_model_path(selected_model_name)
        if not os.path.exists(model_path):
            if st.button(f"Download {selected_model_name}", use_container_width=True):
                with st.status("Downloading local model...", expanded=True):
                    os.makedirs(LOCAL_MODELS_DIR, exist_ok=True)
                    hf_hub_download(
                        repo_id=AVAILABLE_MODELS[selected_model_name]["repo"],
                        filename=AVAILABLE_MODELS[selected_model_name]["file"],
                        local_dir=LOCAL_MODELS_DIR,
                    )
                    st.success("Model downloaded. Reloading...")
                    st.rerun()
            st.warning("A local model is required to use the chat planner.")

        if st.button("Clear chat & mission", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["mission_context"] = {}
            st.session_state["mission_history"] = []
            st.session_state["last_location_query"] = None
            st.session_state["last_raw_distance"] = 25.0
            st.rerun()

        return selected_model_name, n_layers


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
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_local_model_path(model_name: str) -> str:
    return os.path.join(LOCAL_MODELS_DIR, AVAILABLE_MODELS[model_name]["file"])


@st.cache_resource
def load_llm(model_name: str, n_gpu_layers: int):
    path = get_local_model_path(model_name)
    if not os.path.exists(path):
        return None

    kwargs = {}
    if "Qwen3.5" in model_name:
        kwargs["chat_template_kwargs"] = {"enable_thinking": False}

    return Llama(
        model_path=path,
        n_ctx=8192,
        n_gpu_layers=n_gpu_layers,
        verbose=False,
        **kwargs,
    )


def generate_tactical_response(
    messages_history: list, llm_instance: Llama, mission_context: dict | None = None
) -> str:
    json_schema = {
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {
                "briefing": {"type": "string"},
                "can_execute": {"type": "boolean"},
                "tool": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "enum": ["trail_scout_simple"]},
                                "args": {
                                    "type": "object",
                                    "properties": {
                                        "bike_type": {
                                            "type": "string",
                                            "enum": ["mtb", "road", "gravel", "e-mtb", "enduro"],
                                        },
                                        "tire_size": {"type": "string"},
                                        "distance": {"type": "number"},
                                        "route_mode": {
                                            "type": "string",
                                            "enum": ["round_trip", "point_to_point"],
                                        },
                                        "location_name": {"type": "string"},
                                        "destination_name": {"type": "string"},
                                        "dest_latitude": {"type": "number"},
                                        "dest_longitude": {"type": "number"},
                                        "latitude": {"type": "number"},
                                        "longitude": {"type": "number"},
                                        "include_weather": {"type": "boolean"},
                                        "include_mud_analysis": {"type": "boolean"},
                                        "include_nutrition_plan": {"type": "boolean"},
                                        "include_poi": {"type": "boolean"},
                                        "include_gpx": {"type": "boolean"},
                                        "include_map": {"type": "boolean"},
                                        "include_altimetry": {"type": "boolean"},
                                        "is_ebike": {"type": "boolean"},
                                        "weight_kg": {"type": "number"},
                                        "seed": {"type": "number"},
                                        "complexity": {
                                            "type": "integer",
                                            "minimum": 1,
                                            "maximum": 5,
                                        },
                                        "profile": {
                                            "type": "string",
                                            "enum": [
                                                "cycling-mountain",
                                                "cycling-road",
                                                "cycling-regular",
                                                "cycling-electric",
                                            ],
                                        },
                                        "fitness_level": {
                                            "type": "string",
                                            "enum": ["beginner", "intermediate", "pro"],
                                        },
                                        "gender": {
                                            "type": "string",
                                            "enum": ["male", "female"],
                                        },
                                        "direction_bias": {
                                            "type": "array",
                                            "items": {
                                                "type": "string",
                                                "enum": ["north", "south", "east", "west"],
                                            },
                                        },
                                        "avoid_urban": {"type": "boolean"},
                                        "prefer_rural": {"type": "boolean"},
                                        "distance_flex_percent": {
                                            "type": "integer",
                                            "minimum": 0,
                                            "maximum": 30,
                                        },
                                        "priority_mode": {
                                            "type": "string",
                                            "enum": [
                                                "balanced",
                                                "distance_first",
                                                "ride_character_first",
                                            ],
                                        },
                                    },
                                    "required": ["bike_type", "tire_size", "location_name"],
                                },
                            },
                            "required": ["name", "args"],
                        },
                        {"type": "null"},
                    ]
                },
            },
            "required": ["briefing", "tool", "can_execute"],
        },
    }

    mission_block = ""
    if mission_context:
        mission_block = f"""
=== ACTIVE MISSION ===
{json.dumps(mission_context, ensure_ascii=False)}
Reuse mission location unless user explicitly changes it.
Reuse mission routing preferences unless user explicitly changes them.
"""

    system_prompt = f"""
You are BikeScout Tactical AI.
Return ONLY valid JSON matching the schema.
Set can_execute=true only when the user clearly wants a cycling route or route-related analysis.
When can_execute=true, use tool trail_scout_simple.
Always preserve location context for follow-up requests.
Always preserve routing preference context for follow-up requests unless the user changes it.
Distance must be in kilometers.
Complexity range is 1..5, default 3.
Use point_to_point only for A to B routes.

Bike and difficulty normalization rules:
- Infer bike_type="mtb" when the user only names 29"/29er/27.5"/650b wheels; explicit disciplines win.
- Map difficulty wording to complexity: easy=1-2, moderate=3, hard=4, very hard/extreme=5.
- Map profile from bike_type: mtb/enduro/gravel -> cycling-mountain, road -> cycling-road, e-mtb -> cycling-electric.
- Set every explicitly requested include_* flag to true, even for road rides.

Routing preference extraction rules:
- If the user asks to stay south, north, east, or west of the start area, set direction_bias accordingly.
- If the user asks for south-east, south and east, or similar, set direction_bias to multiple values, e.g. ["south", "east"].
- If the user asks to avoid the city, avoid urban streets, or avoid traffic-heavy urban riding, set avoid_urban=true.
- If the user asks for countryside, quieter roads, open country, rural roads, or scenic non-urban riding, set prefer_rural=true.
- If the user asks for mostly MTB singletrack, off-road/dirt trails, or to avoid paved roads, also set profile="cycling-mountain", avoid_urban=true, prefer_rural=true, priority_mode="ride_character_first", and distance_flex_percent between 15 and 20.
- If the user cares more about the ride character than exact distance, set priority_mode="ride_character_first".
- If the user explicitly wants the route as close as possible to the requested distance, set priority_mode="distance_first".
- Otherwise use priority_mode="balanced".
- If the user allows some tolerance on distance, set distance_flex_percent between 10 and 20 depending on wording.
- If the user strongly prioritizes exact target distance, set distance_flex_percent=0.
- If no directional or routing preference is mentioned, omit these fields or preserve them from active mission context.

Examples:
- "keep it south and east of town" -> direction_bias ["south", "east"]
- "avoid the city and prefer countryside roads" -> avoid_urban true, prefer_rural true
- "mostly singletrack MTB trails, no asphalt" -> profile cycling-mountain, avoid_urban true, prefer_rural true, priority_mode ride_character_first, distance_flex_percent 15 or 20
- "about 60 km, doesn't have to be exact" -> distance_flex_percent 10 or 15, priority_mode "balanced"
- "the vibe matters more than exact mileage" -> priority_mode "ride_character_first"
- "make it exactly 60 km if possible" -> priority_mode "distance_first", distance_flex_percent 0

{mission_block}
"""

    formatted_messages = [{"role": "system", "content": system_prompt}]
    llm_history = [
        m
        for m in messages_history
        if m.get("role") == "user"
        or (
            m.get("role") == "assistant"
            and m.get("content") != "Connection established. Provide input..."
        )
    ]
    formatted_messages.extend(llm_history[-6:])

    response = cast(
        dict[str, Any],
        llm_instance.create_chat_completion(
            messages=cast(Any, formatted_messages),
            response_format=cast(Any, json_schema),
            temperature=0.0,
            max_tokens=1024,
        ),
    )
    return str(response["choices"][0]["message"]["content"]).strip()


def _update_mission_context(
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


def _setup_args_from_request(request: dict, profile: dict, bike_type: str) -> dict[str, Any]:
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


def _append_mission_summary(text: str) -> str:
    ctx = st.session_state.get("mission_context") or {}
    if not ctx:
        return text
    return f"{text}\n\n[{summarize_mission(ctx)}]"


def _execute_and_store_request(plan_request: dict, history_label: str | None = None) -> None:
    with st.chat_message("assistant"):
        assistant_text, had_visual_result = execute_plan_request(plan_request)
        if not had_visual_result:
            st.markdown(assistant_text)

    stored_text = history_label if history_label else assistant_text
    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": _append_mission_summary(stored_text),
        }
    )


def render_chat_tab(llm):
    section_intro(
        "AI Ride Planner",
        "Chat with BikeScout to generate route plans, tactical overlays, logistics, and exports.",
    )

    if not st.session_state["messages"]:
        render_empty_state(
            "Start a mission",
            "Try something like: 45 km gravel loop near Siena with water stops, weather, mud analysis and GPX.",
        )

    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    pending_plan_request = st.session_state.get("pending_plan_request")
    manual_input = st.chat_input("Describe your ride mission...")

    if pending_plan_request:
        st.session_state["pending_plan_request"] = None
        st.session_state["pending_chat_prompt"] = None
        st.session_state["pending_chat_hidden"] = False

        st.info("Mission received from Plan a Ride. Running route analysis...")
        _execute_and_store_request(pending_plan_request)
        return

    if not manual_input:
        return

    if llm is None:
        with st.chat_message("assistant"):
            st.error("Local model not available. Download a model from the sidebar first.")
        return

    st.session_state["messages"].append({"role": "user", "content": manual_input})
    with st.chat_message("user"):
        st.markdown(manual_input)

    llm_messages = list(st.session_state["messages"])

    with st.chat_message("assistant"):
        raw_output = generate_tactical_response(
            llm_messages,
            llm,
            mission_context=st.session_state.get("mission_context"),
        )
        final_briefing, had_visual_result = process_local_mcp_request(raw_output, manual_input)
        clean_briefing = re.sub(r"(?i)TOOL:.*", "", final_briefing, flags=re.DOTALL).strip()

        generic_briefings = {
            "",
            "Completed",
            "Mission Briefing",
            "Analysis complete.",
            "Mission analysis complete.",
        }

        should_render_text = not had_visual_result or clean_briefing not in generic_briefings

        if should_render_text:
            assistant_text = clean_briefing or "Mission analysis complete."
            st.markdown(assistant_text)
        else:
            assistant_text = "Mission generated successfully."

    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": _append_mission_summary(assistant_text),
        }
    )


def execute_plan_request(plan_request: dict):
    if not plan_request:
        return "No plan request found.", False

    try:
        rider_profile = st.session_state["rider_profile"]

        route_mode = plan_request.get("route_mode", "loop")
        start_location = cast(str, plan_request.get("start_location"))
        destination_location = plan_request.get("destination_location")
        bike_type = plan_request.get("bike_type", rider_profile["bike_type"])
        final_bike, is_ebike = normalize_bike_type(bike_type)

        tire_size = normalize_tire_size(
            plan_request.get("tire_size") or rider_profile["tire_size"],
            final_bike,
        )

        setup_args = _setup_args_from_request(plan_request, rider_profile, final_bike)
        complexity_val = clamp_complexity(plan_request.get("complexity", 3))
        raw_distance = ext_cast(plan_request.get("distance"), float, 25.0)

        direction_bias = normalize_direction_bias(plan_request.get("direction_bias"))
        avoid_urban = bool(plan_request.get("avoid_urban", False))
        prefer_rural = bool(plan_request.get("prefer_rural", False))
        distance_flex_percent = max(
            0, min(30, ext_cast(plan_request.get("distance_flex_percent"), int, 10))
        )
        priority_mode = str(plan_request.get("priority_mode", "balanced")).strip().lower()
        if priority_mode not in {"balanced", "distance_first", "ride_character_first"}:
            priority_mode = "balanced"

        geo = geocode_location(location_name=start_location)
        if getattr(geo, "status", None) != "Success":
            return f"Could not geocode: {start_location}", False

        dest_lat, dest_lon = None, None
        dest_display = None

        if route_mode == "point_to_point":
            if not destination_location:
                return "Please specify both start and destination.", False

            geo_dest = geocode_location(location_name=destination_location)
            if getattr(geo_dest, "status", None) != "Success":
                return f"Could not geocode destination: {destination_location}", False

            dest_lat = float(geo_dest.lat)
            dest_lon = float(geo_dest.lon)
            dest_display = getattr(geo_dest, "display_name", destination_location)

        _update_mission_context(
            cast(str, getattr(geo, "display_name", start_location)),
            geo.lat,
            geo.lon,
            {
                "bike_type": final_bike,
                "tire_size": tire_size,
                **setup_args,
                "complexity": difficulty_to_waypoints(complexity_val),
                "direction_bias": direction_bias,
                "avoid_urban": avoid_urban,
                "prefer_rural": prefer_rural,
                "distance_flex_percent": distance_flex_percent,
                "priority_mode": priority_mode,
            },
            raw_distance if route_mode != "point_to_point" else 0,
            route_mode=route_mode,
            destination_name=dest_display if route_mode == "point_to_point" else None,
            dest_lat=dest_lat,
            dest_lon=dest_lon,
        )

        valid_args = {
            "latitude": float(geo.lat),
            "longitude": float(geo.lon),
            "tire_size": tire_size,
            **setup_args,
            "include_weather": bool(plan_request.get("include_weather", True)),
            "include_mud_analysis": bool(plan_request.get("include_mud", final_bike != "road")),
            "include_nutrition_plan": bool(plan_request.get("include_nutrition", True)),
            "include_poi": bool(plan_request.get("include_poi", True)),
            "include_gpx": bool(plan_request.get("include_gpx", True)),
            "include_map": True,
            "include_altimetry": bool(plan_request.get("include_altimetry", True)),
            "weight_kg": ext_cast(rider_profile.get("weight_kg"), float, 75.0),
            "gender": str(rider_profile.get("gender", "male")),
            "seed": random.randint(1, 999999),
            "complexity": difficulty_to_waypoints(complexity_val),
            "bike_type": final_bike,
            "profile": resolve_profile(final_bike),
            "is_ebike": is_ebike,
            "fitness_level": str(rider_profile.get("fitness_level", "intermediate")),
            "direction_bias": direction_bias,
            "avoid_urban": avoid_urban,
            "prefer_rural": prefer_rural,
            "distance_flex_percent": distance_flex_percent,
            "priority_mode": priority_mode,
        }

        if route_mode == "point_to_point":
            valid_args["dest_latitude"] = float(cast(float, dest_lat))
            valid_args["dest_longitude"] = float(cast(float, dest_lon))
        else:
            valid_args["total_length_km"] = raw_distance

        with st.expander("Engine debug", expanded=False):
            st.json(valid_args)

        result = trail_scout_simple(**valid_args)
        res_data = cast(
            dict[str, Any],
            result.model_dump() if hasattr(result, "model_dump") else result,
        )

        with st.expander("Engine response", expanded=False):
            st.json(res_data)

        if not res_data or res_data.get("status") != "Success":
            return "The system could not generate a route for this configuration.", False

        render_route_results(res_data)
        return "Mission generated successfully.", True

    except Exception as e:
        st.error("Something went wrong while planning the route.")
        with st.expander("Technical details"):
            st.code(f"{type(e).__name__}: {e}", language="text")
        return "Unable to complete route planning.", False


def _is_number(value) -> bool:
    """Return True for real numbers, excluding booleans."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _format_terrain_value(value, digits: int = 1, suffix: str = "") -> str:
    """Format an optional terrain number for display."""
    if not _is_number(value):
        return "N/A"
    return f"{float(value):.{digits}f}{suffix}"


def _format_terrain_percent(value) -> str:
    """Format a 0.0-1.0 confidence score as a percentage."""
    if not _is_number(value):
        return "N/A"
    return f"{float(value) * 100:.0f}%"


def _terrain_climb_rows(tactical_briefing: dict, terrain_analysis: dict) -> list[dict[str, str]]:
    """Format geometry-detected climbs for the Streamlit climb list table."""
    climbs = (
        tactical_briefing.get("climb_list")
        or terrain_analysis.get("climbs")
        or terrain_analysis.get("climb_list")
        or []
    )

    rows: list[dict[str, str]] = []
    for number, climb in enumerate(climbs, start=1):
        if not isinstance(climb, dict):
            continue

        length_m = climb.get("length_m")
        length_km = None
        if isinstance(length_m, (int, float)) and not isinstance(length_m, bool):
            length_km = length_m / 1000.0
        rows.append(
            {
                "#": str(number),
                "Category": str(climb.get("category", "N/A")),
                "Gain (m)": _format_terrain_value(climb.get("gain_m")),
                "Length (km)": _format_terrain_value(length_km, 2),
                "Avg grade": _format_terrain_value(climb.get("avg_gradient"), 1, "%"),
                "Max grade": _format_terrain_value(climb.get("max_gradient"), 1, "%"),
                "Summit (m)": _format_terrain_value(climb.get("summit_elevation_m")),
                "FIETS": _format_terrain_value(climb.get("fiets_index"), 2),
                "Profile samples": f"{climb.get('start_index', '?')}–{climb.get('end_index', '?')}",
            }
        )
    return rows


def render_route_results(res_data: dict) -> None:
    info = res_data.get("info", {}) or {}
    logistics = res_data.get("logistics", {}) or {}
    conditions = res_data.get("conditions", {}) or {}

    if not info:
        st.warning("Route not found.")
        return

    score, status, badges = compute_readiness_score(info, conditions, logistics)

    intensity_label, intensity_color = compute_mission_intensity(info, conditions, logistics)
    warning_items = build_warning_ribbon(info, conditions, logistics)

    route_type = str(info.get("route_type", "Round Trip"))
    distance_km = info.get("distance_km", "N/A")
    ascent_m = info.get("ascent_m", "N/A")
    difficulty = info.get("difficulty", "N/A")

    weather_data = (conditions.get("weather") or []) if conditions else []
    safety_advice = conditions.get("safety_advice", {}) if conditions else {}
    mud_data = conditions.get("mud_risk", {}) if conditions else {}
    surface_analysis = info.get("surface_analysis", {}) or {}

    weather_summary = safety_advice.get("status", "Stable") if safety_advice else "Stable"
    surface_mix = "Mixed terrain" if surface_analysis else "Standard route"

    st.markdown(
        f"""
        <div class="bs-hud">
            <div class="bs-hud-top">
                <div class="bs-hud-title-wrap">
                    <div class="bs-hud-kicker">TACTICAL MISSION OVERVIEW</div>
                    <div class="bs-hud-title">{route_type}</div>
                </div>
            </div>
            <div class="bs-hud-grid">
                <div class="bs-hud-chip">
                    <span>Distance</span>
                    <strong>{distance_km} km</strong>
                </div>
                <div class="bs-hud-chip">
                    <span>Ascent</span>
                    <strong>{ascent_m} m</strong>
                </div>
                <div class="bs-hud-chip">
                    <span>Difficulty</span>
                    <strong>{difficulty}</strong>
                </div>
                <div class="bs-hud-chip">
                    <span>Weather</span>
                    <strong>{weather_summary}</strong>
                </div>
                <div class="bs-hud-chip">
                    <span>Terrain</span>
                    <strong>{surface_mix}</strong>
                </div>
                <div class="bs-hud-chip">
                    <span>Readiness</span>
                    <strong>{status}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_left, top_right = st.columns([1, 3])
    with top_left:
        render_mission_intensity_badge(intensity_label, intensity_color)
    with top_right:
        render_warning_ribbon(warning_items)

    section_intro(
        "Mission summary",
        "High-level overview before diving into terrain, weather, mud, and support logistics.",
    )

    c0, c1 = st.columns([1.05, 2.15])
    with c0:
        render_score_card(score, status, badges)

    with c1:
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            metric_card("Distance", f"{distance_km} km", "📏", "#38bdf8", "Target route length")
        with g2:
            metric_card("Ascent", f"{ascent_m} m", "⛰️", "#a78bfa", "Total elevation gain")
        with g3:
            metric_card("Difficulty", str(difficulty), "⚡", "#f472b6", "Estimated route challenge")
        with g4:
            metric_card("Route type", route_type, "🧭", "#22c55e", "Loop or A→B")

    st.markdown('<div class="bs-grid-gap"></div>', unsafe_allow_html=True)

    if surface_analysis:
        section_intro(
            "Terrain intelligence", "Surface mix, gradient profile, and tactical setup signals."
        )

        tactical = surface_analysis.get("tactical_briefing", {}) or {}
        terrain = tactical.get("terrain_analysis", {}) or {}
        metadata = surface_analysis.get("metadata", {}) or {}
        elevation_source = metadata.get("elevation_source")

        max_gradient = tactical.get("max_gradient", terrain.get("max_gradient"))
        confidence = tactical.get("data_confidence", terrain.get("data_confidence"))
        technical = (
            tactical.get("technical_difficulty") or terrain.get("technical_difficulty") or {}
        )
        if not isinstance(technical, dict):
            technical = {}

        noise_floor = terrain.get("noise_floor_m")
        profile_points = terrain.get("profile_points")
        profile_length_m = terrain.get("profile_length_m")
        profile_length_km = None
        if isinstance(profile_length_m, (int, float)) and not isinstance(profile_length_m, bool):
            profile_length_km = profile_length_m / 1000.0
        terrain_warnings = [str(warning) for warning in (terrain.get("warnings", []) or [])]

        r1, r2, r3, r4 = st.columns(4)

        with r1:
            metric_card(
                "Avg gradient",
                str(tactical.get("avg_gradient", "N/A")),
                "📈",
                "#2dd4bf",
                "Overall gradient profile",
            )
        with r2:
            metric_card(
                "Climb profile",
                str(tactical.get("climb_category", "N/A")),
                "🧗",
                "#fb923c",
                "Climbing classification",
            )
        with r3:
            metric_card(
                "Climb gradient",
                str(tactical.get("avg_climb_gradient", "N/A")),
                "🔺",
                "#f87171",
                "Climbing intensity",
            )
        with r4:
            metric_card(
                "Max gradient",
                f"{max_gradient}%" if max_gradient is not None else "N/A",
                "⚡",
                "#facc15",
                "Steepest measured pitch",
            )

        q1, q2, q3, q4 = st.columns(4)

        with q1:
            confidence_sub = (
                f"Noise floor {noise_floor} m"
                if noise_floor is not None
                else "Elevation trust score"
            )
            metric_card(
                "Data confidence",
                _format_terrain_percent(confidence),
                "🧪",
                "#22d3ee",
                confidence_sub,
            )
        with q2:
            tech_confidence = technical.get("confidence")
            tech_source = str(technical.get("source", ""))
            tech_sub = "Terrain grade confidence"
            if _is_number(tech_confidence):
                tech_sub = f"{_format_terrain_percent(tech_confidence)} confidence"
                if tech_source:
                    tech_sub += f" · {tech_source}"
            metric_card(
                "Technical grade",
                str(technical.get("label", "N/A")),
                "🥷",
                "#c084fc",
                tech_sub,
            )
        with q3:
            metric_card(
                "Profile length",
                _format_terrain_value(profile_length_km, 2, " km"),
                "🛰️",
                "#60a5fa",
                "Analyzed route geometry",
            )
        with q4:
            metric_card(
                "Profile points",
                str(profile_points) if profile_points is not None else "N/A",
                "🔬",
                "#fbbf24",
                "Usable elevation samples",
            )

        if elevation_source:
            st.caption(f"Elevation source: {elevation_source}")

        with st.expander("Climb list", expanded=True):
            climb_rows = _terrain_climb_rows(tactical, terrain)
            if climb_rows:
                st.dataframe(climb_rows, hide_index=True)
            else:
                st.info("No significant climbs detected or climb data unavailable.")

        if terrain_warnings:
            with st.expander("Terrain warnings", expanded=True):
                for warning in terrain_warnings:
                    st.warning(warning)

        surfaces = surface_analysis.get("surface_breakdown", []) or []
        if surfaces:
            with st.expander("Surface breakdown", expanded=True):
                for s in surfaces:
                    s_type = s.get("type", "Unknown")
                    s_pct_str = str(s.get("percentage", "0%"))
                    icon = get_surface_icon(s_type)
                    try:
                        pct_val = float(s_pct_str.replace("%", "").strip()) / 100.0
                    except Exception:
                        pct_val = 0.0

                    st.markdown(
                        f'<div class="bs-surface-row"><strong>{icon} {s_type}</strong></div>',
                        unsafe_allow_html=True,
                    )
                    st.progress(max(0.0, min(1.0, pct_val)), text=s_pct_str)

        mechanical = surface_analysis.get("mechanical_setup", {}) or {}
        if mechanical:
            with st.expander("Mechanical setup", expanded=True):
                setup = normalize_tire_setup(mechanical.get("setup_details"))
                wheel_label = str(setup.get("wheel_label") or "Standard")
                tire_width_mm = setup.get("tire_width_mm")
                tire_label = f"{wheel_label} · {tire_width_mm}mm" if tire_width_mm else wheel_label

                psi_front = setup.get("psi_front")
                psi_rear = setup.get("psi_rear")
                pressure_label = (
                    f"F: {psi_front} / R: {psi_rear} PSI"
                    if psi_front is not None and psi_rear is not None
                    else "N/A"
                )
                bar_front = setup.get("bar_front")
                bar_rear = setup.get("bar_rear")
                bar_label = (
                    f"≈ {bar_front}/{bar_rear} Bar"
                    if bar_front is not None and bar_rear is not None
                    else ""
                )

                m1, m2, m3 = st.columns(3)
                with m1:
                    metric_card("Wheels / tires", tire_label, "🛞", "#60a5fa", "Volume-based setup")
                with m2:
                    metric_card("Pressure F / R", pressure_label, "🔩", "#34d399", bar_label)
                with m3:
                    metric_card(
                        "Setup strategy",
                        str(setup.get("strategy") or "Standard"),
                        "🧰",
                        "#f59e0b",
                        "Terrain optimization",
                    )

                if setup.get("knob_choice"):
                    st.caption(f"Tread choice: **{setup['knob_choice']}**")

                advice = [str(item) for item in (setup.get("advice") or [])]
                if advice:
                    st.markdown("**Setup intelligence**")
                    for item in advice:
                        st.markdown(f"- {item}")

                if not mechanical.get("compatible", True):
                    st.error(
                        "This bike/setup may not be fully compatible with the current route profile."
                    )

                warnings = []
                for warning in list(setup.get("warnings") or []) + list(
                    mechanical.get("safety_warnings") or []
                ):
                    if warning and warning not in terrain_warnings and warning not in warnings:
                        warnings.append(warning)
                for warning in warnings:
                    st.warning(warning)

        emtb_tactical = surface_analysis.get("emtb_tactical", {}) or {}
        if emtb_tactical and emtb_tactical.get("status") == "Success":
            with st.expander("eMTB tactical analytics", expanded=False):
                advice = emtb_tactical.get("tactical_advice", "No tactical advice available")
                st.markdown(
                    f"""
                    <div class="bs-callout">
                        <strong>Battery strategy</strong>
                        {advice}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                b_metrics = emtb_tactical.get("battery_metrics", {}) or {}
                e1, e2, e3 = st.columns(3)
                with e1:
                    metric_card(
                        "Estimated drain",
                        f"{b_metrics.get('estimated_drain_wh', 0):.1f} Wh",
                        "🔋",
                        "#38bdf8",
                    )
                with e2:
                    metric_card(
                        "Remaining battery",
                        f"{b_metrics.get('remaining_battery_pct', 0):.1f}%",
                        "⚡",
                        "#22c55e",
                    )
                with e3:
                    metric_card(
                        "Usable capacity",
                        f"{b_metrics.get('usable_wh_at_temp', 0):.1f} Wh",
                        "🌡️",
                        "#a78bfa",
                    )

    if weather_data:
        section_intro(
            "Weather & safety",
            "Short-term tactical conditions for confidence, pacing, and kit planning.",
        )

        with st.expander("Forecast details", expanded=True):
            peak_temp = None
            max_rain = None

            for w in weather_data:
                temp_raw = str(w.get("temp", "N/A"))
                rain_raw = str(w.get("rain_prob", "N/A"))
                peak_temp = max(peak_temp or -999, ext_cast(temp_raw, float, -999))
                max_rain = max(max_rain or -999, ext_cast(rain_raw, float, -999))

            t1, t2, t3 = st.columns(3)

            with t1:
                metric_card(
                    "Peak temp",
                    f"{peak_temp if peak_temp != -999 else 'N/A'} °C",
                    "🌡️",
                    "#f97316",
                    "Max forecast temperature",
                )
            with t2:
                metric_card(
                    "Max rain prob",
                    f"{max_rain if max_rain != -999 else 'N/A'} %",
                    "🌧️",
                    "#38bdf8",
                    "Highest rain probability",
                )
            with t3:
                metric_card(
                    "Wind risk",
                    f"{safety_advice.get('wind_risk_score', 'N/A')}/10",
                    "💨",
                    "#f59e0b",
                    "Wind exposure indicator",
                )

            render_weather_tiles_native(weather_data)

            try:
                import pandas as pd

                chart_data = []
                for w in weather_data:
                    try:
                        t_val = float(str(w.get("temp")).replace("°C", "").replace("C", "").strip())
                        r_val = float(str(w.get("rain_prob")).replace("%", "").strip())
                        chart_data.append(
                            {
                                "Time": w.get("time"),
                                "Temp (°C)": t_val,
                                "Rain Prob (%)": r_val,
                            }
                        )
                    except Exception:
                        continue

                if chart_data:
                    st.line_chart(pd.DataFrame(chart_data).set_index("Time"), height=240)
            except Exception:
                st.write("Weather chart unavailable.")

            if safety_advice:
                left, right = st.columns([1, 2])
                with left:
                    metric_card(
                        "Safety status",
                        str(safety_advice.get("status", "N/A")),
                        "🛡️",
                        "#22c55e" if status == "Go" else "#f59e0b",
                        "Operational decision signal",
                    )
                with right:
                    st.info(
                        f"**Gear advice:** {safety_advice.get('gear_advice', 'N/A')}  \n\n"
                        f"**Assessment:** {safety_advice.get('message', 'No message')}"
                    )

    mud_data = conditions.get("mud_risk", {}) if conditions else {}
    if mud_data:
        section_intro(
            "Mud & environmental risk", "Trail rideability, traction, and preservation signals."
        )

        tactical_mud = mud_data.get("tactical_analysis", {}) or {}
        env_context = mud_data.get("environmental_context", {}) or {}

        m1, m2, m3 = st.columns(3)
        with m1:
            metric_card(
                "Mud risk",
                str(tactical_mud.get("mud_risk_score", "Unknown")),
                "🟤",
                "#8b5cf6",
                "Overall terrain softness",
            )
        with m2:
            metric_card(
                "Dry time ETA",
                str(tactical_mud.get("dry_time_eta", "N/A")),
                "⏳",
                "#f59e0b",
                "Estimated recovery window",
            )
        with m3:
            metric_card(
                "Rain 72h",
                f"{env_context.get('total_rain_72h_mm', 'N/A')} mm",
                "🌧️",
                "#38bdf8",
                "Recent accumulated rainfall",
            )

        traction = tactical_mud.get("traction_risk", {}) or {}
        damage = tactical_mud.get("trail_damage_risk", {}) or {}

        b1, b2 = st.columns(2)
        with b1:
            st.markdown(
                f"""
                <div class="bs-risk-box">
                    <div class="bs-risk-title">Traction analysis</div>
                    <div class="bs-risk-value">{traction.get("level", "N/A")}</div>
                    <div class="bs-risk-copy">{traction.get("advice", "No advice available.")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with b2:
            st.markdown(
                f"""
                <div class="bs-risk-box">
                    <div class="bs-risk-title">Trail integrity</div>
                    <div class="bs-risk-value">{damage.get("level", "N/A")}</div>
                    <div class="bs-risk-copy">{damage.get("advice", "No advice available.")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    pois = logistics.get("nearby_amenities", {}) if logistics else {}
    if pois:
        section_intro(
            "POI & logistics", "Nearby support points for water, food, repairs, safety, and rest."
        )
        with st.expander("Amenities on route", expanded=True):
            for i in range(0, len(pois), 3):
                cols = st.columns(3)
                for idx, poi in enumerate(pois[i : i + 3]):
                    with cols[idx]:
                        p_name = poi.get("name", "Unknown POI")
                        p_type = poi.get("type", "Amenity")
                        p_dist = poi.get("distance_m", 0)
                        icon, border_color = get_poi_style(p_type)

                        if isinstance(p_dist, (int, float)):
                            dist_str = (
                                f"{p_dist / 1000:.1f} km" if p_dist >= 1000 else f"{int(p_dist)} m"
                            )
                        else:
                            dist_str = "N/A"

                        link = None
                        p_loc = poi.get("location")
                        if isinstance(p_loc, dict):
                            lat = p_loc.get("latitude", p_loc.get("lat"))
                            lon = p_loc.get("longitude", p_loc.get("lon"))
                            if lat is not None and lon is not None:
                                link = (
                                    f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                                )

                        st.markdown(
                            f"""
                            <div class="bs-poi-card" style="--poi-accent:{border_color};">
                                <div class="bs-poi-head">
                                    <div>
                                        <div class="bs-poi-title">{icon} {p_name}</div>
                                        <div class="bs-poi-type">{p_type}</div>
                                    </div>
                                </div>
                                <div class="bs-poi-distance">Distance: {dist_str}</div>
                                <div class="bs-poi-actions">
                                    {"<a href='" + link + "' target='_blank'>Open in Maps ↗</a>" if link else "No coordinates available"}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    nutrition = logistics.get("nutrition_plan", {}) if logistics else {}
    if nutrition:
        briefing_nut = nutrition.get("mission_nutrition_briefing", {}) or {}
        section_intro(
            "Nutrition & hydration",
            "Fueling strategy aligned with distance, intensity, and environmental load.",
        )
        with st.expander("Fueling details", expanded=True):
            fluids = briefing_nut.get("fluids", {}) or {}
            carbs = briefing_nut.get("carbohydrates", {}) or {}
            sodium = briefing_nut.get("electrolytes", {}) or {}

            n1, n2, n3 = st.columns(3)
            with n1:
                metric_card(
                    "Fluids",
                    f"{fluids.get('total_liters', 'N/A')} L",
                    "💧",
                    "#38bdf8",
                    f"{fluids.get('hourly_average_ml', 'N/A')} ml/h",
                )
            with n2:
                metric_card(
                    "Carbs",
                    f"{carbs.get('total_grams', 'N/A')} g",
                    "🍌",
                    "#22c55e",
                    f"{carbs.get('hourly_target_g', 'N/A')} g/h",
                )
            with n3:
                metric_card(
                    "Sodium",
                    f"{sodium.get('total_sodium_mg', 'N/A')} mg",
                    "🧂",
                    "#f59e0b",
                    f"{sodium.get('hourly_sodium_mg', 'N/A')} mg/h",
                )

            tactical_advice = briefing_nut.get("tactical_advice", []) or []
            for advice in tactical_advice:
                st.info(advice)

    map_uri = res_data.get("map_path")
    alt_uri = res_data.get("elevation_profile_path")
    if map_uri or alt_uri:
        section_intro("Visuals", "Route map and elevation profile for tactical validation.")
        v1, v2 = st.columns(2)
        if map_uri:
            v1.image(map_uri, caption="Tactical map", use_container_width=True)
        if alt_uri:
            v2.image(alt_uri, caption="Elevation profile", use_container_width=True)

    gpx_path = res_data.get("gpx_export_path")
    if gpx_path and os.path.exists(gpx_path):
        dl_col, _ = st.columns([1, 5])
        with dl_col, open(gpx_path, "rb") as file:
            st.download_button(
                "Download GPX",
                file,
                file_name="mission.gpx",
                mime="application/gpx+xml",
                type="primary",
                use_container_width=True,
            )


def process_local_mcp_request(raw_llm_json: str, user_input: str):
    res_data = None
    briefing_text = "Analysis complete."
    had_visual_result = False

    with st.status("Executing analysis...", expanded=True) as status_box:
        try:
            clean_json_str = raw_llm_json.strip()
            if clean_json_str.startswith("```json"):
                clean_json_str = clean_json_str[7:-3].strip()
            elif clean_json_str.startswith("```"):
                clean_json_str = clean_json_str[3:-3].strip()

            data = json.loads(clean_json_str)
            briefing_text = data.get("briefing", "Analysis complete.")
            can_execute = data.get("can_execute", False)
            tool_data = data.get("tool") or {}

            if not can_execute or not tool_data:
                status_box.update(label="Completed", state="complete")
                return briefing_text, False

            tool_name = tool_data.get("name")
            args = tool_data.get("args") or {}

            parsed_distance = extract_distance_km_from_text(user_input)
            parsed_direction_bias = extract_direction_bias_from_text(user_input)
            parsed_avoid_urban = extract_avoid_urban_from_text(user_input)
            parsed_prefer_rural = extract_prefer_rural_from_text(user_input)
            parsed_flex_percent, parsed_priority_mode = extract_distance_flex_from_text(user_input)

            if parsed_distance is not None and not args.get("distance"):
                args["distance"] = parsed_distance

            if parsed_direction_bias and not args.get("direction_bias"):
                args["direction_bias"] = parsed_direction_bias

            if parsed_avoid_urban and "avoid_urban" not in args:
                args["avoid_urban"] = True

            if parsed_prefer_rural and "prefer_rural" not in args:
                args["prefer_rural"] = True

            if "distance_flex_percent" not in args:
                args["distance_flex_percent"] = parsed_flex_percent

            if parsed_priority_mode and not args.get("priority_mode"):
                args["priority_mode"] = parsed_priority_mode

            if tool_name != "trail_scout_simple":
                status_box.update(label="Completed", state="complete")
                return briefing_text, False

            route_mode = resolve_route_mode(args, user_input)
            dest_lat, dest_lon = None, None
            dest_display = None

            location_query = resolve_location_query(args, user_input)
            if not location_query:
                status_box.update(label="Geolocation failed", state="error")
                return "Please specify a starting location.", False

            geo = geocode_location(location_name=location_query)
            if getattr(geo, "status", None) != "Success":
                status_box.update(label="Geolocation failed", state="error")
                return f"Could not geocode: {location_query}", False

            if route_mode == "point_to_point":
                dest_name = args.get("destination_name") or (
                    st.session_state.get("mission_context") or {}
                ).get("destination_name")
                if not dest_name:
                    ab = extract_point_to_point(user_input)
                    if ab:
                        dest_name = ab[1]
                if not dest_name:
                    status_box.update(label="Missing destination", state="error")
                    return "Please specify both start and destination.", False

                geo_dest = geocode_location(location_name=dest_name)
                if getattr(geo_dest, "status", None) != "Success":
                    status_box.update(label="Destination geolocation failed", state="error")
                    return f"Could not geocode destination: {dest_name}", False

                dest_lat = float(geo_dest.lat)
                dest_lon = float(geo_dest.lon)
                dest_display = getattr(geo_dest, "display_name", dest_name)

            args["latitude"] = geo.lat
            args["longitude"] = geo.lon
            display_name = getattr(geo, "display_name", location_query)

            raw_distance = ext_cast(args.get("distance"), float, 25.0)
            if raw_distance and raw_distance > 1000:
                raw_distance = raw_distance / 1000

            args = apply_text_overrides(args, user_input)

            final_bike, is_ebike = normalize_bike_type(args.get("bike_type"))
            complexity_val = clamp_complexity(args.get("complexity", 3))
            args["complexity"] = complexity_val

            rider_profile = st.session_state["rider_profile"]
            normalized_tire_size = normalize_tire_size(
                args.get("tire_size") or rider_profile["tire_size"],
                final_bike,
            )
            setup_profile = dict(rider_profile)
            mission_context = st.session_state.get("mission_context") or {}
            for key in ("tire_width_mm", "rim_internal_width_mm", "casing_type", "tubeless"):
                if mission_context.get(key) is not None:
                    setup_profile[key] = mission_context[key]
            setup_args = _setup_args_from_request(args, setup_profile, final_bike)

            direction_bias = normalize_direction_bias(
                args.get("direction_bias")
                or (st.session_state.get("mission_context") or {}).get("direction_bias")
            )
            avoid_urban = bool(
                args.get(
                    "avoid_urban",
                    (st.session_state.get("mission_context") or {}).get("avoid_urban", False),
                )
            )
            prefer_rural = bool(
                args.get(
                    "prefer_rural",
                    (st.session_state.get("mission_context") or {}).get("prefer_rural", False),
                )
            )
            distance_flex_percent = max(
                0,
                min(
                    30,
                    ext_cast(
                        args.get(
                            "distance_flex_percent",
                            (st.session_state.get("mission_context") or {}).get(
                                "distance_flex_percent", 10
                            ),
                        ),
                        int,
                        10,
                    ),
                ),
            )
            priority_mode = (
                str(
                    args.get(
                        "priority_mode",
                        (st.session_state.get("mission_context") or {}).get(
                            "priority_mode", "balanced"
                        ),
                    )
                )
                .strip()
                .lower()
            )
            if priority_mode not in {"balanced", "distance_first", "ride_character_first"}:
                priority_mode = "balanced"

            _update_mission_context(
                display_name,
                geo.lat,
                geo.lon,
                {
                    **args,
                    "bike_type": final_bike,
                    "tire_size": normalized_tire_size,
                    **setup_args,
                    "direction_bias": direction_bias,
                    "avoid_urban": avoid_urban,
                    "prefer_rural": prefer_rural,
                    "distance_flex_percent": distance_flex_percent,
                    "priority_mode": priority_mode,
                },
                raw_distance if route_mode != "point_to_point" else 0,
                route_mode=route_mode,
                destination_name=dest_display if route_mode == "point_to_point" else None,
                dest_lat=dest_lat,
                dest_lon=dest_lon,
            )

            valid_args = {
                "latitude": float(cast(Any, args.get("latitude"))),
                "longitude": float(cast(Any, args.get("longitude"))),
                "tire_size": normalized_tire_size,
                **setup_args,
                "include_weather": True,
                "include_mud_analysis": (
                    wants_overlay(
                        user_input,
                        args.get("include_mud_analysis"),
                        ("mud", "muddy", "wet trail", "trail condition", "trail conditions"),
                    )
                    or (final_bike != "road" and args.get("include_mud_analysis") is not False)
                ),
                "include_nutrition_plan": wants_overlay(
                    user_input,
                    args.get("include_nutrition_plan"),
                    ("nutrition", "fueling", "hydration", "carbs", "electrolytes", "food", "snack"),
                ),
                "include_poi": wants_overlay(
                    user_input,
                    args.get("include_poi"),
                    ("poi", "amenities", "water", "bars", "places"),
                ),
                "include_gpx": wants_overlay(
                    user_input,
                    args.get("include_gpx"),
                    ("gpx", "track", "download", ".gpx"),
                ),
                "include_map": True,
                "include_altimetry": True,
                "weight_kg": ext_cast(args.get("weight_kg"), float, rider_profile["weight_kg"]),
                "gender": str(args.get("gender") or rider_profile["gender"]),
                "seed": random.randint(1, 999999),
                "complexity": difficulty_to_waypoints(complexity_val),
                "bike_type": final_bike,
                "profile": resolve_profile(final_bike),
                "is_ebike": is_ebike,
                "fitness_level": str(args.get("fitness_level") or rider_profile["fitness_level"]),
                "direction_bias": direction_bias,
                "avoid_urban": avoid_urban,
                "prefer_rural": prefer_rural,
                "distance_flex_percent": distance_flex_percent,
                "priority_mode": priority_mode,
            }

            if route_mode == "point_to_point":
                if dest_lat is None or dest_lon is None:
                    status_box.update(label="Missing destination coordinates", state="error")
                    return "Destination coordinates are missing for the A → B route.", False
                valid_args["dest_latitude"] = float(dest_lat)
                valid_args["dest_longitude"] = float(dest_lon)
                valid_args.pop("total_length_km", None)
            else:
                valid_args["total_length_km"] = raw_distance
                valid_args.pop("dest_latitude", None)
                valid_args.pop("dest_longitude", None)

            with st.expander("Engine debug", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Request**")
                    debug_args = dict(valid_args)
                    debug_args["route_mode"] = route_mode
                    debug_args["original_tire_size"] = args.get("tire_size")
                    debug_args["normalized_tire_size"] = normalized_tire_size
                    st.json(debug_args)
                with c2:
                    st.markdown("**LLM args**")
                    st.json(args)

            result = trail_scout_simple(**valid_args)
            res_data = cast(
                dict[str, Any],
                result.model_dump() if hasattr(result, "model_dump") else result,
            )

            with st.expander("Engine debug - Response", expanded=False):
                st.json(res_data)

            if not res_data or res_data.get("status") != "Success":
                status_box.update(label="Route planning failed", state="error")
                if route_mode == "point_to_point":
                    st.error(
                        "No valid A → B route matched the current parameters. Try adjusting start/destination or bike setup."
                    )
                else:
                    st.error(
                        "No route matched the current parameters. Try changing location, bike type, or distance."
                    )
                return "The system could not generate a route for this configuration.", False

            status_box.update(label="Analysis complete", state="complete")

        except Exception as e:
            status_box.update(label="Analysis interrupted", state="error")
            st.error("Something went wrong while planning the route.")
            with st.expander("Technical details"):
                st.code(f"{type(e).__name__}: {e}", language="text")
            return "Unable to complete route planning.", False

    if res_data:
        render_route_results(res_data)
        had_visual_result = True

    return briefing_text, had_visual_result


def render_plan_tab():
    section_intro(
        "Guided ride planning",
        "For users who prefer form-driven planning instead of free-form chat.",
    )
    rider = st.session_state["rider_profile"]

    route_mode = st.radio(
        "Route mode",
        options=["Circular / Loop", "A → B"],
        horizontal=True,
        key="guided_route_mode_selector",
    )

    if route_mode == "A → B":
        st.caption(
            "For point-to-point missions, the engine will compute the real route distance automatically."
        )

    with st.form("guided_plan_form"):
        top1, top2 = st.columns(2)

        with top1:
            bike_type = cast(
                str,
                st.selectbox(
                    "Bike type",
                    ["mtb", "road", "gravel", "e-mtb", "enduro"],
                    key="guided_bike_type",
                ),
            )
            complexity = st.slider(
                "Difficulty",
                min_value=1,
                max_value=5,
                value=3,
                key="guided_complexity",
            )

        with top2:
            available_tires = ["32", "29", "27.5", "700c", "650b"]
            rider_tire = rider["tire_size"] if rider["tire_size"] in available_tires else "29"
            tire_size = st.selectbox(
                "Tire size",
                available_tires,
                index=available_tires.index(rider_tire),
                key="guided_tire_size",
            )
            goal = cast(
                str,
                st.selectbox(
                    "Ride goal",
                    ["scenic", "training", "technical", "easy", "family"],
                    key="guided_goal",
                ),
            )

        rider_defaults = st.session_state.get("rider_profile", {})
        setup1, setup2, setup3, setup4 = st.columns(4)
        with setup1:
            guided_width = ext_cast(
                rider_defaults.get("tire_width_mm"),
                int,
                default_tire_width_mm(bike_type),
            )
            tire_width_mm = st.number_input(
                "Tire width (mm)",
                min_value=18,
                max_value=75,
                value=int(guided_width),
                key="guided_tire_width_mm",
            )
        with setup2:
            guided_rim = ext_cast(
                rider_defaults.get("rim_internal_width_mm"),
                int,
                default_rim_internal_width_mm(bike_type),
            )
            rim_internal_width_mm = st.number_input(
                "Rim internal (mm)",
                min_value=10,
                max_value=45,
                value=int(guided_rim),
                key="guided_rim_internal_width_mm",
            )
        with setup3:
            casing_options = ["xc", "trail", "enduro", "dh"]
            guided_casing = str(rider_defaults.get("casing_type") or default_casing_type(bike_type))
            if guided_casing not in casing_options:
                guided_casing = "trail"
            casing_type = st.selectbox(
                "Casing",
                casing_options,
                index=casing_options.index(guided_casing),
                key="guided_casing_type",
            )
        with setup4:
            tubeless = st.checkbox(
                "Tubeless setup",
                value=bool(rider_defaults.get("tubeless", True)),
                key="guided_tubeless",
            )

        loc1, loc2 = st.columns(2)
        with loc1:
            start_location = st.text_input(
                "Start location",
                placeholder="e.g. Trento, Italy",
                key="guided_start_location",
            )
        with loc2:
            if route_mode == "A → B":
                destination_location = st.text_input(
                    "Destination",
                    placeholder="e.g. Bolzano, Italy",
                    key="guided_destination",
                )
            else:
                destination_location = ""

        if route_mode == "Circular / Loop":
            distance = st.number_input(
                "Distance (km)",
                min_value=5.0,
                max_value=250.0,
                value=35.0,
                key="guided_distance",
            )
        else:
            st.info("Distance is computed automatically for A → B routes.")
            distance = None

        st.markdown("#### Route character")

        rc1, rc2 = st.columns(2)
        with rc1:
            direction_bias = st.multiselect(
                "Preferred direction",
                options=["north", "south", "east", "west"],
                default=[],
                help="Bias loop generation toward one or more directions relative to the start area.",
                key="guided_direction_bias",
            )
            avoid_urban = st.checkbox(
                "Avoid urban streets",
                value=False,
                help="Bias the route away from denser city sections when possible.",
                key="guided_avoid_urban",
            )

        with rc2:
            prefer_rural = st.checkbox(
                "Prefer countryside / quieter roads",
                value=False,
                help="Bias the route toward quieter, lower-density rural roads when possible.",
                key="guided_prefer_rural",
            )
            priority_mode = st.selectbox(
                "Priority mode",
                ["balanced", "distance_first", "ride_character_first"],
                index=0,
                help="Choose whether the engine should prioritize exact mileage or the qualitative character of the ride.",
                key="guided_priority_mode",
            )

        distance_flex_percent = st.slider(
            "Distance flexibility (%)",
            min_value=0,
            max_value=30,
            value=10,
            help="Allowed tolerance around target distance when the route character matters more than exact mileage.",
            key="guided_distance_flex_percent",
        )

        st.markdown("#### Options")
        o1, o2, o3 = st.columns(3)
        with o1:
            include_poi = st.checkbox("Amenities / POI", value=True, key="guided_poi")
            include_weather = st.checkbox("Weather", value=True, key="guided_weather")
        with o2:
            include_gpx = st.checkbox("GPX export", value=True, key="guided_gpx")
            include_mud = st.checkbox("Mud analysis", value=bike_type != "road", key="guided_mud")
        with o3:
            include_nutrition = st.checkbox("Nutrition plan", value=True, key="guided_nutrition")
            include_altimetry = st.checkbox("Altimetry", value=True, key="guided_altimetry")

        submitted = st.form_submit_button("Generate ride plan", type="primary")

    if submitted:
        if not start_location:
            st.error("Please enter a start location.")
            return
        if route_mode == "A → B" and not destination_location:
            st.error("Please enter a destination for the A → B route.")
            return

        goal_hint = {
            "scenic": "with scenic roads and nice views",
            "training": "optimized for training",
            "technical": "with more technical terrain",
            "easy": "easy and relaxed",
            "family": "safe and beginner friendly",
        }[goal]

        if route_mode == "Circular / Loop":
            prompt = (
                f"Plan a {distance} km {bike_type} circular loop near {start_location} "
                f"{goal_hint}, tire size {tire_size}, tire width {tire_width_mm}mm, "
                f"difficulty {complexity}. "
            )
        else:
            prompt = (
                f"Plan a {bike_type} route from {start_location} to {destination_location} "
                f"{goal_hint}, tire size {tire_size}, tire width {tire_width_mm}mm, "
                f"difficulty {complexity}. "
            )

        if direction_bias:
            if len(direction_bias) == 1:
                prompt += f"Keep it mostly to the {direction_bias[0]}. "
            else:
                prompt += f"Keep it mostly to the {' and '.join(direction_bias)}. "

        if avoid_urban:
            prompt += "Avoid urban streets. "

        if prefer_rural:
            prompt += "Prefer countryside or quieter roads. "

        if priority_mode == "distance_first":
            prompt += "Keep the route as close as possible to the requested distance. "
        elif priority_mode == "ride_character_first":
            prompt += "Prioritize the character of the ride over exact mileage. "
        else:
            prompt += "Balance route character and distance. "

        if distance_flex_percent == 0:
            prompt += "The distance should be exact if possible. "
        else:
            prompt += f"Allow about {distance_flex_percent}% flexibility on the target distance. "

        if include_poi:
            prompt += "Include POIs and amenities. "
        if include_weather:
            prompt += "Include weather. "
        if include_mud:
            prompt += "Include mud analysis. "
        if include_nutrition:
            prompt += "Include nutrition advice. "
        if include_gpx:
            prompt += "Include GPX export. "
        if include_altimetry:
            prompt += "Include altimetry. "

        plan_request = {
            "route_mode": "point_to_point" if route_mode == "A → B" else "loop",
            "start_location": start_location,
            "destination_location": destination_location if route_mode == "A → B" else None,
            "distance": float(distance) if distance is not None else None,
            "bike_type": bike_type,
            "tire_size": tire_size,
            "tire_width_mm": tire_width_mm,
            "rim_internal_width_mm": rim_internal_width_mm,
            "casing_type": casing_type,
            "tubeless": tubeless,
            "complexity": complexity,
            "goal": goal,
            "direction_bias": direction_bias,
            "avoid_urban": avoid_urban,
            "prefer_rural": prefer_rural,
            "distance_flex_percent": distance_flex_percent,
            "priority_mode": priority_mode,
            "include_poi": include_poi,
            "include_weather": include_weather,
            "include_mud": include_mud,
            "include_nutrition": include_nutrition,
            "include_gpx": include_gpx,
            "include_altimetry": include_altimetry,
        }

        st.session_state["pending_plan_request"] = plan_request
        st.session_state["pending_chat_prompt"] = prompt
        st.session_state["pending_chat_hidden"] = True
        st.session_state["pending_tab_redirect"] = "Chat Planner"
        st.rerun()


def render_gpx_tab():
    section_intro(
        "GPX tactical audit",
        "Analyze an existing GPX with rider metrics, weather planning, climbs, and performance simulation.",
    )
    st.caption(
        "Ideal for reviewing a route you already have before race day or a big weekend ride."
    )

    with st.form("gpx_audit_form"):
        gpx_url = st.text_input(
            "GPX source (URL or local path)",
            placeholder="https://.../route.gpx or /path/to/route.gpx",
        )

        st.markdown("#### Rider & bike setup")
        col1, col2, col3 = st.columns(3)
        with col1:
            activity_type = cast(Literal["road", "mtb"], st.selectbox("Type", ["road", "mtb"]))
            rider_gender = cast(
                Literal["male", "female"], st.selectbox("Gender", ["male", "female"])
            )
        with col2:
            rider_weight_kg = st.number_input(
                "Rider weight (kg)", min_value=40.0, max_value=130.0, value=75.0, step=0.5
            )
            bike_weight_kg = st.number_input(
                "Bike weight (kg)", min_value=5.0, max_value=30.0, value=8.5, step=0.1
            )
        with col3:
            rider_fitness_level = cast(
                Literal["beginner", "intermediate", "pro"],
                st.selectbox("Fitness level", ["beginner", "intermediate", "pro"], index=1),
            )
            pro_intensity = st.slider(
                "Intensity factor", min_value=1.0, max_value=2.0, value=1.3, step=0.1
            )

        st.markdown("#### Weather planning")
        col4, col5 = st.columns(2)
        with col4:
            sweat_profile = cast(
                Literal["low", "standard", "high", "extreme"],
                st.selectbox("Sweat profile", ["low", "standard", "high", "extreme"], index=1),
            )
        with col5:
            enable_date = st.checkbox("Schedule date/time")
            if enable_date:
                target_date = st.date_input("Target date", value=date.today())
                c_start, c_end = st.columns(2)
                with c_start:
                    start_hour = st.number_input("Start hour", min_value=0, max_value=23, value=8)
                with c_end:
                    end_hour = st.number_input("End hour", min_value=0, max_value=23, value=14)
            else:
                target_date, start_hour, end_hour = None, None, None

        report = st.toggle("Generate PDF report", value=False)
        submitted = st.form_submit_button("Run GPX analysis", type="primary")

    if submitted:
        if not gpx_url:
            st.error("The GPX source is required.")
            return

        with st.spinner("Analyzing GPX track..."):
            try:
                str_target_date = target_date.strftime("%Y-%m-%d") if target_date else None
                result = analyze_gpx_track(
                    gpx_url=gpx_url,
                    rider_weight_kg=rider_weight_kg,
                    rider_gender=rider_gender,
                    rider_fitness_level=rider_fitness_level,
                    sweat_profile=sweat_profile,
                    bike_weight_kg=bike_weight_kg,
                    pro_intensity=pro_intensity,
                    activity_type=activity_type,
                    target_date=str_target_date,
                    start_hour=start_hour,
                    end_hour=end_hour,
                    report=report,
                )

                res_data = cast(
                    dict[str, Any],
                    result.model_dump() if hasattr(result, "model_dump") else result,
                )
                st.success("GPX analysis completed.")

                track_metrics = res_data.get("track_metrics", {})
                if track_metrics:
                    g1, g2, g3 = st.columns(3)
                    with g1:
                        metric_card(
                            "Distance", f"{track_metrics.get('distance_km')} km", "📏", "#38bdf8"
                        )
                    with g2:
                        metric_card(
                            "Elevation gain",
                            f"+{track_metrics.get('total_ascent')} m",
                            "⛰️",
                            "#a78bfa",
                        )
                    with g3:
                        metric_card(
                            "Max altitude", f"{track_metrics.get('max_altitude')} m", "🏔️", "#22c55e"
                        )

                planning = res_data.get("planning_tools", {})
                weather = planning.get("weather_forecast", {})
                if weather:
                    with st.expander("Weather forecast", expanded=True):
                        advice = weather.get("safety_advice", {})
                        if advice:
                            st.info(
                                f"**{advice.get('status', 'Safety')}** — {advice.get('message', '')}"
                            )

                climbs = res_data.get("climb_analysis", [])
                if climbs:
                    with st.expander("Climb analysis"):
                        climb_df = []
                        for c in climbs:
                            climb_df.append(
                                {
                                    "Start (km)": c["km_start"],
                                    "Length (km)": c["dist_km"],
                                    "Grade (%)": c["avg_grade"],
                                    "Cat": c["category"],
                                }
                            )
                        st.table(climb_df)

                sims = res_data.get("performance_simulation", [])
                if sims:
                    with st.expander("Performance simulation"):
                        sim_df = []
                        for s in sims:
                            sim_df.append(
                                {
                                    "Sector": s["climb"].split("@")[0].strip(),
                                    "VAM": s["est_vam"],
                                    "W/kg": s["target_wkg"],
                                    "Time (min)": s["est_time_min"],
                                }
                            )
                        st.dataframe(sim_df, hide_index=True)

                report_path = res_data.get("report_path")
                if report_path and os.path.exists(report_path):
                    with open(report_path, "rb") as file:
                        st.download_button(
                            label="Download tactical PDF report",
                            data=file,
                            file_name=os.path.basename(report_path),
                            mime="application/pdf",
                            type="primary",
                        )

            except Exception as e:
                st.error(f"Error while parsing GPX: {e}")


def main():
    init_session_state()
    inject_global_styles()
    inject_component_styles()

    selected_model_name, n_layers = render_sidebar()
    llm = (
        load_llm(selected_model_name, n_layers)
        if os.path.exists(get_local_model_path(selected_model_name))
        else None
    )

    render_rider_profile_panel()

    tab_options = ["Plan a Ride", "Chat Planner", "GPX Audit"]

    redirect_tab = st.session_state.get("pending_tab_redirect")
    if redirect_tab in tab_options:
        st.session_state["workspace_tab_selector"] = redirect_tab
        st.session_state["current_tab"] = redirect_tab
        st.session_state["pending_tab_redirect"] = None

    current_tab = st.radio(
        "Workspace",
        tab_options,
        horizontal=True,
        key="workspace_tab_selector",
        label_visibility="collapsed",
    )

    st.session_state["current_tab"] = current_tab

    if current_tab == "Plan a Ride":
        render_plan_tab()
    elif current_tab == "Chat Planner":
        render_chat_tab(llm)
    else:
        render_gpx_tab()


if __name__ == "__main__":
    main()
