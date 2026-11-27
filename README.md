# BikeScout 

### Open-source AI cycling route planner for MTB, gravel, road and e-bike riders

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-red.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Version](https://img.shields.io/badge/Version-1.8.0-green.svg)](https://github.com/hifly81/bikescout/releases)
![Python](https://img.shields.io/badge/python-3.10-blue.svg)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

---

BikeScout is a specialized AI engine for MTB, Road, E-Bike, and Gravel mission planning.
It transforms raw map data into Tactical Intelligence, predicting terrain conditions and trail hazards.
The system provides precise setup advice, tailoring your equipment to the demands of the specific route, identifying technical challenges and environmental risks before you even leave the garage.

---

## Quickstart

### [How to use BikeScout](https://hifly81.github.io/bikescout/documentation/index.html#quickstart)
- instruction, using the **[BikeScout GUI](https://hifly81.github.io/bikescout/documentation/index.html#gui)**
- instruction, using your favourite MCP Agent client: [Claude Desktop, Cursor, Codex, Google Antigravity, Windsurf](https://hifly81.github.io/bikescout/documentation/index.html#mcp-gui)

<details>
 <summary style="cursor: pointer;">
    <h3 style="display: inline; color: #0366d6;">🎥 Click to watch BikeScout GUI</h3>
  </summary>
  <br>
  <div align="center">
    <video src="https://github.com/user-attachments/assets/edba3595-f711-45ef-9ada-ee1d41f11772" width="100%" controls autoplay muted loop>
    </video>
  </div>
</details>


<details>
  <summary style="cursor: pointer;">
    <h3 style="display: inline; color: #0366d6;">🎥 Click to watch a Demo</h3>
  </summary>
  <br>
  <div align="center">
    <video src="https://github.com/user-attachments/assets/cd984f3d-0ba8-4590-9645-99f2b5e980b6" width="100%" controls autoplay muted loop>
    </video>
  </div>
</details>

---

## Explore BikeScout

* **[User Guide](https://hifly81.github.io/bikescout/documentation/index.html)** Detailed API references and step-by-step guides to deploy the BikeScout.

* **[Website](https://hifly81.github.io/bikescout)** Explore the visual breakdown of Mud Logic, S-Scale terrain grading, and how we transform raw OSM data into mission-ready intel. Check the latest race analysis reports from the legendary routes.

**Love BikeScout?** ⭐ Star this repo to support the development of the first open-source tactical cycling engine.

**Found a bug?** Open an Issue. Want to add a local skill? PRs are welcome!

---

## Example Scenarios

You can ask **BikeScout** complex, multi-step requests. It combines real-time data with technical cycling intelligence to provide expert-level answers.

### 🗺️ Advanced Planning (Multi-Tool)
* *"I'm at Monte Cavo, near Rome (Italy) with my MTB bike (29 tires). Plan a 25km loop for me. Check if the terrain is compatible with my bike, verify the afternoon rain probability, and suggest a 'Fraschetta' for the finish. Use the Castelli Romani guide."*

### ⚙️ Bike Setup & Surface Intelligence
* *"Check this route from Barcelona city center to El Prat. I'm on a Road Bike with 25mm tires. Is it compatible? Give me the exact percentage of gravel vs asphalt."*

### 📈 Visual Elevation & Gradient Analysis
* *"Plan a 40km route starting from Bormio, Italy. I need the Visual Elevation Profile to see the exact gradients of the Stelvio climb. Highlight sections over 12% so I can manage my pacing."*
* *"Give me the terrain truth for this route: true ascent, maximum gradient, every significant climb with a FIETS category, and how confident you are in the elevation data."*

### 🏔️ Local Expertise
* *"Use the Derby local guide to plan a road cycling route starting from Derby. I need at least 800m of elevation gain. Also, recommend the correct tire pressure for high-altitude descents."*

### 🛠️ Quick Tech Checks
* *"Give me the safety checklist and calculate front/rear pressure for a 90kg rider on 2.3" tubeless tires (25mm internal rims, DH casing) for a muddy S3 ride."*

### 🏁 Post-Ride Analysis & Terrain Truth
* *"Analyze my ride from 2026-04-12. Compare my average speed with the Mud Risk at that time and tell me if the terrain conditions were the reason for my slow pace."*

---

## How BikeScout compares

BikeScout is built for **pre-ride tactical planning and route audit**. It complements route discovery, training logs, and trail databases with deterministic, cycling-specific analysis.

| Platform | Typical focus | What BikeScout adds |
| :--- | :--- | :--- |
| **Komoot** | Route discovery and navigation | Weather-aware route planning, TAEL mud-risk heuristics, surface/S-scale context, tire pressure and setup guidance, nutrition planning, and exportable GPX/altimetry artifacts. |
| **Strava** | Activity tracking, social, and training history | Pre-ride Go/No-Go window planning with forecast-bounded analysis dates (tomorrow to +5 days), plus GPX tactical audit with heuristic climb categorization, performance simulation, and risk alerts. |
| **Ride with GPS** | Route planning and cue sheets | Terrain truth (distance, ascent, gradient, climb metrics), rider/bike-aware recommendations, POI/logistics overlays, and structured tool outputs. |
| **Trailforks** | Trail maps and community condition reports | Route-specific planning context: weather window, mud/traction heuristics, surface/difficulty signals, and equipment/nutrition recommendations for the planned ride. |
| **Generic AI assistants** | General reasoning from text prompts | Grounded MCP tools with typed schemas, a local Streamlit planner/chat GUI, explicit uncertainty/assumption labels, and exportable artifacts (GPX, altimetry, map, race PDF MCP resource). |

> BikeScout is designed to work alongside these tools, not replace their social, navigation, or community-history strengths.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make to **BikeScout** are **greatly appreciated**.

### How to Contribute

1. **Report Bugs**: Found a glitch? Open an [Issue](https://github.com/hifly81/bikescout/issues) with a detailed description and steps to reproduce.
2. **Feature Requests**: Have an idea to make BikeScout better? Open an issue to discuss it first.
3. **Pull Requests**:
   - Fork the repository and create a feature branch (`git checkout -b feature/AmazingFeature`).
   - Make a focused change with clear commits. Keep comments in English.
   - If you touch Python under `src/`, run `uv run ruff check`, `uv run ruff format --check`, `uv run pyright` and `uv run pytest --cov=src/bikescout --cov-fail-under=80` before opening the PR.
   - Push the branch (`git push -u origin feature/AmazingFeature`) and open a Pull Request describing the change and the checks you ran.
   - Discuss changes to public MCP tool signatures, tool names or Streamlit session keys in an issue before opening the PR.

Development setup: `uv sync --extra test --extra dev`. Set `ORS_API_KEY` in a local, untracked `.env` — never in committed client configs.

### Coding Standards
- Please follow [PEP 8](https://peps.python.org/pep-0008/) for Python code.
- Document new tools and schema changes in `site/documentation/api-reference.html`, with tests.
- Keep comments in English for international collaboration.

*By contributing, you agree that your contributions will be licensed under the project's AGPLv3 License.*

---

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
