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

from __future__ import annotations

import math
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Literal, TypeVar, cast

from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel, ValidationError

from bikescout.schemas import (
    BikeSetup,
    FullMissionBriefingResponse,
    GeocodingResponse,
    GpxRaceAuditResponse,
    HydrationScoutResponse,
    MissionConstraints,
    RiderProfile,
    StrategicPlannerResponse,
    TacticalForecastResponse,
    WeatherContext,
)
from bikescout.tools.bike_setup import (
    default_casing_type,
    default_rim_internal_width_mm,
    default_tire_width_mm,
)
from bikescout.tools.geocoding import get_coordinates
from bikescout.tools.gonogo import calculate_ride_windows
from bikescout.tools.nutrition import get_nutrition_plan
from bikescout.tools.race.analysis import analyze_track
from bikescout.tools.scouting import get_complete_trail_scout
from bikescout.tools.weather import get_weather_forecast

mcp = FastMCP("BikeScout")

load_dotenv()

BIKESCOUT_PROTOCOL_VERSION = "1.0"
ORS_API_KEY = os.getenv("ORS_API_KEY")

ResponseT = TypeVar("ResponseT", bound=BaseModel)


def _error_reason(data: dict[str, Any]) -> str:
    """Extract the diagnostic message from a tool error payload.

    Args:
        data: Raw response dictionary returned by a domain service.

    Returns:
        The cause of the error, or a fallback message when none is provided.
    """
    for key in ("error_message", "message", "error"):
        value = data.get(key)
        if value:
            return str(value)
    return "Tool returned status=Error without a diagnostic message."


def _log_error_details(
    reason: str | None = None,
    exception: BaseException | None = None,
    show_call_stack: bool = True,
    tool_name: str = "BikeScout tool",
) -> None:
    """Print Error diagnostics to stderr.

    Args:
        reason: Human-readable cause of the failure, when known.
        exception: Exception that caused the failure, when available.
        show_call_stack: Print the current call stack when no exception is supplied.
        tool_name: Name of the MCP tool that failed.
    """
    sys.stderr.write(f"{tool_name} failed with status=Error\n")
    if reason:
        sys.stderr.write(f"Reason: {reason}\n")
    if exception is not None:
        traceback.print_exception(
            type(exception), exception, exception.__traceback__, file=sys.stderr
        )
    elif show_call_stack:
        sys.stderr.write("Traceback (most recent call last):\n")
        traceback.print_stack(file=sys.stderr)


def _error_mission_response(
    reason: str | None = None,
    exception: BaseException | None = None,
    tool_name: str = "trail_scout_simple",
) -> FullMissionBriefingResponse:
    """Build an Error response after printing its diagnostics to stderr.

    Args:
        reason: Human-readable cause of the failure, when known.
        exception: Exception that caused the failure, when available.
        tool_name: Name of the MCP tool that failed.

    Returns:
        A FullMissionBriefingResponse with status "Error".
    """
    _log_error_details(reason=reason, exception=exception, tool_name=tool_name)
    return FullMissionBriefingResponse.model_validate(
        {"payload_version": BIKESCOUT_PROTOCOL_VERSION, "status": "Error"}
    )


def _tool_error_response(
    response_model: type[ResponseT],
    tool_name: str,
    data: dict[str, Any] | None = None,
    exception: BaseException | None = None,
) -> ResponseT:
    """Build an Error response after printing its diagnostics to stderr.

    Uses ``model_construct`` because most response schemas require fields that
    are absent from a service error payload.

    Args:
        response_model: Pydantic response class of the MCP tool.
        tool_name: Name of the MCP tool that failed.
        data: Raw error payload returned by the domain service, when available.
        exception: Exception that caused the failure, when available.

    Returns:
        A partially populated response with status "Error".
    """
    reason = _error_reason(data) if data is not None else None
    _log_error_details(reason=reason, exception=exception, tool_name=tool_name)
    if reason and "error_message" in response_model.model_fields:
        return response_model.model_construct(
            payload_version=BIKESCOUT_PROTOCOL_VERSION,
            status="Error",
            error_message=reason,
        )
    return response_model.model_construct(
        payload_version=BIKESCOUT_PROTOCOL_VERSION, status="Error"
    )


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
    try:
        data = get_coordinates(location_name, language)
        if data.get("status") == "Error":
            return _tool_error_response(GeocodingResponse, tool_name="geocode_location", data=data)
        return GeocodingResponse(payload_version=BIKESCOUT_PROTOCOL_VERSION, **data)
    except Exception as exc:  # noqa: BLE001 - log all unexpected tool failures
        return _tool_error_response(GeocodingResponse, tool_name="geocode_location", exception=exc)


@mcp.tool()
def trail_scout(
    latitude: float,
    longitude: float,
    rider: RiderProfile,
    bike: BikeSetup,
    mission: MissionConstraints,
    dest_latitude: float | None = None,
    dest_longitude: float | None = None,
    style: Literal["sparkline", "filled", "bars"] = "filled",
    target_date: str | None = None,
    include_gpx: bool = True,
    include_map: bool = False,
    include_poi: bool = False,
    include_altimetry: bool = False,
    include_weather: bool = False,
    include_mud_analysis: bool = False,
    include_nutrition_plan: bool = False,
) -> FullMissionBriefingResponse:
    """
    Advanced trail discovery.
    Returns route data, difficulty, a GPX file, and a URI with the altimetry report.
    that can be displayed directly in the chat.
    Supports both single-point Round Trips and A->B separate destinations.
    If target_date is None, it defaults to the current date.
    OPERATIONAL NOTE FOR AGENTS:
    - If the user requests a 'circular' route of a specific length (total_length_km),
      a variance of ±10% is considered a SUCCESSFUL MATCH.
    - DO NOT re-invoke the tool or attempt to refine the 'total_length_km' if the
      returned route falls within this 10% tolerance window.
    - Example: For a 25km request, any result between 22.5km and 27.5km is optimal.

    Args:
        latitude: Latitude of the starting point.
        longitude: Longitude of the starting point.
        rider: Profile including weight, fitness level and an optional measured
            sweat rate (ml/h) that replaces the population fluid estimate.
        bike: Setup details including bike type and tire width.
        mission: Constraints like search total_length_km and surface preference.
        dest_latitude: Latitude of the ending point.
        dest_longitude: Longitude of the ending point.
        style: Visual style of the profile "sparkline", "filled", "bars".
        target_date: Optional. The date of the event in YYYY-MM-DD format.
        include_gpx: If True, generates a GPX file for navigation.
        include_map: If True, generates a visual map image.
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
        - elevation_source / elevation_samples_total / elevation_samples_interpolated /
          elevation_uncertainty: Elevation data credit and sample-level uncertainty;
          elevation_error explains an omitted profile.
        - logistics.nutrition_plan: Fueling targets with their evidence basis, confidence,
          uncertainty note, normalised inputs and references; nutrition_error explains a
          rejected plan. A rider-provided measured sweat rate replaces the population estimate.
    """

    if not ORS_API_KEY:
        _log_error_details(
            reason="ORS_API_KEY is not set. Set it in the environment or in .env "
            "(get a free key at https://openrouteservice.org/).",
            show_call_stack=False,
            tool_name="trail_scout",
        )
        return FullMissionBriefingResponse.model_validate(
            {"payload_version": BIKESCOUT_PROTOCOL_VERSION, "status": "Error"}
        )

    try:
        data = get_complete_trail_scout(
            ORS_API_KEY,
            latitude,
            longitude,
            rider,
            bike,
            mission,
            dest_latitude,
            dest_longitude,
            style,
            target_date,
            include_gpx,
            include_map,
            include_poi,
            include_altimetry,
            include_weather,
            include_mud_analysis,
            include_nutrition_plan,
            sweat_rate_ml_per_hour=getattr(rider, "sweat_rate_ml_per_hour", None),
        )
        if data.get("status") == "Error":
            return _error_mission_response(reason=_error_reason(data), tool_name="trail_scout")
        return FullMissionBriefingResponse.model_validate(
            {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}
        )
    except Exception as exc:  # noqa: BLE001 - log all unexpected tool failures
        return _error_mission_response(reason=str(exc), exception=exc, tool_name="trail_scout")


@mcp.tool()
def trail_scout_simple(
    latitude: float,
    longitude: float,
    weight_kg: float = 75.0,
    gender: Literal["male", "female"] = "male",
    sweat_profile: Literal["standard", "low", "high", "extreme"] = "standard",
    fitness_level: Literal["beginner", "intermediate", "pro"] = "intermediate",
    bike_type: Literal["mtb", "road", "gravel", "e-mtb", "enduro"] = "mtb",
    tire_size: Literal["32", "29", "27.5", "700c", "650b"] = "29",
    tire_width_mm: int | None = None,
    rim_internal_width_mm: int | None = None,
    casing_type: Literal["xc", "trail", "enduro", "dh"] | None = None,
    tubeless: bool = True,
    is_ebike: bool = False,
    battery_wh: int = 625,
    motor_power_limit_w: int | None = None,
    total_length_km: int = 30,
    profile: Literal[
        "cycling-mountain", "cycling-road", "cycling-regular", "cycling-electric"
    ] = "cycling-mountain",
    surface_preference: Literal["neutral", "prefer_paved", "avoid_unpaved"] = "neutral",
    complexity: int = 3,
    seed: int = 42,
    assist_mode: Literal["Eco", "Trail", "Boost"] = "Eco",
    direction_bias: list[str] | None = None,
    avoid_urban: bool = False,
    prefer_rural: bool = False,
    distance_flex_percent: int = 10,
    priority_mode: Literal["balanced", "distance_first", "ride_character_first"] = "balanced",
    dest_latitude: float | None = None,
    dest_longitude: float | None = None,
    style: Literal["sparkline", "filled", "bars"] = "filled",
    include_gpx: bool = True,
    include_map: bool = False,
    include_poi: bool = False,
    include_altimetry: bool = False,
    include_weather: bool = False,
    include_mud_analysis: bool = False,
    include_nutrition_plan: bool = False,
    sweat_rate_ml_per_hour: float | None = None,
) -> FullMissionBriefingResponse:
    """
    Simplified tactical scout for cycling routes.
    Use this for quick route generation with sensible defaults.
    Only lat and lon are strictly required.
    Supports both single-point Round Trips and A->B separate destinations.
    OPERATIONAL NOTE FOR AGENTS:
    - If the user requests a 'circular' route of a specific length (total_length_km),
      a variance of ±10% is considered a SUCCESSFUL MATCH.
    - DO NOT re-invoke the tool or attempt to refine the 'total_length_km' if the
      returned route falls within this 10% tolerance window.
    - Example: For a 25km request, any result between 22.5km and 27.5km is optimal.

    Args:
        latitude: Latitude of the starting point.
        longitude: Longitude of the starting point.
        weight_kg: Rider's weight in kilograms (default: 75.0). Used for energy and nutrition math.
        gender: "male" or "female". Recorded for context; it does not change the
            fluid target without a measured sweat rate.
        sweat_profile: Self-reported sweat sodium concentration profile; a measured
            sweat test is needed to personalise it.
            - "low": ~400 mg/L.
            - "standard": ~800 mg/L (population average).
            - "high": ~1200 mg/L.
            - "extreme": ~1800 mg/L.
        fitness_level: Rider's stamina level ("beginner", "intermediate", "pro").
        bike_type: Type of bicycle to optimize the mechanical and tactical advice.
        tire_size: Wheel/tire diameter for specific pressure (PSI) recommendations.
        tire_width_mm: Actual tire width; defaults to the discipline reference.
        rim_internal_width_mm: Rim internal width; defaults to the discipline reference.
        casing_type: Casing stiffness (xc, trail, enduro, dh); defaults by discipline.
        tubeless: False for inner tubes, which require roughly 18% more pressure.
        is_ebike: Set to True if using a pedelec/e-bike to enable battery analysis.
        battery_wh: Battery capacity in Watt-hours (default: 625).
        motor_power_limit_w: Optional hardware motor continuous power limit in Watts.
            When omitted, battery estimation uses a conservative heuristic fallback.
        total_length_km: The total distance of the round trip in kilometers (e.g., 25.0).
        profile: Routing engine profile (e.g., 'cycling-mountain' for trails, 'cycling-road' for asphalt).
        surface_preference: Bias towards paved or unpaved roads.
        complexity: Number of ORS waypoints shaping the loop (3-10). Higher values add turns; the Streamlit UI maps its 1-5 difficulty scale to 3-5.
        seed: Random seed for route generation consistency.
        assist_mode: E-bike motor support level (affects range estimation).
        direction_bias: Preferred route quadrant bias, e.g. ["south", "east"].
        avoid_urban: Bias route generation away from dense urban sections when possible.
        prefer_rural: Bias route generation toward countryside or quieter roads when possible.
        distance_flex_percent: Allowed tolerance on target distance when route character matters more than exact mileage.
        priority_mode: Optimization strategy between exact distance and ride character.
        sweat_rate_ml_per_hour: Optional measured whole-body sweat rate (ml/h) from a
            timed weigh-in; overrides the population fluid estimate in the nutrition plan.
        dest_latitude: Optional. Latitude of the finish line (for A-to-B missions).
        dest_longitude: Optional. Longitude of the finish line (for A-to-B missions).
        style: Visual style for the elevation profile graphic.
        include_gpx: If True, generates a downloadable navigation file.
        include_map: If True, generates a tactical map image.
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
        - elevation_source / elevation_samples_total / elevation_samples_interpolated /
          elevation_uncertainty: Elevation data credit and sample-level uncertainty;
          elevation_error explains an omitted profile.
        - logistics.nutrition_plan: Fueling targets with their evidence basis, confidence,
          uncertainty note, normalised inputs and references; nutrition_error explains a
          rejected plan. A rider-provided measured sweat rate replaces the population estimate.
    """
    try:
        rider = RiderProfile(
            weight_kg=weight_kg,
            gender=gender,
            fitness_level=fitness_level,
            sweat_profile=sweat_profile,
            sweat_rate_ml_per_hour=sweat_rate_ml_per_hour,
        )

        bike = BikeSetup(
            bike_type=bike_type,
            tire_size=tire_size,
            tire_width_mm=tire_width_mm or default_tire_width_mm(bike_type),
            rim_internal_width_mm=(
                rim_internal_width_mm or default_rim_internal_width_mm(bike_type)
            ),
            casing_type=cast(
                Literal["xc", "trail", "enduro", "dh"],
                casing_type or default_casing_type(bike_type),
            ),
            tubeless=tubeless,
            is_ebike=is_ebike,
            battery_wh=battery_wh,
            motor_power_limit_w=motor_power_limit_w,
        )

        mission = MissionConstraints(
            total_length_km=total_length_km,
            profile=profile,
            surface_preference=surface_preference,
            complexity=complexity,
            seed=seed,
            assist_mode=assist_mode,
            direction_bias=cast(
                list[Literal["north", "south", "east", "west"]], direction_bias or []
            ),
            avoid_urban=avoid_urban,
            prefer_rural=prefer_rural,
            distance_flex_percent=distance_flex_percent,
            priority_mode=priority_mode,
        )

        response = trail_scout(
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
            include_poi=include_poi,
            include_altimetry=include_altimetry,
            include_weather=include_weather,
            include_mud_analysis=include_mud_analysis,
            include_nutrition_plan=include_nutrition_plan,
        )
        return response

    except (ValueError, KeyError, RuntimeError, ValidationError) as exc:
        return _error_mission_response(reason=str(exc), exception=exc)


@mcp.tool()
def check_trail_weather(
    lat: float, lon: float, target_date: str | None = None, target_hour: int = 9
) -> TacticalForecastResponse:
    """Cycling-specific weather briefing for a full forecast day.

    The safety advice always scans every hourly slot of the requested day.
    ``target_hour`` only anchors the reference conditions; it does not narrow
    the safety analysis. If ``target_date`` is omitted, today is analyzed.

    Args:
        lat: Latitude of the trail area.
        lon: Longitude of the trail area.
        target_date: Optional. The date of the event in YYYY-MM-DD format.
        target_hour: Reference hour (0-23) used for the headline conditions.
    Returns:
        A TacticalForecastResponse containing:
        - status: API operation status.
        - error_message: Diagnostic reason when status is Error.
        - metadata: Contextual data (date, timezone, location, analysis scope).
        - tactical_forecast: Numeric hourly breakdown including WMO condition.
        - reference_conditions: Verified reference-hour values and window aggregates.
        - safety_advice: Worst-hour briefing, or an explicit [UNAVAILABLE] verdict.
    """
    try:
        data = get_weather_forecast(lat, lon, target_date, target_hour)
        if data.get("status") == "Error":
            return _tool_error_response(
                TacticalForecastResponse, tool_name="check_trail_weather", data=data
            )
        return TacticalForecastResponse(payload_version=BIKESCOUT_PROTOCOL_VERSION, **data)
    except Exception as exc:  # noqa: BLE001 - log all unexpected tool failures
        return _tool_error_response(
            TacticalForecastResponse, tool_name="check_trail_weather", exception=exc
        )


@mcp.tool()
def ride_window_planner(
    lat: float,
    lon: float,
    ride_duration_hours: float = 2.0,
    surface_type: Literal["dirt", "gravel", "asphalt", "sand", "clay"] = "dirt",
    target_date: str | None = None,
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

    try:
        data = calculate_ride_windows(lat, lon, ride_duration_hours, surface_type, target_date)
        if data.get("status") == "Error":
            return _tool_error_response(
                StrategicPlannerResponse, tool_name="ride_window_planner", data=data
            )
        return StrategicPlannerResponse.model_validate(
            {"payload_version": BIKESCOUT_PROTOCOL_VERSION, **data}
        )
    except Exception as exc:  # noqa: BLE001 - log all unexpected tool failures
        return _tool_error_response(
            StrategicPlannerResponse, tool_name="ride_window_planner", exception=exc
        )


def _ride_window_temperature(
    weather_data: dict[str, Any], duration_hours: float
) -> tuple[float, Literal["ride_window", "reference_fallback", "default"]]:
    """Return the forecast peak inside the ride window, never the daily maximum.

    Args:
        weather_data: Weather payload returned by the forecast tool.
        duration_hours: Planned ride duration used to bound the window.

    Returns:
        The temperature in °C and a label describing where it came from.
    """
    metadata = weather_data.get("metadata") or {}
    start_label = str(metadata.get("target_time_local") or "")
    try:
        start_hour = int(start_label.split(":")[0])
    except (ValueError, IndexError):
        start_hour = 9
    try:
        window_hours = max(1, min(24, math.ceil(float(duration_hours))))
    except (TypeError, ValueError):
        window_hours = 1
    end_hour = min(23, start_hour + window_hours - 1)

    window_temps: list[float] = []
    for entry in weather_data.get("tactical_forecast") or []:
        try:
            hour = int(str(entry["time"]).split(":")[0])
            temp = float(str(entry["temp"]).replace("°C", "").strip())
        except (ValueError, KeyError, TypeError):
            continue
        if start_hour <= hour <= end_hour:
            window_temps.append(temp)
    if window_temps:
        return max(window_temps), "ride_window"

    reference = weather_data.get("reference_conditions") or {}
    try:
        return float(reference["temp"]), "reference_fallback"
    except (KeyError, TypeError, ValueError):
        return 20.0, "default"


@mcp.tool()
def hydration_scout(
    lat: float,
    lon: float,
    duration_hours: float = 2,
    intensity_score: int = 3,
    weight_kg: float = 70.0,
    gender: str = "male",
    sweat_profile: Literal["standard", "low", "high", "extreme"] = "standard",
    target_date: str | None = None,
    sweat_rate_ml_per_hour: float | None = None,
    relative_humidity_pct: float | None = None,
) -> HydrationScoutResponse:
    """
    Physiological Intelligence Engine.
    Calculates a nutrition and hydration plan from the ride-window temperature
    and the predicted mission intensity.

    If target_date is None, it defaults to the current window.
    For future dates, it uses the forecast peak inside the ride window rather
    than the daily maximum.

    Args:
        lat: Latitude of the mission area.
        lon: Longitude of the mission area.
        duration_hours: Estimated time in the saddle.
        intensity_score: Physiological effort (1 to 5) 5 = Max Effort/Race.
        weight_kg: Weight in Kg.
        gender: "male" or "female". Recorded for context; it does not change the
            fluid target without a measured sweat rate.
        sweat_profile: Self-reported sweat sodium concentration profile; a measured
            sweat test is needed to personalise it.
            - "low": ~400 mg/L.
            - "standard": ~800 mg/L (population average).
            - "high": ~1200 mg/L.
            - "extreme": ~1800 mg/L.
        target_date: Optional. The date of the event in YYYY-MM-DD format.
        sweat_rate_ml_per_hour: Optional measured whole-body sweat rate (ml/h)
            from a timed weigh-in; replaces the population fluid estimate.
        relative_humidity_pct: Optional relative humidity (%). It raises a heat
            alert but does not change the fluid target.
    Returns:
        A HydrationScoutResponse containing the weather context (with the
        temperature basis) and the nutrition briefing, including its evidence
        basis, confidence, uncertainty note, normalised inputs and references.
        error_message explains rejected inputs.
    """
    try:
        # 1. Fetch weather context using the updated forecast engine
        # This now supports both real-time and future dates
        weather_data = get_weather_forecast(lat, lon, target_date)
        if weather_data.get("status") == "Error":
            return _tool_error_response(
                HydrationScoutResponse, tool_name="hydration_scout", data=weather_data
            )

        # 2. Use the peak temperature inside the ride window, not the daily maximum.
        max_temp, temperature_basis = _ride_window_temperature(weather_data, duration_hours)

        # 3. Execute the Nutrition Logic
        # The engine calculates carbs/hour and ml/hour based on heat and intensity
        data = get_nutrition_plan(
            duration_hours=duration_hours,
            temp_c=max_temp,
            intensity_score=intensity_score,
            weight_kg=weight_kg,
            gender=gender,
            sweat_profile=sweat_profile,
            sweat_rate_ml_per_hour=sweat_rate_ml_per_hour,
            relative_humidity_pct=relative_humidity_pct,
            temperature_basis=temperature_basis,
        )
        if data.get("status") == "Error":
            return _tool_error_response(
                HydrationScoutResponse, tool_name="hydration_scout", data=data
            )

        context = WeatherContext(
            date_referenced=weather_data.get("metadata", {}).get("date_analyzed", target_date),
            max_temp_detected=f"{max_temp}°C",
            temperature_basis=temperature_basis,
            is_future_event=weather_data.get("metadata", {}).get("is_future_planning", False),
        )

        return HydrationScoutResponse(
            payload_version=BIKESCOUT_PROTOCOL_VERSION, weather_context=context, **data
        )
    except Exception as exc:  # noqa: BLE001 - log all unexpected tool failures
        return _tool_error_response(
            HydrationScoutResponse, tool_name="hydration_scout", exception=exc
        )


@mcp.tool()
def analyze_gpx_track(
    gpx_url: str,
    rider_weight_kg: float = 75,
    rider_gender: Literal["male", "female"] = "male",
    rider_fitness_level: Literal["beginner", "intermediate", "pro"] = "intermediate",
    sweat_profile: Literal["standard", "low", "high", "extreme"] = "standard",
    bike_weight_kg: float = 8.5,
    pro_intensity: float = 1.3,
    activity_type: Literal["road", "mtb"] = "road",
    target_date: str | None = None,
    start_hour: int | None = None,
    end_hour: int | None = None,
    report: bool = False,
) -> GpxRaceAuditResponse:
    """
    Performs a high-fidelity audit of a GPX race track.
    Estimates climb categories (BikeScout heuristic, not official UCI race classification),
    VAM, W/kg requirements, and crosswind (echelon) risks. Integrates weather, mud risk,
    and nutrition planning.

    Args:
        gpx_url: Remote URL or local path of the GPX file to analyze.
        rider_weight_kg: Body mass of the rider for Power-to-Weight calculations. Default: 75
        rider_gender: Default "male",
        rider_fitness_level: User's athletic preparation level. Affects fatigue and climbing logic. Default "intermediate"
        sweat_profile: Self-reported sweat sodium concentration profile; a measured
            sweat test is needed to personalise it.
            - "low": ~400 mg/L.
            - "standard": ~800 mg/L (population average).
            - "high": ~1200 mg/L.
            - "extreme": ~1800 mg/L.
        bike_weight_kg: Mass of the bike (default 8.5kg for road bikes).
        pro_intensity: Effort multiplier (1.0 = amateur, 1.6 = pro pace, 2.0 = world-class attack).
        activity_type: Type of activity ('road' or 'mtb').
        target_date: Optional race date (YYYY-MM-DD). If provided, fetches historical or forecast weather.
        start_hour: Expected start time (0-23). If provided with end_hour, calculates window-averaged metrics.
        end_hour: Expected finish time (0-23). Used to average weather conditions during the event.
        report: True or False, generate a PDF race book.
    Returns:
        A GpxRaceAuditResponse object containing:
        - track_metrics: Core distance and elevation data.
        - planning_tools: Weather, nutrition strategy, mud risk, and weather basis metadata.
        - climb_analysis: Detailed climb categorization (BikeScout heuristic).
        - performance_simulation: Estimated times, VAM, and W/kg per sector.
        - tactical_alerts: Positioning warnings, echelon risks, and attack points.
        - report_path: Local filesystem path to the generated PDF document (if requested).
        - mcp_resource_uri_report: MCP resource URI for the generated PDF document (if requested).
    """

    try:
        data = analyze_track(
            gpx_url=gpx_url,
            rider_weight_kg=rider_weight_kg,
            rider_gender=rider_gender,
            rider_fitness_level=rider_fitness_level,
            sweat_profile=sweat_profile,
            bike_weight_kg=bike_weight_kg,
            pro_intensity=pro_intensity,
            activity_type=activity_type,
            target_date=target_date,
            start_hour=start_hour,
            end_hour=end_hour,
            report=report,
        )
        if data.get("status") == "Error":
            return _tool_error_response(
                GpxRaceAuditResponse, tool_name="analyze_gpx_track", data=data
            )
        return GpxRaceAuditResponse(payload_version=BIKESCOUT_PROTOCOL_VERSION, **data)
    except Exception as exc:  # noqa: BLE001 - log all unexpected tool failures
        return _tool_error_response(
            GpxRaceAuditResponse, tool_name="analyze_gpx_track", exception=exc
        )


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


@mcp.resource("bikescout://race/{filename}")
def serve_race_report(filename: str) -> bytes:
    file_path = Path.home() / ".bikescout" / "race" / filename
    if not file_path.exists():
        raise FileNotFoundError("Race report not found.")
    return file_path.read_bytes()


def main():
    """
    Main entry point for the BikeScout Server.
    Supports both 'stdio' for local clients
    and 'sse' for remote deployments/web interfaces.
    """

    transport_mode = os.getenv("BIKESCOUT_TRANSPORT", "stdio").lower()

    if transport_mode == "sse":
        # Remote mode: Requires a host and port (defaulting to 0.0.0.0 for Docker/Cloud)
        host = os.getenv("BIKESCOUT_HOST", "0.0.0.0")
        port = int(os.getenv("BIKESCOUT_PORT", "8000"))

        print(f"Starting BikeScout Server in SSE mode on {host}:{port}")
        mcp.run(transport="sse", host=host, port=port)
    else:
        # Local mode: Standard I/O transport
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
