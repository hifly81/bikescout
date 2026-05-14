import streamlit as st
import os
import time
import json
import re
import random
import pprint
from typing import Dict, Any
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
try:
    from bikescout.mcp_server import (
        geocode_location,
        trail_scout_simple
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
        font-weight: 900; /* font-black */
        font-style: italic; /* italic */
        text-transform: uppercase; /* uppercase */
        letter-spacing: -0.05em; /* tracking-tighter */
        color: white;
    }

    .neon-text {
        color: #bef264; 
        text-shadow: 0 0 5px #bef264;, 0 0 10px #bef264; 
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
        n_gpu_layers=n_gpu_layers, # -1 for all layers on GPU, 0 for CPU
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

                    # Direct fetch from HuggingFace Hub
                    hf_hub_download(
                        repo_id=AVAILABLE_MODELS[selected_model_name]["repo"],
                        filename=AVAILABLE_MODELS[selected_model_name]["file"],
                        local_dir=LOCAL_MODELS_DIR,
                        local_dir_use_symlinks=False
                    )
                    status.update(label="Download Complete! .", state="complete")
                    st.rerun() # Refresh to load the newly acquired model
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

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Connection established. Local LLM initialized. Provide parameters."}
    ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def include_args(args, input_msg: str):
    arg_key = next((k for k in args.keys() if input_msg in k.lower()), None)
    arg_value = args.get(arg_key, False) if arg_key else False
    include_arg = str(arg_value).lower() in ['true', '1', 't', 'y', 'yes', 'on']
    return include_arg

def ext_cast(val, to_type, default):
    """
    Extracts numbers from messy strings (e.g., '25 km' -> 25)
    and converts to the desired type.
    """
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
    """
    The 'Tactical Dispatcher' - JSON Native Version.
    Directly parses structured intelligence to execute Python tools and render UI.
    """
    with (st.status("Executing Analysis...", expanded=True) as status):
        try:
            clean_json_str = raw_llm_json.strip()
            if clean_json_str.startswith("```json"):
                clean_json_str = clean_json_str[7:-3].strip()
            elif clean_json_str.startswith("```"):
                clean_json_str = clean_json_str[3:-3].strip()

            data = json.loads(clean_json_str)
            #st.sidebar.write("Inspector", data)
            briefing_text = data.get("briefing", "Analysis complete.")
            can_execute = data.get("can_execute", False)
            tool_data = data.get("tool")

            if not can_execute:
                return briefing_text

            if not tool_data:
                status.update(label="Analysis Complete", state="complete")
                return briefing_text

            tool_name = tool_data.get("name")
            args = tool_data.get("args", {})

            if tool_name == "trail_scout_simple":
                def get_val(obj, key, default=None):
                    if isinstance(obj, dict): return obj.get(key, default)
                    return getattr(obj, key, default)

                current_query = args.get("location_name")

                if current_query:
                    st.session_state["last_location_query"] = current_query
                    location_query = current_query
                else:
                    location_query = st.session_state.get("last_location_query")

                #st.sidebar.write("location_query:", location_query)
                #st.sidebar.write("current_query:", current_query)

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

                #st.sidebar.write("raw_distance:", raw_distance)

                raw_bike = str(args.get("bike_type")).lower()
                is_ebike = False
                if any(word in raw_bike for word in ["electric", "e-mtb", "emtb", "ebike"]):
                    final_bike = "e-mtb"
                    is_ebike = True
                elif "road" in raw_bike in raw_bike:
                    final_bike = "road"
                elif "gravel" in raw_bike:
                    final_bike = "gravel"
                elif "enduro" in raw_bike or "downhill" in raw_bike:
                    final_bike = "enduro"
                else:
                    final_bike = "mtb"

                valid_args = {
                    "latitude": float(args.get("latitude")),
                    "longitude": float(args.get("longitude")),
                    "total_length_km": raw_distance,
                    "tire_size": str(args.get("tire_size")),
                    "include_weather": bool(args.get("include_weather") or args.get("go_no_go")),
                    "include_mud_analysis": bool(args.get("include_mud_analysis") or args.get("go_no_go")),
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

                result = trail_scout_simple(**valid_args)
                res_data = result.model_dump() if hasattr(result, 'model_dump') else result

                #with st.expander("Debug Data"):
                    #c1, c2 = st.columns(2)
                    #c1.json({"input_args": valid_args})
                    #c2.json({"raw_response": res_data})

                status.update(label="Briefing Ready", state="complete")

                info = res_data.get("info", {})
                surface_analysis = info.get("surface_analysis", {})
                tactical_briefing = surface_analysis.get("tactical_briefing", {})
                logistics = res_data.get("logistics", {})
                conditions = res_data.get("conditions", {})

                dist = info.get("distance_km", "N/A")
                elev = info.get("ascent_m", "N/A")
                diff = info.get("difficulty", "N/A")

                climb_category = tactical_briefing.get("climb_category", "N/A")
                avg_gradient = tactical_briefing.get("avg_gradient", "N/A")
                avg_climb_gradient = tactical_briefing.get("avg_climb_gradient", "N/A")

                mechanical = surface_analysis.get("mechanical_setup", {})
                setup_details_list = mechanical.get("setup_details", [])
                setup_text = setup_details_list[1] if len(setup_details_list) > 1 else "Standard Setup"

                max_temp = conditions.get("max_temp_detected", "N/A")

                st.markdown(f"### 📍 Route Deployed: {dist} km")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Distance", f"{dist} km")
                m2.metric("Ascent", f"{elev} m")
                m3.metric("Difficulty", diff.split('(')[0].strip() if isinstance(diff, str) else diff)
                m4.metric("Avg Gradient", f"{avg_gradient}")

                briefing_md = f"**⚙️ Tactical Setup:** {setup_text}\n\n"
                briefing_md += f"**🏔️ Climb Profile:** {climb_category} (Avg climb gradient: {avg_climb_gradient})\n\n"
                briefing_md += f"**🌡️ Peak Temp:** {max_temp}\n\n"

                st.markdown(briefing_md)

                if surface_analysis:
                    surfaces = surface_analysis.get("surface_breakdown", [])
                    if surfaces:
                        with st.expander("🛣️ Surface Breakdown"):
                            for s in surfaces:
                                st.write(f"- **{s.get('type', 'Unknown')}**: {s.get('percentage', '0%')}")

                weather_data = None
                if conditions:
                    weather_data = conditions.get("weather", [])

                if weather_data and isinstance(weather_data, list):
                    with st.expander("🌤️ Tactical Weather Forecast"):

                        def clean_unit(text):
                            if not text: return "N/A"
                            text = str(text)
                            for unit in ["°C", "%%", "mm", "km/h"]:
                                if text.count(unit) > 1:
                                    text = text.replace(unit + unit, unit)
                            return text

                        chart_data = []
                        for w in weather_data:
                            try:
                                t_val = float(str(w.get('temp')).encode('ascii', 'ignore').decode('ascii').replace('C', '').strip())
                                r_val = float(str(w.get('rain_prob')).replace('%', '').strip())
                                chart_data.append({
                                    "Ora": w.get("time"),
                                    "Temp (°C)": t_val,
                                    "Rain Prob (%)": r_val
                                })
                            except:
                                continue

                        w_col1, w_col2, w_col3 = st.columns(3)
                        if chart_data:
                            max_t = max([d["Temp (°C)"] for d in chart_data])
                            max_r = max([d["Rain Prob (%)"] for d in chart_data])
                            w_col1.metric("Peak Temp", f"{max_t} °C")
                            w_col2.metric("Max Rain Prob", f"{max_r} %")

                        if conditions.get("safety_advice"):
                            w_col3.metric("Safety Advice", conditions.get("safety_advice", "Clear")[:20] + "...")

                        st.divider()

                        if chart_data:
                            st.write("**Temperature & Rain Probability Trend**")
                            import pandas as pd
                            df_weather = pd.DataFrame(chart_data).set_index("Ora")
                            st.line_chart(df_weather, height=250)

                        st.divider()

                        weather_table = []
                        for w in weather_data:
                            weather_table.append({
                                "Time": w.get("time"),
                                "Temp": clean_unit(w.get("temp")),
                                "Apparent": clean_unit(w.get("app_temp")),
                                "Rain %": clean_unit(w.get("rain_prob")),
                                "Rain mm": clean_unit(w.get("rain_mm")),
                                "Wind": clean_unit(w.get("wind")),
                                "Gusts": clean_unit(w.get("gusts"))
                            })

                        st.dataframe(weather_table, use_container_width=True, hide_index=True)

                        if conditions.get("safety_advice"):
                            st.warning(f"**Security Note:** {conditions.get('safety_advice')}")

                mud_data = None
                if conditions:
                    mud_data = conditions.get("mud_risk", {})

                if mud_data:
                    tactical_mud = mud_data.get("tactical_analysis", {})
                    env_context = mud_data.get("environmental_context", {})

                    with st.expander("🛡️ Terrain & Environmental Intelligence"):
                        m_col1, m_col2, m_col3 = st.columns(3)

                        risk_score = tactical_mud.get("mud_risk_score", "Unknown")
                        risk_color = "🟢" if risk_score == "Low" else "🟡" if risk_score == "Moderate" else "🔴"

                        m_col1.metric("Mud Risk", f"{risk_color} {risk_score}")
                        m_col2.metric("Dry Time ETA", tactical_mud.get("dry_time_eta", "N/A"))
                        m_col3.metric("Rain (72h)", f"{env_context.get('total_rain_72h_mm')} mm")

                        st.divider()

                        t1, t2 = st.columns(2)

                        traction = tactical_mud.get("traction_risk", {})
                        with t1:
                            st.write("**🛞 Traction Analysis**")
                            t_level = traction.get("level", "N/A")
                            t_advice = traction.get("advice", "")
                            if t_level == "Low":
                                st.success(f"Risk: {t_level} - {t_advice}")
                            else:
                                st.warning(f"Risk: {t_level} - {t_advice}")

                        damage = tactical_mud.get("trail_damage_risk", {})
                        with t2:
                            st.write("**🌳 Trail Integrity**")
                            d_level = damage.get("level", "N/A")
                            d_advice = damage.get("advice", "")
                            if d_level == "Low":
                                st.info(f"Damage Risk: {d_level} - {d_advice}")
                            else:
                                st.error(f"Damage Risk: {d_level} - {d_advice}")

                        st.caption(f"Model: {mud_data.get('metadata', {}).get('model')} | Timezone: {mud_data.get('metadata', {}).get('timezone')}")

                pois = None
                if logistics:
                    pois = logistics.get("nearby_amenities")
                if pois:
                    with st.expander("💧 Logistics & POIs"):
                        for poi in pois:
                            name = poi.get("name", "Unknown POI")
                            dist_poi = poi.get("distance_m", "N/A")
                            poi_type = poi.get("type", "")
                            st.write(f"- **{name}** ({poi_type}) at {dist_poi}m")

                nutrition = None
                if logistics:
                    nutrition = logistics.get("nutrition_plan", {})
                if nutrition:
                    briefing_nut = nutrition["mission_nutrition_briefing"]

                    with st.expander("🥣 Tactical Nutrition & Fueling"):
                        n_col1, n_col2, n_col3 = st.columns(3)

                        fluids = briefing_nut.get("fluids", {})
                        n_col1.metric("Total Fluids", f"{fluids.get('total_liters')} L")
                        n_col1.caption(f"Avg: {fluids.get('hourly_average_ml')} ml/h")

                        carbs = briefing_nut.get("carbohydrates", {})
                        n_col2.metric("Total Carbs", f"{carbs.get('total_grams')} g")
                        n_col2.caption(f"Target: {carbs.get('hourly_target_g')} g/h ({carbs.get('intensity_context')})")

                        electro = briefing_nut.get("electrolytes", {})
                        n_col3.metric("Total Sodium", f"{electro.get('total_sodium_mg')} mg")
                        n_col3.caption(f"Target: {electro.get('hourly_sodium_mg')} mg/h")

                        st.divider()

                        advice_list = briefing_nut.get("tactical_advice", [])
                        if advice_list:
                            st.markdown("**🛡️ Fueling Strategy:**")
                            for advice in advice_list:
                                st.info(advice)

                map_uri = res_data.get("map_path")
                alt_uri = res_data.get("elevation_profile_path")

                if map_uri or alt_uri:
                    st.divider()
                    v1, v2 = st.columns(2)

                    if map_uri:
                        with v1:
                            st.image(map_uri, caption="Tactical Map")

                    if alt_uri:
                        with v2:
                            st.image(alt_uri, caption="Elevation Profile")

                gpx_path = res_data.get("gpx_export_path")
                if gpx_path and os.path.exists(gpx_path):
                    try:
                        with open(gpx_path, "rb") as file:
                            btn = st.download_button(
                                label="📥 Download Tactical GPX",
                                data=file,
                                file_name="mission.gpx",
                                mime="application/gpx+xml"
                            )
                    except Exception as e:
                        st.error(f"Could not load GPX file for download: {e}")

                return briefing_text

        except json.JSONDecodeError:
            status.update(label="Format Error", state="error")
            st.error("The AI generated a non-compliant JSON string.")
            st.code(raw_llm_json)
            return "Mission Aborted: Intelligence format corrupted."

        except Exception as e:
            status.update(label="Critical Failure", state="error")
            st.error(f"Engine Fault: {str(e)}")
            return f"Strategic error during execution: {str(e)}"

    return briefing_text

# --- CHAT INPUT ---
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