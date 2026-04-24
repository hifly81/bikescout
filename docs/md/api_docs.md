# BikeScout Documentation

Tactical Cycling Intelligence | MCP Server for AI-Powered Mission Planning.

_Version: 1.1.2 - April 2026_

---

## Key Features

### 🏔️ Terrain & Surface Intelligence
- **Real Trail Discovery**: Fetches actual trail names and surface data directly from OpenStreetMap (via Overpass API).
- **Surface Breakdown**: Generates a detailed percentage breakdown of the entire route (asphalt, gravel, dirt, etc.).
- **Technical Grading**: Analyzes OSM Tracktypes (Grade 1-5) to distinguish between smooth fire roads and rugged, technical MTB paths.
- **Bike Compatibility Check**: A first-of-its-kind feature that validates if a route suits your specific bike (Road, Gravel, MTB) and tire width, issuing instant safety warnings.

### ⛈️ Predictive Environmental Modeling
- **TAEL Algorithm**: Our flagship **Terrain-Aware Evaporation Lag** model that predicts "Shadow-Lock" mud on north-facing slopes by analyzing real-time solar altitude and soil memory.
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
- **Post-Ride Analysis**: Fuses Strava activity logs with environmental intelligence to analyze how mud and weather conditions impacted your actual performance.

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

### 🌧️ Ground Memory & TAEL Logic
Standard forecasts only tell you if it *might* rain. BikeScout analyzes what *actually* happened to the soil.
* **Generic Maps:** Provide only current atmospheric snapshots.
* **BikeScout:** Uses the **TAEL (Terrain-Aware Evaporation Lag)** index. By cross-referencing 72h precipitation history with soil geology (Clay vs. Sand) and solar altitude, it predicts where "Shadow-Lock" mud persists even on sunny days.

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
| Field | Type | Default | Description |
| :--- | :--- |:--------| :--- |
| `bike_type` | `string` |         | Geometry profile. Options: `Road`, `Gravel`, `MTB`, `Enduro`. |
| `tire_size` | `string` |         | Diameter/Standard. Options: `26`, `27.5`, `29`, `700c`, `650b`. |
| `is_ebike` | `bool` | `false` | If true, triggers battery consumption and motor-assist logic. |
| `battery_wh` | `int` |         | Battery capacity in Watt-hours (required if `is_ebike` is true). |

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

---

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
| Parameter | Type | Default | Description                                          |
| :--- | :--- | :--- |:-----------------------------------------------------|
| `lat` | `float` | Required | Latitude of the starting point (e.g., `45.81`).      |
| `lon` | `float` | Required | Longitude of the starting point (e.g., `9.08`).      |
| **`rider`** | `object` | Required | [Rider Profile](#rider-profile-rider).               |
| **`bike`** | `object` | Required | [Bike Setup](#bike-setup-bike).                      |
| **`mission`** | `object` | Required | [Mission Constraints](#mission-constraints-mission). |
| `include_gpx` | `bool` | `True` | Whether to include the raw XML GPX content.          |
| `include_map` | `bool` | `False` | Whether to generate the Static Map URL.              |
| `output_level` | `string` | `standard` | Verbosity level: `summary`, `standard`, or `full`.   |
| `target_date` | `string` |  | target_date: Optional string in 'YYYY-MM-DD' format  |


#### **Tool Output Example (JSON):**
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
  "map_image_url": "/home/test/.bikescout/gpx/tactical_route_3c3c37.png",
  "gpx_export_path": "/home/test/.bikescout/gpx/tactical_route_3c3c37.gpx",
  "gpx_stats": {
    "total_points": 945,
    "healed_points": 945,
    "waypoints_count": 11
  },
  "elevation_profile_path": "/home/test/.bikescout/altimetry/bs_altimetry_3c3c37.png",
  "elevation_summary": "Visual sparkline generated and cached."
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
| `target_date` | `string` |  | target_date: Optional string in 'YYYY-MM-DD' format |


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
* **TAEL (Terrain-Aware Evaporation Lag):** A tactical model that cross-references 72h rainfall and geological drainage with real-time solar altitude to predict trail saturation and "Shadow-Lock" mud persistence.

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
  "status": "Success",
  "metadata": {
    "target_date": "2026-05-10",
    "is_predictive": true
  },
  "environmental_context": {
    "cumulative_rain_72h": "18.5mm",
    "avg_temp": "14.2°C",
    "drying_efficiency": "0.65x",
    "shadow_penalty_active": "Yes",
    "solar_altitude": "58.4°"
  },
  "tactical_analysis": {
    "adjusted_moisture_index": 28.46,
    "mud_risk_score": "High",
    "mud_risk_numeric": 34.2,
    "surface_type": "clay",
    "safety_advice": "Significant saturation. High risk of sliding in technical sectors. Heavy clay sticking likely to affect drivetrain and tire clearance."
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
* **Base64 Visual Delivery**: Returns the image as a Base64 string (Data URI), enabling immediate integration into chat interfaces, PDF reports, or web dashboards without external hosting.
* **Terrain-Sync Validation**: Uses RouteGeometry logic to validate and sanitize elevation data, eliminating "spikes" common in raw satellite data.
* **Tactical Overview**: Provides a crucial "at-a-glance" briefing for energy management (pacing) and gear selection before starting the ride.

#### **Parameters:**

| Parameter  | Type     | Default            | Description                                        |
|:-----------|:---------|:-------------------|:---------------------------------------------------|
| `geometry` | `object` | **Required**       | [Route Geometry](#route-geometry-geometry).        |
| `width`    | `int`    | 8                  | Width of the generated image (matplotlib inches).  |
| `height`   | `int`    | 3                  | Height of the generated image (matplotlib inches). |
| `style`    | `string` | sparkline          | Visual style of the profile, "sparkline", "filled", "bars"|                     |


#### **Example Output (JSON):**

```json
{
  "status": "Success",
  "message": "Elevation profile stored in BikeScout home directory.",
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

#### **Parameters:**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `gpx_url` | `string` | Required | Remote URL or local path of the GPX file to analyze. |
| `rider_weight_kg` | `float` | Required | Body mass of the rider for Power-to-Weight calculations. |
| `bike_weight_kg` | `float` | `7.5` | Mass of the bike (default is for pro road bikes). |
| `pro_intensity` | `float` | `1.6` | Effort multiplier (**1.0** = amateur, **1.6** = pro pace, **2.0** = attack). |
| `surface_type` | `string` | `"road"` | Terrain mode: `"road"` or `"mtb"` (affects noise filtering). |

**Example Output (JSON):**
```json
{
  "payload_version": "1.0",
  "status": "Success",
  "mode": "ROAD",
  "track_metrics": {
    "distance_km": 155.29,
    "total_ascent": 2245.6,
    "max_altitude": 1136
  },
  "climb_analysis": [
    {
      "km_start": 79.8,
      "dist_km": 1.6,
      "gain_m": 112,
      "avg_grade": 7,
      "category": "Cat 3"
    },
    {
      "km_start": 83.1,
      "dist_km": 2.27,
      "gain_m": 161,
      "avg_grade": 7.1,
      "category": "Cat 3"
    },
    {
      "km_start": 92.9,
      "dist_km": 3.58,
      "gain_m": 296.8,
      "avg_grade": 8.3,
      "category": "Cat 2"
    },
    {
      "km_start": 102,
      "dist_km": 1.42,
      "gain_m": 221.2,
      "avg_grade": 15.6,
      "category": "Cat 2"
    },
    {
      "km_start": 112.2,
      "dist_km": 1.61,
      "gain_m": 118,
      "avg_grade": 7.3,
      "category": "Cat 3"
    },
    {
      "km_start": 114.1,
      "dist_km": 3.53,
      "gain_m": 535.4,
      "avg_grade": 15.2,
      "category": "HC"
    }
  ],
  "performance_simulation": [
    {
      "climb": "Climb @ km 79.8",
      "category": "Cat 3",
      "target_vam": 1100,
      "power_required_watts": 381.2,
      "watts_per_kg": 5.29
    },
    {
      "climb": "Climb @ km 83.1",
      "category": "Cat 3",
      "target_vam": 1100,
      "power_required_watts": 381.2,
      "watts_per_kg": 5.29
    },
    {
      "climb": "Climb @ km 92.9",
      "category": "Cat 2",
      "target_vam": 1100,
      "power_required_watts": 381.2,
      "watts_per_kg": 5.29
    },
    {
      "climb": "Climb @ km 102.0",
      "category": "Cat 2",
      "target_vam": 1100,
      "power_required_watts": 381.2,
      "watts_per_kg": 5.29
    },
    {
      "climb": "Climb @ km 112.2",
      "category": "Cat 3",
      "target_vam": 1100,
      "power_required_watts": 381.2,
      "watts_per_kg": 5.29
    },
    {
      "climb": "Climb @ km 114.1",
      "category": "HC",
      "target_vam": 1550,
      "power_required_watts": 537.1,
      "watts_per_kg": 7.46
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
      "km": 117.08,
      "grade": 18.9,
      "type": "Steep Road Wall"
    }
  ]
}
```

---

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
    "date": "2026-03-11",
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

### `hydration_scout`
The **Physiological Intelligence Engine** of BikeScout. This tool translates environmental and mission data into a concrete fueling strategy, preventing dehydration and "bonking" (hypoglycemia) by bridging the gap between terrain data and human physiology.

#### **Functionality:**
* **Dynamic Hydration Modeling:** Calculates sweat rates by cross-referencing real-time peak temperatures from the `check_trail_weather` module with planned mission duration.
* **Carbohydrate Strategy:** Predicts glycogen depletion and targets specific replenishment rates (**30g to 90g/hr**) based on the `intensity_score`.
* **Environmental Fusion:** Automatically adjusts the "Base Rate" of 500ml/hr by adding **100ml for every 5°C** above the 20°C threshold.
* **Safety Thresholds:** Triggers specific **Electrolyte & Sodium alerts** if temperatures exceed **28°C** or if the mission duration exceeds **3 hours**.

#### **Parameters:**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | **Required** | Latitude of the mission area for weather correlation. |
| `lon` | `float` | **Required** | Longitude of the mission area for weather correlation. |
| `duration_hours` | `float` | **Required** | Total estimated time in the saddle. |
| `intensity_score` | `int` | `50` | Physiological effort (0-100). Agent should scale this based on climb categories (e.g., HC climbs = 90). |
| `target_date` | `string` |  | target_date: Optional string in 'YYYY-MM-DD' format |

#### **Tool Output Example (JSON):**
```json
{
  "payload_version": "1.0",
  "weather_context": {
    "date_referenced": "2026-04-23",
    "max_temp_detected": "19.2°C",
    "is_future_event": false
  },
  "status": "Success",
  "mission_nutrition_briefing": {
    "fluids": {
      "total_liters": 1.1,
      "hourly_rate_ml": 575
    },
    "carbohydrates": {
      "total_grams": 120,
      "hourly_target_g": 60,
      "intensity_context": "Moderate"
    },
    "tactical_advice": []
  }
}
```
---
