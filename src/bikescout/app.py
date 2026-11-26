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

from bikescout.app_helpers import (
    append_mission_summary,
    apply_text_overrides,
    clamp_complexity,
    difficulty_to_waypoints,
    ext_cast,
    extract_avoid_urban_from_text,
    extract_direction_bias_from_text,
    extract_distance_flex_from_text,
    extract_distance_km_from_text,
    extract_point_to_point,
    extract_prefer_rural_from_text,
    init_session_state,
    normalize_bike_type,
    normalize_direction_bias,
    normalize_tire_size,
    resolve_location_query,
    resolve_profile,
    resolve_route_mode,
    setup_args_from_request,
    update_mission_context,
    wants_overlay,
)
from bikescout.app_llm import (
    LlamaChatModel,
    generate_tactical_response,
    get_local_model_path,
    load_llm,
)
from bikescout.app_ui_helpers import (
    inject_component_styles,
    inject_global_styles,
    metric_card,
    render_empty_state,
    render_route_results,
    render_rider_profile_fields,
    reset_climb_profile_state,
    render_sidebar,
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


st.set_page_config(
    page_title="BikeScout",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _execute_and_store_request(plan_request: dict) -> None:
    with st.chat_message("assistant"):
        assistant_text, had_visual_result = execute_plan_request(plan_request)
        if not had_visual_result:
            st.markdown(assistant_text)

    stored_text = assistant_text
    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": append_mission_summary(stored_text),
        }
    )


def render_chat_tab(llm: LlamaChatModel | None) -> None:
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
            "content": append_mission_summary(assistant_text),
        }
    )


def execute_plan_request(plan_request: dict) -> tuple[str, bool]:
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

        setup_args = setup_args_from_request(plan_request, rider_profile, final_bike)
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

        update_mission_context(
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

        reset_climb_profile_state()
        render_route_results(res_data)
        return "Mission generated successfully.", True

    except Exception as e:
        st.error("Something went wrong while planning the route.")
        with st.expander("Technical details"):
            st.code(f"{type(e).__name__}: {e}", language="text")
        return "Unable to complete route planning.", False


def process_local_mcp_request(raw_llm_json: str, user_input: str) -> tuple[str, bool]:
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
            setup_args = setup_args_from_request(args, setup_profile, final_bike)

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

            update_mission_context(
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
        reset_climb_profile_state()
        render_route_results(res_data)
        had_visual_result = True

    return briefing_text, had_visual_result


def render_plan_tab() -> None:
    section_intro(
        "Guided ride planning",
        "For users who prefer form-driven planning instead of free-form chat.",
    )
    render_rider_profile_fields()
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


def render_gpx_tab() -> None:
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


def main() -> None:
    init_session_state()
    inject_global_styles()
    inject_component_styles()

    selected_model_name, n_layers = render_sidebar()
    llm = (
        load_llm(selected_model_name, n_layers)
        if os.path.exists(get_local_model_path(selected_model_name))
        else None
    )

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
