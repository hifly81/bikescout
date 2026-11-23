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

import os
import random
import re
from datetime import date
from typing import Optional

import streamlit as st
from langchain_community.chat_models import ChatLlamaCpp
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

from bikescout.app_helpers import (
    build_mission_snapshot,
    clamp_complexity,
    ext_cast,
    extract_avoid_urban_from_text,
    extract_direction_bias_from_text,
    extract_distance_flex_from_text,
    extract_distance_km_from_text,
    extract_point_to_point,
    normalize_bike_type,
    normalize_direction_bias,
    normalize_tire_size,
    resolve_location_query,
    resolve_profile,
    resolve_route_mode,
    summarize_mission,
    compute_readiness_score,
    compute_mission_intensity,
)
from bikescout.app_ui_helpers import (
    build_warning_ribbon,
    get_poi_style,
    get_surface_icon,
    inject_component_styles,
    inject_global_styles,
    metric_card,
    render_empty_state,
    render_mission_hud,
    render_mission_intensity_badge,
    render_rider_profile_panel,
    render_score_card,
    render_warning_ribbon,
    render_weather_tiles_native,
    section_intro,
)
try:
    from bikescout.mcp_server import (
        analyze_gpx_track,
        geocode_location,
        trail_scout_simple,
    )
    server_loaded = True
except (SystemExit, ImportError):
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

# ---------------------------------------------------------------------------
# Pydantic schemas for structured LLM output
# ---------------------------------------------------------------------------

class TrailScoutArgs(BaseModel):
    """Structured arguments the LLM requests for trail_scout_simple."""

    bike_type: str = Field(
        ..., enum=["mtb", "road", "gravel", "e-mtb", "enduro"],
        description="Type of bicycle.",
    )
    tire_size: str = Field(..., description="Wheel/tire size (e.g. 29, 700c).")
    total_length_km: Optional[float] = Field(
        None, description="Target distance in km for round trips."
    )
    route_mode: str = Field(
        ..., enum=["round_trip", "point_to_point"],
        description="round_trip for loops, point_to_point for A → B.",
    )
    location_name: str = Field(..., description="Starting place name.")
    destination_name: Optional[str] = Field(
        None, description="Destination place name (A → B only)."
    )
    dest_latitude: Optional[float] = None
    dest_longitude: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    include_weather: bool = True
    include_mud_analysis: bool = True
    include_nutrition_plan: bool = True
    include_poi: bool = True
    include_gpx: bool = True
    include_map: bool = True
    include_altimetry: bool = True
    is_ebike: bool = False
    weight_kg: float = 75.0
    seed: int = 42
    complexity: int = Field(3, ge=1, le=5)
    profile: str = Field(
        ..., enum=["cycling-mountain", "cycling-road", "cycling-electric"],
    )
    fitness_level: str = Field(
        ..., enum=["beginner", "intermediate", "pro"],
    )
    gender: str = Field(..., enum=["male", "female"])
    direction_bias: Optional[list[str]] = None
    avoid_urban: bool = False
    prefer_rural: bool = False
    distance_flex_percent: int = Field(10, ge=0, le=30)
    priority_mode: str = Field(
        "balanced", enum=["balanced", "distance_first", "ride_character_first"],
    )


class TacticalResponse(BaseModel):
    briefing: str = Field(..., description="Plain-language mission briefing.")
    can_execute: bool = Field(
        ..., description="True only when the user wants a cycling route/analysis."
    )
    tool: Optional[TrailScoutArgs] = Field(
        None, description="Tool arguments when can_execute is true."
    )


# ---------------------------------------------------------------------------
# LangChain setup
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are BikeScout Tactical AI.
Return ONLY valid JSON matching the schema.

Rules:
- Set can_execute=true only when the user clearly wants a cycling route or route-related analysis.
- When can_execute=true, use the trail_scout_simple tool via the `tool` field.
- Always preserve location context for follow-up requests.
- Always preserve routing preference context unless the user changes it.
- Distance must be in kilometers. Complexity range is 1..5 (default 3).
- Use point_to_point only for A to B routes; otherwise round_trip.

Routing preference extraction:
- N/S/E/W of start area -> direction_bias (e.g. ["south", "east"]).
- "avoid the city / urban streets" -> avoid_urban=true.
- "countryside / quieter roads / rural" -> prefer_rural=true.
- "vibe matters more than mileage" -> priority_mode="ride_character_first".
- "exactly X km" -> priority_mode="distance_first", distance_flex_percent=0.
- "about / roughly X km" -> distance_flex_percent=10 or 15, priority_mode="balanced".
- Otherwise priority_mode="balanced".
- Omit routing fields when nothing is mentioned.

Examples:
- "keep it south and east of town" -> direction_bias ["south", "east"]
- "avoid the city and prefer countryside roads" -> avoid_urban true, prefer_rural true
- "about 60 km, doesn't have to be exact" -> distance_flex_percent 10, priority_mode balanced
- "the vibe matters more than exact mileage" -> priority_mode ride_character_first
- "make it exactly 60 km if possible" -> priority_mode distance_first, distance_flex_percent 0
"""

parser = JsonOutputParser(pydantic_object=TacticalResponse)

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])


def get_local_model_path(model_name: str) -> str:
    return os.path.join(LOCAL_MODELS_DIR, AVAILABLE_MODELS[model_name]["file"])


@st.cache_resource
def load_llm(model_name: str, n_gpu_layers: int) -> Optional[ChatLlamaCpp]:
    path = get_local_model_path(model_name)
    if not os.path.exists(path):
        return None
    return ChatLlamaCpp(
        model_path=path,
        n_ctx=8192,
        n_gpu_layers=n_gpu_layers,
        temperature=0.0,
        max_tokens=512,
        verbose=False,
    )


def build_chain(llm: ChatLlamaCpp):
    return prompt | llm | parser


def llm_history_from_messages(messages: list[dict]) -> list:
    """Convert Streamlit chat messages into LangChain message objects."""
    out: list = []
    for m in messages:
        role = m.get("role")
        content = m.get("content", "")
        if role == "user":
            out.append(HumanMessage(content=content))
        elif role == "assistant" and content != "Connection established. Provide input...":
            out.append(AIMessage(content=content))
    return out[-6:]


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def init_session_state() -> None:
    defaults = {
        "messages": [],
        "mission_context": {},
        "mission_history": [],
        "ors_api_key": os.getenv("ORS_API_KEY", ""),
        "last_location_query": None,
        "rider_profile": {
            "bike_type": "mtb",
            "tire_size": "29",
            "fitness_level": "intermediate",
            "weight_kg": 75.0,
            "gender": "male",
        },
        "workspace_tab_selector": "Plan a Ride",
        "pending_tab_redirect": None,
        "pending_plan_request": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

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
                    from huggingface_hub import hf_hub_download
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
            st.rerun()

        return selected_model_name, n_layers


# ---------------------------------------------------------------------------
# Mission context
# ---------------------------------------------------------------------------

def update_mission_context(
    location_name: str,
    lat: float,
    lon: float,
    args: dict,
    distance_km: float,
    route_mode: str = "round_trip",
    destination_name: Optional[str] = None,
    dest_lat: Optional[float] = None,
    dest_lon: Optional[float] = None,
) -> None:
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


def _append_mission_summary(text: str) -> str:
    ctx = st.session_state.get("mission_context") or {}
    if not ctx:
        return text
    return f"{text}\n\n[{summarize_mission(ctx)}]"


# ---------------------------------------------------------------------------
# Plan execution (single consolidated entry point)
# ---------------------------------------------------------------------------

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
            with st.expander("Mechanical setup", expanded=True):
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


def _normalize_plan_args(
    args: dict,
    rider_profile: dict,
    route_mode: str,
    location_query: str,
    geo,
    dest_lat: Optional[float],
    dest_lon: Optional[float],
) -> dict:
    final_bike, is_ebike = normalize_bike_type(args.get("bike_type"))
    complexity_val = clamp_complexity(args.get("complexity", 3))
    raw_distance = ext_cast(args.get("distance"), float, 25.0)
    if raw_distance and raw_distance > 1000:
        raw_distance = raw_distance / 1000

    normalized_tire_size = normalize_tire_size(
        args.get("tire_size") or rider_profile["tire_size"],
        final_bike,
    )

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
    priority_mode = str(
        args.get(
            "priority_mode",
            (st.session_state.get("mission_context") or {}).get(
                "priority_mode", "balanced"
            ),
        )
    ).strip().lower()
    if priority_mode not in {"balanced", "distance_first", "ride_character_first"}:
        priority_mode = "balanced"

    return {
        "latitude": float(geo.lat),
        "longitude": float(geo.lon),
        "tire_size": normalized_tire_size,
        "include_weather": bool(args.get("include_weather", True)),
        "include_mud_analysis": bool(args.get("include_mud_analysis", final_bike != "road")),
        "include_nutrition_plan": bool(args.get("include_nutrition_plan", True)),
        "include_poi": bool(args.get("include_poi", True)),
        "include_gpx": bool(args.get("include_gpx", True)),
        "include_map": True,
        "include_altimetry": bool(args.get("include_altimetry", True)),
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
        "total_length_km": raw_distance if route_mode != "point_to_point" else None,
        "dest_latitude": dest_lat if route_mode == "point_to_point" else None,
        "dest_longitude": dest_lon if route_mode == "point_to_point" else None,
    }


def execute_plan(plan_request: dict, chain) -> tuple[str, bool]:
    """Execute a plan request from either the chat or the guided form.

    Returns (briefing_text, had_visual_result).
    """
    if not plan_request:
        return "No plan request found.", False

    try:
        rider_profile = st.session_state["rider_profile"]
        route_mode = resolve_route_mode(
            plan_request, plan_request.get("_raw_input", "")
        )
        start_location = plan_request.get("start_location") or plan_request.get("location_name")
        destination_location = plan_request.get("destination_location")

        if not start_location:
            return "Please specify a starting location.", False

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

        valid_args = _normalize_plan_args(
            plan_request,
            rider_profile,
            route_mode,
            start_location,
            geo,
            dest_lat,
            dest_lon,
        )

        # Drop None values so trail_scout_simple uses its own defaults.
        valid_args = {k: v for k, v in valid_args.items() if v is not None}

        with st.expander("Engine debug", expanded=False):
            st.json(valid_args)

        result = trail_scout_simple(**valid_args)
        res_data = result.model_dump() if hasattr(result, "model_dump") else result

        with st.expander("Engine response", expanded=False):
            st.json(res_data)

        if not res_data or res_data.get("status") != "Success":
            return "The system could not generate a route for this configuration.", False

        display_name = getattr(geo, "display_name", start_location)
        raw_distance = valid_args.get("total_length_km", 0) or 0

        update_mission_context(
            display_name,
            geo.lat,
            geo.lon,
            {
                "bike_type": valid_args["bike_type"],
                "tire_size": valid_args["tire_size"],
                "complexity": valid_args["complexity"],
                "direction_bias": valid_args["direction_bias"],
                "avoid_urban": valid_args["avoid_urban"],
                "prefer_rural": valid_args["prefer_rural"],
                "distance_flex_percent": valid_args["distance_flex_percent"],
                "priority_mode": valid_args["priority_mode"],
            },
            raw_distance,
            route_mode=route_mode,
            destination_name=dest_display if route_mode == "point_to_point" else None,
            dest_lat=dest_lat,
            dest_lon=dest_lon,
        )

        render_route_results(res_data)
        return "Mission generated successfully.", True

    except Exception as e:
        st.error("Something went wrong while planning the route.")
        with st.expander("Technical details"):
            st.code(f"{type(e).__name__}: {e}", language="text")
        return "Unable to complete route planning.", False


# ---------------------------------------------------------------------------
# Chat tab
# ---------------------------------------------------------------------------

def render_chat_tab(chain) -> None:
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

        st.info("Mission received from Plan a Ride. Running route analysis...")
        briefing, had_visual = execute_plan(pending_plan_request, chain)
        st.session_state["messages"].append(
            {
                "role": "assistant",
                "content": _append_mission_summary(briefing),
            }
        )
        return

    if not manual_input:
        return

    if chain is None:
        with st.chat_message("assistant"):
            st.error("Local model not available. Download a model from the sidebar first.")
        return

    st.session_state["messages"].append({"role": "user", "content": manual_input})
    with st.chat_message("user"):
        st.markdown(manual_input)

    llm_messages = list(st.session_state["messages"])
    history = llm_history_from_messages(llm_messages)

    with st.chat_message("assistant"):
        with st.status("Executing analysis...", expanded=True) as status_box:
            try:
                llm_output: TacticalResponse = chain.invoke(
                    {"input": manual_input, "history": history}
                )
                briefing_text = llm_output.briefing

                if not llm_output.can_execute or not llm_output.tool:
                    status_box.update(label="Completed", state="complete")
                    st.markdown(briefing_text)
                    st.session_state["messages"].append(
                        {
                            "role": "assistant",
                            "content": _append_mission_summary(briefing_text),
                        }
                    )
                    return

                tool_args = llm_output.tool.model_dump()
                tool_args["_raw_input"] = manual_input

                # Merge text-extracted preferences when the LLM omitted them.
                parsed_distance = extract_distance_km_from_text(manual_input)
                if parsed_distance is not None and not tool_args.get("total_length_km"):
                    tool_args["total_length_km"] = parsed_distance

                parsed_bias = extract_direction_bias_from_text(manual_input)
                if parsed_bias and not tool_args.get("direction_bias"):
                    tool_args["direction_bias"] = parsed_bias

                if extract_avoid_urban_from_text(manual_input):
                    tool_args["avoid_urban"] = True

                if extract_prefer_rural_from_text(manual_input):
                    tool_args["prefer_rural"] = True

                parsed_flex, parsed_priority = extract_distance_flex_from_text(manual_input)
                if "distance_flex_percent" not in tool_args or not tool_args["distance_flex_percent"]:
                    tool_args["distance_flex_percent"] = parsed_flex
                if parsed_priority and not tool_args.get("priority_mode"):
                    tool_args["priority_mode"] = parsed_priority

                briefing_text, had_visual = execute_plan(tool_args, chain)

                if had_visual:
                    status_box.update(label="Analysis complete", state="complete")
                else:
                    status_box.update(label="Completed", state="complete")
                    st.markdown(briefing_text)

                st.session_state["messages"].append(
                    {
                        "role": "assistant",
                        "content": _append_mission_summary(briefing_text),
                    }
                )

            except Exception as e:
                status_box.update(label="Analysis interrupted", state="error")
                st.error("Something went wrong while planning the route.")
                with st.expander("Technical details"):
                    st.code(f"{type(e).__name__}: {e}", language="text")


# ---------------------------------------------------------------------------
# Guided plan tab
# ---------------------------------------------------------------------------

def render_plan_tab() -> None:
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
            destination_location = (
                st.text_input("Destination", placeholder="e.g. Bolzano, Italy", key="guided_destination")
                if route_mode == "A → B"
                else ""
            )

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
                key="guided_direction_bias",
            )
            avoid_urban = st.checkbox(
                "Avoid urban streets",
                value=False,
                key="guided_avoid_urban",
            )
        with rc2:
            prefer_rural = st.checkbox(
                "Prefer countryside / quieter roads",
                value=False,
                key="guided_prefer_rural",
            )
            priority_mode = st.selectbox(
                "Priority mode",
                ["balanced", "distance_first", "ride_character_first"],
                index=0,
                key="guided_priority_mode",
            )

        distance_flex_percent = st.slider(
            "Distance flexibility (%)",
            min_value=0,
            max_value=30,
            value=10,
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
            prompt_text = (
                f"Plan a {distance} km {bike_type} circular loop near {start_location} "
                f"{goal_hint}, tire size {tire_size}, difficulty {complexity}. "
            )
        else:
            prompt_text = (
                f"Plan a {bike_type} route from {start_location} to {destination_location} "
                f"{goal_hint}, tire size {tire_size}, difficulty {complexity}. "
            )

        if direction_bias:
            prompt_text += f"Keep it mostly to the {' and '.join(direction_bias)}. "
        if avoid_urban:
            prompt_text += "Avoid urban streets. "
        if prefer_rural:
            prompt_text += "Prefer countryside or quieter roads. "
        if priority_mode == "distance_first":
            prompt_text += "Keep the route as close as possible to the requested distance. "
        elif priority_mode == "ride_character_first":
            prompt_text += "Prioritize the character of the ride over exact mileage. "
        else:
            prompt_text += "Balance route character and distance. "
        if distance_flex_percent == 0:
            prompt_text += "The distance should be exact if possible. "
        else:
            prompt_text += f"Allow about {distance_flex_percent}% flexibility on the target distance. "
        if include_poi:
            prompt_text += "Include POIs and amenities. "
        if include_weather:
            prompt_text += "Include weather. "
        if include_mud:
            prompt_text += "Include mud analysis. "
        if include_nutrition:
            prompt_text += "Include nutrition advice. "
        if include_gpx:
            prompt_text += "Include GPX export. "
        if include_altimetry:
            prompt_text += "Include altimetry. "

        plan_request = {
            "route_mode": "point_to_point" if route_mode == "A → B" else "loop",
            "start_location": start_location,
            "destination_location": destination_location if route_mode == "A → B" else None,
            "distance": float(distance) if distance is not None else None,
            "bike_type": bike_type,
            "tire_size": tire_size,
            "complexity": complexity,
            "goal": goal,
            "direction_bias": direction_bias,
            "avoid_urban": avoid_urban,
            "prefer_rural": prefer_rural,
            "distance_flex_percent": distance_flex_percent,
            "priority_mode": priority_mode,
            "include_poi": include_poi,
            "include_weather": include_weather,
            "include_mud_analysis": include_mud,
            "include_nutrition_plan": include_nutrition,
            "include_gpx": include_gpx,
            "include_altimetry": include_altimetry,
            "_raw_input": prompt_text,
        }

        st.session_state["pending_plan_request"] = plan_request
        st.session_state["pending_tab_redirect"] = "Chat Planner"
        st.rerun()


# ---------------------------------------------------------------------------
# GPX tab
# ---------------------------------------------------------------------------

def render_gpx_tab() -> None:
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    init_session_state()
    inject_global_styles()
    inject_component_styles()

    selected_model_name, n_layers = render_sidebar()

    model_path = get_local_model_path(selected_model_name)
    llm = load_llm(selected_model_name, n_layers) if os.path.exists(model_path) else None
    chain = build_chain(llm) if llm is not None else None

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
        render_chat_tab(chain)
    else:
        render_gpx_tab()


if __name__ == "__main__":
    main()
