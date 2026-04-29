# BikeScout - Tactical Intelligence for Cyclists
# Copyright (C) 2026 hifly81 (https://github.com/hifly81/bikescout)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import os
import sys
import json
from dotenv import load_dotenv
from fastmcp import FastMCP
from pathlib import Path
from typing import Literal, Optional
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
from bikescout.tools.race.analysis import analyze_track
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
def geocode_location(location_name: str, language: str = "en"):
    """
    Finds latitude and longitude for any place name (city, mountain pass, address).
    Use this BEFORE other tools if you only have a location name and not coordinates.

    Args:
        location_name: The natural language name of the location (e.g., "Stelvio Pass").
        language: header Accept-Language , e.g. en,it,fr,es
    """
    data = get_coordinates(location_name, language)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def trail_scout(
        latitude: float,
        longitude: float,
        rider: RiderProfile,
        bike: BikeSetup,
        mission: MissionConstraints,
        dest_latitude: Optional[float] = None,
        dest_longitude: Optional[float] = None,
        include_gpx: bool = True,
        include_map: bool = False,
        style: Literal["sparkline", "filled", "bars"] = "filled",
        output_level: Literal["summary", "standard", "full"] = "standard",
        target_date: Optional[str] = None
):
    """
    Advanced trail discovery.
    Returns route data, difficulty, a GPX file, and a URI with the altimetry report.
    that can be displayed directly in the chat.
    Supports both single-point Round Trips and A->B separate destinations.
    If target_date is None, it defaults to the current date.

    Args:
        latitude: Latitude of the starting point.
        longitude: Longitude of the starting point.
        rider: Profile including weight and fitness level.
        bike: Setup details including bike type and tire width.
        mission: Constraints like search radius and surface preference.
        dest_latitude: Latitude of the ending point.
        dest_longitude: Longitude of the ending point.
        include_gpx: If True, generates a GPX file for navigation.
        include_map: If True, generates a visual map image.
        style: Visual style of the profile "sparkline", "filled", "bars".
        output_level: Detail level of the report ("summary", "standard", "full").
        target_date: Optional. The date of the event in YYYY-MM-DD format.
    """

    data = get_complete_trail_scout(
        ORS_API_KEY, latitude, longitude, rider, bike, mission, dest_latitude, dest_longitude, include_gpx, include_map, style, output_level, target_date)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def trail_scout_simple(
        latitude: float,
        longitude: float,
        # --- Rider Profile (Flat) ---
        weight_kg: float = 75.0,
        fitness_level: Literal["beginner", "intermediate", "pro"] = "intermediate",
        # --- Bike Setup (Flat) ---
        bike_type: Literal['mtb', 'road', 'gravel', 'e-mtb', 'enduro'] = "mtb",
        tire_size: Literal["32", "29", "27.5", "700c", "650b"] = "29",
        is_ebike: bool = False,
        battery_wh: int = 625,
        # --- Mission Constraints (Flat) ---
        radius_km: int = 30,
        profile: Literal["cycling-mountain", "cycling-road", "cycling-regular", "cycling-electric"] = "cycling-mountain",
        surface_preference: Literal["neutral", "prefer_paved", "avoid_unpaved"] = "neutral",
        complexity: int = 3,
        seed: int = 42,
        assist_mode: Literal["Eco", "Trail", "Boost"] = "Eco",
        dest_latitude: Optional[float] = None,
        dest_longitude: Optional[float] = None,
        # --- Output Options ---
        include_gpx: bool = True,
        include_map: bool = True,
        style: Literal["sparkline", "filled", "bars"] = "filled",
        output_level: Literal["summary", "standard", "full"] = "standard"
):
    """
    Simplified tactical scout for cycling routes.
    Use this for quick route generation with sensible defaults.
    Only lat and lon are strictly required.
    """
    try:
        # Internal reconstruction of validated Pydantic models
        # This preserves all the validation logic (like e-bike battery checks)
        rider = RiderProfile(
            weight_kg=weight_kg,
            fitness_level=fitness_level
        )

        bike = BikeSetup(
            bike_type=bike_type,
            tire_size=tire_size,
            is_ebike=is_ebike,
            battery_wh=battery_wh
        )

        mission = MissionConstraints(
            radius_km=radius_km,
            profile=profile,
            surface_preference=surface_preference,
            complexity=complexity,
            seed=seed,
            assist_mode=assist_mode
        )

        # Call the core logic (reusing the existing trail_scout logic)
        return trail_scout(
            latitude=latitude,
            longitude=longitude,
            rider=rider,
            bike=bike,
            mission=mission,
            dest_latitude=dest_latitude,
            dest_longitude=dest_longitude,
            include_gpx=include_gpx,
            include_map=include_map,
            style=style,
            output_level=output_level
        )

    except Exception as e:
        return {"status": "Error", "message": f"Trail Scout Simple failed: {str(e)}"}

@mcp.tool()
def check_trail_weather(lat: float, lon: float, target_date: Optional[str] = None):
    """
    Advanced cycling-specific weather assistant for real-time and future planning.
    Provides temperature, rain risk, and wind speed analysis.

    If target_date is provided, it analyzes the forecast for that specific day
    (ideal for race planning like Tour de France stages or MTB World Cup).
    If target_date is None, it defaults to the current 4-hour window.

    Args:
        lat: Latitude of the trail area.
        lon: Longitude of the trail area.
        target_date: Optional. The date of the event in YYYY-MM-DD format.
    """
    # Now passing the optional target_date to the underlying weather engine
    data = get_weather_forecast(lat, lon, target_date)

    return {
        "payload_version": BIKESCOUT_PROTOCOL_VERSION,
        **data
    }

@mcp.tool()
def ride_window_planner(
        lat: float,
        lon: float,
        ride_duration_hours: float = 2.0,
        surface_type: Literal["dirt", "gravel", "asphalt", "sand", "clay"] = "dirt",
        target_date: Optional[str] = None
):
    """
    Tactical Go/No-Go Planner.
    Predicts the best riding window by cross-referencing weather stability
    and TAEL soil drainage efficiency for the next 12-24 hours.
    If target_date is None, it defaults to the current date.

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.
        ride_duration_hours: Planned time for the cycling session.
        surface_type: Type of ground (e.g., "dirt", "gravel", "asphalt") to calculate drying lag.
        target_date: Optional. The date of the event in YYYY-MM-DD format.
    """

    data = calculate_ride_windows(lat, lon, ride_duration_hours, surface_type, target_date)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def analyze_route_surfaces(
    lat: float,
    lon: float,
    rider: RiderProfile,
    bike: BikeSetup,
    mission: MissionConstraints,
    target_date: Optional[str] = None,
):
    """
    Analyzes the route surface, technical difficulty, categorize climbs,
    and provides dynamic mechanical setup (PSI/Bar) based on terrain and weight.
    If target_date is None, it defaults to the current date.

    Args:
        lat: Latitude of the center point.
        lon: Longitude of the center point.
        rider: Profile of the cyclist.
        bike: Current bicycle configuration.
        mission: Route requirements and radius.
        target_date: Optional. The date of the event in YYYY-MM-DD format.
    """
    data = get_surface_analyzer(
        ORS_API_KEY,
        lat,
        lon,
        rider,
        bike,
        mission,
        target_date
    )
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}


@mcp.tool()
def poi_scout(lat: float, lon: float, radius_km: int = 2):
    """
    Identifies bike-specific points of interest (POIs) around a location.
    Focuses on water fountains, bike shops, repair stations, and shelters.

    Args:
        lat: Latitude of the center point (usually start/end or a climb peak).
        lon: Longitude of the center point.
        radius_km: Search radius in kilometers. Max: 2km.
    """
    data = get_poi_scout(ORS_API_KEY, lat, lon, radius_km)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def check_trail_soil_condition(
        lat: float,
        lon: float,
        surface_type: Literal["dirt", "gravel", "asphalt", "sand", "clay"] = "dirt",
        target_date: Optional[str] = None
):
    """
    Advanced predictive and historical model for ground saturation and mud risk.
    Uses the TAEL (Terrain-Aware Evaporation Lag) algorithm to cross-reference
    cumulative 72h precipitation with drying efficiency factors.

    This tool is essential for:
    1. Pre-ride planning: Assessing trail conditions for today.
    2. Race strategy: Predicting mud risk for future dates (e.g., upcoming GPX tracks).

    Args:
        lat: Latitude of the target trail or sector.
        lon: Longitude of the target trail or sector.
        surface_type: Ground material (e.g., "clay", "gravel") to calculate specific drainage lag.
        target_date: Optional. The specific date to analyze (YYYY-MM-DD).
                     Defaults to today's date if not provided.
    """
    # Executes the core TAEL logic with dynamic date windowing
    data = get_mud_risk_analysis(lat, lon, surface_type, target_date)

    return {
        "payload_version": BIKESCOUT_PROTOCOL_VERSION,
        **data
    }

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
def elevation_profile_image(geometry: RouteGeometry, width: int = 8, height: int = 3, style: Literal["sparkline", "filled", "bars"] = "filled"):
    """
    Generates a visual elevation profile image amd return a URI with the altimetry report.

    This tool transforms raw elevation data into a color-coded graph:
    - Green: Flat/Easy (<3%)
    - Yellow: Moderate (4-7%)
    - Red: Steep/HC climbs (>8%)

    Args:
        geometry: The coordinates and elevation data (typically from trail_scout).
        width: Visual width in inches (default 8).
        height: Visual height in inches (default 3).
        style: Visual style of the profile "sparkline", "filled", "bars".
    """

    data = get_elevation_profile_image(geometry=geometry, width=width, height=height, style=style)
    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

@mcp.tool()
def hydration_scout(
        lat: float,
        lon: float,
        duration_hours: float = 2,
        intensity_score: int = 3,
        target_date: Optional[str] = None
):
    """
    Physiological Intelligence Engine.
    Calculates a specific nutrition and hydration plan by cross-referencing
    weather data (heat/humidity) with predicted mission intensity.

    If target_date is None, it defaults to the current window.
    For future dates, it analyzes the predicted race-day thermal peak.

    Args:
        lat: Latitude of the mission area.
        lon: Longitude of the mission area.
        duration_hours: Estimated time in the saddle.
        intensity_score: Physiological effort (1 to 5) 5 = Max Effort/Race.
        target_date: Optional. The date of the event in YYYY-MM-DD format.
    """
    # 1. Fetch weather context using the updated forecast engine
    # This now supports both real-time and future dates
    weather_data = get_weather_forecast(lat, lon, target_date)

    # 2. Extract peak temperature from the tactical forecast window
    # Default to 20°C if weather data is unavailable
    max_temp = 20.0

    # We now look for 'tactical_forecast' (the new key in our updated weather tool)
    forecast = weather_data.get("tactical_forecast", [])

    if forecast:
        try:
            # We parse the temperature strings (e.g., "24.5°C" -> 24.5)
            # and find the maximum expected during the ride window
            temps = [float(h["temp"].replace("°C", "")) for h in forecast]
            max_temp = max(temps)
        except (ValueError, KeyError, TypeError):
            # Fallback to the reference condition if list parsing fails
            ref_cond = weather_data.get("reference_conditions", {})
            max_temp = float(ref_cond.get("temp", 20.0))

    # 3. Execute the Nutrition Logic
    # The engine calculates carbs/hour and ml/hour based on heat and intensity
    data = get_nutrition_plan(duration_hours, max_temp, intensity_score)

    return {
        "payload_version": BIKESCOUT_PROTOCOL_VERSION,
        "weather_context": {
            "date_referenced": weather_data.get("metadata", {}).get("date_analyzed", target_date),
            "max_temp_detected": f"{max_temp}°C",
            "is_future_event": weather_data.get("metadata", {}).get("is_future_planning", False)
        },
        **data
    }

@mcp.tool()
def analyze_gpx_track(
        gpx_url: str,
        rider_weight_kg: float,
        bike_weight_kg: float = 7.5,
        pro_intensity: float = 1.6,
        activity_type: Literal["road", "mtb"] = "road",
        target_date: Optional[str] = None,
        start_hour: Optional[int] = None,
        end_hour: Optional[int] = None,
        report: bool = False
):
    """
    Performs a high-fidelity professional audit of a GPX race track.
    Calculates UCI climb categories, VAM, W/kg requirements, and crosswind (echelon) risks.
    Integrates predictive weather, mud risk, and nutrition planning.

    Args:
        gpx_url: Remote URL or local path of the GPX file to analyze.
        rider_weight_kg: Body mass of the rider for Power-to-Weight calculations.
        bike_weight_kg: Mass of the bike (default 7.5kg for pro road bikes).
        pro_intensity: Effort multiplier (1.0 = amateur, 1.6 = pro pace, 2.0 = world-class attack).
        activity_type: Type of activity ('road' or 'mtb').
        target_date: Optional race date (YYYY-MM-DD). If provided, fetches historical or forecast weather.
        start_hour: Expected start time (0-23). If provided with end_hour, calculates window-averaged metrics.
        end_hour: Expected finish time (0-23). Used to average weather conditions during the event.
        report: True or False, geenarte a pdf report with the analysis.
    """

    data = analyze_track(
            gpx_url=gpx_url,
            rider_weight_kg=rider_weight_kg,
            bike_weight_kg=bike_weight_kg,
            pro_intensity=pro_intensity,
            activity_type=activity_type,
            target_date=target_date,
            start_hour=start_hour,
            end_hour=end_hour,
            report=report
    )

    return {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}

# --- SKILLS SECTION

BASE_DIR = Path(__file__).parent.absolute() / "prompts"

@mcp.resource("bikescout://world-knowledge")
def get_world_knowledge() -> str:
    """
    Central index for all tactical regions.
    """
    if not BASE_DIR.exists():
        return "Directory not found."

    resource_list = []
    for file in BASE_DIR.glob("*.md"):
        slug = file.stem.replace("explore-", "")
        resource_list.append({
            "uri": f"bikescout://knowledge/{slug}",
            "name": f"Tactical Guide: {slug.replace('-', ' ').title()}",
            "mimeType": "text/markdown"
        })
    return json.dumps(resource_list, indent=2)

@mcp.resource("bikescout://knowledge/{region}")
def get_specific_knowledge(region: str) -> str:
    """
    Fetches the actual markdown content.
    """
    target_slug = region.lower().replace("-", "").replace("_", "")

    for file in BASE_DIR.glob("*.md"):
        file_name_clean = file.stem.lower().replace("explore-", "").replace("-", "").replace("_", "")

        if target_slug == file_name_clean:
            return file.read_text(encoding="utf-8")

    return f"Data for {region} not found."

@mcp.resource("bikescout://altimetry/{filename}")
def serve_altimetry_image(filename: str) -> bytes:
    file_path = Path.home() / ".bikescout" / "altimetry" / filename
    if not file_path.exists():
        raise FileNotFoundError("Altimetry not found.")
    return file_path.read_bytes()

@mcp.resource("bikescout://maps/{filename}")
def serve_map_image(filename: str) -> bytes:
    file_path = Path.home() / ".bikescout" / "maps" / filename
    if not file_path.exists():
        raise FileNotFoundError("Map not found.")
    return file_path.read_bytes()

@mcp.resource("bikescout://gpx/{filename}")
def serve_gpx(filename: str) -> bytes:
    file_path = Path.home() / ".bikescout" / "gpx" / filename
    if not file_path.exists():
        raise FileNotFoundError("GPX not found.")
    return file_path.read_bytes()

@mcp.tool()
def apply_safety_protocol(
        mission_type: Literal["mtb", "ebike", "road", "gravel", "general"]
):
    """
    Executes the official BikeScout Safety Protocol.

    This tool provides a mandatory safety checklist and risk assessment.
    It MUST be called before finalizing any 'Go' decision.
    The protocol adapts based on the terrain and bike mechanics.

    Args:
        mission_type: Category of ride to tailor the safety checklist.
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
def get_baseline_mechanics(bike_category: Literal["mtb", "ebike", "road", "gravel", "general"]):
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

import os

def main():
    """
    Main entry point for the BikeScout MCP Server.
    Supports both 'stdio' for local clients
    and 'sse' for remote deployments/web interfaces.
    """
    # Use environment variable to choose the transport, defaulting to stdio
    transport_mode = os.getenv("BIKESCOUT_TRANSPORT", "stdio").lower()

    if transport_mode == "sse":
        # Remote mode: Requires a host and port (defaulting to 0.0.0.0 for Docker/Cloud)
        host = os.getenv("BIKESCOUT_HOST", "0.0.0.0")
        port = int(os.getenv("BIKESCOUT_PORT", 8000))

        print(f"Starting BikeScout MCP Server in SSE mode on {host}:{port}")
        mcp.run(transport='sse', host=host, port=port)
    else:
        # Local mode: Standard I/O transport
        mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
