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
from bikescout.schemas import RiderProfile, BikeSetup, MissionConstraints, RouteSurfaceResponse, MechanicalBaselineResponse, SafetyProtocolResponse, GpxRaceAuditResponse, WeatherContext, HydrationScoutResponse, StrategicPlannerResponse, TacticalForecastResponse, FullMissionBriefingResponse, GeocodingResponse
from bikescout.tools.scouting import get_complete_trail_scout
from bikescout.tools.weather import get_weather_forecast
from bikescout.tools.geocoding import get_coordinates
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
BASE_DIR = Path(__file__).parent.absolute() / "prompts"
ORS_API_KEY = os.getenv("ORS_API_KEY")

if not ORS_API_KEY:
    print("Error: ORS_API_KEY is not set.", file=sys.stderr)
    print("Please set the ORS_API_KEY environment variable or add it to your .env file.", file=sys.stderr)
    print("You can get a free key at https://openrouteservice.org/", file=sys.stderr)
    sys.exit(1)


# --- TOOLS SECTION ---

@mcp.tool()
def geocode_location(location_name: str, language: str = "en") -> GeocodingResponse:
    """
    Finds latitude and longitude for any place name (city, mountain pass, address).
    Use this BEFORE other tools if you only have a location name and not coordinates.

    Args:
        location_name: The natural language name of the location (e.g., "Stelvio Pass").
        language: header Accept-Language , e.g. en,it,fr,es
    Returns:
        A GeocodingResponse containing:
        - lat/lon: Precise coordinates for routing.
        - display_name: The formal name used for the mission report.
        - importance: A score indicating the reliability of the match.
        - place_class/type: Contextual info to distinguish between cities, peaks, or regions.
    """
    data = get_coordinates(location_name, language)
    return GeocodingResponse(payload_version=BIKESCOUT_PROTOCOL_VERSION, **data)

@mcp.tool()
def trail_scout(
        latitude: float,
        longitude: float,
        rider: RiderProfile,
        bike: BikeSetup,
        mission: MissionConstraints,
        dest_latitude: Optional[float] = None,
        dest_longitude: Optional[float] = None,
        style: Literal["sparkline", "filled", "bars"] = "filled",
        target_date: Optional[str] = None,
        include_gpx: bool = True,
        include_map: bool = False,
        include_surface_analysis: bool = False,
        include_poi: bool = False,
        include_altimetry: bool = False,
        include_weather: bool = False,
        include_mud_analysis: bool = False,
        include_nutrition_plan: bool = False
) -> FullMissionBriefingResponse:
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
        style: Visual style of the profile "sparkline", "filled", "bars".
        target_date: Optional. The date of the event in YYYY-MM-DD format.
        include_gpx: If True, generates a GPX file for navigation.
        include_map: If True, generates a visual map image.
        include_surface_analysis: If True, generates surface analysis report.
        include_poi: If True, includes amenities and points of interest.
        include_altimetry: If True, generates the altimetry profile.
        include_weather: If True, includes weather conditions.
        include_mud_analysis: If True, generates a report including mud analysis.
        include_nutrition_plan: If True, generates nutrition plan report.
    Returns:
        FullMissionBriefingResponse: A comprehensive tactical intelligence report containing:
        - info: Route metrics (distance, ascent, difficulty) and deep surface analysis
          (TAEL© mud risk, traction levels, and mechanical/PSI recommendations).
        - conditions: Hourly weather forecast for the specific cycling window,
          including rain probability, wind gusts, and safety gear advice.
        - logistics: A complete nutrition/hydration plan based on rider effort and
          nearby water fountains or amenities detected along the trail.
        - map_path & mcp_resource_uri_map: The visual map asset (PNG) and its URI
          for rendering in the chat interface.
        - gpx_export_path & mcp_resource_uri_gpx: The tactical navigation file
          and its resource reference.
        - elevation_profile_path & mcp_resource_uri_elevation_profile: The visual
          altimetry report (PNG) in the requested 'style'.
        - gpx_stats: Technical summary of the generated trace (point count, healed segments).
    """

    data = get_complete_trail_scout(
        ORS_API_KEY, latitude, longitude, rider, bike, mission, dest_latitude, dest_longitude,
        style, target_date, include_gpx, include_map,
        include_surface_analysis, include_poi, include_altimetry, include_weather, include_mud_analysis, include_nutrition_plan)
    return FullMissionBriefingResponse(payload_version=BIKESCOUT_PROTOCOL_VERSION, **data)

@mcp.tool()
def trail_scout_simple(
        latitude: float,
        longitude: float,
        weight_kg: float = 75.0,
        fitness_level: Literal["beginner", "intermediate", "pro"] = "intermediate",
        bike_type: Literal['mtb', 'road', 'gravel', 'e-mtb', 'enduro'] = "mtb",
        tire_size: Literal["32", "29", "27.5", "700c", "650b"] = "29",
        is_ebike: bool = False,
        battery_wh: int = 625,
        radius_km: int = 30,
        profile: Literal["cycling-mountain", "cycling-road", "cycling-regular", "cycling-electric"] = "cycling-mountain",
        surface_preference: Literal["neutral", "prefer_paved", "avoid_unpaved"] = "neutral",
        complexity: int = 3,
        seed: int = 42,
        assist_mode: Literal["Eco", "Trail", "Boost"] = "Eco",
        dest_latitude: Optional[float] = None,
        dest_longitude: Optional[float] = None,
        style: Literal["sparkline", "filled", "bars"] = "filled",
        include_gpx: bool = True,
        include_map: bool = False,
        include_surface_analysis: bool = False,
        include_poi: bool = False,
        include_altimetry: bool = False,
        include_weather: bool = False,
        include_mud_analysis: bool = False,
        include_nutrition_plan: bool = False
) -> FullMissionBriefingResponse:
    """
    Simplified tactical scout for cycling routes.
    Use this for quick route generation with sensible defaults.
    Only lat and lon are strictly required.

    Args:
        latitude: Latitude of the starting point.
        longitude: Longitude of the starting point.
        weight_kg: Rider's weight in kilograms (default: 75.0). Used for energy and nutrition math.
        fitness_level: Rider's stamina level ("beginner", "intermediate", "pro").
        bike_type: Type of bicycle to optimize the mechanical and tactical advice.
        tire_size: Wheel/tire diameter for specific pressure (PSI) recommendations.
        is_ebike: Set to True if using a pedelec/e-bike to enable battery analysis.
        battery_wh: Battery capacity in Watt-hours (default: 625).
        radius_km: Maximum search radius for round trips in kilometers.
        profile: Routing engine profile (e.g., 'cycling-mountain' for trails, 'cycling-road' for asphalt).
        surface_preference: Bias towards paved or unpaved roads.
        complexity: Route complexity factor (1-5). Higher values allow more turns and technical segments.
        seed: Random seed for route generation consistency.
        assist_mode: E-bike motor support level (affects range estimation).
        dest_latitude: Optional. Latitude of the finish line (for A-to-B missions).
        dest_longitude: Optional. Longitude of the finish line (for A-to-B missions).
        style: Visual style for the elevation profile graphic.
        include_gpx: If True, generates a downloadable navigation file.
        include_map: If True, generates a tactical map image.
        include_surface_analysis: If True, generates surface analysis report.
        include_poi: If True, includes amenities and points of interest.
        include_altimetry: If True, generates the altimetry profile.
        include_weather: If True, includes weather conditions.
        include_mud_analysis: If True, generates a report including mud analysis.
        include_nutrition_plan: If True, generates nutrition plan report.
    Returns:
        FullMissionBriefingResponse: A comprehensive tactical intelligence report containing:
        - info: Route metrics (distance, ascent, difficulty) and deep surface analysis
          (TAEL© mud risk, traction levels, and mechanical/PSI recommendations).
        - conditions: Hourly weather forecast for the specific cycling window,
          including rain probability, wind gusts, and safety gear advice.
        - logistics: A complete nutrition/hydration plan based on rider effort and
          nearby water fountains or amenities detected along the trail.
        - map_path & mcp_resource_uri_map: The visual map asset (PNG) and its URI
          for rendering in the chat interface.
        - gpx_export_path & mcp_resource_uri_gpx: The tactical navigation file
          and its resource reference.
        - elevation_profile_path & mcp_resource_uri_elevation_profile: The visual
          altimetry report (PNG) in the requested 'style'.
        - gpx_stats: Technical summary of the generated trace (point count, healed segments).
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
        data = trail_scout(
            latitude=latitude,
            longitude=longitude,
            rider=rider,
            bike=bike,
            mission=mission,
            dest_latitude=dest_latitude,
            dest_longitude=dest_longitude,
            style=style,
            include_gpx=include_gpx,
            include_map=include_map,
            include_surface_analysis = include_surface_analysis,
            include_poi = include_poi,
            include_altimetry = include_altimetry,
            include_weather = include_weather,
            include_mud_analysis = include_mud_analysis,
            include_nutrition_plan = include_nutrition_plan
        )

        return FullMissionBriefingResponse(payload_version=BIKESCOUT_PROTOCOL_VERSION, **data)

    except Exception as e:
        return {"status": "Error", "message": f"Trail Scout Simple failed: {str(e)}"}

@mcp.tool()
def check_trail_weather(lat: float, lon: float, target_date: Optional[str] = None) -> TacticalForecastResponse:
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
    Returns:
        A TacticalForecastResponse containing:
        - status: API operation status.
        - metadata: Contextual data (date, timezone, location).
        - tactical_forecast: Hourly breakdown of temp, rain probability, and wind.
        - reference_conditions: Aggregated metrics for the analysis window.
        - safety_advice: Crucial briefing on wind risk scores and recommended gear.
    """
    # Now passing the optional target_date to the underlying weather engine
    data = get_weather_forecast(lat, lon, target_date)
    return TacticalForecastResponse(payload_version=BIKESCOUT_PROTOCOL_VERSION, **data)

@mcp.tool()
def ride_window_planner(
        lat: float,
        lon: float,
        ride_duration_hours: float = 2.0,
        surface_type: Literal["dirt", "gravel", "asphalt", "sand", "clay"] = "dirt",
        target_date: Optional[str] = None
) -> StrategicPlannerResponse:
    """
    Tactical Go/No-Go Planner.
    Predicts the best riding window by cross-referencing weather stability
    and TAEL® soil drainage efficiency for the next 12-24 hours.
    If target_date is None, it defaults to the current date.

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.
        ride_duration_hours: Planned time for the cycling session.
        surface_type: Type of ground (e.g., "dirt", "gravel", "asphalt") to calculate drying lag.
        target_date: Optional. The date of the event in YYYY-MM-DD format.
    Returns:
        A StrategicPlannerResponse containing:
        - metadata: Contextual info including the solar window (sunrise/sunset).
        - planner_report: The final 'GO/NO-GO' verdict with a tactical risk color.
        - environmental_briefing: Summary of average rain, wind, and temp for the window.
        - best_window: The identified optimal time range for the activity.
        - mud_risk_impact: The percentage of mission success affected by soil saturation.
    """

    data = calculate_ride_windows(lat, lon, ride_duration_hours, surface_type, target_date)
    return StrategicPlannerResponse(payload_version=BIKESCOUT_PROTOCOL_VERSION, **data)

@mcp.tool()
def hydration_scout(
        lat: float,
        lon: float,
        duration_hours: float = 2,
        intensity_score: int = 3,
        target_date: Optional[str] = None
) -> HydrationScoutResponse:
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
    Returns:
        A HydrationScoutResponse containing the tactical weather context and
        the complete nutrition briefing (fluids, carbs, electrolytes).
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

    context = WeatherContext(
        date_referenced=weather_data.get("metadata", {}).get("date_analyzed", target_date),
        max_temp_detected=f"{max_temp}°C",
        is_future_event=weather_data.get("metadata", {}).get("is_future_planning", False)
    )

    return HydrationScoutResponse(
        payload_version=BIKESCOUT_PROTOCOL_VERSION,
        weather_context=context,
        **data
    )

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
) -> GpxRaceAuditResponse:
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
    Returns:
        A GpxRaceAuditResponse object containing:
        - track_metrics: Core distance and elevation data.
        - planning_tools: Predictive weather, nutrition strategy, and mud risk analysis.
        - climb_analysis: Detailed UCI categorization of all climbs.
        - performance_simulation: Estimated times, VAM, and W/kg per sector.
        - tactical_alerts: Positioning warnings, echelon risks, and attack points.
        - report_path: Local URI to the generated PDF document (if requested).
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

    return GpxRaceAuditResponse(payload_version=BIKESCOUT_PROTOCOL_VERSION,**data)

# --- SKILLS SECTION

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
) -> SafetyProtocolResponse:
    """
    Executes the official BikeScout Safety Protocol.

    This tool provides a mandatory safety checklist and risk assessment.
    It MUST be called before finalizing any 'Go' decision.
    The protocol adapts based on the terrain and bike mechanics.

    Args:
        mission_type: Category of ride to tailor the safety checklist.

    Returns:
        A SafetyProtocolResponse with markdown checklists and tactical commands.
    """

    base = BikeScoutResources.BASE_COMMANDS
    extra = BikeScoutResources.EXTRA_PROTOCOLS.get(mission_type.lower(), [])

    final_commands = base + extra

    data = {
        "mission_type_applied": mission_type,
        "standard_checklist": BikeScoutResources.SAFETY_CHECKLIST,
        "tactical_pre_ride_commands": final_commands,
        "status": "Success"
    }

    return SafetyProtocolResponse(
        payload_version=BIKESCOUT_PROTOCOL_VERSION,
        **data
    )

@mcp.tool()
def get_baseline_mechanics(bike_category: Literal["mtb", "ebike", "road", "gravel", "general"]) -> MechanicalBaselineResponse:
    """
    Provides baseline tire pressure and mechanical settings from the BikeScout Registry.
    Categories: 'road', 'gravel', 'mtb'.
    Use this as a starting point before applying 'analyze_route_surfaces'.

    Returns:
        A MechanicalBaselineResponse containing the recommended setup (PSI/Bar),
        a full markdown guide for different bike types, and tactical setup notes.
    """
    category = bike_category.lower()

    baseline = BikeScoutResources.PRESSURE_DATA.get(category)

    if not baseline:
        return {
            "status": "Error",
            "message": f"Category '{bike_category}' not recognized. Use 'road', 'gravel', or 'mtb'.",
            "available_categories": list(BikeScoutResources.PRESSURE_DATA.keys())
        }

    data = {
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

    return MechanicalBaselineResponse(payload_version=BIKESCOUT_PROTOCOL_VERSION, **data)


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
