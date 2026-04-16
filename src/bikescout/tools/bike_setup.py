def analyze_compatibility(bike_type: str, tire_mm: int, extras: dict, surface_map: dict):
    """
    Physics-based compatibility check using tire width (mm) and bike geometry.
    """
    breakdown = []
    warnings = []
    is_compatible = True

    if 'surface' in extras:
        for item in extras['surface']['summary']:
            name = surface_map.get(item['value'], "Other")
            percentage = round(item['amount'], 1)

            # --- 1. Physics-Based Safety Thresholds (Tire Width) ---
            if name in ["Gravel", "Unpaved"]:
                if tire_mm < 28 and percentage > 10.0:
                    is_compatible = False
                    warnings.append(f"CRITICAL: {tire_mm}mm tires are unsafe for {percentage}% {name} (min 28mm).")
                elif tire_mm < 32:
                    warnings.append(f"Caution: {tire_mm}mm tires may lack stability on {percentage}% {name}.")

            elif name in ["Pebbles", "Stony", "Cobblestone"]:
                if tire_mm < 32:
                    warnings.append(f"Safety Alert: Loose stones ({name}) detected. {tire_mm}mm is below recommended safety margin.")

            # --- 2. Traction & Comfort Alerts ---
            elif name in ["Grass", "Muddy", "Earth"]:
                if tire_mm < 42:
                    warnings.append(f"Traction Alert: {percentage}% is {name}. {tire_mm}mm tires may slip in wet/loose conditions.")

            # --- 3. Geometry vs. Rubber (Frame-specific logic) ---
            # Even with wide tires, a pure 'Road' geometry has limits in off-road handling
            if bike_type.lower() == "road":
                if name in ["Gravel", "Unpaved", "Pebbles", "Grass", "Other"] and percentage > 15.0:
                    warnings.append(f"Geometry Warning: {percentage}% {name} exceeds standard road bike handling design.")

            breakdown.append({"type": name, "percentage": f"{percentage}%"})

    return breakdown, warnings, is_compatible