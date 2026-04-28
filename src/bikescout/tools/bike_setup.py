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

def get_tire_setup(bike_type: str, tire_size_option: str, mud_index: float = 0.0, surface_type: str = "mixed", rider_weight_kg: float = 80.0):
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
