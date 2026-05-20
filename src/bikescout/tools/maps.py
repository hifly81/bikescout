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

import time
import numpy as np
import matplotlib.colors as mcolors
from pathlib import Path
from staticmap import StaticMap, Line, CircleMarker

def _get_gradient_color(grade: float) -> str:
    """
    Maps a slope percentage to a hex color.
    Green: Flat, Yellow: Moderate, Red: Steep.
    """
    # Define a colormap consistent with the altimetry profile
    cmap = mcolors.LinearSegmentedColormap.from_list("bike_grade", ["#2ecc71", "#f1c40f", "#e74c3c"])
    # Normalize between 0% and 12% (standard cycling range)
    norm = mcolors.Normalize(vmin=0, vmax=12)
    color = cmap(norm(abs(grade)))
    return mcolors.to_hex(color)

def save_local_tactical_map(
        filename_part: str,
        geojson_data: dict,
        use_gradient: bool = True,
        line_color: str = 'red',
        line_width: int = 7
) -> dict:
    """
    Generates and saves a tactical map image locally using OSM tiles.
    Features:
    - Auto-cleanup of files older than 3 days.
    - Robust GeoJSON validation (multi-geometry/null safety).
    - Slope-based heatmap (gradient) or solid color line with 2D fallback.
    - Start/End tactical markers.
    - MCP resource URI compatibility.
    """
    try:
        # --- 1. Directory & Cleanup ---
        # Move output to a semantic directory (~/.bikescout/maps/)
        home_dir = Path.home() / ".bikescout" / "maps"
        home_dir.mkdir(parents=True, exist_ok=True)

        # Cleanup: Remove files older than 3 days to prevent storage bloat
        now = time.time()
        for f in home_dir.glob("*.png"):
            if f.is_file() and (now - f.stat().st_mtime) > (3 * 86400):
                try:
                    f.unlink()
                except Exception:
                    pass

        # --- 2. Robust Data Validation & Normalization ---
        # Safely check for features to prevent IndexError on empty collections
        features = geojson_data.get('features', [])
        if not features:
            return {"status": "Error", "message": "No features found in GeoJSON."}

        # Extract the geometry safely, ensuring it exists and is a LineString
        geometry = features[0].get('geometry')
        if not geometry or geometry.get('type') != 'LineString':
            return {"status": "Error", "message": "Invalid or missing LineString geometry."}

        # Extract coordinates and ensure we have at least 2 points to draw a line
        all_coords = geometry.get('coordinates', [])
        if len(all_coords) < 2:
            return {"status": "Error", "message": "Insufficient coordinates for mapping."}

        # Check if elevation data is present (3D coordinates vs 2D coordinates)
        has_elevation = len(all_coords[0]) >= 3
        # Disable gradient automatically if data is only 2D
        actual_use_gradient = use_gradient and has_elevation

        # --- 3. Initialize Renderer ---
        # Note: Set a proper User-Agent in your environment to comply with OSM Tile Usage Policy
        m = StaticMap(800, 600, url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png')

        # --- 4. Layers: Path (Gradient or Solid) ---
        if actual_use_gradient:
            # Heatmap logic: Break the track into segments colored by slope
            for i in range(len(all_coords) - 1):
                p1, p2 = all_coords[i], all_coords[i+1]

                rise = p2[2] - p1[2]
                run = np.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2) * 111000

                # Prevent division by zero and calculate grade %
                grade = (rise / run) * 100 if run > 0.5 else 0
                segment_color = _get_gradient_color(grade)

                # Draw small segment (staticmap needs [lon, lat])
                segment = Line([[p1[0], p1[1]], [p2[0], p2[1]]], segment_color, line_width)
                m.add_line(segment)
        else:
            # Fallback to solid color if gradient is disabled or elevation is missing (2D data)
            clean_coords = [[c[0], c[1]] for c in all_coords]
            tactical_path = Line(clean_coords, line_color, line_width)
            m.add_line(tactical_path)

        # --- 5. Layers: Tactical Markers ---
        # Start Marker (White ring + Green dot)
        m.add_marker(CircleMarker([all_coords[0][0], all_coords[0][1]], 'white', 10))
        m.add_marker(CircleMarker([all_coords[0][0], all_coords[0][1]], 'green', 6))

        # End Marker (White ring + Black dot)
        m.add_marker(CircleMarker([all_coords[-1][0], all_coords[-1][1]], 'white', 10))
        m.add_marker(CircleMarker([all_coords[-1][0], all_coords[-1][1]], 'black', 6))

        # --- 6. Render & Save ---
        image = m.render()
        filename = f"tactical_map_{filename_part}_{int(time.time())}.png"
        file_path = home_dir / filename
        image.save(file_path)

        mcp_uri = f"bikescout://maps/{filename}"

        return {
            "status": "Success",
            "message": "Tactical map created successfully.",
            "mcp_resource_uri": mcp_uri,
            "file_location": str(file_path),
            "style_applied": "gradient" if actual_use_gradient else "solid"
        }

    except Exception as e:
        return {"status": "Error", "message": f"Local Map Generation Failed: {str(e)}"}