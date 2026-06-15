# BikeScout 

### Open-source AI cycling route planner for MTB, gravel, road and e-bike riders

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-red.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Version](https://img.shields.io/badge/Version-1.5.2-green.svg)](https://github.com/hifly81/bikescout/releases)
![Python](https://img.shields.io/badge/python-3.10-blue.svg)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

---

BikeScout is a specialized AI engine for MTB, Road, E-Bike, and Gravel mission planning.
It transforms raw map data into Tactical Intelligence, predicting terrain conditions and trail hazards.
The system provides precise setup advice, tailoring your equipment to the demands of the specific route, identifying technical challenges and environmental risks before you even leave the garage.

<p align="center">
  <img width="632" height="345" alt="logo-medium" src="https://github.com/user-attachments/assets/f7e15304-0a91-465d-9c7f-ba35933609ed" />
</p>

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

## Example Queries

You can ask **BikeScout** complex, multi-step requests. It combines real-time data with technical cycling intelligence to provide expert-level answers.

### 🗺️ Advanced Planning (Multi-Tool)
* *"I'm at Monte Cavo with my MTB bike (29 tires). Plan a 25km loop for me. Check if the terrain is compatible with my bike, verify the afternoon rain probability, and suggest a 'Fraschetta' for the finish. Use the Castelli Romani guide."*

### ⚙️ Bike Setup & Surface Intelligence
* *"Check this route from Barcelona city center to El Prat. I'm on a Road Bike with 25mm tires. Is it compatible? Give me the exact percentage of gravel vs asphalt."*

### 📈 Visual Elevation & Gradient Analysis
* *"Plan a 40km route starting from Bormio. I need the Visual Elevation Profile to see the exact gradients of the Stelvio climb. Highlight sections over 12% so I can manage my pacing."*

### 🏔️ Local Expertise
* *"Use the Derby local guide to plan a road cycling route starting from Derby. I need at least 800m of elevation gain. Also, recommend the correct tire pressure for high-altitude descents."*

### 🛠️ Quick Tech Checks
* *"Give me the safety checklist and calculate the tire pressure for a 90kg rider on 2.3" tubeless tires for a muddy ride."*

### 🏁 Post-Ride Analysis & Terrain Truth
* *"Analyze my ride from 2026-04-12. Compare my average speed with the Mud Risk at that time and tell me if the terrain conditions were the reason for my slow pace."*

---

## 🏆 Why BikeScout?

While others products focus on where to go, BikeScout focuses on how you can thrive on that specific ride, right now.

| Platform | What they provide | Why BikeScout is superior |
| :--- | :--- | :--- |
| **Komoot** | Static maps | We add **live risk-context** |
| **Strava** | History/Social | We add **predictive safety** |
| **Trailforks** | Databases | We add **personalized intelligence** |
| **Generic AI** | Theory | We add **real-world telemetry** |

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make to **BikeScout** are **greatly appreciated**.

### How to Contribute

1. **Report Bugs**: Found a glitch? Open an [Issue](https://github.com/hifly81/bikescout/issues) with a detailed description and steps to reproduce.
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
