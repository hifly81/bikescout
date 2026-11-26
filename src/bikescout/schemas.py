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

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

BIKESCOUT_PROTOCOL_VERSION_MSG = "BikeScout protocol version"
BIKESCOUT_PROTOCOL_OPERATION_MSG = "Operation status (Success/Error)"

# --- BIKE SCOUT CORE SCHEMAS (PYDANTIC V2) ----


class RiderProfile(BaseModel):
    """
    Physiological data of the user.
    Required fields without defaults to force Agent-User interaction.
    """

    weight_kg: float = Field(
        75.0,
        description="Rider weight in kilograms. Critical for tire pressure and energy modeling.",
        json_schema_extra={"examples": [70.0, 85.5]},
    )
    gender: Literal["male", "female"] = Field(
        "male",
        description="User's gender.",
        json_schema_extra={"examples": ["male", "female"]},
    )
    fitness_level: Literal["beginner", "intermediate", "pro"] = Field(
        "intermediate",
        description="User's athletic preparation level. Affects fatigue and climbing logic.",
        json_schema_extra={"examples": ["intermediate"]},
    )
    sweat_profile: Literal["standard", "low", "high", "extreme"] = Field(
        "standard",
        description="Self-reported sweat sodium concentration profile. low: ~400 mg/L, standard: ~800 mg/L, high: ~1200 mg/L, extreme: ~1800 mg/L; a measured sweat test is needed to personalise it.",
        json_schema_extra={"examples": ["standard", "extreme", "low", "high"]},
    )
    sweat_rate_ml_per_hour: float | None = Field(
        default=None,
        description="Optional measured whole-body sweat rate (ml/h) from a timed weigh-in; overrides the population fluid estimate.",
    )


class BikeSetup(BaseModel):
    """
    Technical configuration of the bicycle.
    Includes cross-validation for electric bike specifications.
    """

    bike_type: Literal[
        "MTB",
        "Road",
        "Gravel",
        "E-MTB",
        "Enduro",
        "mtb",
        "road",
        "gravel",
        "e-mtb",
        "enduro",
    ] = Field(
        "mtb",
        description="The category of the bike, used to filter suitable trail surfaces.",
        json_schema_extra={"examples": ["mtb", "road"]},
    )
    tire_size: Literal["32", "29", "27.5", "700c", "650b"] = Field(
        "29",
        description="Standard wheel diameter.",
        json_schema_extra={"examples": ["29", "700c"]},
    )
    tire_width_mm: int = Field(
        54,
        ge=18,
        le=75,
        description="The actual width of the tire in mm. Critical for surface safety thresholds.",
        json_schema_extra={"examples": [54]},
    )
    rim_internal_width_mm: int | None = Field(
        None,
        ge=10,
        le=45,
        description="Rim internal width in mm. Drives volume and rim-width mismatch checks.",
        json_schema_extra={"examples": [25, 19]},
    )
    casing_type: Literal["xc", "trail", "enduro", "dh"] = Field(
        "trail",
        description="Casing construction: stiffer casings need less pressure for the same support.",
        json_schema_extra={"examples": ["xc", "trail", "enduro", "dh"]},
    )
    tubeless: bool = Field(
        True,
        description="True for tubeless setups; tubes require roughly 18% more pressure.",
        json_schema_extra={"examples": [True, False]},
    )
    is_ebike: bool = Field(
        False,
        description="Set to True if the bike has an electric motor.",
        json_schema_extra={"examples": [False]},
    )
    battery_wh: int = Field(
        625,
        description="Battery capacity in Watt-hours. Mandatory if is_ebike is True.",
        json_schema_extra={"examples": [625, 750]},
    )

    @model_validator(mode="after")
    def check_ebike_specs(self) -> "BikeSetup":
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

    total_length_km: int = Field(
        30,
        description="The total distance of the round trip in kilometers (e.g., 25.0).",
        json_schema_extra={"examples": [20, 50]},
    )
    profile: Literal["cycling-mountain", "cycling-road", "cycling-regular", "cycling-electric"] = (
        Field(
            "cycling-mountain",
            description="The OpenRouteService routing profile.",
            json_schema_extra={"examples": ["cycling-mountain"]},
        )
    )
    surface_preference: Literal["neutral", "prefer_paved", "avoid_unpaved"] = Field(
        "neutral",
        description="User preference for road vs off-road surfaces.",
        json_schema_extra={"examples": ["neutral"]},
    )
    complexity: int = Field(
        3,
        ge=3,
        le=10,
        serialization_alias="points",
        description="Number of waypoints to generate for the route shape (3-10).",
        json_schema_extra={"examples": [3, 5]},
    )
    seed: int = Field(
        42,
        description="Random seed for reproducibility of generated trails.",
        json_schema_extra={"examples": [11, 42]},
    )
    assist_mode: Literal["Eco", "Trail", "Boost", "eco", "trail", "boost"] = Field(
        "Eco",
        description="E-bike motor assistance level. Influences battery range predictions.",
        json_schema_extra={"examples": ["Trail"]},
    )
    direction_bias: list[Literal["north", "south", "east", "west"]] = Field(
        default_factory=list,
        description="Preferred geographic bias for route exploration.",
        json_schema_extra={"examples": [["south", "east"]]},
    )
    avoid_urban: bool = Field(
        False,
        description="Bias route generation away from dense urban sections when possible.",
        json_schema_extra={"examples": [True]},
    )
    prefer_rural: bool = Field(
        False,
        description="Bias route generation toward open countryside and lower-density road networks when possible.",
        json_schema_extra={"examples": [True]},
    )
    distance_flex_percent: int = Field(
        10,
        ge=0,
        le=30,
        description="Allowed flexibility around target distance when route character matters more than exact distance.",
        json_schema_extra={"examples": [10, 15]},
    )
    priority_mode: Literal["balanced", "distance_first", "ride_character_first"] = Field(
        "balanced",
        description="Optimization strategy between exact target distance and requested route character.",
        json_schema_extra={"examples": ["balanced", "ride_character_first"]},
    )

    @field_validator("direction_bias")
    @classmethod
    def normalize_direction_bias(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys([str(v).strip().lower() for v in value if str(v).strip()]))


class RouteGeometry(BaseModel):
    """
    GeoJSON-compatible geometry container.
    Coordinates format: [longitude, latitude, elevation]
    """

    coordinates: list[list[float]] = Field(
        ...,
        description="A list of coordinate triplets: [lon, lat, ele].",
        json_schema_extra={"examples": [[[9.1913, 45.4642, 120.0], [9.1915, 45.4645, 122.5]]]},
    )

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates_structure(cls, v: list[list[float]]) -> list[list[float]]:
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
    score: float = Field(
        ..., description="TAEL® mud moisture index in mm (heuristic, not a 1-100 score)"
    )
    label: str = Field(..., description="Qualitative risk label (e.g., Low, High, Extreme)")
    traction_risk: str = Field(..., description="Assessment of tire grip on the predicted surface")
    trail_damage_risk: str = Field(..., description="Risk of damaging the trail due to soft ground")
    dry_time_eta: str = Field(
        ..., description="Estimated time until trail returns to dry conditions"
    )


class MudTactical(BaseModel):
    surface_type: str = Field(..., description="Primary soil/surface type analyzed")
    mud_risk_numeric: float = Field(
        ..., description="Raw TAEL® moisture index in mm (heuristic reservoir value)"
    )
    mud_risk_score: str = Field(..., description="Qualitative mud risk label")
    traction_risk: dict[str, str] = Field(..., description="Grip assessment and tire advice")
    trail_damage_risk: dict[str, str] = Field(
        ..., description="Risk of leaving deep ruts or damaging terrain"
    )
    dry_time_eta: str = Field(
        ..., description="Estimated time until the trail is considered 'ready'"
    )


class MudRiskAnalysis(BaseModel):
    status: str = Field(..., description="Mud analysis status")
    metadata: dict[str, Any] = Field(..., description="Model version and predictive flags")
    environmental_context: dict[str, Any] = Field(
        ..., description="Soil moisture and 72h rain accumulation"
    )
    tactical_analysis: MudTactical = Field(
        ..., description="Direct riding implications of ground conditions"
    )


class ClimbDetail(BaseModel):
    """A single geometry-detected significant climb."""

    start_index: int = Field(..., description="First profile sample of the climb")
    end_index: int = Field(..., description="Last profile sample of the climb")
    length_m: float = Field(..., description="Ground length of the climb in meters")
    gain_m: float = Field(..., description="Elevation gained on this climb in meters")
    avg_gradient: float = Field(..., description="Average gradient in percent")
    max_gradient: float = Field(..., description="Steepest pitch inside the climb in percent")
    summit_elevation_m: float = Field(..., description="Elevation at the climb summit")
    fiets_index: float = Field(..., description="FIETS difficulty index of the climb")
    category: str = Field(..., description="FIETS-derived pro-cycling category")


class TechnicalDifficulty(BaseModel):
    """Technical grade with an explicit confidence score."""

    label: str = Field(..., description="Estimated or tagged technical grade")
    confidence: float = Field(..., description="Confidence from 0.0 to 1.0")
    source: str = Field(..., description="Origin of the grade (OSM tag or inference)")


class TerrainAnalysis(BaseModel):
    """Geometry-derived terrain intelligence produced by the offline engine."""

    total_ascent_m: float = Field(
        ..., description="Ascent summed from significant profile segments"
    )
    max_gradient: float = Field(..., description="Steepest positive gradient in percent")
    avg_gradient: float = Field(..., description="Ascent over total route distance in percent")
    avg_climb_gradient: float = Field(
        ..., description="Weighted gradient of detected climbs in percent"
    )
    profile_length_m: float = Field(
        ..., description="Ground length of the analyzed profile in meters"
    )
    climbs: list[ClimbDetail] = Field(..., description="Detected climbs sorted along the route")
    climb_category: str = Field(..., description="Hardest detected climb category")
    data_confidence: float = Field(
        ..., description="Heuristic confidence in elevation-derived metrics from 0.0 to 1.0"
    )
    data_confidence_basis: str | None = Field(
        None,
        description="How data_confidence is computed; heuristic, not a statistical interval or DEM error bound",
    )
    technical_difficulty: TechnicalDifficulty = Field(
        ..., description="Technical grade and its provenance"
    )
    profile_points: int = Field(..., description="Number of usable elevation samples")
    noise_floor_m: float = Field(..., description="Adaptive hysteresis threshold in meters")
    micro_spikes: bool = Field(..., description="True when a pitch of 20% or more was detected")
    warnings: list[str] = Field(..., description="Terrain-specific tactical warnings")


class TacticalBriefing(BaseModel):
    distance_km: float = Field(..., description="Total route distance in kilometers")
    elevation_gain_m: int = Field(..., description="Total positive altitude gain in meters")
    climb_category: str = Field(..., description="UCI or HC climb categorization based on effort")
    avg_gradient: str = Field(..., description="Average gradient of the entire route")
    avg_climb_gradient: str = Field(
        ..., description="Average gradient considering only the uphill sectors"
    )
    mud_intelligence: MudIntelligence = Field(
        ..., description="Ground saturation and soil condition analytics"
    )
    terrain_analysis: TerrainAnalysis | None = Field(
        None, description="Geometry-derived ascent, climb list and data confidence"
    )
    max_gradient: float | None = Field(
        None, description="Steepest positive gradient in percent from the terrain engine"
    )
    data_confidence: float | None = Field(
        None, description="Confidence in the elevation-derived terrain metrics"
    )
    technical_difficulty: TechnicalDifficulty | None = Field(
        None, description="Technical grade inferred from OSM tags and gradient"
    )


class TireSetupRecommendation(BaseModel):
    """Structured front/rear pressure recommendation from the volume/load model."""

    wheel_label: str = Field(..., description="Wheel diameter label (e.g. 29, 700c)")
    tire_width_mm: int = Field(..., description="Tire width used for the calculation")
    rim_internal_width_mm: int | None = Field(
        None, description="Rim internal width used for the calculation"
    )
    casing_type: str = Field(..., description="Casing stiffness class applied")
    tubeless: bool = Field(..., description="Whether a tubeless setup was assumed")
    psi_front: float = Field(..., description="Recommended front tire pressure in PSI")
    psi_rear: float = Field(..., description="Recommended rear tire pressure in PSI")
    bar_front: float = Field(..., description="Recommended front tire pressure in bar")
    bar_rear: float = Field(..., description="Recommended rear tire pressure in bar")
    strategy: str = Field(
        ..., description="Dominant optimization strategy (Mud, Compliance, Efficiency, ...)"
    )
    load_split: dict[str, float] = Field(
        ..., description="Front/rear load share, e.g. {'front': 0.4, 'rear': 0.6}"
    )
    knob_choice: str = Field(..., description="Suggested tread pattern for the conditions")
    advice: list[str] = Field(
        default_factory=list, description="Actionable setup intelligence messages"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Setup-specific warnings (e.g. pinch-flat risk)"
    )
    confidence: str | None = Field(
        None,
        description="Confidence in the recommendation: low for heuristic, uncalibrated models",
    )
    model_basis: str | None = Field(
        None,
        description="Short description of the model and its calibration status",
    )
    tactical_display: str = Field(
        ..., description="Human-readable tactical string with differential pressures"
    )


class MechanicalSetup(BaseModel):
    compatible: bool = Field(..., description="True if the bike setup is suitable for the route")
    setup_details: TireSetupRecommendation = Field(
        ..., description="Structured tire-pressure and load-distribution recommendation"
    )
    bike_type: str = Field(..., description="Category of bike analyzed (mtb, road, etc.)")
    safety_warnings: list[str] = Field(
        ..., description="Critical alerts regarding safety or technical risks"
    )


class SurfaceEntry(BaseModel):
    type: str = Field(..., description="Normalized surface type (e.g., Paved, Unmapped/Mixed)")
    percentage: str = Field(..., description="Percentage of total distance for this surface")


class EmtbMetrics(BaseModel):
    estimated_drain_wh: float = Field(..., description="Total energy consumption in Watt-hours")
    remaining_battery_pct: float = Field(
        ..., description="Predicted battery percentage at destination"
    )
    safety_buffer_status: str = Field(
        ..., description="Battery safety assessment (e.g., SAFE, CRITICAL)"
    )
    usable_wh_at_temp: float = Field(
        ...,
        description="Actual usable battery capacity adjusted for ambient temperature",
    )


class EmtbPower(BaseModel):
    gravity_resistance: float = Field(
        ..., description="Power required to overcome elevation in Watts"
    )
    rolling_resistance: float = Field(
        ..., description="Power required to overcome surface friction"
    )
    aerodynamic_drag: float = Field(..., description="Power required to overcome air resistance")
    rider_contribution: int = Field(
        ..., description="Estimated average power output from the cyclist"
    )
    motor_net_output: int = Field(..., description="Required average assistance from the motor")


class EmtbTactical(BaseModel):
    status: str = Field(..., description=BIKESCOUT_PROTOCOL_OPERATION_MSG)
    battery_metrics: EmtbMetrics = Field(..., description="Detailed battery drain and safety data")
    power_breakdown_w: EmtbPower = Field(..., description="Breakdown of physical forces in Watts")
    tactical_advice: str = Field(..., description="E-MTB specific pacing and assistance advice")


class WeatherSnapshot(BaseModel):
    time: str = Field(..., description="Local time of the forecast snapshot")
    temp: float = Field(..., description="Ambient temperature in Celsius")
    app_temp: float = Field(..., description="Apparent (feels-like) temperature in Celsius")
    rain_prob: int = Field(..., description="Probability of precipitation in percentage")
    rain_mm: float = Field(..., description="Expected rainfall in millimeters")
    wind: float = Field(..., description="Average wind speed in km/h")
    gusts: float = Field(..., description="Maximum wind gust speed in km/h")
    wind_direction: int = Field(..., description="Wind bearing in degrees from north")
    weather_code: int | None = Field(None, description="WMO weather code reported by the provider")
    condition: str | None = Field(None, description="Plain-language description of the WMO code")


class ReferenceConditions(BaseModel):
    """Verified conditions at the reference hour, plus window aggregates."""

    temp_actual: float = Field(..., description="Air temperature at the reference hour in Celsius")
    temp_apparent: float = Field(
        ..., description="Apparent temperature at the reference hour in Celsius"
    )
    rain_probability: int = Field(
        ..., description="Precipitation probability at the reference hour"
    )
    precipitation_mm: float = Field(
        ..., description="Rainfall at the reference hour in millimeters"
    )
    wind_speed: float = Field(..., description="Wind speed at the reference hour in km/h")
    wind_gusts: float = Field(..., description="Wind gusts at the reference hour in km/h")
    wind_direction: int = Field(..., description="Wind bearing at the reference hour in degrees")
    reference_hour_local: str = Field(..., description="Local reference hour in HH:MM format")
    temp_max: float = Field(..., description="Highest forecast temperature of the analyzed day")
    weather_code: int | None = Field(None, description="WMO weather code at the reference hour")
    condition: str | None = Field(None, description="Description of the reference WMO code")
    temp: float | None = Field(None, description="Mean temperature after ride-window filtering")
    wind_dir_degrees: int | None = Field(
        None, description="Circular mean bearing after ride-window filtering"
    )
    wind_direction_ambiguous: bool = Field(
        False, description="True when opposing wind directions make the mean bearing undefined"
    )
    reference_hour: str | None = Field(None, description="Label of the filtered ride window")


class SafetyAdvice(BaseModel):
    status: str = Field(
        ..., description="Visual alert status indicator (e.g. [GO], [WATCH], [UNAVAILABLE])"
    )
    message: str = Field(..., description="Human-readable safety assessment")
    wind_risk_score: float | None = Field(
        None, description="Numeric risk index from the worst hour, null when data is unavailable"
    )
    gear_advice: str | None = Field(
        None, description="Recommended clothing and equipment, null when data is unavailable"
    )
    condition_at_peak_risk: str | None = Field(
        None, description="Descriptive condition at the peak-risk hour"
    )


class NutritionBriefing(BaseModel):
    fluids: dict[str, Any] = Field(..., description="Total liters and hourly intake rate (ml/h)")
    carbohydrates: dict[str, Any] = Field(
        ..., description="Total grams and hourly target (g/h) with absorption ratio"
    )
    electrolytes: dict[str, Any] = Field(
        ..., description="Total and hourly sodium/salt requirements (mg)"
    )
    tactical_advice: list[str] = Field(
        ..., description="Critical nutrition alerts (e.g., Bonk Risk, Heat Stress)"
    )
    data_basis: str | None = Field(
        None, description="Evidence basis for the fluid, carbohydrate and sodium targets"
    )
    estimate_confidence: str | None = Field(
        None,
        description="Confidence in the fluid target: low for estimates, moderate when measured",
    )
    uncertainty_note: str | None = Field(
        None, description="What the plan cannot resolve without an individual sweat test"
    )
    inputs_used: dict[str, Any] | None = Field(
        None, description="Normalised inputs and their measurement source"
    )
    references: list[str] | None = Field(
        None, description="Published ranges informing the planning heuristics"
    )


class ClimbMetrics(BaseModel):
    km_start: float = Field(..., description="Distance from start where the climb begins")
    dist_km: float = Field(..., description="Length of the climbing sector")
    gain_m: float = Field(..., description="Total vertical ascent of the climb")
    avg_grade: float = Field(..., description="Average gradient percentage")
    category: str = Field(..., description="UCI classification (Cat 4 to HC)")


class PerformanceSim(BaseModel):
    climb: str = Field(..., description="Climb identifier with location and category")
    est_time_min: float = Field(
        ..., description="Estimated time to complete the climb at the given intensity"
    )
    est_vam: int = Field(..., description="Estimated VAM (Vertical Ascent Meters per hour)")
    target_wkg: float = Field(..., description="Required Power-to-Weight ratio (Watts/kg)")
    weather_adjusted_wkg: float = Field(
        ..., description="Required W/kg adjusted for wind and air density"
    )


class TacticalActionZone(BaseModel):
    km: float = Field(..., description="Kilometer mark of the zone")
    grade: float = Field(..., description="Local extreme gradient")
    type: str = Field(..., description="Type of zone (e.g., Explosive Wall, Technical Descent)")
    difficulty: str = Field(..., description="Technical/Physical difficulty level")


class WeatherContext(BaseModel):
    """Contextual weather data used to adjust physiological requirements."""

    date_referenced: str = Field(..., description="The date used for the thermal analysis")
    max_temp_detected: str = Field(
        ...,
        description="Peak temperature detected in the activity window (e.g., '16.2°C')",
    )
    temperature_basis: str | None = Field(
        None,
        description="Where the temperature came from: ride_window, reference_fallback or default",
    )
    is_future_event: bool = Field(
        ...,
        description="True if the analysis is based on a forecast rather than current conditions",
    )


class EnvironmentalBriefing(BaseModel):
    """Aggregated environmental metrics for the selected mission window."""

    message: str | None = Field(None, description="No go message")
    rain_avg: str | None = Field(
        None, description="Average probability of precipitation (e.g., '0%')"
    )
    wind_max: str | None = Field(None, description="Maximum expected wind speed (e.g., '8 km/h')")
    temp_avg: str | None = Field(
        None, description="Average temperature during the mission (e.g., '11°C')"
    )


class PlannerReport(BaseModel):
    """The final tactical verdict and timing recommendations."""

    verdict: str = Field(..., description="Final decision: GO, WATCH, or NO-GO")
    tactical_color: str = Field(..., description="Visual risk indicator (GREEN, YELLOW, RED)")
    confidence_score: str = Field(..., description="AI confidence level in the prediction (0-100)")
    best_window: str = Field(..., description="The optimal time range for the activity")
    environmental_briefing: EnvironmentalBriefing = Field(
        ..., description="Summary of weather conditions"
    )
    mud_risk_impact: str = Field(..., description="Predicted soil saturation impact on the mission")


class MissionConditions(BaseModel):
    weather: list[WeatherSnapshot] | None = Field(
        None, description="Hourly weather forecast snapshots for the mission duration."
    )
    mud_risk: MudRiskAnalysis | None = Field(
        None, description="Technical analysis of soil saturation and trail rideability."
    )
    max_temp_detected: str = Field(
        ..., description="The peak temperature identified within the activity window."
    )
    safety_advice: SafetyAdvice | None = Field(
        None,
        description="Critical safety briefing including gear recommendations and wind risk.",
    )


class Amenity(BaseModel):
    name: str = Field(
        ...,
        description="The name of the point of interest (e.g., 'Water Fountain', 'Bike Shop').",
    )
    type: str = Field(..., description="The category of the amenity for tactical filtering.")
    distance_m: int = Field(
        ..., description="Distance from the sampled route/start point in meters."
    )
    route_km: float | None = Field(
        None,
        description="Approximate route progress in km where this POI was found; null when unknown.",
    )
    location: dict[str, float] = Field(
        ..., description="The exact GPS coordinates (lat/lon) of the amenity."
    )
    opening_hours: str | None = Field(
        None, description="OSM opening_hours tag when available; null if unknown"
    )
    drinking_water: str | None = Field(
        None, description="OSM drinking_water tag when available; null if unknown"
    )
    water_source: str | None = Field(
        None, description="OSM water source/fountain tag when available"
    )
    potability: str | None = Field(
        None,
        description="Potability hint for water POIs: potable_tagged, not_potable_tagged, unknown_verify, or null",
    )


class NutritionPlanWrapper(BaseModel):
    status: str = Field(..., description="The calculation status of the nutrition engine.")
    error_message: str | None = Field(
        None, description="Reason why the nutrition engine rejected the inputs."
    )
    mission_nutrition_briefing: NutritionBriefing = Field(
        ..., description="The detailed fueling and hydration strategy."
    )


class MissionLogistics(BaseModel):
    nutrition_plan: NutritionPlanWrapper | None = Field(
        None,
        description="The physiological fueling plan including fluids, carbs, and electrolytes.",
    )
    nearby_amenities: list[Amenity] | None = Field(
        None, description="A list of strategic points detected along or near the route."
    )


class RouteSurface(BaseModel):
    profile_used: str = Field(..., description="Routing profile used (e.g., cycling-mountain)")
    metadata: dict[str, Any] = Field(..., description="Technical metadata (dates, api flags)")
    tactical_briefing: TacticalBriefing = Field(
        ..., description="Core route metrics including climb and mud analysis"
    )
    mechanical_setup: MechanicalSetup = Field(
        ..., description="Tire pressure and compatibility recommendations"
    )
    surface_breakdown: list[SurfaceEntry] = Field(
        ..., description="Aggregated and normalized surface statistics"
    )
    emtb_tactical: EmtbTactical | None = Field(
        None, description="Power and battery metrics for E-Bikes"
    )


### RESPONSE


class GeocodingResponse(BaseModel):
    """Response Schema for location lookup and geocoding results."""

    payload_version: str = Field(..., description=BIKESCOUT_PROTOCOL_VERSION_MSG)
    status: str = Field(..., description=BIKESCOUT_PROTOCOL_OPERATION_MSG)
    lat: float = Field(..., description="Latitude of the identified location")
    lon: float = Field(..., description="Longitude of the identified location")
    display_name: str = Field(..., description="Full human-readable address or place name")
    place_class: str = Field(
        ..., alias="class", description="Type of area (e.g., boundary, highway)"
    )
    place_type: str = Field(
        ...,
        alias="type",
        description="Sub-type of the location (e.g., administrative, city)",
    )
    importance: float = Field(..., description="Relevance score of the result")

    model_config = ConfigDict(populate_by_name=True)


class TacticalForecastResponse(BaseModel):
    """Response schema for trail weather."""

    payload_version: str = Field(..., description=BIKESCOUT_PROTOCOL_VERSION_MSG)
    status: str = Field(..., description=BIKESCOUT_PROTOCOL_OPERATION_MSG)
    error_message: str | None = Field(
        None, description="Reason reported when the weather service returns Error"
    )
    metadata: dict[str, Any] = Field(..., description="Location and timezone metadata")
    tactical_forecast: list[WeatherSnapshot] = Field(
        ..., description="Hourly weather breakdown for the analyzed day"
    )
    reference_conditions: ReferenceConditions = Field(
        ..., description="Verified reference-hour conditions and window aggregates"
    )
    safety_advice: SafetyAdvice = Field(
        ..., description="Strategic safety briefing based on weather risks"
    )


class RouteSurfaceResponse(BaseModel):
    """Response schema for route surfaces."""

    payload_version: str = Field(..., description=BIKESCOUT_PROTOCOL_VERSION_MSG)
    status: str = Field(..., description=BIKESCOUT_PROTOCOL_OPERATION_MSG)
    profile_used: str = Field(..., description="Routing profile used (e.g., cycling-mountain)")
    metadata: dict[str, Any] = Field(..., description="Technical metadata (dates, api flags)")
    tactical_briefing: TacticalBriefing = Field(
        ..., description="Core route metrics including climb and mud analysis"
    )
    mechanical_setup: MechanicalSetup = Field(
        ..., description="Tire pressure and compatibility recommendations"
    )
    surface_breakdown: list[SurfaceEntry] = Field(
        ..., description="Aggregated and normalized surface statistics"
    )
    emtb_tactical: EmtbTactical | None = Field(
        None, description="Power and battery metrics for E-Bikes"
    )


class RouteInfo(BaseModel):
    route_type: str = Field(
        ...,
        description="The specific cycling activity profile (e.g., 'cycling-road', 'cycling-mountain').",
    )
    distance_km: float = Field(
        ..., description="The total length of the route measured in kilometers."
    )
    ascent_m: int = Field(..., description="The total vertical elevation gain in meters.")
    difficulty: str = Field(
        ...,
        description="The overall challenge rating based on gradient, surface, and distance.",
    )
    surface_analysis: RouteSurface | None = Field(
        None,
        description="A detailed breakdown of surface compositions and traction indices.",
    )
    max_gradient: float | None = Field(
        None, description="Steepest positive gradient in percent from the terrain engine"
    )
    climb_list: list[ClimbDetail] | None = Field(
        None, description="Geometry-detected significant climbs sorted along the route"
    )
    data_confidence: float | None = Field(
        None, description="Confidence in the elevation-derived terrain metrics"
    )


class FullMissionBriefingResponse(BaseModel):
    """Response schema for trail scout: Tactical, Environmental, and Logistical."""

    payload_version: str = Field(..., description=BIKESCOUT_PROTOCOL_VERSION_MSG)
    status: str = Field(..., description=BIKESCOUT_PROTOCOL_OPERATION_MSG)
    info: RouteInfo | None = Field(
        None,
        description="Structured data regarding the route's morphology and difficulty.",
    )
    conditions: MissionConditions | None = Field(
        None,
        description="Environmental analysis synchronized with the mission time window.",
    )
    logistics: MissionLogistics | None = Field(
        None,
        description="Tactical recommendations for mechanical setup, nutrition, and timing.",
    )
    map_path: str | None = Field(
        None, description="The local file path for the static map image of the route."
    )
    mcp_resource_uri_map: str | None = Field(
        None, description="The MCP URI for direct map layer access."
    )
    map_style_applied: str | None = Field(
        None, description="Map rendering style actually applied (gradient or solid)."
    )
    map_attribution: str | None = Field(
        None, description="Attribution text for map tiles/data (e.g. OpenStreetMap)."
    )
    gpx_export_path: str | None = Field(
        None, description="The local file path of the generated GPX file."
    )
    mcp_resource_uri_gpx: str | None = Field(
        None, description="The MCP URI for downloading the GPX mission file."
    )
    elevation_profile_path: str | None = Field(
        None, description="The local file path for the elevation profile chart."
    )
    mcp_resource_uri_elevation_profile: str | None = Field(
        None, description="The MCP URI for the visual altimetry analysis."
    )
    elevation_source: str | None = Field(
        None, description="Credit for the elevation data behind the altimetry chart."
    )
    elevation_samples_total: int | None = Field(
        None, description="Number of elevation samples considered for the altimetry chart."
    )
    elevation_samples_interpolated: int | None = Field(
        None, description="Number of elevation samples estimated from neighbouring values."
    )
    elevation_uncertainty: str | None = Field(
        None, description="Explanation of which elevation samples are estimates."
    )
    elevation_error: str | None = Field(
        None, description="Reason why the elevation profile was omitted."
    )
    nutrition_error: str | None = Field(
        None, description="Reason why the nutrition plan was omitted."
    )
    gpx_stats: dict[str, int] | None = Field(
        None, description="Dictionary of raw metadata extracted from the GPX file."
    )


class HydrationScoutResponse(BaseModel):
    """Response schema for the Physiological Intelligence Engine."""

    payload_version: str = Field(..., description=BIKESCOUT_PROTOCOL_VERSION_MSG)
    status: str = Field(..., description=BIKESCOUT_PROTOCOL_OPERATION_MSG)
    weather_context: WeatherContext = Field(
        ...,
        description="Environmental factors that influenced the hydration/sodium calculation",
    )
    mission_nutrition_briefing: NutritionBriefing = Field(
        ..., description="Detailed fluid, carb, and electrolyte plan"
    )
    error_message: str | None = Field(
        None, description="Reason why the nutrition engine rejected the inputs."
    )


class StrategicPlannerResponse(BaseModel):
    """Response schema for mission planning and Go/No-Go decisions."""

    payload_version: str = Field(..., description=BIKESCOUT_PROTOCOL_VERSION_MSG)
    status: str = Field(..., description=BIKESCOUT_PROTOCOL_OPERATION_MSG)
    metadata: dict[str, Any] = Field(
        ..., description="Metadata including analyzed date and surface type"
    )
    planner_report: PlannerReport = Field(
        ..., description="Strategic assessment and tactical timing"
    )


class GpxRaceAuditResponse(BaseModel):
    """Response schema high-fidelity audit for a professional GPX race analysis."""

    payload_version: str = Field(..., description=BIKESCOUT_PROTOCOL_VERSION_MSG)
    status: str = Field(..., description=BIKESCOUT_PROTOCOL_OPERATION_MSG)
    mode: str = Field(..., description="Activity mode (ROAD or MTB)")
    target_date: str = Field(..., description="Date used for weather and mud prediction")
    track_metrics: dict[str, float] = Field(
        ..., description="Core track data: distance, ascent, altitude"
    )
    planning_tools: dict[str, Any] = Field(
        ..., description="Container for weather_forecast, nutrition_plan, and mud_risk"
    )
    climb_analysis: list[ClimbMetrics] = Field(
        ..., description="UCI categorization of all significant uphill sectors"
    )
    performance_simulation: list[PerformanceSim] = Field(
        ..., description="Climb-by-climb power and time estimates"
    )
    tactical_alerts: list[dict[str, Any]] = Field(
        ..., description="Safety and tactical alerts (e.g., ECHELON RISK)"
    )
    pre_climb_positioning: list[dict[str, Any]] = Field(
        ..., description="Points where the rider must move to the front of the pack"
    )
    tactical_action_zones: list[TacticalActionZone] = Field(
        ..., description="Key points for attacks or technical caution"
    )
    report_path: str | None = Field(
        None, description="Path to the generated PDF race book, if requested"
    )
