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

import gpxpy
import requests
import math
import sys
import os
import traceback
import numpy as np
import uuid
import random
import matplotlib.pyplot as plt
from fpdf import FPDF
from typing import List, Dict, Any, Optional, Literal
from datetime import date
from geopy.distance import geodesic
from bikescout.tools.weather import get_weather_forecast, apply_weather_windowing
from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.nutrition import get_nutrition_plan

# --- CONSTANTS ---
GRAVITY = 9.80665
AIR_DENSITY = 1.225 # kg/m^3 (approximate at sea level)
CRR_ROAD = 0.004    # Rolling resistance coefficient for road
CDA_CLIMB = 0.35    # Aerodynamic drag coefficient for climbing position

def analyze_track(
        gpx_url: str,
        rider_weight_kg: float = 75,
        rider_gender: Literal["male", "female"] = "male",
        rider_fitness_level: Literal["beginner", "intermediate", "pro"] = "intermediate",
        sweat_profile: Literal["standard", "low", "high", "extreme"] = "standard",
        bike_weight_kg: float = 8.5,
        pro_intensity: float = 1.3,
        activity_type: Literal["road", "mtb"] = "road",
        target_date: Optional[str] = None,
        start_hour: Optional[int] = None,
        end_hour: Optional[int] = None,
        report: bool = False
) -> Dict[str, Any]:
    """
    High-fidelity track audit. Processes GPX data, applies weather windowing,
    calculates performance metrics, identifies strategic tactical zones (weighted for the finale),
    and generates a Technical Director PDF report.
    """
    try:
        # 1. Data Retrieval and Parsing
        content = _load_gpx_content(gpx_url)
        gpx = gpxpy.parse(content)

        points = []
        for track in gpx.tracks:
            for segment in track.segments:
                for p in segment.points:
                    if p.elevation is not None:
                        points.append({
                            'lat': p.latitude, 'lon': p.longitude,
                            'ele': p.elevation, 'time': p.time
                        })

        if len(points) < 10:
            return {"status": "Error", "message": "Insufficient data points in GPX."}

        start_lat, start_lon = points[0]['lat'], points[0]['lon']
        distance_km = round(gpx.length_3d() / 1000, 2)
        total_ascent = round(gpx.get_uphill_downhill().uphill, 1)

        # 2. Path Analysis (Smoothing and Segmenting)
        analysis_segments = _process_segments(points, activity_type)
        uci_climbs = _detect_uci_climbs(analysis_segments)

        # 3. Dynamic Weather Windowing
        # Default window: 09:00 AM to 07:00 PM if not specified
        s_hour = start_hour if start_hour is not None else 9
        e_hour = end_hour if end_hour is not None else 19
        t_date = target_date if target_date else date.today().isoformat()

        weather_data = get_weather_forecast(start_lat, start_lon, t_date)
        ref_temp, ref_wind_speed, ref_wind_dir = 20.0, 10.0, 90

        if weather_data.get("status") == "Success":
            weather_data = apply_weather_windowing(weather_data, s_hour, e_hour)
            ref_cond = weather_data.get("reference_conditions", {})
            ref_temp = ref_cond.get("temp", ref_temp)
            ref_wind_speed = ref_cond.get("wind_speed", ref_wind_speed)
            ref_wind_dir = ref_cond.get("wind_dir_degrees", ref_wind_dir)

        # 4. Environmental and Tactical Assessment
        intensity_score = min(100, int((total_ascent / max(distance_km, 1)) * 10 * pro_intensity))
        duration_hours,est_speed = _estimate_ride_duration(distance_km, total_ascent, rider_fitness_level, activity_type)

        tactical_alerts = []
        mud_risk = None
        if activity_type.lower() == "road":
            tactical_alerts = _calculate_aero_risks(analysis_segments, ref_wind_dir, ref_wind_speed)
        else:
            mapped_surface = "gravel" if "gravel" in activity_type.lower() else "dirt"
            mud_risk = get_mud_risk_analysis(start_lat, start_lon, mapped_surface, t_date)

        nutrition_plan = get_nutrition_plan(duration_hours, ref_temp, intensity_score, rider_weight_kg, rider_gender, sweat_profile)
        performance = _calculate_performance(uci_climbs, rider_weight_kg, bike_weight_kg, pro_intensity, ref_temp, ref_wind_speed)

        # 5. Strategic Zone Identification (Weighted for the finale)
        tactical_output = _identify_tactical_zones(analysis_segments, uci_climbs, distance_km)

        elev_extremes = gpx.get_elevation_extremes()

        final_json = {
            "status": "Success",
            "mode": activity_type.upper(),
            "target_date": t_date,
            "track_metrics": {
                "distance_km": distance_km,
                "total_ascent": total_ascent,
                "max_altitude": round(getattr(elev_extremes, 'maximum', 0), 1)
            },
            "planning_tools": {
                "weather_forecast": weather_data,
                "nutrition_plan": nutrition_plan,
                "mud_risk": mud_risk
            },
            "climb_analysis": uci_climbs,
            "performance_simulation": performance,
            "tactical_alerts": tactical_alerts,
            "pre_climb_positioning": tactical_output["pre_climb_positioning"],
            "tactical_action_zones": tactical_output["action_zones"]
        }

        # 6. PDF Report Generation with Elevation Chart and DS Briefing
        if report:
            plot_path = _generate_elevation_plot(analysis_segments, t_date)
            pdf_path = _generate_pdf_report(final_json, plot_path)
            final_json["report_path"] = pdf_path

        return final_json

    except Exception as e:
        sys.stderr.write(f"ANALYSIS FAILURE: {traceback.format_exc()}\n")
        return {"status": "Error", "message": str(e)}

def _estimate_ride_duration(distance_km: float, total_ascent_m: float, rider_fitness_level: str, activity_type: str):
    """
    Calculates a realistic estimated speed to avoid under-fueling.
    Adjusts base speed based on fitness level and climbing intensity.
    """
    # 1. Base speed mapping (Conservative estimates for amateurs)
    base_speeds = {
        "beginner": {"road": 20.0, "gravel": 15.0, "mtb": 12.0},
        "intermediate": {"road": 26.0, "gravel": 20.0, "mtb": 15.0},
        "pro": {"road": 34.0, "gravel": 27.0, "mtb": 22.0}
    }

    # Get speeds for the specific rider profile
    rider_speeds = base_speeds.get(rider_fitness_level, base_speeds["intermediate"])
    est_speed = rider_speeds.get(activity_type.lower(), rider_speeds["road"])

    # 2. Climbing Penalty (The "Gravity Tax")
    # Every 100m of climbing per 10km significantly reduces average speed
    climbing_density = total_ascent_m / (distance_km / 10)
    # Penalty: reduce speed by ~1% for every 50m of climbing density
    climbing_penalty = (climbing_density / 50.0) * 0.01

    final_est_speed = est_speed * (1.0 - climbing_penalty)

    # Ensure speed doesn't drop below a walking pace (safety floor)
    final_est_speed = max(final_est_speed, 8.0)

    duration_hours = distance_km / final_est_speed
    return duration_hours, final_est_speed

def _load_gpx_content(gpx_path: str) -> str:
    """Fetches GPX content from the web or local file system."""
    if gpx_path.startswith(('http://', 'https://')):
        res = requests.get(gpx_path, timeout=20)
        res.raise_for_status()
        return res.text
    with open(gpx_path, 'r', encoding='utf-8') as f:
        return f.read()

def _process_segments(points: List[Dict], surface: str) -> List[Dict]:
    """Smooths raw elevation data and groups it into measurable segments."""
    dist_filter = 25.0 if surface == "road" else 15.0
    grade_cap = 25.0 if surface == "road" else 35.0

    elevations = [p['ele'] for p in points]
    smoothed_ele = np.convolve(elevations, np.ones(10)/10, mode='same')

    segments = []
    accum_d, total_elapsed, start_idx = 0.0, 0.0, 0
    for i in range(len(points) - 1):
        d = geodesic((points[i]['lat'], points[i]['lon']), (points[i+1]['lat'], points[i+1]['lon'])).meters
        accum_d += d
        total_elapsed += d

        if accum_d >= dist_filter:
            grade = ((smoothed_ele[i+1] - smoothed_ele[start_idx]) / accum_d) * 100

            # Cold start protection
            if total_elapsed < 500:
                grade = max(min(grade, 8.0), -8.0)
            else:
                grade = max(min(grade, grade_cap), -grade_cap)

            # Bearing calculation for crosswind alerts
            lat1, lon1, lat2, lon2 = map(math.radians, [points[i]['lat'], points[i]['lon'], points[i+1]['lat'], points[i+1]['lon']])
            y = math.sin(lon2 - lon1) * math.cos(lat2)
            x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
            bearing = (math.degrees(math.atan2(y, x)) + 360) % 360

            segments.append({
                'dist': accum_d, 'grade': grade, 'bearing': bearing,
                'ele_start': smoothed_ele[start_idx], 'ele_end': smoothed_ele[i+1]
            })
            start_idx, accum_d = i + 1, 0.0
    return segments

def _detect_uci_climbs(segments: List[Dict]) -> List[Dict]:
    """Isolates significant uphill sections and categorizes them."""
    climbs, current, flat_b = [], [], 0
    for s in segments:
        if s['grade'] >= 1.5:
            current.append(s)
            flat_b = 0
        elif current:
            flat_b += s['dist']
            current.append(s)
            if flat_b > 1000:
                while current and current[-1]['grade'] < 1.0: current.pop()
                _finalize_climb_data(current, segments, climbs)
                current, flat_b = [], 0
    if current:
        while current and current[-1]['grade'] < 1.0: current.pop()
        _finalize_climb_data(current, segments, climbs)
    return climbs

def _finalize_climb_data(current_climb, all_segments, climbs_list):
    """Calculates final metrics for a climb with Pro-Tour filtering logic."""
    if not current_climb: return

    total_dist = sum(x['dist'] for x in current_climb)
    total_gain = current_climb[-1]['ele_end'] - current_climb[0]['ele_start']
    avg_grade = (total_gain / total_dist) * 100

    # Discard shallow or insignificant bumps
    if avg_grade < 3.5 and total_gain < 250:
        return

    if total_dist > 1500 and total_gain > 100:
        score = (total_gain * avg_grade) / 10
        start_idx = all_segments.index(current_climb[0])
        km_start = sum(x['dist'] for x in all_segments[:start_idx]) / 1000

        # Mapping to categories
        category = "HC" if score >= 800 or total_gain >= 1000 else \
            "Cat 1" if score >= 400 or total_gain >= 600 else \
                "Cat 2" if score >= 200 or total_gain >= 350 else \
                    "Cat 3" if (score >= 100 or total_gain >= 150) and total_dist > 2500 else "Cat 4"

        climbs_list.append({
            "km_start": round(km_start, 1),
            "dist_km": round(total_dist / 1000, 2),
            "gain_m": round(total_gain, 1),
            "avg_grade": round(avg_grade, 1),
            "category": category
        })

def _identify_tactical_zones(segments: List[Dict], uci_climbs: List[Dict], total_dist: float) -> Dict:
    """
    Enhanced tactical detection classifying zones and applying a recency bias
    so points in the final 60km are heavily favored for strategic importance.
    """
    pre_climb = []

    # 1. ALWAYS isolate Major Climb Positioning
    for c in uci_climbs:
        if c['category'] in ['HC', 'Cat 1']:
            pre_climb.append({
                "km": round(c['km_start'] - 0.8, 2),
                "type": f"CRITICAL POSITIONING: {c['category']} Entrance",
                "detail": f"Climb {c['dist_km']}km @ {c['avg_grade']}%"
            })

    # 2. Extract Action Zones with Recency Bias
    raw_zones = []
    curr_d = 0.0
    for s in segments:
        curr_d += s['dist']
        km = curr_d / 1000
        abs_grade = abs(s['grade'])

        # We look for steep segments
        if abs_grade > 10.0:
            dist_to_finish = total_dist - km

            # The closer to the finish (within 60km), the higher the multiplier
            weight = 1.0
            if 0 < dist_to_finish <= 60:
                # Multiplier scales linearly from 1.0 at 60km to 2.5 at 0km
                weight = 1.0 + (1.5 * (60 - dist_to_finish) / 60)

            score = abs_grade * weight

            # Categorize the base physical difficulty without the bias
            diff = "high" if abs_grade > 14 else "medium" if abs_grade > 11 else "low"
            z_type = "Explosive Wall / Attack Point" if s['grade'] > 0 else "Steep Technical Descent"

            raw_zones.append({
                "km": round(km, 2),
                "grade": round(s['grade'], 1),
                "score": score,
                "type": z_type,
                "difficulty": diff
            })

    # 3. Sort by our weighted tactical score descending
    raw_zones.sort(key=lambda x: x['score'], reverse=True)

    # 4. Limit Outputs per requirements: max 3 high, 2 medium, 1 low
    # and ensure they are physically separated (min 1km apart)
    final_action = []
    targets = {"high": 3, "medium": 2, "low": 1}

    for z in raw_zones:
        if targets[z['difficulty']] > 0:
            # Avoid picking zones that are essentially the same hill
            if all(abs(z['km'] - existing['km']) > 1.0 for existing in final_action):
                # Remove the internal 'score' before final output
                final_action.append({
                    "km": z['km'], "grade": z['grade'],
                    "type": z['type'], "difficulty": z['difficulty']
                })
                targets[z['difficulty']] -= 1

    # 5. Re-sort chronologically for the user
    final_action.sort(key=lambda x: x['km'])

    return {
        "pre_climb_positioning": pre_climb,
        "action_zones": final_action
    }

def _calculate_performance(climbs, rider_w, bike_w, intensity, temp, wind_speed) -> List[Dict]:
    """Physics model to solve required W/Kg and estimated time/VAM."""
    results = []
    total_mass = rider_w + bike_w
    target_wkg = 3.8 * intensity
    target_power = target_wkg * rider_w

    for c in climbs:
        grade_decimal = c['avg_grade'] / 100
        theta = math.atan(grade_decimal)

        v_mps = 2.0
        for _ in range(10): # Newton-Raphson approximation
            f_grav = total_mass * GRAVITY * math.sin(theta)
            f_roll = total_mass * GRAVITY * math.cos(theta) * CRR_ROAD
            f_aero = 0.5 * AIR_DENSITY * CDA_CLIMB * (v_mps ** 2)
            p_total = v_mps * (f_grav + f_roll + f_aero)
            dp_dv = f_grav + f_roll + 1.5 * AIR_DENSITY * CDA_CLIMB * (v_mps ** 2)
            v_mps = v_mps - (p_total - target_power) / dp_dv

        speed_kmh = max(v_mps * 3.6, 5.0)
        time_hours = c['dist_km'] / speed_kmh
        vam = c['gain_m'] / time_hours

        penalty = (target_power * 0.03 if temp > 28 else 0) + (target_power * 0.02 if wind_speed > 15 else 0)
        adj_wkg = (target_power + penalty) / rider_w

        results.append({
            "climb": f"Climb @ km {c['km_start']} ({c['category']})",
            "est_time_min": round(time_hours * 60, 1),
            "est_vam": round(vam),
            "target_wkg": round(target_wkg, 2),
            "weather_adjusted_wkg": round(adj_wkg, 2)
        })
    return results

def _calculate_aero_risks(segments, wind_dir, wind_speed) -> List[Dict]:
    """Identifies potential echelon formation zones due to crosswinds."""
    alerts = []
    if wind_speed < 18: return []
    for i in range(0, len(segments), 45):
        s = segments[i]
        rel_angle = abs(s['bearing'] - wind_dir) % 360
        if rel_angle > 180: rel_angle = 360 - rel_angle

        if 60 < rel_angle < 120:
            dist_at = sum(x['dist'] for x in segments[:i]) / 1000
            alerts.append({
                "km": round(dist_at, 1), "type": "ECHELON RISK",
                "detail": f"{round(wind_speed, 1)}km/h Crosswind"
            })
    return alerts[:4]

def _generate_elevation_plot(segments: List[Dict], target_date: str) -> str:
    """Uses matplotlib to generate a track elevation profile image."""
    x_dist = []
    y_ele = []
    curr_dist = 0.0

    for s in segments:
        curr_dist += s['dist'] / 1000
        x_dist.append(curr_dist)
        y_ele.append(s['ele_end'])

    plt.figure(figsize=(10, 3.5))
    plt.fill_between(x_dist, y_ele, color='steelblue', alpha=0.3)
    plt.plot(x_dist, y_ele, color='midnightblue', linewidth=1.5)

    plt.title('Stage Elevation Profile', fontsize=12, fontweight='bold')
    plt.xlabel('Distance (km)', fontsize=10)
    plt.ylabel('Elevation (m)', fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    # Save to local directory
    save_dir = os.path.join(os.path.expanduser("~"), ".bikescout", "race")
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"profile_{target_date}.png")

    plt.savefig(file_path, dpi=150)
    plt.close()

    return file_path

def _generate_pdf_report(data: Dict[str, Any], plot_path: str) -> str:
    """
    Generates a fluent English PDF report including the altimetry chart,
    dynamic DS Briefing and official BikeScout branding.
    """

    # --- 1. Setup Directories and Unique File Paths ---
    report_dir = os.path.join(os.path.expanduser("~"), ".bikescout", "race")
    os.makedirs(report_dir, exist_ok=True)

    # Generate a unique ID to prevent file overriding on the same date
    unique_id = uuid.uuid4().hex[:6]
    target_date = data.get('target_date', 'unknown')
    file_path = os.path.join(report_dir, f"race_report_{target_date}_{unique_id}.pdf")

    # --- 2. Custom PDF Class for Footer Branding ---
    class BikeScoutPDF(FPDF):
        def footer(self):
            """Adds the official BikeScout footer at the bottom of every page."""
            self.set_y(-15) # Position 15mm from the bottom
            self.set_font("Arial", 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, "Produced by BikeScout - https://hifly81.github.io/bikescout/", 0, 0, 'C')

    # --- 4. Initialize PDF ---
    pdf = BikeScoutPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(0, 10, txt="BikeScout Pro Race Strategy Report", ln=True, align='C')
    pdf.ln(5)

    # Insert Global Elevation Profile Image
    if os.path.exists(plot_path):
        pdf.image(plot_path, x=10, y=pdf.get_y(), w=190)
        pdf.set_y(pdf.get_y() + 65)
    else:
        pdf.ln(10)

    # ---------------------------------------------------------
    # TECHNICAL DIRECTOR BRIEFING (Dynamic & Data-Driven)
    # ---------------------------------------------------------
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Technical Director Briefing", ln=True)
    pdf.set_font("Arial", '', 11)

    # Track metrics
    metrics = data.get('track_metrics', {})
    dist = float(metrics.get('distance_km', 0.0))
    asc = float(metrics.get('total_ascent', 0.0))
    climbs = data.get('climb_analysis', [])
    zones = data.get('tactical_action_zones', [])
    weather = data.get("planning_tools", {}).get("weather_forecast", {}).get("reference_conditions", {})

    profile_ratio = asc / dist if dist > 0 else 0
    is_xc_circuit = dist < 15.0 and profile_ratio > 15.0 # XC Mountain Bike Detection

    # Evaluate Stage Profile
    if is_xc_circuit:
        intro = f"Team, we are looking at a punchy XC circuit today: {dist} km per lap with {asc} meters of elevation gain. Forget pacing; this requires repeated VO2 max efforts and flawless technical execution on every lap. "
    elif profile_ratio >= 22:
        intro = f"Team, today is a brutal day in the mountains: {dist} km and a massive {asc} meters of elevation. Survival and GC preservation are our primary directives. "
    elif profile_ratio >= 12:
        intro = f"We have {dist} km with {asc} meters of climbing on the menu. It's a leg-breaking, rolling parcours that perfectly favors a strong breakaway or late puncheur attacks. "
    else:
        intro = f"At {dist} km and only {asc} m of climbing, this is ostensibly a flat stage. Staying safe, hiding from the wind, and delivering our sprinter is everything today. "

    # Dynamic Weather Impacts
    temp = weather.get('temp', 20)
    wind = weather.get('wind_speed', 10)
    wx_str = f"Expect conditions around {temp}C with winds at {wind} km/h. "

    if temp >= 30:
        wx_str += "The heat is going to be a major factor; constant hydration and ice packs are mandatory. "
    elif temp <= 10:
        wx_str += "It's going to be freezing out there. Keep your core warm, especially before the technical descents. "
    if wind >= 20:
        wx_str += "Wind speeds are absolutely high enough to split the peloton. Stay vigilant and ride at the front to avoid echelon traps! "

    # Dynamic Ignition Point
    tactical_str = ""
    if zones:
        sorted_zones = sorted(zones, key=lambda x: x.get('km', 0))
        late_zones = [z for z in sorted_zones if z.get('km', 0) >= (dist * 0.5)]

        if late_zones:
            ignition_zone = max(late_zones, key=lambda z: (z.get('difficulty') == 'high', abs(z.get('grade', 0))))
        else:
            ignition_zone = max(sorted_zones, key=lambda z: (z.get('difficulty') == 'high', abs(z.get('grade', 0))))

        ignite_km = ignition_zone.get('km', 0)
        zone_type = ignition_zone.get('type', 'sector').lower()
        zone_grade = ignition_zone.get('grade', 0)
        dist_to_go = dist - ignite_km

        if is_xc_circuit:
            tactical_str = f"The primary launchpad for attacks is the {zone_type} around km {ignite_km} ({zone_grade}% grade). Hit it hard every single lap. "
        elif dist_to_go > (dist * 0.4):
            tactical_str = f"Based on the topography, the race will blow apart unusually early, around km {ignite_km}. We cannot afford to be caught sleeping when the {zone_type} starts. From there, it's a pure race of attrition. "
        elif dist_to_go < 15:
            tactical_str = f"It all comes down to a late, explosive finale. The decisive move will likely happen on the {zone_type} at km {ignite_km}, just {round(dist_to_go, 1)} km from the line. It kicks up to {zone_grade}%. Be perfectly positioned before this point. "
        else:
            tactical_str = f"The true battle for the stage begins at km {ignite_km}. That {zone_type} (hitting gradients of {zone_grade}%) is the natural launchpad for the winning move. "

        if not is_xc_circuit:
            tactical_str += "If you have the legs, this is where you commit. "
    else:
        tactical_str = "There are no extreme technical features today. Positioning and tactical awareness will dictate the finale. "

    # ---------------------------------------------------------
    # REASONED CLOSING STATEMENT (Logic-Driven)
    # ---------------------------------------------------------

    if is_xc_circuit:
        # Focus on Technical & Start for XC
        if temp >= 28:
            closing = "Heat will spike your HR on this circuit. Use the descents for active cooling and hydration."
        else:
            closing = "Nail the start loop to avoid traffic. It's a high-intensity battle from the gun."
    else:
        # Focus on Strategy & Endurance for Road/P2P
        if wind >= 22:
            closing = "The wind is the real enemy today. Stay tucked in and never be the first to break the line."
        elif profile_ratio >= 20:
            closing = "This is a war of attrition. Save every watt for the final two climbs; nutrition is non-negotiable."
        elif dist > 150:
            closing = "It's a long day. Stay hydrated early so you have the clarity to make the right move in the final 20km."
        else:
            closing = "Positioning is everything today. Communicate with the team and stay in the top 20 before the decisive sectors."

    # Final motivation punch
    closing += " Let's go execute."

    briefing = intro + wx_str + tactical_str + closing
    pdf.multi_cell(0, 6, txt=briefing)
    pdf.ln(10)

    # ---------------------------------------------------------
    # Detailed Tactical Zones Table
    # ---------------------------------------------------------
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Detailed Tactical Zones", ln=True)
    pdf.set_font("Arial", '', 10)

    if not zones:
        pdf.cell(0, 6, txt="No high-risk tactical zones identified.", ln=True)
    for z in zones:
        diff_str = str(z.get('difficulty', 'unknown')).upper()
        pdf.cell(0, 6, txt=f"- KM {z.get('km', 0)}: {z.get('type', 'Unknown')} | Grade: {z.get('grade', 0)}% [Severity: {diff_str}]", ln=True)

    pdf.output(file_path)

    # Clean up temporary climb images
    for f in os.listdir(report_dir):
        if f.startswith("climb_") and f.endswith(f"_{unique_id}.png"):
            try:
                os.remove(os.path.join(report_dir, f))
            except OSError:
                pass

    return file_path
