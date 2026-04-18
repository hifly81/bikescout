# BikeScout MCP Server

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Version](https://img.shields.io/badge/Version-1.0.1-green.svg)](https://github.com/hifly81/bikescout/releases)
![Python](https://img.shields.io/badge/python-3.10-blue.svg)
[![hifly81/bikescout](https://glama.ai/mcp/servers/hifly81/bikescout/badges/score.svg)](https://glama.ai/mcp/servers/hifly81/bikescout)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Discord](https://img.shields.io/badge/Discord-7289DA?style=flat&logo=discord&logoColor=white)](https://discord.gg/TCetrnAM5b)
[![Reddit](https://img.shields.io/badge/Reddit-FF4500?style=flat&logo=reddit&logoColor=white)](https://www.reddit.com/r/BikeScout/)

BikeScout is a specialized MCP server for MTB, Road, E-Bike, and Gravel mission planning.
It transforms raw map data into Tactical Intelligence, predicting terrain conditions and trail hazards.
The system provides precise setup advice, tailoring your equipment to the demands of the specific route, identifying technical challenges and environmental risks before you even leave the garage.

<div align="center">
  <video src="https://github.com/user-attachments/assets/cd984f3d-0ba8-4590-9645-99f2b5e980b6" width="100%" controls autoplay muted loop>
  </video>
</div>

**Love BikeScout?** ⭐ Star this repo to support the development of the first open-source tactical cycling engine.

**Found a bug?** Open an Issue. Want to add a local skill? PRs are welcome!

---

## Example Queries

You can ask **BikeScout** complex, multi-step requests. It combines real-time data with technical cycling intelligence to provide expert-level answers.

### Advanced Planning (Multi-Tool)
* *"I'm at **Monte Cavo** with my **Gravel bike (40mm tires)**. Plan a **25km loop** for me. Check if the terrain is compatible with my bike, verify the afternoon rain probability, and suggest a 'Fraschetta' for the finish. Use the **Castelli Romani guide**."*
* *"I want to ride in **Moab** tomorrow. I have a **hardtail MTB**. Find me a **20km route** that isn't too technical (avoid Grade 4/5 tracks), check the heat forecast, and give me the desert safety checklist."*
* *"I'm a 75kg rider on a Gravel bike with 38mm tubeless tires. Based on the surface breakdown of this route (60% loose gravel, 40% asphalt), calculate my optimal tire pressure for maximum traction without risking rim strikes."*

### Bike Setup & Surface Intelligence
* *"Check this route `[LAT, LON]` for a **15km loop**. I'm on a **Road Bike with 25mm tires**. Is it compatible? Give me the exact percentage of gravel vs asphalt."*
* *"I'm planning a ride in **Kyoto, Japan**. Find a **30km loop** that is at least **70% gravel**, but only if the rain probability is below **10%** for the next 4 hours."*
* *"I'm riding an E-MTB (750Wh battery) in Boost mode. Analyze this 40km route and tell me if I'll have enough juice to finish the final Category 2 climb, considering the current mud risk."*

### Visual Elevation & Gradient Analysis
* *"Plan a 40km route starting from Bormio. I need the Visual Elevation Profile to see the exact gradients of the Stelvio climb. Highlight sections over 12% so I can manage my pacing."*
* *"Check this route [LAT, LON]. Generate the high-resolution altitude chart and tell me if the descent is too steep for a rider with rim brakes."*

### Local Expertise
* *"Use the **Dolomiti local guide** to plan a road cycling route starting from **Cortina**. I need at least **800m of elevation gain**. Also, recommend the correct tire pressure for high-altitude descents and a mountain hut for a strudel stop."*
* *"Are there any named trails near **Vancouver, Canada**? Analyze the surface types and tell me if they are suitable for a beginner on an **E-MTB**."*
* *"Plan a hiking/biking hybrid mission in the Swiss Alps. Use the SAC-Scale to identify sections where I might need to carry my bike (hike-a-bike) due to technical rock gardens."*

### Quick Tech Checks
* *"Give me the **safety checklist** and calculate the **tire pressure** for a **90kg rider** on **2.3" tubeless tires** for a muddy ride."*
* *"What is the terrain breakdown for a **10km ride** in **Taichung**? I need to know if I'll encounter any 'Grade 5' technical segments."*

### Post-Ride Analysis & Terrain Truth
* *"Analyze my Strava ride from 2026-04-12. Compare my average speed with the Mud Risk at that time and tell me if the terrain conditions were the reason for my slow pace."*
* *"Check my ride from last Sunday on Strava. Cross-reference the GPS path with the 72h rain history to see if the 'High' mud risk I encountered was accurately predicted."*
* *"Get my activity from Strava for [Date]. Based on the surface types detected and the weather context of that day, was my tire pressure setup (1.8 bar) optimal or should I have gone lower?"*

---

## Key Features

🗺️ Terrain & Surface Intelligence
- **Real Trail Discovery**: Fetches actual trail names and surface data directly from OpenStreetMap (via Overpass API).
- **Surface Breakdown**: Generates a detailed percentage breakdown of the entire route (asphalt, gravel, dirt, etc.).
- **Technical Grading**: Analyzes OSM Tracktypes (Grade 1-5) to distinguish between smooth fire roads and rugged, technical MTB paths.
- **Bike Compatibility Check**: A first-of-its-kind feature that validates if a route suits your specific bike (Road, Gravel, MTB) and tire width, issuing instant safety warnings.

🌡️ Predictive Environmental Modeling
- **TAEL Algorithm**: Our flagship Terrain-Aware Evaporation Lag model that predicts "Shadow-Lock" mud on north-facing slopes by analyzing real-time solar altitude and soil memory.
- **Predictive Mud Risk**: Advanced rideability analysis based on geological soil composition (Clay vs. Sand) and 72-hour precipitation history.
- **Tactical Ride Window**: A "Go/No-Go" decision engine that identifies the optimal start time by cross-referencing atmospheric hazards with terrain saturation.
- **Smart Safety Weather**: Hyper-local 4-hour forecasts with expert-level gear and layering advice based on temperature, wind, and rain thresholds.

📈 High-Fidelity Navigation & Altimetry
- **Wall-Sense Technology**: Automatically detects gradients >10% and injects active <wpt> alerts into your GPX file to warn you on your head unit before you hit the "wall."
- **Tactical GPX Export**: Produces optimized GPX files (max 1,500 points) to eliminate GPS signal noise while strictly preserving critical elevation spikes.
- **Visual Elevation Profiling**: Generates high-resolution graphical sparklines with chromatic difficulty scaling, cached locally to save AI context window.
- **Pro Climb Categorization**: Automatically identifies and ranks climbs using professional UCI standards (from Category 4 to Hors Catégorie).

🧠 Mission Logistics & Intelligence
- **Smart POI Scouting**: Scans a 2km radius along the route for drinking water, bicycle repair stations, and mountain shelters.
- **E-MTB Energy Management**: Calculates estimated battery consumption (Wh) based on rider weight, assist mode (Eco/Boost), and terrain-specific rolling resistance.
- **Local Expert Skills**: Specialized "Local Wisdom" knowledge bases for world-class destinations like The Dolomites, Moab, and Finale Ligure.
- **Post-Ride Analysis**: Fuses Strava activity logs with environmental intelligence to analyze how mud and weather conditions impacted your actual performance.

## Documentation

- [API & Tools Documentation](site/md/api_docs.md)
- [Website](https://hifly81.github.io/bikescout)
- [Blog](https://hifly81.github.io/bikescout/site/blog.html)
- [Why BikeScout? (vs Generic Maps)](site/md/comparison.md)

---

## Quickstart: Deploy BikeScout in 3 Minutes

You don't need to be a developer to give your AI "eyes" on the trail. If you can copy-paste, you can deploy **BikeScout**. Follow this mission briefing to turn Claude into your personal tactical cycling scout.

### 1. The Essentials 
* **Claude Desktop:** The "Command Center." [Download it here](https://claude.ai/download).
* **Python:** The engine. [Download it here](https://www.python.org/downloads/) (Make sure to check **"Add Python to PATH"** during setup).

### 2. Get Your Intel Keys 
BikeScout pulls high-precision data from professional sources. You need these FREE keys:
1. **OpenRouteService:** [Sign up here](https://openrouteservice.org/) for trail and surface data.

### 3. Tactical Deployment 
1. **Download the Lab:** Download this repository as a ZIP and extract it to a folder (e.g., `C:\BikeScout` or `/Users/YourName/BikeScout`).
2. **Prepare the Environment:** Open your terminal in the BikeScout folder and run these two commands to create your isolated "lab":
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install bikescout
```
3. **Open Claude Config:**
    * In Claude Desktop, click the **Settings icon** (bottom left) -> **Developer** -> **Edit Config**.
4. **Plug it in:** Copy the block below and paste it into the file. **Replace the placeholders** with your actual keys and the path where you saved the folder:

```json
{
  "mcpServers": {
    "bikescout": {
      "command": "PATH/TO/YOUR/FOLDER/venv/bin/python3",
      "args": [
        "-u",
        "-m",
        "bikescout.mcp_server"
      ],
      "env": {
        "PYTHONPATH": "PATH/TO/YOUR/FOLDER/src",
        "ORS_API_KEY": "YOUR_ORS_API_KEY_HERE"
      }
    }
  }
}
```

### 4. Initiate First Mission
Restart Claude Desktop. Look for the **🔌 (Plug icon)**—that means BikeScout is online.

**Try your first command:**
> "I'm planning a 30km MTB loop in the Alps. Check the mud risk for the last 72 hours and tell me if I should run my mud tires or my fast-rolling ones."

You have successfully deployed your tactical scout. Your AI is now ready to analyze the terrain. 🚲💨

---

## Prerequisites

- **Python 3.10+**
- **OpenRouteService API Key**: Get a free key at [openrouteservice.org](https://openrouteservice.org/).
- **MCP Client**: Such as Claude Desktop.
- **Strava Account (Optional)**: Required only for the **Post-Ride Tactical Analysis** feature.
- **Stadia Maps Account (Optional)**: Required only for generating Static Route Maps.

To enable Strava integration, you need to create a developer application and generate a long-lived Refresh Token:

See the related [how to obtain a Strava key section](site/md/strava_key.md)

## Installation

BikeScout is available on [PyPI](https://pypi.org/project/bikescout/). You can install it directly using `pip` or `uv`.

## MCP Client Integration

To integrate **BikeScout** with your preferred MCP client (Claude Desktop, Cline, Roo Code, etc.), add the following configuration to your settings file:

- Clone the repo in a local folder:
   ```bash
   git clone git@github.com:hifly81/bikescout.git <your_local_folder_path>
   ```
- Create a Python Virtual Env from the local folder:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install bikescout
   ```

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
        "ORS_API_KEY": "YOUR_OPENROUTE_SERVICE_API_KEY",
        "STRAVA_CLIENT_ID": "YOUR_STRAVA_CLIENT_ID",
        "STRAVA_CLIENT_SECRET": "YOUR_STRAVA_CLIENT_SECRET",
        "STRAVA_REFRESH_TOKEN": "YOUR_STRAVA_REFRESH_TOKEN",
        "STADIA_API_KEY": "YOUR_STADIA_API_KEY"
      }
    }
  }
}
```

## Debugging and Testing

You can test **BikeScout** using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector), a web-based tool for testing MCP servers.

#### Using the Inspector
To launch the inspector and interact with the tools manually, run the following command from the root directory:

```bash
export ORS_API_KEY=YOUR_OPENROUTE_SERVICE_API_KEY
## Optional API Key
export STRAVA_CLIENT_ID=YOUR_STRAVA_CLIENT_ID
export STRAVA_CLIENT_SECRET=YOUR_STRAVA_CLIENT_SECRET
export STRAVA_REFRESH_TOKEN=YOUR_STRAVA_REFRESH_TOKEN
export STADIA_API_KEY=YOUR_STADIA_API_KEY

PYTHONPATH=./src npx @modelcontextprotocol/inspector ./venv/bin/python3 -m bikescout.mcp_server
```

What to check:
- **List Tools**: Ensure all tools (geocode_location, trail_scout, etc.) are visible. 
- **Run Tool**: Test the geocode_location tool by passing a city name (e.g., "Rome") to verify the Nominatim integration.

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
* **Static Maps**: Map previews are generated using [Stadia Maps](https://docs.stadiamaps.com), utilizing OpenStreetMap data.
* **Post-ride analysis**: Provided by Strava. Post-ride analysis and GPS telemetry are accessed via the [Strava API](https://developers.strava.com/docs/reference).
