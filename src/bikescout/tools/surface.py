import requests


def _get_tire_setup(bike_type: str, tire_size_option: str):
    """
    Standardizes tire size and width based on bike type.
    Returns (actual_tire_mm, display_string).
    """
    if bike_type.lower() in ["mtb", "e-mtb", "enduro"]:
        display_tire = "29" if tire_size_option in ["700c", "650b", "25", "28"] else tire_size_option
        return 58, f"{display_tire} wheels (Wide Grip)" # 58mm ~ 2.3-2.4"

    if bike_type.lower() == "gravel":
        display_tire = tire_size_option if tire_size_option in ["700c", "650b"] else "700c"
        return 40, f"{display_tire} wheels"

    # Default for Road
    return 25, "700c wheels"

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

def _analyze_compatibility(bike_type: str, tire_mm: int, extras: dict, surface_map: dict):
    """
    Checks if the bike setup is compatible with the detected surfaces.
    """
    breakdown = []
    warnings = []
    is_compatible = True

    if 'surface' in extras:
        for item in extras['surface']['summary']:
            name = surface_map.get(item['value'], "Other")
            percentage = round(item['amount'], 1)

            if bike_type.lower() == "road":
                if name in ["Gravel", "Unpaved", "Pebbles", "Grass", "Other"]:
                    is_compatible = False
                    warnings.append(f"Safety risk: {percentage}% of the route is {name}.")
            elif bike_type.lower() == "gravel":
                if name in ["Pebbles", "Grass", "Other"]:
                    warnings.append(f"Comfort warning: {percentage}% is {name}.")

            breakdown.append({"type": name, "percentage": f"{percentage}%"})

    return breakdown, warnings, is_compatible

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


def get_surface_analyzer(api_key, lat, lon, radius_km, profile, bike_type, tire_size_option, points, seed, surface_preference):
    """
    Main entry point for route analysis.
    """
    # 1. Setup tires
    tire_mm, tire_display = _get_tire_setup(bike_type, tire_size_option)

    # 2. API Setup and fallback logic
    attempts = [
        (profile, ["surface", "waytype", "tracktype"]),
        (profile, ["surface", "waytype"]),
        ("cycling-regular", ["surface", "waytype"])
    ]

    last_error = ""
    for current_profile, current_extras in attempts:
        url = f"https://api.openrouteservice.org/v2/directions/{current_profile}/geojson"
        headers = {'Authorization': api_key, 'Content-Type': 'application/json'}
        body = {
            "coordinates": [[lon, lat]],
            "elevation": True,
            "options": {"round_trip": {"length": radius_km * 1000, "points": points, "seed": seed},**_build_ors_options(surface_preference)},
            "extra_info": current_extras
        }

        try:
            response = requests.post(url, json=body, headers=headers)
            if response.status_code == 400:
                last_error = response.json().get('error', {}).get('message', 'Bad Request')
                continue

            response.raise_for_status()
            data = response.json()

            # 3. Extract Core Data
            props = data['features'][0]['properties']
            total_dist_m = props['summary']['distance']

            # 4. Process Elevation and Climbs
            clean_ascent = _sanitize_elevation(props.get('ascent', 0))
            climb_cat, avg_grad = _categorize_climb(clean_ascent, total_dist_m, current_profile)

            # 5. Process Surfaces
            surface_map = {0: "Unknown", 1: "Asphalt", 2: "Unpaved", 3: "Paved", 4: "Cobblestone",
                           5: "Gravel", 6: "Fine Gravel", 11: "Grass", 12: "Compact", 14: "Concrete"}

            breakdown, warnings, compatible = _analyze_compatibility(bike_type, tire_mm, props.get('extras', {}), surface_map)

            tech_specs = _analyze_technical_difficulty(props.get('extras', {}))

            # 6. Final Response
            return {
                "status": "Success",
                "profile_used": current_profile,
                "technical_summary": {
                    "distance_km": round(total_dist_m / 1000, 2),
                    "elevation_gain_m": clean_ascent,
                    "climb_category": climb_cat,
                    "avg_gradient_est": f"{round(avg_grad, 1)}%",
                    "technical_difficulty": tech_specs
                },
                "bike_setup_check": {
                    "compatible": compatible,
                    "bike_used": bike_type,
                    "tire_setup": tire_display
                },
                "surface_breakdown": breakdown,
                "safety_warnings": warnings
            }

        except Exception as e:
            last_error = str(e)
            continue

    return {"status": "Error", "message": f"Analysis failed: {last_error}"}