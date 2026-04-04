import os
from mcp.server.fastmcp import FastMCP
from src.tools.scouting import get_complete_trail_scout
from src.tools.weather import get_weather_forecast

# Initialize the MCP Server
mcp = FastMCP("BikeScout")

ORS_API_KEY = "YOUR_OPENROUTE_SERVICE_API_KEY="

@mcp.tool()
def trail_scout(lat: float, lon: float, radius_km: int = 10, profile: str = "cycling-mountain"):
    """
    Finds real trail names from OpenStreetMap and calculates a full route with GPX.
    """

    return get_complete_trail_scout(ORS_API_KEY, lat, lon, radius_km, profile)

@mcp.tool()
def check_trail_weather(lat: float, lon: float):
    """
    Check weather conditions for a specific trail location.
    Provides temperature, rain probability, and wind for the next 4 hours.
    """
    return get_weather_forecast(lat, lon)

if __name__ == "__main__":
    mcp.run()