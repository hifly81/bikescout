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

# --- PROMPTS SECTION ---

@mcp.prompt("explore-moab-usa")
def explore_moab():
    """Expert guide for Moab, Utah - The MTB Mecca."""
    return """
    Act as a professional MTB guide specialized in the Moab, Utah desert area.

    Context: Moab is famous for its 'Slickrock' (sandstone) and technical trails like 'The Whole Enchilada' or 'Slickrock Trail'.
    The climate is arid and terrain can be punishing for both rider and gear.

    Instructions:
    1. Use the 'trail_scout' tool to look for trails in 'Moab, Utah'.
    2. Analyze the weather forecast to warn about heat or wind.
    3. Recommend specific gear: high tire pressure for rocks, extra hydration (3L+), and tubeless kits.
    4. Provide the response in the user's preferred language, but keep the technical trail names in English.
    """

@mcp.prompt("explore-castelli-romani-italy")
def explore_castelli():
    """Local guide for the Castelli Romani (Albano/Nemi Lakes), Italy."""
    return """
    Act as a local Italian MTB expert for the Castelli Romani Regional Park (Colli Albani).

    Context: This volcanic area near Rome offers 'peperino' rock segments, loose volcanic soil, and ancient Roman roads (like Via Appia Antica).
    Iconic spots: Monte Cavo (downhill/enduro), Lake Nemi (XC/Gravel), and the 'Canalone'.

    Instructions:
    1. Use the 'geocode_location' and 'trail_scout' tools for 'Rocca di Papa' or 'Monte Cavo'.
    2. Focus on the vertical gain (elevation) as these volcanic climbs are short but steep.
    3. Suggest a post-ride 'Fraschetta' stop in Ariccia for the local cycling culture experience.
    4. Provide the response in the user's preferred language.
    """

@mcp.resource("bikescout://safety/checklist")
def get_safety_checklist() -> str:
    """Returns the essential pre-ride safety checklist."""
    return """
    ### 🛡️ BikeScout Safety Checklist
    1. **M-Check**: Check hubs, bottom bracket, and headset for play.
    2. **Brakes**: Ensure pads have life and levers don't touch the bars.
    3. **Tires**: Check for cuts and ensure correct pressure.
    4. **Chain**: Clean and lubed?
    5. **Emergency**: Do you have a multi-tool, pump, and spare tube?
    6. **Helmet**: Buckle it up!
    """

@mcp.resource("bikescout://tech/tire-pressure")
def get_tire_pressure_guide() -> str:
    """Basic guide for tire pressures."""
    return """
    ### 🚲 Tire Pressure Recommendations (Tubeless)
    - **Road (28mm)**: 4.5 - 5.5 Bar (65-80 PSI)
    - **Gravel (40mm)**: 2.0 - 3.0 Bar (30-45 PSI)
    - **MTB (2.3")**: 1.4 - 1.8 Bar (20-26 PSI)
    *Note: Add 0.3 Bar if using inner tubes.*
    """

if __name__ == "__main__":
    mcp.run()