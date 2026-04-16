import requests
from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.geophysic import haversine_distance
from bikescout.tools.bike_setup import analyze_compatibility
from bikescout.schemas import RiderProfile, BikeSetup, MissionConstraints


def _get_tire_setup(bike_type: str, tire_size_option: str, mud_index: float = 0.0, surface_type: str = "mixed", rider_weight_kg: float = 80.0):
    """
    Standardizes tire size and calculates Actionable Setup Intelligence (PSI/Bar).
    Transitions from static descriptors to dynamic tactical briefings.

    Returns:
        tuple: (actual_tire_mm, tactical_display_string)
    """
    bike_type = bike_type.lower()

    # 1. Base Configuration Mapping
    # (Base_PSI_at_85kg, Width_mm, Default_Wheel_Label)
    configs = {
        "mtb": (24.0, 58, "29\""),
        "e-mtb": (26.0, 60, "29\""),
        "enduro": (23.0, 60, "29\""),
        "gravel": (35.0, 40, "700c"),
        "road": (85.0, 25, "700c")
    }

    # Default to road if type is unknown
    base_psi, width_mm, wheel_label = configs.get(bike_type, configs["road"])

    # 2. Wheel Label Normalization (Legacy support for tire_size_option)
    if bike_type in ["mtb", "e-mtb", "enduro"]:
        wheel_label = "29\"" if tire_size_option in ["700c", "650b", "25", "28"] else tire_size_option
    elif bike_type == "gravel":
        wheel_label = tire_size_option if tire_size_option in ["700c", "650b"] else "700c"

    # 3. Rider Weight Normalization (Heuristic: +/- 1 PSI per 5kg deviation)
    weight_adjustment = (rider_weight_kg - 85.0) / 5.0
    adjusted_psi = base_psi + weight_adjustment

    # 4. Tactical Strategy Logic
    strategy = "Standard"

    # Mud Strategy: Lower pressure for flotation and traction
    if mud_index > 0.6:
        adjusted_psi *= 0.85  # 15% reduction
        strategy = "Mud Flotation"

    # Surface Strategy: Compliance vs Efficiency
    elif any(keyword in surface_type.lower() for keyword in ["rock", "root", "technical"]):
        adjusted_psi -= 2.0
        strategy = "Compliance"
    elif any(keyword in surface_type.lower() for keyword in ["smooth", "asphalt", "paved"]):
        adjusted_psi += 3.0
        strategy = "Efficiency"

    # 5. Unit Conversion
    final_psi = round(adjusted_psi, 1)
    final_bar = round(final_psi * 0.0689476, 2)

    # 6. Tactical Display String
    tactical_display = (
        f"{wheel_label} wheels | {final_psi} PSI ({final_bar} Bar) "
        f"[{strategy} Setup]"
    )

    return width_mm, tactical_display

def _sanitize_elevation(raw_ascent: float):
    """
    Filters satellite SRTM noise. Applies progressive reduction based on ascent intensity.
    """
    if raw_ascent > 2000:
        return round(raw_ascent * 0.60, 0)  # 40% reduction for high noise
    if raw_ascent > 1000:
        return round(raw_ascent * 0.70, 0)  # 30% reduction
    return round(raw_ascent * 0.85, 0)      # 15% reduction for light hills

def _categorize_climb(total_ascent: float, total_dist_m: float, bike_type: str):
    """
    Calculates the average gradient and assigns a pro-cycling climb category.
    Adjusts effort scores and climbing ratios based on the specific bike type (Road, MTB, Enduro).
    """
    # --- 1. DYNAMIC CLIMBING RATIO & EFFORT MULTIPLIER ---
    # Enduro: Steep, punchy climbs followed by descents (Climbing covers ~25% of total distance)
    # MTB/XC: Mixed trails with moderate climbing efficiency (~30% of total distance)
    # Road/Gravel: Longer, sustained efforts on predictable terrain (~45% of total distance)

    bike_type_low = bike_type.lower()

    if "enduro" in bike_type_low:
        climbing_ratio = 0.25
        effort_multiplier = 1.6  # Maximum effort due to technical terrain and bike weight
    elif "mountain" in bike_type_low or "mtb" in bike_type_low:
        climbing_ratio = 0.30
        effort_multiplier = 1.4  # Increased effort for off-road rolling resistance
    else:
        climbing_ratio = 0.45
        effort_multiplier = 1.0  # Baseline effort for paved or smooth surfaces

    # --- 2. GRADIENT CALCULATION ---
    climbing_dist = total_dist_m * climbing_ratio
    avg_gradient = (total_ascent / climbing_dist) * 100 if climbing_dist > 0 else 0

    # Cap the display gradient for realism (Enduro can realistically reach higher averages)
    max_display = 25.0 if "enduro" in bike_type_low else 20.0
    display_gradient = min(avg_gradient, max_display)

    # --- 3. EFFORT SCORE CALCULATION ---
    # The score combines total vertical gain with steepness and a bike-specific multiplier
    # We cap the gradient at 18% for the scoring formula to prevent outliers from breaking categories
    scoring_gradient = min(display_gradient, 18.0)
    adjusted_score = total_ascent * (scoring_gradient / 10) * effort_multiplier

    # --- 4. CATEGORIZATION LOGIC ---
    if total_ascent < 50:
        return "Flat / Rolling", display_gradient

    # HC (Hors Catégorie): Climbs that are beyond classification
    if adjusted_score >= 800 or total_ascent > 1000:
        category = "Hors Catégorie (HC) - Legendary Challenge"
    elif adjusted_score >= 500:
        category = "Category 1 - Brutal Ascent"
    elif adjusted_score >= 300:
        category = "Category 2 - Hard Climb"
    elif adjusted_score >= 150:
        category = "Category 3 - Challenging"
    else:
        category = "Category 4 - Short Burner"

    # Append technical tag for Enduro to distinguish from standard XC/MTB
    if "enduro" in bike_type_low:
        category = f"Enduro Tech: {category}"

    return category, display_gradient

def _analyze_technical_difficulty(extras: dict):
    """
    Parses OSM tags for professional technical grading (MTB-Scale & SAC-Scale).
    """
    # 1. MTB Scale (Singletrail-Skala S0-S5)
    # ORS returns 'surface' or 'tracktype' summaries, but specific scale tags
    # are often in the 'steepness' or 'suitability' segments if enabled.
    # Se ORS non passa il tag diretto, usiamo il tracktype come fallback intelligente.

    mtb_val = extras.get('mtb_scale', {}).get('summary', [{}])[0].get('value', 'N/A')

    scale_info = {
        "0": "S0: Smooth, paved/firm trails without obstacles.",
        "1": "S1: Small roots/stones, easy technical sections.",
        "2": "S2: Loose soil, larger roots/stones, steps required.",
        "3": "S3: Technical rock gardens, high steps, hairpins.",
        "4": "S4: Extreme steepness, tight switchbacks, trial skills.",
        "5": "S5: Near-vertical terrain, maximum difficulty."
    }

    # 2. Trail Visibility
    vis_val = extras.get('trail_visibility', {}).get('summary', [{}])[0].get('value', '1')
    vis_map = {"1": "Excellent", "2": "Good", "3": "Poor", "4": "Invisible/Requires GPS"}

    return {
        "mtb_scale": scale_info.get(str(mtb_val), "Standard / Unclassified"),
        "trail_visibility": vis_map.get(str(vis_val), "Standard"),
        "technical_notes": "Technical grading based on OSM mountain standards."
    }

def _build_ors_options(surface_preference):
    """
    Translates user surface preferences into ORS API options.
    """
    options = {}
    avoid_features = []

    if surface_preference == "avoid_unpaved":
        avoid_features.append("unpaved")

    if surface_preference == "prefer_paved":
        options["avoid_polygons"] = {}
        if "unpaved" not in avoid_features:
            avoid_features.append("unpaved")

    if avoid_features:
        options["avoid_features"] = avoid_features

    return options

def get_surface_analyzer(api_key, lat, lon, rider, bike, mission):
    """
    Main entry point for route analysis.
    Integrated with Geodesic Accuracy (Haversine) and TAEL Mud Risk Model.
    """

    attempts = [
        (mission.profile, ["surface", "waytype", "tracktype"]),
        (mission.profile, ["surface", "waytype"]),
        ("cycling-regular", ["surface", "waytype"])
    ]

    last_error = ""
    for current_profile, current_extras in attempts:
        url = f"https://api.openrouteservice.org/v2/directions/{current_profile}/geojson"
        headers = {'Authorization': api_key, 'Content-Type': 'application/json'}
        body = {
            "coordinates": [[lon, lat]],
            "elevation": True,
            "options": {
                "round_trip": {"length": mission.radius_km * 1000, "points": mission.complexity, "seed": mission.seed},
                **_build_ors_options(mission.surface_preference)
            },
            "extra_info": current_extras
        }

        try:
            response = requests.post(url, json=body, headers=headers)
            if response.status_code == 400:
                last_error = response.json().get('error', {}).get('message', 'Bad Request')
                continue

            response.raise_for_status()
            data = response.json()

            # --- 2. Extract Geometry & Core Data ---
            feature = data['features'][0]
            props = feature['properties']
            geometry = feature['geometry']['coordinates'] # List of [lon, lat, ele]
            extras = props.get('extras', {})

            # --- 2b. GEODESIC ACCURACY UPGRADE ---
            # Instead of using props['summary']['distance'], we calculate the real distance
            # summing segments with Haversine to avoid latitude distortion.
            real_dist_m = 0
            for i in range(len(geometry) - 1):
                p1 = geometry[i]
                p2 = geometry[i+1]
                # ORS uses [lon, lat], haversine needs (lat1, lon1, lat2, lon2)
                real_dist_m += haversine_distance(p1[1], p1[0], p2[1], p2[0])

            # --- 3. Surface & Mud Analysis (INTEGRATED TAEL MODEL) ---
            surface_map = {0: "Unknown", 1: "Asphalt", 2: "Unpaved", 3: "Paved", 4: "Cobblestone",
                           5: "Gravel", 6: "Fine Gravel", 11: "Grass", 12: "Compact", 14: "Concrete"}

            dominant_surface = _extract_dominant_surface(extras.get('surface', {}), surface_map)
            mud_analysis = get_mud_risk_analysis(lat, lon, dominant_surface)

            if mud_analysis["status"] == "Success":
                mud_index = mud_analysis["tactical_analysis"]["adjusted_moisture_index"]
                mud_risk_label = mud_analysis["tactical_analysis"]["mud_risk_score"]
                safety_advice = mud_analysis["tactical_analysis"]["safety_advice"]
                env_context = mud_analysis["environmental_context"]
            else:
                mud_index = 0.5
                mud_risk_label = "Unknown (Telemetry Failure)"
                safety_advice = "Weather data unavailable. Proceed with caution."
                env_context = {}

            # --- 4. Tire Intelligence ---
            tire_mm, tire_display = _get_tire_setup(
                bike_type=bike.bike_type,
                tire_size_option=bike.tire_size,
                mud_index=mud_index,
                surface_type=dominant_surface,
                rider_weight_kg=rider.weight_kg
            )

            # --- 5. Process Elevation and Climbs (Using REAL Geodesic Distance) ---
            clean_ascent = _sanitize_elevation(props.get('ascent', 0))
            climb_cat, avg_grad = _categorize_climb(clean_ascent, real_dist_m, current_profile)

            # --- 6. Process Compatibility & Technical Specs ---
            breakdown, warnings, compatible = analyze_compatibility(bike.bike_type, tire_mm, extras, surface_map)
            tech_specs = _analyze_technical_difficulty(extras)

            if mud_index > 10:
                warnings.append(f"MUD ALERT: {safety_advice}")

            # --- 7. Final Tactical Briefing Response ---
            return {
                "status": "Success",
                "profile_used": current_profile,
                "tactical_briefing": {
                    "distance_km": round(real_dist_m / 1000, 2), # Now geodesic accurate
                    "elevation_gain_m": clean_ascent,
                    "climb_category": climb_cat,
                    "avg_gradient_est": f"{round(avg_grad, 1)}%",
                    "technical_difficulty": tech_specs,
                    "mud_risk": {
                        "score": mud_index,
                        "label": mud_risk_label,
                        "details": safety_advice,
                        "environmental_factors": env_context
                    }
                },
                "mechanical_setup": {
                    "compatible": compatible,
                    "bike_category": bike.bike_type,
                    "setup_details": tire_display,
                    "rider_weight_baseline": f"{rider.weight_kg}kg"
                },
                "surface_breakdown": breakdown,
                "safety_warnings": warnings
            }

        except Exception as e:
            last_error = str(e)
            continue

    return {"status": "Error", "message": f"Analysis failed: {last_error}"}

def _extract_dominant_surface(surface_extra, surface_map):
    """Helper to find the surface with the highest distance in the route."""
    if not surface_extra or 'summary' not in surface_extra:
        return "Unknown"

    # Find the value with the maximum distance
    dominant_val = max(surface_extra['summary'], key=lambda x: x['distance'])['value']
    return surface_map.get(dominant_val, "Unknown")