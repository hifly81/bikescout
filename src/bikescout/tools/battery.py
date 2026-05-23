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

import math

def calculate_battery_drain(
        battery_wh: float,
        assist_level: str,
        weight_kg: float,
        ascent_m: float,
        distance_km: float,
        surface_breakdown: any,
        mud_index: float,
        avg_speed_kmh: float = 18.0,
        ambient_temp_c: float = 20.0,
        rider_ftp_w: int = 200,
        intensity_score: int = 3
):
    """
    Tactical Battery Intelligence v3.0: Total Resistance Force (TRF) Model.
    Calculates drain based on gravity, rolling resistance (Crr), aero drag (CdA),
    and metabolic split between the rider and the mid-drive motor.
    """

    # Usable Capacity: Modern BMS reserves ~5-8% to protect cells
    usable_wh = battery_wh * 0.93

    # Temperature Derating: Capacity drops in cold weather (~1% per degree below 15°C)
    if ambient_temp_c < 15:
        temp_penalty = (15 - ambient_temp_c) * 0.01
        usable_wh *= (1 - temp_penalty)

    velocity_ms = avg_speed_kmh / 3.6
    gravity = 9.81
    air_density = 1.225  # kg/m^3 at sea level
    cda = 0.45           # Typical CdA for an MTB rider in upright position

    # Grade calculation (tan theta)
    grade = ascent_m / (distance_km * 1000) if distance_km > 0 else 0
    theta = math.atan(grade)

    # A. Gravitational Power (P_gravity)
    p_gravity = weight_kg * gravity * velocity_ms * math.sin(theta)

    # B. Aero Drag Power (P_aero = 0.5 * rho * CdA * v^3)
    p_aero = 0.5 * air_density * cda * (velocity_ms ** 3)

    # C. Rolling Resistance Power (P_rolling)
    # Crr values based on surface type analysis
    surface_crr_map = {
        "Asphalt": 0.004,
        "Gravel": 0.015,
        "Fine Gravel": 0.012,
        "Dirt": 0.020,
        "Grass": 0.030,
        "Sand": 0.060,
        "Deep Mud": 0.080
    }

    # Calculate weighted Crr from breakdown
    avg_crr = 0.015 # Fallback/Default
    if isinstance(surface_breakdown, dict) and surface_breakdown:
        weighted_crr = 0
        for surf, pct in surface_breakdown.items():
            crr_val = surface_crr_map.get(surf, 0.020)
            weighted_crr += (crr_val * (pct / 100))
        avg_crr = weighted_crr

    # Add Mud Penalty to Crr (Non-linear increase in rolling friction)
    avg_crr += (mud_index * 0.05)

    p_rolling = avg_crr * weight_kg * gravity * velocity_ms * math.cos(theta)

    # Total Power required to maintain velocity
    p_required = p_gravity + p_aero + p_rolling

    # Estimate Rider Power based on FTP and Mission Intensity Score (1-5)
    # Score 1: 40% FTP, Score 3: 75% FTP, Score 5: 100% FTP
    intensity_mult = 0.25 + (intensity_score * 0.15)
    p_rider = rider_ftp_w * intensity_mult

    # Calculate remaining power needed from motor
    # Assistance levels cap the motor contribution ratio
    assist_ratios = {"Eco": 0.6, "Trail": 2.0, "Boost": 3.4}
    max_assist_ratio = assist_ratios.get(assist_level, 2.0)

    p_motor_raw = max(0, p_required - p_rider)

    # Ensure motor power doesn't exceed ratio vs rider (unless in Boost/Safety)
    if p_motor_raw > (p_rider * max_assist_ratio):
        p_motor_raw = p_rider * max_assist_ratio

    # Efficiency drops under high torque/low RPM (climbing) or overheating
    efficiency = 0.85 # Peak mid-drive efficiency
    if grade > 0.08: # Steep climb penalty
        efficiency -= 0.10
    if ambient_temp_c > 30: # Heat dissipation penalty
        efficiency -= 0.05

    p_motor_final = p_motor_raw / efficiency

    total_time_hours = distance_km / avg_speed_kmh
    total_wh_spent = p_motor_final * total_time_hours

    remaining_wh = max(0, usable_wh - total_wh_spent)
    remaining_pct = round((remaining_wh / battery_wh) * 100, 1)

    status = "SAFE"
    if remaining_pct < 15:
        status = "CRITICAL"
    elif remaining_pct < 25:
        status = "WARNING"

    return {
        "status": "Success",
        "battery_metrics": {
            "estimated_drain_wh": round(total_wh_spent, 1),
            "remaining_battery_pct": remaining_pct,
            "safety_buffer_status": status,
            "usable_wh_at_temp": round(usable_wh, 1)
        },
        "power_breakdown_w": {
            "gravity_resistance": round(p_gravity, 1),
            "rolling_resistance": round(p_rolling, 1),
            "aerodynamic_drag": round(p_aero, 1),
            "rider_contribution": round(p_rider, 1),
            "motor_net_output": round(p_motor_raw, 1)
        },
        "tactical_advice": "Switch to lower assist on flats to save range" if status != "SAFE" else "Pace maintained"
    }
