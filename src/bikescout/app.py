import streamlit as st
import os
import time
import json
import re
from typing import Dict, Any
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
from bikescout.mcp_server import geocode_location, trail_scout_simple, ride_window_planner

# --- CONFIGURATION: LOCAL MODELS ---
# We define high-quality GGUF models available on HuggingFace
AVAILABLE_MODELS = {
    "Llama-3-8B (Balanced)": {
        "repo": "MaziyarPanahi/Llama-3-8B-Instruct-v0.1-GGUF",
        "file": "Llama-3-8B-Instruct-v0.1.Q4_K_M.gguf",
        "description": "Meta's flagship - Great for complex reasoning."
    },
    "Mistral-7B (Fast)": {
        "repo": "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        "file": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "description": "Snappy and reliable for direct tool calling."
    },
    "Phi-3-Mini (Lightweight)": {
        "repo": "microsoft/Phi-3-mini-4k-instruct-gguf",
        "file": "Phi-3-mini-4k-instruct-q4.gguf",
        "description": "Small enough to run on a toaster (almost)."
    }
}

LOCAL_MODELS_DIR = "models"

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="BikeScout Intelligence",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- MODEL MANAGEMENT LOGIC ---
def get_local_model_path(model_name: str) -> str:
    """Returns the local path of the selected model."""
    filename = AVAILABLE_MODELS[model_name]["file"]
    return os.path.join(LOCAL_MODELS_DIR, filename)

@st.cache_resource
def load_llm(model_name: str, n_gpu_layers: int):
    """Loads the GGUF model into memory. Cached to prevent re-loading on every click."""
    path = get_local_model_path(model_name)
    if not os.path.exists(path):
        return None

    # Initialize the local llama-cpp instance
    return Llama(
        model_path=path,
        n_ctx=2048,
        n_gpu_layers=n_gpu_layers, # -1 for all layers on GPU, 0 for CPU
        verbose=False
    )

def generate_tactical_response(user_input: str, llm_instance: Llama) -> str:
    """
    Orchestrates the reasoning phase. It forces the local LLM to follow a strict
    ReAct protocol: Thinking -> Tool Selection -> JSON Arguments.
    """
    # System Prompt: Defining the BikeScout mission rules for the LLM
    system_prompt = """
    You are the BikeScout Tactical AI, a rugged assistant for mountain bikers and cyclists.
    Your mission is to convert user requests into specific tool calls.
    CRITICAL RULE: Never use 'None' or 'null' in arguments.
    
    STRATEGY:
    1. If the user provides a location NAME (e.g., 'Roma', 'Stelvio') but NO coordinates:
       YOU MUST CALL: geocode_location(location_name="NAME")
    
    2. ONLY if you have numerical latitude and longitude, call:
       trail_scout_simple(latitude, longitude, total_length_km, bike_type) or ride_window_planner(lat, lon, surface_type) 
    
    AVAILABLE TOOLS:
    1. geocode_location(location_name: str) -> Use this for place names (e.g. 'Stelvio').
    2. trail_scout_simple(latitude, longitude, total_length_km, bike_type) -> Use for routing.
    3. ride_window_planner(lat, lon, surface_type) -> Use for mud/weather risk.

    OUTPUT FORMAT:
    You must respond with your brief tactical assessment first, then a single line:
    TOOL: {"name": "tool_name", "args": {"arg1": "val1"}}
    
    If no tool is needed, just reply normally.
    """

    # Formatting using Llama-3 special tokens for better instruction following
    prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
    prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{user_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

    # Local Inference: Let the local silicon sweat a bit
    output = llm_instance(
        prompt,
        max_tokens=512,
        stop=["<|eot_id|>", "User:"],
        temperature=0.2 # Lower temp = more reliable JSON
    )

    return output["choices"][0]["text"].strip()

# --- SIDEBAR: SETTINGS & DOWNLOADS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3198/3198336.png", width=100)
    st.title("BikeScout Control")
    st.divider()

    st.subheader("🧠 Intelligence Engine")
    selected_model_name = st.selectbox(
        "Select Local LLM",
        options=list(AVAILABLE_MODELS.keys()),
        help="Models are loaded directly from your local hardware."
    )

    st.caption(AVAILABLE_MODELS[selected_model_name]["description"])

    # GPU acceleration toggle
    gpu_enabled = st.toggle("GPU Acceleration", value=True)
    n_layers = -1 if gpu_enabled else 0

    # Check if we need to download
    model_path = get_local_model_path(selected_model_name)
    if not os.path.exists(model_path):
        st.warning("📥 Model not found on disk.")
        if st.button(f"Download {selected_model_name}", use_container_width=True):
            with st.status("Initializing download...", expanded=True) as status:
                st.write("☕ *Grab a coffee and lube your chain, we're downloading the brain...*")
                try:
                    if not os.path.exists(LOCAL_MODELS_DIR):
                        os.makedirs(LOCAL_MODELS_DIR)

                    hf_hub_download(
                        repo_id=AVAILABLE_MODELS[selected_model_name]["repo"],
                        filename=AVAILABLE_MODELS[selected_model_name]["file"],
                        local_dir=LOCAL_MODELS_DIR,
                        local_dir_use_symlinks=False
                    )
                    status.update(label="Download Complete! Ready for deployment.", state="complete")
                    st.rerun()
                except Exception as e:
                    st.error(f"Mission Failed: {e}")
        st.stop() # Prevent chat interaction until model is ready

    st.divider()
    if st.button("Clear Mission History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- MAIN INTERFACE ---
st.title("🚴 BikeScout Assistant")
st.markdown(f"##### Local Intelligence Active: `{selected_model_name}`")
# IMPORTANT: Load the LLM here so it's available for the rest of the script
llm = load_llm(selected_model_name, n_layers)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Satellite link established. Local LLM initialized. Provide mission parameters."}
    ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def process_local_mcp_request(raw_llm_text: str):
    """
    The 'Tactical Dispatcher'. It parses the LLM output using Regex to avoid
    JSON formatting errors, handles geocoding, and fires the core BikeScout tools.
    """
    with st.status("Deploying Tactical Tools...", expanded=True) as status:
        # 1. Quick Exit: If the LLM didn't flag a tool call, just return the text
        if "TOOL:" not in raw_llm_text:
            status.update(label="Direct Intelligence Briefing", state="complete")
            return raw_llm_text

        try:
            # 2. Robust Parsing: Use Regex to find content between { }
            # Local GGUF models often add trailing garbage that breaks json.loads()
            json_match = re.search(r'\{.*\}', raw_llm_text, re.DOTALL)

            if not json_match:
                status.update(label="Parsing Error", state="error")
                return f"⚠️ Tactical Error: LLM requested a tool but provided invalid syntax.\n\nRaw Output: {raw_llm_text}"

            tool_json_str = json_match.group(0)

            # 3. Clean up common LLM typos (like single quotes instead of double quotes)
            tool_json_str = tool_json_str.replace("'", '"')
            tool_data = json.loads(tool_json_str)

            tool_name = tool_data.get("name")
            args = tool_data.get("args", {})

            # SAFETY CHECK: If the LLM sent 'None' or empty values for coordinates
            # we force a geocoding search using the original user prompt
            needs_geo = False
            if tool_name == "trail_scout_simple":
                lat = args.get("latitude")
                lon = args.get("longitude")
                if lat is None or lon is None or lat == "None":
                    needs_geo = True

            if needs_geo:
                st.info("🛰️ Coordinates missing. Auto-detecting location from context...")
                search_query = args.get("location_name") or user_input
                geo_result = geocode_location(location_name=search_query)
                args["latitude"] = geo_result.lat
                args["longitude"] = geo_result.lon
                st.success(f"📍 Location locked: {geo_result.display_name}")

            # 4. Intelligence Pre-processing: Resolve Location Names to Coordinates
            # If the user mentioned a place name but the tool needs lat/lon
            if "location_name" in args and "latitude" not in args:
                st.write(f"🌍 *Target acquired: `{args['location_name']}`. Synchronizing satellites...*")
                geo_result = geocode_location(location_name=args['location_name'])
                args['latitude'] = geo_result.lat
                args['longitude'] = geo_result.lon
                # Remove the name to avoid passing unexpected args to the next tool
                args.pop('location_name', None)

            st.write(f"⚙️ *Executing mission parameters for `{tool_name}`...*")
            time.sleep(0.8) # Wit: Giving the CPU some 'thinking' credit

            # 5. Routing: Map the JSON intent to the real Python logic in mcp_server
            if tool_name == "geocode_location":
                result = geocode_location(**args)
                status.update(label=f"Location Locked: {result.display_name}", state="complete")
                return f"**Target Coordinates:** `{result.lat}, {result.lon}`\n\n{result.display_name}"

            if tool_name == "trail_scout_simple":
                if args.get("latitude") is None or args.get("latitude") == "None":
                    st.write("🌍 *Coordinates missing. Attempting geocoding...*")
                    geo = geocode_location(location_name=user_input)
                    args["latitude"], args["longitude"] = geo.lat, geo.lon

            st.write(f"⚙️ *Executing `{tool_name}`...*")

            # 3. Execution: Mapping to real tools
            if tool_name == "trail_scout_simple":

                # Ensure boolean/numeric types are correct
                args["include_map"] = True
                args["include_altimetry"] = True
                args["include_gpx"] = True

                # CALL THE TOOL
                result = trail_scout_simple(**args)

                # --- FIX: ATTRIBUTE ACCESS INSTEAD OF DICT KEYS ---
                # result.info is a Pydantic model (RouteInfo), so use .attribute
                dist = result.info.distance_km
                elev = result.info.ascent_m
                diff = result.info.difficulty

                status.update(label="Mission Briefing Ready!", state="complete")

                # Prepare the UI briefing
                briefing = f"### 🗺️ Tactical Mission: {dist}km Loop\n"
                briefing += f"**Metrics:** 📈 {elev}m ascent | 🚩 Difficulty: {diff}\n\n"

                # Display Resources (Images/Files)
                col1, col2 = st.columns(2)
                with col1:
                    st.image(result.mcp_resource_uri_map.replace("bikescout://", "http://localhost:8000/"), caption="Tactical Map")
                with col2:
                    st.image(result.mcp_resource_uri_elevation_profile.replace("bikescout://", "http://localhost:8000/"), caption="Elevation Profile")

                st.download_button("💾 Download Tactical GPX", data=result.gpx_export_path, file_name="mission.gpx")

                return briefing

            elif tool_name == "ride_window_planner":
                from bikescout.mcp_server import ride_window_planner
                result = ride_window_planner(**args)
                status.update(label="Weather/Surface Scan Complete", state="complete")
                return f"**Go/No-Go Verdict:** {result.planner_report['verdict']}\n\n{result.planner_report['reasoning']}"

        except json.JSONDecodeError as je:
            status.update(label="Format Corruption", state="error")
            st.error(f"Neural Syntax Error: The model output malformed JSON.")
            st.code(raw_llm_text, language="text") # Show user the raw output for context
            return "Mission aborted. Intelligence format was non-compliant."

        except Exception as e:
            status.update(label="Tactical Failure", state="error")
            st.error(f"Engine Failure: {str(e)}")
            return "Mission aborted. Internal logic error."

    return raw_llm_text
# --- CHAT INPUT ---
if user_input := st.chat_input("Plan a 30km ride in Milan"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        # Step 1: The Brain thinks and picks a tool
        raw_output = generate_tactical_response(user_input, llm)

        # Step 2: The Dispatcher executes the tool and gives the final report
        final_briefing = process_local_mcp_request(raw_output)

        st.markdown(final_briefing)

        # Add a metric if we have distance data
        if "km" in final_briefing:
            st.metric("Briefing Status", "DATA ACQUIRED", "100%")

    st.session_state.messages.append({"role": "assistant", "content": final_briefing})