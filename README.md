# BikeScout MCP Server

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Version](https://img.shields.io/badge/Version-0.7.3-green.svg)](https://github.com/hifly81/bikescout/releases)
![Python](https://img.shields.io/badge/python-3.10-blue.svg)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Downloads](https://pepy.tech/badge/global-chem)](https://pepy.tech/project/global-chem)

**BikeScout** is a specialized MCP (Model Context Protocol) server designed for cyclists and mountain bikers. It provides intelligent trail recommendations by combining real-world map data with advanced routing analysis.

## Key Features

* **Real Trail Discovery**: Fetches actual trail names and surface types from **OpenStreetMap** (via Overpass API).
* **Technical Metrics**: Calculates precise distance in kilometers and total elevation gain (ascent).
* **Difficulty & Technical Grading**: Evaluates trails as Beginner, Moderate, or Expert and analyzes **OSM Tracktypes** (Grade 1-5) to distinguish between smooth gravel and rugged MTB paths.
* **Dynamic Routing & Surface Analysis**: Generates suggested loops (round trips) with a detailed **Percentage Breakdown** of surface types (asphalt, gravel, dirt, etc.).
* **Bike Setup Compatibility**: A first-of-its-kind feature that checks if a route is suitable for your specific bike (**Road, Gravel, or MTB**) and **tire width**, providing instant safety warnings.
* **Smart Safety & Weather Forecast**: Cross-references location data with real-time weather to ensure you don't get caught in a storm.
* **Pro-Cycling Gear Advice**: Provides specific technical advice on clothing and gear based on temperature, wind, and rain thresholds.
* **Seamless Location Search**: No GPS coordinates required. Use natural language (e.g., *"Find a ride in Albano Laziale"*) via integrated Nominatim Geocoding.
* **Instant Map Previews**: Automatically generates a **Static Map (.png)** of the route to visualize the trail directly within the chat interface.
* **Local Expert Knowledge**: Specialized regional prompts for world-class destinations like the **Dolomites (UNESCO)**, **Moab (USA)**, and **Castelli Romani**.
* **Pro Climb Categorization**: Automatically identifies and names specific climbs (from **Category 4** to **Hors Catégorie**) using professional cycling standards based on length and average gradient.

## Prerequisites

- **Python 3.10+**
- **OpenRouteService API Key**: Get a free key at [openrouteservice.org](https://openrouteservice.org/).
- **MCP Client**: Such as Claude Desktop.

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
        "ORS_API_KEY": "YOUR_OPENROUTE_SERVICE_API_KEY"
      }
    }
  }
}
```

## Using BikeScout with VS Code (Linux/Windows/macOS)

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
            "ORS_API_KEY": "YOUR_OPENROUTE_SERVICE_API_KEY"
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

#### Route Highlights

- Starts and ends at Lake Albano
- Mix of paved roads (50.8%) and gravel/unknown surfaces (49.2%)
- Challenging climbs with rewarding views
- Scenic loops around the volcanic lake

#### 🍽️ Restaurant Recommendations

After your ride, refuel at these highly-rated spots near Lake Albano:

__Top Recommendations:__

1. __Ristorante Bucci__ - Upscale dining with lake views
2. __Al Porticciolo__ - Traditional Italian cuisine
3. __Terraces overlooking Lake Castel Gandolfo__ - Scenic dining experience
4. __Ricciotti Trattoria__ - Authentic Roman trattoria

> ✅ **Advice:** Perfect for riding! The route is challenging (856m of climbing over 11km) but offers great scenic views over the Colli Albani area.

#### 🚵‍♂️ BikeScout Terrain Analysis
The route composition is as follows:

* 🪨 **Gravel/Dirt:** 65% (Ideal for MTB or Gravel bikes)
* 🛣️ **Asphalt:** 25% (Connecting sections)
* 🌿 **Grass/Trail:** 10%

> 💡 **Technical Advice:** Given the high percentage of gravel and loose stones, we recommend using tires with a minimum width of **40mm** and slightly lower tire pressure to improve grip and comfort.

---

## AI Explorer Prompts

BikeScout includes pre-configured **AI Prompts**. These prompts provide local context, gear tips, and cultural insights.

| Prompt Name                     | Destination              | Specialization                                                               |
|:--------------------------------|:-------------------------|:-----------------------------------------------------------------------------|
| `explore-moab-usa`              | 🏜️ 🇺🇸 Moab, Utah      | Desert riding, technical sandstone, hydration & gear safety.                 |
| `explore-castelli-romani-italy` | 🇮🇹 🏔️ Castelli Romani | Volcanic terrain, steep climbs, Roman history, and local food stops.         |
| `explore-dolomiti-italy`        | 🇮🇹 🏛️ Dolomites       | Expert guide for cycling in the Dolomites (UNESCO Heritage), Northern Italy. |

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
    "trails": [
      "Via Coste del Lago",
      "sentiero del Diavolo -  Diavola",
      "Fratte Ignoranti",
      "511a",
      "sentiero non manutenuto"
    ],
    "distance_km": 8.95,
    "ascent_m": 180,
    "difficulty": "🟢 Beginner (Short and relatively flat, ideal for everyone)"
  },
  "map_image_url": "https://static-maps.fly.dev/staticmap?size=600x400&path=weight:3|color:red|41.72884,12.658322|41.728698,12.658645|41.727697,12.659724|41.726724,12.66084|41.724928,12.662776|41.724354,12.662834|41.723463,12.663892|41.72239,12.664424|41.7204,12.665261|41.718755,12.666515|41.718456,12.667007|41.718446,12.667268|41.718055,12.666385|41.716761,12.665358|41.715515,12.664873|41.714009,12.664308|41.713043,12.663772|41.712424,12.663656|41.708698,12.661992|41.707263,12.661138|41.706247,12.662865|41.704467,12.662073|41.70086,12.660068|41.6995,12.664117|41.697048,12.662747|41.696534,12.662809|41.696426,12.662215|41.697318,12.659836|41.698138,12.658682|41.698522,12.658749|41.698706,12.658374|41.699874,12.656835|41.701813,12.655463|41.705429,12.65443|41.708277,12.654626|41.710628,12.655317|41.715592,12.657084|41.717997,12.657972|41.718528,12.657977|41.718807,12.657954|41.722864,12.659048|41.725675,12.65948|41.726595,12.659229|41.726447,12.658924|41.726478,12.658338|41.727223,12.657301|41.727823,12.658088|41.728498,12.658147|41.72877,12.658069|41.72883,12.658305|41.72884,12.658322&maptype=mapnik",
  "map_url": "https://www.google.com/maps/dir/?api=1&destination=41.728889,12.6582689",
  "gpx_content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<gpx version=\"1.1\" creator=\"BikeScout\" xmlns=\"http://www.topografix.com/GPX/1/1\">\n  <trk><name>BikeScout Route</name><trkseg>\n    <trkpt lat=\"41.72884\" lon=\"12.658322\"><ele>379.0</ele></trkpt>\n    <trkpt lat=\"41.728895\" lon=\"12.658414\"><ele>380.0</ele></trkpt>\n    <trkpt lat=\"41.728764\" lon=\"12.658573\"><ele>380.0</ele></trkpt>\n    <trkpt lat=\"41.728724\" lon=\"12.658616\"><ele>380.0</ele></trkpt>\n    <trkpt lat=\"41.728698\" lon=\"12.658645\"><ele>380.0</ele></trkpt>\n    <trkpt lat=\"41.72852\" lon=\"12.658842\"><ele>380.0</ele></trkpt>\n    <trkpt lat=\"41.72832\" lon=\"12.659062\"><ele>372.0</ele></trkpt>\n    <trkpt lat=\"41.728005\" lon=\"12.659394\"><ele>382.0</ele></trkpt>\n    <trkpt lat=\"41.727697\" lon=\"12.659724\"><ele>382.0</ele></trkpt>\n    <trkpt lat=\"41.727181\" lon=\"12.660305\"><ele>387.0</ele></trkpt>\n    <trkpt lat=\"41.727154\" lon=\"12.660339\"><ele>387.0</ele></trkpt>\n    <trkpt lat=\"41.726939\" lon=\"12.660592\"><ele>387.0</ele></trkpt>\n    <trkpt lat=\"41.726724\" lon=\"12.66084\"><ele>393.0</ele></trkpt>\n    <trkpt lat=\"41.726591\" lon=\"12.660994\"><ele>387.0</ele></trkpt>\n    <trkpt lat=\"41.7261\" lon=\"12.66149\"><ele>387.3</ele></trkpt>\n    <trkpt lat=\"41.725284\" lon=\"12.662387\"><ele>388.0</ele></trkpt>\n    <trkpt lat=\"41.724928\" lon=\"12.662776\"><ele>389.0</ele></trkpt>\n    <trkpt lat=\"41.724887\" lon=\"12.662725\"><ele>389.0</ele></trkpt>\n    <trkpt lat=\"41.724854\" lon=\"12.662711\"><ele>389.0</ele></trkpt>\n    <trkpt lat=\"41.724556\" lon=\"12.662766\"><ele>389.0</ele></trkpt>\n    <trkpt lat=\"41.724354\" lon=\"12.662834\"><ele>387.0</ele></trkpt>\n    <trkpt lat=\"41.724129\" lon=\"12.662971\"><ele>381.0</ele></trkpt>\n    <trkpt lat=\"41.723985\" lon=\"12.663059\"><ele>381.0</ele></trkpt>\n    <trkpt lat=\"41.723953\" lon=\"12.66311\"><ele>381.0</ele></trkpt>\n    <trkpt lat=\"41.723463\" lon=\"12.663892\"><ele>383.3</ele></trkpt>\n    <trkpt lat=\"41.723378\" lon=\"12.663968\"><ele>383.8</ele></trkpt>\n    <trkpt lat=\"41.723124\" lon=\"12.664095\"><ele>379.0</ele></trkpt>\n    <trkpt lat=\"41.72278\" lon=\"12.664262\"><ele>380.0</ele></trkpt>\n    <trkpt lat=\"41.72239\" lon=\"12.664424\"><ele>365.0</ele></trkpt>\n    <trkpt lat=\"41.722306\" lon=\"12.664417\"><ele>363.9</ele></trkpt>\n    <trkpt lat=\"41.722234\" lon=\"12.664434\"><ele>364.2</ele></trkpt>\n    <trkpt lat=\"41.720907\" lon=\"12.665037\"><ele>349.0</ele></trkpt>\n    <trkpt lat=\"41.7204\" lon=\"12.665261\"><ele>337.0</ele></trkpt>\n    <trkpt lat=\"41.719511\" lon=\"12.665673\"><ele>332.0</ele></trkpt>\n    <trkpt lat=\"41.719135\" lon=\"12.665942\"><ele>324.0</ele></trkpt>\n    <trkpt lat=\"41.718813\" lon=\"12.66641\"><ele>324.0</ele></trkpt>\n    <trkpt lat=\"41.718755\" lon=\"12.666515\"><ele>324.0</ele></trkpt>\n    <trkpt lat=\"41.718618\" lon=\"12.66681\"><ele>325.0</ele></trkpt>\n    <trkpt lat=\"41.718564\" lon=\"12.666963\"><ele>326.0</ele></trkpt>\n    <trkpt lat=\"41.718506\" lon=\"12.666963\"><ele>326.0</ele></trkpt>\n    <trkpt lat=\"41.718456\" lon=\"12.667007\"><ele>326.0</ele></trkpt>\n    <trkpt lat=\"41.718433\" lon=\"12.667085\"><ele>326.0</ele></trkpt>\n    <trkpt lat=\"41.718437\" lon=\"12.667128\"><ele>326.0</ele></trkpt>\n    <trkpt lat=\"41.718471\" lon=\"12.667198\"><ele>326.0</ele></trkpt>\n    <trkpt lat=\"41.718446\" lon=\"12.667268\"><ele>326.0</ele></trkpt>\n    <trkpt lat=\"41.718399\" lon=\"12.667229\"><ele>326.0</ele></trkpt>\n    <trkpt lat=\"41.718404\" lon=\"12.666882\"><ele>321.0</ele></trkpt>\n    <trkpt lat=\"41.718289\" lon=\"12.666686\"><ele>320.0</ele></trkpt>\n    <trkpt lat=\"41.718055\" lon=\"12.666385\"><ele>319.4</ele></trkpt>\n    <trkpt lat=\"41.717811\" lon=\"12.666168\"><ele>319.0</ele></trkpt>\n    <trkpt lat=\"41.71722\" lon=\"12.665683\"><ele>316.5</ele></trkpt>\n    <trkpt lat=\"41.716935\" lon=\"12.665465\"><ele>315.9</ele></trkpt>\n    <trkpt lat=\"41.716761\" lon=\"12.665358\"><ele>315.0</ele></trkpt>\n    <trkpt lat=\"41.716579\" lon=\"12.665256\"><ele>313.6</ele></trkpt>\n    <trkpt lat=\"41.715636\" lon=\"12.664905\"><ele>306.0</ele></trkpt>\n    <trkpt lat=\"41.715569\" lon=\"12.664887\"><ele>306.0</ele></trkpt>\n    <trkpt lat=\"41.715515\" lon=\"12.664873\"><ele>306.0</ele></trkpt>\n    <trkpt lat=\"41.714815\" lon=\"12.664699\"><ele>303.3</ele></trkpt>\n    <trkpt lat=\"41.714052\" lon=\"12.664389\"><ele>301.0</ele></trkpt>\n    <trkpt lat=\"41.713995\" lon=\"12.664368\"><ele>301.0</ele></trkpt>\n    <trkpt lat=\"41.714009\" lon=\"12.664308\"><ele>301.0</ele></trkpt>\n    <trkpt lat=\"41.713354\" lon=\"12.664078\"><ele>301.0</ele></trkpt>\n    <trkpt lat=\"41.713181\" lon=\"12.663948\"><ele>300.0</ele></trkpt>\n    <trkpt lat=\"41.713135\" lon=\"12.663828\"><ele>300.0</ele></trkpt>\n    <trkpt lat=\"41.713043\" lon=\"12.663772\"><ele>300.0</ele></trkpt>\n    <trkpt lat=\"41.712963\" lon=\"12.66379\"><ele>300.0</ele></trkpt>\n    <trkpt lat=\"41.7129\" lon=\"12.663859\"><ele>300.0</ele></trkpt>\n    <trkpt lat=\"41.71278\" lon=\"12.663773\"><ele>299.8</ele></trkpt>\n    <trkpt lat=\"41.712424\" lon=\"12.663656\"><ele>299.0</ele></trkpt>\n    <trkpt lat=\"41.712206\" lon=\"12.663568\"><ele>299.0</ele></trkpt>\n    <trkpt lat=\"41.711071\" lon=\"12.663092\"><ele>298.0</ele></trkpt>\n    <trkpt lat=\"41.709462\" lon=\"12.662412\"><ele>291.6</ele></trkpt>\n    <trkpt lat=\"41.708698\" lon=\"12.661992\"><ele>290.8</ele></trkpt>\n    <trkpt lat=\"41.707882\" lon=\"12.661506\"><ele>289.0</ele></trkpt>\n    <trkpt lat=\"41.707826\" lon=\"12.661473\"><ele>289.0</ele></trkpt>\n    <trkpt lat=\"41.707615\" lon=\"12.661348\"><ele>289.0</ele></trkpt>\n    <trkpt lat=\"41.707263\" lon=\"12.661138\"><ele>288.0</ele></trkpt>\n    <trkpt lat=\"41.706817\" lon=\"12.661967\"><ele>288.0</ele></trkpt>\n    <trkpt lat=\"41.706457\" lon=\"12.662689\"><ele>288.0</ele></trkpt>\n    <trkpt lat=\"41.706338\" lon=\"12.662806\"><ele>288.0</ele></trkpt>\n    <trkpt lat=\"41.706247\" lon=\"12.662865\"><ele>288.0</ele></trkpt>\n    <trkpt lat=\"41.706048\" lon=\"12.662882\"><ele>288.0</ele></trkpt>\n    <trkpt lat=\"41.705642\" lon=\"12.662707\"><ele>287.0</ele></trkpt>\n    <trkpt lat=\"41.705506\" lon=\"12.662628\"><ele>287.0</ele></trkpt>\n    <trkpt lat=\"41.704467\" lon=\"12.662073\"><ele>289.0</ele></trkpt>\n    <trkpt lat=\"41.703136\" lon=\"12.661321\"><ele>288.0</ele></trkpt>\n    <trkpt lat=\"41.701683\" lon=\"12.660473\"><ele>287.0</ele></trkpt>\n    <trkpt lat=\"41.700874\" lon=\"12.660012\"><ele>287.0</ele></trkpt>\n    <trkpt lat=\"41.70086\" lon=\"12.660068\"><ele>287.0</ele></trkpt>\n    <trkpt lat=\"41.699876\" lon=\"12.664065\"><ele>287.4</ele></trkpt>\n    <trkpt lat=\"41.699813\" lon=\"12.664231\"><ele>287.8</ele></trkpt>\n    <trkpt lat=\"41.699719\" lon=\"12.66436\"><ele>288.0</ele></trkpt>\n    <trkpt lat=\"41.6995\" lon=\"12.664117\"><ele>287.1</ele></trkpt>\n    <trkpt lat=\"41.699272\" lon=\"12.663963\"><ele>287.6</ele></trkpt>\n    <trkpt lat=\"41.697629\" lon=\"12.663154\"><ele>303.3</ele></trkpt>\n    <trkpt lat=\"41.697414\" lon=\"12.663018\"><ele>304.7</ele></trkpt>\n    <trkpt lat=\"41.697048\" lon=\"12.662747\"><ele>306.0</ele></trkpt>\n    <trkpt lat=\"41.696754\" lon=\"12.662614\"><ele>306.8</ele></trkpt>\n    <trkpt lat=\"41.696632\" lon=\"12.662624\"><ele>307.2</ele></trkpt>\n    <trkpt lat=\"41.696567\" lon=\"12.6627\"><ele>307.2</ele></trkpt>\n    <trkpt lat=\"41.696534\" lon=\"12.662809\"><ele>307.2</ele></trkpt>\n    <trkpt lat=\"41.696394\" lon=\"12.663616\"><ele>307.2</ele></trkpt>\n    <trkpt lat=\"41.696337\" lon=\"12.663692\"><ele>306.9</ele></trkpt>\n    <trkpt lat=\"41.696252\" lon=\"12.66372\"><ele>311.0</ele></trkpt>\n    <trkpt lat=\"41.696426\" lon=\"12.662215\"><ele>297.3</ele></trkpt>\n    <trkpt lat=\"41.696476\" lon=\"12.661909\"><ele>296.1</ele></trkpt>\n    <trkpt lat=\"41.696564\" lon=\"12.661605\"><ele>295.4</ele></trkpt>\n    <trkpt lat=\"41.696831\" lon=\"12.660957\"><ele>299.0</ele></trkpt>\n    <trkpt lat=\"41.697318\" lon=\"12.659836\"><ele>293.4</ele></trkpt>\n    <trkpt lat=\"41.697557\" lon=\"12.659421\"><ele>292.5</ele></trkpt>\n    <trkpt lat=\"41.697955\" lon=\"12.658807\"><ele>288.0</ele></trkpt>\n    <trkpt lat=\"41.698069\" lon=\"12.658711\"><ele>288.1</ele></trkpt>\n    <trkpt lat=\"41.698138\" lon=\"12.658682\"><ele>288.1</ele></trkpt>\n    <trkpt lat=\"41.698247\" lon=\"12.658685\"><ele>288.2</ele></trkpt>\n    <trkpt lat=\"41.698368\" lon=\"12.658744\"><ele>289.0</ele></trkpt>\n    <trkpt lat=\"41.698445\" lon=\"12.658762\"><ele>289.0</ele></trkpt>\n    <trkpt lat=\"41.698522\" lon=\"12.658749\"><ele>289.0</ele></trkpt>\n    <trkpt lat=\"41.698592\" lon=\"12.658705\"><ele>289.0</ele></trkpt>\n    <trkpt lat=\"41.698636\" lon=\"12.658656\"><ele>289.0</ele></trkpt>\n    <trkpt lat=\"41.698695\" lon=\"12.658526\"><ele>289.0</ele></trkpt>\n    <trkpt lat=\"41.698706\" lon=\"12.658374\"><ele>289.0</ele></trkpt>\n    <trkpt lat=\"41.698696\" lon=\"12.658311\"><ele>290.0</ele></trkpt>\n    <trkpt lat=\"41.698691\" lon=\"12.658093\"><ele>290.0</ele></trkpt>\n    <trkpt lat=\"41.698744\" lon=\"12.657931\"><ele>290.0</ele></trkpt>\n    <trkpt lat=\"41.699874\" lon=\"12.656835\"><ele>290.2</ele></trkpt>\n    <trkpt lat=\"41.700256\" lon=\"12.656485\"><ele>290.2</ele></trkpt>\n    <trkpt lat=\"41.700761\" lon=\"12.656074\"><ele>289.8</ele></trkpt>\n    <trkpt lat=\"41.701331\" lon=\"12.655703\"><ele>290.0</ele></trkpt>\n    <trkpt lat=\"41.701813\" lon=\"12.655463\"><ele>298.0</ele></trkpt>\n    <trkpt lat=\"41.702829\" lon=\"12.655107\"><ele>302.4</ele></trkpt>\n    <trkpt lat=\"41.703777\" lon=\"12.654811\"><ele>308.6</ele></trkpt>\n    <trkpt lat=\"41.704662\" lon=\"12.654587\"><ele>312.0</ele></trkpt>\n    <trkpt lat=\"41.705429\" lon=\"12.65443\"><ele>314.9</ele></trkpt>\n    <trkpt lat=\"41.706018\" lon=\"12.654362\"><ele>314.0</ele></trkpt>\n    <trkpt lat=\"41.706686\" lon=\"12.654352\"><ele>311.0</ele></trkpt>\n    <trkpt lat=\"41.707301\" lon=\"12.654415\"><ele>312.8</ele></trkpt>\n    <trkpt lat=\"41.708277\" lon=\"12.654626\"><ele>314.1</ele></trkpt>\n    <trkpt lat=\"41.709075\" lon=\"12.654673\"><ele>317.0</ele></trkpt>\n    <trkpt lat=\"41.709243\" lon=\"12.654664\"><ele>314.0</ele></trkpt>\n    <trkpt lat=\"41.709672\" lon=\"12.65488\"><ele>314.0</ele></trkpt>\n    <trkpt lat=\"41.710628\" lon=\"12.655317\"><ele>315.0</ele></trkpt>\n    <trkpt lat=\"41.711908\" lon=\"12.655985\"><ele>320.8</ele></trkpt>\n    <trkpt lat=\"41.712119\" lon=\"12.656079\"><ele>320.7</ele></trkpt>\n    <trkpt lat=\"41.714157\" lon=\"12.656705\"><ele>327.0</ele></trkpt>\n    <trkpt lat=\"41.715592\" lon=\"12.657084\"><ele>329.5</ele></trkpt>\n    <trkpt lat=\"41.716748\" lon=\"12.657518\"><ele>330.6</ele></trkpt>\n    <trkpt lat=\"41.717382\" lon=\"12.657842\"><ele>331.4</ele></trkpt>\n    <trkpt lat=\"41.717601\" lon=\"12.657906\"><ele>331.6</ele></trkpt>\n    <trkpt lat=\"41.717997\" lon=\"12.657972\"><ele>333.0</ele></trkpt>\n    <trkpt lat=\"41.718276\" lon=\"12.657976\"><ele>333.0</ele></trkpt>\n    <trkpt lat=\"41.718371\" lon=\"12.657977\"><ele>332.0</ele></trkpt>\n    <trkpt lat=\"41.718455\" lon=\"12.658004\"><ele>332.0</ele></trkpt>\n    <trkpt lat=\"41.718528\" lon=\"12.657977\"><ele>332.0</ele></trkpt>\n    <trkpt lat=\"41.718544\" lon=\"12.657963\"><ele>332.0</ele></trkpt>\n    <trkpt lat=\"41.718594\" lon=\"12.657937\"><ele>332.0</ele></trkpt>\n    <trkpt lat=\"41.718749\" lon=\"12.657935\"><ele>332.0</ele></trkpt>\n    <trkpt lat=\"41.718807\" lon=\"12.657954\"><ele>332.0</ele></trkpt>\n    <trkpt lat=\"41.719926\" lon=\"12.658274\"><ele>331.0</ele></trkpt>\n    <trkpt lat=\"41.720851\" lon=\"12.658535\"><ele>340.0</ele></trkpt>\n    <trkpt lat=\"41.72172\" lon=\"12.658749\"><ele>346.0</ele></trkpt>\n    <trkpt lat=\"41.722864\" lon=\"12.659048\"><ele>349.0</ele></trkpt>\n    <trkpt lat=\"41.723294\" lon=\"12.65916\"><ele>349.0</ele></trkpt>\n    <trkpt lat=\"41.723605\" lon=\"12.659232\"><ele>355.0</ele></trkpt>\n    <trkpt lat=\"41.72422\" lon=\"12.659333\"><ele>363.0</ele></trkpt>\n    <trkpt lat=\"41.725675\" lon=\"12.65948\"><ele>367.5</ele></trkpt>\n    <trkpt lat=\"41.726217\" lon=\"12.659555\"><ele>368.1</ele></trkpt>\n    <trkpt lat=\"41.726405\" lon=\"12.659556\"><ele>368.4</ele></trkpt>\n    <trkpt lat=\"41.726633\" lon=\"12.659464\"><ele>369.0</ele></trkpt>\n    <trkpt lat=\"41.726595\" lon=\"12.659229\"><ele>365.7</ele></trkpt>\n    <trkpt lat=\"41.726618\" lon=\"12.65909\"><ele>361.0</ele></trkpt>\n    <trkpt lat=\"41.726536\" lon=\"12.659073\"><ele>361.0</ele></trkpt>\n    <trkpt lat=\"41.7265\" lon=\"12.659045\"><ele>361.0</ele></trkpt>\n    <trkpt lat=\"41.726447\" lon=\"12.658924\"><ele>361.0</ele></trkpt>\n    <trkpt lat=\"41.726381\" lon=\"12.658935\"><ele>361.0</ele></trkpt>\n    <trkpt lat=\"41.726213\" lon=\"12.658897\"><ele>361.0</ele></trkpt>\n    <trkpt lat=\"41.726458\" lon=\"12.658381\"><ele>361.0</ele></trkpt>\n    <trkpt lat=\"41.726478\" lon=\"12.658338\"><ele>361.0</ele></trkpt>\n    <trkpt lat=\"41.726572\" lon=\"12.658142\"><ele>358.0</ele></trkpt>\n    <trkpt lat=\"41.726747\" lon=\"12.657824\"><ele>361.3</ele></trkpt>\n    <trkpt lat=\"41.726901\" lon=\"12.657625\"><ele>362.0</ele></trkpt>\n    <trkpt lat=\"41.727223\" lon=\"12.657301\"><ele>357.0</ele></trkpt>\n    <trkpt lat=\"41.727695\" lon=\"12.656961\"><ele>359.0</ele></trkpt>\n    <trkpt lat=\"41.727813\" lon=\"12.656882\"><ele>359.0</ele></trkpt>\n    <trkpt lat=\"41.727831\" lon=\"12.657683\"><ele>362.2</ele></trkpt>\n    <trkpt lat=\"41.727823\" lon=\"12.658088\"><ele>364.0</ele></trkpt>\n    <trkpt lat=\"41.728103\" lon=\"12.658169\"><ele>370.0</ele></trkpt>\n    <trkpt lat=\"41.728178\" lon=\"12.658208\"><ele>370.8</ele></trkpt>\n    <trkpt lat=\"41.728382\" lon=\"12.658382\"><ele>380.0</ele></trkpt>\n    <trkpt lat=\"41.728498\" lon=\"12.658147\"><ele>377.0</ele></trkpt>\n    <trkpt lat=\"41.728588\" lon=\"12.657962\"><ele>377.0</ele></trkpt>\n    <trkpt lat=\"41.728648\" lon=\"12.658018\"><ele>377.0</ele></trkpt>\n    <trkpt lat=\"41.728667\" lon=\"12.657981\"><ele>377.0</ele></trkpt>\n    <trkpt lat=\"41.72877\" lon=\"12.658069\"><ele>377.0</ele></trkpt>\n    <trkpt lat=\"41.728806\" lon=\"12.658104\"><ele>377.0</ele></trkpt>\n    <trkpt lat=\"41.728793\" lon=\"12.658157\"><ele>377.0</ele></trkpt>\n    <trkpt lat=\"41.72881\" lon=\"12.658209\"><ele>377.0</ele></trkpt>\n    <trkpt lat=\"41.72883\" lon=\"12.658305\"><ele>377.9</ele></trkpt>\n    <trkpt lat=\"41.72884\" lon=\"12.658322\"><ele>379.0</ele></trkpt>\n  </trkseg></trk></gpx>"
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

### 4. `analyze_route_surfaces`

Analyzes the physical composition of the route to help users choose the appropriate bike (Road, Gravel, or MTB) and categorizes climbs using professional cycling standards.
This tool goes beyond simple mapping by analyzing the physical composition of the route and cross-referencing it with the user's specific bike setup to ensure safety, performance, and realistic effort estimation.

#### **Core Functionality:**
* **Surface Detection:** Identifies asphalt, gravel, grass, stones, and unpaved sections using OpenStreetMap metadata.
* **Percentage Breakdown:** Calculates the exact percentage of each surface type relative to the total distance.
* **Pro Climb Categorization:** Identifies climbs (Category 4 to Hors Catégorie) using an effort-weighted algorithm that accounts for terrain resistance.
* **Professional Technical Grading**: Leverages international standards like MTB-Scale (S0-S5) and SAC-Scale. It identifies technical features such as rock gardens, steep steps, and trail visibility to provide expert-level safety briefings.
* **Elevation Sanitization:** Uses a progressive filtering logic to remove "satellite noise" from SRTM data, providing realistic elevation gain metrics.
* **Bike Compatibility Check:** Automatically assesses if the route is suitable based on the bike type and standardized tire setup.
* **Safety & Technical Grading:** Analyzes OSM tracktype (Grades 1-5) to distinguish between smooth gravel and rough, technical MTB trails.

#### **Parameters:**

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | Latitude of the starting point. |
| `lon` | `float` | Required | Longitude of the starting point. |
| `radius_km` | `int` | `10` | The total target distance of the loop (Round Trip). |
| `profile` | `str` | `cycling-mountain` | ORS routing profile (e.g., `cycling-road`, `cycling-mountain`). |
| `bike_type` | `str` | `MTB` | User's bike (Options: `Road`, `Gravel`, `MTB`, `E-MTB`, `Enduro`). |
| `tire_size_option` | `str` | `29` | Standard wheel sizes (MTB: `26`, `27.5`, `29` | Road/Gravel: `700c`, `650b`). |
| `points` | `int` | `3` | Complexity of the loop shape (3 = triangle, 10 = circular). |
| `seed` | `int` | `42` | Random seed. Change it to discover a different route variation in the same area. |

#### **Technical Insights:**

> **Reality Filter:** This tool automatically reduces raw satellite elevation data by up to 40% on steep terrain to correct for SRTM sensor noise, ensuring the "Elevation Gain" matches real-world barometric sensors.
>
> **Effort Multiplier:** Climb categories are calculated with a **1.4x intensity factor** for MTB profiles to account for the increased rolling resistance and technical effort of off-road ascending.

**Example Output (JSON) for MTB:**
```json
{
  "status": "Success",
  "profile_used": "cycling-mountain",
  "technical_summary": {
    "distance_km": 39.64,
    "elevation_gain_m": 1796,
    "climb_category": "Hors Catégorie (HC) - Legendary Challenge",
    "avg_gradient_est": "12.9%",
    "technical_difficulty": {
      "mtb_scale": "Standard / Unclassified",
      "trail_visibility":"Excellent",
      "technical_notes": "Technical grading based on OSM mountain standards."
    }
  },
  "bike_setup_check": {
    "compatible": true,
    "bike_used": "MTB",
    "tire_setup": "29 wheels (~54mm)"
  },
  "surface_breakdown": [
    {
      "type": "Paved",
      "percentage": "44.8%"
    },
    {
      "type": "Unknown",
      "percentage": "39.5%"
    },
    {
      "type": "Compact",
      "percentage": "7.2%"
    },
    {
      "type": "Grass",
      "percentage": "5.7%"
    },
    {
      "type": "Concrete",
      "percentage": "1.6%"
    },
    {
      "type": "Asphalt",
      "percentage": "1.2%"
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
  "technical_summary": {
    "distance_km": 44.48,
    "elevation_gain_m": 979,
    "climb_category": "Category 2 - Hard Climb",
    "avg_gradient_est": "4.9%"
  },
  "bike_setup_check": {
    "compatible": true,
    "bike_used": "Road",
    "tire_setup": "700c wheels"
  },
  "surface_breakdown": [
    {
      "type": "Paved",
      "percentage": "61.3%"
    },
    {
      "type": "Unknown",
      "percentage": "37.4%"
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
  "profile_used": "cycling-regular",
  "technical_summary": {
    "distance_km": 38.08,
    "elevation_gain_m": 976,
    "climb_category": "Category 1 - Brutal Ascent",
    "avg_gradient_est": "5.7%"
  },
  "bike_setup_check": {
    "compatible": true,
    "bike_used": "Gravel",
    "tire_setup": "700c wheels"
  },
  "surface_breakdown": [
    {
      "type": "Paved",
      "percentage": "51.9%"
    },
    {
      "type": "Unknown",
      "percentage": "45.2%"
    },
    {
      "type": "Asphalt",
      "percentage": "1.3%"
    },
    {
      "type": "Concrete",
      "percentage": "1.1%"
    },
    {
      "type": "Other",
      "percentage": "0.5%"
    }
  ],
  "safety_warnings": [
    "Comfort warning: 0.5% is Other."
  ]
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
* **Static Maps:** Static map images generated via OpenStreetMap contributors and rendered through public static map instances.
