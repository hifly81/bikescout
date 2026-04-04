# BikeScout MCP Server

[![License](https://img.shields.io/badge/License-Mixed-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.2.0-green.svg)](https://github.com/hifly81/bikescout/releases)

**BikeScout** is a specialized MCP (Model Context Protocol) server designed for cyclists and mountain bikers. It provides intelligent trail recommendations by combining real-world map data with advanced routing analysis.

## Key Features

- **Real Trail Discovery**: Fetches actual trail names and surface types from **OpenStreetMap** (via Overpass API).
- **Technical Metrics**: Calculates precise distance in kilometers and total elevation gain (ascent).
- **Difficulty Grading**: Automatically evaluates trails as Beginner, Moderate, or Expert based on incline and length.
- **Dynamic Routing**: Generates suggested loops (round trips) based on your starting coordinates.
- **Smart Safety and Weather Forecast**: BikeScout doesn't just find trails; it cross-references location data with real-time weather forecasts to ensure you don't get caught in a storm.

## Prerequisites

- **Python 3.10+**
- **OpenRouteService API Key**: Get a free key at [openrouteservice.org](https://openrouteservice.org/).
- **MCP Client**: Such as Claude Desktop.

## Installation

1. **Clone or save the script**: Save `mcp_server.py` in a local folder.
2. Create a Python Virtual Env from the local folder:
   ```bash
   python3 -m venv venv
   ```
3. Use the provided requirements.txt to install all necessary libraries:
   ```bash
   ./venv/bin/pip install -r requirements.txt
   ```
4. Configure the API Key: Open `mcp_server.py` and replace `YOUR_OPENROUTE_SERVICE_API_KEY` with your actual token.

## Configuration
Add the server to your `claude_desktop_config.json`:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json` 
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

You must replace the placeholders in the JSON configuration with your local absolute paths to the Python script file.
`PATH/TO/YOUR/BIKESCOUT_FOLDER/mcp_server.py`

Example:
 - Linux/macOS: `/home/username/bikescout/mcp_server.py`
 - Windows: `C:/Users/Username/Documents/bikescout/mcp_server.py`

```json
{
  "mcpServers": {
    "bikescout": {
      "command": "PATH/TO/YOUR/BIKESCOUT_FOLDER/venv/bin/python3",
      "args": ["PATH/TO/YOUR/BIKESCOUT_FOLDER/mcp_server.py"],
      "env": {
        "PYTHONPATH": "PATH/TO/YOUR/BIKESCOUT_FOLDER"
      }
    }
  }
}
```

### Using BikeScout with VS Code (Linux/Windows/macOS)
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
      "args": ["PATH/TO/YOUR/BIKESCOUT_FOLDER/mcp_server.py"],
      "env": {
        "PYTHONPATH": "PATH/TO/YOUR/BIKESCOUT_FOLDER"
      }
    }
  }
}
```
4. Start Scouting
   Once saved, you can chat with the AI directly within VS Code. It will automatically detect BikeScout as a "tool." You can then ask: _"Find me a scenic 30km MTB route starting from my current coordinates."_ The AI will execute the Python script, fetch the data from OpenStreetMap and OpenRouteService, and present the results right in your chat window.

## Example Queries

You can ask **BikeScout** questions in both English and Italian. It understands complex requests regarding distance, elevation, and specific file types.

### 🇬🇧 English
* *"BikeScout, find me a 20km mountain bike loop near Frascati and tell me the total ascent and check if it's too windy for a mountain bike."*
* *"Are there any named trails near [Lat, Lon]? I need to know the surface type."*
* *"Suggest a difficult MTB route with at least 600m of climbing."*
* *"What is the terrain like for a 15km ride starting at these coordinates?"*

### 🇮🇹 Italiano
* *"BikeScout, trovami un giro in MTB di 20km vicino a Frascati e dimmi quanta salita c'è. Dammi la traccia GPX ed il link alla traccia e come sarà il tempo lungo il percorso."*
* *"Ci sono sentieri con un nome ufficiale vicino a [Lat, Lon]? Dimmi che tipo di terreno troverò."*
* *"Suggeriscimi un percorso MTB difficile con almeno 600m di dislivello."*
* *"Com'è il terreno per un giro di 15km partendo da queste coordinate?"*

---

## Example Responses

Below is an example of the detailed information **BikeScout** can provide:

### 🇬🇧 English
I found an MTB loop near **Frascati**. Here are the details:

#### 📊 Route Details
* 📍 **Distance:** 11.26 km
* ⛰️ **Total Ascent:** 856 meters
* 🏷️ **Difficulty:** Expert
* 🛤️ **Included Trails:** *Viale Moderno, Via dei Sepolcri*
* 🔗 **Map:** [View on Google Maps](https://www.google.com/maps?q=41.8078,12.6808)

#### 🌤️ Weather Forecast (Next 4 hours)
| Time | Temp | Rain | Wind |
| :--- | :--- | :--- | :--- |
| **10:00 AM** | 13.7°C | 0% | 6.4 km/h |
| **11:00 AM** | 15.2°C | 0% | 7.5 km/h |
| **12:00 PM** | 16.4°C | 0% | 8.7 km/h |
| **01:00 PM** | 17.6°C | 0% | 9.7 km/h |

> ✅ **Advice:** Perfect for riding! The route is challenging (856m of climbing over 11km) but offers great scenic views over the Colli Albani area.

### 🇮🇹 Italiano
Ho trovato un giro in MTB vicino a **Frascati**. Ecco i dettagli:

#### 📊 Dettagli del Percorso
* 📍 **Distanza:** 11.26 km
* ⛰️ **Dislivello:** 856 metri di salita
* 🏷️ **Difficoltà:** Esperto
* 🛤️ **Sentieri inclusi:** *Viale Moderno, Via dei Sepolcri*
* 🔗 **Mappa:** [Visualizza su Google Maps](https://www.google.com/maps?q=41.8078,12.6808)

#### 🌤️ Meteo lungo il percorso (Prossime 4 ore)
| Ora | Temp | Pioggia | Vento |
| :--- | :--- | :--- | :--- |
| **10:00** | 13.7°C | 0% | 6.4 km/h |
| **11:00** | 15.2°C | 0% | 7.5 km/h |
| **12:00** | 16.4°C | 0% | 8.7 km/h |
| **13:00** | 17.6°C | 0% | 9.7 km/h |

> ✅ **Consiglio:** Il tempo è perfetto per l'uscita! Il percorso è impegnativo (856m di dislivello in soli 11km) ma molto panoramico sui Colli Albani.

## Tools Reference

**BikeScout** exposes specialized tools to the MCP host. Currently, the server provides a comprehensive scouting tool, with more modules planned for future releases.

### 1. `trail_scout`
This is the core tool of the server. It performs a multi-step analysis to provide a ride-ready cycling route.

#### **Functionality:**
* **Semantic Search:** Queries OpenStreetMap (Overpass API) to find real names of trails and paths near the starting point.
* **Smart Routing:** Uses OpenRouteService to generate a **Round Trip** (loop) based on the user's preferred distance.
* **Elevation Profiling:** Fetches SRTM elevation data to calculate total ascent and evaluate difficulty.
* **File Generation:** Produces a valid **GPX XML** string for navigation.

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
  "map_url": "http://googleusercontent.com/maps.google.com/...",
  "gpx_content": "<?xml version='1.0' encoding='UTF-8'?>..."
}
```

### 2. `check_trail_weather`
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


---

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

This project has been implemented using:

© openrouteservice.org by HeiGIT | Map data © OpenStreetMap contributors