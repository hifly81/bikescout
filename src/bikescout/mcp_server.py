import os
import sys
from dotenv import load_dotenv
from fastmcp import FastMCP
from bikescout.schemas import RiderProfile, BikeSetup, MissionConstraints
from bikescout.tools.scouting import get_complete_trail_scout
from bikescout.tools.weather import get_weather_forecast
from bikescout.tools.surface import get_surface_analyzer
from bikescout.tools.geocoding import get_coordinates
from bikescout.tools.poi import get_poi_scout
from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.strava import get_strava_activity
from bikescout.tools.gonogo import calculate_ride_windows
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
    """
    data = get_mud_risk_analysis(lat, lon, surface_type)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def analyze_strava_activity(activity_date: str):
    """
    Analyzes a past Strava activity by date (format: YYYY-MM-DD).
    Extracts real GPS data to provide a tactical post-ride report,
    including surface breakdown and historical mud validation.
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


# --- RESOURCES SECTION ---

@mcp.resource("bikescout://safety/checklist")
def get_safety_checklist() -> str:
    """Returns the essential pre-ride safety checklist."""
    return BikeScoutResources.SAFETY_CHECKLIST

@mcp.resource("bikescout://tech/tire-pressure")
def get_tire_pressure_guide() -> str:
    """Basic guide for tire pressures."""
    return BikeScoutResources.TIRE_PRESSURE_GUIDE


if __name__ == "__main__":
    mcp.run()