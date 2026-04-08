import os
from mcp.server.fastmcp import FastMCP
from src.tools.scouting import get_complete_trail_scout
from src.tools.weather import get_weather_forecast
from src.tools.surface import get_surface_analyzer

# Initialize the MCP Server
mcp = FastMCP("BikeScout")

ORS_API_KEY = "YOUR_OPENROUTE_SERVICE_API_KEY"

@mcp.tool()
def trail_scout(lat: float, lon: float, radius_km: int = 10, profile: str = "cycling-mountain"):
    """
    Finds real trail names from OpenStreetMap and calculates a full route with GPX.
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