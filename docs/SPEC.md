# SPEC.md — BikeScout product specification

Normative for **product intent**. Current behavior is defined by `src/`; build and verification rules live in `PROCESS.md` and `CODE_STANDARDS.md`; user-facing language and terminology follow `BRAND.md`.

## 1. Executive summary and value proposition

**BikeScout** is a tactical cycling intelligence and route-planning platform engineered for off-road, mixed-terrain, road and electric cycling (`mtb`, `enduro`, `gravel`, `road`, `e-mtb`).

Standard consumer navigation platforms optimize for shortest path or generic road routing, failing to account for dynamic surface degradation, micro-weather hydrology, terrain-specific mechanical setup and physiological energy expenditure. BikeScout bridges this operational gap by transforming raw geospatial, meteorological and elevation telemetry into actionable, pre-ride **Tactical Intelligence** — delivered both as an interactive web application and as a headless **Model Context Protocol (MCP)** tool suite for autonomous AI workflows.

## 2. Target market and use cases

### 2.1 Primary user personas

1. **Endurance and off-road cyclists (MTB, Enduro, Gravel):** require trail surface composition, mud/wetness risk forecasting, tire pressure calibration and technical difficulty ratings before departure.
2. **e-MTB and performance riders:** require battery consumption modeling across elevation profiles, ambient temperature derating and rider/bike mass dynamics.
3. **AI agents and autonomous hosts** (Claude, Gemini Antigravity, Cursor, Windsurf, Codex): require deterministic, schema-validated geospatial and cycling intelligence tools exposed via MCP — or local GGUF inference — to execute end-to-end ride planning workflows on behalf of users.

### 2.2 Core operational scenarios

- **Autonomous loop and point-to-point mission generation:** routes constrained by target distance, directional bias, urban avoidance, rural preference and tolerance thresholds.
- **Pre-ride risk and readiness assessment:** weather windows, soil/mud conditions and climb severity combined into a consolidated briefing with actionable safety advisories.
- **Logistics and self-sufficiency planning:** caloric/hydration/electrolyte schedules and route-adjacent Points of Interest (water, shelter, bike support).
- **Navigation artifact export:** standardized GPX tracks, elevation profiles and tactical map visualizations for head-unit deployment.

## 3. Functional capabilities and domain modules

### 3.1 Geospatial routing and geocoding engine

- **Capabilities:** forward/reverse geocoding, round-trip loop synthesis and A-to-B routing via an ORS-compatible provider (currently HeiGIT).
- **Tactical routing controls:** directional corridor biasing (`north`, `south`, `east`, `west`); environment filtering (`avoid_urban`, `prefer_rural`); optimization priorities (`balanced`, `distance_first`, `ride_character_first`) with distance flexibility from `0` to `30` percent.
- **Point-to-point missions** are selected by supplying destination coordinates; there is no separate `route_mode` parameter on the MCP tool (see `PROCESS.md`).

### 3.2 Surface and mechanical intelligence

- **Capabilities:** decomposes route geometry into surface categories (singletrack, gravel, paved, unpaved) and computes gradient metrics (average gradient, climb categories, peak climb pitch).
- **Equipment optimization:** discipline- and wheel-size-specific (`27.5"`, `29"`, `700c`, etc.) tire pressure recommendations (PSI/bar) and bike-to-terrain compatibility hazards.
- **e-MTB telemetry:** estimates battery energy drain (`Wh`), remaining state of charge (`%`) and temperature-adjusted usable capacity.

### 3.3 Environmental and hydrology risk

- **Capabilities:** localized short-term forecasts (temperature peaks, precipitation probability, wind) combined with historical precipitation and soil saturation modeling to predict trail mud severity and ride windows.

### 3.4 Physiological and logistics planning

- **Nutrition and hydration:** energy expenditure and resupply targets based on rider mass (`kg`), gender, fitness tier (`beginner`, `intermediate`, `pro`), distance and elevation gain.
- **Tactical POIs and exports:** route-adjacent hydration/support amenities, downloadable GPX files, altimetry charts and static tactical maps.

### 3.5 Capability to implementation traceability

| Capability | Registered tool(s) | Evidence in tests |
| :--- | :--- | :--- |
| Geocoding | `geocode_location` | `tests/tools/test_geocoding.py` |
| Mission synthesis + tactical overlays | `trail_scout_simple`, `trail_scout` | `tests/tools/test_scouting.py`, `test_mcp_server.py` |
| Weather / ride window | `check_trail_weather`, `ride_window_planner` | `tests/tools/test_weather.py` |
| Hydration and nutrition | `hydration_scout`, mission nutrition overlay | `tests/tools/test_nutrition.py` |
| Imported track audit | `analyze_gpx_track` | `tests/tools/race/test_race_analysis.py` |
| Surface, tire, battery, mud, terrain | Internal services used by the mission tools | `tests/tools/test_surface.py`, `test_bike_setup.py`, `test_battery.py`, `test_mud.py`, `test_terrain.py` |

New capabilities must update this table, the tool inventory in `TECH_STACK.md`, the parameter table in `PROCESS.md`, and the tests in the same change.

## 4. Acceptance criteria

A change satisfies the specification only when all applicable criteria hold:

1. Every tool invocation returns a Pydantic response or a structured `{"status": "Error", "message": ...}` payload; no unhandled exception reaches the MCP client.
2. Coordinates are resolved before routing; A-to-B missions are inferred from destination coordinates.
3. Explicit `include_*` requests are honored regardless of bike type; defaults never suppress an explicit user request.
4. MCP and the Streamlit local planner produce equivalent mission briefings for the same normalized intent.
5. Estimates (mud severity, battery, nutrition, difficulty) state their inputs and uncertainty; they are never presented as measurements.
6. Generated artifacts are reproducible and served from `~/.bikescout` through the declared MCP resources.
7. Unit tests use stubs/fakes — no live model, no live HTTP — and the suite stays at or above 80% coverage.
8. User-facing copy, units and terminology match `BRAND.md`.

## 5. Invariants and non-goals

**Invariants:** metric units in outputs; ISO-formatted dates; structured and schema-validated tool results; no fabricated data on failure; explicit user overrides win over defaults.

**Non-goals:** general-purpose car navigation or live traffic; medical advice; guarantees about trail legality or access; model training inside the test suite; autonomous git push/deployment.

## 6. Canonical vocabulary

Terms are defined in `BRAND.md`: **BikeScout**, **Tactical Intelligence**, **mission**, **briefing**, **overlay**, **bike type**, **profile**, **complexity**, **ride window**, **Go/No-Go**, **POI**, **tire setup**, **battery telemetry**. Use those spellings consistently in code docstrings, docs and user-facing copy; add new terms to the glossary when a capability is introduced.

## 7. Change protocol

When product intent changes: update this file, the traceability table (§3.5), the relevant schemas and tools, the tests, and public examples in `README.md`. Changing a public schema, tool parameter or mission state contract requires approval per `AGENTS.md` §2.
