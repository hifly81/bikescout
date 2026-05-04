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

import uuid
import time
from pathlib import Path
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, model_validator, field_validator

# --- BIKE SCOUT CORE SCHEMAS (PYDANTIC V2) ---

class RiderProfile(BaseModel):
    """
    Physiological data of the user.
    Required fields without defaults to force Agent-User interaction.
    """
    weight_kg: float = Field(
        75.0,
        description="Rider weight in kilograms. Critical for tire pressure and energy modeling.",
        json_schema_extra={"examples": [70.0, 85.5]}
    )
    fitness_level: Literal["beginner", "intermediate", "pro"] = Field(
        "intermediate",
        description="User's athletic preparation level. Affects fatigue and climbing logic.",
        json_schema_extra={"examples": ["intermediate"]}
    )

class BikeSetup(BaseModel):
    """
    Technical configuration of the bicycle.
    Includes cross-validation for electric bike specifications.
    """
    bike_type: Literal['MTB', 'Road', 'Gravel', 'E-MTB', 'Enduro', 'mtb', 'road', 'gravel', 'e-mtb', 'enduro'] = Field(
        "mtb",
        description="The category of the bike, used to filter suitable trail surfaces.",
        json_schema_extra={"examples": ["mtb", "road"]}
    )
    tire_size: Literal["32", "29", "27.5", "700c", "650b"] = Field(
        "29",
        description="Standard wheel diameter.",
        json_schema_extra={"examples": ["29", "700c"]}
    )
    tire_width_mm: int = Field(
        54,
        ge=18,
        le=75,
        description="The actual width of the tire in mm. Critical for surface safety thresholds.",
        json_schema_extra={"examples": 54}
    )
    is_ebike: bool = Field(
        False,
        description="Set to True if the bike has an electric motor.",
        json_schema_extra={"examples": [False]}
    )
    battery_wh: int = Field(
        625,
        description="Battery capacity in Watt-hours. Mandatory if is_ebike is True.",
        json_schema_extra={"examples": [625, 750]}
    )

    @model_validator(mode='after')
    def check_ebike_specs(self) -> 'BikeSetup':
        """
        Pydantic V2 model validator.
        Ensures battery data is provided if the bike is electric.
        """
        if self.is_ebike and self.battery_wh is None:
            raise ValueError("battery_wh must be specified for E-MTB setups.")
        return self

class MissionConstraints(BaseModel):
    """
    Tactical constraints for the specific ride/mission.
    """
    radius_km: int = Field(
        30,
        description="The desired search radius or loop length in kilometers.",
        json_schema_extra={"examples": [20, 50]}
    )
    profile: Literal["cycling-mountain", "cycling-road", "cycling-regular", "cycling-electric"] = Field(
        "cycling-mountain",
        description="The OpenRouteService routing profile.",
        json_schema_extra={"examples": ["cycling-mountain"]}
    )
    surface_preference: Literal["neutral", "prefer_paved", "avoid_unpaved"] = Field(
        "neutral",
        description="User preference for road vs off-road surfaces.",
        json_schema_extra={"examples": ["neutral"]}
    )
    complexity: int = Field(
        3,
        ge=3,
        le=10,
        serialization_alias="points",
        description="Number of waypoints to generate for the route shape (3-10).",
        json_schema_extra={"examples": [3, 5]}
    )
    seed: int = Field(
        42,
        description="Random seed for reproducibility of generated trails.",
        json_schema_extra={"examples": [11, 42]}
    )
    assist_mode: Literal["Eco", "Trail", "Boost", "eco", "trail", "boost"] = Field(
        "Eco",
        description="E-bike motor assistance level. Influences battery range predictions.",
        json_schema_extra={"examples": ["Trail"]}
    )

class RouteGeometry(BaseModel):
    """
    GeoJSON-compatible geometry container.
    Coordinates format: [longitude, latitude, elevation]
    """
    coordinates: List[List[float]] = Field(
        ...,
        description="A list of coordinate triplets: [lon, lat, ele].",
        json_schema_extra={
            "examples": [
                [[9.1913, 45.4642, 120.0], [9.1915, 45.4645, 122.5]]
            ]
        }
    )

    @field_validator('coordinates')
    @classmethod
    def validate_coordinates_structure(cls, v: List[List[float]]) -> List[List[float]]:
        """
        Pydantic V2 field validator.
        Ensures each point has [lon, lat] and standardizes elevation.
        """
        if not v:
            raise ValueError("Coordinates list cannot be empty.")

        for point in v:
            if len(point) < 2:
                raise ValueError(f"Invalid point structure: {point}. Expected [lon, lat, ele].")
            if len(point) == 2:
                # Standardize to 3D by adding 0.0 elevation if missing
                point.append(0.0)
        return v

    @property
    def has_elevation(self) -> bool:
        """Helper to verify if the dataset contains meaningful vertical data."""
        return any(len(p) > 2 and p[2] != 0 for p in self.coordinates)

    def to_dict(self):
        """Converts the model back to a standard dictionary for MCP transport."""
        return self.model_dump()

class MudIntelligence(BaseModel):
    score: float = Field(..., description="TAEL® mud score (higher means more saturation)")
    label: str = Field(..., description="Qualitative risk label (e.g., Low, High, Extreme)")
    traction_risk: str = Field(..., description="Assessment of tire grip on the predicted surface")
    trail_damage_risk: str = Field(..., description="Risk of damaging the trail due to soft ground")
    dry_time_eta: str = Field(..., description="Estimated time until trail returns to dry conditions")
    safety_advice: str = Field(..., description="Tactical advice for riding in current soil conditions")

class MudTactical(BaseModel):
    surface_type: str = Field(..., description="Primary soil/surface type analyzed")
    mud_risk_numeric: float = Field(..., description="Raw TAEL® moisture index")
    mud_risk_score: str = Field(..., description="Qualitative mud risk label")
    traction_risk: Dict[str, str] = Field(..., description="Grip assessment and tire advice")
    trail_damage_risk: Dict[str, str] = Field(..., description="Risk of leaving deep ruts or damaging terrain")
    dry_time_eta: str = Field(..., description="Estimated time until the trail is considered 'ready'")

class MudRiskAnalysis(BaseModel):
    status: str = Field(..., description="Mud analysis status")
    metadata: Dict[str, Any] = Field(..., description="Model version and predictive flags")
    environmental_context: Dict[str, Any] = Field(..., description="Soil moisture and 72h rain accumulation")
    tactical_analysis: MudTactical = Field(..., description="Direct riding implications of ground conditions")

class TacticalBriefing(BaseModel):
    distance_km: float = Field(..., description="Total route distance in kilometers")
    elevation_gain_m: int = Field(..., description="Total positive altitude gain in meters")
    climb_category: str = Field(..., description="UCI or HC climb categorization based on effort")
    avg_gradient: str = Field(..., description="Average gradient of the entire route")
    avg_climb_gradient: str = Field(..., description="Average gradient considering only the uphill sectors")
    mud_intelligence: MudIntelligence = Field(..., description="Ground saturation and soil condition analytics")

class MechanicalSetup(BaseModel):
    compatible: bool = Field(..., description="True if the bike setup is suitable for the route")
    setup_details: List[Any] = Field(..., description="Technical specifics [tire_width_mm, setup_string]")
    bike_type: str = Field(..., description="Category of bike analyzed (mtb, road, etc.)")

class SurfaceEntry(BaseModel):
    type: str = Field(..., description="Normalized surface type (e.g., Paved, Unmapped/Mixed)")
    percentage: str = Field(..., description="Percentage of total distance for this surface")

class EmtbMetrics(BaseModel):
    estimated_drain_wh: float = Field(..., description="Total energy consumption in Watt-hours")
    remaining_battery_pct: float = Field(..., description="Predicted battery percentage at destination")
    safety_buffer_status: str = Field(..., description="Battery safety assessment (e.g., SAFE, CRITICAL)")
    usable_wh_at_temp: float = Field(..., description="Actual usable battery capacity adjusted for ambient temperature")

class EmtbPower(BaseModel):
    gravity_resistance: float = Field(..., description="Power required to overcome elevation in Watts")
    rolling_resistance: float = Field(..., description="Power required to overcome surface friction")
    aerodynamic_drag: float = Field(..., description="Power required to overcome air resistance")
    rider_contribution: int = Field(..., description="Estimated average power output from the cyclist")
    motor_net_output: int = Field(..., description="Required average assistance from the motor")

class EmtbTactical(BaseModel):
    status: str = Field(..., description="Analysis status (Success or Error)")
    battery_metrics: EmtbMetrics = Field(..., description="Detailed battery drain and safety data")
    power_breakdown_w: EmtbPower = Field(..., description="Breakdown of physical forces in Watts")
    tactical_advice: str = Field(..., description="E-MTB specific pacing and assistance advice")

class RecommendedSetup(BaseModel):
    tire_width_ref: str = Field(..., description="Reference tire width (e.g., '2.3\"' or '28mm')")
    pressure_bar: str = Field(..., description="Recommended pressure range in Bar")
    pressure_psi: str = Field(..., description="Recommended pressure range in PSI")

class WeatherSnapshot(BaseModel):
    time: str = Field(..., description="Local time of the forecast snapshot")
    temp: str = Field(..., description="Ambient temperature")
    app_temp: str = Field(..., description="Apparent (feels-like) temperature")
    rain_prob: str = Field(..., description="Probability of precipitation in percentage")
    rain_mm: str = Field(..., description="Expected rainfall in millimeters")
    wind: str = Field(..., description="Average wind speed")
    gusts: str = Field(..., description="Maximum wind gust speed")

class SafetyAdvice(BaseModel):
    status: str = Field(..., description="Visual alert status indicator (e.g., 🔵 [WATCH], 🔴 [DANGER])")
    message: str = Field(..., description="Human-readable safety assessment")
    wind_risk_score: float = Field(..., description="Numeric risk index for crosswinds and gusts")
    gear_advice: str = Field(..., description="Recommended clothing and equipment for these conditions")

class NutritionBriefing(BaseModel):
    fluids: Dict[str, Any] = Field(..., description="Total liters and hourly intake rate (ml/h)")
    carbohydrates: Dict[str, Any] = Field(..., description="Total grams and hourly target (g/h) with absorption ratio")
    electrolytes: Dict[str, Any] = Field(..., description="Total and hourly sodium/salt requirements (mg)")
    tactical_advice: List[str] = Field(..., description="Critical nutrition alerts (e.g., Bonk Risk, Heat Stress)")

class ClimbMetrics(BaseModel):
    km_start: float = Field(..., description="Distance from start where the climb begins")
    dist_km: float = Field(..., description="Length of the climbing sector")
    gain_m: float = Field(..., description="Total vertical ascent of the climb")
    avg_grade: float = Field(..., description="Average gradient percentage")
    category: str = Field(..., description="UCI classification (Cat 4 to HC)")

class PerformanceSim(BaseModel):
    climb: str = Field(..., description="Climb identifier with location and category")
    est_time_min: float = Field(..., description="Estimated time to complete the climb at the given intensity")
    est_vam: int = Field(..., description="Estimated VAM (Vertical Ascent Meters per hour)")
    target_wkg: float = Field(..., description="Required Power-to-Weight ratio (Watts/kg)")
    weather_adjusted_wkg: float = Field(..., description="Required W/kg adjusted for wind and air density")

class TacticalActionZone(BaseModel):
    km: float = Field(..., description="Kilometer mark of the zone")
    grade: float = Field(..., description="Local extreme gradient")
    type: str = Field(..., description="Type of zone (e.g., Explosive Wall, Technical Descent)")
    difficulty: str = Field(..., description="Technical/Physical difficulty level")

class WeatherContext(BaseModel):
    """Contextual weather data used to adjust physiological requirements."""
    date_referenced: str = Field(..., description="The date used for the thermal analysis")
    max_temp_detected: str = Field(..., description="Peak temperature detected in the activity window (e.g., '16.2°C')")
    is_future_event: bool = Field(..., description="True if the analysis is based on a forecast rather than current conditions")

class EnvironmentalBriefing(BaseModel):
    """Aggregated environmental metrics for the selected mission window."""
    rain_avg: str = Field(..., description="Average probability of precipitation (e.g., '0%')")
    wind_max: str = Field(..., description="Maximum expected wind speed (e.g., '8 km/h')")
    temp_avg: str = Field(..., description="Average temperature during the mission (e.g., '11°C')")

class PlannerReport(BaseModel):
    """The final tactical verdict and timing recommendations."""
    verdict: str = Field(..., description="Final decision: GO, WATCH, or NO-GO")
    tactical_color: str = Field(..., description="Visual risk indicator (GREEN, YELLOW, RED)")
    confidence_score: str = Field(..., description="AI confidence level in the prediction (0-100)")
    best_window: str = Field(..., description="The optimal time range for the activity")
    environmental_briefing: EnvironmentalBriefing = Field(..., description="Summary of weather conditions")
    mud_risk_impact: str = Field(..., description="Predicted soil saturation impact on the mission")

class MissionConditions(BaseModel):
    weather: List[WeatherSnapshot] = Field(..., description="Hourly weather forecast snapshots for the mission duration.")
    mud_risk: MudRiskAnalysis = Field(..., description="Technical analysis of soil saturation and trail rideability.")
    max_temp_detected: str = Field(..., description="The peak temperature identified within the activity window.")
    safety_advice: SafetyAdvice = Field(..., description="Critical safety briefing including gear recommendations and wind risk.")

class Amenity(BaseModel):
    name: str = Field(..., description="The name of the point of interest (e.g., 'Water Fountain', 'Bike Shop').")
    type: str = Field(..., description="The category of the amenity for tactical filtering.")
    distance_m: int = Field(..., description="The geodesic distance from the route path in meters.")
    location: Dict[str, float] = Field(..., description="The exact GPS coordinates (lat/lon) of the amenity.")

class NutritionPlanWrapper(BaseModel):
    status: str = Field(..., description="The calculation status of the nutrition engine.")
    mission_nutrition_briefing: NutritionBriefing = Field(..., description="The detailed fueling and hydration strategy.")

class MissionLogistics(BaseModel):
    nutrition_plan: NutritionPlanWrapper = Field(..., description="The physiological fueling plan including fluids, carbs, and electrolytes.")
    nearby_amenities: List[Amenity] = Field(..., description="A list of strategic points detected along or near the route.")

class RouteSurface(BaseModel):
    profile_used: str = Field(..., description="Routing profile used (e.g., cycling-mountain)")
    metadata: Dict[str, Any] = Field(..., description="Technical metadata (dates, api flags)")
    tactical_briefing: TacticalBriefing = Field(..., description="Core route metrics including climb and mud analysis")
    mechanical_setup: MechanicalSetup = Field(..., description="Tire pressure and compatibility recommendations")
    surface_breakdown: List[SurfaceEntry] = Field(..., description="Aggregated and normalized surface statistics")
    emtb_tactical: Optional[EmtbTactical] = Field(None, description="Power and battery metrics for E-Bikes")
    safety_warnings: List[str] = Field(..., description="Critical alerts regarding safety or technical risks")

### RESPONSE

class GeocodingResponse(BaseModel):
    """Response Schema for location lookup and geocoding results."""
    payload_version: str = Field(..., description="BikeScout protocol version")
    status: str = Field(..., description="Operation status (Success/Error)")
    lat: float = Field(..., description="Latitude of the identified location")
    lon: float = Field(..., description="Longitude of the identified location")
    display_name: str = Field(..., description="Full human-readable address or place name")
    place_class: str = Field(..., alias="class", description="Type of area (e.g., boundary, highway)")
    place_type: str = Field(..., alias="type", description="Sub-type of the location (e.g., administrative, city)")
    importance: float = Field(..., description="Relevance score of the result")

    class Config:
        populate_by_name = True

class TacticalForecastResponse(BaseModel):
    """Response schema for trail weather."""
    payload_version: str = Field(..., description="BikeScout protocol version")
    status: str = Field(..., description="Weather service status")
    metadata: Dict[str, Any] = Field(..., description="Location and timezone metadata")
    tactical_forecast: List[WeatherSnapshot] = Field(..., description="Hourly weather breakdown for the race duration")
    reference_conditions: Dict[str, Any] = Field(..., description="Aggregated weather data used for performance adjustments")
    safety_advice: SafetyAdvice = Field(..., description="Strategic safety briefing based on weather risks")

class RouteSurfaceResponse(BaseModel):
    """Response schema for route surfaces."""
    payload_version: str = Field(..., description="BikeScout protocol version")
    status: str = Field(..., description="Operation status (Success/Error)")
    profile_used: str = Field(..., description="Routing profile used (e.g., cycling-mountain)")
    metadata: Dict[str, Any] = Field(..., description="Technical metadata (dates, api flags)")
    tactical_briefing: TacticalBriefing = Field(..., description="Core route metrics including climb and mud analysis")
    mechanical_setup: MechanicalSetup = Field(..., description="Tire pressure and compatibility recommendations")
    surface_breakdown: List[SurfaceEntry] = Field(..., description="Aggregated and normalized surface statistics")
    emtb_tactical: Optional[EmtbTactical] = Field(None, description="Power and battery metrics for E-Bikes")
    safety_warnings: List[str] = Field(..., description="Critical alerts regarding safety or technical risks")

class RouteInfo(BaseModel):
    route_type: str = Field(..., description="The specific cycling activity profile (e.g., 'cycling-road', 'cycling-mountain').")
    distance_km: float = Field(..., description="The total length of the route measured in kilometers.")
    ascent_m: int = Field(..., description="The total vertical elevation gain in meters.")
    difficulty: str = Field(..., description="The overall challenge rating based on gradient, surface, and distance.")
    surface_analysis: RouteSurface = Field(..., description="A detailed breakdown of surface compositions and traction indices.")

class FullMissionBriefingResponse(BaseModel):
    """Response schema for trail scout: Tactical, Environmental, and Logistical."""
    payload_version: str = Field(..., description="BikeScout protocol version")
    status: str = Field(..., description="Operation status (Success/Error)")
    info: RouteInfo = Field(..., description="Structured data regarding the route's morphology and difficulty.")
    conditions: MissionConditions = Field(..., description="Environmental analysis synchronized with the mission time window.")
    logistics: MissionLogistics = Field(..., description="Tactical recommendations for mechanical setup, nutrition, and timing.")
    map_path: str = Field(..., description="The local file path for the static map image of the route.")
    mcp_resource_uri_map: str = Field(..., description="The MCP URI for direct map layer access.")
    gpx_export_path: str = Field(..., description="The local file path of the generated GPX file.")
    mcp_resource_uri_gpx: str = Field(..., description="The MCP URI for downloading the GPX mission file.")
    elevation_profile_path: str = Field(..., description="The local file path for the elevation profile chart.")
    mcp_resource_uri_elevation_profile: str = Field(..., description="The MCP URI for the visual altimetry analysis.")
    gpx_stats: Dict[str, int] = Field(..., description="Dictionary of raw metadata extracted from the GPX file.")

class HydrationScoutResponse(BaseModel):
    """Response schema for the Physiological Intelligence Engine."""
    payload_version: str = Field(..., description="BikeScout protocol version")
    status: str = Field(..., description="Operation status (Success/Error)")
    weather_context: WeatherContext = Field(..., description="Environmental factors that influenced the hydration/sodium calculation")
    mission_nutrition_briefing: NutritionBriefing = Field(..., description="Detailed fluid, carb, and electrolyte plan")

class StrategicPlannerResponse(BaseModel):
    """Response schema for mission planning and Go/No-Go decisions."""
    payload_version: str = Field(..., description="BikeScout protocol version")
    status: str = Field(..., description="Operation status (Success/Error)")
    metadata: Dict[str, Any] = Field(..., description="Metadata including analyzed date and surface type")
    planner_report: PlannerReport = Field(..., description="Strategic assessment and tactical timing")

class GpxRaceAuditResponse(BaseModel):
    """Response schema high-fidelity audit for a professional GPX race analysis."""
    payload_version: str = Field(..., description="BikeScout Protocol version")
    status: str = Field(..., description="Overall analysis status")
    mode: str = Field(..., description="Activity mode (ROAD or MTB)")
    target_date: str = Field(..., description="Date used for weather and mud prediction")
    track_metrics: Dict[str, float] = Field(..., description="Core track data: distance, ascent, altitude")
    planning_tools: Dict[str, Any] = Field(..., description="Container for weather_forecast, nutrition_plan, and mud_risk")
    climb_analysis: List[ClimbMetrics] = Field(..., description="UCI categorization of all significant uphill sectors")
    performance_simulation: List[PerformanceSim] = Field(..., description="Climb-by-climb power and time estimates")
    tactical_alerts: List[Dict[str, Any]] = Field(..., description="Safety and tactical alerts (e.g., ECHELON RISK)")
    pre_climb_positioning: List[Dict[str, Any]] = Field(..., description="Points where the rider must move to the front of the pack")
    tactical_action_zones: List[TacticalActionZone] = Field(..., description="Key points for attacks or technical caution")
    report_path: Optional[str] = Field(None, description="Path to the generated PDF race book, if requested")

class MechanicalBaselineResponse(BaseModel):
    """Response schema for baseline mechanical settings and pressure guides."""
    payload_version: str = Field("1.0", description="The BikeScout protocol version for client-side compatibility.")
    status: str = Field(..., description="Operation status indicator (e.g., 'Success', 'Error').")
    category: str = Field(..., description="The detected bike category used for calculation (mtb, road, gravel).")
    recommended_setup: RecommendedSetup = Field(..., description="Detailed technical specifications for tires, wheels, and baseline pressures.")
    full_guide_reference: str = Field(..., description="URL or markdown documentation link regarding international pressure standards.")
    setup_notes: str = Field(..., description="Tactical engineering notes regarding tire casing and tube vs. tubeless efficiency.")

class SafetyProtocolResponse(BaseModel):
    """Response schema for the official BikeScout Safety Protocol and mission-specific checklists."""
    payload_version: str = Field(..., description="BikeScout protocol version")
    status: str = Field(..., description="Operation status (Success/Error)")
    mission_type_applied: str = Field(..., description="The category of ride the protocol was tailored for (e.g., mtb, road)")
    standard_checklist: str = Field(..., description="Markdown formatted global safety checks (M-Check, Brakes, etc.)")
    tactical_pre_ride_commands: List[str] = Field(
        ...,
        description="Specific mechanical and gear actions to perform before departure (e.g., Sag check, GPS sync)"
    )