import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from bikescout.tools.scouting import get_complete_trail_scout
from bikescout.tools.weather import get_weather_forecast
from bikescout.tools.surface import get_surface_analyzer
from bikescout.tools.geocoding import get_coordinates

# Initialize the MCP Server
mcp = FastMCP("BikeScout")

load_dotenv()

ORS_API_KEY = os.getenv("ORS_API_KEY")

if not ORS_API_KEY:
    raise ValueError("ORS_API_KEY not found.")

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
def analyze_route_surfaces(lat: float, lon: float, radius_km: int = 10, profile: str = "cycling-mountain"):
    """
    Provides a detailed breakdown of the terrain types (e.g., % of gravel, asphalt, dirt).
    Useful for choosing the right bike for the route.
    """
    return get_surface_analyzer(ORS_API_KEY, lat, lon, radius_km, profile)

if __name__ == "__main__":
    mcp.run()