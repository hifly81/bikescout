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

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import io
import base64
import uuid
import time
from geopy.distance import geodesic
from pathlib import Path
from bikescout.schemas import RouteGeometry
from typing import Literal

def _generate_altimetry_plot(geometry: list, width: int = 8, height: int = 3, style: str = "filled"):
    """
    Generates an elevation profile plot with high-precision geodetic distances.
    Uses WGS-84 Geodesic distances to ensure X-axis accuracy (prevents coordinate compression).
    """
    if not geometry or len(geometry) < 2:
        return None

    healed_geometry = []
    for i in range(len(geometry)):
        lon, lat, ele = geometry[i]
        if (ele <= 0 or (i > 0 and abs(ele - geometry[i-1][2]) > 200)) and i > 0:
            ele = healed_geometry[i-1][2]
        healed_geometry.append([lon, lat, ele])

    geometry = healed_geometry
    elevations = [p[2] for p in geometry]

    distances = [0]
    total_dist = 0
    for i in range(len(geometry) - 1):
        p1, p2 = geometry[i], geometry[i+1]

        d = geodesic((p1[1], p1[0]), (p2[1], p2[0])).meters

        total_dist += d
        distances.append(total_dist)

    dist_km = [d / 1000 for d in distances]

    grades = []
    for i in range(len(elevations) - 1):
        rise = elevations[i+1] - elevations[i]
        run = distances[i+1] - distances[i]

        g = (rise / run) * 100 if run > 0.1 else 0
        grades.append(np.clip(g, -25, 25))
    grades.append(0)

    plt.figure(figsize=(width, height), dpi=100)
    ax = plt.gca()

    cmap = mcolors.LinearSegmentedColormap.from_list("grav_cmap", ["#2ecc71", "#f1c40f", "#e74c3c"])
    norm = mcolors.Normalize(vmin=0, vmax=12)
    min_ele = min(elevations)

    if style == "sparkline":
        plt.plot(dist_km, elevations, color='#2c3e50', linewidth=2)
        plt.axis('off')

    elif style == "bars":
        for i in range(len(dist_km) - 1):
            avg_grade = abs(grades[i])
            color = cmap(norm(avg_grade))
            plt.bar(dist_km[i], elevations[i] - (min_ele - 10),
                    width=(dist_km[i+1] - dist_km[i]),
                    bottom=min_ele - 10, color=color, align='edge')
        plt.plot(dist_km, elevations, color='#2c3e50', linewidth=0.5, alpha=0.5)

    else: # Default: "filled"
        for i in range(len(dist_km) - 1):
            x = [dist_km[i], dist_km[i+1]]
            y = [elevations[i], elevations[i+1]]
            avg_grade = abs(grades[i])
            color = cmap(norm(avg_grade))
            plt.fill_between(x, y, min_ele - 20, color=color, alpha=0.8)
        plt.plot(dist_km, elevations, color='#2c3e50', linewidth=1.5)

    if style != "sparkline":
        ax.set_facecolor('#ffffff')
        plt.title(f"Tactical Elevation Profile ({style.capitalize()})", fontsize=10, fontweight='bold')
        plt.xlabel("Distance (km)", fontsize=8)
        plt.ylabel("Elevation (m)", fontsize=8)
        plt.grid(True, linestyle='--', alpha=0.3)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return img_base64

def get_elevation_profile_image(geometry: RouteGeometry, uuid_input, width: int = 8, height: int = 3, style: Literal["sparkline", "filled", "bars"] = "filled"):
    """
    Generates an elevation profile, manages local storage and auto-cleaning.
    """
    try:
        coords_list = geometry.coordinates

        home_dir = Path.home() / ".bikescout" / "altimetry"
        home_dir.mkdir(parents=True, exist_ok=True)

        now = time.time()
        for f in home_dir.glob("*.png"):
            if f.is_file() and (now - f.stat().st_mtime) > (3 * 86400):
                try:
                    f.unlink()
                except: pass
        plot_result = _generate_altimetry_plot(coords_list, width, height, style)

        raw_data = plot_result
        if isinstance(plot_result, dict):
            raw_data = plot_result.get("image_data_url", "")

        if "base64," in raw_data:
            raw_data = raw_data.split("base64,")[1]

        if not raw_data:
            return {"status": "Error", "message": "No plot data generated."}

        unique_id = uuid_input if uuid_input else uuid.uuid4().hex[:6]
        filename = f"bs_altimetry_{unique_id}.png"
        file_path = home_dir / filename

        with open(file_path, "wb") as f:
            f.write(base64.b64decode(raw_data))

        mcp_uri = f"bikescout://altimetry/{filename}"

        return {
            "status": "Success",
            "message": "Elevation profile image created.",
            "mcp_resource_uri": mcp_uri,
            "file_location": str(file_path),
            "style_applied": style,
            "dimensions": f"{width}x{height} in",
            "total_distance_km": round(sum(geodesic((geometry.coordinates[i][1], geometry.coordinates[i][0]),
                                                    (geometry.coordinates[i+1][1], geometry.coordinates[i+1][0])).meters
                                           for i in range(len(geometry.coordinates)-1)) / 1000, 2)
        }

    except Exception as e:
        return {"status": "Error", "message": f"Altimetry home-storage failed: {str(e)}"}