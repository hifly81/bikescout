import os
import sys
from dotenv import load_dotenv
from fastmcp import FastMCP
from pathlib import Path
from bikescout.schemas import RiderProfile, BikeSetup, MissionConstraints, RouteGeometry
from bikescout.tools.scouting import get_complete_trail_scout
from bikescout.tools.weather import get_weather_forecast
from bikescout.tools.surface import get_surface_analyzer
from bikescout.tools.geocoding import get_coordinates
from bikescout.tools.poi import get_poi_scout
from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.strava import get_strava_activity
from bikescout.tools.gonogo import calculate_ride_windows
from bikescout.tools.altimetry import get_elevation_profile_image
from bikescout.tools.nutrition import get_nutrition_plan
from bikescout.prompts import BikeScoutPrompts
from bikescout.resources import BikeScoutResources


mcp = FastMCP("BikeScout")
prompts_manager = BikeScoutPrompts()

load_dotenv()

BIKESCOUT_PROTOCOL_VERSION = "1.0"

ORS_API_KEY = os.getenv("ORS_API_KEY")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

if not ORS_API_KEY:
    print("Error: ORS_API_KEY is not set.", file=sys.stderr)
    print("Please set the ORS_API_KEY environment variable or add it to your .env file.", file=sys.stderr)
    print("You can get a free key at https://openrouteservice.org/", file=sys.stderr)
    sys.exit(1)


# --- TOOLS SECTION ---

@mcp.tool()
def geocode_location(location_name: str):
    """
    Finds latitude and longitude for any place name (city, mountain pass, address).
    Use this BEFORE other tools if you only have a location name and not coordinates.

    Args:
        location_name: The natural language name of the location (e.g., "Stelvio Pass").
    """
    data = get_coordinates(location_name)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def trail_scout(
        rider: RiderProfile,
        bike: BikeSetup,
        mission: MissionConstraints,
        lat: float = 41.7615,
        lon: float = 12.7118,
        include_gpx: bool = True,
        include_map: bool = False,
        output_level: str = "standard"  # "summary" | "standard" | "full"
):
    """
    Advanced trail discovery.
    Returns route data, difficulty, a GPX file, and a STATIC MAP IMAGE
    that can be displayed directly in the chat.

    Args:
        rider: Profile including weight and fitness level.
        bike: Setup details including bike type and tire width.
        mission: Constraints like search radius and surface preference.
        lat: Latitude of the starting point.
        lon: Longitude of the starting point.
        include_gpx: If True, generates a downloadable GPX file for navigation.
        include_map: If True, generates a visual static map image.
        output_level: Detail level of the report ("summary", "standard", "full").
    """
    data = get_complete_trail_scout(
        ORS_API_KEY, lat, lon, rider, bike, mission, include_gpx, include_map, output_level)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def check_trail_weather(lat: float = 41.7615, lon: float = 12.7118):
    """
    Detailed cycling-specific weather assistant.
    Provides temperature, rain risk, and wind speed analysis for the next 4 hours,
    including technical safety advice on gear and riding conditions.

    Args:
        lat: Latitude of the trail area.
        lon: Longitude of the trail area.
    """
    data = get_weather_forecast(lat, lon)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def ride_window_planner(
        lat: float = 41.7615,
        lon: float = 12.7118,
        ride_duration_hours: float = 2.0,
        surface_type: str = "dirt"
):
    """
    Tactical Go/No-Go Planner.
    Predicts the best riding window by cross-referencing weather stability
    and TAEL soil drainage efficiency for the next 12-24 hours.

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.
        ride_duration_hours: Planned time for the cycling session.
        surface_type: Type of ground (e.g., "dirt", "gravel", "asphalt") to calculate drying lag.
    """

    data = calculate_ride_windows(lat, lon, ride_duration_hours, surface_type)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def analyze_route_surfaces(
    rider: RiderProfile,
    bike: BikeSetup,
    mission: MissionConstraints,
    lat: float = 41.7615,
    lon: float = 12.7118
):
    """
    Analyzes the route surface, technical difficulty, categorize climbs,
    and provides dynamic mechanical setup (PSI/Bar) based on terrain and weight.

    Args:
        rider: Profile of the cyclist.
        bike: Current bicycle configuration.
        mission: Route requirements and radius.
        lat: Latitude of the center point.
        lon: Longitude of the center point.
    """
    data = get_surface_analyzer(
        ORS_API_KEY,
        lat,
        lon,
        rider,
        bike,
        mission
    )
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}


@mcp.tool()
def poi_scout(lat: float = 41.7615, lon: float = 12.7118, radius_km: int = 5):
    """
    Identifies bike-specific points of interest (POIs) around a location.
    Focuses on water fountains, bike shops, repair stations, and shelters.

    Args:
        lat: Latitude of the center point (usually start/end or a climb peak).
        lon: Longitude of the center point.
        radius_km: Search radius in kilometers (max 5km recommended for precision).
    """
    data = get_poi_scout(ORS_API_KEY, lat, lon, radius_km)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def check_trail_soil_condition(lat: float = 41.7615, lon: float = 12.7118, surface_type: str = "dirt"):
    """
    Advanced predictive model for ground saturation and mud risk.
    Uses the TAEL (Terrain-Aware Evaporation Lag) algorithm to cross-reference
    72h precipitation data with real-time solar altitude and atmospheric drying efficiency.

    Args:
        lat: Latitude of the trail.
        lon: Longitude of the trail.
        surface_type: Ground material to evaluate drying efficiency (e.g., "dirt", "clay").
    """
    data = get_mud_risk_analysis(lat, lon, surface_type)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def analyze_strava_activity(activity_date: str):
    """
    Analyzes a past Strava activity by date (format: YYYY-MM-DD).
    Extracts real GPS data to provide a tactical post-ride report,
    including surface breakdown and historical mud validation.

    Args:
        activity_date: The date of the ride in YYYY-MM-DD format.
    """
    if not all([STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN]):
        return {
            "status": "Error",
            "message": "Strava credentials missing. Please set STRAVA_CLIENT_ID, CLIENT_SECRET and REFRESH_TOKEN."
        }

    data = get_strava_activity(
        activity_date,
        STRAVA_CLIENT_ID,
        STRAVA_CLIENT_SECRET,
        STRAVA_REFRESH_TOKEN
    )
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def elevation_profile_image(geometry: RouteGeometry, width: int = 8, height: int = 3):
    """
    Generates a visual 'sparkline' image (base64 encoded PNG) of the route's elevation profile.

    The plot colors segments based on gradient steepness:
    - Green: Flat/Easy (<3%)
    - Yellow: Moderate (4-7%)
    - Red: Steep Wall (>8%)

    Args:
        geometry: The coordinates and elevation data of the route.
        width: Visual width of the sparkline in inches.
        height: Visual height of the sparkline in inches.
    """
    if not all([STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN]):
        return {
            "status": "Error",
            "message": "Strava credentials missing. Please set STRAVA_CLIENT_ID, CLIENT_SECRET and REFRESH_TOKEN."
        }

    data = get_elevation_profile_image(geometry, width, height)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def hydration_scout(
        lat: float = 41.7615,
        lon: float = 12.7118,
        duration_hours: float = 3,
        intensity_score: int = 50
):
    """
    Physiological Intelligence Engine.
    Calculates a specific nutrition and hydration plan by cross-referencing
    real-time weather (heat/humidity) with predicted mission intensity.

    Args:
        lat: Latitude of the mission area.
        lon: Longitude of the mission area.
        duration_hours: Estimated time in the saddle.
        intensity_score: Physiological effort (0-100).
                         Use <30 for recovery, 50 for standard training,
                         >80 for races or HC climbs.
    """
    # 1. Fetch real-time weather context for the location
    weather_data = get_weather_forecast(lat, lon)

    # 2. Extract peak temperature for the next 4 hours
    # Default to 20°C if weather data is unavailable
    forecast = weather_data.get("next_4_hours", [])
    max_temp = 20.0
    if forecast:
        try:
            temps = [float(h["temp"].replace("°C", "")) for h in forecast]
            max_temp = max(temps)
        except (ValueError, KeyError):
            pass

    # 3. Execute the Nutrition Logic
    data = get_nutrition_plan(duration_hours, max_temp, intensity_score)

    return {
        "payload_version": BIKESCOUT_PROTOCOL_VERSION,
        "weather_context": {"max_temp_detected": f"{max_temp}°C"},
        **data
    }

# --- SKILLS SECTION

@mcp.tool()
def get_local_knowledge(region: str):
    """
    Retrieves high-fidelity tactical intelligence for specific cycling meccas.

    Args:
        region: Name of the cycling destination (e.g., "Dolomites", "Moab", "Finale Ligure").
    """

    current_dir = Path(__file__).parent.absolute()
    base_dir = current_dir / "prompts"

    target_slug = region.lower().replace(" ", "").replace("_", "")

    try:
        if not base_dir.exists():
            return {
                "status": "Error",
                "message": f"Critical Error: 'prompts' directory not found at {base_dir}",
                "debug_current_working_dir": os.getcwd()
            }

        available_files = list(base_dir.glob("*.md"))

        selected_file = None
        for file in available_files:
            # (eg: explore-moab-usa.md -> moab)
            file_name_clean = file.name.lower().replace("-", "").replace("_", "")

            if target_slug in file_name_clean:
                selected_file = file
                break

        if not selected_file:
            return {
                "status": "Error",
                "message": f"Region '{region}' not found in tactical database.",
                "scanned_directory": str(base_dir),
                "available_files": [f.name for f in available_files]
            }

        with open(selected_file, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "payload_version": BIKESCOUT_PROTOCOL_VERSION,
            "region": region,
            "matched_file": selected_file.name,
            "tactical_intelligence": content,
            "status": "Success"
        }

    except Exception as e:
        return {"status": "Error", "message": f"FileSystem Exception: {str(e)}"}

@mcp.tool()
def apply_safety_protocol(mission_type: str = "general"):
    """
    Executes the official BikeScout Safety Protocol.
    Adapts recommendations based on mission_type: 'mtb', 'ebike', 'road', 'gravel'.
    Mandatory skill to call before finalizing any 'Go' decision.

    Args:
        mission_type: Category of ride ("mtb", "ebike", "road", "gravel", or "general").
    """

    base = BikeScoutResources.BASE_COMMANDS
    extra = BikeScoutResources.EXTRA_PROTOCOLS.get(mission_type.lower(), [])

    final_commands = base + extra

    return {
        "payload_version": BIKESCOUT_PROTOCOL_VERSION,
        "mission_type_applied": mission_type,
        "standard_checklist": BikeScoutResources.SAFETY_CHECKLIST,
        "tactical_pre_ride_commands": final_commands,
        "status": "Success"
    }

@mcp.tool()
def get_baseline_mechanics(bike_category: str):
    """
    Provides baseline tire pressure and mechanical settings from the BikeScout Registry.
    Categories: 'road', 'gravel', 'mtb'.
    Use this as a starting point before applying 'analyze_route_surfaces'.
    """
    category = bike_category.lower()

    baseline = BikeScoutResources.PRESSURE_DATA.get(category)

    if not baseline:
        return {
            "status": "Error",
            "message": f"Category '{bike_category}' not recognized. Use 'road', 'gravel', or 'mtb'.",
            "available_categories": list(BikeScoutResources.PRESSURE_DATA.keys())
        }

    return {
        "payload_version": BIKESCOUT_PROTOCOL_VERSION,
        "category": category,
        "recommended_setup": {
            "tire_width_ref": baseline["width"],
            "pressure_bar": baseline["range"],
            "pressure_psi": baseline["psi"]
        },
        "full_guide_reference": BikeScoutResources.TIRE_PRESSURE_GUIDE,
        "setup_notes": BikeScoutResources.MECHANICAL_NOTES,
        "status": "Success"
    }

# --- PROMPTS SECTION ---

def register_dynamic_prompts(mcp_instance, manager):
    for slug, content in manager.prompts_data.items():
        def create_handler(static_content):
            def handler():
                return static_content
            return handler

        mcp_instance.prompt(
            name=slug,
            description=(
                f"SYSTEM_PROMPT: Load this to act as the expert guide for {slug}. "
                "Do not access as a resource. Use this prompt to initialize your "
                "knowledge, tools usage logic, and tactical persona for this region."
            )
        )(create_handler(content))

register_dynamic_prompts(mcp, prompts_manager)


def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()