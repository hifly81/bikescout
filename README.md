# BikeScout MCP Server

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Version](https://img.shields.io/badge/Version-0.9.2-green.svg)](https://github.com/hifly81/bikescout/releases)
![Python](https://img.shields.io/badge/python-3.10-blue.svg)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Downloads](https://pepy.tech/badge/global-chem)](https://pepy.tech/project/global-chem)

**BikeScout** is a specialized MCP server designed for cyclists and mountain bikers. It provides intelligent trail recommendations by combining real-world map data with advanced routing analysis.


<div align="center">
  <video src="https://github.com/user-attachments/assets/cd984f3d-0ba8-4590-9645-99f2b5e980b6" width="100%" controls autoplay muted loop>
  </video>
</div>

## Key Features

* **Real Trail Discovery**: Fetches actual trail names and surface types from **OpenStreetMap** (via Overpass API).
* **Technical Metrics**: Calculates precise distance in kilometers and total elevation gain (ascent).
* **Difficulty & Technical Grading**: Evaluates trails as Beginner, Moderate, or Expert and analyzes **OSM Tracktypes** (Grade 1-5) to distinguish between smooth gravel and rugged MTB paths.
* **Dynamic Routing & Surface Analysis**: Generates suggested loops (round trips) with a detailed **Percentage Breakdown** of surface types (asphalt, gravel, dirt, etc.).
* **Bike Setup Compatibility**: A first-of-its-kind feature that checks if a route is suitable for your specific bike (**Road, Gravel, or MTB**) and **tire width**, providing instant safety warnings.
* **Predictive Mud Risk Analysis**: A specialized model for off-roaders that cross-references **72h historical precipitation** with **soil geology** (e.g., clay vs. sand) to predict trail rideability.
* **TAEL (Terrain-Aware Evaporation Lag)**: A tactical model that cross-references 72h rainfall and geological drainage with real-time solar altitude to predict trail saturation and "Shadow-Lock" mud persistence.
* **Smart POI Scouting (Pit-Stop Finder)**: Automatically locates cycling-specific amenities like **drinking water fountains**, **bicycle repair stations**, and **mountain shelters** within a 2km radius of your route.
* **Smart Safety & Weather Forecast**: Cross-references location data with real-time weather to ensure you don't get caught in a storm.
* **Pro-Cycling Gear Advice**: Provides specific technical advice on clothing and gear based on temperature, wind, and rain thresholds.
* **Seamless Location Search**: No GPS coordinates required. Use natural language (e.g., *"Find a ride in Albano Laziale"*) via integrated Nominatim Geocoding.
* **Instant Map Previews**: Automatically generates a **Static Map (.png)** of the route to visualize the trail directly within the chat interface.
* **Local Expert Knowledge**: Specialized regional prompts for world-class destinations like the **Dolomites (UNESCO)**, **Moab (USA)**, and **Castelli Romani**.
* **Pro Climb Categorization**: Automatically identifies and names specific climbs (from **Category 4** to **Hors Catégorie**) using professional cycling standards based on length and average gradient.
* **Post-Ride Tactical Analysis (Strava Integration)**: Fuses actual **Strava** activity logs with environmental intelligence. By decoding GPS polylines, it cross-references your past performance with historical **Mud Risk** and weather data to validate your gear choice and analyze how trail conditions impacted your speed and effort.

## Why BikeScout? (vs Generic Maps)

While Google Maps or standard navigation tools are excellent for urban commuting, they fail when the terrain gets technical. **BikeScout** bridges the gap between a simple "line on a map" and the technical reality of professional cycling, turning your AI into an expert local guide.

### Truth in Elevation (Progressive Filtering)
Raw satellite data (SRTM) often suffers from "noise," overestimating total vertical gain by up to 40% in mountainous areas due to sudden spikes in readings.
* **Generic Maps:** Display "jagged" elevation profiles that inflate effort and make charts unreadable.
* **BikeScout:** Uses a **Progressive Elevation Filter**. Our algorithm recognizes and smooths out satellite sensor errors, returning a total ascent value that matches real-world barometric sensors (Garmin/Wahoo).

### Beyond "Paved" vs "Unpaved" (S-Scale Grading)
For a standard navigator, a trail is just a trail. For a cyclist, the difference between packed gravel and a bed of loose rocks is the difference between fun and danger.
* **Generic Maps:** Indiscriminately label everything that isn't asphalt as "unpaved."
* **BikeScout:** Parses deep OpenStreetMap metadata to extract the **MTB-Scale (S0-S5)** and **SAC-Scale**. It warns you if you'll encounter a Grade S0 (easy) or an S3 (technical with rocks and steps), allowing you to decide if your setup is appropriate.

### Beyond traditional POI
Generic maps often prioritize sponsored results or restaurants. BikeScout probes deep OpenStreetMap tags like amenity=drinking_water and shop=bicycle. These points are often verified by the cycling community, ensuring you find a working fountain on a mountain pass rather than a closed supermarket.

### Historical Weather data
Standard forecasts only tell you if it will rain. BikeScout analyzes what has already happened. Since clay-heavy soil can remain unrideable for days after a storm while sandy soil dries in hours, this tool provides the specific context needed for off-road decision making.

### Discipline-Specific Intelligence
Effort is relative to your gear. 500m of climbing feels different on a 7kg Road bike than on a 16kg Enduro rig with 2.4" knobby tires.
* **Generic Maps:** Provide "standard" travel times and difficulty based on generic averages.
* **BikeScout:** Features a **Dynamic Effort Engine**. It calculates difficulty and climb categorization (from Cat 4 to *Hors Catégorie*) based specifically on your **Bike Type** (Road, Gravel, MTB, Enduro) and your **Tire Setup**.

### Native AI Orchestration (MCP)
BikeScout isn't just an isolated script; it's a native extension for next-generation large language models.
* **Generic Maps:** Require manual searches, screenshots, and visual interpretation by the user.
* **BikeScout:** Is a **Model Context Protocol (MCP)** server. It allows Claude, Cursor, or other LLMs to "reason" like a local guide, automatically cross-referencing weather, soil type, and technical setup in a single conversational flow.

### Comparison at a Glance

| Feature | Generic Maps | BikeScout AI |
| :--- | :--- | :--- |
| **Elevation Gain** | Raw & Noisy | **Filtered & Realistic** |
| **Surface Analysis** | Basic (Paved/Dirt) | **Technical (S-Scale/Tracktype)** |
| **Difficulty Rating** | Time-based only | **Weighted by Bike Type** |
| **Climb Grading** | None | **UCI-Standard (Cat 4 to HC)** |
| **Safety Logistics** | General Stores/Gas | **Cycling POIs (Water/Repair/Shelter)** |
| **Condition Predictive** | Future Weather only | **Mud Risk (72h Rain + Soil Analysis)** |
| **AI Integration** | Manual / External | **Native MCP Tooling** |

## News, Blog & Live Demo

Stay updated with the latest tactical cycling intelligence, mission reports, and MCP ecosystem news.
* **Official Website:** [https://hifly81.github.io/bikescout](https://hifly81.github.io/bikescout)
* **Tactical Blog:** [https://hifly81.github.io/bikescout/site/blog.html](https://hifly81.github.io/bikescout/site/blog.html)
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

### How to obtain Strava API Credentials:
To enable Strava integration, you need to create a developer application and generate a long-lived Refresh Token:

1. **Create an App**: Go to the [Strava Settings API](https://www.strava.com/settings/api) and create an application (set "Localhost" as the Authorization Callback Domain).
2. **Get Client ID & Secret**: Note down your `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET`.
3. **Authorize and Get Code**: Paste the following URL in your browser (replace `YOUR_CLIENT_ID` with your actual ID):
   `https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=read,activity:read_all`
4. **Exchange Code for Refresh Token**: Click "Authorize", then copy the `code` parameter from the URL of the resulting blank page. Use this command in your terminal to get the final `STRAVA_REFRESH_TOKEN`:
   ```bash
   curl -X POST [https://www.strava.com/oauth/token](https://www.strava.com/oauth/token) \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d code=YOUR_CODE_FROM_URL \
     -d grant_type=authorization_code
   ```

## Installation

BikeScout is available on [PyPI](https://pypi.org/project/bikescout/). You can install it directly using `pip` or `uv`.

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

## Configuration for Claude Desktop

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
        "STRAVA_REFRESH_TOKEN": "YOUR_STRAVA_REFRESH_TOKEN"
      }
    }
  }
}
```

## Using BikeScout with VS Code

If your goal is to test the BikeScout server while you are coding, you don't actually need the Claude Desktop app. You can use VS Code along with the Cline (formerly Claude Dev) or Continue extensions.

- Install the Extension:

   Go to the VS Code Marketplace and install the **Cline** extension (or Continue). These extensions act as a "bridge" between the AI and your local machine.

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
- Open MCP Settings:

   In the extension settings (usually a gear icon or a specific "MCP" tab within the extension's side panel), look for the section titled "Configure MCP Servers".

- Add the JSON Configuration:

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
            "ORS_API_KEY": "YOUR_OPENROUTE_SERVICE_API_KEY",
            "STRAVA_CLIENT_ID": "YOUR_STRAVA_CLIENT_ID",
            "STRAVA_CLIENT_SECRET": "YOUR_STRAVA_CLIENT_SECRET",
            "STRAVA_REFRESH_TOKEN": "YOUR_STRAVA_REFRESH_TOKEN"
         }
      }
   }
}
```
- Start Scouting
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

You can ask **BikeScout** complex, multi-step requests. It combines real-time data with technical cycling intelligence to provide expert-level answers.

### Advanced Planning (Multi-Tool)
* *"I'm at **Monte Cavo** with my **Gravel bike (40mm tires)**. Plan a **25km loop** for me. Check if the terrain is compatible with my bike, verify the afternoon rain probability, and suggest a 'Fraschetta' for the finish. Use the **Castelli Romani guide**."*
* *"I want to ride in **Moab** tomorrow. I have a **hardtail MTB**. Find me a **20km route** that isn't too technical (avoid Grade 4/5 tracks), check the heat forecast, and give me the desert safety checklist."*

### Bike Setup & Surface Intelligence
* *"Check this route `[LAT, LON]` for a **15km loop**. I'm on a **Road Bike with 25mm tires**. Is it compatible? Give me the exact percentage of gravel vs asphalt."*
* *"I'm planning a ride in **Kyoto, Japan**. Find a **30km loop** that is at least **70% gravel**, but only if the rain probability is below **10%** for the next 4 hours."*

### Local Expertise
* *"Use the **Dolomiti local guide** to plan a road cycling route starting from **Cortina**. I need at least **800m of elevation gain**. Also, recommend the correct tire pressure for high-altitude descents and a mountain hut for a strudel stop."*
* *"Are there any named trails near **Vancouver, Canada**? Analyze the surface types and tell me if they are suitable for a beginner on an **E-MTB**."*

### Quick Tech Checks
* *"Give me the **safety checklist** and calculate the **tire pressure** for a **90kg rider** on **2.3" tubeless tires** for a muddy ride."*
* *"What is the terrain breakdown for a **10km ride** in **Taichung**? I need to know if I'll encounter any 'Grade 5' technical segments."*

### Post-Ride Analysis & Terrain Truth
* *"Analyze my Strava ride from 2026-04-12. Compare my average speed with the Mud Risk at that time and tell me if the terrain conditions were the reason for my slow pace."*
* *"Check my ride from last Sunday on Strava. Cross-reference the GPS path with the 72h rain history to see if the 'High' mud risk I encountered was accurately predicted."*
* *"Get my activity from Strava for [Date]. Based on the surface types detected and the weather context of that day, was my tire pressure setup (1.8 bar) optimal or should I have gone lower?"*

---

## Pre-Confiugured Prompts

BikeScout includes pre-configured **AI Prompts**. These prompts provide local context, gear tips, and cultural insights.

| Prompt Name                    | Destination              | Specialization                                                               |
|:-------------------------------|:-------------------------|:-----------------------------------------------------------------------------|
| `explore-moab-usa`             | 🏜️ 🇺🇸 Moab, Utah      | Desert riding, technical sandstone, hydration & gear safety.                 |
| `explore-castelliromani-italy` | 🇮🇹 🏔️ Castelli Romani | Volcanic terrain, steep climbs, Roman history, and local food stops.         |
| `explore-dolomiti-italy`       | 🇮🇹 🏛️ Dolomites       | Expert guide for cycling in the Dolomites (UNESCO Heritage), Northern Italy. |
| `explore-arenberg-france`	     | 🇫🇷 🚜 Arenberg Forest | Northern French Pavé, mud risk, tire pressure for cobbles, and "The Hell of the North."|
| `explore-finale-ligure-italy`	 | 🌊 🇮🇹 Finale Ligure	 | World-class Enduro, limestone rock gardens, and "Sea-to-Summit" trails|
| `explore-derby-australia`	     | 🌿 🇦🇺 Derby, Tasmania | Granite slabs, "Hero Dirt," and world-class MTB flow trails.|
| `explore-shimanami-japan`	     | 🌉 🇯🇵 Shimanami Kaido | Island hopping, road/gravel touring, and bridge wind analysis.|

### How to use them:

1. Open your MCP-compatible client (e.g., Claude Desktop or Cline).
2. Look for the **Prompts** library (usually a 📄 or ✨ icon).
3. Select an explorer prompt to start a guided session.

---

## Knowledge Resources

BikeScout provides direct access to specialized cycling knowledge bases via the **MCP Resource** protocol. These resources can be read by the AI to provide accurate, data-driven advice.

| Resource URI | Content | Use Case |
| :--- | :--- | :--- |
| `bikescout://safety/checklist` | Essential pre-ride safety steps. | Checking brakes, bolts, and emergency gear. |
| `bikescout://tech/tire-pressure` | Recommended PSI/Bar by terrain. | Optimizing grip for Mud, Rock, or Asphalt. |

### How to access:

In your AI client, you can ask:
* *"Read the safety checklist from BikeScout"* * *"What is the recommended tire pressure for wet gravel?"*
  The AI will automatically fetch the data from the resource URI.

---

## Tools Reference

**BikeScout** exposes specialized tools to the MCP host. Currently, the server provides a comprehensive scouting tool, with more modules planned for future releases.

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
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | Latitude of the starting point (e.g., `45.81`). |
| `lon` | `float` | Required | Longitude of the starting point (e.g., `9.08`). |
| `radius_km` | `int` | `10` | The target total length of the loop in kilometers. |
| `profile` | `string`| `cycling-mountain` | Routing profile: `cycling-mountain`, `cycling-road`, or `cycling-regular`. |
| `rider_weight_kg` | `float` | `80.0` | **Total rider weight.** Used to calculate technical compatibility and tire setup recommendations. |

#### **Tool Output Example (JSON):**
```json
{
  "status": "Success",
  "info": {
    "distance_km": 10.67,
    "ascent_m": 745,
    "difficulty": "🟠 Advanced (Requires good fitness and stamina)",
    "surface_analysis": {
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
          "technical_notes": "Technical grading based on OSM mountain standards."
        },
        "mud_risk_index": 0.1
      },
      "mechanical_setup": {
        "compatible": true,
        "bike_category": "mountain",
        "setup_details": "700c wheels | 84.0 PSI (5.79 Bar) [Standard Setup]",
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
  },
  "conditions": {
    "weather": [
      {
        "time": "10:00",
        "temp": "14.8°C",
        "rain_prob": "23%",
        "wind": "32.8 km/h"
      },
      {
        "time": "11:00",
        "temp": "15.0°C",
        "rain_prob": "40%",
        "wind": "32.4 km/h"
      },
      {
        "time": "12:00",
        "temp": "14.7°C",
        "rain_prob": "65%",
        "wind": "31.0 km/h"
      },
      {
        "time": "13:00",
        "temp": "13.8°C",
        "rain_prob": "78%",
        "wind": "28.6 km/h"
      }
    ],
    "mud_risk": {
      "status": "Success",
      "environmental_context": {
        "raw_rain_72h": "10.5mm",
        "avg_temp": "17.9°C",
        "avg_wind_speed": "19.2km/h",
        "drying_efficiency": "1.14x",
        "shadow_penalty_active": "Yes",
        "solar_altitude": "-18.2°"
      },
      "tactical_analysis": {
        "adjusted_moisture_index": 9.2,
        "mud_risk_score": "Medium",
        "surface_detected": "dirt",
        "safety_advice": "Damp soil. Slick roots and loose corners possible."
      }
    },
    "safety_advice": "💨 WINDY: Strong winds. Use caution on descents and open ridges."
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
  "map_image_url": "https://static-maps.fly.dev/staticmap?size=600x400&path=weight:3|color:red|41.761455,12.711841|41.76152,12.710373|41.761076,12.709096|41.760035,12.709483|41.759277,12.710744|41.758929,12.711532|41.757093,12.712508|41.753772,12.714909|41.74963,12.715928|41.748309,12.717065|41.747452,12.716023|41.748646,12.715071|41.746967,12.715361|41.744589,12.714556|41.744851,12.715735|41.744305,12.717544|41.743158,12.718267|41.742393,12.718359|41.741203,12.717956|41.740679,12.718472|41.739939,12.71837|41.739015,12.717709|41.73844,12.717027|41.737164,12.7168|41.73624,12.717525|41.733067,12.714569|41.731646,12.717553|41.731984,12.715879|41.733231,12.715695|41.73505,12.717395|41.737521,12.719066|41.738818,12.720568|41.739762,12.722252|41.741253,12.724031|41.742935,12.721113|41.743735,12.719028|41.745539,12.716748|41.747722,12.71534|41.749355,12.713807|41.748946,12.711107|41.749694,12.708977|41.750163,12.70773|41.751906,12.707686|41.754669,12.710229|41.757016,12.710369|41.759054,12.71113|41.75897,12.711756|41.760751,12.714322|41.761528,12.712515|41.761413,12.711403|41.761455,12.711841&maptype=mapnik",
  "gpx_content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<gpx version=\"1.1\" creator=\"BikeScout\" xmlns=\"http://www.topografix.com/GPX/1/1\">\n  <wpt lat=\"41.761793\" lon=\"12.709082\">\n    <name>Water Fountain 💧</name>\n    <sym>Watering Hole</sym>\n  </wpt>\n  <wpt lat=\"41.761158\" lon=\"12.703411\">\n    <name>Water Fountain 💧</name>\n    <sym>Watering Hole</sym>\n  </wpt>\n  <wpt lat=\"41.761246\" lon=\"12.703337\">\n    <name>Water Fountain 💧</name>\n    <sym>Watering Hole</sym>\n  </wpt>\n  <wpt lat=\"41.761305\" lon=\"12.703291\">\n    <name>Water Fountain 💧</name>\n    <sym>Watering Hole</sym>\n  </wpt>\n  <wpt lat=\"41.752849\" lon=\"12.708615\">\n    <name>SUMMIT: 895m</name>\n    <sym>Summit</sym>\n  </wpt>\n  <wpt lat=\"41.761165\" lon=\"12.708999\">\n    <name>WALL: 30%</name>\n    <sym>Danger Area</sym>\n  </wpt>\n  <wpt lat=\"41.759931\" lon=\"12.709608\">\n    <name>WALL: 30%</name>\n    <sym>Danger Area</sym>\n  </wpt>\n  <wpt lat=\"41.738585\" lon=\"12.720096\">\n    <name>WALL: 13%</name>\n    <sym>Danger Area</sym>\n  </wpt>\n  <wpt lat=\"41.739722\" lon=\"12.722081\">\n    <name>WALL: 24%</name>\n    <sym>Danger Area</sym>\n  </wpt>\n  <wpt lat=\"41.749825\" lon=\"12.708244\">\n    <name>WALL: 10%</name>\n    <sym>Danger Area</sym>\n  </wpt>\n  <trk>\n    <name>BikeScout Tactical Route</name>\n    <trkseg>\n      <trkpt lat=\"41.761455\" lon=\"12.711841\"><ele>705.2</ele></trkpt>\n      <trkpt lat=\"41.761426\" lon=\"12.711786\"><ele>706.4</ele></trkpt>\n      <trkpt lat=\"41.761415\" lon=\"12.711547\"><ele>739.0</ele></trkpt>\n      <trkpt lat=\"41.761413\" lon=\"12.711403\"><ele>739.0</ele></trkpt>\n      <trkpt lat=\"41.761533\" lon=\"12.711189\"><ele>739.0</ele></trkpt>\n      <trkpt lat=\"41.761533\" lon=\"12.711111\"><ele>739.0</ele></trkpt>\n      <trkpt lat=\"41.761553\" lon=\"12.710914\"><ele>732.5</ele></trkpt>\n      <trkpt lat=\"41.761527\" lon=\"12.710738\"><ele>730.9</ele></trkpt>\n      <trkpt lat=\"41.76152\" lon=\"12.710373\"><ele>726.0</ele></trkpt>\n      <trkpt lat=\"41.761443\" lon=\"12.710467\"><ele>726.0</ele></trkpt>\n      <trkpt lat=\"41.761361\" lon=\"12.710084\"><ele>720.5</ele></trkpt>\n      <trkpt lat=\"41.761278\" lon=\"12.709834\"><ele>701.0</ele></trkpt>\n      <trkpt lat=\"41.76118\" lon=\"12.709566\"><ele>701.0</ele></trkpt>\n      <trkpt lat=\"41.761145\" lon=\"12.709436\"><ele>696.0</ele></trkpt>\n      <trkpt lat=\"41.76113\" lon=\"12.709303\"><ele>697.0</ele></trkpt>\n      <trkpt lat=\"41.761165\" lon=\"12.708999\"><ele>677.0</ele></trkpt>\n      <trkpt lat=\"41.761076\" lon=\"12.709096\"><ele>697.0</ele></trkpt>\n      <trkpt lat=\"41.76085\" lon=\"12.709209\"><ele>699.9</ele></trkpt>\n      <trkpt lat=\"41.760785\" lon=\"12.709212\"><ele>698.8</ele></trkpt>\n      <trkpt lat=\"41.760714\" lon=\"12.709173\"><ele>707.0</ele></trkpt>\n      <trkpt lat=\"41.760609\" lon=\"12.709132\"><ele>687.6</ele></trkpt>\n      <trkpt lat=\"41.760552\" lon=\"12.709202\"><ele>707.0</ele></trkpt>\n      <trkpt lat=\"41.760339\" lon=\"12.709375\"><ele>707.0</ele></trkpt>\n      <trkpt lat=\"41.7601\" lon=\"12.709397\"><ele>707.0</ele></trkpt>\n      <trkpt lat=\"41.760035\" lon=\"12.709483\"><ele>707.0</ele></trkpt>\n      <trkpt lat=\"41.759931\" lon=\"12.709608\"><ele>721.0</ele></trkpt>\n      <trkpt lat=\"41.759633\" lon=\"12.709825\"><ele>721.0</ele></trkpt>\n      <trkpt lat=\"41.759591\" lon=\"12.710083\"><ele>730.1</ele></trkpt>\n      <trkpt lat=\"41.759516\" lon=\"12.710211\"><ele>732.9</ele></trkpt>\n      <trkpt lat=\"41.759501\" lon=\"12.710303\"><ele>742.0</ele></trkpt>\n      <trkpt lat=\"41.759482\" lon=\"12.710468\"><ele>742.0</ele></trkpt>\n      <trkpt lat=\"41.759307\" lon=\"12.710641\"><ele>742.0</ele></trkpt>\n      <trkpt lat=\"41.759277\" lon=\"12.710744\"><ele>742.0</ele></trkpt>\n      <trkpt lat=\"41.759207\" lon=\"12.71081\"><ele>748.1</ele></trkpt>\n      <trkpt lat=\"41.759121\" lon=\"12.71083\"><ele>760.0</ele></trkpt>\n      <trkpt lat=\"41.7591\" lon=\"12.710968\"><ele>763.6</ele></trkpt>\n      <trkpt lat=\"41.759054\" lon=\"12.71113\"><ele>765.0</ele></trkpt>\n      <trkpt lat=\"41.759017\" lon=\"12.711192\"><ele>765.0</ele></trkpt>\n      <trkpt lat=\"41.758978\" lon=\"12.711392\"><ele>765.0</ele></trkpt>\n      <trkpt lat=\"41.758957\" lon=\"12.711517\"><ele>765.0</ele></trkpt>\n      <trkpt lat=\"41.758929\" lon=\"12.711532\"><ele>764.0</ele></trkpt>\n      <trkpt lat=\"41.758892\" lon=\"12.711592\"><ele>763.6</ele></trkpt>\n      <trkpt lat=\"41.75889\" lon=\"12.711671\"><ele>759.0</ele></trkpt>\n      <trkpt lat=\"41.758749\" lon=\"12.711663\"><ele>765.0</ele></trkpt>\n      <trkpt lat=\"41.758633\" lon=\"12.711657\"><ele>765.0</ele></trkpt>\n      <trkpt lat=\"41.758372\" lon=\"12.711645\"><ele>765.0</ele></trkpt>\n      <trkpt lat=\"41.758255\" lon=\"12.711684\"><ele>764.0</ele></trkpt>\n      <trkpt lat=\"41.757572\" lon=\"12.712092\"><ele>764.0</ele></trkpt>\n      <trkpt lat=\"41.757093\" lon=\"12.712508\"><ele>768.3</ele></trkpt>\n      <trkpt lat=\"41.756557\" lon=\"12.71307\"><ele>774.0</ele></trkpt>\n      <trkpt lat=\"41.755964\" lon=\"12.713669\"><ele>769.0</ele></trkpt>\n      <trkpt lat=\"41.755364\" lon=\"12.714279\"><ele>778.0</ele></trkpt>\n      <trkpt lat=\"41.754917\" lon=\"12.71469\"><ele>786.9</ele></trkpt>\n      <trkpt lat=\"41.754694\" lon=\"12.714814\"><ele>786.6</ele></trkpt>\n      <trkpt lat=\"41.754538\" lon=\"12.714851\"><ele>788.0</ele></trkpt>\n      <trkpt lat=\"41.75426\" lon=\"12.714855\"><ele>799.0</ele></trkpt>\n      <trkpt lat=\"41.753772\" lon=\"12.714909\"><ele>800.5</ele></trkpt>\n      <trkpt lat=\"41.75347\" lon=\"12.714983\"><ele>800.2</ele></trkpt>\n      <trkpt lat=\"41.753054\" lon=\"12.715125\"><ele>800.7</ele></trkpt>\n      <trkpt lat=\"41.752776\" lon=\"12.715195\"><ele>800.8</ele></trkpt>\n      <trkpt lat=\"41.752627\" lon=\"12.715187\"><ele>800.7</ele></trkpt>\n      <trkpt lat=\"41.752562\" lon=\"12.715149\"><ele>801.0</ele></trkpt>\n      <trkpt lat=\"41.750632\" lon=\"12.715664\"><ele>843.0</ele></trkpt>\n      <trkpt lat=\"41.749774\" lon=\"12.715939\"><ele>843.0</ele></trkpt>\n      <trkpt lat=\"41.74963\" lon=\"12.715928\"><ele>848.6</ele></trkpt>\n      <trkpt lat=\"41.749333\" lon=\"12.716024\"><ele>848.0</ele></trkpt>\n      <trkpt lat=\"41.749125\" lon=\"12.716239\"><ele>849.4</ele></trkpt>\n      <trkpt lat=\"41.748989\" lon=\"12.716561\"><ele>850.7</ele></trkpt>\n      <trkpt lat=\"41.748893\" lon=\"12.716625\"><ele>851.8</ele></trkpt>\n      <trkpt lat=\"41.748741\" lon=\"12.716926\"><ele>851.8</ele></trkpt>\n      <trkpt lat=\"41.74871\" lon=\"12.71696\"><ele>851.0</ele></trkpt>\n      <trkpt lat=\"41.748541\" lon=\"12.717151\"><ele>857.5</ele></trkpt>\n      <trkpt lat=\"41.748309\" lon=\"12.717065\"><ele>859.6</ele></trkpt>\n      <trkpt lat=\"41.748157\" lon=\"12.716904\"><ele>860.4</ele></trkpt>\n      <trkpt lat=\"41.747925\" lon=\"12.716786\"><ele>861.1</ele></trkpt>\n      <trkpt lat=\"41.747813\" lon=\"12.716861\"><ele>861.7</ele></trkpt>\n      <trkpt lat=\"41.747044\" lon=\"12.716776\"><ele>866.0</ele></trkpt>\n      <trkpt lat=\"41.747124\" lon=\"12.716372\"><ele>854.5</ele></trkpt>\n      <trkpt lat=\"41.747231\" lon=\"12.716208\"><ele>854.0</ele></trkpt>\n      <trkpt lat=\"41.747356\" lon=\"12.716077\"><ele>853.8</ele></trkpt>\n      <trkpt lat=\"41.747452\" lon=\"12.716023\"><ele>853.6</ele></trkpt>\n      <trkpt lat=\"41.747566\" lon=\"12.716028\"><ele>854.4</ele></trkpt>\n      <trkpt lat=\"41.747715\" lon=\"12.715992\"><ele>855.0</ele></trkpt>\n      <trkpt lat=\"41.747952\" lon=\"12.715769\"><ele>855.1</ele></trkpt>\n      <trkpt lat=\"41.748299\" lon=\"12.715527\"><ele>853.5</ele></trkpt>\n      <trkpt lat=\"41.748489\" lon=\"12.715332\"><ele>854.5</ele></trkpt>\n      <trkpt lat=\"41.748623\" lon=\"12.715246\"><ele>855.0</ele></trkpt>\n      <trkpt lat=\"41.748662\" lon=\"12.715152\"><ele>856.0</ele></trkpt>\n      <trkpt lat=\"41.748646\" lon=\"12.715071\"><ele>856.0</ele></trkpt>\n      <trkpt lat=\"41.748641\" lon=\"12.714968\"><ele>846.3</ele></trkpt>\n      <trkpt lat=\"41.748527\" lon=\"12.714894\"><ele>843.0</ele></trkpt>\n      <trkpt lat=\"41.748442\" lon=\"12.714956\"><ele>833.3</ele></trkpt>\n      <trkpt lat=\"41.748366\" lon=\"12.714941\"><ele>831.7</ele></trkpt>\n      <trkpt lat=\"41.748046\" lon=\"12.714995\"><ele>829.6</ele></trkpt>\n      <trkpt lat=\"41.747673\" lon=\"12.714986\"><ele>829.0</ele></trkpt>\n      <trkpt lat=\"41.747293\" lon=\"12.715127\"><ele>829.8</ele></trkpt>\n      <trkpt lat=\"41.746967\" lon=\"12.715361\"><ele>827.2</ele></trkpt>\n      <trkpt lat=\"41.746866\" lon=\"12.715394\"><ele>826.9</ele></trkpt>\n      <trkpt lat=\"41.746705\" lon=\"12.715355\"><ele>826.1</ele></trkpt>\n      <trkpt lat=\"41.746466\" lon=\"12.715477\"><ele>815.0</ele></trkpt>\n      <trkpt lat=\"41.745477\" lon=\"12.715505\"><ele>796.1</ele></trkpt>\n      <trkpt lat=\"41.74513\" lon=\"12.715198\"><ele>787.1</ele></trkpt>\n      <trkpt lat=\"41.744917\" lon=\"12.715153\"><ele>785.4</ele></trkpt>\n      <trkpt lat=\"41.744856\" lon=\"12.714912\"><ele>783.2</ele></trkpt>\n      <trkpt lat=\"41.744589\" lon=\"12.714556\"><ele>783.0</ele></trkpt>\n      <trkpt lat=\"41.744316\" lon=\"12.714352\"><ele>780.5</ele></trkpt>\n      <trkpt lat=\"41.744074\" lon=\"12.714134\"><ele>759.0</ele></trkpt>\n      <trkpt lat=\"41.744177\" lon=\"12.714506\"><ele>785.0</ele></trkpt>\n      <trkpt lat=\"41.744269\" lon=\"12.714764\"><ele>785.9</ele></trkpt>\n      <trkpt lat=\"41.744352\" lon=\"12.714932\"><ele>786.0</ele></trkpt>\n      <trkpt lat=\"41.744593\" lon=\"12.715299\"><ele>786.0</ele></trkpt>\n      <trkpt lat=\"41.744813\" lon=\"12.715583\"><ele>785.9</ele></trkpt>\n      <trkpt lat=\"41.744851\" lon=\"12.715735\"><ele>785.8</ele></trkpt>\n      <trkpt lat=\"41.744832\" lon=\"12.715936\"><ele>785.7</ele></trkpt>\n      <trkpt lat=\"41.744792\" lon=\"12.716038\"><ele>785.9</ele></trkpt>\n      <trkpt lat=\"41.744603\" lon=\"12.716361\"><ele>787.3</ele></trkpt>\n      <trkpt lat=\"41.744539\" lon=\"12.716498\"><ele>787.3</ele></trkpt>\n      <trkpt lat=\"41.744504\" lon=\"12.716652\"><ele>787.3</ele></trkpt>\n      <trkpt lat=\"41.744453\" lon=\"12.717093\"><ele>789.2</ele></trkpt>\n      <trkpt lat=\"41.744416\" lon=\"12.717259\"><ele>790.4</ele></trkpt>\n      <trkpt lat=\"41.744305\" lon=\"12.717544\"><ele>793.2</ele></trkpt>\n      <trkpt lat=\"41.744204\" lon=\"12.717717\"><ele>795.7</ele></trkpt>\n      <trkpt lat=\"41.74412\" lon=\"12.71781\"><ele>796.2</ele></trkpt>\n      <trkpt lat=\"41.744031\" lon=\"12.717853\"><ele>796.5</ele></trkpt>\n      <trkpt lat=\"41.743591\" lon=\"12.717953\"><ele>799.1</ele></trkpt>\n      <trkpt lat=\"41.743404\" lon=\"12.718027\"><ele>799.6</ele></trkpt>\n      <trkpt lat=\"41.743261\" lon=\"12.718134\"><ele>799.5</ele></trkpt>\n      <trkpt lat=\"41.74319\" lon=\"12.7183\"><ele>791.0</ele></trkpt>\n      <trkpt lat=\"41.743158\" lon=\"12.718267\"><ele>797.8</ele></trkpt>\n      <trkpt lat=\"41.743126\" lon=\"12.718286\"><ele>798.2</ele></trkpt>\n      <trkpt lat=\"41.743112\" lon=\"12.718381\"><ele>798.6</ele></trkpt>\n      <trkpt lat=\"41.74312\" lon=\"12.718453\"><ele>798.1</ele></trkpt>\n      <trkpt lat=\"41.74292\" lon=\"12.71853\"><ele>795.6</ele></trkpt>\n      <trkpt lat=\"41.742694\" lon=\"12.71846\"><ele>791.9</ele></trkpt>\n      <trkpt lat=\"41.74258\" lon=\"12.718366\"><ele>789.9</ele></trkpt>\n      <trkpt lat=\"41.742484\" lon=\"12.71834\"><ele>788.1</ele></trkpt>\n      <trkpt lat=\"41.742393\" lon=\"12.718359\"><ele>787.9</ele></trkpt>\n      <trkpt lat=\"41.742274\" lon=\"12.718299\"><ele>787.2</ele></trkpt>\n      <trkpt lat=\"41.742203\" lon=\"12.718289\"><ele>786.3</ele></trkpt>\n      <trkpt lat=\"41.742036\" lon=\"12.718195\"><ele>783.2</ele></trkpt>\n      <trkpt lat=\"41.741982\" lon=\"12.718141\"><ele>783.0</ele></trkpt>\n      <trkpt lat=\"41.741745\" lon=\"12.718069\"><ele>780.0</ele></trkpt>\n      <trkpt lat=\"41.741515\" lon=\"12.717933\"><ele>778.2</ele></trkpt>\n      <trkpt lat=\"41.741349\" lon=\"12.717918\"><ele>777.9</ele></trkpt>\n      <trkpt lat=\"41.741203\" lon=\"12.717956\"><ele>777.1</ele></trkpt>\n      <trkpt lat=\"41.741089\" lon=\"12.717881\"><ele>776.1</ele></trkpt>\n      <trkpt lat=\"41.740953\" lon=\"12.717897\"><ele>775.6</ele></trkpt>\n      <trkpt lat=\"41.740899\" lon=\"12.717961\"><ele>775.6</ele></trkpt>\n      <trkpt lat=\"41.74084\" lon=\"12.718067\"><ele>775.1</ele></trkpt>\n      <trkpt lat=\"41.740839\" lon=\"12.718313\"><ele>776.8</ele></trkpt>\n      <trkpt lat=\"41.740799\" lon=\"12.718366\"><ele>749.0</ele></trkpt>\n      <trkpt lat=\"41.740746\" lon=\"12.718437\"><ele>740.4</ele></trkpt>\n      <trkpt lat=\"41.740679\" lon=\"12.718472\"><ele>739.9</ele></trkpt>\n      <trkpt lat=\"41.740667\" lon=\"12.718383\"><ele>738.5</ele></trkpt>\n      <trkpt lat=\"41.740558\" lon=\"12.718395\"><ele>737.9</ele></trkpt>\n      <trkpt lat=\"41.740468\" lon=\"12.718431\"><ele>737.4</ele></trkpt>\n      <trkpt lat=\"41.740356\" lon=\"12.718425\"><ele>735.3</ele></trkpt>\n      <trkpt lat=\"41.740329\" lon=\"12.718453\"><ele>734.6</ele></trkpt>\n      <trkpt lat=\"41.740338\" lon=\"12.718476\"><ele>733.9</ele></trkpt>\n      <trkpt lat=\"41.740175\" lon=\"12.718502\"><ele>731.2</ele></trkpt>\n      <trkpt lat=\"41.739939\" lon=\"12.71837\"><ele>727.5</ele></trkpt>\n      <trkpt lat=\"41.739782\" lon=\"12.718326\"><ele>726.3</ele></trkpt>\n      <trkpt lat=\"41.739722\" lon=\"12.718255\"><ele>724.5</ele></trkpt>\n      <trkpt lat=\"41.739602\" lon=\"12.718271\"><ele>724.6</ele></trkpt>\n      <trkpt lat=\"41.73946\" lon=\"12.718255\"><ele>723.8</ele></trkpt>\n      <trkpt lat=\"41.739486\" lon=\"12.718296\"><ele>723.8</ele></trkpt>\n      <trkpt lat=\"41.739323\" lon=\"12.718271\"><ele>719.8</ele></trkpt>\n      <trkpt lat=\"41.739136\" lon=\"12.717897\"><ele>715.5</ele></trkpt>\n      <trkpt lat=\"41.739015\" lon=\"12.717709\"><ele>711.1</ele></trkpt>\n      <trkpt lat=\"41.738947\" lon=\"12.717731\"><ele>710.3</ele></trkpt>\n      <trkpt lat=\"41.738856\" lon=\"12.717682\"><ele>708.2</ele></trkpt>\n      <trkpt lat=\"41.738693\" lon=\"12.717397\"><ele>706.2</ele></trkpt>\n      <trkpt lat=\"41.738615\" lon=\"12.717379\"><ele>705.5</ele></trkpt>\n      <trkpt lat=\"41.73855\" lon=\"12.717391\"><ele>704.8</ele></trkpt>\n      <trkpt lat=\"41.738432\" lon=\"12.717267\"><ele>702.1</ele></trkpt>\n      <trkpt lat=\"41.738382\" lon=\"12.71714\"><ele>699.8</ele></trkpt>\n      <trkpt lat=\"41.73844\" lon=\"12.717027\"><ele>699.8</ele></trkpt>\n      <trkpt lat=\"41.738334\" lon=\"12.716948\"><ele>698.6</ele></trkpt>\n      <trkpt lat=\"41.737971\" lon=\"12.716332\"><ele>697.3</ele></trkpt>\n      <trkpt lat=\"41.73761\" lon=\"12.716122\"><ele>697.0</ele></trkpt>\n      <trkpt lat=\"41.737613\" lon=\"12.715988\"><ele>685.0</ele></trkpt>\n      <trkpt lat=\"41.737389\" lon=\"12.716287\"><ele>675.3</ele></trkpt>\n      <trkpt lat=\"41.73732\" lon=\"12.716474\"><ele>672.0</ele></trkpt>\n      <trkpt lat=\"41.737272\" lon=\"12.71657\"><ele>672.0</ele></trkpt>\n      <trkpt lat=\"41.737164\" lon=\"12.7168\"><ele>673.6</ele></trkpt>\n      <trkpt lat=\"41.737064\" lon=\"12.716946\"><ele>673.8</ele></trkpt>\n      <trkpt lat=\"41.736954\" lon=\"12.717071\"><ele>674.0</ele></trkpt>\n      <trkpt lat=\"41.736679\" lon=\"12.717216\"><ele>674.8</ele></trkpt>\n      <trkpt lat=\"41.736618\" lon=\"12.71722\"><ele>674.4</ele></trkpt>\n      <trkpt lat=\"41.736496\" lon=\"12.717376\"><ele>673.6</ele></trkpt>\n      <trkpt lat=\"41.73645\" lon=\"12.717411\"><ele>673.3</ele></trkpt>\n      <trkpt lat=\"41.736309\" lon=\"12.717465\"><ele>668.0</ele></trkpt>\n      <trkpt lat=\"41.73624\" lon=\"12.717525\"><ele>669.4</ele></trkpt>\n      <trkpt lat=\"41.735962\" lon=\"12.717547\"><ele>670.0</ele></trkpt>\n      <trkpt lat=\"41.735071\" lon=\"12.71651\"><ele>659.0</ele></trkpt>\n      <trkpt lat=\"41.734681\" lon=\"12.716026\"><ele>650.9</ele></trkpt>\n      <trkpt lat=\"41.734373\" lon=\"12.715449\"><ele>645.0</ele></trkpt>\n      <trkpt lat=\"41.733791\" lon=\"12.714744\"><ele>639.4</ele></trkpt>\n      <trkpt lat=\"41.733381\" lon=\"12.714152\"><ele>629.0</ele></trkpt>\n      <trkpt lat=\"41.733243\" lon=\"12.714392\"><ele>634.3</ele></trkpt>\n      <trkpt lat=\"41.733067\" lon=\"12.714569\"><ele>634.4</ele></trkpt>\n      <trkpt lat=\"41.733138\" lon=\"12.714934\"><ele>634.5</ele></trkpt>\n      <trkpt lat=\"41.733121\" lon=\"12.715566\"><ele>635.0</ele></trkpt>\n      <trkpt lat=\"41.733087\" lon=\"12.715627\"><ele>638.0</ele></trkpt>\n      <trkpt lat=\"41.732659\" lon=\"12.716249\"><ele>647.3</ele></trkpt>\n      <trkpt lat=\"41.732292\" lon=\"12.716599\"><ele>648.6</ele></trkpt>\n      <trkpt lat=\"41.732206\" lon=\"12.716757\"><ele>648.8</ele></trkpt>\n      <trkpt lat=\"41.731781\" lon=\"12.717326\"><ele>649.9</ele></trkpt>\n      <trkpt lat=\"41.731646\" lon=\"12.717553\"><ele>650.1</ele></trkpt>\n      <trkpt lat=\"41.731551\" lon=\"12.717645\"><ele>650.1</ele></trkpt>\n      <trkpt lat=\"41.731541\" lon=\"12.717649\"><ele>650.2</ele></trkpt>\n      <trkpt lat=\"41.731379\" lon=\"12.717718\"><ele>650.2</ele></trkpt>\n      <trkpt lat=\"41.731064\" lon=\"12.71789\"><ele>652.0</ele></trkpt>\n      <trkpt lat=\"41.731241\" lon=\"12.71739\"><ele>647.0</ele></trkpt>\n      <trkpt lat=\"41.73179\" lon=\"12.716452\"><ele>642.9</ele></trkpt>\n      <trkpt lat=\"41.731843\" lon=\"12.716243\"><ele>641.3</ele></trkpt>\n      <trkpt lat=\"41.731984\" lon=\"12.715879\"><ele>640.5</ele></trkpt>\n      <trkpt lat=\"41.732014\" lon=\"12.715662\"><ele>640.1</ele></trkpt>\n      <trkpt lat=\"41.732059\" lon=\"12.715544\"><ele>640.1</ele></trkpt>\n      <trkpt lat=\"41.732099\" lon=\"12.715485\"><ele>640.2</ele></trkpt>\n      <trkpt lat=\"41.73215\" lon=\"12.715447\"><ele>640.3</ele></trkpt>\n      <trkpt lat=\"41.732362\" lon=\"12.71547\"><ele>640.1</ele></trkpt>\n      <trkpt lat=\"41.733014\" lon=\"12.71563\"><ele>639.9</ele></trkpt>\n      <trkpt lat=\"41.733087\" lon=\"12.715627\"><ele>638.0</ele></trkpt>\n      <trkpt lat=\"41.733231\" lon=\"12.715695\"><ele>647.4</ele></trkpt>\n      <trkpt lat=\"41.733456\" lon=\"12.715895\"><ele>649.4</ele></trkpt>\n      <trkpt lat=\"41.733669\" lon=\"12.71599\"><ele>649.2</ele></trkpt>\n      <trkpt lat=\"41.733986\" lon=\"12.716331\"><ele>649.0</ele></trkpt>\n      <trkpt lat=\"41.734249\" lon=\"12.716698\"><ele>660.0</ele></trkpt>\n      <trkpt lat=\"41.734467\" lon=\"12.716984\"><ele>661.2</ele></trkpt>\n      <trkpt lat=\"41.734581\" lon=\"12.717182\"><ele>661.3</ele></trkpt>\n      <trkpt lat=\"41.734806\" lon=\"12.717349\"><ele>662.3</ele></trkpt>\n      <trkpt lat=\"41.73505\" lon=\"12.717395\"><ele>662.7</ele></trkpt>\n      <trkpt lat=\"41.735466\" lon=\"12.717344\"><ele>662.6</ele></trkpt>\n      <trkpt lat=\"41.735962\" lon=\"12.717547\"><ele>670.0</ele></trkpt>\n      <trkpt lat=\"41.736191\" lon=\"12.717742\"><ele>672.4</ele></trkpt>\n      <trkpt lat=\"41.736573\" lon=\"12.71812\"><ele>671.8</ele></trkpt>\n      <trkpt lat=\"41.736755\" lon=\"12.718478\"><ele>672.7</ele></trkpt>\n      <trkpt lat=\"41.737144\" lon=\"12.718781\"><ele>678.0</ele></trkpt>\n      <trkpt lat=\"41.737328\" lon=\"12.718969\"><ele>692.5</ele></trkpt>\n      <trkpt lat=\"41.737521\" lon=\"12.719066\"><ele>694.6</ele></trkpt>\n      <trkpt lat=\"41.737945\" lon=\"12.719388\"><ele>696.5</ele></trkpt>\n      <trkpt lat=\"41.738153\" lon=\"12.719516\"><ele>697.9</ele></trkpt>\n      <trkpt lat=\"41.738457\" lon=\"12.719667\"><ele>700.4</ele></trkpt>\n      <trkpt lat=\"41.738553\" lon=\"12.719817\"><ele>702.6</ele></trkpt>\n      <trkpt lat=\"41.738585\" lon=\"12.720096\"><ele>704.3</ele></trkpt>\n      <trkpt lat=\"41.738634\" lon=\"12.720268\"><ele>705.6</ele></trkpt>\n      <trkpt lat=\"41.738706\" lon=\"12.720439\"><ele>706.3</ele></trkpt>\n      <trkpt lat=\"41.738818\" lon=\"12.720568\"><ele>709.0</ele></trkpt>\n      <trkpt lat=\"41.73889\" lon=\"12.720718\"><ele>710.5</ele></trkpt>\n      <trkpt lat=\"41.739058\" lon=\"12.720933\"><ele>712.2</ele></trkpt>\n      <trkpt lat=\"41.739154\" lon=\"12.721083\"><ele>714.5</ele></trkpt>\n      <trkpt lat=\"41.73929\" lon=\"12.721437\"><ele>718.5</ele></trkpt>\n      <trkpt lat=\"41.739354\" lon=\"12.721512\"><ele>720.2</ele></trkpt>\n      <trkpt lat=\"41.73961\" lon=\"12.722027\"><ele>729.5</ele></trkpt>\n      <trkpt lat=\"41.739722\" lon=\"12.722081\"><ele>731.2</ele></trkpt>\n      <trkpt lat=\"41.739762\" lon=\"12.722252\"><ele>734.4</ele></trkpt>\n      <trkpt lat=\"41.740051\" lon=\"12.722746\"><ele>745.1</ele></trkpt>\n      <trkpt lat=\"41.740162\" lon=\"12.722918\"><ele>746.9</ele></trkpt>\n      <trkpt lat=\"41.740251\" lon=\"12.722982\"><ele>750.8</ele></trkpt>\n      <trkpt lat=\"41.740371\" lon=\"12.723111\"><ele>753.7</ele></trkpt>\n      <trkpt lat=\"41.740587\" lon=\"12.723636\"><ele>760.4</ele></trkpt>\n      <trkpt lat=\"41.740643\" lon=\"12.723712\"><ele>763.4</ele></trkpt>\n      <trkpt lat=\"41.741019\" lon=\"12.723883\"><ele>768.6</ele></trkpt>\n      <trkpt lat=\"41.741253\" lon=\"12.724031\"><ele>785.0</ele></trkpt>\n      <trkpt lat=\"41.741545\" lon=\"12.72389\"><ele>791.0</ele></trkpt>\n      <trkpt lat=\"41.741713\" lon=\"12.72361\"><ele>794.2</ele></trkpt>\n      <trkpt lat=\"41.742009\" lon=\"12.723266\"><ele>795.9</ele></trkpt>\n      <trkpt lat=\"41.742127\" lon=\"12.722962\"><ele>796.3</ele></trkpt>\n      <trkpt lat=\"41.742531\" lon=\"12.722517\"><ele>803.6</ele></trkpt>\n      <trkpt lat=\"41.742665\" lon=\"12.722105\"><ele>803.4</ele></trkpt>\n      <trkpt lat=\"41.742923\" lon=\"12.721792\"><ele>805.4</ele></trkpt>\n      <trkpt lat=\"41.742935\" lon=\"12.721113\"><ele>806.8</ele></trkpt>\n      <trkpt lat=\"41.743262\" lon=\"12.720283\"><ele>805.0</ele></trkpt>\n      <trkpt lat=\"41.743323\" lon=\"12.720096\"><ele>804.3</ele></trkpt>\n      <trkpt lat=\"41.743508\" lon=\"12.719661\"><ele>807.2</ele></trkpt>\n      <trkpt lat=\"41.743493\" lon=\"12.719539\"><ele>808.5</ele></trkpt>\n      <trkpt lat=\"41.743431\" lon=\"12.71936\"><ele>822.0</ele></trkpt>\n      <trkpt lat=\"41.743484\" lon=\"12.719344\"><ele>820.8</ele></trkpt>\n      <trkpt lat=\"41.743593\" lon=\"12.719244\"><ele>821.0</ele></trkpt>\n      <trkpt lat=\"41.743735\" lon=\"12.719028\"><ele>820.7</ele></trkpt>\n      <trkpt lat=\"41.743859\" lon=\"12.718879\"><ele>820.4</ele></trkpt>\n      <trkpt lat=\"41.744222\" lon=\"12.718584\"><ele>821.2</ele></trkpt>\n      <trkpt lat=\"41.744699\" lon=\"12.718045\"><ele>821.7</ele></trkpt>\n      <trkpt lat=\"41.745017\" lon=\"12.717654\"><ele>822.7</ele></trkpt>\n      <trkpt lat=\"41.745127\" lon=\"12.717457\"><ele>824.6</ele></trkpt>\n      <trkpt lat=\"41.74529\" lon=\"12.717035\"><ele>824.1</ele></trkpt>\n      <trkpt lat=\"41.745429\" lon=\"12.71683\"><ele>823.7</ele></trkpt>\n      <trkpt lat=\"41.745539\" lon=\"12.716748\"><ele>824.0</ele></trkpt>\n      <trkpt lat=\"41.745975\" lon=\"12.716579\"><ele>825.0</ele></trkpt>\n      <trkpt lat=\"41.746272\" lon=\"12.716437\"><ele>824.2</ele></trkpt>\n      <trkpt lat=\"41.746403\" lon=\"12.7163\"><ele>825.2</ele></trkpt>\n      <trkpt lat=\"41.746703\" lon=\"12.715865\"><ele>850.0</ele></trkpt>\n      <trkpt lat=\"41.746792\" lon=\"12.715759\"><ele>837.2</ele></trkpt>\n      <trkpt lat=\"41.746884\" lon=\"12.715685\"><ele>836.1</ele></trkpt>\n      <trkpt lat=\"41.747329\" lon=\"12.71547\"><ele>837.1</ele></trkpt>\n      <trkpt lat=\"41.747722\" lon=\"12.71534\"><ele>838.0</ele></trkpt>\n      <trkpt lat=\"41.74834\" lon=\"12.715218\"><ele>843.6</ele></trkpt>\n      <trkpt lat=\"41.748646\" lon=\"12.715071\"><ele>856.0</ele></trkpt>\n      <trkpt lat=\"41.74872\" lon=\"12.71501\"><ele>849.2</ele></trkpt>\n      <trkpt lat=\"41.748776\" lon=\"12.714932\"><ele>847.8</ele></trkpt>\n      <trkpt lat=\"41.748884\" lon=\"12.714624\"><ele>843.0</ele></trkpt>\n      <trkpt lat=\"41.748978\" lon=\"12.714328\"><ele>841.5</ele></trkpt>\n      <trkpt lat=\"41.749114\" lon=\"12.71409\"><ele>833.0</ele></trkpt>\n      <trkpt lat=\"41.749355\" lon=\"12.713807\"><ele>862.0</ele></trkpt>\n      <trkpt lat=\"41.749442\" lon=\"12.713634\"><ele>862.0</ele></trkpt>\n      <trkpt lat=\"41.749484\" lon=\"12.713446\"><ele>862.0</ele></trkpt>\n      <trkpt lat=\"41.749495\" lon=\"12.713292\"><ele>873.0</ele></trkpt>\n      <trkpt lat=\"41.749504\" lon=\"12.712981\"><ele>862.3</ele></trkpt>\n      <trkpt lat=\"41.749466\" lon=\"12.712772\"><ele>861.9</ele></trkpt>\n      <trkpt lat=\"41.748995\" lon=\"12.711427\"><ele>853.8</ele></trkpt>\n      <trkpt lat=\"41.748964\" lon=\"12.711288\"><ele>851.3</ele></trkpt>\n      <trkpt lat=\"41.748946\" lon=\"12.711107\"><ele>848.9</ele></trkpt>\n      <trkpt lat=\"41.748963\" lon=\"12.710808\"><ele>846.7</ele></trkpt>\n      <trkpt lat=\"41.749126\" lon=\"12.709987\"><ele>845.9</ele></trkpt>\n      <trkpt lat=\"41.749234\" lon=\"12.709747\"><ele>849.2</ele></trkpt>\n      <trkpt lat=\"41.749404\" lon=\"12.709522\"><ele>879.0</ele></trkpt>\n      <trkpt lat=\"41.749481\" lon=\"12.709441\"><ele>879.0</ele></trkpt>\n      <trkpt lat=\"41.749614\" lon=\"12.709299\"><ele>871.9</ele></trkpt>\n      <trkpt lat=\"41.749665\" lon=\"12.70918\"><ele>873.2</ele></trkpt>\n      <trkpt lat=\"41.749694\" lon=\"12.708977\"><ele>871.5</ele></trkpt>\n      <trkpt lat=\"41.749683\" lon=\"12.708609\"><ele>869.7</ele></trkpt>\n      <trkpt lat=\"41.749722\" lon=\"12.70853\"><ele>864.0</ele></trkpt>\n      <trkpt lat=\"41.749736\" lon=\"12.708399\"><ele>859.0</ele></trkpt>\n      <trkpt lat=\"41.749806\" lon=\"12.708299\"><ele>857.8</ele></trkpt>\n      <trkpt lat=\"41.749825\" lon=\"12.708244\"><ele>854.0</ele></trkpt>\n      <trkpt lat=\"41.749818\" lon=\"12.708169\"><ele>854.0</ele></trkpt>\n      <trkpt lat=\"41.749943\" lon=\"12.707935\"><ele>854.0</ele></trkpt>\n      <trkpt lat=\"41.750163\" lon=\"12.70773\"><ele>879.8</ele></trkpt>\n      <trkpt lat=\"41.750376\" lon=\"12.707572\"><ele>888.0</ele></trkpt>\n      <trkpt lat=\"41.750713\" lon=\"12.707457\"><ele>876.2</ele></trkpt>\n      <trkpt lat=\"41.75081\" lon=\"12.707481\"><ele>875.7</ele></trkpt>\n      <trkpt lat=\"41.751247\" lon=\"12.707442\"><ele>875.8</ele></trkpt>\n      <trkpt lat=\"41.751319\" lon=\"12.707477\"><ele>875.5</ele></trkpt>\n      <trkpt lat=\"41.751554\" lon=\"12.707493\"><ele>875.0</ele></trkpt>\n      <trkpt lat=\"41.751643\" lon=\"12.70753\"><ele>876.2</ele></trkpt>\n      <trkpt lat=\"41.751906\" lon=\"12.707686\"><ele>877.0</ele></trkpt>\n      <trkpt lat=\"41.751926\" lon=\"12.707723\"><ele>877.8</ele></trkpt>\n      <trkpt lat=\"41.752155\" lon=\"12.707825\"><ele>888.0</ele></trkpt>\n      <trkpt lat=\"41.752849\" lon=\"12.708615\"><ele>895.7</ele></trkpt>\n      <trkpt lat=\"41.753254\" lon=\"12.709244\"><ele>881.2</ele></trkpt>\n      <trkpt lat=\"41.753974\" lon=\"12.709903\"><ele>866.4</ele></trkpt>\n      <trkpt lat=\"41.754386\" lon=\"12.710161\"><ele>850.0</ele></trkpt>\n      <trkpt lat=\"41.75452\" lon=\"12.710219\"><ele>839.3</ele></trkpt>\n      <trkpt lat=\"41.754669\" lon=\"12.710229\"><ele>832.5</ele></trkpt>\n      <trkpt lat=\"41.755578\" lon=\"12.710131\"><ele>820.5</ele></trkpt>\n      <trkpt lat=\"41.755795\" lon=\"12.710092\"><ele>817.6</ele></trkpt>\n      <trkpt lat=\"41.756011\" lon=\"12.710009\"><ele>809.2</ele></trkpt>\n      <trkpt lat=\"41.756302\" lon=\"12.70996\"><ele>808.3</ele></trkpt>\n      <trkpt lat=\"41.756951\" lon=\"12.709938\"><ele>776.0</ele></trkpt>\n      <trkpt lat=\"41.757008\" lon=\"12.709957\"><ele>788.7</ele></trkpt>\n      <trkpt lat=\"41.757039\" lon=\"12.710023\"><ele>790.1</ele></trkpt>\n      <trkpt lat=\"41.757016\" lon=\"12.710369\"><ele>788.4</ele></trkpt>\n      <trkpt lat=\"41.757044\" lon=\"12.710442\"><ele>786.3</ele></trkpt>\n      <trkpt lat=\"41.757501\" lon=\"12.710573\"><ele>782.6</ele></trkpt>\n      <trkpt lat=\"41.757753\" lon=\"12.710664\"><ele>782.5</ele></trkpt>\n      <trkpt lat=\"41.757994\" lon=\"12.71081\"><ele>782.2</ele></trkpt>\n      <trkpt lat=\"41.758308\" lon=\"12.711072\"><ele>778.8</ele></trkpt>\n      <trkpt lat=\"41.758379\" lon=\"12.711075\"><ele>778.7</ele></trkpt>\n      <trkpt lat=\"41.75844\" lon=\"12.71105\"><ele>765.0</ele></trkpt>\n      <trkpt lat=\"41.759054\" lon=\"12.71113\"><ele>765.0</ele></trkpt>\n      <trkpt lat=\"41.759017\" lon=\"12.711192\"><ele>765.0</ele></trkpt>\n      <trkpt lat=\"41.758978\" lon=\"12.711392\"><ele>765.0</ele></trkpt>\n      <trkpt lat=\"41.758957\" lon=\"12.711517\"><ele>765.0</ele></trkpt>\n      <trkpt lat=\"41.758929\" lon=\"12.711532\"><ele>764.0</ele></trkpt>\n      <trkpt lat=\"41.758892\" lon=\"12.711592\"><ele>763.6</ele></trkpt>\n      <trkpt lat=\"41.75889\" lon=\"12.711671\"><ele>759.0</ele></trkpt>\n      <trkpt lat=\"41.75892\" lon=\"12.71173\"><ele>759.0</ele></trkpt>\n      <trkpt lat=\"41.75897\" lon=\"12.711756\"><ele>759.0</ele></trkpt>\n      <trkpt lat=\"41.759019\" lon=\"12.711742\"><ele>759.0</ele></trkpt>\n      <trkpt lat=\"41.759054\" lon=\"12.711695\"><ele>759.0</ele></trkpt>\n      <trkpt lat=\"41.759175\" lon=\"12.711859\"><ele>757.1</ele></trkpt>\n      <trkpt lat=\"41.759328\" lon=\"12.71212\"><ele>756.0</ele></trkpt>\n      <trkpt lat=\"41.75971\" lon=\"12.712778\"><ele>748.0</ele></trkpt>\n      <trkpt lat=\"41.760483\" lon=\"12.714051\"><ele>740.0</ele></trkpt>\n      <trkpt lat=\"41.760647\" lon=\"12.71424\"><ele>736.7</ele></trkpt>\n      <trkpt lat=\"41.760751\" lon=\"12.714322\"><ele>736.2</ele></trkpt>\n      <trkpt lat=\"41.760925\" lon=\"12.714409\"><ele>735.7</ele></trkpt>\n      <trkpt lat=\"41.761118\" lon=\"12.714471\"><ele>731.0</ele></trkpt>\n      <trkpt lat=\"41.761609\" lon=\"12.713519\"><ele>734.0</ele></trkpt>\n      <trkpt lat=\"41.761942\" lon=\"12.71287\"><ele>722.6</ele></trkpt>\n      <trkpt lat=\"41.761954\" lon=\"12.712776\"><ele>724.8</ele></trkpt>\n      <trkpt lat=\"41.761928\" lon=\"12.712723\"><ele>725.7</ele></trkpt>\n      <trkpt lat=\"41.761879\" lon=\"12.712678\"><ele>727.2</ele></trkpt>\n      <trkpt lat=\"41.761528\" lon=\"12.712515\"><ele>728.3</ele></trkpt>\n      <trkpt lat=\"41.761472\" lon=\"12.712462\"><ele>728.2</ele></trkpt>\n      <trkpt lat=\"41.761367\" lon=\"12.712292\"><ele>727.9</ele></trkpt>\n      <trkpt lat=\"41.761296\" lon=\"12.712119\"><ele>727.6</ele></trkpt>\n      <trkpt lat=\"41.761267\" lon=\"12.711997\"><ele>727.4</ele></trkpt>\n      <trkpt lat=\"41.761257\" lon=\"12.711858\"><ele>730.0</ele></trkpt>\n      <trkpt lat=\"41.761282\" lon=\"12.711681\"><ele>735.5</ele></trkpt>\n      <trkpt lat=\"41.761349\" lon=\"12.71151\"><ele>739.0</ele></trkpt>\n      <trkpt lat=\"41.761413\" lon=\"12.711403\"><ele>739.0</ele></trkpt>\n      <trkpt lat=\"41.761415\" lon=\"12.711547\"><ele>739.0</ele></trkpt>\n      <trkpt lat=\"41.761426\" lon=\"12.711786\"><ele>706.4</ele></trkpt>\n      <trkpt lat=\"41.761455\" lon=\"12.711841\"><ele>705.2</ele></trkpt>\n    </trkseg>\n  </trk>\n</gpx>"
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

#### **Parameters:**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | Latitude of the starting point. |
| `lon` | `float` | Required | Longitude of the starting point. |
| `radius_km` | `int` | `10` | The total target distance of the loop (Round Trip). |
| `profile` | `str` | `cycling-mountain` | ORS routing profile (e.g., `cycling-road`, `cycling-mountain`). |
| `bike_type` | `str` | `MTB` | User's bike (Options: `Road`, `Gravel`, `MTB`, `E-MTB`, `Enduro`). |
| `tire_size_option` | `str` | `29` | Standard wheel sizes (MTB: `26`, `27.5`, `29` | Road/Gravel: `700c`, `650b`). |
| `rider_weight_kg` | `float` | `80.0` | **Total rider weight.** Used to calculate technical compatibility and tire setup recommendations. |
| `points` | `int` | `3` | Complexity of the loop shape (3 = triangle, 10 = circular). |
| `seed` | `int` | `42` | Random seed. Change it to discover a different route variation in the same area. |
| `surface_pref`| `str` | `neutral` | Routing preference (Options: `neutral`, `avoid_unpaved`, `prefer_trails`). |

#### **Technical Insights:**

> **Reality Filter:** This tool automatically reduces raw satellite elevation data by up to 40% on steep terrain to correct for SRTM sensor noise, ensuring the "Elevation Gain" matches real-world barometric sensors.
>
> **Effort Multiplier:** Climb categories are calculated with a **1.4x intensity factor** for MTB profiles to account for the increased rolling resistance and technical effort of off-road ascending.
>
> **MTB-Scale Integration:** Routes are analyzed for technical obstacles. An "S3" rating will trigger warnings for Gravel/Road setups, indicating sections with rock gardens or high steps.

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
      "technical_notes": "Technical grading based on OSM mountain standards."
    },
    "mud_risk_index": 0.1
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
      "technical_notes": "Technical grading based on OSM mountain standards."
    },
    "mud_risk_index": 0.1
  },
  "mechanical_setup": {
    "compatible": true,
    "bike_category": "ROAD",
    "setup_details": "700c wheels | 87.0 PSI (6.0 Bar) [Efficiency Setup]",
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
  "safety_warnings": []
}
```

**Example Output (JSON) for Gravel:**
```json
{
  "status": "Success",
  "profile_used": "cycling-mountain",
  "tactical_briefing": {
    "distance_km": 27.31,
    "elevation_gain_m": 885,
    "climb_category": "Hors Catégorie (HC) - Legendary Challenge",
    "avg_gradient_est": "10.8%",
    "technical_difficulty": {
      "mtb_scale": "Standard / Unclassified",
      "trail_visibility": "Excellent",
      "technical_notes": "Technical grading based on OSM mountain standards."
    },
    "mud_risk_index": 0.1
  },
  "mechanical_setup": {
    "compatible": true,
    "bike_category": "Gravel",
    "setup_details": "700c wheels | 34.0 PSI (2.34 Bar) [Standard Setup]",
    "rider_weight_baseline": "80.0kg"
  },
  "surface_breakdown": [
    {
      "type": "Unknown",
      "percentage": "42.0%"
    },
    {
      "type": "Paved",
      "percentage": "28.2%"
    },
    {
      "type": "Compact",
      "percentage": "23.9%"
    },
    {
      "type": "Grass",
      "percentage": "3.1%"
    },
    {
      "type": "Concrete",
      "percentage": "1.2%"
    },
    {
      "type": "Unpaved",
      "percentage": "1.1%"
    },
    {
      "type": "Asphalt",
      "percentage": "0.4%"
    }
  ],
  "safety_warnings": [
    "Comfort warning: 3.1% is Grass."
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
* **Static Maps:** Map previews are generated using Static Maps via Fly.dev, utilizing OpenStreetMap data.
* **Post-ride analysis**: Provided by Strava. Post-ride analysis and GPS telemetry are accessed via the [Strava API](https://developers.strava.com/docs/reference).
