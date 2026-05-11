import streamlit as st
import os
import time
import json
import re
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
    "Hermes-3-Llama-3.1-8B": {
        "repo": "NousResearch/Hermes-3-Llama-3.1-8B-GGUF",
        "file": "Hermes-3-Llama-3.1-8B.Q4_K_M.gguf",
        "description": "State-of-the-art for tool use and long-context planning. Highly creative yet precise."
    },
    "Llama-3-8B": {
        "repo": "MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF",
        "file": "Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf",
        "description": "Meta's flagship - Great for complex reasoning."
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
    .stChatMessage { border-radius: 15px; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
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
        n_ctx=4096,
        n_gpu_layers=n_gpu_layers, # -1 for all layers on GPU, 0 for CPU
        verbose=False
    )

def generate_tactical_response(user_input: str, llm_instance: Llama) -> str:

    system_prompt = """
    You are the BikeScout Tactical AI, a rugged assistant for mountain bikers and cyclists.
    Your mission is to convert user requests into specific tool calls.
    CRITICAL RULE: Never use 'None' or 'null' in arguments.
    
    STRATEGY:
    1. If the user provides a location NAME (e.g., 'Roma', 'Stelvio') but NO coordinates:
       YOU MUST CALL: geocode_location(location_name="NAME")
    
    2. ONLY if you have numerical latitude and longitude, call:
       trail_scout_simple(latitude, longitude, total_length_km, bike_type)
       
    AVAILABLE TOOLS:
    1. geocode_location(location_name: str) -> Use this for place names (e.g. 'Stelvio').
    2. trail_scout_simple(latitude, longitude, total_length_km, bike_type) -> Use for routing.

    OUTPUT FORMAT:
    You must respond with your brief tactical assessment first, then a single line:
    TOOL: {"name": "tool_name", "args": {"arg1": "val1"}}
    
    If no tool is needed, just reply normally.
    """

    prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
    prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{user_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

    output = llm_instance(
        prompt,
        max_tokens=512,
        stop=["<|eot_id|>", "User:"],
        temperature=0.2 # Lower temp = more reliable JSON
    )

    return output["choices"][0]["text"].strip()

# --- SIDEBAR: SETTINGS, MODELS & API CONFIG ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3198/3198336.png", width=100)
    st.title("BikeScout")
    st.divider()

    st.subheader("🔑 Configuration")
    existing_key = os.getenv("ORS_API_KEY", "")
    # Secure text input for the OpenRouteService API Key
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
        st.info("💡 Pro Tip: Configure an ORS key.")

    st.divider()

    st.subheader("🧠 LLM Models")
    selected_model_name = st.selectbox(
        "Select Local LLM",
        options=list(AVAILABLE_MODELS.keys()),
        help="Models are executed locally on your hardware for maximum privacy."
    )

    st.caption(AVAILABLE_MODELS[selected_model_name]["description"])

    # GPU acceleration toggle
    gpu_enabled = st.toggle("GPU Acceleration", value=True, help="Enable this for faster reasoning speed.")
    n_layers = -1 if gpu_enabled else 0

    model_path = get_local_model_path(selected_model_name)

    if not os.path.exists(model_path):
        if st.button(f"Download {selected_model_name}", use_container_width=True):
            with st.status("Initializing secure download...", expanded=True) as status:
                st.write("☕ *Wait, downloading the model...*")
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
st.title("🚴 BikeScout")
st.markdown(f"##### LLM Active: `{selected_model_name}`")
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

def process_local_mcp_request(raw_llm_text: str, user_input: str):
    """
    The 'Tactical Dispatcher'.
    Parses LLM output via Regex, sanitizes arguments for specific tools,
    automatically resolves missing coordinates, and executes core Python tools.
    """
    with st.status("Deploying Tools...", expanded=True) as status:
        # Quick Exit: If the LLM didn't flag a tool call, return the raw text
        if "TOOL:" not in raw_llm_text:
            status.update(label="BikeScout response", state="complete")
            return raw_llm_text

        try:
            json_match = re.search(r'\{.*\}', raw_llm_text, re.DOTALL)

            if not json_match:
                status.update(label="Parsing Error", state="error")
                return f"⚠️ Error: LLM requested a tool but provided invalid syntax.\n\nRaw Output: {raw_llm_text}"

            tool_json_str = json_match.group(0).replace("'", '"')
            tool_data = json.loads(tool_json_str)

            tool_name = tool_data.get("name")
            args = tool_data.get("args", {})

            is_trail_request = tool_name == "trail_scout_simple"
            missing_coords = args.get("latitude") in [None, "None"] or args.get("longitude") in [None, "None"]

            if is_trail_request and (missing_coords or "location_name" in args):
                st.info("⚠️ Error: Coordinates missing ...")

                # Determine what to search for: prioritize 'location_name', fallback to user prompt
                search_query = args.get("location_name") or user_input
                geo_result = geocode_location(location_name=search_query)

                args["latitude"] = geo_result.lat
                args["longitude"] = geo_result.lon
                args.pop("location_name", None)
                st.success(f"📍 Location: {geo_result.display_name}")

            st.write(f"⚙️ *Processing parameters for `{tool_name}`...*")
            time.sleep(0.5)

            if tool_name == "geocode_location":
                valid_args = {k: v for k, v in args.items() if k in ['location_name', 'language']}
                result = geocode_location(**valid_args)

                st.success(f"📍 Location: {result.display_name}")
                args["latitude"] = result.lat
                args["longitude"] = result.lon
                tool_name = "trail_scout_simple"

            if tool_name == "trail_scout_simple":
                try:
                    def cast(val, to_type, default):
                        if val is None or val == "": return default
                        try:
                            if to_type == bool:
                                return str(val).lower() in ['true', '1', 't', 'y', 'yes']
                            return to_type(val)
                        except: return default

                    def get_val(obj, key, default=None):
                        if isinstance(obj, dict):
                            return obj.get(key, default)
                        return getattr(obj, key, default)

                    raw_bike = str(args.get("bike_type", "mtb")).lower()
                    if "29" in raw_bike:
                        bike_type, tire_size = "mtb", "29"
                    elif any(x in raw_bike for x in ["ebike", "e-mtb", "electric"]):
                        bike_type, is_ebike = "e-mtb", True
                    else:
                        bike_type = raw_bike if raw_bike in ['mtb', 'road', 'gravel', 'e-mtb', 'enduro'] else "mtb"
                        tire_size = str(args.get("tire_size", "29"))

                    valid_args = {
                        "latitude": cast(args.get("latitude"), float, 0.0),
                        "longitude": cast(args.get("longitude"), float, 0.0),
                        "weight_kg": cast(args.get("weight_kg"), float, 75.0),
                        "gender": args.get("gender") if args.get("gender") in ['male', 'female'] else "male",
                        "sweat_profile": args.get("sweat_profile") if args.get("sweat_profile") in ["standard", "low", "high", "extreme"] else "standard",
                        "fitness_level": args.get("fitness_level") if args.get("fitness_level") in ["beginner", "intermediate", "pro"] else "intermediate",
                        "bike_type": bike_type,
                        "tire_size": tire_size if tire_size in ["32", "29", "27.5", "700c", "650b"] else "29",
                        "is_ebike": cast(args.get("is_ebike"), bool, ("e-mtb" in bike_type)),
                        "battery_wh": cast(args.get("battery_wh"), int, 625),
                        "assist_mode": args.get("assist_mode") if args.get("assist_mode") in ["Eco", "Trail", "Boost"] else "Eco",
                        "total_length_km": cast(args.get("total_length_km"), int, 30),
                        "profile": args.get("profile") if args.get("profile") in ["cycling-mountain", "cycling-road", "cycling-regular", "cycling-electric"] else "cycling-mountain",
                        "surface_preference": args.get("surface_preference", "neutral"),
                        "complexity": cast(args.get("complexity"), int, 3),
                        "seed": cast(args.get("seed"), int, 42),
                        "dest_latitude": cast(args.get("dest_latitude"), float, None),
                        "dest_longitude": cast(args.get("dest_longitude"), float, None),
                        "style": args.get("style", "filled"),
                        "include_gpx": cast(args.get("include_gpx"), bool, True),
                        "include_map": cast(args.get("include_map"), bool, True),
                        "include_poi": cast(args.get("include_poi"), bool, False),
                        "include_altimetry": cast(args.get("include_altimetry"), bool, True),
                        "include_weather": cast(args.get("include_weather"), bool, True),
                        "include_mud_analysis": cast(args.get("include_mud_analysis"), bool, True),
                        "include_nutrition_plan": cast(args.get("include_nutrition_plan"), bool, False)
                    }

                    # --- 4.5 MISSION PARAMETERS LOG (UI DEBUG) ---
                    with st.expander("🛠️ Mission Configuration Details (Debug)"):
                        c1, c2, c3, c4 = st.columns(4)

                        with c1:
                            st.markdown("**Rider & Bike**")
                            st.write(f"Weight: {valid_args['weight_kg']}kg")
                            st.write(f"Gender: {valid_args['gender']}")
                            st.write(f"Bike: {valid_args['bike_type']} ({valid_args['tire_size']}\")")
                            st.write(f"E-Bike: {'✅' if valid_args['is_ebike'] else '❌'}")

                        with c2:
                            st.markdown("**Tactical Settings**")
                            st.write(f"Fitness: {valid_args['fitness_level']}")
                            st.write(f"Complexity: {valid_args['complexity']}/5")
                            st.write(f"Profile: {valid_args['profile']}")
                            st.write(f"Distance: {valid_args['total_length_km']}km")

                        with c3:
                            st.markdown("**Intelligence Flags**")
                            st.write(f"Weather: {'✅' if valid_args['include_weather'] else '❌'}")
                            st.write(f"Mud Analysis: {'✅' if valid_args['include_mud_analysis'] else '❌'}")
                            st.write(f"Nutrition: {'✅' if valid_args['include_nutrition_plan'] else '❌'}")
                            st.write(f"GPX: {'✅' if valid_args['include_gpx'] else '❌'}")

                        with c4:
                            st.json(valid_args)

                except Exception as e:
                    st.error(f"⚠️ Dispatcher Intelligence Failure: {e}")
                    return "Tactical Error: Parameter mapping failed."

                if valid_args["latitude"] != 0.0:
                    with st.status("🛰️ Analyzing Mission Parameters...", expanded=True) as status:

                        result = trail_scout_simple(**valid_args)

                        # Extract Core Metrics (Handling Pydantic vs Dict)
                        info = get_val(result, 'info')
                        dist = get_val(info, 'distance_km', 0)
                        elev = get_val(info, 'ascent_m', 0)
                        diff = get_val(info, 'difficulty', 'Unknown')

                        briefing = f"### 🗺️ Route Intelligence Report: {dist}km\n"
                        briefing += f"**Metrics:** 📈 {elev}m ascent | 🚩 Difficulty: {diff}\n\n"

                        def resolve_path(uri, local_path):
                            if local_path and os.path.exists(local_path):
                                return local_path
                            if uri:
                                return uri.replace("bikescout://", "/home/hifly/.bikescout/")
                            return None

                        col1, col2 = st.columns(2)

                        with col1:
                            m_path = get_val(result, 'map_path')
                            m_uri = get_val(result, 'mcp_resource_uri_map')
                            map_img = resolve_path(m_uri, m_path)
                            if map_img:
                                st.image(map_img, caption="🛰️ Tactical Map", use_container_width=True)

                        with col2:
                            a_path = get_val(result, 'elevation_profile_path')
                            a_uri = get_val(result, 'mcp_resource_uri_elevation_profile')
                            alt_img = resolve_path(a_uri, a_path)
                            if alt_img:
                                st.image(alt_img, caption="📈 Elevation Profile", use_container_width=True)

                        surface = get_val(info, 'surface_analysis')
                        if surface:
                            with st.expander("🧬 Surface & Mechanical Intel"):
                                mud = get_val(surface, 'mud_intelligence')
                                if mud:
                                    mud_label = get_val(mud, 'label', 'Unknown')
                                    st.write(f"**Mud Risk:** {mud_label}")

                                setup = get_val(surface, 'mechanical_setup')
                                if setup:
                                    raw_details = get_val(setup, 'setup_details', [])
                                    if raw_details:
                                        # This map(str, ...) is the key fix
                                        clean_details = ", ".join(map(str, raw_details))
                                        st.write(f"**Setup Advice:** {clean_details}")

                                    b_type = get_val(setup, 'bike_type')
                                    if b_type:
                                        st.write(f"**Optimized for:** {b_type.upper()}")

                        weather = get_val(result, 'weather_report')
                        if weather:
                            with st.expander("🌤️ Environmental Briefing"):
                                temp = get_val(weather, 'temperature', '--')
                                cond = get_val(weather, 'condition', 'Unknown')
                                wind = get_val(weather, 'wind_speed', '--')

                                st.write(f"**Conditions:** {cond} | **Temp:** {temp}°C")
                                st.write(f"**Wind:** {wind} km/h")

                                verdict = get_val(weather, 'tactical_verdict')
                                if verdict:
                                    st.info(f"**Weather Verdict:** {verdict}")

                        nutrition = get_val(result, 'nutrition_plan')
                        if nutrition:
                            with st.expander("🔋 Fueling & Hydration Plan"):
                                liquids = get_val(nutrition, 'total_liquids_ml', '--')
                                carbs = get_val(nutrition, 'total_carbs_g', '--')

                                st.write(f"**Total Hydration:** {liquids} ml")
                                st.write(f"**Energy Req:** {carbs} g Carbohydrates")

                                strategy = get_val(nutrition, 'strategy_notes', [])
                                if strategy:
                                    st.write("**Tactical Strategy:**")
                                    for note in strategy:
                                        st.write(f"- {note}")

                        gpx_path = get_val(result, 'gpx_export_path')
                        if gpx_path and isinstance(gpx_path, str) and os.path.exists(gpx_path):
                            with open(gpx_path, "rb") as f:
                                st.download_button(
                                    label="💾 Download Tactical GPX",
                                    data=f,
                                    file_name=os.path.basename(gpx_path),
                                    mime="application/gpx+xml",
                                    use_container_width=True
                                )

                        status.update(label="Full Mission Briefing Ready!", state="complete")

                        return briefing
                else:
                    return "❌ Error: Mission coordinates could not be established."

        except json.JSONDecodeError:
            status.update(label="Format Corruption", state="error")
            st.error("Neural Syntax Error: The model output malformed JSON.")
            st.code(raw_llm_text, language="text")
            return "Mission aborted. Intelligence format was non-compliant."

        except Exception as e:
            status.update(label="Tactical Failure", state="error")
            st.error(f"Engine Failure: {str(e)}")
            st.write("Debug - Faulty Arguments:", args)
            return f"Critical error during execution: {str(e)}"

    return raw_llm_text

# --- CHAT INPUT ---
if user_input := st.chat_input("Plan a 30km ride in Milan"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        raw_output = generate_tactical_response(user_input, llm)
        final_briefing = process_local_mcp_request(raw_output, user_input)
        clean_briefing = re.sub(r'(?i)TOOL:.*', '', final_briefing, flags=re.DOTALL)
        st.markdown(clean_briefing.strip())

    st.session_state.messages.append({"role": "assistant", "content": final_briefing})