import streamlit as st
import os
import time
import json
import re
import random
import pprint
from datetime import date
from typing import Dict, Any
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
try:
    from bikescout.mcp_server import (
        geocode_location,
        trail_scout_simple,
        analyze_gpx_track
    )
    server_loaded = True
except SystemExit:
    server_loaded = False
except ImportError:
    st.error("Could not find bikescout.mcp_server. Check your PYTHONPATH.")
    server_loaded = False

AVAILABLE_MODELS = {
    "Llama-3-8B": {
        "repo": "MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF",
        "file": "Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf",
        "description": ""
    },
    "Llama-3.1-8B-Instruct": {
        "repo": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "file": "Meta-Llama-3.1-8B-Instruct-Q6_K.gguf",
        "description": ""
    }
}

LOCAL_MODELS_DIR = "models"

st.set_page_config(
    page_title="BikeScout",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    
    .stApp, [data-testid="stHeader"] {
        background-color: #000000 !important;
        color: #e0e0e0 !important;
    }

    [data-testid="stChatInput"] {
        background-color: #000000 !important;
        padding-bottom: 20px;
    }
    
    [data-testid="stChatInput"] textarea {
        background-color: #000000 !important;
        color: #e0e0e0 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
    }

    [data-testid="stChatMessage"] {
        background-color: #000000 !important;
        border: 1px solid #30363d !important;
        border-radius: 15px;
    }
    
    .stChatMessage p, .stChatMessage span {
        color: #e0e0e0 !important;
    }

    .stExpander, [data-testid="stMetric"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
    }

    h1, h2, h3, h4, h5, h6, label {
        color: #ffffff !important;
    }

    .status-card {
        background-color: #161b22;
        padding: 10px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-top: 10px;
    }

    footer {visibility: hidden;}
    header {background-color: rgba(0,0,0,0) !important;}
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
        color: #e0e0e0 !important;
    }
    
    button[title="Change theme"] {
        display: none !important;
    }

    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
        border-bottom: none !important;
    }

    [data-testid="stChatInput"] {
        background-color: #0e1117 !important;
    }
    
    [data-testid="stChatInput"] textarea {
        background-color: #161b22 !important;
        color: #e0e0e0 !important;
        border: 1px solid #30363d !important;
    }

    [data-testid="stChatMessage"], [data-testid="stMetric"], .stExpander {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
    }

    .stDeployButton {
        display: none !important;
    }

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');

    .brand-container {
        font-family: 'Inter', sans-serif;
        text-decoration: none;
        font-size: 1.8rem;
        font-weight: 900;
        font-style: italic;
        text-transform: uppercase;
        letter-spacing: -0.05em;
        color: white;
    }

    .neon-text {
        color: #bef264; 
        text-shadow: 0 0 5px #bef264, 0 0 10px #bef264; 
    }
    
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #000000 !important;
    }

    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p {
        color: #e0e0e0 !important;
    }

    [data-testid="stSidebar"] div[data-baseweb="select"] {
        background-color: #161b22 !important;
        border-radius: 8px;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid #30363d !important;
    }

    .sidebar-brand {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        font-style: italic;
        text-transform: uppercase;
        letter-spacing: -0.05em;
        font-size: 1.2rem;
        color: white;
        margin-bottom: 20px;
    }
    
    </style>
    """, unsafe_allow_html=True)

def get_local_model_path(model_name: str) -> str:
    filename = AVAILABLE_MODELS[model_name]["file"]
    return os.path.join(LOCAL_MODELS_DIR, filename)

@st.cache_resource
def load_llm(model_name: str, n_gpu_layers: int):
    path = get_local_model_path(model_name)
    if not os.path.exists(path):
        return None

    return Llama(
        model_path=path,
        n_ctx=8192,
        n_gpu_layers=n_gpu_layers,
        verbose=False
    )

def generate_tactical_response(messages_history: list, llm_instance: Llama) -> str:
    json_schema = {
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {
                "briefing": {"type": "string"},
                "can_execute": {
                    "type": "boolean",
                    "description": "Set to true only if the location is clearly defined (including from conversation history) and the user's intent is cycling-related."
                },
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
                                            "enum": ["mtb", "road", "gravel", "e-mtb", "enduro"]
                                        },
                                        "tire_size": {"type": "string"},
                                        "distance": {"type": "number"},
                                        "location_name": {
                                            "type": "string",
                                            "description": "MANDATORY. Use the place from the current prompt or RECOVER it from history if missing."
                                        },
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
                                        "fitness_level": {
                                            "type": "string",
                                            "enum": ["beginner", "intermediate", "pro"]
                                        },
                                        "gender": {
                                            "type": "string",
                                            "enum": ["male", "female"]
                                        },
                                    },
                                    "required": ["bike_type", "tire_size"]
                                }
                            },
                            "required": ["name", "args"]
                        },
                        {"type": "null"}
                    ]
                }
            },
            "required": ["briefing", "tool", "can_execute"]
        }
    }

    system_prompt = """
    You are BikeScout Tactical AI, an expert cycling logistics and route-planning assistant.
    You MUST respond ONLY with a valid JSON object matching the provided schema. No markdown, no preambles.
    
    === 1. MISSION CONTROL (CRITICAL LOGIC) ===
    - CAN_EXECUTE PROTOCOL: Set 'can_execute' to true ONLY if you have a clear geographic location AND the user wants to plan or analyze a cycling route. 
    - REJECTION: If the user is chatting, asking about unrelated topics (e.g., soccer, politics), or if the location is completely unknown and missing from history, you MUST set 'can_execute' to false and 'tool' to null.
    - TOOL SELECTION: When 'can_execute' is true, always set 'tool.name' to 'trail_scout_simple'.
    
    === 2. LOCATION PERSISTENCE (MANDATORY) ===
    - You MUST always populate either 'location_name' or 'latitude' and 'longitude' inside the tool args.
    - STRATEGY: Extract the location from the current prompt. If the user gives a relative command (e.g., "add POI", "make it 30km"), you MUST look at the chat history and reuse the last known location/coordinates. NEVER leave the location null if it was established earlier.
    
    === 3. PARAMETER & ENTITY MAPPING ===
    - DISTANCE: Always express 'distance' as a FLOAT in KILOMETERS (e.g., 25.0). NEVER use meters.
    - BIKE_TYPE: Identify from context. Allowed values ONLY: ["mtb", "road", "gravel", "e-mtb", "enduro"].
    - TIRE_SIZE: Map explicit sizes (e.g., '29-inch' -> '29', '700c' -> '700c').
    - FITNESS_LEVEL: Map to ["beginner", "intermediate", "pro"].
    - Ensure 'distance', 'bike_type', and 'tire_size' are always included in the args if mentioned or logically inferred.
    
    === 4. TACTICAL OVERLAYS (Set to TRUE if context matches) ===
    - 'include_weather' & 'include_mud_analysis': If user mentions 'tomorrow', 'weather', 'conditions', or 'go/no-go'.
    - 'include_mud_analysis': If user mentions 'mud', 'terrain', 'conditions'.
    - 'include_nutrition_plan': If user mentions 'food', 'eating', 'calories', or 'nutrition'.
    - 'include_poi': If user mentions 'amenities', 'poi', 'bars', 'water', or 'places'.
    - 'include_gpx': If user asks for 'gpx', 'track', or 'download'.
    - 'include_altimetry': If user asks about 'altimetry', 'elevation', 'climb', or 'hills'.
    - 'include_map': If user asks for a 'map', 'visual map', or 'layout'.
    """

    formatted_messages = [{"role": "system", "content": system_prompt}]
    last_messages = messages_history[-6:]
    formatted_messages.extend(last_messages)

    response = llm_instance.create_chat_completion(
        messages=formatted_messages,
        response_format=json_schema,
        temperature=0.0,
        max_tokens=512
    )

    return response["choices"][0]["message"]["content"].strip()

with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            BIKE<span class="neon-text">SCOUT</span>
        </div>
        <hr style="margin-top: -10px; border-color: #30363d;">
    """, unsafe_allow_html=True)

    st.subheader("Configuration")
    existing_key = os.getenv("ORS_API_KEY", "")
    ors_key = st.text_input(
        "OpenRouteService API Key",
        value=st.session_state.get("ors_api_key", existing_key),
        type="password",
        help="Required for routing, geocoding, and trail analysis. Get one at openrouteservice.org"
    )

    if ors_key:
        st.session_state["ors_api_key"] = ors_key
        os.environ["ORS_API_KEY"] = ors_key
        st.success("ORS Status: ACTIVE")
    else:
        st.error("ORS Status: OFFLINE")

    st.divider()

    st.subheader("LLM Models")
    selected_model_name = st.selectbox(
        "Select Local LLM",
        options=list(AVAILABLE_MODELS.keys()),
        help="Models are executed locally on your hardware for maximum privacy."
    )

    st.caption(AVAILABLE_MODELS[selected_model_name]["description"])

    gpu_enabled = st.toggle("GPU Acceleration", value=True, help="Enable this for faster reasoning speed.")
    n_layers = -1 if gpu_enabled else 0

    model_path = get_local_model_path(selected_model_name)

    if not os.path.exists(model_path):
        if st.button(f"Download {selected_model_name}", use_container_width=True):
            with st.status("Initializing secure download...", expanded=True) as status:
                st.write("*Wait, downloading the model...*")
                try:
                    if not os.path.exists(LOCAL_MODELS_DIR):
                        os.makedirs(LOCAL_MODELS_DIR)

                    hf_hub_download(
                        repo_id=AVAILABLE_MODELS[selected_model_name]["repo"],
                        filename=AVAILABLE_MODELS[selected_model_name]["file"],
                        local_dir=LOCAL_MODELS_DIR,
                        local_dir_use_symlinks=False
                    )
                    status.update(label="Download Complete!", state="complete")
                    st.rerun()
                except Exception as e:
                    st.error(f"Mission Aborted: {e}")

        st.stop()

    st.divider()

    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- MAIN INTERFACE ---
head_col1, head_col2 = st.columns([0.7, 0.3])

with head_col1:
    st.markdown("""
        <div class="brand-container">
            BIKE<span class="neon-text">SCOUT</span>
        </div>
        <div style="margin-top: -10px; margin-bottom: 20px;">
            <small style="color: #8b949e; letter-spacing: 1px; text-transform: uppercase;">
                The AI Engine that turns raw geodata into Predictive Intel.
            </small>
        </div>
    """, unsafe_allow_html=True)

with head_col2:
    st.markdown(f"""
        <div class="status-card">
            <small style="color: #8b949e;">ENGINE STATUS</small><br>
            <span style="color: #238636;">●</span> <strong>READY</strong> | <code>{selected_model_name}</code>
        </div>
    """, unsafe_allow_html=True)

st.divider()
llm = load_llm(selected_model_name, n_layers)

# --- MODE SELECTOR ---
mode = st.radio(
    "Select Operation Mode:",
    ["💬 BikeScout (Chat)", "🗺️ GPX Track Audit"],
    horizontal=True,
    label_visibility="collapsed"
)
st.divider()

def ext_cast(val, to_type, default):
    if val in [None, "", "None", "null"]:
        return default
    if isinstance(val, str):
        match = re.search(r"[-+]?\d*\.?\d+", val)
        if match:
            val = match.group()
        else:
            return default

    try:
        if to_type == bool:
            return str(val).lower() in ['true', '1', 't', 'y', 'yes']
        if to_type == int:
            return int(float(val))
        return to_type(val)
    except (ValueError, TypeError):
        return default

def process_local_mcp_request(raw_llm_json: str, user_input: str):
    res_data = None
    briefing_text = "Analysis complete."

    with st.status("Executing Analysis...", expanded=True) as status:
        try:
            clean_json_str = raw_llm_json.strip()
            if clean_json_str.startswith("```json"):
                clean_json_str = clean_json_str[7:-3].strip()
            elif clean_json_str.startswith("```"):
                clean_json_str = clean_json_str[3:-3].strip()

            data = json.loads(clean_json_str)
            briefing_text = data.get("briefing", "Analysis complete.")

            briefing_text = re.sub(r'(?i)Mission Control|Briefing Ready', '', briefing_text).strip()

            can_execute = data.get("can_execute", False)
            tool_data = data.get("tool")

            if not can_execute:
                status.update(label="Analysis Complete", state="complete")
                return briefing_text

            if not tool_data:
                status.update(label="Analysis Complete", state="complete")
                return briefing_text

            tool_name = tool_data.get("name")
            args = tool_data.get("args", {})

            if tool_name == "trail_scout_simple":
                current_query = args.get("location_name")
                if current_query:
                    st.session_state["last_location_query"] = current_query
                    location_query = current_query
                else:
                    location_query = st.session_state.get("last_location_query")

                geo = geocode_location(location_name=location_query)
                if not geo:
                    status.update(label="Geolocalization failed", state="error")
                    return "Geolocalization failed"

                args["latitude"] = geo.lat
                args["longitude"] = geo.lon

                raw_distance = ext_cast(args.get("distance"), float, 25.0)
                if raw_distance:
                    if raw_distance > 1000:
                        raw_distance = raw_distance / 1000
                    st.session_state["last_raw_distance"] = raw_distance
                else:
                    raw_distance = st.session_state.get("last_raw_distance")

                raw_bike = str(args.get("bike_type")).lower()
                is_ebike = False
                if any(word in raw_bike for word in ["electric", "e-mtb", "emtb", "ebike"]):
                    final_bike, is_ebike = "e-mtb", True
                elif "road" in raw_bike: final_bike = "road"
                elif "gravel" in raw_bike: final_bike = "gravel"
                elif "enduro" in raw_bike or "downhill" in raw_bike: final_bike = "enduro"
                else: final_bike = "mtb"

                valid_args = {
                    "latitude": float(args.get("latitude")),
                    "longitude": float(args.get("longitude")),
                    "total_length_km": raw_distance,
                    "tire_size": str(args.get("tire_size")),
                    "include_weather": bool(args.get("include_weather")),
                    "include_mud_analysis": bool(args.get("include_mud_analysis")),
                    "include_nutrition_plan": bool(args.get("include_nutrition_plan")),
                    "include_poi": bool(args.get("include_poi")),
                    "include_gpx": bool(args.get("include_gpx")),
                    "include_map": bool(args.get("include_map")),
                    "include_altimetry": bool(args.get("include_altimetry")),
                    "weight_kg": ext_cast(args.get("weight_kg"), float, 75.0),
                    "gender": str(args.get("gender") or "male"),
                    "seed": random.randint(1, 999999),
                    "bike_type": final_bike,
                    "is_ebike": is_ebike,
                    "fitness_level": str(args.get("fitness_level") or "intermediate"),
                }

                #st.markdown(valid_args, unsafe_allow_html=True)

                result = trail_scout_simple(**valid_args)
                res_data = result.model_dump() if hasattr(result, 'model_dump') else result

                if not res_data or res_data is False:
                    status.update(label="Route planning failed", state="error")

                    st.error(
                        "### 🗺️ No route matches your parameters\n"
                        "The engine completed the search but couldn't find or generate a valid trail "
                        "with the current combination of location, distance, and bike settings.\n\n"
                        "💡 **What can you do?** Try increasing the search distance, changing the bike type, "
                        "or choosing a slightly different starting location."
                    )

                    return "The system could not generate a tactical profile for this specific configuration."
                status.update(label="Analysis Complete", state="complete")

        except Exception as e:
            status.update(label="Route analysis interrupted", state="error")

            st.error(
                "### 🗺️ Oops! Something went wrong while planning your route\n"
                "We couldn't successfully process the trail data at this moment. "
                "This might be due to a temporary connection glitch or unresolvable location coordinates.\n\n"
                "💡 **What can you do?** Please try again in a few moments or slightly adjust your search parameters."
            )

            with st.expander("🔍 Technical Details (Engine Telemetry Debug)"):
                st.code(f"Error Type: {type(e).__name__}\nDiagnostic Log: {str(e)}", language="text")

            return "Unable to complete tactical route planning due to a system anomaly."

    if res_data:
        info = res_data.get("info", {})

        if not info:
            briefing_text = "Route not found."
            return briefing_text

        surface_analysis = info.get("surface_analysis", {})
        logistics = res_data.get("logistics", {})
        conditions = res_data.get("conditions", {})
        dist, elev, diff = info.get("distance_km", "N/A"), info.get("ascent_m", "N/A"), info.get("difficulty", "N/A")

        st.markdown(f"### 📍 Route")

    if surface_analysis:
        tactical_briefing = surface_analysis.get("tactical_briefing", {})
        if tactical_briefing:
            climb_category = tactical_briefing.get("climb_category", "N/A")
            avg_gradient = tactical_briefing.get("avg_gradient", "N/A")
            avg_climb_gradient = tactical_briefing.get("avg_climb_gradient", "N/A")

            r1_m1, r1_m2, r1_m3 = st.columns(3)
            with r1_m1:
                st.markdown("<div style='padding: 10px; border-radius: 5px; background-color: rgba(151, 166, 195, 0.1); border-left: 5px solid #29b6f6;'>", unsafe_allow_html=True)
                st.metric("🏃 Distance", f"{dist} km")
                st.markdown("</div>", unsafe_allow_html=True)
            with r1_m2:
                st.markdown("<div style='padding: 10px; border-radius: 5px; background-color: rgba(151, 166, 195, 0.1); border-left: 5px solid #ab47bc;'>", unsafe_allow_html=True)
                st.metric("🏔️ Total Ascent", f"{elev} m")
                st.markdown("</div>", unsafe_allow_html=True)
            with r1_m3:
                st.markdown("<div style='padding: 10px; border-radius: 5px; background-color: rgba(151, 166, 195, 0.1); border-left: 5px solid #ec407a;'>", unsafe_allow_html=True)
                st.metric("⚡ Difficulty", diff.split('(')[0].strip() if isinstance(diff, str) else diff)
                st.markdown("</div>", unsafe_allow_html=True)

            st.write("")

            r2_m1, r2_m2, r2_m3 = st.columns(3)
            with r2_m1:
                st.markdown("<div style='padding: 10px; border-radius: 5px; background-color: rgba(151, 166, 195, 0.1); border-left: 5px solid #26a69a;'>", unsafe_allow_html=True)
                st.metric("📈 Avg Gradient", f"{avg_gradient}")
                st.markdown("</div>", unsafe_allow_html=True)
            with r2_m2:
                st.markdown("<div style='padding: 10px; border-radius: 5px; background-color: rgba(151, 166, 195, 0.1); border-left: 5px solid #ffa726;'>", unsafe_allow_html=True)
                st.metric("🧗 Climb Profile", f"{climb_category}")
                st.markdown("</div>", unsafe_allow_html=True)
            with r2_m3:
                st.markdown("<div style='padding: 10px; border-radius: 5px; background-color: rgba(151, 166, 195, 0.1); border-left: 5px solid #ef5350;'>", unsafe_allow_html=True)
                st.metric("🔺 Avg Climb Gradient", f"{avg_climb_gradient}")
                st.markdown("</div>", unsafe_allow_html=True)

        surfaces = surface_analysis.get("surface_breakdown", [])
        if surfaces:
            st.write("")
            with st.expander("🧱 Surface Breakdown & Terrain Mix", expanded=True):
                def get_surface_icon(s_type):
                    s_lower = s_type.lower()
                    if "asphalt" in s_lower or "tarmac" in s_lower or "paved" in s_lower or "strada" in s_lower:
                        return "🛣️"
                    if "gravel" in s_lower or "sterrato" in s_lower:
                        return "🪨"
                    if "dirt" in s_lower or "singletrack" in s_lower or "trail" in s_lower:
                        return "🌲"
                    if "mud" in s_lower or "fango" in s_lower:
                        return "💩"
                    if "sand" in s_lower or "sabbia" in s_lower:
                        return "🏖️"
                    return "🗺️"

                for s in surfaces:
                    s_type = s.get('type', 'Unknown')
                    s_pct_str = s.get('percentage', '0%')
                    icon = get_surface_icon(s_type)

                    try:
                        pct_val = float(s_pct_str.replace('%', '').strip()) / 100.0
                        pct_val = max(0.0, min(1.0, pct_val)) # Clamp tra 0 e 1
                    except:
                        pct_val = 0.0

                    col_label, col_bar = st.columns([2, 3])
                    with col_label:
                        st.markdown(f"**{icon} {s_type}**")
                    with col_bar:
                        st.progress(pct_val, text=f"**{s_pct_str}**")

            mechanical = surface_analysis.get("mechanical_setup", {})
            if mechanical:
                with st.expander("⚙️ Mechanical Setup"):
                    mech_col1, mech_col2, mech_col3 = st.columns(3)

                    tire_size = "Standard"
                    pressure_psi = "N/A"
                    pressure_bar = "N/A"
                    setup_type = "Standard Setup"

                    setup_details_list = mechanical.get("setup_details", [])

                    if len(setup_details_list) > 1 and isinstance(setup_details_list[1], str):
                        raw_text = setup_details_list[1]

                        # 1. Estrazione dimensione ruote (es. 29)
                        wheel_match = re.search(r'(\d+)\s*wheels', raw_text)
                        if wheel_match:
                            tire_size = f"{wheel_match.group(1)}\""

                        # 2. Estrazione PSI (es. 18.7)
                        psi_match = re.search(r'([\d.]+)\s*PSI', raw_text)
                        if psi_match:
                            pressure_psi = f"{psi_match.group(1)} PSI"

                        # 3. Estrazione Bar (es. 1.29)
                        bar_match = re.search(r'\(([\d.]+)\s*Bar\)', raw_text)
                        if bar_match:
                            pressure_bar = f"{bar_match.group(1)} Bar"

                        # 4. Estrazione Tipo Setup nelle parentesi quadre (es. Mud Flotation Setup)
                        type_match = re.search(r'\[(.*?)\]', raw_text)
                        if type_match:
                            setup_type = type_match.group(1)
                    else:
                        if mechanical.get("tire_size"): tire_size = f"{mechanical.get('tire_size')}\""
                        if mechanical.get("recommended_pressure_psi"): pressure_psi = f"{mechanical.get('recommended_pressure_psi')} PSI"
                        if mechanical.get("recommended_pressure_bar"): pressure_bar = f"{mechanical.get('recommended_pressure_bar')} Bar"
                        if mechanical.get("setup_type"): setup_type = mechanical.get("setup_type")

                    mech_col1.metric("Wheels / Tires", tire_size)
                    mech_col1.caption("Optimal Wheel Size")

                    mech_col2.metric("Pressure", pressure_psi)
                    mech_col2.caption(f"Equivalent: {pressure_bar}")

                    mech_col3.metric("Setup Strategy", setup_type)
                    mech_col3.caption("Terrain Optimization")


        weather_data = None
        if conditions:
            weather_data = conditions.get("weather", [])
        if weather_data and isinstance(weather_data, list):
            with st.expander("🌤️ Tactical Weather Forecast"):
                def clean_unit(text):
                    if not text: return "N/A"
                    text = str(text)
                    for unit in ["°C", "%%", "mm", "km/h"]:
                        if text.count(unit) > 1: text = text.replace(unit + unit, unit)
                    return text

                chart_data = []

                for w in weather_data:
                    try:
                        t_val = float(str(w.get('temp')).encode('ascii', 'ignore').decode('ascii').replace('C', '').strip())
                        r_val = float(str(w.get('rain_prob')).replace('%', '').strip())
                        chart_data.append({"Ora": w.get("time"), "Temp (°C)": t_val, "Rain Prob (%)": r_val})
                    except: continue

                w_col1, w_col2, w_col3 = st.columns(3)
                if chart_data:
                    w_col1.metric("Peak Temp", f"{max([d['Temp (°C)'] for d in chart_data])} °C")
                    w_col2.metric("Max Rain Prob", f"{max([d['Rain Prob (%)'] for d in chart_data])} %")
                if conditions.get("safety_advice"):
                    w_col3.metric("Safety Advice", conditions.get("safety_advice")[:20] + "...")

                st.divider()
                if chart_data:
                    st.write("**Temperature & Rain Probability Trend**")
                    import pandas as pd
                    st.line_chart(pd.DataFrame(chart_data).set_index("Ora"), height=250)

                st.divider()
                weather_table = [{"Time": w.get("time"), "Temp": clean_unit(w.get("temp")), "Apparent": clean_unit(w.get("app_temp")), "Rain %": clean_unit(w.get("rain_prob")), "Rain mm": clean_unit(w.get("rain_mm")), "Wind": clean_unit(w.get("wind")), "Gusts": clean_unit(w.get("gusts"))} for w in weather_data]
                st.dataframe(weather_table, use_container_width=True, hide_index=True)

                if conditions.get("safety_advice"):
                    st.warning(f"**Security Note:** {conditions.get('safety_advice')}")

        mud_data = None
        if conditions:
            mud_data = conditions.get("mud_risk", {})
        if mud_data:
            tactical_mud = mud_data.get("tactical_analysis", {})
            env_context = mud_data.get("environmental_context", {})
            with st.expander("📋 Terrain & Environmental Intelligence"):
                m_col1, m_col2, m_col3 = st.columns(3)
                risk_s = tactical_mud.get("mud_risk_score", "Unknown")
                risk_c = "🟢" if risk_s == "Low" else "🟡" if risk_s == "Moderate" else "🔴"
                m_col1.metric("Mud Risk", f"{risk_c} {risk_s}")
                m_col2.metric("Dry Time ETA", tactical_mud.get("dry_time_eta", "N/A"))
                m_col3.metric("Rain (72h)", f"{env_context.get('total_rain_72h_mm')} mm")
                st.divider()
                t1, t2 = st.columns(2)
                traction = tactical_mud.get("traction_risk", {})
                with t1:
                    st.write("**🚜 Traction Analysis**")
                    if traction.get("level") == "Low": st.success(f"Risk: {traction.get('level')} - {traction.get('advice')}")
                    else: st.warning(f"Risk: {traction.get('level')} - {traction.get('advice')}")
                damage = tactical_mud.get("trail_damage_risk", {})
                with t2:
                    st.write("**🌲 Trail Integrity**")
                    if damage.get("level") == "Low": st.info(f"Damage Risk: {damage.get('level')} - {damage.get('advice')}")
                    else: st.error(f"Damage Risk: {damage.get('level')} - {damage.get('advice')}")

        pois = None
        if logistics:
            pois = logistics.get("nearby_amenities")

        if pois:
            with st.expander("📍 Logistics & POIs", expanded=True):
                st.markdown("#### 🚀 Waypoints & Tactical Amenities")

                def get_poi_style(poi_type):
                    t_lower = poi_type.lower()
                    if "water" in t_lower or "fontan" in t_lower or "drink" in t_lower:
                        return "💧", "#29b6f6"
                    if "shop" in t_lower or "repair" in t_lower or "bike" in t_lower or "meccan" in t_lower:
                        return "🔧", "#ffa726"
                    if "food" in t_lower or "restaur" in t_lower or "bar" in t_lower or "caf" in t_lower:
                        return "☕", "#26a69a"
                    if "shelter" in t_lower or "hotel" in t_lower or "camp" in t_lower:
                        return "🏠", "#ab47bc"
                    if "hospital" in t_lower or "first aid" in t_lower or "med" in t_lower:
                        return "🚨", "#ef5350"
                    return "📍", "#97a6c3"

                for i in range(0, len(pois), 3):
                    chunk = pois[i:i+3]
                    cols = st.columns(3)

                    for idx, poi in enumerate(chunk):
                        with cols[idx]:
                            p_name = poi.get('name', 'Unknown POI')
                            p_type = poi.get('type', 'Amenity')
                            p_dist = poi.get('distance_m', 0)

                            if isinstance(p_dist, (int, float)):
                                if p_dist >= 1000:
                                    dist_str = f"{p_dist / 1000:.1f} km"
                                else:
                                    dist_str = f"{int(p_dist)} m"
                            else:
                                dist_str = "N/A"

                            icon, border_color = get_poi_style(p_type)

                            st.markdown(
                                f"""
                                <div style='
                                    padding: 12px; 
                                    border-radius: 6px; 
                                    background-color: rgba(151, 166, 195, 0.1); 
                                    border-left: 5px solid {border_color};
                                    margin-bottom: 10px;
                                    height: 105px;
                                '>
                                    <div style='font-size: 1.1em; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>
                                        {icon} {p_name}
                                    </div>
                                    <div style='font-size: 0.85em; opacity: 0.8; margin-top: 4px;'>
                                        Category: <b>{p_type.capitalize()}</b>
                                    </div>
                                    <div style='font-size: 0.9em; font-weight: 500; color: {border_color}; margin-top: 2px;'>
                                        📏 Distance: {dist_str}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            p_loc = poi.get('location')
                            if isinstance(p_loc, dict) and 'latitude' in p_loc and 'longitude' in p_loc:
                                lat, lon = p_loc['latitude'], p_loc['longitude']
                                st.utility_cube = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                                st.markdown(f"[🗺️ View on Map]({st.utility_cube})", unsafe_allow_html=True)
                            elif isinstance(p_loc, dict) and 'lat' in p_loc and 'lon' in p_loc:
                                lat, lon = p_loc['lat'], p_loc['lon']
                                st.utility_cube = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                                st.markdown(f"[🗺️ View on Map]({st.utility_cube})", unsafe_allow_html=True)

        nutrition = None
        if logistics:
            nutrition = logistics.get("nutrition_plan", {})
        if nutrition:
            briefing_nut = nutrition.get("mission_nutrition_briefing", {})
            with st.expander("🥣 Tactical Nutrition & Fueling"):
                n_col1, n_col2, n_col3 = st.columns(3)
                f, c, e = briefing_nut.get("fluids", {}), briefing_nut.get("carbohydrates", {}), briefing_nut.get("electrolytes", {})
                n_col1.metric("Total Fluids", f"{f.get('total_liters')} L")
                n_col1.caption(f"Avg: {f.get('hourly_average_ml')} ml/h")
                n_col2.metric("Total Carbs", f"{c.get('total_grams')} g")
                n_col2.caption(f"Target: {c.get('hourly_target_g')} g/h ({c.get('intensity_context')})")
                n_col3.metric("Total Sodium", f"{e.get('total_sodium_mg')} mg")
                n_col3.caption(f"Target: {e.get('hourly_sodium_mg')} mg/h")
                st.divider()
                if briefing_nut.get("tactical_advice"):
                    st.markdown("**🛡️ Fueling Strategy:**")
                    for advice in briefing_nut.get("tactical_advice", []): st.info(advice)

        map_uri, alt_uri = res_data.get("map_path"), res_data.get("elevation_profile_path")
        if map_uri or alt_uri:
            st.divider()
            v1, v2 = st.columns(2)
            if map_uri: v1.image(map_uri, caption="Tactical Map")
            if alt_uri: v2.image(alt_uri, caption="Elevation Profile")

        gpx_path = res_data.get("gpx_export_path")
        if gpx_path and os.path.exists(gpx_path):
            with open(gpx_path, "rb") as file:
                st.download_button("📥 Download Tactical GPX", file, file_name="mission.gpx", mime="application/gpx+xml")

    return briefing_text

# ==========================================
# UI ROUTING (CHAT VS GPX FORM)
# ==========================================

if mode == "💬 BikeScout (Chat)":

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Connection established. Provide input..."}
        ]

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input Box
    if user_input := st.chat_input("Plan a 30km mtb ride in Moab area"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            raw_output = generate_tactical_response(st.session_state.messages, llm)
            final_briefing = process_local_mcp_request(raw_output, user_input)
            clean_briefing = re.sub(r'(?i)TOOL:.*', '', final_briefing, flags=re.DOTALL)
            st.markdown(clean_briefing.strip())

        clean_history_text = re.sub(r'(?i)TOOL:.*', '', final_briefing, flags=re.DOTALL).strip()
        st.session_state.messages.append({"role": "assistant", "content": clean_history_text})


elif mode == "🗺️ GPX Track Audit":
    st.subheader("GPX Tactical Audit")
    st.caption("Perform a professional analysis of a GPX track by calculating VAM, W/kg, weather risks, and UCI categories.")

    with st.form("gpx_audit_form"):
        gpx_url = st.text_input(
            "GPX Source (URL or local path) *",
            placeholder="es. https://raw.githubusercontent.com/.../route.gpx o /home/test/route_local.gpx"
        )

        st.markdown("#### Rider & Bike Setup")
        col1, col2, col3 = st.columns(3)

        with col1:
            activity_type = st.selectbox("Type", ["road", "mtb"])
            rider_gender = st.selectbox("Gender", ["male", "female"])

        with col2:
            rider_weight_kg = st.number_input("Rider Weight (kg)", min_value=40.0, max_value=130.0, value=75.0, step=0.5)
            bike_weight_kg = st.number_input("Bike Weight (kg)", min_value=5.0, max_value=30.0, value=8.5, step=0.1)

        with col3:
            rider_fitness_level = st.selectbox("Fitness Level", ["beginner", "intermediate", "pro"], index=1)
            pro_intensity = st.slider("Fitness Level", min_value=1.0, max_value=2.0, value=1.3, step=0.1, help="1.0 = Amateur, 1.6 = Pro Pace, 2.0 = World Class attack")

        st.markdown("#### Physiology & Weather")
        col4, col5 = st.columns(2)

        with col4:
            sweat_profile = st.selectbox(
                "Sweat Profile (Sodium)",
                ["low", "standard", "high", "extreme"],
                index=1,
                help="Low: ~400mg/L | Std: ~800mg/L | High: ~1200mg/L | Ext: ~1800mg/L"
            )

        with col5:
            enable_date = st.checkbox("Schedule Date/Time (for Predictive Weather)")
            if enable_date:
                target_date = st.date_input("Data Target", value=date.today())
                c_start, c_end = st.columns(2)
                with c_start:
                    start_hour = st.number_input("Starting Hour (0-23)", min_value=0, max_value=23, value=8)
                with c_end:
                    end_hour = st.number_input("End Hour (0-23)", min_value=0, max_value=23, value=14)
            else:
                target_date, start_hour, end_hour = None, None, None

        st.markdown("#### Output")
        report = st.toggle("Generate Final PDF Report", value=False)
        submitted = st.form_submit_button("Start Tactical Analysis", type="primary")

    if submitted:
        if not gpx_url:
            st.error("⚠️ The GPX Source field is mandatory.")
        else:
            with st.spinner("Telemetry extraction and metrics calculation in progress..."):
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
                        report=report
                    )

                    res_data = result.model_dump() if hasattr(result, 'model_dump') else result

                    st.success("🏁 Tactical Analysis Completed!")

                    track_metrics = res_data.get("track_metrics", {})
                    if track_metrics:
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Total Distance", f"{track_metrics.get('distance_km')} km")
                        m2.metric("Elevation Gain", f"+{track_metrics.get('total_ascent')} m")
                        m3.metric("Max Altitude", f"{track_metrics.get('max_altitude')} m")

                    st.divider()

                    planning = res_data.get("planning_tools", {})
                    weather = planning.get("weather_forecast", {})
                    if weather and weather.get("status") == "Success":
                        st.subheader("🌤️ Tactical Weather Forecast")

                        advice = weather.get("safety_advice", {})
                        if advice:
                            st.info(f"**{advice.get('status')}**: {advice.get('message')}")
                            st.caption(f"Gear Suggestion: {advice.get('gear_advice')}")

                        forecast_list = weather.get("tactical_forecast", [])
                        if forecast_list:
                            import pandas as pd
                            chart_data = []
                            for f in forecast_list:
                                chart_data.append({
                                    "Time": f["time"],
                                    "Temp (°C)": float(f["temp"].replace("°C", "")),
                                    "Rain Prob (%)": float(f["rain_prob"].replace("%", ""))
                                })
                            df_weather = pd.DataFrame(chart_data).set_index("Time")
                            st.line_chart(df_weather, height=250)

                    nutrition = planning.get("nutrition_plan", {}).get("mission_nutrition_briefing", {})
                    if nutrition:
                        with st.expander("🥣 Nutrition & Hydration Plan", expanded=True):
                            n1, n2, n3 = st.columns(3)

                            fluids = nutrition.get("fluids", {})
                            n1.metric("Total Fluids", f"{fluids.get('total_liters')} L", f"{fluids.get('hourly_average_ml')} ml/h")

                            carbs = nutrition.get("carbohydrates", {})
                            n2.metric("Carbohydrates", f"{carbs.get('total_grams')} g", f"{carbs.get('hourly_target_g')} g/h")

                            sodium = nutrition.get("electrolytes", {})
                            n3.metric("Sodium (Salt)", f"{sodium.get('total_sodium_mg')} mg", f"{sodium.get('hourly_sodium_mg')} mg/h")

                    st.divider()

                    col_climb, col_perf = st.columns(2)

                    with col_climb:
                        st.subheader("🏔️ Climb Analysis (UCI)")
                        climbs = res_data.get("climb_analysis", [])
                        if climbs:
                            climb_df = []
                            for c in climbs:
                                climb_df.append({
                                    "Start (km)": c["km_start"],
                                    "Length (km)": c["dist_km"],
                                    "Grade (%)": c["avg_grade"],
                                    "Cat": c["category"]
                                })
                            st.table(climb_df)

                    with col_perf:
                        st.subheader("⚡ Performance Simulation")
                        sims = res_data.get("performance_simulation", [])
                        if sims:
                            sim_df = []
                            for s in sims:
                                sim_df.append({
                                    "Sector": s["climb"].split("@")[0].strip(),
                                    "VAM": s["est_vam"],
                                    "W/kg": s["target_wkg"],
                                    "Time (min)": s["est_time_min"]
                                })
                            st.dataframe(sim_df, hide_index=True)

                    st.divider()

                    t_zones = res_data.get("tactical_action_zones", [])
                    if t_zones:
                        with st.expander("🎯 Tactical Action Zones (Walls & Descents)"):
                            for zone in t_zones:
                                icon = "🧨" if "Wall" in zone["type"] else "⛷️"
                                color = "red" if zone["difficulty"] == "high" else "orange" if zone["difficulty"] == "medium" else "blue"
                                st.markdown(f"**{icon} KM {zone['km']}**: {zone['type']} (Grade: :{color}[{zone['grade']}%])")

                    report_path = res_data.get("report_path")
                    if report_path and os.path.exists(report_path):
                        with open(report_path, "rb") as file:
                            st.download_button(
                                label="📥 Download Full Tactical PDF Report",
                                data=file,
                                file_name=os.path.basename(report_path),
                                mime="application/pdf",
                                type="primary"
                            )

                except Exception as e:
                    st.error(f"Error while parsing GPX: {str(e)}")