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

import json
import os
import random
import re
from datetime import date

import streamlit as st
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

from bikescout.domain_logic import (
    build_mission_snapshot,
    clamp_complexity,
    ext_cast,
    extract_location_hint,
    extract_point_to_point,
    normalize_bike_type,
    normalize_tire_size,
    resolve_profile,
    resolve_route_mode,
    summarize_mission,
    wants_overlay,
)
from bikescout.ui_helpers import inject_global_styles, render_empty_state

try:
    from bikescout.mcp_server import (
        analyze_gpx_track,
        geocode_location,
        trail_scout_simple,
    )
    server_loaded = True
except SystemExit:
    server_loaded = False
except ImportError:
    server_loaded = False

AVAILABLE_MODELS = {
    "Llama-3-8B": {
        "repo": "MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF",
        "file": "Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf",
        "description": "",
    },
    "Llama-3.1-8B-Instruct": {
        "repo": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "file": "Meta-Llama-3.1-8B-Instruct-Q6_K.gguf",
        "description": "",
    },
}

LOCAL_MODELS_DIR = "models"

st.set_page_config(
    page_title="BikeScout",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
            "fitness_level": "intermediate",
            "weight_kg": 75.0,
            "gender": "male",
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def inject_premium_component_styles() -> None:
    st.markdown(
        """
        <style>
        
        .bs-sidebar-brand {
            display: flex;
            align-items: baseline;
            gap: 0.18rem;
            margin-bottom: 0.35rem;
            line-height: 1;
        }
    
        .bs-sidebar-bike {
            font-size: 1.35rem;
            font-weight: 900;
            font-style: italic;
            text-transform: uppercase;
            letter-spacing: -0.06em;
            color: #ffffff;
        }
        
        .bs-sidebar-scout {
            font-size: 1.35rem;
            font-weight: 900;
            font-style: italic;
            text-transform: uppercase;
            letter-spacing: -0.04em;
            color: #4ade80;
            text-shadow:
                0 0 6px rgba(74, 222, 128, 0.75),
                0 0 12px rgba(34, 197, 94, 0.60),
                0 0 20px rgba(22, 163, 74, 0.50);
        }
        
        .bs-grid-gap { margin-top: 0.35rem; }

        .bs-panel {
            background: rgba(20, 27, 52, 0.78);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 20px;
            padding: 18px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.24);
            margin-bottom: 14px;
        }

        .bs-panel-title {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #a5b4fc;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .bs-section {
            margin-top: 16px;
            margin-bottom: 10px;
        }

        .bs-section h3 {
            margin: 0 0 8px 0 !important;
            font-size: 1.12rem !important;
            font-weight: 800 !important;
        }

        .bs-section p {
            color: #aeb8d0 !important;
            margin: 0 !important;
        }

        .bs-metric-card {
            position: relative;
            overflow: hidden;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.82), rgba(15, 23, 42, 0.9));
            padding: 16px;
            min-height: 110px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.22);
        }

        .bs-metric-card::after {
            content: "";
            position: absolute;
            inset: 0 auto auto 0;
            width: 100%;
            height: 4px;
            background: var(--accent, #7c3aed);
            opacity: 0.95;
        }

        .bs-metric-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }

        .bs-metric-label {
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #9fb0d1;
            font-weight: 800;
        }

        .bs-metric-icon {
            font-size: 1.1rem;
            opacity: 0.95;
        }

        .bs-metric-value {
            margin-top: 12px;
            font-size: 1.7rem;
            font-weight: 900;
            line-height: 1.05;
            color: #f8fbff;
        }

        .bs-metric-sub {
            margin-top: 8px;
            font-size: 0.86rem;
            color: #aeb8d0;
        }

        .bs-score-card {
            border-radius: 22px;
            padding: 20px;
            background:
                radial-gradient(circle at top left, rgba(124,58,237,0.25), transparent 35%),
                linear-gradient(135deg, rgba(30,41,59,0.92), rgba(15,23,42,0.98));
            border: 1px solid rgba(148, 163, 184, 0.16);
            box-shadow: 0 12px 40px rgba(0,0,0,0.26);
        }

        .bs-score-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #c4b5fd;
            font-weight: 800;
        }

        .bs-score-value {
            font-size: 3rem;
            font-weight: 900;
            margin-top: 8px;
            line-height: 1;
        }

        .bs-score-sub {
            margin-top: 8px;
            font-size: 0.95rem;
            color: #cbd5e1;
        }

        .bs-badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }

        .bs-badge {
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.78rem;
            font-weight: 700;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(255,255,255,0.06);
        }

        .bs-badge.safe { color: #86efac; }
        .bs-badge.warn { color: #fde68a; }
        .bs-badge.risk { color: #fca5a5; }
        .bs-badge.info { color: #93c5fd; }

        .bs-mini-kpi {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 16px;
            padding: 12px 14px;
            min-height: 84px;
        }

        .bs-mini-kpi .k-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #9fb0d1;
            font-weight: 800;
        }

        .bs-mini-kpi .k-value {
            margin-top: 8px;
            font-size: 1.15rem;
            font-weight: 800;
            color: #f8fbff;
        }

        .bs-poi-card {
            background: linear-gradient(180deg, rgba(30,41,59,0.78), rgba(15,23,42,0.9));
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-left: 4px solid var(--poi-accent, #38bdf8);
            border-radius: 16px;
            padding: 14px 14px 12px 14px;
            min-height: 140px;
            box-shadow: 0 8px 28px rgba(0,0,0,0.18);
        }

        .bs-poi-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
        }

        .bs-poi-title {
            font-size: 0.98rem;
            font-weight: 800;
            line-height: 1.25;
        }

        .bs-poi-type {
            margin-top: 4px;
            color: #9fb0d1;
            font-size: 0.82rem;
        }

        .bs-poi-distance {
            margin-top: 10px;
            font-size: 0.86rem;
            font-weight: 800;
            color: var(--poi-accent, #38bdf8);
        }

        .bs-poi-actions {
            margin-top: 12px;
            font-size: 0.84rem;
        }

        .bs-risk-box {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 16px;
            padding: 14px;
            min-height: 120px;
        }

        .bs-risk-title {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #9fb0d1;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .bs-risk-value {
            font-size: 1.1rem;
            font-weight: 800;
            margin-bottom: 6px;
        }

        .bs-risk-copy {
            color: #cbd5e1;
            font-size: 0.9rem;
            line-height: 1.45;
        }

        .bs-weather-strip {
            display: flex;
            gap: 10px;
            overflow-x: auto;
            padding-bottom: 4px;
        }

        .bs-weather-tile {
            min-width: 128px;
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(255,255,255,0.04);
            padding: 12px;
        }

        .bs-weather-time {
            font-size: 0.78rem;
            color: #9fb0d1;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .bs-weather-temp {
            margin-top: 10px;
            font-size: 1.3rem;
            font-weight: 900;
        }

        .bs-weather-meta {
            margin-top: 6px;
            font-size: 0.84rem;
            color: #cbd5e1;
            line-height: 1.45;
        }

        .bs-surface-row {
            margin-bottom: 12px;
        }

        .bs-callout {
            border-radius: 18px;
            padding: 16px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: linear-gradient(135deg, rgba(34,197,94,0.08), rgba(56,189,248,0.06));
        }

        .bs-callout strong {
            display: block;
            margin-bottom: 6px;
        }
        
        .bs-hud {
            margin: 0.4rem 0 1rem 0;
            padding: 0.9rem 1rem;
            border-radius: 18px;
            background:
                linear-gradient(135deg, rgba(17, 24, 39, 0.92), rgba(15, 23, 42, 0.88)),
                radial-gradient(circle at top right, rgba(34, 197, 94, 0.10), transparent 35%);
            border: 1px solid rgba(148, 163, 184, 0.14);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
        }
        
        .bs-hud-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.7rem;
        }
        
        .bs-hud-kicker {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #86efac;
            font-weight: 800;
            margin-bottom: 0.18rem;
        }
        
        .bs-hud-title {
            font-size: 1.15rem;
            font-weight: 900;
            font-style: italic;
            letter-spacing: -0.03em;
            color: #ffffff;
        }
        
        .bs-hud-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
            gap: 0.55rem;
        }
        
        .bs-hud-chip {
            padding: 0.55rem 0.7rem;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(148, 163, 184, 0.10);
        }
        
        .bs-hud-chip span {
            display: block;
            font-size: 0.64rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            margin-bottom: 0.15rem;
        }
        
        .bs-hud-chip strong {
            display: block;
            font-size: 0.92rem;
            font-weight: 800;
            color: #f8fafc;
        }
        
        .bs-hud {
            margin: 0.1rem 0 1rem 0;
            padding: 0.9rem 1rem;
            border-radius: 18px;
            background:
                linear-gradient(135deg, rgba(17, 24, 39, 0.92), rgba(15, 23, 42, 0.88)),
                radial-gradient(circle at top right, rgba(34, 197, 94, 0.10), transparent 35%);
            border: 1px solid rgba(148, 163, 184, 0.14);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
        }
        
        .bs-hud-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.7rem;
        }
        
        .bs-hud-kicker {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #86efac;
            font-weight: 800;
            margin-bottom: 0.18rem;
        }
        
        .bs-hud-title {
            font-size: 1.15rem;
            font-weight: 900;
            font-style: italic;
            letter-spacing: -0.03em;
            color: #ffffff;
        }
        
        .bs-hud-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
            gap: 0.55rem;
        }
        
        .bs-hud-chip {
            padding: 0.55rem 0.7rem;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(148, 163, 184, 0.10);
        }
        
        .bs-hud-chip span {
            display: block;
            font-size: 0.64rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            margin-bottom: 0.15rem;
        }
        
        .bs-hud-chip strong {
            display: block;
            font-size: 0.92rem;
            font-weight: 800;
            color: #f8fafc;
        }
        
        .bs-intensity-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.55rem 0.9rem;
            border-radius: 999px;
            background: color-mix(in srgb, var(--badge-color) 16%, rgba(15, 23, 42, 0.92));
            border: 1px solid color-mix(in srgb, var(--badge-color) 45%, rgba(255, 255, 255, 0.10));
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
            margin-bottom: 0.75rem;
        }
        
        .bs-intensity-dot {
            width: 0.6rem;
            height: 0.6rem;
            border-radius: 999px;
            background: var(--badge-color);
            box-shadow: 0 0 12px var(--badge-color);
            display: inline-block;
        }
        
        .bs-intensity-label {
            font-size: 0.78rem;
            font-weight: 900;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: #f8fafc;
        }
        
        .bs-warning-ribbon {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 1rem;
        }
        
        .bs-warning-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.45rem 0.7rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            color: #f8fafc;
            background: color-mix(in srgb, var(--chip-color) 14%, rgba(15, 23, 42, 0.92));
            border: 1px solid color-mix(in srgb, var(--chip-color) 38%, rgba(255, 255, 255, 0.10));
            line-height: 1;
        }
        
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_local_model_path(model_name: str) -> str:
    return os.path.join(LOCAL_MODELS_DIR, AVAILABLE_MODELS[model_name]["file"])


@st.cache_resource
def load_llm(model_name: str, n_gpu_layers: int):
    path = get_local_model_path(model_name)
    if not os.path.exists(path):
        return None

    return Llama(
        model_path=path,
        n_ctx=8192,
        n_gpu_layers=n_gpu_layers,
        verbose=False,
    )

def generate_tactical_response(messages_history: list, llm_instance: Llama, mission_context: dict | None = None) -> str:
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
                                        "complexity": {"type": "integer", "minimum": 1, "maximum": 5},
                                        "profile": {
                                            "type": "string",
                                            "enum": ["cycling-mountain", "cycling-road", "cycling-electric"],
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
                                            "enum": ["balanced", "distance_first", "ride_character_first"],
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

Routing preference extraction rules:
- If the user asks to stay south, north, east, or west of the start area, set direction_bias accordingly.
- If the user asks for south-east, south and east, or similar, set direction_bias to multiple values, e.g. ["south", "east"].
- If the user asks to avoid the city, avoid urban streets, or avoid traffic-heavy urban riding, set avoid_urban=true.
- If the user asks for countryside, quieter roads, open country, rural roads, or scenic non-urban riding, set prefer_rural=true.
- If the user cares more about the ride character than exact distance, set priority_mode="ride_character_first".
- If the user explicitly wants the route as close as possible to the requested distance, set priority_mode="distance_first".
- Otherwise use priority_mode="balanced".
- If the user allows some tolerance on distance, set distance_flex_percent between 10 and 20 depending on wording.
- If the user strongly prioritizes exact target distance, set distance_flex_percent=0.
- If no directional or routing preference is mentioned, omit these fields or preserve them from active mission context.

Examples:
- "keep it south and east of town" -> direction_bias ["south", "east"]
- "avoid the city and prefer countryside roads" -> avoid_urban true, prefer_rural true
- "about 60 km, doesn't have to be exact" -> distance_flex_percent 10 or 15, priority_mode "balanced"
- "the vibe matters more than exact mileage" -> priority_mode "ride_character_first"
- "make it exactly 60 km if possible" -> priority_mode "distance_first", distance_flex_percent 0

{mission_block}
"""

    formatted_messages = [{"role": "system", "content": system_prompt}]
    llm_history = [
        m for m in messages_history
        if m.get("role") == "user"
           or (m.get("role") == "assistant" and m.get("content") != "Connection established. Provide input...")
    ]
    formatted_messages.extend(llm_history[-6:])

    response = llm_instance.create_chat_completion(
        messages=formatted_messages,
        response_format=json_schema,
        temperature=0.0,
        max_tokens=512,
    )
    return response["choices"][0]["message"]["content"].strip()


def resolve_location_query(args: dict, user_input: str) -> str | None:
    return (
            args.get("location_name")
            or st.session_state.get("last_location_query")
            or extract_location_hint(user_input)
            or (st.session_state.get("mission_context") or {}).get("location_name")
    )


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


def metric_card(label: str, value: str, icon: str, accent: str, sub: str = "") -> None:
    st.markdown(
        f"""
        <div class="bs-metric-card" style="--accent:{accent};">
            <div class="bs-metric-top">
                <div class="bs-metric-label">{label}</div>
                <div class="bs-metric-icon">{icon}</div>
            </div>
            <div class="bs-metric-value">{value}</div>
            <div class="bs-metric-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_intro(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="bs-section">
            <h3>{title}</h3>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mini_kpi(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="bs-mini-kpi">
            <div class="k-label">{label}</div>
            <div class="k-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_status_panel(selected_model_name: str) -> None:
    ors_active = bool(st.session_state.get("ors_api_key") or os.getenv("ORS_API_KEY"))

    st.markdown('<div class="bs-panel-title">System status</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        mini_kpi("Engine", "Loaded" if server_loaded else "Missing")
    with c2:
        mini_kpi("ORS", "Configured" if ors_active else "Missing")
    with c3:
        mini_kpi("Model", selected_model_name)
    st.markdown("</div>", unsafe_allow_html=True)

def render_home_dashboard(selected_model_name: str) -> None:
    render_status_panel(selected_model_name)

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
        selected_model_name = st.selectbox("Model", list(AVAILABLE_MODELS.keys()))
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
                        local_dir_use_symlinks=False,
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

def render_quick_presets():
    st.markdown("#### Quick presets")
    c1, c2, c3 = st.columns(3)

    selected_request = None

    with c1:
        if st.button("Quick gravel", use_container_width=True):
            selected_request = {
                "route_mode": "loop",
                "start_location": "Trento, Italy",
                "destination_location": None,
                "distance": 35.0,
                "bike_type": "gravel",
                "tire_size": "700c",
                "complexity": 3,
                "goal": "scenic",
                "include_poi": True,
                "include_weather": True,
                "include_mud": True,
                "include_nutrition": False,
                "include_gpx": False,
                "include_altimetry": True,
                "ui_label": "Gravel Loop near Trento",
            }

    with c2:
        if st.button("Quick road", use_container_width=True):
            selected_request = {
                "route_mode": "loop",
                "start_location": "Verona, Italy",
                "destination_location": None,
                "distance": 50.0,
                "bike_type": "road",
                "tire_size": "700c",
                "complexity": 3,
                "goal": "training",
                "include_poi": True,
                "include_weather": True,
                "include_mud": False,
                "include_nutrition": True,
                "include_gpx": False,
                "include_altimetry": True,
                "ui_label": "Road Training Loop near Verona",
            }

    with c3:
        if st.button("Quick MTB", use_container_width=True):
            selected_request = {
                "route_mode": "loop",
                "start_location": "Bergamo, Italy",
                "destination_location": None,
                "distance": 28.0,
                "bike_type": "mtb",
                "tire_size": "29",
                "complexity": 4,
                "goal": "technical",
                "include_poi": False,
                "include_weather": True,
                "include_mud": True,
                "include_nutrition": False,
                "include_gpx": False,
                "include_altimetry": True,
                "ui_label": "MTB Technical Loop near Bergamo",
            }

    return selected_request

def render_mission_hud(
        title: str,
        bike_type: str,
        route_mode: str,
        distance_km: float | None = None,
        elevation_m: float | None = None,
        eta_text: str | None = None,
        weather_text: str | None = None,
        surface_text: str | None = None,
) -> None:
    chips = []

    if distance_km is not None:
        chips.append(f'<div class="bs-hud-chip"><span>Distance</span><strong>{distance_km:.1f} km</strong></div>')
    if elevation_m is not None:
        chips.append(f'<div class="bs-hud-chip"><span>Elevation</span><strong>{int(elevation_m)} m</strong></div>')
    if eta_text:
        chips.append(f'<div class="bs-hud-chip"><span>ETA</span><strong>{eta_text}</strong></div>')
    if weather_text:
        chips.append(f'<div class="bs-hud-chip"><span>Weather</span><strong>{weather_text}</strong></div>')
    if surface_text:
        chips.append(f'<div class="bs-hud-chip"><span>Surface</span><strong>{surface_text}</strong></div>')

    st.markdown(
        f"""
        <div class="bs-hud">
            <div class="bs-hud-top">
                <div class="bs-hud-title-wrap">
                    <div class="bs-hud-kicker">{bike_type.upper()} · {route_mode.upper()}</div>
                    <div class="bs-hud-title">{title}</div>
                </div>
            </div>
            <div class="bs-hud-grid">
                {''.join(chips)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_mission_intensity_badge(label: str, color: str) -> None:
    html = f"""
    <div class="bs-intensity-badge" style="--badge-color:{color};">
        <span class="bs-intensity-dot"></span>
        <span class="bs-intensity-label">{label}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_warning_ribbon(warnings: list[tuple[str, str]]) -> None:
    if not warnings:
        return

    chips_html = "".join(
        f'<div class="bs-warning-chip" style="--chip-color:{color};">{text}</div>'
        for text, color in warnings
    )

    html = f"""
    <div class="bs-warning-ribbon">
        {chips_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_chat_tab(llm):
    section_intro(
        "AI Ride Planner",
        "Chat with BikeScout to generate route plans, tactical overlays, logistics, and exports.",
    )

    preset_request = render_quick_presets()

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

    if preset_request:
        st.info("Quick preset selected. Running route analysis...")
        with st.chat_message("assistant"):
            assistant_text, had_visual_result = execute_plan_request(preset_request)
            if not had_visual_result:
                st.markdown(assistant_text)

        ctx = st.session_state.get("mission_context") or {}
        location_note = f"\n\n[{summarize_mission(ctx)}]" if ctx else ""
        summary_text = preset_request.get("ui_label") or assistant_text

        st.session_state["messages"].append(
            {"role": "assistant", "content": summary_text + location_note}
        )
        return

    if pending_plan_request:
        st.session_state["pending_plan_request"] = None
        st.session_state["pending_chat_prompt"] = None
        st.session_state["pending_chat_hidden"] = False

        st.info("Mission received from Plan a Ride. Running route analysis...")

        with st.chat_message("assistant"):
            assistant_text, had_visual_result = execute_plan_request(pending_plan_request)
            if not had_visual_result:
                st.markdown(assistant_text)

        ctx = st.session_state.get("mission_context") or {}
        location_note = f"\n\n[{summarize_mission(ctx)}]" if ctx else ""
        st.session_state["messages"].append(
            {"role": "assistant", "content": assistant_text + location_note}
        )
        return

    user_input = manual_input
    if not user_input:
        return

    if llm is None:
        with st.chat_message("assistant"):
            st.error("Local model not available. Download a model from the sidebar first.")
        return

    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    llm_messages = list(st.session_state["messages"])

    with st.chat_message("assistant"):
        raw_output = generate_tactical_response(
            llm_messages,
            llm,
            mission_context=st.session_state.get("mission_context"),
        )
        final_briefing, had_visual_result = process_local_mcp_request(raw_output, user_input)
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

    ctx = st.session_state.get("mission_context") or {}
    location_note = f"\n\n[{summarize_mission(ctx)}]" if ctx else ""

    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": assistant_text + location_note,
        }
    )

def _normalize_direction_bias(value) -> list[str]:
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

def execute_plan_request(plan_request: dict):
    if not plan_request:
        return "No plan request found.", False

    try:
        rider_profile = st.session_state["rider_profile"]

        route_mode = plan_request.get("route_mode", "loop")
        start_location = plan_request.get("start_location")
        destination_location = plan_request.get("destination_location")
        bike_type = plan_request.get("bike_type", rider_profile["bike_type"])
        final_bike, is_ebike = normalize_bike_type(bike_type)

        tire_size = normalize_tire_size(
            plan_request.get("tire_size") or rider_profile["tire_size"],
            final_bike,
            )

        complexity_val = clamp_complexity(plan_request.get("complexity", 3))
        raw_distance = ext_cast(plan_request.get("distance"), float, 25.0)

        direction_bias = _normalize_direction_bias(plan_request.get("direction_bias"))
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
            getattr(geo, "display_name", start_location),
            geo.lat,
            geo.lon,
            {
                "bike_type": final_bike,
                "tire_size": tire_size,
                "complexity": complexity_val,
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
            "complexity": complexity_val,
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
            valid_args["dest_latitude"] = float(dest_lat)
            valid_args["dest_longitude"] = float(dest_lon)
        else:
            valid_args["total_length_km"] = raw_distance

        with st.expander("Engine debug", expanded=False):
            st.json(valid_args)

        result = trail_scout_simple(**valid_args)
        res_data = result.model_dump() if hasattr(result, "model_dump") else result

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

def compute_readiness_score(info: dict, conditions: dict, logistics: dict) -> tuple[int, str, list[str]]:
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


def build_warning_ribbon(info: dict, conditions: dict, logistics: dict) -> list[tuple[str, str]]:
    warnings = []

    safety = conditions.get("safety_advice", {}) or {}
    wind_risk = ext_cast(safety.get("wind_risk_score"), float, 0)
    if wind_risk >= 7:
        warnings.append(("High wind exposure", "#f59e0b"))
    elif wind_risk >= 4:
        warnings.append(("Moderate wind exposure", "#fbbf24"))

    mud_data = conditions.get("mud_risk", {}) or {}
    tactical_mud = mud_data.get("tactical_analysis", {}) or {}
    mud_level = str(tactical_mud.get("mud_risk_score", "")).lower()
    if "high" in mud_level:
        warnings.append(("High mud risk", "#8b5cf6"))
    elif "medium" in mud_level:
        warnings.append(("Moderate mud risk", "#a78bfa"))

    ascent = ext_cast(info.get("ascent_m"), float, 0)
    if ascent >= 1800:
        warnings.append(("Major climbing load", "#fb7185"))
    elif ascent >= 900:
        warnings.append(("Sustained climbing", "#f97316"))

    pois = logistics.get("nearby_amenities", {}) or []
    if isinstance(pois, list) and len(pois) <= 2:
        warnings.append(("Limited support coverage", "#38bdf8"))

    nutrition = logistics.get("nutrition_plan", {}) or {}
    if nutrition:
        briefing_nut = nutrition.get("mission_nutrition_briefing", {}) or {}
        fluids = briefing_nut.get("fluids", {}) or {}
        total_liters = ext_cast(fluids.get("total_liters"), float, 0)
        if total_liters >= 2.5:
            warnings.append(("High hydration demand", "#06b6d4"))

    surface_analysis = info.get("surface_analysis", {}) or {}
    mechanical = surface_analysis.get("mechanical_setup", {}) or {}
    if mechanical and not mechanical.get("compatible", True):
        warnings.append(("Bike setup mismatch", "#ef4444"))

    return warnings[:5]


def render_weather_tiles_native(weather_data) -> None:
    if not weather_data:
        return

    rows = [weather_data[i:i + 5] for i in range(0, len(weather_data), 5)]

    for row in rows:
        cols = st.columns(len(row))
        for idx, w in enumerate(row):
            with cols[idx]:
                time_label = str(w.get("time", "Time"))
                temp_raw = str(w.get("temp", "N/A"))
                app_raw = str(w.get("app_temp", "N/A"))
                rain_raw = str(w.get("rain_prob", "N/A"))
                wind_raw = str(w.get("wind", w.get("wind_speed", "N/A")))

                st.markdown(
                    f"""
                    <div class="bs-risk-box">
                        <div class="bs-risk-title">{time_label}</div>
                        <div class="bs-risk-value">{temp_raw}</div>
                        <div class="bs-risk-copy">
                            Apparent: {app_raw}<br/>
                            Rain: {rain_raw}<br/>
                            Wind: {wind_raw}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

def render_score_card(score: int, status: str, badges: list[str]) -> None:
    color = "#22c55e" if status == "Go" else "#f59e0b" if status == "Caution" else "#ef4444"
    st.markdown(
        f"""
        <div class="bs-score-card">
            <div class="bs-score-label">Ride readiness score</div>
            <div class="bs-score-value" style="color:{color};">{score}/100</div>
            <div class="bs-score-sub">Decision: <strong>{status}</strong></div>
            <div class="bs-badge-row">
                {''.join([f'<div class="bs-badge {"safe" if status=="Go" else "warn" if status=="Caution" else "risk"}">{b}</div>' for b in badges[:5]])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_surface_icon(surface_type: str) -> str:
    s = surface_type.lower()
    if "asphalt" in s or "tarmac" in s or "paved" in s:
        return "🛣️"
    if "gravel" in s or "sterrato" in s:
        return "🪨"
    if "dirt" in s or "trail" in s or "singletrack" in s:
        return "🌲"
    if "mud" in s:
        return "🟤"
    if "sand" in s:
        return "🏖️"
    return "🗺️"


def get_poi_style(poi_type: str) -> tuple[str, str]:
    t = poi_type.lower()
    if "water" in t or "fontan" in t or "drink" in t:
        return "💧", "#38bdf8"
    if "shop" in t or "repair" in t or "bike" in t or "meccan" in t:
        return "🔧", "#f59e0b"
    if "food" in t or "restaur" in t or "bar" in t or "caf" in t:
        return "☕", "#22c55e"
    if "shelter" in t or "hotel" in t or "camp" in t:
        return "🏠", "#a78bfa"
    if "hospital" in t or "first aid" in t or "med" in t:
        return "🚨", "#ef4444"
    return "📍", "#94a3b8"


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
        section_intro("Terrain intelligence", "Surface mix, gradient profile, and tactical setup signals.")

        tactical = surface_analysis.get("tactical_briefing", {}) or {}
        r1, r2, r3 = st.columns(3)

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
            with st.expander("Mechanical setup", expanded=False):
                m1, m2, m3 = st.columns(3)

                setup_details_list = mechanical.get("setup_details", []) or []
                tire_size = "Standard"
                pressure_psi = "N/A"
                pressure_bar = "N/A"
                setup_type = "Standard"

                if len(setup_details_list) > 1 and isinstance(setup_details_list[1], str):
                    raw_text = setup_details_list[1]
                    wheel_match = re.search(r"(\d+(?:\.\d+)?)\s*wheels", raw_text)
                    psi_match = re.search(r"([\d.]+)\s*PSI", raw_text)
                    bar_match = re.search(r"\(([\d.]+)\s*Bar\)", raw_text)
                    type_match = re.search(r"\[(.*?)\]", raw_text)

                    if wheel_match:
                        tire_size = f'{wheel_match.group(1)}"'
                    if psi_match:
                        pressure_psi = f"{psi_match.group(1)} PSI"
                    if bar_match:
                        pressure_bar = f"{bar_match.group(1)} Bar"
                    if type_match:
                        setup_type = type_match.group(1)
                else:
                    tire_size = f'{mechanical.get("tire_size", "Standard")}"'
                    if mechanical.get("recommended_pressure_psi") is not None:
                        pressure_psi = f'{mechanical.get("recommended_pressure_psi")} PSI'
                    if mechanical.get("recommended_pressure_bar") is not None:
                        pressure_bar = f'{mechanical.get("recommended_pressure_bar")} Bar'
                    setup_type = mechanical.get("setup_type", "Standard")

                with m1:
                    metric_card("Wheels / tires", tire_size, "🛞", "#60a5fa", "Recommended wheel setup")
                with m2:
                    metric_card("Pressure", pressure_psi, "🔩", "#34d399", f"≈ {pressure_bar}")
                with m3:
                    metric_card("Setup strategy", setup_type, "🧰", "#f59e0b", "Terrain optimization")

                if not mechanical.get("compatible", True):
                    st.error("This bike/setup may not be fully compatible with the current route profile.")

                warnings = mechanical.get("safety_warnings", []) or []
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
        section_intro("Weather & safety", "Short-term tactical conditions for confidence, pacing, and kit planning.")

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
        section_intro("Mud & environmental risk", "Trail rideability, traction, and preservation signals.")

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
        section_intro("POI & logistics", "Nearby support points for water, food, repairs, safety, and rest.")
        with st.expander("Amenities on route", expanded=True):
            for i in range(0, len(pois), 3):
                cols = st.columns(3)
                for idx, poi in enumerate(pois[i:i + 3]):
                    with cols[idx]:
                        p_name = poi.get("name", "Unknown POI")
                        p_type = poi.get("type", "Amenity")
                        p_dist = poi.get("distance_m", 0)
                        icon, border_color = get_poi_style(p_type)

                        if isinstance(p_dist, (int, float)):
                            dist_str = f"{p_dist / 1000:.1f} km" if p_dist >= 1000 else f"{int(p_dist)} m"
                        else:
                            dist_str = "N/A"

                        link = None
                        p_loc = poi.get("location")
                        if isinstance(p_loc, dict):
                            lat = p_loc.get("latitude", p_loc.get("lat"))
                            lon = p_loc.get("longitude", p_loc.get("lon"))
                            if lat is not None and lon is not None:
                                link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"

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
        section_intro("Nutrition & hydration", "Fueling strategy aligned with distance, intensity, and environmental load.")
        with st.expander("Fueling details", expanded=False):
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
        with dl_col:
            with open(gpx_path, "rb") as file:
                st.download_button(
                    "Download GPX",
                    file,
                    file_name="mission.gpx",
                    mime="application/gpx+xml",
                    type="primary",
                    use_container_width=True,
                )

def _extract_direction_bias_from_text(user_input: str) -> list[str]:
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


def _extract_avoid_urban_from_text(user_input: str) -> bool:
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


def _extract_prefer_rural_from_text(user_input: str) -> bool:
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


def _extract_distance_flex_from_text(user_input: str) -> tuple[int, str | None]:
    text = (user_input or "").lower()

    if any(p in text for p in [
        "exactly",
        "as close as possible",
        "precisely",
        "exact distance",
    ]):
        return 0, "distance_first"

    if any(p in text for p in [
        "doesn't have to be exact",
        "does not have to be exact",
        "roughly",
        "around",
        "about",
        "approximately",
    ]):
        return 10, "balanced"

    if any(p in text for p in [
        "ride character matters more",
        "vibe matters more",
        "more about the ride quality",
        "prefer the character of the ride",
    ]):
        return 15, "ride_character_first"

    return 10, None


def _extract_distance_km_from_text(user_input: str):
    text = user_input or ""
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*km\b", text.lower())
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None

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

            parsed_distance = _extract_distance_km_from_text(user_input)
            parsed_direction_bias = _extract_direction_bias_from_text(user_input)
            parsed_avoid_urban = _extract_avoid_urban_from_text(user_input)
            parsed_prefer_rural = _extract_prefer_rural_from_text(user_input)
            parsed_flex_percent, parsed_priority_mode = _extract_distance_flex_from_text(user_input)

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
                dest_name = (
                        args.get("destination_name")
                        or (st.session_state.get("mission_context") or {}).get("destination_name")
                )
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

            final_bike, is_ebike = normalize_bike_type(args.get("bike_type"))
            complexity_val = clamp_complexity(args.get("complexity", 3))
            args["complexity"] = complexity_val

            rider_profile = st.session_state["rider_profile"]
            normalized_tire_size = normalize_tire_size(
                args.get("tire_size") or rider_profile["tire_size"],
                final_bike,
                )

            direction_bias = _normalize_direction_bias(
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
                            (st.session_state.get("mission_context") or {}).get("distance_flex_percent", 10),
                        ),
                        int,
                        10,
                    ),
                ),
            )
            priority_mode = str(
                args.get(
                    "priority_mode",
                    (st.session_state.get("mission_context") or {}).get("priority_mode", "balanced"),
                )
            ).strip().lower()
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
                "latitude": float(args.get("latitude")),
                "longitude": float(args.get("longitude")),
                "tire_size": normalized_tire_size,
                "include_weather": True,
                "include_mud_analysis": final_bike != "road",
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
                "complexity": complexity_val,
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
            res_data = result.model_dump() if hasattr(result, "model_dump") else result

            with st.expander("Raw engine response (res_data)", expanded=False):
                st.json(res_data)

            if not res_data or res_data.get("status") != "Success":
                status_box.update(label="Route planning failed", state="error")
                if route_mode == "point_to_point":
                    st.error("No valid A → B route matched the current parameters. Try adjusting start/destination or bike setup.")
                else:
                    st.error("No route matched the current parameters. Try changing location, bike type, or distance.")
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
        st.caption("For point-to-point missions, the engine will compute the real route distance automatically.")

    with st.form("guided_plan_form"):
        top1, top2 = st.columns(2)

        with top1:
            bike_type = st.selectbox(
                "Bike type",
                ["mtb", "road", "gravel", "e-mtb", "enduro"],
                key="guided_bike_type",
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
            goal = st.selectbox(
                "Ride goal",
                ["scenic", "training", "technical", "easy", "family"],
                key="guided_goal",
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
                f"{goal_hint}, tire size {tire_size}, difficulty {complexity}. "
            )
        else:
            prompt = (
                f"Plan a {bike_type} route from {start_location} to {destination_location} "
                f"{goal_hint}, tire size {tire_size}, difficulty {complexity}. "
            )

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
            "complexity": complexity,
            "goal": goal,
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
    st.caption("Ideal for reviewing a route you already have before race day or a big weekend ride.")

    with st.form("gpx_audit_form"):
        gpx_url = st.text_input(
            "GPX source (URL or local path)",
            placeholder="https://.../route.gpx or /path/to/route.gpx",
        )

        st.markdown("#### Rider & bike setup")
        col1, col2, col3 = st.columns(3)
        with col1:
            activity_type = st.selectbox("Type", ["road", "mtb"])
            rider_gender = st.selectbox("Gender", ["male", "female"])
        with col2:
            rider_weight_kg = st.number_input("Rider weight (kg)", min_value=40.0, max_value=130.0, value=75.0, step=0.5)
            bike_weight_kg = st.number_input("Bike weight (kg)", min_value=5.0, max_value=30.0, value=8.5, step=0.1)
        with col3:
            rider_fitness_level = st.selectbox("Fitness level", ["beginner", "intermediate", "pro"], index=1)
            pro_intensity = st.slider("Intensity factor", min_value=1.0, max_value=2.0, value=1.3, step=0.1)

        st.markdown("#### Weather planning")
        col4, col5 = st.columns(2)
        with col4:
            sweat_profile = st.selectbox("Sweat profile", ["low", "standard", "high", "extreme"], index=1)
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

                res_data = result.model_dump() if hasattr(result, "model_dump") else result
                st.success("GPX analysis completed.")

                track_metrics = res_data.get("track_metrics", {})
                if track_metrics:
                    g1, g2, g3 = st.columns(3)
                    with g1:
                        metric_card("Distance", f"{track_metrics.get('distance_km')} km", "📏", "#38bdf8")
                    with g2:
                        metric_card("Elevation gain", f"+{track_metrics.get('total_ascent')} m", "⛰️", "#a78bfa")
                    with g3:
                        metric_card("Max altitude", f"{track_metrics.get('max_altitude')} m", "🏔️", "#22c55e")

                planning = res_data.get("planning_tools", {})
                weather = planning.get("weather_forecast", {})
                if weather:
                    with st.expander("Weather forecast", expanded=True):
                        advice = weather.get("safety_advice", {})
                        if advice:
                            st.info(f"**{advice.get('status', 'Safety')}** — {advice.get('message', '')}")

                climbs = res_data.get("climb_analysis", [])
                if climbs:
                    with st.expander("Climb analysis"):
                        climb_df = []
                        for c in climbs:
                            climb_df.append({
                                "Start (km)": c["km_start"],
                                "Length (km)": c["dist_km"],
                                "Grade (%)": c["avg_grade"],
                                "Cat": c["category"],
                            })
                        st.table(climb_df)

                sims = res_data.get("performance_simulation", [])
                if sims:
                    with st.expander("Performance simulation"):
                        sim_df = []
                        for s in sims:
                            sim_df.append({
                                "Sector": s["climb"].split("@")[0].strip(),
                                "VAM": s["est_vam"],
                                "W/kg": s["target_wkg"],
                                "Time (min)": s["est_time_min"],
                            })
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

def render_rider_profile_panel() -> None:
    profile = st.session_state["rider_profile"]

    section_intro(
        "Rider profile",
        "Personal defaults used across planning, fueling, and route recommendations.",
    )

    with st.expander("Open rider settings", expanded=False):
        c1, c2, c3 = st.columns(3)

        with c1:
            profile["bike_type"] = st.selectbox(
                "Default bike",
                ["mtb", "road", "gravel", "e-mtb", "enduro"],
                index=["mtb", "road", "gravel", "e-mtb", "enduro"].index(profile["bike_type"]),
                key="rider_profile_bike_type",
            )

            available_tires = ["32", "29", "27.5", "700c", "650b"]
            current_tire = profile["tire_size"] if profile["tire_size"] in available_tires else "29"
            profile["tire_size"] = st.selectbox(
                "Default tire size",
                available_tires,
                index=available_tires.index(current_tire),
                key="rider_profile_tire_size",
            )

        with c2:
            profile["fitness_level"] = st.selectbox(
                "Fitness level",
                ["beginner", "intermediate", "pro"],
                index=["beginner", "intermediate", "pro"].index(profile["fitness_level"]),
                key="rider_profile_fitness_level",
            )

            profile["weight_kg"] = st.number_input(
                "Weight (kg)",
                min_value=40.0,
                max_value=150.0,
                value=float(profile["weight_kg"]),
                key="rider_profile_weight",
            )

        with c3:
            profile["gender"] = st.selectbox(
                "Gender",
                ["male", "female"],
                index=["male", "female"].index(profile["gender"]),
                key="rider_profile_gender",
            )

            metric_card("Bike", profile["bike_type"], "🚲", "#7c3aed", "Default ride setup")
            metric_card("Tire", profile["tire_size"], "🛞", "#38bdf8", "Tool-safe normalized value")

        st.session_state["rider_profile"] = profile

def main():
    init_session_state()
    inject_global_styles()
    inject_premium_component_styles()

    selected_model_name, n_layers = render_sidebar()
    llm = load_llm(selected_model_name, n_layers) if os.path.exists(get_local_model_path(selected_model_name)) else None

    render_home_dashboard(selected_model_name)
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