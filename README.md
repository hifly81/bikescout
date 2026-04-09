# BikeScout MCP Server

[![License](https://img.shields.io/badge/License-Mixed-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.6.0-green.svg)](https://github.com/hifly81/bikescout/releases)
![Python](https://img.shields.io/badge/python-3.10-blue.svg)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Downloads](https://pepy.tech/badge/global-chem)](https://pepy.tech/project/global-chem)

**BikeScout** is a specialized MCP (Model Context Protocol) server designed for cyclists and mountain bikers. It provides intelligent trail recommendations by combining real-world map data with advanced routing analysis.

## Key Features

- **Real Trail Discovery**: Fetches actual trail names and surface types from **OpenStreetMap** (via Overpass API).
- **Technical Metrics**: Calculates precise distance in kilometers and total elevation gain (ascent).
- **Difficulty Grading**: Automatically evaluates trails as Beginner, Moderate, or Expert based on incline and length.
- **Dynamic Routing**: Generates suggested loops (round trips) based on your starting coordinates.
- **Smart Safety and Weather Forecast**: BikeScout doesn't just find trails; it cross-references location data with real-time weather forecasts to ensure you don't get caught in a storm.
- **Surface Detection:** Identifies asphalt, gravel, grass, stones, and unpaved sections.
- **Percentage Breakdown:** Calculates the exact percentage of each surface type relative to the total distance.
- **Seamless Location Search**: No GPS coordinates required. Use natural language to find trails (e.g., "Find a ride in Albano Laziale") via integrated Nominatim Geocoding.
- **Instant Map Previews**: Automatically generates a Static Map (.png) of the route, allowing you to visualize the trail directly within the chat interface.
- **Pro-Cycling Weather Gear Advice**: Goes beyond basic forecasts by providing specific technical advice on clothing and gear based on temperature, wind, and rain thresholds.

## Prerequisites

- **Python 3.10+**
- **OpenRouteService API Key**: Get a free key at [openrouteservice.org](https://openrouteservice.org/).
- **MCP Client**: Such as Claude Desktop.

## Installation

BikeScout is now available on **PyPI**. You can install it directly using `pip` or `uv`.

### Install via pip
We recommend installing BikeScout in a virtual environment:

```bash
python -m venv venv
source venv/bin/activate 
pip install bikescout
```

Configure your OpenRouteService API Key:

```bash
export ORS_API_KEY=YOUR_OPENROUTE_SERVICE_API_KEY
```

## Manual Installation

1. Clone the repo in a local folder:
   ```bash
   git clone git@github.com:hifly81/bikescout.git <your_local_folder_path>
   ```
2. Create a Python Virtual Env from the local folder:
   ```bash
   python3 -m venv venv
   ```
3. Use the provided requirements.txt to install all necessary libraries:
   ```bash
   ./venv/bin/pip install -r requirements.txt
   ```

## Configuration for Claude Desktop
Add the server to your `claude_desktop_config.json`:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json` 
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

You must replace the placeholders in the JSON configuration with your local absolute paths to the Python script file.
`PATH/TO/YOUR/BIKESCOUT_FOLDER/src/bikescout/mcp_server.py`

Example:
 - Linux/macOS: `/home/username/bikescout/src/bikescout/mcp_server.py`
 - Windows: `C:/Users/Username/Documents/bikescout/src/bikescout/mcp_server.py`

```json
{
  "mcpServers": {
    "bikescout": {
      "command": "PATH/TO/YOUR/BIKESCOUT_FOLDER/venv/bin/python3",
       "args": [
          "-u",
          "-m",
          "bikescout.mcp_server"
       ],
      "env": {
        "PYTHONPATH": "PATH/TO/YOUR/BIKESCOUT_FOLDER/src", 
        "ORS_API_KEY": "YOUR_OPENROUTE_SERVICE_API_KEY"
      }
    }
  }
}
```

## Using BikeScout with VS Code (Linux/Windows/macOS)
If your goal is to test the BikeScout server while you are coding, you don't actually need the Claude Desktop app. You can use VS Code along with the Cline (formerly Claude Dev) or Continue extensions.

1. Install the Extension:

   Go to the VS Code Marketplace and install the **Cline** extension (or Continue). These extensions act as a "bridge" between the AI and your local machine.

2. Open MCP Settings:

   In the extension settings (usually a gear icon or a specific "MCP" tab within the extension's side panel), look for the section titled "Configure MCP Servers".

3. Add the JSON Configuration:

   Paste the following JSON configuration into the settings file (make sure to update the path to your actual directory):

```json
{
   "mcpServers": {
      "bikescout": {
         "command": "PATH/TO/YOUR/BIKESCOUT_FOLDER/venv/bin/python3",
         "args": [
            "-u",
            "-m",
            "bikescout.mcp_server"
         ],
         "env": {
            "PYTHONPATH": "PATH/TO/YOUR/BIKESCOUT_FOLDER/src",
            "ORS_API_KEY": "YOUR_OPENROUTE_SERVICE_API_KEY"
         }
      }
   }
}
```
4. Start Scouting
   Once saved, you can chat with the AI directly within VS Code. It will automatically detect BikeScout as a "tool." You can then ask: _"Find me a scenic 30km MTB route starting from my current coordinates."_ The AI will execute the Python script, fetch the data from OpenStreetMap and OpenRouteService, and present the results right in your chat window.

## Debugging and Testing

You can test **BikeScout** using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector), a web-based tool for testing MCP servers.

#### Using the Inspector
To launch the inspector and interact with the tools manually, run the following command from the root directory:

```bash
export ORS_API_KEY=YOUR_OPENROUTE_SERVICE_API_KEY
PYTHONPATH=./src npx @modelcontextprotocol/inspector ./venv/bin/python3 -m bikescout.mcp_server
```

What to check:
- **List Tools**: Ensure all tools (geocode_location, trail_scout, etc.) are visible. 
- **Run Tool**: Test the geocode_location tool by passing a city name (e.g., "Rome") to verify the Nominatim integration.

---

## Example Queries

You can ask **BikeScout** questions. It understands complex requests regarding distance, elevation, and specific file types.

* *"BikeScout, find me a 20km mountain bike loop near Frascati, Italy and tell me the total ascent and check if it's too windy for a mountain bike."*
* *"Are there any named trails in the area of Taichung, China? I need to know the surface type."*
* *"Suggest a difficult MTB route with at least 600m of climbing near Park City, Utah"*
* *"What is the terrain like for a 15km ride starting at these coordinates [LAT,LON]?"*
* *"Find me a 20km loop that is at least 50% gravel, but only if the ground isn't wet (rain probability < 10%) near Kyoto, Japan."*
* *"Search for a beginner-friendly loop in Vancouver, Canada."*
---

## Example Responses

Below is an example of the detailed information **BikeScout** can provide:

I found an MTB loop near **Frascati, Italy**. Here are the details:

### 📊 Route Details
* 📍 **Distance:** 11.26 km
* ⛰️ **Total Ascent:** 856 meters
* 🏷️ **Difficulty:** Expert (Challenging distance or very steep climbs)
* 🛤️ **Included Trails:** *Viale Moderno, Via dei Sepolcri*
* 🔗 **Map:** View on Google Maps
* 🔗 **Route Map Image:** mtb_route_map.png

#### Key Route Characteristics
- **Technical Terrain**: Mountain bike trails with technical sections
- **Elevation Profile**: Significant descent from Rocca di Papa (703m) to Albano Laziale (542m)
- **Trail Surfaces**: Mix of gravel, dirt, and forest paths
- **Scenery**: Beautiful views of the Alban Hills and Roman countryside

#### Equipment Checklist
- **Bike**: Full-suspension MTB recommended for technical terrain
- **Helmet**: Mandatory safety equipment
- **Hydration**: At least 2L of water
- **Nutrition**: Energy bars/gels for the 15km distance
- **Repair Kit**: Spare tube, pump, multi-tool
- **Clothing**: Layered clothing for changing elevations
- **Navigation**: GPS device or smartphone with the GPX file loaded

#### Safety Notes
- This is an expert-level route with technical sections
- Significant elevation changes require good fitness level
- Some sections may be steep and challenging
- Ride within your skill limits
- Let someone know your planned route and expected return time

#### 🌤️ Weather Forecast (Next 4 hours)
| Time | Temp | Rain | Wind |
| :--- | :--- | :--- | :--- |
| **10:00 AM** | 13.7°C | 0% | 6.4 km/h |
| **11:00 AM** | 15.2°C | 0% | 7.5 km/h |
| **12:00 PM** | 16.4°C | 0% | 8.7 km/h |
| **01:00 PM** | 17.6°C | 0% | 9.7 km/h |

> ✅ **Advice:** Perfect for riding! The route is challenging (856m of climbing over 11km) but offers great scenic views over the Colli Albani area.

#### 🚵‍♂️ BikeScout Terrain Analysis
The route composition is as follows:

* 🪨 **Gravel/Dirt:** 65% (Ideal for MTB or Gravel bikes)
* 🛣️ **Asphalt:** 25% (Connecting sections)
* 🌿 **Grass/Trail:** 10%

> 💡 **Technical Advice:** Given the high percentage of gravel and loose stones, we recommend using tires with a minimum width of **40mm** and slightly lower tire pressure to improve grip and comfort.

---

## Tools Reference

**BikeScout** exposes specialized tools to the MCP host. Currently, the server provides a comprehensive scouting tool, with more modules planned for future releases.

### 1. `geocode_location`
This tool acts as the intelligent "entry point" for all natural language queries. It translates place names into geographical coordinates, enabling a seamless experience where users don't need to provide raw GPS data.

#### **Functionality:**
* **Forward Geocoding:** Converts city names, landmarks, or addresses (e.g., "Passo dello Stelvio") into lat and lon.
* **Disambiguation:** Returns the full display name to confirm the AI has found the correct location.
* **OSM Integration:** Uses the Nominatim API (OpenStreetMap) for reliable, open-source data.

#### **Parameters:**
| Parameter | Type     | Default | Description |
| :--- |:---------| :--- | :--- |
| `location_name` | `string` | Required | The name of the place to search for (e.g., "Frascati, Italy"). |

#### **Tool Output Example (JSON):**
```json
{
   "status": "Success",
   "lat": 41.8034,
   "lon": 12.6738,
   "display_name": "Frascati, Roma, Lazio, 00044, Italia"
}
```

### 2. `trail_scout`
This is the core tool of the server. It performs a multi-step analysis to provide a ride-ready cycling route.

#### **Functionality:**
* **Semantic Search:** Queries OpenStreetMap (Overpass API) to find real names of trails and paths near the starting point.
* **Smart Routing:** Uses OpenRouteService to generate a **Round Trip** (loop) based on the user's preferred distance.
* **Elevation Profiling:** Fetches SRTM elevation data to calculate total ascent and evaluate difficulty.
* **File Generation:** Produces a valid **GPX XML** string for navigation.
* **Static map image:** Construct the URL using a public OpenStreetMap static map service.

#### **Parameters:**
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | Latitude of the starting point (e.g., `45.81`). |
| `lon` | `float` | Required | Longitude of the starting point (e.g., `9.08`). |
| `radius_km` | `int` | `10` | The target total length of the loop in kilometers. |
| `profile` | `string`| `cycling-mountain` | Routing profile: `cycling-mountain`, `cycling-road`, or `cycling-regular`. |

#### **Tool Output Example (JSON):**
```json
{
  "status": "Success",
  "info": {
    "trails": ["Sentiero 1", "Via dei Monti"],
    "distance_km": 12.4,
    "ascent_m": 450,
    "difficulty": "Intermediate"
  }, 
  "map_image_url": "https://static-maps.fly.dev/staticmap/...",
  "map_url": "http://googleusercontent.com/maps.google.com/...",
  "gpx_content": "<?xml version='1.0' encoding='UTF-8'?>..."
}
```

### 3. `check_trail_weather`
A real-time safety tool designed specifically for outdoor activities. It provides a localized 4-hour window forecast.

#### **Functionality:**
* **Hyper-local Forecast:** Uses precise coordinates to fetch data from the Open-Meteo API.
* **Cycling-Specific Metrics:** Focuses on precipitation probability, temperature, and wind speed.
* **Smart Advice:** Automatically evaluates conditions and provides a "Go/No-Go" suggestion.

#### **Parameters:**
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | Latitude of the trail or starting point. |
| `lon` | `float` | Required | Longitude of the trail or starting point. |

**Example Output (JSON):**
```json
{
  "status": "Success",
  "location": {"lat": 41.80, "lon": 12.67},
  "next_4_hours": [
    { "time": "10:00", "temp": "18.5°C", "rain_prob": "5%", "wind": "12 km/h" }
  ],
  "advice": "Perfect for riding!"
}
```

### 4. `analyze_route_surfaces`
Analyzes the physical composition of the route to help users choose the appropriate bike (Road, Gravel, or MTB).

#### **Functionality:**
* **Surface Detection:** Identifies asphalt, gravel, grass, stones, and unpaved sections.
* **Percentage Breakdown:** Calculates the exact percentage of each surface type relative to the total distance.
* **Waytype Insights:** Distinguishes between cycleways, tracks, and footways.

#### **Parameters:**
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | Latitude of the starting point. |
| `lon` | `float` | Required | Longitude of the starting point. |
| `radius_km` | `int` | `10` | The total length of the loop to analyze. |

**Example Output (JSON):**
```json
{
  "status": "Success",
  "surface_breakdown": [
    { "type": "Gravel", "percentage": "65.2%" },
    { "type": "Asphalt", "percentage": "25.8%" },
    { "type": "Grass", "percentage": "9.0%" }
  ],
  "total_distance_m": 12400
}
```

## Advanced Query Example 

**User:** *"Find me a 20km loop that is at least 50% gravel, but only if the ground isn't wet (rain probability < 10%)."*

**AI Logic & Action:**
1. **Weather Check:** The AI calls `check_trail_weather` to verify the precipitation probability for the next few hours.
2. **Surface Analysis:** It calls `analyze_route_surfaces` with a `cycling-mountain` or `cycling-regular` profile.
3. **Filtering:** If `rain_prob < 10` AND `Gravel + Dirt > 50%`, the AI calls `get_complete_trail_scout` to finalize the route and generate the **GPX file**.
4. **Final Response:** > "I've found the perfect 21km loop for you! The rain probability is only 5%, and the route is **68% gravel**, perfectly matching your request. Here is your GPX file and the technical breakdown..."

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make to **BikeScout** are **greatly appreciated**.

### How to Contribute

1. **Report Bugs**: Found a glitch? Open an [Issue](https://github.com/yourusername/bikescout/issues) with a detailed description and steps to reproduce.
2. **Feature Requests**: Have an idea to make BikeScout better? Open an issue to discuss it!
3. **Pull Requests**:
   - Fork the Project.
   - Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
   - Commit your changes (`git commit -m 'Add some AmazingFeature'`).
   - Push to the Branch (`git checkout origin feature/AmazingFeature`).
   - Open a Pull Request.

### Development Roadmap
We are currently looking for help with:
- [ ] **POI Integration**: Adding water fountains, bike repair stations, and cafés to the route summary.
- [ ] **Advanced Surface Analysis**: Better mapping of trail technicality grades (S0-S5).
- [ ] **Frontend Mockups**: Visualizing how BikeScout looks in different MCP clients.

### Coding Standards
- Please follow [PEP 8](https://peps.python.org/pep-0008/) for Python code.
- Ensure all new tools are documented in the `README.md`.
- Keep comments in English for international collaboration.


*By contributing, you agree that your contributions will be licensed under the project's Apache-2.0 License.*

---

## License & Data Attributions

### Software License
This project is licensed under the **Apache-2.0 License** - see the [LICENSE](LICENSE) file for details.

### Data Sources & Credits
BikeScout aggregates data from several open providers. Users of this server must adhere to their respective terms:

* **Routing & Map Data:** Provided by [OpenRouteService](https://openrouteservice.org/) by HeiGIT.
* **Geospatial & Geocoding Data:** © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors. Data is available under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/). Geocoding service powered by [Nominatim](https://nominatim.org/).
* **Weather Forecasts:** Powered by [Open-Meteo](https://open-meteo.com/). Data is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
* **Elevation Data:** SRTM (NASA) processed via OpenRouteService.
* **Static Maps:** Static map images generated via OpenStreetMap contributors and rendered through public static map instances.
