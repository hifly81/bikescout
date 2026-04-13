import os
import sys
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from bikescout.tools.scouting import get_complete_trail_scout
from bikescout.tools.weather import get_weather_forecast
from bikescout.tools.surface import get_surface_analyzer
from bikescout.tools.geocoding import get_coordinates
from bikescout.tools.poi import get_poi_scout
from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.strava import get_strava_activity
from bikescout.prompts import BikeScoutPrompts
from bikescout.resources import BikeScoutResources


mcp = FastMCP("BikeScout")
prompts_manager = BikeScoutPrompts()

load_dotenv()

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
    return get_coordinates(location_name)

@mcp.tool()
def trail_scout(lat: float = 41.7615, lon: float = 12.7118, radius_km: int = 10, profile: str = "cycling-mountain", rider_weight_kg: float = 80.0):
    """
    Advanced trail discovery.
    Returns route data, difficulty, a GPX file, and a STATIC MAP IMAGE
    that can be displayed directly in the chat.
    """
    return get_complete_trail_scout(ORS_API_KEY, lat, lon, radius_km, profile, rider_weight_kg)

@mcp.tool()
def check_trail_weather(lat: float = 41.7615, lon: float = 12.7118):
    """
    Detailed cycling-specific weather assistant.
    Provides temperature, rain risk, and wind speed analysis for the next 4 hours,
    including technical safety advice on gear and riding conditions.
    """
    return get_weather_forecast(lat, lon)

@mcp.tool()
def analyze_route_surfaces(
    lat: float = 41.7615,
    lon: float = 12.7118,
    radius_km: int = 10,
    profile: str = "cycling-mountain",
    bike_type: str = "MTB",
    tire_size_option: str = "29",
    points: int = 3,
    seed: int = 42,
    surface_preference: str = "neutral",
    rider_weight_kg: float = 80.0
):
    """
    Analyzes the route surface, technical difficulty, categorize climbs,
    and provides dynamic mechanical setup (PSI/Bar) based on terrain and weight.

    Args:
        lat: Latitude of the starting point.
        lon: Longitude of the starting point.
        radius_km: Total target distance for the round-trip loop.
        profile: ORS profile (cycling-mountain, cycling-road, cycling-regular).
        bike_type: Type of bike (MTB, Road, Gravel, E-MTB).
        tire_size_option: Wheel size ('26', '27.5', '29', '700c', '650b').
        rider_weight_kg: Rider weight in kg to normalize tire pressure (default 85kg).
        points: Complexity of the loop shape (3=triangle, 10=circular).
        seed: Random seed to generate different route variations.
    """
    return get_surface_analyzer(
        ORS_API_KEY,
        lat,
        lon,
        radius_km,
        profile,
        bike_type,
        tire_size_option,
        points,
        seed,
        surface_preference,
        rider_weight_kg
    )

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
    return get_poi_scout(ORS_API_KEY, lat, lon, radius_km)

@mcp.tool()
def check_trail_soil_condition(lat: float = 41.7615, lon: float = 12.7118, surface_type: str = "dirt"):
    """
    Advanced predictive model for ground saturation and mud risk.
    Uses the TAEL (Terrain-Aware Evaporation Lag) algorithm to cross-reference
    72h precipitation data with real-time solar altitude and atmospheric drying efficiency.

    Args:
        lat: Latitude of the trail section.
        lon: Longitude of the trail section.
        surface_type: Detected surface (e.g., 'clay', 'dirt', 'gravel', 'sand').
                      Crucial for calculating drainage coefficients.
    """
    return get_mud_risk_analysis(lat, lon, surface_type)

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

    return get_strava_activity(
        activity_date,
        STRAVA_CLIENT_ID,
        STRAVA_CLIENT_SECRET,
        STRAVA_REFRESH_TOKEN
    )

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