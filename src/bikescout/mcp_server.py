import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from bikescout.tools.scouting import get_complete_trail_scout
from bikescout.tools.weather import get_weather_forecast
from bikescout.tools.surface import get_surface_analyzer
from bikescout.tools.geocoding import get_coordinates
from bikescout.prompts import BikeScoutPrompts
from bikescout.resources import BikeScoutResources

# Initialize the MCP Server
mcp = FastMCP("BikeScout")

load_dotenv()

ORS_API_KEY = os.getenv("ORS_API_KEY")

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
def trail_scout(lat: float, lon: float, radius_km: int = 10, profile: str = "cycling-mountain"):
    """
    Advanced trail discovery.
    Returns route data, difficulty, a GPX file, and a STATIC MAP IMAGE
    that can be displayed directly in the chat.
    """
    return get_complete_trail_scout(ORS_API_KEY, lat, lon, radius_km, profile)

@mcp.tool()
def check_trail_weather(lat: float, lon: float):
    """
    Detailed cycling-specific weather assistant.
    Provides temperature, rain risk, and wind speed analysis for the next 4 hours,
    including technical safety advice on gear and riding conditions.
    """
    return get_weather_forecast(lat, lon)

@mcp.tool()
def analyze_route_surfaces(
    lat: float,
    lon: float,
    radius_km: int = 10,
    profile: str = "cycling-mountain",
    bike_type: str = "MTB",
    tire_size_option: str = "29",
    points: int = 3,
    seed: int = 42
):
    """
    Analyzes the route surface, technical difficulty, and bike compatibility.

    Args:
        lat: Latitude of the starting point.
        lon: Longitude of the starting point.
        radius_km: Total target distance for the round-trip loop.
        profile: ORS profile (cycling-mountain, cycling-road, cycling-regular).
        bike_type: Type of bike (MTB, Road, Gravel, E-MTB).
        tire_size_option: For MTB: '26', '27.5', '29'. For Road/Gravel: '700c', '650b'.
        points: Complexity of the loop shape (3=triangle, 10=circular).
        seed: Random seed to generate different route variations for the same area.
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
        seed
    )


# --- PROMPTS SECTION ---

@mcp.prompt("explore-moab-usa")
def explore_moab():
    """Expert guide for Moab, Utah - The MTB Mecca."""
    return BikeScoutPrompts.MOAB_USA

@mcp.prompt("explore-castelli-romani-italy")
def explore_castelli():
    """Local guide for the Castelli Romani (Albano/Nemi Lakes), Italy."""
    return BikeScoutPrompts.CASTELLI_ROMANI

@mcp.prompt("explore-dolomiti-italy")
def explore_dolomiti():
    """Expert guide for cycling in the Dolomites (UNESCO Heritage), Northern Italy."""
    return BikeScoutPrompts.DOLOMITI


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