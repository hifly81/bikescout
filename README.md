# 🚲 BikeScout MCP Server

**BikeScout** is a specialized MCP (Model Context Protocol) server designed for cyclists and mountain bikers. It provides intelligent trail recommendations by combining real-world map data with advanced routing analysis.

## 🌟 Key Features

- **Real Trail Discovery**: Fetches actual trail names and surface types from **OpenStreetMap** (via Overpass API).
- **Technical Metrics**: Calculates precise distance in kilometers and total elevation gain (ascent).
- **Difficulty Grading**: Automatically evaluates trails as Beginner, Moderate, or Expert based on incline and length.
- **Dynamic Routing**: Generates suggested loops (round trips) based on your starting coordinates.

## 🛠️ Prerequisites

- **Python 3.10+**
- **OpenRouteService API Key**: Get a free key at [openrouteservice.org](https://openrouteservice.org/).
- **MCP Client**: Such as Claude Desktop.

## 🚀 Installation

1. **Clone or save the script**: Save `mcp_server.py` in a local folder.
2. **Install dependencies**:
   ```bash
   pip install mcp requests
3. Configure the API Key: Open `mcp_server.py` and replace `YOUR_OPENROUTE_SERVICE_API_KEY` with your actual token.

## ⚙️ Configuration
Add the server to your `claude_desktop_config.json`:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json` 
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bikescout": {
      "command": "python",
      "args": ["PATH/TO/YOUR/mcp_server.py"],
      "env": {
        "PYTHONPATH": "PATH/TO/YOUR"
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
      "command": "python3",
      "args": ["PATH/TO/YOUR/mcp_server.py"],
      "env": {
        "PYTHONPATH": "PATH/TO/YOUR"
      }
    }
  }
}
```
4. Start Scouting
   Once saved, you can chat with the AI directly within VS Code. It will automatically detect BikeScout as a "tool." You can then ask: _"Find me a scenic 30km MTB route starting from my current coordinates."_ The AI will execute the Python script, fetch the data from OpenStreetMap and OpenRouteService, and present the results right in your chat window.

## ❓ Example Queries / Domande Esempio

You can ask **BikeScout** questions in both English and Italian. It understands complex requests regarding distance, elevation, and specific file types.

### 🇬🇧 English
* *"BikeScout, find me a 20km mountain bike loop near Frascati and tell me the total ascent."*
* *"Are there any named trails near [Lat, Lon]? I need to know the surface type."*
* *"Suggest a difficult MTB route with at least 600m of climbing."*
* *"What is the terrain like for a 15km ride starting at these coordinates?"*

### 🇮🇹 Italiano
* *"BikeScout, trovami un giro in MTB di 20km vicino a Frascati e dimmi quanta salita c'è. Dammi la traccia GPX ed il link alla traccia."*
* *"Ci sono sentieri con un nome ufficiale vicino a [Lat, Lon]? Dimmi che tipo di terreno troverò."*
* *"Suggeriscimi un percorso MTB difficile con almeno 600m di dislivello."*
* *"Com'è il terreno per un giro di 15km partendo da queste coordinate?"*

---

## 📝 Example Response / Esempio di Risposta

Below is an example of the detailed information **BikeScout** can provide:

### 🇬🇧 English
**Here is an MTB route found near Frascati:**

### 🚵‍♂️ MTB Route - BikeScout Route
* **Distance:** 16.2 km
* **Total Ascent:** 967 meters
* **Difficulty:** Expert
* **Included Trails:** *Via dei Sepolcri, Viale Moderno*
* **Map Link:** [Google Maps](https://www.google.com/maps?q=41.8077,12.6805)
* **GPX File:** I have generated the GPX track. You can save it as `frascati_mtb_route.gpx` and upload it to your GPS device or app (Komoot, Strava, Garmin).

> *The route takes place in the Colli Albani, a classic cycling area near Rome, with a significant elevation gain of nearly 1000 meters making it challenging but rewarding.*


### 🇮🇹 Italiano
**Ecco un percorso MTB trovato vicino a Frascati:**

### 🚵‍♂️ Percorso MTB - BikeScout Route
* **Distanza:** 16.2 km
* **Dislivello in salita:** 967 metri
* **Difficoltà:** Esperto
* **Trails inclusi:** *Via dei Sepolcri, Viale Moderno*
* **Link alla mappa:** [Google Maps](https://www.google.com/maps?q=41.8077,12.6805)
* **File GPX:** Ho generato la traccia GPX. Puoi salvarla come `frascati_mtb_route.gpx` e caricarla sul tuo dispositivo GPS o app (Komoot, Strava, Garmin).

> *Il percorso si sviluppa sui Colli Albani, zona classica per il ciclismo, con un dislivello significativo di quasi 1000 metri che lo rende impegnativo ma gratificante.*

---

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

This project has been implemented using:

© openrouteservice.org by HeiGIT | Map data © OpenStreetMap contributors