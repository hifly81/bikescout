# BikeScout MCP Server

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Version](https://img.shields.io/badge/Version-1.1.2-green.svg)](https://github.com/hifly81/bikescout/releases)
![Python](https://img.shields.io/badge/python-3.10-blue.svg)
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

---

## Explore BikeScout

* **[BikeScout Documentation](docs/md/api_docs.md)** **The Technical Core.** Detailed API references and step-by-step guides to deploy the MCP server. Essential for developers integrating BikeScout into Claude, ChatGPT, or custom AI agents.

* **[Official Website](https://hifly81.github.io/bikescout)** **The Strategic Hub.** A high-level overview of our predictive algorithms. Explore the visual breakdown of Mud Logic, S-Scale terrain grading, and how we transform raw OSM data into mission-ready intel.

* **[Tactical Intelligence Blog](https://hifly81.github.io/bikescout/blog.html)** **Field Reports & R&D.** Stay ahead of the curve with our latest research on cycling AI, terrain analysis updates, and real-world testing of tactical routing logic.


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

## Quickstart: Deploy and Use BikeScout 

### Using Docker and OpenClaw

Pre Requirements:

* **Docker Desktop:** [Download it here](https://www.docker.com/products/docker-desktop/).
* **OpenRouteService Key:** [Sign up here](https://openrouteservice.org/) for trail and surface data.
* **LLM Key:** An API key from OpenAI or Anthropic to power the reasoning engine.

1. **Download the repository:** Download this repository as a ZIP and extract it to a folder (e.g., `C:\BikeScout` or `/Users/YourName/BikeScout`).
2. Rename `.env.example` to `.env` and paste your API keys:
```bash
ORS_API_KEY=your_ors_key_here
OPENAI_API_KEY=your_llm_key_here
```
3. Launch: Open your terminal in the folder and run:
```bash
docker-compose up -d
```
4. Access:
- On PC: Open http://localhost:3000
- On Smartphone: Connect to the same Wi-Fi, find your PC's IP (e.g., 192.168.1.15), and open http://192.168.1.15:3000.

To teardown the environment, execute:
```bash
docker compose down -v
```

### Using Docker, Ollama and Open WebUI

If you prefer a private and free experience without external API costs, use the `docker-compose-ollama.yml`
file to run BikeScout with Ollama (Llama 3/Mistral) instead of OpenAI.
Refer to this [guide](docs/md/bikescout_ollama.md) to setup a complete local installation with Ollama and Open WebUI.

### Using the Source Code

Pre Requirements:

- **Python 3.10+**
- **OpenRouteService API Key**: Get a free key at [openrouteservice.org](https://openrouteservice.org/).
- **MCP Client**: Such as Claude Desktop.
- **Strava Account (Optional)**: Required only for the **Post-Ride Tactical Analysis** feature.

To enable Strava integration, you need to create a developer application and generate a long-lived Refresh Token:

See the related [how to obtain a Strava key section](docs/md/strava_key.md)

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

- Add the server to your `claude_desktop_config.json`:
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
* **Post-ride analysis**: Provided by Strava. Post-ride analysis and GPS telemetry are accessed via the [Strava API](https://developers.strava.com/docs/reference).
