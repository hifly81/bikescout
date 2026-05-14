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
        "description": "TODO"
    },
    "Llama-3.1-8B-Instruct": {
        "repo": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "file": "Meta-Llama-3.1-8B-Instruct-Q6_K.gguf",
        "description": "TODO"
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

    st.subheader("🔑 Configuration")
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
    with st.status("Executing Analysis...", expanded=True) as status:
        try:
            data = json.loads(raw_llm_json)
            st.sidebar.write("Raw Tool Call:", data)
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

                current_query = args.get("location") or args.get("start") or args.get("location_name")

                if current_query:
                    st.session_state["last_location_query"] = current_query
                    location_query = current_query
                else:
                    location_query = st.session_state.get("last_location_query")

                st.sidebar.write("location_query:", location_query)
                st.sidebar.write("current_query:", current_query)

                geo = geocode_location(location_name=location_query)

                args["latitude"] = geo.lat
                args["longitude"] = geo.lon

                include_gpx = include_args(args, 'gpx')
                include_altimetry = include_args(args, 'altimetry')

                raw_distance = ext_cast(args.get("distance") or args.get("total_length_km"), float, 25.0)
                if raw_distance:
                    if raw_distance > 1000:
                        raw_distance = raw_distance / 1000
                        st.session_state["last_raw_distance"] = raw_distance
                else:
                    raw_distance = st.session_state.get("last_raw_distance")

                st.sidebar.write("raw_distance:", raw_distance)

                raw_bike = str(args.get("bike_type") or args.get("bike") or "mtb").lower()
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
                    "tire_size": str(args.get("tire_size") or args.get("wheel_size")),
                    "include_weather": bool(args.get("include_weather") or args.get("go_no_go")),
                    "include_mud_analysis": bool(args.get("include_mud_analysis") or args.get("go_no_go")),
                    "include_nutrition_plan": bool(args.get("include_nutrition_plan")),
                    "include_poi": bool(args.get("include_poi") or args.get("amenities")),
                    "include_gpx": include_gpx,
                    "include_map": bool(args.get("include_map") or args.get("map")),
                    "include_altimetry": include_altimetry,
                    "weight_kg": ext_cast(args.get("weight_kg") or args.get("weight") or args.get("user_weight") or args.get("rider_weight") or args.get("user_type"), float, 75.0),
                    "gender": str(args.get("gender") or args.get("sex") or args.get("user_gender") or 'male'),
                    "seed": random.randint(1, 999999),
                    "bike_type": final_bike,
                    "is_ebike": is_ebike,
                    "fitness_level": str(args.get("fitness") or args.get("fitness_level")),
                }

                result = trail_scout_simple(**valid_args)

                with st.expander("Debug Data"):
                    c1, c2 = st.columns(2)
                    c1.json({"input_args": valid_args})
                    c2.json({"raw_response": result.model_dump() if hasattr(result, 'model_dump') else str(result)})

                status.update(label="Mission Briefing Ready", state="complete")
                return "TODO"

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