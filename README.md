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

## Why BikeScout? (vs Generic Maps)

See the related [comparison section](site/md/comparison.md)

## News, Blog & Live Demo

Stay updated with the latest tactical cycling intelligence, mission reports, and MCP ecosystem news.
* **Official Website:** [https://hifly81.github.io/bikescout](https://hifly81.github.io/bikescout)
* **Tactical Blog:** [https://hifly81.github.io/bikescout/site/blog.html](https://hifly81.github.io/bikescout/site/blog.html)
* **Tactical Encyclopedia:** [https://hifly81.github.io/bikescout/site/encyclopedia.html](https://hifly81.github.io/bikescout/site/encyclopedia.html) — *Deep dive into TAEL, ASI, and Geodesic protocols.*
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

## BikeScout Skills

BikeScout doesn't just provide raw data; it utilizes a system of **Actionable Knowledge Bases** (Skills) to transform data into tactical decisions. The system operates on two distinct levels:

### 1. Global Foundation Skills
These skills ensure that every mission starts with a certified mechanical and safety baseline, regardless of the location.

| Skill Name | Purpose | Tactical Output |
| :--- | :--- | :--- |
| `apply_safety_protocol` | **Safety & M-Check** | Generates dynamic checklists based on `mission_type` (MTB, E-Bike, Road, Gravel). |
| `get_baseline_mechanics` | **Standard Setup** | Provides baseline tire pressures and mechanical configurations from the BikeScout Registry. |

### 2. Local Expert Skills 
These skills inject "Local Wisdom" into the AI's reasoning, adapting calculations (pressure, battery, risk) to the specific geology and environment of the territory.

| Skill / Knowledge Base | Destination | Tactical Specialization |
| :--- | :--- | :--- |
| `get_moab_intel` | 🏜️ **Moab, Utah** | High-desert survival, Slickrock traction mastery, and extreme hydration protocols. |
| `get_castelli_intel` | 🌋 **Castelli Romani** | Volcanic soil behavior (dust/mud), aggressive spikes in gradient, and cultural stop protocols. |
| `get_dolomiti_intel` | 🏔️ **Dolomites, Italy** | High-altitude weather vigilance, UNESCO limestone grip analysis, and 1:1 gearing strategies. |
| `get_arenberg_intel` | 🧱 **Arenberg Forest** | Vibration damping on Pavé, stone humidity risk (TAEL), and "Roubaix-spec" setup. |
| `get_finale_intel` | 🌊 **Finale Ligure** | EWS standards, brake fade management, and limestone rock garden suspension tuning. |
| `get_derby_intel` | 🌿 **Derby, Tasmania** | Granite slab traction, "Hero Dirt" saturation analysis, and high-speed rebound optimization. |
| `get_shimanami_intel` | 🌉 **Shimanami Kaido** | Bridge crosswind analysis, island-hopping logistics, and road/gravel touring efficiency. |


### **How These Skills Work: Retrieve-and-Reason**

The AI goes beyond simple data reading, performing a dynamic synthesis in four phases:

1.  **Context Detection**: Identifies the region and mission type (e.g., *Enduro in Finale Ligure*).
2.  **Foundation Setting**: Invokes `get_baseline_mechanics` to establish a technical starting point (e.g., *1.8 Bar for MTB*).
3.  **Local Skill Invocation**: Triggers the local skill (e.g., `get_finale_intel`) to load the geological profile (e.g., *"Wet Limestone = Zero Traction"*).
4.  **Synthesized Briefing**: Cross-references everything with real-time data.
    * *Example:* The `analyze_route_surfaces` tool will suggest lowering pressure to 1.6 Bar and using soft compounds *because* the local expert intelligence knows that specific terrain doesn't drain quickly after the rain detected by the weather tool.


## Tools Reference

**BikeScout** exposes specialized tools to the MCP host. Currently, the server provides a comprehensive scouting tool, with more modules planned for future releases.

### **Object Schemas**

#### **Rider Profile (`rider`)**

Used for tire pressure and difficulty scaling.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `weight_kg` | `float` | `80.0` | Total weight (rider + gear) for PSI and energy calculations. |
| `fitness_level` | `string` | `intermediate` | Affects difficulty grading. Options: `beginner`, `intermediate`, `advanced`, `pro`. |

#### **Bike Setup (`bike`)**
| Field | Type | Default | Description |
| :--- | :--- |:--------| :--- |
| `bike_type` | `string` | `MTB`   | Geometry profile. Options: `Road`, `Gravel`, `MTB`, `Enduro`. |
| `tire_size` | `string` | `29`    | Diameter/Standard. Options: `26`, `27.5`, `29`, `700c`, `650b`. |
| `is_ebike` | `bool` | `false` | If true, triggers battery consumption and motor-assist logic. |
| `battery_wh` | `int` | `625`   | Battery capacity in Watt-hours (required if `is_ebike` is true). |

#### **Mission Constraints (`mission`)**
| Field                | Type     | Default            | Description                                                                                                                                                                                                                                                                                            |
|:---------------------|:---------|:-------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `radius_km`          | `int`    | `10`               | Total target distance for the loop.                                                                                                                                                                                                                                                                    |
| `profile`            | `string` | `cycling-mountain` | ORS Routing profile.                                                                                                                                                                                                                                                                                   |
| `surface_preference` | `string` | `neutral`          | Options: `neutral`, `avoid_unpaved`, `prefer_trails`.                                                                                                                                                                                                                                                  |
| `points`             | `int`    | `3`                | Complexity of the loop (higher = more circular).                                                                                                                                                                                                                                                       |
| `seed`               | `int`    | `42`               | Randomizer seed to reproduce specific route variations.                                                                                                                                                                                                                                                |
| `assist_mode`        | `string` | `Eco`              | Defines the motor's power output profile (Eco, Trail, Boost). This tactical parameter scales the energy consumption model by adjusting the motor-to-rider assistance ratio, directly impacting predicted battery range and "Safety Buffer" alerts based on terrain resistance. 'Eco', 'Trail', 'Boost' |

#### **Route Geometry (`geometry`)**
| Field                | Type     | Default | Description                                                                                                                                                                                                                                                                                            |
|:---------------------|:---------|:--------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `coordinates`          | `list[list[float]]`    | `...`   | A list of GPS points in GeoJSON format. Each sub-list represents a coordinate triplet: [longitude, latitude, elevation]. This sequence is used by the SMA Filter to sanitize elevation and by the Haversine formula for geodesic accuracy.                                                                                                                                                                                                                                                                   |

### `geocode_location`
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

### `trail_scout`
The flagship tool of the server. It acts as a **Master Orchestrator**, merging geographic routing with real-time environmental data and technical bike-setup analysis to provide a comprehensive **"Cycling Dossier"**.

#### **Functionality**
* **Dynamic Round-Trip Routing**: Interfaces with **OpenRouteService (ORS)** to generate a loop based on the user's preferred distance, profile (MTB, Road, Gravel), and starting point.
* **Multi-Engine Integration**:
  - **Surface & Compatibility**: Automatically triggers the `get_surface_analyzer` to check if the trail suits the user's bike type and tire width.
  - **Predictive Mud Risk**: Cross-references the last **72 hours of precipitation** with soil geology (clay, sand, dirt) to estimate trail rideability.
  - **Live Weather Check**: Fetches a 4-hour window forecast and provides pro-cycling gear advice (clothing/layers).
  - **Cycling POI Scout**: Scans a 2km radius around the route for **drinking water**, **bicycle repair stations**, and **mountain shelters**.
* **Technical Grading**: Identifies and categorizes climbs using **UCI-standardization** (Cat 4 to HC) based on length and average gradient.
* **Visual & Navigational Assets**:
    * Generates a **Static Map (.png)** preview for instant visualization.
    * Enhanced GPX Engine: Produces a high-utility GPX XML string, ready to be loaded on Garmin, Strava,... 
Unlike standard GPS files, BikeScout automatically injects active <wpt> (waypoint) tags that trigger alerts on Garmin, Wahoo, and Hammerhead units for:
      - Summit Alerts: Marks the highest elevation point of the route. 
      - Wall Alerts: Flags steep sections (gradient > 10%) before you reach them. 
      - Hydration & Service: Precisely locates water fountains and repair shops found during the POI scouting.

#### **Parameters:**
| Parameter | Type | Default | Description                                             |
| :--- | :--- | :--- |:--------------------------------------------------------|
| `lat` | `float` | Required | Latitude of the starting point (e.g., `45.81`).         |
| `lon` | `float` | Required | Longitude of the starting point (e.g., `9.08`).         |
| **`rider`** | `object` | Required | [Rider Profile](#rider-profile-rider).                  |
| **`bike`** | `object` | Required | [Bike Setup](#bike-setup-bike).                         |
| **`mission`** | `object` | Required | [Mission Constraints](#mission-constraints-mission).    |
| `include_gpx` | `bool` | `True` | Whether to include the raw XML GPX content.             |
| `include_map` | `bool` | `False` | Whether to generate the Static Map URL via Stadia Maps. |
| `output_level` | `string` | `standard` | Verbosity level: `summary`, `standard`, or `full`.      |

#### **Tool Output Example (JSON):**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "info": {
    "distance_km": 10.67,
    "ascent_m": 745,
    "difficulty": "🟠 Advanced (Requires good fitness and stamina)",
    "surface_analysis": {
      "status": "Success",
      "profile_used": "cycling-mountain",
      "tactical_briefing": {
        "distance_km": 10.12,
        "elevation_gain_m": 586,
        "climb_category": "Hors Catégorie (HC) - Legendary Challenge",
        "avg_gradient_est": "19.3%",
        "technical_difficulty": {
          "mtb_scale": "Standard / Unclassified",
          "trail_visibility": "Excellent",
          "technical_notes": "Technical grading based on OSM mountain standards.",
          "fitness_context": "Evaluated for intermediate level"
        },
        "mud_risk": {
          "score": 49.36,
          "label": "Extreme",
          "details": "Total saturation. Trail damage likely. Recommend Go/No-Go re-evaluation.",
          "environmental_factors": {
            "raw_rain_72h": "20.9mm",
            "avg_temp": "17.4°C",
            "drying_efficiency": "0.42x",
            "shadow_penalty_active": "Yes",
            "solar_altitude": "-19.5°"
          }
        }
      },
      "mechanical_setup": {
        "compatible": true,
        "bike_category": "MTB",
        "setup_details": "29 wheels | 19.6 PSI (1.35 Bar) [Mud Flotation Setup]",
        "rider_weight_baseline": "80.0kg"
      },
      "surface_breakdown": [
        {
          "type": "Unknown",
          "percentage": "40.9%"
        },
        {
          "type": "Paved",
          "percentage": "27.0%"
        },
        {
          "type": "Asphalt",
          "percentage": "9.5%"
        },
        {
          "type": "Compact",
          "percentage": "8.4%"
        },
        {
          "type": "Grass",
          "percentage": "8.0%"
        },
        {
          "type": "Concrete",
          "percentage": "3.4%"
        },
        {
          "type": "Unpaved",
          "percentage": "2.9%"
        }
      ],
      "emtb_tactical": {
        "estimated_drain_wh": 2740.8,
        "remaining_battery_pct": 0,
        "safety_buffer_status": "CRITICAL",
        "breakdown_wh": {
          "horizontal_base": 121.4,
          "vertical_climb": 221.4,
          "terrain_friction": 2397.9
        }
      },
      "safety_warnings": [
        "MUD ALERT: Total saturation. Trail damage likely. Recommend Go/No-Go re-evaluation.",
        "RANGE ANXIETY: SoC at finish is 0.0%. Drop to Eco!"
      ]
    }
  },
  "conditions": {
    "weather": [
      {
        "time": "21:00",
        "temp": "14.1°C",
        "rain_prob": "0%",
        "wind": "3.3 km/h"
      },
      {
        "time": "22:00",
        "temp": "13.4°C",
        "rain_prob": "0%",
        "wind": "4.0 km/h"
      },
      {
        "time": "23:00",
        "temp": "13.1°C",
        "rain_prob": "0%",
        "wind": "4.2 km/h"
      }
    ],
    "mud_risk": {
      "status": "Success",
      "environmental_context": {
        "raw_rain_72h": "20.9mm",
        "avg_temp": "17.4°C",
        "drying_efficiency": "0.42x",
        "shadow_penalty_active": "Yes",
        "solar_altitude": "-19.5°"
      },
      "tactical_analysis": {
        "adjusted_moisture_index": 49.36,
        "mud_risk_score": "Extreme",
        "surface_detected": "dirt",
        "safety_advice": "Total saturation. Trail damage likely. Recommend Go/No-Go re-evaluation."
      }
    },
    "safety_advice": "🌥️ CHILLY: Light jacket or arm warmers recommended."
  },
  "logistics": {
    "nearby_amenities": [
      {
        "name": "Water Fountain 💧",
        "type": "Water Fountain 💧",
        "distance_m": 228,
        "location": {
          "lat": 41.761793,
          "lon": 12.709082
        }
      },
      {
        "name": "Water Fountain 💧",
        "type": "Water Fountain 💧",
        "distance_m": 699,
        "location": {
          "lat": 41.761158,
          "lon": 12.703411
        }
      },
      {
        "name": "Water Fountain 💧",
        "type": "Water Fountain 💧",
        "distance_m": 704,
        "location": {
          "lat": 41.761246,
          "lon": 12.703337
        }
      },
      {
        "name": "Water Fountain 💧",
        "type": "Water Fountain 💧",
        "distance_m": 708,
        "location": {
          "lat": 41.761305,
          "lon": 12.703291
        }
      }
    ]
  },
  "gpx_export_path": "/home/test/.bikescout/gpx/tactical_route_39382d.gpx",
  "gpx_stats": {
    "total_points": 396,
    "optimized_points": 396,
    "waypoints_count": 4
  },
  "elevation_profile_path": "/home/test/.bikescout/altimetry/bs_altimetry_01c3ec.png",
  "elevation_summary": "Visual sparkline generated and cached."
}
```

### `check_trail_weather`
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
  "location": {
    "lat": 41.7615,
    "lon": 12.7118
  },
  "next_4_hours": [
    {
      "time": "12:00",
      "temp": "16.0°C",
      "rain_prob": "0%",
      "wind": "8.3 km/h"
    },
    {
      "time": "13:00",
      "temp": "16.7°C",
      "rain_prob": "0%",
      "wind": "9.4 km/h"
    },
    {
      "time": "14:00",
      "temp": "17.3°C",
      "rain_prob": "0%",
      "wind": "10.4 km/h"
    },
    {
      "time": "15:00",
      "temp": "17.5°C",
      "rain_prob": "0%",
      "wind": "10.8 km/h"
    }
  ],
  "current_conditions": {
    "temp": 16,
    "rain_prob": 0,
    "wind_speed": 8.3
  },
  "safety_advice": "✅ IDEAL: Perfect conditions for a great ride!"
}
```

### `ride_window_planner`
The ultimate **Decision Intelligence** tool for the modern rider. It goes beyond simple weather reporting by calculating the optimal "Strategic Window" to deploy. It cross-references atmospheric stability with the **TAEL (Terrain-Aware Evaporation Lag)** index to determine exactly when the terrain will be at its peak performance.

#### **Functionality**
* **Sliding Window Logic:** Instead of a static snapshot, it iterates through consecutive hourly blocks to find the highest "Confidence Score" for your specific ride duration.
* **Ground Memory Integration:** It factors in the `mud_risk_score` as a persistent penalty, ensuring that "sunny but swampy" conditions are flagged correctly.
* **Tactical Scoring System:** Uses a weighted algorithm that penalizes rain probability exponentially (the "Mission Killer") while adjusting for wind safety and thermal comfort.
* **Auto-Normalization:** A robust data layer that cleans string-based API responses (e.g., converting "93%" to `93.0`) for real-time mathematical analysis.

#### **Parameters**
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | Latitude of the deployment area. |
| `lon` | `float` | Required | Longitude of the deployment area. |
| `ride_duration_hours` | `float` | `2.0` | Target length of the mission (defines the sliding window size). |
| `surface_type` | `str` | `"dirt"` | Used to calculate specific soil drainage coefficients for the TAEL index. |

#### **Example Output (JSON)**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "planner_report": {
    "verdict": "CAUTION",
    "tactical_color": "YELLOW",
    "confidence_score": "62.5/100",
    "best_window": "10:00 - 12:00",
    "environmental_briefing": {
      "rain_avg": "12%",
      "wind_max": "18 km/h",
      "temp_avg": "16°C"
    },
    "mud_risk_impact": "30%"
  }
}
```

### `analyze_route_surfaces`

Analyzes the physical composition of the route to help users choose the appropriate bike (Road, Gravel, or MTB) and categorizes climbs using professional cycling standards.
This tool goes beyond simple mapping by cross-referencing terrain data with the user's specific **mechanical setup and body weight** to ensure safety, performance, and realistic effort estimation.

#### **Core Functionality:**
* **Surface Detection:** Identifies asphalt, gravel, grass, stones, and unpaved sections using OpenStreetMap metadata.
* **Percentage Breakdown:** Calculates the exact percentage of each surface type relative to the total distance.
* **Pro Climb Categorization:** Identifies climbs (Category 4 to Hors Catégorie) using an effort-weighted algorithm that accounts for terrain resistance.
* **Professional Technical Grading**: Leverages international standards like MTB-Scale (S0-S5) and SAC-Scale. It identifies technical features such as rock gardens, steep steps, and trail visibility to provide expert-level safety briefings.
* **Elevation Sanitization:** Uses a progressive filtering logic to remove "satellite noise" from SRTM data, providing realistic elevation gain metrics.
* **Bike Compatibility Check:** Automatically assesses if the route is suitable based on the bike type and standardized tire setup.
* **Safety & Technical Grading:** Analyzes OSM tracktype (Grades 1-5) to distinguish between smooth gravel and rough, technical MTB trails.
* **Surface-Aware Routing:** Fine-tunes the route generation based on user preferences like "avoid unpaved" or "prefer trails."
* **Tactical Tire Intelligence:** Calculates optimal tire recommendations and pressure baseline by cross-referencing **Rider Weight**, bike type, and dominant surface composition.
* **Mud Risk Score:** Provides a localized risk rating (Low/Medium/High) to help cyclists prevent drivetrain damage and avoid unrideable sections.
* **TAEL (Terrain-Aware Evaporation Lag):** A tactical model that cross-references 72h rainfall and geological drainage with real-time solar altitude to predict trail saturation and "Shadow-Lock" mud persistence.
* **E-MTB Power Predictor:** A physics-based energy model ($W = m \cdot g \cdot h$) that predicts battery drain by cross-referencing Total System Weight, Assist Mode, Surface Drag, and Mud Suction effects.

#### **Parameters:**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | Latitude of the starting point. |
| `lon` | `float` | Required | Longitude of the starting point. |
| **`rider`** | `object` | Required | [Rider Profile](#rider-profile-rider).                  |
| **`bike`** | `object` | Required | [Bike Setup](#bike-setup-bike).                         |
| **`mission`** | `object` | Required | [Mission Constraints](#mission-constraints-mission).    |


**Example Output (JSON) for MTB:**
```json
{
  "status": "Success",
  "profile_used": "cycling-mountain",
  "tactical_briefing": {
    "distance_km": 10.16,
    "elevation_gain_m": 835,
    "climb_category": "Hors Catégorie (HC) - Legendary Challenge",
    "avg_gradient_est": "20.0%",
    "technical_difficulty": {
      "mtb_scale": "Standard / Unclassified",
      "trail_visibility": "Excellent",
      "technical_notes": "Technical grading based on OSM mountain standards.",
      "fitness_context": "Evaluated for intermediate level"
    },
    "mud_risk": {
      "score": 10.26,
      "label": "Medium",
      "details": "Damp sections. Expect reduced traction on off-camber roots.",
      "environmental_factors": {
        "raw_rain_72h": "11.9mm",
        "avg_temp": "17.6°C",
        "drying_efficiency": "1.16x",
        "shadow_penalty_active": "No",
        "solar_altitude": "46.3°"
      }
    }
  },
  "mechanical_setup": {
    "compatible": true,
    "bike_category": "MTB",
    "setup_details": "29 wheels | 23.0 PSI (1.59 Bar) [Standard Setup]",
    "rider_weight_baseline": "80.0kg"
  },
  "surface_breakdown": [
    {
      "type": "Unknown",
      "percentage": "40.9%"
    },
    {
      "type": "Paved",
      "percentage": "27.0%"
    },
    {
      "type": "Asphalt",
      "percentage": "9.5%"
    },
    {
      "type": "Compact",
      "percentage": "8.4%"
    },
    {
      "type": "Grass",
      "percentage": "8.0%"
    },
    {
      "type": "Concrete",
      "percentage": "3.4%"
    },
    {
      "type": "Unpaved",
      "percentage": "2.9%"
    }
  ],
  "safety_warnings": []
}
```

**Example Output (JSON) for Road:**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "profile_used": "cycling-road",
  "tactical_briefing": {
    "distance_km": 81.18,
    "elevation_gain_m": 1055,
    "climb_category": "Hors Catégorie (HC) - Legendary Challenge",
    "avg_gradient_est": "2.9%",
    "technical_difficulty": {
      "mtb_scale": "Standard / Unclassified",
      "trail_visibility": "Excellent",
      "technical_notes": "Technical grading based on OSM mountain standards.",
      "fitness_context": "Evaluated for intermediate level"
    },
    "mud_risk": {
      "score": 10.26,
      "label": "Medium",
      "details": "Damp sections. Expect reduced traction on off-camber roots.",
      "environmental_factors": {
        "raw_rain_72h": "11.9mm",
        "avg_temp": "17.6°C",
        "drying_efficiency": "1.16x",
        "shadow_penalty_active": "No",
        "solar_altitude": "47.0°"
      }
    }
  },
  "mechanical_setup": {
    "compatible": true,
    "bike_category": "ROAD",
    "setup_details": "700c wheels | 71.4 PSI (4.92 Bar) [Mud Flotation Setup]",
    "rider_weight_baseline": "80.0kg"
  },
  "surface_breakdown": [
    {
      "type": "Paved",
      "percentage": "59.1%"
    },
    {
      "type": "Unknown",
      "percentage": "40.2%"
    },
    {
      "type": "Asphalt",
      "percentage": "0.4%"
    },
    {
      "type": "Concrete",
      "percentage": "0.3%"
    }
  ],
  "safety_warnings": [
    "MUD ALERT: Damp sections. Expect reduced traction on off-camber roots."
  ]
}
```

**Example Output (JSON) for Gravel:**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "profile_used": "cycling-road",
  "tactical_briefing": {
    "distance_km": 47.47,
    "elevation_gain_m": 1000,
    "climb_category": "Category 2 - Hard Climb",
    "avg_gradient_est": "4.7%",
    "technical_difficulty": {
      "mtb_scale": "Standard / Unclassified",
      "trail_visibility": "Excellent",
      "technical_notes": "Technical grading based on OSM mountain standards.",
      "fitness_context": "Evaluated for intermediate level"
    },
    "mud_risk": {
      "score": 10.26,
      "label": "Medium",
      "details": "Damp sections. Expect reduced traction on off-camber roots.",
      "environmental_factors": {
        "raw_rain_72h": "11.9mm",
        "avg_temp": "17.6°C",
        "drying_efficiency": "1.16x",
        "shadow_penalty_active": "No",
        "solar_altitude": "47.2°"
      }
    }
  },
  "mechanical_setup": {
    "compatible": true,
    "bike_category": "GRAVEL",
    "setup_details": "700c wheels | 28.9 PSI (1.99 Bar) [Mud Flotation Setup]",
    "rider_weight_baseline": "80.0kg"
  },
  "surface_breakdown": [
    {
      "type": "Paved",
      "percentage": "60.2%"
    },
    {
      "type": "Unknown",
      "percentage": "38.5%"
    },
    {
      "type": "Asphalt",
      "percentage": "0.7%"
    },
    {
      "type": "Concrete",
      "percentage": "0.6%"
    }
  ],
  "safety_warnings": [
    "MUD ALERT: Damp sections. Expect reduced traction on off-camber roots."
  ]
}
```

**Example Output (JSON) for E-Bike:**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "profile_used": "cycling-mountain",
  "tactical_briefing": {
    "distance_km": 10.12,
    "elevation_gain_m": 586,
    "climb_category": "Hors Catégorie (HC) - Legendary Challenge",
    "avg_gradient_est": "19.3%",
    "technical_difficulty": {
      "mtb_scale": "Standard / Unclassified",
      "trail_visibility": "Excellent",
      "technical_notes": "Technical grading based on OSM mountain standards.",
      "fitness_context": "Evaluated for intermediate level"
    },
    "mud_risk": {
      "score": 24.19,
      "label": "High",
      "details": "Significant saturation. High risk of sliding in technical sectors.",
      "environmental_factors": {
        "raw_rain_72h": "25.6mm",
        "avg_temp": "17.4°C",
        "drying_efficiency": "1.06x",
        "shadow_penalty_active": "No",
        "solar_altitude": "52.5°"
      }
    }
  },
  "mechanical_setup": {
    "compatible": true,
    "bike_category": "MTB",
    "setup_details": "29 wheels | 19.6 PSI (1.35 Bar) [Mud Flotation Setup]",
    "rider_weight_baseline": "80.0kg"
  },
  "surface_breakdown": [
    {
      "type": "Unknown",
      "percentage": "40.9%"
    },
    {
      "type": "Paved",
      "percentage": "27.0%"
    },
    {
      "type": "Asphalt",
      "percentage": "9.5%"
    },
    {
      "type": "Compact",
      "percentage": "8.4%"
    },
    {
      "type": "Grass",
      "percentage": "8.0%"
    },
    {
      "type": "Concrete",
      "percentage": "3.4%"
    },
    {
      "type": "Unpaved",
      "percentage": "2.9%"
    }
  ],
  "emtb_tactical": {
    "estimated_drain_wh": 1518,
    "remaining_battery_pct": 0,
    "safety_buffer_status": "CRITICAL",
    "breakdown_wh": {
      "horizontal_base": 121.4,
      "vertical_climb": 221.4,
      "terrain_friction": 1175.1
    }
  },
  "safety_warnings": [
    "MUD ALERT: Significant saturation. High risk of sliding in technical sectors.",
    "RANGE ANXIETY: SoC at finish is 0.0%. Drop to Eco!"
  ]
}
```


### `poi_scout`
A specialized safety and logistics tool designed to identify critical cycling amenities. It bypasses standard "commercial noise" by focusing strictly on professional cycling infrastructure and public utilities.

#### **Functionality:**
* **Cyclist-Centric Filtering:** Excludes generic businesses to focus on water fountains, repair stations, and shelters.
* **Request Bundling:** Optimized to perform multiple specialized searches (Water, Repair, Shelter) ensuring comprehensive results even where API limits are strict.
* **Smart Proximity Sorting:** Automatically calculates the distance from your current coordinate or trail point to the nearest amenity.

#### **Parameters:**
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | Latitude of the area to scout. |
| `lon` | `float` | Required | Longitude of the area to scout. |
| `radius_km` | `float` | `2.0` | Search radius in km. Capped at **2.0 km** for maximum API stability. |

#### **Example Output (JSON):**
```json
{
  "status": "Success",
  "search_radius": "2000m",
  "total_found": 3,
  "amenities": [
    {
      "name": "Public Fountain",
      "type": "Water Fountain 💧",
      "distance_m": 120,
      "location": { "lat": 40.7128, "lon": -74.0060 },
      "details": {
        "opening_hours": "24/7",
        "note": "Potable water available"
      }
    },
    {
      "name": "Local Bike Hub",
      "type": "Bike Shop/Repair 🔧",
      "distance_m": 450,
      "location": { "lat": 40.7140, "lon": -74.0075 },
      "details": {
        "opening_hours": "09:00-19:00",
        "note": "Tools and pumps available"
      }
    },
    {
      "name": "Trailside Shelter",
      "type": "Shelter/Rest Area 🏠",
      "distance_m": 1100,
      "location": { "lat": 40.7180, "lon": -74.0100 },
      "details": {
        "opening_hours": "N/A",
        "note": "Rain shelter for cyclists"
      }
    }
  ]
}
```

### `check_trail_soil_condition`
A predictive safety tool that cross-references geological surface data with historical precipitation to estimate trail rideability and mud levels.

#### **Functionality:**
* **Rain History Audit:** Automatically fetches cumulative rainfall from the last 72 hours using the Open-Meteo Archive API.
* **Geological Sensitivity:** Differentiates how rain affects various terrains, calculating saturation levels for surfaces like clay, dirt, sand, and gravel.
* **Mud Risk Score:** Provides a localized risk rating (Low/Medium/High) to help cyclists prevent drivetrain damage and avoid unrideable sections.
* **TAEL (Terrain-Aware Evaporation Lag):** A tactical model that cross-references 72h rainfall and geological drainage with real-time solar altitude to predict trail saturation and "Shadow-Lock" mud persistence.

#### **Parameters:**
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | Latitude of the trail section. |
| `lon` | `float` | Required | Longitude of the trail section. |
| `surface_type` | `string` | `dirt` | The OSM surface tag (e.g., `clay`, `sand`, `gravel`, `asphalt`). |

#### **Example Output (JSON):**
```json
{
  "status": "Success",
  "environmental_context": {
    "raw_rain_72h": "10.0mm",
    "avg_temp": "17.9°C",
    "drying_efficiency": "0.43x",
    "shadow_penalty_active": "Yes",
    "solar_altitude": "-18.2°"
  },
  "tactical_analysis": {
    "adjusted_moisture_index": 23.44,
    "mud_risk_score": "Extreme",
    "surface_detected": "dirt",
    "safety_advice": "Total saturation. Trail damage likely. Recommend Go/No-Go re-evaluation."
  }
}
```

### `elevation_profile_image`
Generates a high-resolution visual analysis of the route's elevation profile. Unlike simple line charts, this tool produces a tactical graphical representation that integrates color-coded slope data, allowing for an immediate assessment of vertical difficulties.

#### **Functionality:**
* **Visual Slope Gradient:** Applies a dynamic chromatic scale (Green → Yellow → Red → Black) to instantly highlight critical steepness (over 10-15%).
* **SRTM Data Processing:** Processes 3D coordinates (Longitude, Latitude, Elevation) to reconstruct the terrain profile with high precision.
* **Automated Scaling**: Automatically adjusts the chart axes based on total elevation gain to ensure maximum readability for both flat valley floors and alpine passes.
* **Base64 Visual Delivery**: Returns the image as a Base64 string (Data URI), enabling immediate integration into chat interfaces, PDF reports, or web dashboards without external hosting.
* **Terrain-Sync Validation**: Uses RouteGeometry logic to validate and sanitize elevation data, eliminating "spikes" common in raw satellite data.
* **Tactical Overview**: Provides a crucial "at-a-glance" briefing for energy management (pacing) and gear selection before starting the ride.

#### **Parameters:**

| Parameter  | Type     | Default      | Description                                        |
|:-----------|:---------|:-------------|:---------------------------------------------------|
| `geometry` | `object` | **Required** | [Route Geometry](#route-geometry-geometry).         |
| `width`    | `int`    | 8            | Width of the generated image (matplotlib inches).  |
| `height`    | `int`    | 3            | Height of the generated image (matplotlib inches). |


#### **Example Output (JSON):**

```json
{
  "status": "Success",
  "image_data_url": "data:image/png;base64,...",
  "message": "Elevation profile generated successfully"
}
```

Example image generated:

![Example image generated:](site/md/elevation_profile.png)

### `analyze_strava_activity`
A post-ride tactical diagnostic tool that fuses actual Strava GPS telemetry with historical environmental data to validate trail conditions and performance.

#### **Functionality:**
* **Satellite Data Retrieval:** Connects to the Strava API to fetch precise activity logs, including distance, elevation, and speed metrics.
* **Environmental Fusion:** Automatically triggers the **Mud Risk** and **Weather** modules for the specific time and location of the ride.
* **Surface-Aware Validation:** Detects the activity type (MTB vs. Road) to apply the correct soil sensitivity coefficients to the moisture analysis.

#### **Parameters:**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `activity_date` | `string` | **Required** | Date of the ride in `YYYY-MM-DD` format. |

#### **Example Output (JSON):**

```json
{
  "status": "Success",
  "mission_briefing": {
    "name": "Afternoon Mountain Bike Session",
    "distance_km": 41.26,
    "elevation_gain_m": 709.3,
    "avg_speed_kmh": 15.0
  },
  "environmental_validation": {
    "mud_risk": "Low",
    "moisture_index": 9.01,
    "weather_advice": "❌ NOT RECOMMENDED: High risk of heavy rain or dangerous wind gusts.",
    "conditions_at_start": {
      "temp": 17.1,
      "rain_prob": 53,
      "wind_speed": 32.0
    }
  },
  "tactical_notes": "Analysis based on asphalt surface coefficients. GPS data validated."
}
```

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
