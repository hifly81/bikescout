# BikeScout Documentation

Tactical Cycling Intelligence | MCP Server for AI-Powered Mission Planning.

_Version: 1.3.0 - April 2026_

## License & Data Attributions

### Software License
This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** - see the [LICENSE](LICENSE) file for details.

#### Why AGPLv3? 
BikeScout contains proprietary-grade tactical logic (such as the TAEL® Mud Reservoir Model). The AGPLv3 ensures that:
- Transparency: Any modified version of BikeScout used to provide a service over a network (SaaS/Cloud) must make its full source code available to the community.
- Integrity: The core tactical intelligence remains open and collaborative, preventing "closed-source" commercial hijacking of the platform's unique algorithms.

### Data Sources & Credits
BikeScout aggregates data from several open providers. Users of this server must adhere to their respective terms:

* **Routing & Map Data:** Provided by [OpenRouteService](https://openrouteservice.org/) by HeiGIT.
* **Geospatial & Geocoding Data:** © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors. Data is available under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/). Geocoding service powered by [Nominatim](https://nominatim.org/).
* **Weather Forecasts:** Powered by [Open-Meteo](https://open-meteo.com/). Data is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

---

## Key Features

### 🏔️ Terrain & Surface Intelligence
- **Real Trail Discovery**: Fetches actual trail names and surface data directly from OpenStreetMap (via Overpass API).
- **Surface Breakdown**: Generates a detailed percentage breakdown of the entire route (asphalt, gravel, dirt, etc.).
- **Technical Grading**: Analyzes OSM Tracktypes (Grade 1-5) to distinguish between smooth fire roads and rugged, technical MTB paths.
- **Bike Compatibility Check**: A first-of-its-kind feature that validates if a route suits your specific bike (Road, Gravel, MTB) and tire width, issuing instant safety warnings.

### ⛈️ Predictive Environmental Modeling
- **TAEL® Algorithm**: Our flagship **Terrain-Aware Evaporation Lag** model that predicts "Shadow-Lock" mud on north-facing slopes by analyzing real-time solar altitude and soil memory.
- **Predictive Mud Risk**: Advanced rideability analysis based on geological soil composition (Clay vs. Sand) and 72-hour precipitation history.
- **Tactical Ride Window**: A "Go/No-Go" decision engine that identifies the optimal start time by cross-referencing atmospheric hazards with terrain saturation.
- **Smart Safety Weather**: Hyper-local 4-hour forecasts with expert-level gear and layering advice based on temperature, wind, and rain thresholds.
- **Hydration Scout**: Calculates real-time liquid and electrolyte requirements based on the route's technical intensity and the maximum forecasted temperature.

### 📈 High-Fidelity Navigation & Altimetry
- **Wall-Sense Technology**: Automatically detects gradients >10% and injects active `<wpt>` alerts into your GPX file to warn you on your head unit before you hit the "wall."
- **Tactical GPX Export**: Produces optimized GPX files (max 1,500 points) to eliminate GPS signal noise while strictly preserving critical elevation spikes.
- **Visual Elevation Profiling**: Generates high-resolution graphical sparklines with chromatic difficulty scaling, cached locally to save AI context window.
- **Pro Climb Categorization**: Automatically identifies and ranks climbs using professional **UCI standards** (from Category 4 to Hors Catégorie).

### 🤖 Mission Logistics & Intelligence
- **Smart POI Scouting**: Scans a 5km radius along the route for drinking water, bicycle repair stations, and mountain shelters.
- **E-MTB Energy Management**: Calculates estimated battery consumption (**Wh**) based on rider weight, assist mode (Eco/Boost), and terrain-specific rolling resistance.
- **Local Expert Skills**: Specialized "Local Wisdom" knowledge bases for world-class destinations like The Dolomites, Moab, and Finale Ligure.
- **Post-Ride Analysis**: Fuses activity logs with environmental intelligence to analyze how mud and weather conditions impacted your actual performance.

### 🏁 Pro-Racing & Tactical Engine
- **VAM & Power Modeling**: Precise **$W/kg$** requirements based on professional VAM targets and UCI climb categorization.
- **Echelon Alert**: Predictive crosswind analysis that flags "Danger Zones" for peloton splits based on real-time wind vectors.
- **Tactical GPX Injection**: Injects "Climb Start," "Crux," and "Crosswind" markers as active Waypoints for on-device race management.
- **The "Crux" Identifier**: Detects the steepest gradient transitions within a climb to signal the optimal point for a decisive attack.
---

## Why BikeScout? (The Intelligence Gap)

Standard navigation tools like Google Maps or Komoot are designed for simple "lines on a map." They treat every trail as a generic path. **BikeScout** is built for **Mission Planning**, bridging the gap between raw data and technical reality. We don't just show you the way; we provide the **Tactical Intelligence** needed to conquer the terrain.

### 🛰️ Truth in Elevation (Progressive Filtering)
Standard SRTM satellite data is notoriously "noisy," often overestimating vertical gain by up to 40% due to sensor spikes in mountain environments.
* **Generic Maps:** Display jagged, unrealistic elevation profiles that inflate effort and drain battery.
* **BikeScout:** Employs a **Progressive Elevation Filter (SMA)**. Our algorithm sanitizes satellite noise, delivering ascent values that match professional barometric sensors (Garmin/Wahoo) for pinpoint energy planning.

### 🪨 Beyond "Paved" vs "Unpaved" (S-Scale Grading)
To a standard navigator, a trail is just a trail. To a scout, the difference between packed gravel and loose rock gardens is the difference between a flow trail and a rescue mission.
* **Generic Maps:** Indiscriminately label everything non-asphalt as "unpaved."
* **BikeScout:** Probes deep OSM metadata to extract **MTB-Scale (S0-S5)** and **Tracktypes (Grade 1-5)**. It warns you if your setup is "under-gunned" for a technical section before you are committed.

### 🌧️ Ground Memory & TAEL® Logic
Standard forecasts only tell you if it *might* rain. BikeScout analyzes what *actually* happened to the soil.
* **Generic Maps:** Provide only current atmospheric snapshots.
* **BikeScout:** Uses the **TAEL® (Terrain-Aware Evaporation Lag)** index. By cross-referencing 72h precipitation history with soil geology (Clay vs. Sand) and solar altitude, it predicts where "Shadow-Lock" mud persists even on sunny days.

### ⚡ E-MTB & Mechanical Synchronization
Effort is relative to your machine. A 20% gradient feels different on a 7kg Road bike than on a 24kg E-MTB rig.
* **Generic Maps:** Offer "one-size-fits-all" travel times and difficulty ratings.
* **BikeScout:** Features a **Dynamic Effort Engine**. It calculates battery drain ($Wh$), tire pressure ($PSI$), and climb categorization based specifically on your **Total System Weight**, **Bike Type**, and **Tire Width**.

### 🤖 Native AI Orchestration (MCP)
The ultimate competitive advantage: BikeScout isn't just a script; it’s a specialized brain for your AI.
* **Generic Maps:** Require manual searching, external tabs, and visual guessing.
* **BikeScout:** Is a native **Model Context Protocol (MCP)** server. It allows LLMs like Claude, ChatGPT, or Cursor to "reason" like a local guide, automatically synthesizing weather, terrain, and logistics into a single tactical briefing.

---

### 📊 Strategic Comparison at a Glance

| Feature | Generic Navigators | BikeScout Tactical AI |
| :--- | :--- | :--- |
| **Elevation Accuracy** | Raw & Inflated | **Filtered & Realistic (SMA)** |
| **Surface Analysis** | Basic (Paved/Dirt) | **Technical (S-Scale/Tracktype)** |
| **Effort Calculation** | Time-based average | **Physics-based (Weight/Friction)** |
| **Condition Prediction** | Future Weather only | **Mud Risk (72h Rain + Soil Memory)** |
| **Climb Categorization** | None | **UCI-Standard (Cat 4 to HC)** |
| **Logistics** | Sponsored / Restaurants | **Tactical (Water/Repair/Shelter)** |
| **AI Integration** | Manual / External | **Native MCP Tooling** |
---

## Skills

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
| `bikescout://knowledge/moab-usa` | 🏜️ **Moab, Utah** | High-desert survival, Slickrock traction mastery, and extreme hydration protocols. |
| `bikescout://knowledge/castelliromani-italy` | 🌋 **Castelli Romani** | Volcanic soil behavior (dust/mud), aggressive spikes in gradient, and cultural stop protocols. |
| `bikescout://knowledge/dolomiti-italy` | 🏔️ **Dolomites, Italy** | High-altitude weather vigilance, UNESCO limestone grip analysis, and 1:1 gearing strategies. |
| `bikescout://knowledge/trouee-darenberg-france` | 🧱 **Arenberg Forest** | Vibration damping on Pavé, stone humidity risk (TAEL®), and "Roubaix-spec" setup. |
| `bikescout://knowledge/finale-ligure-italy` | 🌊 **Finale Ligure** | EWS standards, brake fade management, and limestone rock garden suspension tuning. |
| `bikescout://knowledge/derby-australia` | 🌿 **Derby, Tasmania** | Granite slab traction, "Hero Dirt" saturation analysis, and high-speed rebound optimization. |
| `bikescout://knowledge/shimanamikaido-japan` | 🌉 **Shimanami Kaido** | Bridge crosswind analysis, island-hopping logistics, and road/gravel touring efficiency. |


### **How These Skills Work: Retrieve-and-Reason**

The AI goes beyond simple data reading, performing a dynamic synthesis in four phases:

1.  **Context Detection**: Identifies the region and mission type (e.g., *Enduro in Finale Ligure*).
2.  **Foundation Setting**: Invokes `get_baseline_mechanics` to establish a technical starting point (e.g., *1.8 Bar for MTB*).
3.  **Local Skill Invocation**: Triggers the local skill (e.g., `get_finale_intel`) to load the geological profile (e.g., *"Wet Limestone = Zero Traction"*).
4.  **Synthesized Briefing**: Cross-references everything with real-time data.
    * *Example:* The `analyze_route_surfaces` tool will suggest lowering pressure to 1.6 Bar and using soft compounds *because* the local expert intelligence knows that specific terrain doesn't drain quickly after the rain detected by the weather tool.

---

## Tools Reference

**BikeScout** exposes specialized tools to the MCP host. Currently, the server provides a comprehensive scouting tool, with more modules planned for future releases.

### **Object Schemas**

#### **Rider Profile (`rider`)**

Used for tire pressure and difficulty scaling.

| Field | Type | Default | Description |
| :--- | :--- |:--------| :--- |
| `weight_kg` | `float` |         | Total weight (rider + gear) for PSI and energy calculations. |
| `fitness_level` | `string` |         | Affects difficulty grading. Options: `beginner`, `intermediate`, `advanced`, `pro`. |

#### **Bike Setup (`bike`)**
| Field | Type     | Default | Description                                                                                          |
| :--- |:---------|:--------|:-----------------------------------------------------------------------------------------------------|
| `bike_type` | `string` |         | Geometry profile. Options: `Road`, `Gravel`, `MTB`, `Enduro`,`E-MTB`.                                |
| `tire_size` | `string` | `29`    | Diameter/Standard. Options: `26`, `27.5`, `29`, `32`, `700c`, `650b`.                                |
| `tire_width_mm` | `int`    | 54      | The actual width of the tire in mm. Critical for surface safety thresholds. Value between `18` and `75`. |
| `is_ebike` | `bool`   | `false` | If true, triggers battery consumption and motor-assist logic.                                        |
| `battery_wh` | `int`    |         | Battery capacity in Watt-hours (required if `is_ebike` is true).                                     |

#### **Mission Constraints (`mission`)**
| Field                | Type     | Default            | Description                                                                                                                                                                                                                                                                                            |
|:---------------------|:---------|:-------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `radius_km`          | `int`    |                    | Total target distance for the loop.                                                                                                                                                                                                                                                                    |
| `profile`            | `string` | `cycling-mountain` | ORS Routing profile.                                                                                                                                                                                                                                                                                   |
| `surface_preference` | `string` | `neutral`          | Options: `neutral`, `avoid_unpaved`, `prefer_trails`.                                                                                                                                                                                                                                                  |
| `complexity`         | `int`    | `3`                | Complexity of the loop (higher = more circular).                                                                                                                                                                                                                                                       |
| `seed`               | `int`    | `42`               | Randomizer seed to reproduce specific route variations.                                                                                                                                                                                                                                                |
| `assist_mode`        | `string` | `Eco`              | Defines the motor's power output profile (Eco, Trail, Boost). This tactical parameter scales the energy consumption model by adjusting the motor-to-rider assistance ratio, directly impacting predicted battery range and "Safety Buffer" alerts based on terrain resistance. 'Eco', 'Trail', 'Boost' |

#### **Route Geometry (`geometry`)**
| Field                | Type     | Default | Description                                                                                                                                                                                                                                                                                            |
|:---------------------|:---------|:--------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `coordinates`          | `list[list[float]]`    | `...`   | A list of GPS points in GeoJSON format. Each sub-list represents a coordinate triplet: [longitude, latitude, elevation]. This sequence is used by the SMA Filter to sanitize elevation and by the Haversine formula for geodesic accuracy.                                                                                                                                                                                                                                                                   |

---

### `geocode_location`
This tool acts as the intelligent "entry point" for all natural language queries. It translates place names into geographical coordinates, enabling a seamless experience where users don't need to provide raw GPS data.

#### **Functionality:**
* **Forward Geocoding:** Converts city names, landmarks, or addresses (e.g., "Passo dello Stelvio") into lat and lon.
* **Disambiguation:** Returns the full display name to confirm the AI has found the correct location.
* **OSM Integration:** Uses the Nominatim API (OpenStreetMap) for reliable, open-source data.

#### **Parameters:**
| Parameter | Type     | Default | Description                                                    |
| :--- |:---------| :--- |:---------------------------------------------------------------|
| `location_name` | `string` | Required | The name of the place to search for (e.g., "Frascati, Italy"). |
| `language` | `string` |  | header Accept-Language , e.g. en,it,fr,es                      |

#### **Tool Output Example (JSON):**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "lat": 38.5738096,
  "lon": -109.546214,
  "display_name": "Moab, Grand County, Utah, 84532, United States",
  "class": "boundary",
  "type": "administrative",
  "importance": 0.4671633623008776
}
```

---

### `trail_scout`
The flagship tool of the server. It acts as a **Master Orchestrator**, merging geographic routing with real-time environmental data and technical bike-setup analysis to provide a comprehensive **"Cycling Dossier"**.

#### **Functionality**
* **Dynamic Round-Trip and A-->B Routing**: Interfaces with **OpenRouteService (ORS)** to generate a route on the user's preferred distance, profile (MTB, Road, Gravel).
* **Multi-Engine Integration**:
  - **Surface & Compatibility**: Automatically triggers the `get_surface_analyzer` to check if the trail suits the user's bike type and tire width.
  - **Predictive Mud Risk**: Cross-references the last **72 hours of precipitation** with soil geology (clay, sand, dirt) to estimate trail rideability.
  - **Live Weather Check**: Fetches a 4-hour window forecast and provides pro-cycling gear advice (clothing/layers).
  - **Cycling POI Scout**: Scans a 2km radius around the route for **drinking water**, **bicycle repair stations**, and **mountain shelters**.
* **Technical Grading**: Identifies and categorizes climbs using **UCI-standardization** (Cat 4 to HC) based on length and average gradient.
* **Visual & Navigational Assets**:
    * Generates a Map (.png) preview for instant visualization.
    * Enhanced GPX Engine: Produces a high-utility GPX XML string, ready to be loaded on Garmin, Strava,... 
Unlike standard GPS files, BikeScout automatically injects active <wpt> (waypoint) tags that trigger alerts on Garmin, Wahoo, and Hammerhead units for:
      - Summit Alerts: Marks the highest elevation point of the route. 
      - Wall Alerts: Flags steep sections (gradient > 10%) before you reach them. 
      - Hydration & Service: Precisely locates water fountains and repair shops found during the POI scouting.

#### **Parameters:**
| Parameter        | Type | Default | Description                                                |
|:-----------------| :--- | :--- |:-----------------------------------------------------------|
| `latitude`       | `float` | Required | Latitude of the starting point (e.g., `45.81`).            |
| `longitude`      | `float` | Required | Longitude of the starting point (e.g., `9.08`).            |
| **`rider`**      | `object` | Required | [Rider Profile](#rider-profile-rider).                     |
| **`bike`**       | `object` | Required | [Bike Setup](#bike-setup-bike).                            |
| **`mission`**    | `object` | Required | [Mission Constraints](#mission-constraints-mission).       |
| `dest_latitude`  | `float` |  | Latitude of the ending point (e.g., `45.81`).              |
| `dest_longitude` | `float` |  | Longitude of the ending point (e.g., `9.08`).            |
| `include_gpx`    | `bool` | `True` | Whether to include the raw XML GPX content.                |
| `include_map`    | `bool` | `False` | Whether to generate the Static Map URL.                    |
| `style`          | `string` | `filled`          | Visual style of the profile, "sparkline", "filled", "bars" |                     |
| `output_level`   | `string` | `standard` | Verbosity level: `summary`, `standard`, or `full`.         |
| `target_date`    | `string` |  | target_date: Optional string in 'YYYY-MM-DD' format        |

#### **Tool Output Example (JSON):**

Round Route Type:

```json
{
  "payload_version": "1.3",
  "status": "Success",
  "info": {
    "distance_km": 46.35,
    "ascent_m": 1830,
    "difficulty": "🔴 Expert (Challenging distance or very steep climbs)",
    "surface_analysis": {
      "status": "Success",
      "profile_used": "cycling-mountain",
      "tactical_briefing": {
        "distance_km": 46.35,
        "elevation_gain_m": 1830,
        "climb_category": "Hors Catégorie (HC) - Legendary Challenge",
        "avg_gradient_est": "13.2%",
        "technical_difficulty": {
          "mtb_scale": "Standard / Unclassified",
          "trail_visibility": "Excellent",
          "technical_notes": "Technical grading based on OSM mountain standards.",
          "fitness_context": "Evaluated for intermediate level"
        },
        "mud_risk": {
          "score": 43.94,
          "label": "Extreme",
          "details": "Total saturation. Trail damage likely. Recommend Go/No-Go re-evaluation.",
          "environmental_factors": {
            "raw_rain_72h": "12.1mm",
            "avg_temp": "19.3°C",
            "drying_efficiency": "0.28x",
            "shadow_penalty_active": "Yes",
            "solar_altitude": "-30.0°"
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
          "percentage": "53.1%"
        },
        {
          "type": "Paved",
          "percentage": "39.1%"
        },
        {
          "type": "Compact",
          "percentage": "6.1%"
        },
        {
          "type": "Concrete",
          "percentage": "0.8%"
        },
        {
          "type": "Unpaved",
          "percentage": "0.6%"
        },
        {
          "type": "Asphalt",
          "percentage": "0.3%"
        }
      ],
      "emtb_tactical": {
        "estimated_drain_wh": 11024.5,
        "remaining_battery_pct": 0,
        "safety_buffer_status": "CRITICAL",
        "breakdown_wh": {
          "horizontal_base": 556.3,
          "vertical_climb": 691.5,
          "terrain_friction": 9776.7
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
        "time": "23:00",
        "temp": "12.7°C",
        "rain_prob": "0%",
        "wind": "7.6 km/h"
      }
    ],
    "mud_risk": {
      "status": "Success",
      "environmental_context": {
        "raw_rain_72h": "12.1mm",
        "avg_temp": "19.3°C",
        "drying_efficiency": "0.28x",
        "shadow_penalty_active": "Yes",
        "solar_altitude": "-30.0°"
      },
      "tactical_analysis": {
        "adjusted_moisture_index": 43.94,
        "mud_risk_score": "Extreme",
        "surface_detected": "Unknown",
        "safety_advice": "Total saturation. Trail damage likely. Recommend Go/No-Go re-evaluation."
      }
    },
    "max_temp_detected": "12.7°C",
    "safety_advice": "🌥️ CHILLY: Light jacket or arm warmers recommended."
  },
  "logistics": {
    "nutrition_plan": {
      "status": "Success",
      "mission_nutrition_briefing": {
        "fluids": {
          "total_liters": 2.5,
          "hourly_rate_ml": 458
        },
        "carbohydrates": {
          "total_grams": 220,
          "hourly_target_g": 40,
          "intensity_context": "Low"
        },
        "tactical_advice": [
          "ELECTROLYTE CRITICAL: High sweat rate or duration detected. Add sodium to bottles."
        ]
      }
    },
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
  "map_path": "bikescout://maps/tactical_map_6af64c_1777452416.png",
  "mcp_resource_uri_map": "bikescout://maps/tactical_map_6af64c_1777452416.png",
  "mcp_resource_uri_gpx": "bikescout://gpx/tactical_route_3c3c37.gpx",
  "gpx_export_path": "/home/test/.bikescout/gpx/tactical_route_3c3c37.gpx",
  "gpx_stats": {
    "total_points": 945,
    "healed_points": 945,
    "waypoints_count": 11
  },
  "elevation_profile_path": "/home/test/.bikescout/altimetry/bs_altimetry_3c3c37.png",
  "mcp_resource_uri_elevation_profile": "bikescout://altimetry/bs_altimetry_3c3c37.png"
}
```

A-->B Route Type:

```json
{
  "payload_version": "1.3",
  "status": "Success",
  "info": {
    "route_type": "A to B",
    "distance_km": 135.87,
    "ascent_m": 3040,
    "difficulty": "🔥 Expert (Challenging distance or very steep climbs)",
    "surface_analysis": {
      "status": "Success",
      "profile_used": "cycling-road",
      "metadata": {
        "analyzed_date": "2026-04-29T14:07:33.379339+00:00",
        "api_extras": [
          "waytype",
          "surface"
        ]
      },
      "tactical_briefing": {
        "distance_km": 135.87,
        "elevation_gain_m": 3040,
        "climb_category": "Hors Catégorie (HC) - Legendary Challenge",
        "avg_gradient_est": "5.0%",
        "mud_intelligence": {
          "score": 0,
          "label": "Unknown",
          "traction_risk": "Low",
          "trail_damage_risk": "Low",
          "dry_time_eta": "Ready Now",
          "safety_advice": "Check local conditions."
        }
      },
      "mechanical_setup": {
        "compatible": true,
        "setup_details": "700c wheels | 86.0 PSI (5.93 Bar) [Efficiency Setup]",
        "bike_type": "Road"
      },
      "surface_breakdown": [
        {
          "type": "Paved",
          "percentage": "74.0%"
        },
        {
          "type": "Unknown",
          "percentage": "23.5%"
        },
        {
          "type": "Asphalt",
          "percentage": "2.5%"
        },
        {
          "type": "Other",
          "percentage": "0.1%"
        },
        {
          "type": "Concrete",
          "percentage": "0.0%"
        }
      ],
      "emtb_tactical": null,
      "safety_warnings": []
    }
  },
  "conditions": {
    "weather": [
      {
        "time": "00:00",
        "temp": "10.2°C",
        "app_temp": "6.8°C",
        "rain_prob": "0%",
        "rain_mm": "0.0 mm",
        "wind": "7.4 km/h",
        "gusts": "18.4 km/h"
      },
      {
        "time": "01:00",
        "temp": "10.0°C",
        "app_temp": "6.7°C",
        "rain_prob": "0%",
        "rain_mm": "0.0 mm",
        "wind": "7.3 km/h",
        "gusts": "19.8 km/h"
      },
      {
        "time": "02:00",
        "temp": "9.9°C",
        "app_temp": "6.4°C",
        "rain_prob": "0%",
        "rain_mm": "0.0 mm",
        "wind": "7.6 km/h",
        "gusts": "20.5 km/h"
      },
      {
        "time": "03:00",
        "temp": "9.4°C",
        "app_temp": "5.8°C",
        "rain_prob": "0%",
        "rain_mm": "0.0 mm",
        "wind": "7.4 km/h",
        "gusts": "20.5 km/h"
      },
      {
        "time": "04:00",
        "temp": "9.3°C",
        "app_temp": "5.8°C",
        "rain_prob": "0%",
        "rain_mm": "0.0 mm",
        "wind": "7.6 km/h",
        "gusts": "21.2 km/h"
      },
      {
        "time": "05:00",
        "temp": "9.8°C",
        "app_temp": "6.4°C",
        "rain_prob": "0%",
        "rain_mm": "0.0 mm",
        "wind": "7.4 km/h",
        "gusts": "21.2 km/h"
      },
      {
        "time": "06:00",
        "temp": "11.6°C",
        "app_temp": "8.7°C",
        "rain_prob": "0%",
        "rain_mm": "0.0 mm",
        "wind": "6.0 km/h",
        "gusts": "20.9 km/h"
      },
      {
        "time": "07:00",
        "temp": "14.8°C",
        "app_temp": "11.7°C",
        "rain_prob": "0%",
        "rain_mm": "0.0 mm",
        "wind": "4.7 km/h",
        "gusts": "17.6 km/h"
      },
      {
        "time": "08:00",
        "temp": "16.0°C",
        "app_temp": "12.9°C",
        "rain_prob": "0%",
        "rain_mm": "0.0 mm",
        "wind": "4.2 km/h",
        "gusts": "19.8 km/h"
      },
      {
        "time": "09:00",
        "temp": "17.0°C",
        "app_temp": "13.9°C",
        "rain_prob": "0%",
        "rain_mm": "0.0 mm",
        "wind": "6.1 km/h",
        "gusts": "25.2 km/h"
      },
      {
        "time": "10:00",
        "temp": "18.1°C",
        "app_temp": "15.7°C",
        "rain_prob": "0%",
        "rain_mm": "0.0 mm",
        "wind": "9.4 km/h",
        "gusts": "25.6 km/h"
      },
      {
        "time": "11:00",
        "temp": "18.1°C",
        "app_temp": "15.0°C",
        "rain_prob": "0%",
        "rain_mm": "0.0 mm",
        "wind": "12.0 km/h",
        "gusts": "31.7 km/h"
      },
      {
        "time": "12:00",
        "temp": "19.0°C",
        "app_temp": "16.5°C",
        "rain_prob": "3%",
        "rain_mm": "0.0 mm",
        "wind": "13.4 km/h",
        "gusts": "35.3 km/h"
      },
      {
        "time": "13:00",
        "temp": "19.1°C",
        "app_temp": "16.5°C",
        "rain_prob": "3%",
        "rain_mm": "0.0 mm",
        "wind": "14.1 km/h",
        "gusts": "36.7 km/h"
      },
      {
        "time": "14:00",
        "temp": "18.5°C",
        "app_temp": "15.1°C",
        "rain_prob": "5%",
        "rain_mm": "0.0 mm",
        "wind": "12.9 km/h",
        "gusts": "36.4 km/h"
      },
      {
        "time": "15:00",
        "temp": "18.0°C",
        "app_temp": "14.2°C",
        "rain_prob": "3%",
        "rain_mm": "0.0 mm",
        "wind": "11.9 km/h",
        "gusts": "33.5 km/h"
      },
      {
        "time": "16:00",
        "temp": "17.0°C",
        "app_temp": "13.8°C",
        "rain_prob": "5%",
        "rain_mm": "0.0 mm",
        "wind": "9.4 km/h",
        "gusts": "31.7 km/h"
      },
      {
        "time": "17:00",
        "temp": "15.7°C",
        "app_temp": "13.1°C",
        "rain_prob": "10%",
        "rain_mm": "0.0 mm",
        "wind": "6.6 km/h",
        "gusts": "27.0 km/h"
      },
      {
        "time": "18:00",
        "temp": "14.7°C",
        "app_temp": "13.1°C",
        "rain_prob": "13%",
        "rain_mm": "0.0 mm",
        "wind": "1.8 km/h",
        "gusts": "22.3 km/h"
      },
      {
        "time": "19:00",
        "temp": "14.0°C",
        "app_temp": "12.4°C",
        "rain_prob": "30%",
        "rain_mm": "0.0 mm",
        "wind": "2.5 km/h",
        "gusts": "15.1 km/h"
      },
      {
        "time": "20:00",
        "temp": "13.2°C",
        "app_temp": "11.1°C",
        "rain_prob": "15%",
        "rain_mm": "0.0 mm",
        "wind": "4.8 km/h",
        "gusts": "22.7 km/h"
      },
      {
        "time": "21:00",
        "temp": "12.8°C",
        "app_temp": "10.5°C",
        "rain_prob": "18%",
        "rain_mm": "0.2 mm",
        "wind": "6.3 km/h",
        "gusts": "28.8 km/h"
      },
      {
        "time": "22:00",
        "temp": "12.5°C",
        "app_temp": "10.4°C",
        "rain_prob": "33%",
        "rain_mm": "0.0 mm",
        "wind": "6.5 km/h",
        "gusts": "15.8 km/h"
      },
      {
        "time": "23:00",
        "temp": "12.0°C",
        "app_temp": "10.4°C",
        "rain_prob": "40%",
        "rain_mm": "0.0 mm",
        "wind": "4.9 km/h",
        "gusts": "18.4 km/h"
      }
    ],
    "mud_risk": {
      "status": "Success",
      "metadata": {
        "target_date": "2026-04-29T14:07:33.664740+00:00",
        "is_predictive": false,
        "model_version": "TAEL® v3.1"
      },
      "environmental_context": {
        "total_rain_72h_mm": 0,
        "integrated_pet_hours": 30,
        "reservoir_moisture_mm": 0
      },
      "tactical_analysis": {
        "surface_type": "Unknown",
        "traction_risk": {
          "level": "Low",
          "advice": "Maximum grip. Surface is hardpack and fast."
        },
        "trail_damage_risk": {
          "level": "Low",
          "advice": "Trail structure is solid. No rutting expected."
        },
        "dry_time_eta": "Ready Now"
      }
    },
    "max_temp_detected": "19.1°C",
    "safety_advice": {
      "status": "🟢 [GO]",
      "message": "Ideal conditions: Low wind, dry, and safe.",
      "wind_risk_score": 27,
      "gear_advice": "Standard (Short sleeves, summer bibs, light base layer)"
    }
  },
  "logistics": {
    "nutrition_plan": {
      "status": "Success",
      "mission_nutrition_briefing": {
        "fluids": {
          "total_liters": 6.6,
          "hourly_rate_ml": 678
        },
        "carbohydrates": {
          "total_grams": 880,
          "hourly_target_g": 90,
          "recommended_ratio": "2:1 Glucose-to-Fructose (or 1:0.8 ratio)",
          "intensity_context": "Tempo"
        },
        "electrolytes": {
          "total_sodium_mg": 5304,
          "hourly_sodium_mg": 542
        },
        "tactical_advice": [
          "FUELING ALERT: High target (90g/hr). Use a 2:1 Glucose-to-Fructose (or 1:0.8 ratio) mix to prevent GI distress. Gut training required.",
          "BONK RISK: High intensity over prolonged duration. Missing a single feeding window will cause catastrophic glycogen depletion."
        ]
      }
    },
    "nearby_amenities": [
      {
        "name": "Water Fountain 💧",
        "type": "Water Fountain 💧",
        "distance_m": 1072,
        "location": {
          "lat": 41.761793,
          "lon": 12.709082
        }
      },
      {
        "name": "Water Fountain 💧",
        "type": "Water Fountain 💧",
        "distance_m": 1101,
        "location": {
          "lat": 41.760723,
          "lon": 12.703403
        }
      },
      {
        "name": "Water Fountain 💧",
        "type": "Water Fountain 💧",
        "distance_m": 1108,
        "location": {
          "lat": 41.76081,
          "lon": 12.703437
        }
      },
      {
        "name": "Water Fountain 💧",
        "type": "Water Fountain 💧",
        "distance_m": 1110,
        "location": {
          "lat": 41.760813,
          "lon": 12.703393
        }
      },
      {
        "name": "Water Fountain 💧",
        "type": "Water Fountain 💧",
        "distance_m": 1142,
        "location": {
          "lat": 41.761132,
          "lon": 12.703355
        }
      }
    ]
  },
  "map_path": "/home/test/.bikescout/gpx/tactical_map_fec080_1777471655.png",
  "mcp_resource_uri_map": "bikescout://maps/tactical_map_fec080_1777471655.png",
  "gpx_export_path": "/home/test/.bikescout/gpx/tactical_route_fec080.gpx",
  "mcp_resource_uri_gpx": "bikescout://gpx/tactical_route_fec080.gpx",
  "gpx_stats": {
    "total_points": 856,
    "healed_points": 856,
    "waypoints_count": 15
  },
  "elevation_profile_path": "/home/test/.bikescout/altimetry/bs_altimetry_fec080.png",
  "mcp_resource_uri_elevation_profile": "bikescout://altimetry/bs_altimetry_fec080.png"
}
```

---

### `check_trail_weather`
A real-time safety tool designed specifically for outdoor activities. It provides a localized 4-hour window forecast.

#### **Functionality:**
* **Hyper-local Forecast:** Uses precise coordinates to fetch data from the Open-Meteo API.
* **Cycling-Specific Metrics:** Focuses on precipitation probability, temperature, and wind speed.
* **Smart Advice:** Automatically evaluates conditions and provides a "Go/No-Go" suggestion.

#### **Parameters:**
| Parameter | Type     | Default | Description                                         |
| :--- |:---------| :--- |:----------------------------------------------------|
| `lat` | `float`  | Required | Latitude of the trail or starting point.            |
| `lon` | `float`  | Required | Longitude of the trail or starting point.           |
| `target_date` | `string` |  | target_date: Optional string in 'YYYY-MM-DD' format |

**Example Output (JSON):**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "metadata": {
    "date_analyzed": "2026-07-14",
    "is_future_planning": true,
    "location": {
      "lat": 45.9237,
      "lon": 6.8694
    }
  },
  "tactical_forecast": [
    {
      "time": "08:00",
      "temp": "14.2°C",
      "rain_prob": "0%",
      "wind": "5.4 km/h"
    },
    {
      "time": "10:00",
      "temp": "18.5°C",
      "rain_prob": "5%",
      "wind": "8.2 km/h"
    },
    {
      "time": "12:00",
      "temp": "22.1°C",
      "rain_prob": "15%",
      "wind": "12.5 km/h"
    },
    {
      "time": "14:00",
      "temp": "24.8°C",
      "rain_prob": "40%",
      "wind": "18.1 km/h"
    },
    {
      "time": "16:00",
      "temp": "21.3°C",
      "rain_prob": "65%",
      "wind": "15.3 km/h"
    }
  ],
  "reference_conditions": {
    "temp": 14.2,
    "rain_prob": 0,
    "wind_speed": 5.4,
    "reference_hour": "8:00"
  },
  "safety_advice": {
    "risk_level": "Moderate",
    "recommendations": {
      "clothing": "Start with a light gilet; temperatures will rise rapidly.",
      "tires": "Standard pressure, but be wary of wet tarmac after 14:00.",
      "hydration": "High sweat rate expected midday. 750ml/hour recommended."
    },
    "alerts": [
      "Thunderstorm risk in the afternoon (65% probability after 15:00)."
    ]
  }
}
```

---

### `ride_window_planner`
The ultimate **Decision Intelligence** tool for the modern rider. It goes beyond simple weather reporting by calculating the optimal "Strategic Window" to deploy. It cross-references atmospheric stability with the **TAEL® (Terrain-Aware Evaporation Lag)** index to determine exactly when the terrain will be at its peak performance.

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
| `surface_type` | `str` | `"dirt"` | Used to calculate specific soil drainage coefficients for the TAEL® index. |
| `target_date` | `string` |  | target_date: Optional string in 'YYYY-MM-DD' format |


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

---

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
* **TAEL® (Terrain-Aware Evaporation Lag):** A tactical model that cross-references 72h rainfall and geological drainage with real-time solar altitude to predict trail saturation and "Shadow-Lock" mud persistence.
* **E-MTB Power Predictor:** A physics-based energy model that predicts battery drain by cross-referencing Total System Weight, Assist Mode, Surface Drag, and Mud Suction effects.

#### **Parameters:**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | Latitude of the starting point. |
| `lon` | `float` | Required | Longitude of the starting point. |
| **`rider`** | `object` | Required | [Rider Profile](#rider-profile-rider).                  |
| **`bike`** | `object` | Required | [Bike Setup](#bike-setup-bike).                         |
| **`mission`** | `object` | Required | [Mission Constraints](#mission-constraints-mission).    |
| `target_date` | `string` |  | target_date: Optional string in 'YYYY-MM-DD' format |


**Example Output (JSON) for MTB:**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "profile_used": "cycling-mountain",
  "metadata": {
    "analyzed_date": "2026-04-28T12:57:43.244647+00:00",
    "api_extras": [
      "waytype",
      "surface"
    ]
  },
  "tactical_briefing": {
    "distance_km": 38.19,
    "elevation_gain_m": 1367,
    "climb_category": "Hors Catégorie (HC) - Legendary Challenge",
    "avg_gradient_est": "11.9%",
    "mud_intelligence": {
      "score": 0,
      "label": "Unknown",
      "traction_risk": "Low",
      "trail_damage_risk": "Low",
      "dry_time_eta": "Ready Now",
      "safety_advice": "Check local conditions."
    }
  },
  "mechanical_setup": {
    "compatible": true,
    "setup_details": "29 wheels | 22.0 PSI (1.52 Bar) [Standard Setup]",
    "bike_type": "mtb"
  },
  "surface_breakdown": [
    {
      "type": "Unknown",
      "percentage": "50.3%"
    },
    {
      "type": "Paved",
      "percentage": "35.8%"
    },
    {
      "type": "Grass",
      "percentage": "6.6%"
    },
    {
      "type": "Asphalt",
      "percentage": "2.7%"
    },
    {
      "type": "Concrete",
      "percentage": "1.7%"
    },
    {
      "type": "Other",
      "percentage": "1.5%"
    },
    {
      "type": "Other",
      "percentage": "0.8%"
    },
    {
      "type": "Unpaved",
      "percentage": "0.7%"
    }
  ],
  "emtb_tactical": null,
  "safety_warnings": []
}
```

**Example Output (JSON) for Road:**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "profile_used": "cycling-road",
  "metadata": {
    "analyzed_date": "2026-04-28T12:58:33.209965+00:00",
    "api_extras": [
      "waytype",
      "surface"
    ]
  },
  "tactical_briefing": {
    "distance_km": 109.29,
    "elevation_gain_m": 1254,
    "climb_category": "Hors Catégorie (HC) - Legendary Challenge",
    "avg_gradient_est": "2.5%",
    "mud_intelligence": {
      "score": 0,
      "label": "Unknown",
      "traction_risk": "Low",
      "trail_damage_risk": "Low",
      "dry_time_eta": "Ready Now",
      "safety_advice": "Check local conditions."
    }
  },
  "mechanical_setup": {
    "compatible": true,
    "setup_details": "700c wheels | 86.0 PSI (5.93 Bar) [Efficiency Setup]",
    "bike_type": "Road"
  },
  "surface_breakdown": [
    {
      "type": "Paved",
      "percentage": "67.4%"
    },
    {
      "type": "Unknown",
      "percentage": "29.1%"
    },
    {
      "type": "Asphalt",
      "percentage": "2.7%"
    },
    {
      "type": "Concrete",
      "percentage": "0.4%"
    },
    {
      "type": "Grass",
      "percentage": "0.3%"
    },
    {
      "type": "Other",
      "percentage": "0.1%"
    }
  ],
  "emtb_tactical": null,
  "safety_warnings": [
    "Traction Alert: 0.3% is Grass. 25mm tires may slip in wet/loose conditions."
  ]
}
```

**Example Output (JSON) for E-Bike:**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "profile_used": "cycling-electric",
  "metadata": {
    "analyzed_date": "2026-04-28T12:59:43.240941+00:00",
    "api_extras": [
      "waytype",
      "surface"
    ]
  },
  "tactical_briefing": {
    "distance_km": 79.74,
    "elevation_gain_m": 1137,
    "climb_category": "Hors Catégorie (HC) - Legendary Challenge",
    "avg_gradient_est": "3.2%",
    "mud_intelligence": {
      "score": 0,
      "label": "Unknown",
      "traction_risk": "Low",
      "trail_damage_risk": "Low",
      "dry_time_eta": "Ready Now",
      "safety_advice": "Check local conditions."
    }
  },
  "mechanical_setup": {
    "compatible": true,
    "setup_details": "29 wheels | 24.0 PSI (1.65 Bar) [Standard Setup]",
    "bike_type": "E-MTB"
  },
  "surface_breakdown": [
    {
      "type": "Unknown",
      "percentage": "56.9%"
    },
    {
      "type": "Paved",
      "percentage": "38.0%"
    },
    {
      "type": "Asphalt",
      "percentage": "3.4%"
    },
    {
      "type": "Other",
      "percentage": "0.9%"
    },
    {
      "type": "Concrete",
      "percentage": "0.4%"
    },
    {
      "type": "Unpaved",
      "percentage": "0.2%"
    },
    {
      "type": "Grass",
      "percentage": "0.1%"
    }
  ],
  "emtb_tactical": {
    "status": "Success",
    "battery_metrics": {
      "estimated_drain_wh": 190.3,
      "remaining_battery_pct": 62.5,
      "safety_buffer_status": "SAFE",
      "usable_wh_at_temp": 581.2
    },
    "power_breakdown_w": {
      "gravity_resistance": 69.2,
      "rolling_resistance": 72.8,
      "aerodynamic_drag": 34.5,
      "rider_contribution": 140,
      "motor_net_output": 36.5
    },
    "tactical_advice": "Pace maintained"
  },
  "safety_warnings": []
}
```

---

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

---

### `check_trail_soil_condition`
A predictive safety tool that cross-references geological surface data with historical precipitation to estimate trail rideability and mud levels.

#### **Functionality:**
* **Rain History Audit:** Automatically fetches cumulative rainfall from the last 72 hours using the Open-Meteo Archive API.
* **Geological Sensitivity:** Differentiates how rain affects various terrains, calculating saturation levels for surfaces like clay, dirt, sand, and gravel.
* **Mud Risk Score:** Provides a localized risk rating (Low/Medium/High) to help cyclists prevent drivetrain damage and avoid unrideable sections.
* **TAEL® v3.1 (Terrain-Aware Evaporation Lag)**: A high-fidelity reservoir model that replaces static daily sums with an hourly recursive engine ($M_t = M_{t-1} \cdot e^{-k \cdot D_t} + R_t$), integrating time-step rainfall, non-linear clay drainage physics, and cumulative solar energy to predict traction risks and provide a precise "Dry-Time" ETA.

#### **Parameters:**
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | Latitude of the trail section. |
| `lon` | `float` | Required | Longitude of the trail section. |
| `surface_type` | `string` | `dirt` | The OSM surface tag (e.g., `clay`, `sand`, `gravel`, `asphalt`). |
| `target_date` | `string` |  | target_date: Optional string in 'YYYY-MM-DD' format |

#### **Example Output (JSON):**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "metadata": {
    "target_date": "2026-04-27T22:25:05.786299+00:00",
    "is_predictive": false,
    "model_version": "TAEL® v3.1"
  },
  "environmental_context": {
    "total_rain_72h_mm": 0,
    "integrated_pet_hours": 30,
    "reservoir_moisture_mm": 0
  },
  "tactical_analysis": {
    "surface_type": "dirt",
    "traction_risk": {
      "level": "Low",
      "advice": "Maximum grip. Surface is hardpack and fast."
    },
    "trail_damage_risk": {
      "level": "Low",
      "advice": "Trail structure is solid. No rutting expected."
    },
    "dry_time_eta": "Ready Now"
  }
}
```

---

### `elevation_profile_image`
Generates a high-resolution visual analysis of the route's elevation profile. Unlike simple line charts, this tool produces a tactical graphical representation that integrates color-coded slope data, allowing for an immediate assessment of vertical difficulties.

#### **Functionality:**
* **Visual Slope Gradient:** Applies a dynamic chromatic scale (Green → Yellow → Red → Black) to instantly highlight critical steepness (over 10-15%).
* **SRTM Data Processing:** Processes 3D coordinates (Longitude, Latitude, Elevation) to reconstruct the terrain profile with high precision.
* **Automated Scaling**: Automatically adjusts the chart axes based on total elevation gain to ensure maximum readability for both flat valley floors and alpine passes.
* **Terrain-Sync Validation**: Uses RouteGeometry logic to validate and sanitize elevation data, eliminating "spikes" common in raw satellite data.
* **Tactical Overview**: Provides a crucial "at-a-glance" briefing for energy management (pacing) and gear selection before starting the ride.

#### **Parameters:**

| Parameter  | Type     | Default      | Description                                        |
|:-----------|:---------|:-------------|:---------------------------------------------------|
| `geometry` | `object` | **Required** | [Route Geometry](#route-geometry-geometry).        |
| `width`    | `int`    | 8            | Width of the generated image (matplotlib inches).  |
| `height`   | `int`    | 3            | Height of the generated image (matplotlib inches). |
| `style`    | `string` | `filled`      | Visual style of the profile, "sparkline", "filled", "bars"|                     |


#### **Example Output (JSON):**

```json
{
  "status": "Success",
  "message": "Elevation profile stored in BikeScout home directory.",
  "mcp_resource_uri": "bikescout://altimetry/climb.png",
  "file_location": "/home/.test/bikescout/altimetry/climb.png",
  "style_applied": "sparkline",
  "dimensions": "8x3 in",
  "instructions": "The file is safe in your home directory: /home/.test/bikescout/altimetry/climb.png"
}
```

Example image generated:

![Example image generated:](site/md/elevation_profile.png)

---

### `analyze_gpx_track`
A professional-grade performance engine for high-fidelity race track auditing. It simulates World Tour conditions by cross-referencing topographic data with professional physical constraints and real-time environmental factors.

#### **Functionality:**
* **UCI Categorization:** Automatically identifies and grades climbs from Category 4 up to **HC (Hors Catégorie)** based on length, gain, and average gradient.
* **Adaptive Surface Filtering:** Features a specialized "Road vs MTB" switch that adjusts jitter filtering and gradient caps to eliminate GPS artifacts and sensor noise.
* **Performance Simulation:** Calculates required Power (Watts), Power-to-Weight ratio (**$W/kg$**), and **VAM** (Vertical Ascent Meters/hour) for every major climb.
* **Tactical Insights:** Detects "Muros" (steep road walls) and identifies potential echelon risks by analyzing wind vectors relative to the track heading.
* **Pro Strategy Report (PDF):** Generates a comprehensive, data-driven dossier featuring reasoned tactical briefings and prioritized sector analysis tailored for professional riders and staff.

#### **Parameters:**

| Parameter         | Type     | Default | Description                                                                                |
|:------------------|:---------| :--- |:-------------------------------------------------------------------------------------------|
| `gpx_url`         | `string` | Required | Remote URL or local path of the GPX file to analyze.                                       |
| `rider_weight_kg` | `float`  | Required | Body mass of the rider for Power-to-Weight calculations.                                   |
| `bike_weight_kg`  | `float`  | `7.5` | Mass of the bike (default is for pro road bikes).                                          |
| `pro_intensity`   | `float`  | `1.6` | Effort multiplier (**1.0** = amateur, **1.6** = pro pace, **2.0** = attack).               |
| `activity_type`   | `string` | `"road"` | Activty type: `"road"` or `"mtb"` (affects noise filtering).                               |
| `target_date`     | `string` | | Optional race date (YYYY-MM-DD). If provided, fetches historical or forecast weather.      |
| `start_hour`      | `int`    |  | Expected start time (0-23). If provided with end_hour, calculates window-averaged metrics. |
| `end_hour`        | `int`    |  | Expected end time (0-23). If provided with end_hour, calculates window-averaged metrics.   |

**Example Output (JSON):**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "mode": "ROAD",
  "target_date": "2026-04-26",
  "track_metrics": {
    "distance_km": 155.29,
    "total_ascent": 2245.6,
    "max_altitude": 1136
  },
  "planning_tools": {
    "weather_forecast": {
      "status": "Success",
      "metadata": {
        "date_analyzed": "2026-04-26",
        "is_future_planning": true,
        "location": {
          "lat": 45.25411,
          "lon": 7.65618
        },
        "data_points": 24
      },
      "tactical_forecast": [
        {
          "time": "09:00",
          "temp": "15.3°C",
          "rain_prob": "0%",
          "wind": "3.1 km/h"
        },
        {
          "time": "10:00",
          "temp": "17.7°C",
          "rain_prob": "0%",
          "wind": "2.5 km/h"
        },
        {
          "time": "11:00",
          "temp": "19.8°C",
          "rain_prob": "0%",
          "wind": "3.1 km/h"
        },
        {
          "time": "12:00",
          "temp": "21.4°C",
          "rain_prob": "0%",
          "wind": "3.9 km/h"
        },
        {
          "time": "13:00",
          "temp": "22.7°C",
          "rain_prob": "0%",
          "wind": "5.8 km/h"
        },
        {
          "time": "14:00",
          "temp": "23.3°C",
          "rain_prob": "0%",
          "wind": "6.1 km/h"
        },
        {
          "time": "15:00",
          "temp": "23.9°C",
          "rain_prob": "0%",
          "wind": "6.5 km/h"
        },
        {
          "time": "16:00",
          "temp": "24.5°C",
          "rain_prob": "0%",
          "wind": "6.3 km/h"
        },
        {
          "time": "17:00",
          "temp": "24.7°C",
          "rain_prob": "0%",
          "wind": "8.3 km/h"
        }
      ],
      "reference_conditions": {
        "temp": 21.9,
        "rain_prob": 0,
        "wind_speed": 4.9,
        "reference_hour": "Average 10-16"
      },
      "safety_advice": "🌥️ CHILLY: Light jacket or arm warmers recommended."
    },
    "nutrition_plan": {
      "status": "Success",
      "mission_nutrition_briefing": {
        "fluids": {
          "total_liters": 4.7,
          "hourly_rate_ml": 700
        },
        "carbohydrates": {
          "total_grams": 535,
          "hourly_target_g": 80,
          "intensity_context": "High"
        },
        "tactical_advice": [
          "ELECTROLYTE CRITICAL: High sweat rate or duration detected. Add sodium to bottles.",
          "FUELING ALERT: High intensity detected. Train your gut for 80g+/hr intake."
        ]
      }
    },
    "mud_risk": null
  },
  "climb_analysis": [
    {
      "km_start": 0,
      "dist_km": 1.44,
      "gain_m": 143.2,
      "avg_grade": 9.9,
      "category": "Cat 3"
    },
    {
      "km_start": 36.5,
      "dist_km": 2.29,
      "gain_m": 58.8,
      "avg_grade": 2.6,
      "category": "Cat 4"
    },
    {
      "km_start": 77,
      "dist_km": 17.06,
      "gain_m": 286,
      "avg_grade": 1.7,
      "category": "Cat 3"
    },
    {
      "km_start": 96.6,
      "dist_km": 4.33,
      "gain_m": 184.8,
      "avg_grade": 4.3,
      "category": "Cat 3"
    },
    {
      "km_start": 107.9,
      "dist_km": 8.36,
      "gain_m": 337,
      "avg_grade": 4,
      "category": "Cat 3"
    },
    {
      "km_start": 123.8,
      "dist_km": 8.2,
      "gain_m": 234,
      "avg_grade": 2.9,
      "category": "Cat 3"
    },
    {
      "km_start": 140.7,
      "dist_km": 14.25,
      "gain_m": 716.4,
      "avg_grade": 5,
      "category": "Cat 1"
    }
  ],
  "performance_simulation": [
    {
      "climb": "Climb @ km 0.0",
      "category": "Cat 3",
      "base_wkg": 5.29,
      "weather_adjusted_wkg": 5.29
    },
    {
      "climb": "Climb @ km 36.5",
      "category": "Cat 4",
      "base_wkg": 5.29,
      "weather_adjusted_wkg": 5.29
    },
    {
      "climb": "Climb @ km 77.0",
      "category": "Cat 3",
      "base_wkg": 5.29,
      "weather_adjusted_wkg": 5.29
    },
    {
      "climb": "Climb @ km 96.6",
      "category": "Cat 3",
      "base_wkg": 5.29,
      "weather_adjusted_wkg": 5.29
    },
    {
      "climb": "Climb @ km 107.9",
      "category": "Cat 3",
      "base_wkg": 5.29,
      "weather_adjusted_wkg": 5.29
    },
    {
      "climb": "Climb @ km 123.8",
      "category": "Cat 3",
      "base_wkg": 5.29,
      "weather_adjusted_wkg": 5.29
    },
    {
      "climb": "Climb @ km 140.7",
      "category": "Cat 1",
      "base_wkg": 6.5,
      "weather_adjusted_wkg": 6.5
    }
  ],
  "tactical_alerts": [],
  "explosivity_zones": [
    {
      "km": 0,
      "grade": 28,
      "type": "Steep Road Wall"
    },
    {
      "km": 0.07,
      "grade": 28,
      "type": "Steep Road Wall"
    },
    {
      "km": 97.89,
      "grade": 25.6,
      "type": "Steep Road Wall"
    },
    {
      "km": 111.47,
      "grade": 18.5,
      "type": "Steep Road Wall"
    },
    {
      "km": 111.5,
      "grade": 23.9,
      "type": "Steep Road Wall"
    },
    {
      "km": 111.52,
      "grade": 22.3,
      "type": "Steep Road Wall"
    },
    {
      "km": 128.1,
      "grade": 23,
      "type": "Steep Road Wall"
    },
    {
      "km": 128.55,
      "grade": 28,
      "type": "Steep Road Wall"
    },
    {
      "km": 129.06,
      "grade": 25.4,
      "type": "Steep Road Wall"
    },
    {
      "km": 129.1,
      "grade": 26.6,
      "type": "Steep Road Wall"
    }
  ]
}
```

---

### `hydration_scout`
The **Physiological Intelligence Engine** of BikeScout. This tool translates environmental and mission data into a concrete fueling strategy, preventing dehydration and "bonking" (hypoglycemia) by bridging the gap between terrain data and human physiology.

#### **Functionality:**
* **Continuous Sweat Rate Modeling**: Replaces rigid step-functions with a linear regression model. It calculates fluid loss by integrating a 300ml/hr base rate, a thermal coefficient (+30ml per 1°C above 15°C), and metabolic heat generated by the Intensity Factor.
* **Metabolic Scaling (Intensity Factor)**: Corrects previous scaling bugs by mapping the 1-5 score to a standardized Intensity Factor (0.60 to 1.05). This ensures a realistic variance in fuel demand between recovery rides and high-threshold race missions.
* **Dynamic Carbohydrate Optimization**: Predicts glycogen depletion to target replenishment rates from 40g up to 120g/hr. The system automatically recommends a 2:1 Glucose-to-Fructose ratio for targets exceeding 60g/hr to optimize gut absorption and prevent GI distress.
* **Precision Electrolyte Estimation**: Moves beyond generic warnings to provide a calculated Sodium Target (mg/hr). It correlates sodium loss to estimated sweat volume at a physiological rate of 800mg/L, providing specific dosage instructions for bottles.
* **Predictive "Bonk" & Heat Alerts**: Tactical triggers detect high-risk scenarios, such as Thermoregulatory Strain (Temp > 28°C) or Sub-Surface Depletion (High Intensity + Duration > 2.5h), issuing critical mission-saving briefings.
#### **Parameters:**

| Parameter | Type | Default      | Description                                                                                         |
| :--- | :--- |:-------------|:----------------------------------------------------------------------------------------------------|
| `lat` | `float` | **Required** | Latitude of the mission area for weather correlation.                                               |
| `lon` | `float` | **Required** | Longitude of the mission area for weather correlation.                                              |
| `duration_hours` | `float` | **Required** | Total estimated time in the saddle.                                                                 |
| `intensity_score` | `int` | `3`          | Physiological effort (1-5). Agent should scale this based on climb categories.                      |
| `target_date` | `string` |              | target_date: Optional string in 'YYYY-MM-DD' format                                                 |

#### **Tool Output Example (JSON):**
```json
{
  "payload_version": "1.0",
  "weather_context": {
    "date_referenced": "2026-04-28",
    "max_temp_detected": "18.3°C",
    "is_future_event": false
  },
  "status": "Success",
  "mission_nutrition_briefing": {
    "fluids": {
      "total_liters": 3.1,
      "hourly_rate_ml": 624
    },
    "carbohydrates": {
      "total_grams": 200,
      "hourly_target_g": 40,
      "recommended_ratio": "Standard isotonic or whole foods",
      "intensity_context": "Endurance / Recovery"
    },
    "electrolytes": {
      "total_sodium_mg": 2496,
      "hourly_sodium_mg": 499
    },
    "tactical_advice": []
  }
}
```
---
