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

from staticmap import StaticMap, Line
from pathlib import Path
import os

def save_local_tactical_map(filename_part, geojson_data: dict) -> str:
    """
    Generates and saves a tactical map image locally using OpenStreetMap tiles.

    It automatically handles scaling,
    path drawing, and map tile composition.
    """
    try:

        home_dir = Path.home() / ".bikescout" / "gpx"
        home_dir.mkdir(parents=True, exist_ok=True)

        # 1. Data Validation
        if not geojson_data or 'features' not in geojson_data:
            return "Error: Invalid GeoJSON data provided."

        # Extract [lon, lat] coordinates from the ORS response
        # Note: OpenRouteService returns coordinates as [longitude, latitude]
        all_coords = geojson_data['features'][0]['geometry']['coordinates']
        if not all_coords:
            return "Error: No coordinates found in track."

        # 2. Initialize Local Renderer
        # Size: 800x600 pixels.
        # URL template: Uses public OSM tiles (no API key required).
        m = StaticMap(800, 600, url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png')

        # 3. Create the Path Overlay
        # Line(coordinates, color, width)
        # The library accepts [[lon, lat], ...] format which matches GeoJSON perfectly.
        tactical_path = Line(all_coords, 'red', 4)
        m.add_line(tactical_path)

        # 4. Render and Save to Disk
        # The library calculates the bounding box and optimal zoom level automatically.
        image = m.render()

        # Ensure output directory exists (optional safety)

        filename = f"tactical_route_{filename_part}.png"
        file_path = home_dir / filename
        image.save(file_path)

        return file_path

    except ImportError:
        return "Error: Missing dependencies. Install 'staticmap' and 'pillow'."
    except Exception as e:
        print(f"Local Map Generation Error: {e}")
        return f"Local Map Generation Error: {str(e)}"
