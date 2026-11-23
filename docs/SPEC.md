# SPEC.md — BikeScout Agent & MCP Operational Specification

## 1. Executive Summary & Value Proposition

**BikeScout** is a tactical cycling intelligence and route-planning platform engineered for off-road, mixed-terrain, road, and electric cycling (`mtb`, `enduro`, `gravel`, `road`, `e-mtb`).

Standard consumer navigation platforms optimize for shortest path or generic road routing, failing to account for dynamic surface degradation, micro-weather hydrology, terrain-specific mechanical setup, and physiological energy expenditure. BikeScout bridges this operational gap by transforming raw geospatial, meteorological, and elevation telemetry into actionable, pre-ride **Tactical Intelligence**—delivered both as an interactive web application and as a headless **Model Context Protocol (MCP)** tool suite for autonomous AI workflows.

---

## 2. Target Market & Use Cases

### 2.1 Primary User Personas
1. **Endurance & Off-Road Cyclists (MTB, Enduro, Gravel):** Require trail surface composition, mud/wetness risk forecasting, tire pressure calibration, and technical difficulty ratings prior to departure.
2. **e-MTB & Performance Riders:** Require battery consumption modeling across elevation profiles, ambient temperature derating, and rider/bike mass dynamics.
3. **AI Agents & Autonomous Hosts (Claude, Gemini Antigravity, Cursor, Windsurf, Codex):** Require deterministic, schema-validated geospatial and cycling intelligence tools exposed via MCP—or local GGUF inference—to execute end-to-end ride planning workflows on behalf of users.

### 2.2 Core Operational Scenarios
- **Autonomous Loop & Point-to-Point Mission Generation:** Synthesizing routes constrained by target distance, directional bias, urban avoidance, rural preference, and tolerance thresholds.
- **Pre-Ride Risk & Readiness Assessment:** Evaluating weather windows, soil/mud conditions, and climb severity to produce a consolidated readiness score and actionable safety advisories.
- **Logistics & Self-Sufficiency Planning:** Computing caloric/hydration/electrolyte schedules and mapping critical Points of Interest (water resupply, shelter, bike support).
- **Navigation Artifact Export:** Generating standardized GPX tracks, elevation profiles, and tactical map visualizations for head-unit deployment.

---

## 3. Functional Capabilities & Domain Modules

### 3.1 Geospatial Routing & Geocoding Engine
- **Capabilities:** Forward/reverse geocoding, round-trip loop synthesis, and A-to-B routing powered by OpenRouteService.
- **Tactical Routing Controls:**
  - Directional corridor biasing (`north`, `south`, `east`, `west`).
  - Environment filtering (`avoid_urban`, `prefer_rural`).
  - Optimization priority modes (`balanced`, `distance_first`, `ride_character_first`) with configurable distance flexibility (`0`–`30` percent).

### 3.2 Surface & Mechanical Intelligence
- **Capabilities:** Decomposes route geometry into granular surface categories (singletrack, gravel, paved, unpaved) and calculates gradient metrics (average gradient, climb categorization, peak climb pitch).
- **Equipment Optimization:** Computes discipline- and wheel-size-specific (`27.5"`, `29"`, `700c`, etc.) tire pressure recommendations (PSI/Bar) and flags bike-to-terrain compatibility hazards.
- **e-MTB Telemetry Modeling:** Estimates battery energy drain (`Wh`), remaining state-of-charge (`%`), and temperature-adjusted usable capacity.

### 3.3 Environmental & Hydrology Risk
- **Capabilities:** Aggregates localized short-term meteorological forecasts (temperature peaks, precipitation probability, wind) alongside historical precipitation and soil saturation modeling to predict trail mud severity.

### 3.4 Physiological & Logistics Planning
- **Nutrition & Hydration:** Calculates ride energy expenditure and resupply targets tailored to rider mass (`kg`), gender, fitness tier (`beginner`, `intermediate`, `pro`), route distance, and elevation gain.
- **Tactical POIs & Exports:** Identifies route-adjacent hydration/support amenities and generates downloadable GPX files, altimetry charts, and static tactical maps.

---