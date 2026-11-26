# TECH_STACK.md — BikeScout architecture and stack

Factual map of the current implementation (version 1.7.0). See `SPEC.md` for intent, `PROCESS.md` for workflow, `CODE_STANDARDS.md` for code rules, `BRAND.md` for visual and language identity.

## 1. Runtime modes

| Mode | Entry point | Notes |
| :--- | :--- | :--- |
| MCP stdio server | `bikescout` (`bikescout.mcp_server:main`) | Default; used by Claude/Cursor/Windsurf/Codex/Gemini clients |
| MCP SSE server | `BIKESCOUT_TRANSPORT=sse bikescout` | `BIKESCOUT_HOST` (default `0.0.0.0`) and `BIKESCOUT_PORT` (default `8000`) |
| Streamlit UI | `streamlit run src/bikescout/app.py` | Tactical UI plus local GGUF chat planner; ORS key can be entered in the sidebar |

Both modes converge on the same domain services under `src/bikescout/tools/`.

## 2. Layering

```text
Clients (.claude/, .cursor/, .codex/, .gemini/, .codeium/)
        |  MCP stdio (or SSE)
        v
FastMCP("BikeScout")  -- src/bikescout/mcp_server.py
        |
        +-- Pydantic v2 contracts -- src/bikescout/schemas.py
        |
        v
Domain services -- src/bikescout/tools/ (surface, weather, geocoding,
        |          mud, nutrition, poi, maps, altimetry, battery, race/, ...)
        v
Providers & local engines
        |-- ORS-compatible routing / POI API (HeiGIT)
        |-- Geocoding: Nominatim / OSM
        |-- Weather: Open-Meteo
        |-- Offline terrain truth, GPX, static maps, charts (local)
        v
Generated artifacts -- ~/.bikescout/{gpx,maps,altimetry}/ (MCP resources)

Streamlit app (app.py) --> local GGUF planner (llama-cpp-python, models/)
                       --> execute_plan_request / process_local_mcp_request
                       --> same domain services
```

## 3. MCP surface (seven tools)

| Tool | Purpose | Key inputs / output |
| :--- | :--- | :--- |
| `geocode_location` | Resolve place names to coordinates | `location_name`, `language` → `GeocodingResponse` |
| `trail_scout` | Full mission with typed profiles | `latitude`, `longitude`, `rider`, `bike`, `mission`; optional destination and `include_*` → `FullMissionBriefingResponse` |
| `trail_scout_simple` | **Unified orchestrator** used by agents and the local planner | Coordinates, rider/bike/mission scalars, `total_length_km`, biases, `priority_mode`, seven `include_*` flags → `FullMissionBriefingResponse` |
| `check_trail_weather` | Tactical forecast | `lat`, `lon`, optional `target_date` → `TacticalForecastResponse` |
| `ride_window_planner` | Best ride window | `lat`, `lon`, duration, surface, date → `StrategicPlannerResponse` |
| `hydration_scout` | Hydration/electrolyte plan | `lat`, `lon`, duration, intensity, rider profile → `HydrationScoutResponse` |
| `analyze_gpx_track` | Imported track / race audit | `gpx_url`, rider/bike scalars, activity, date range → `GpxRaceAuditResponse` |

Resources: `bikescout://altimetry/{filename}`, `bikescout://maps/{filename}`, `bikescout://gpx/{filename}`. The authoritative parameter list is the tool signature in `mcp_server.py`; `PROCESS.md` §4 gives the natural-language mapping rules.

## 4. Stack by layer

- **Server:** `fastmcp>=3.0.0`, `python-dotenv`, `pydantic>=2.0.0`.
- **Domain services:** `requests`, `polyline`, `geopy`, `astral`, `timezonefinder`, `numpy`, `matplotlib`.
- **Exports:** `gpxpy`, `staticmap`, `pillow`, `fpdf`.
- **UI:** `streamlit>=1.35.0`, `watchdog`; theme in `src/bikescout/config.toml`; CSS design tokens in `app_ui_helpers.py`.
- **Local planner:** `llama-cpp-python>=0.3.16`, `huggingface_hub>=0.27.0`; GGUF cache in the ignored `models/` directory; structured JSON with thinking disabled on Qwen3.5.
- **Tests:** `pytest`, `pytest-cov`, `pytest-asyncio` (`asyncio_mode = auto`, `pythonpath = ["src"]`, `testpaths = ["src/bikescout/tests"]`).
- **Dev gates:** `ruff`, `pyright`, `lefthook` (pre-commit runs lint, format, type check and pytest with 80% coverage).

Python >= 3.10; single root `pyproject.toml` with `packages = ["src/bikescout"]`.

## 5. Configuration and environment

| Setting | Where | Purpose |
| :--- | :--- | :--- |
| `ORS_API_KEY` | `.env` (via `python-dotenv`) or Streamlit sidebar | Routing, geocoding and POI requests; never commit it |
| `BIKESCOUT_TRANSPORT` | Environment | `stdio` (default) or `sse` |
| `BIKESCOUT_HOST`, `BIKESCOUT_PORT` | Environment | SSE bind address/port |
| `src/bikescout/config.toml` | Repo | Streamlit dark theme and sidebar behavior; palette in `BRAND.md` |
| `models/` | Ignored directory | On-demand GGUF downloads (Qwen3.5-9B, Ministral-3-8B-Instruct, Qwen2.5-7B-Instruct) |
| `~/.bikescout/` | Generated at runtime | Artifacts exposed through MCP resources |

Client configs under `.claude/`, `.cursor/`, `.codex/`, `.gemini/` and `.codeium/` launch `uv run bikescout` with no `ORS_API_KEY` override, so the gitignored `.env` supplies the key. Deployments may override the command locally; the harness setup is in `AGENTS.md` §6.

## 6. Dependency and version policy

- Dependencies use minimum-version constraints (`>=`) in `pyproject.toml`; only `test` and `dev` extras exist.
- Adding/upgrading a dependency, adding an extra, or changing a provider endpoint requires approval per `AGENTS.md` §2.
- `uv.lock` and `.venv/` are git-ignored; `ruff` and `pyright` configuration lives in `pyproject.toml` (DR-09 resolved). Do not introduce a third config location for these tools without updating `PROCESS.md`.

## 7. Data credits

Routing and POI data: ORS-compatible API provided by HeiGIT. Places: OpenStreetMap contributors (ODbL) via Nominatim. Weather: Open-Meteo (CC BY 4.0). Preserve these attributions in public-facing material as described in `BRAND.md` §8.
