import requests
import numpy as np
from datetime import datetime, date
from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.geophysic import calculate_geodetic_segment
from bikescout.tools.bike_setup import analyze_compatibility
from bikescout.tools.bike_setup import get_tire_setup
from bikescout.tools.battery import calculate_battery_drain
from bikescout.schemas import RiderProfile, BikeSetup, MissionConstraints

def _sanitize_elevation_profile(geometry, window_size=7, threshold=0.5):
    """
    Filters satellite SRTM noise using a Simple Moving Average and Hysteresis.
    Ensures that flat roads don't accumulate 'phantom' elevation gain.
    """
    elevations = [p[2] for p in geometry if len(p) > 2]
    if len(elevations) < window_size:
        return 0.0

    # Apply SMA smoothing
    weights = np.ones(window_size) / window_size
    smoothed = np.convolve(elevations, weights, mode='valid')

    total_ascent = 0.0
    for i in range(1, len(smoothed)):
        diff = smoothed[i] - smoothed[i-1]
        # Only count ascent if change exceeds 0.5m (Hysteresis)
        if diff > threshold:
            total_ascent += diff

    return round(total_ascent, 0)

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

def _analyze_technical_difficulty(extras: dict, fitness_level: str = "intermediate"):
    """
    Parses OSM tags for technical grading and cross-references with rider fitness.
    """
    # 1. MTB Scale (Singletrail-Skala S0-S5)
    mtb_summary = extras.get('mtb_scale', {}).get('summary', [])
    mtb_val = str(mtb_summary[0].get('value', 'N/A')) if mtb_summary else 'N/A'

    scale_info = {
        "0": "S0: Smooth, paved/firm trails without obstacles.",
        "1": "S1: Small roots/stones, easy technical sections.",
        "2": "S2: Loose soil, larger roots/stones, steps required.",
        "3": "S3: Technical rock gardens, high steps, hairpins.",
        "4": "S4: Extreme steepness, tight switchbacks, trial skills.",
        "5": "S5: Near-vertical terrain, maximum difficulty."
    }

    # 2. Trail Visibility
    vis_summary = extras.get('trail_visibility', {}).get('summary', [])
    vis_val = str(vis_summary[0].get('value', '1')) if vis_summary else '1'
    vis_map = {"1": "Excellent", "2": "Good", "3": "Poor", "4": "Invisible/Requires GPS"}

    # 3. Fitness-Based Technical Advice
    # Se il livello tecnico è S2+ e il rider è beginner, aggiungiamo un warning.
    tech_note = "Technical grading based on OSM mountain standards."

    try:
        level_int = int(mtb_val)
        if fitness_level == "beginner" and level_int >= 2:
            tech_note = "FITNESS ALERT: This trail requires technical maneuvers (S2+) that might be exhausting for a beginner."
        elif fitness_level == "pro" and level_int >= 3:
            tech_note = "PRO ADVICE: High technicality (S3+) detected. Ideal for testing suspension and technical handling."
        elif fitness_level == "beginner" and level_int <= 1:
            tech_note = "Confidence Builder: Technical level is well-suited for your fitness and skill profile."
    except ValueError:
        pass # mtb_val is N/A or non-numeric

    return {
        "mtb_scale": scale_info.get(mtb_val, "Standard / Unclassified"),
        "trail_visibility": vis_map.get(vis_val, "Standard"),
        "technical_notes": tech_note,
        "fitness_context": f"Evaluated for {fitness_level} level"
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

def get_surface_analyzer(api_key, lat, lon, rider, bike, mission, target_date: str = None):
    """
    Analyzes route surfaces and tactical risks by integrating OpenRouteService geometry
    with TAEL Mud Intelligence (v2.5) and E-MTB performance metrics.

    This method employs an adaptive fallback strategy to prevent ORS 400 errors by
    dynamically stripping unsupported 'extra_info' (like tracktype) depending on the
    routing profile. It also performs safe E-MTB power consumption analysis only
    when specific hardware criteria are met.

    Args:
        api_key (str): OpenRouteService API Authorization token.
        lat (float): Starting latitude.
        lon (float): Starting longitude.
        rider (object): Contains rider-specific data (weight_kg, fitness_level).
        bike (object): Contains hardware specs (bike_type, tire_size, battery_wh).
        mission (object): Contains mission parameters (radius_km, profile, complexity, seed).
        target_date (str, optional): YYYY-MM-DD date for predictive mud analysis.
                                     Defaults to current date if None.

    Returns:
        dict: A structured report containing tactical briefing, mechanical setup,
              surface breakdown, and E-MTB analytics.
    """

    # 1. Parameter Normalization
    safe_complexity = max(3, min(int(getattr(mission, 'complexity', 10)), 30))
    safe_length = int(mission.radius_km * 1000)

    # 2. Strategic fallback system
    attempts = [
        (mission.profile, ["surface", "waytype"]),
        (mission.profile, ["surface", "waytype"]),
        ("cycling-regular", ["surface", "waytype"])
    ]

    last_error = ""
    for current_profile, requested_extras in attempts:
        try:

            url = f"https://api.openrouteservice.org/v2/directions/{current_profile}/geojson"
            headers = {'Authorization': api_key, 'Content-Type': 'application/json'}

            # ORS Request Body
            body = {
                "coordinates": [[lon, lat]],
                "elevation": True,
                "extra_info": requested_extras,
                "options": {
                    "round_trip": {
                        "length": safe_length,
                        "points": safe_complexity,
                        "seed": int(getattr(mission, 'seed', 42))
                    }
                }
            }

            res = requests.post(url, json=body, headers=headers, timeout=15)

            if res.status_code != 200:
                # Capture the specific reason for failure
                try:
                    detail = res.json().get('error', {}).get('message', res.text)
                except:
                    detail = res.text

                last_error = f"ORS {res.status_code}: {detail}"
                continue # Try the next fallback profile/extra combo
            data = res.json()

            # ORS GeoJSON structure: features -> [0] -> properties -> extras
            feature = data['features'][0]
            props = feature.get('properties', {})
            geometry = feature.get('geometry', {}).get('coordinates', [])

            # Extras can contain 'surface', 'waytype', etc.
            extras = props.get('extras', {})

            # 3. Terrain Intelligence
            clean_ascent = _sanitize_elevation_profile(geometry, 7, 0.5)

            # Distance calculation (Geodesic)
            real_dist_m = 0
            for i in range(len(geometry) - 1):
                p1, p2 = geometry[i], geometry[i+1]
                real_dist_m += calculate_geodetic_segment(p1[1], p1[0], p2[1], p2[0])["distance"]

            # Surface Mapping
            surface_map = {0: "Unknown", 1: "Asphalt", 2: "Unpaved", 3: "Paved", 5: "Gravel", 11: "Grass", 14: "Concrete"}
            dominant_surface = _extract_dominant_surface(extras.get('surface', {}), surface_map)

            # Mud Analysis (TAEL v2.5)
            mud_analysis = get_mud_risk_analysis(lat, lon, dominant_surface, target_date)
            t_analysis = mud_analysis.get("tactical_analysis") or {}

            # Force numeric float
            raw_mud = t_analysis.get("mud_risk_numeric")
            mud_score_val = float(raw_mud) if raw_mud is not None else 0.0

            # 4. Mechanical & Performance Audit
            tire_mm, tire_display = get_tire_setup(
                bike_type=bike.bike_type,
                tire_size_option=bike.tire_size,
                mud_index=mud_score_val,
                surface_type=dominant_surface,
                rider_weight_kg=rider.weight_kg
            )

            climb_cat, avg_grad = _categorize_climb(clean_ascent, real_dist_m, current_profile)
            breakdown, warnings, compatible = analyze_compatibility(bike.bike_type, tire_mm, extras, surface_map)

            # --- 5. E-MTB Power Management (Safe Detection) ---
            emtb_analysis = None

            # Check if it's an E-Bike: must have "E-" in name AND a valid battery capacity
            bike_type_str = str(getattr(bike, 'bike_type', "")).upper()
            battery_cap = getattr(bike, 'battery_wh', 0)

            # Ensure battery_cap is a number before comparison
            if not isinstance(battery_cap, (int, float)):
                battery_cap = 0

            is_emtb = "E-" in bike_type_str and battery_cap > 0

            if is_emtb:
                try:
                    emtb_analysis = calculate_battery_drain(
                        battery_wh=battery_cap,
                        assist_level=getattr(mission, 'assist_mode', "Trail"),
                        weight_kg=float(getattr(rider, 'weight_kg', 80)) + 24, # 24kg is avg E-bike weight
                        ascent_m=clean_ascent,
                        distance_km=real_dist_m / 1000,
                        surface_breakdown=breakdown,
                        mud_index=mud_score_val
                    )
                except Exception as e_emtb:
                    emtb_analysis = {"error": "Battery calculation failed"}

            return {
                "status": "Success",
                "profile_used": current_profile,
                "metadata": {
                    "analyzed_date": mud_analysis.get("metadata", {}).get("target_date"),
                    "api_extras": list(extras.keys())
                },
                "tactical_briefing": {
                    "distance_km": round(real_dist_m / 1000, 2),
                    "elevation_gain_m": clean_ascent,
                    "climb_category": climb_cat,
                    "avg_gradient_est": f"{round(avg_grad, 1)}%",
                    "mud_intelligence": {
                        "score": mud_score_val,
                        "label": t_analysis.get("mud_risk_score", "Unknown"),
                        "safety_advice": t_analysis.get("safety_advice", "Check local conditions.")
                    }
                },
                "mechanical_setup": {
                    "compatible": compatible,
                    "setup_details": tire_display,
                    "bike_type": bike.bike_type
                },
                "surface_breakdown": breakdown,
                "emtb_tactical": emtb_analysis,
                "safety_warnings": warnings
            }


        except Exception as e:
            last_error = f"Local processing error: {str(e)}"
            continue

    return {"status": "Error", "message": f"Global failure: {last_error}"}

def _extract_dominant_surface(surface_extra, surface_map):
    """Helper to find the surface with the highest distance in the route."""
    if not surface_extra or 'summary' not in surface_extra:
        return "Unknown"

    # Find the value with the maximum distance
    dominant_val = max(surface_extra['summary'], key=lambda x: x['distance'])['value']
    return surface_map.get(dominant_val, "Unknown")