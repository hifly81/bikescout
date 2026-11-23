# PROCESS.md

AI agents interacting with BikeScout MUST follow these execution rules when translating user intent into tool invocations:

## 1.1 MCP Connection & Prerequisites
- **Server Entry Point:** `bikescout` (FastMCP stdio server defined in `src/bikescout/mcp_server.py`).
- **Client Configuration Locations:**
  - Claude Code: `.claude/settings.json`
  - Gemini Antigravity: `.gemini/antigravity/mcp_config.json`
  - Cursor: `.cursor/mcp.json`
  - Windsurf: `.codeium/windsurf/mcp_config.json`
  - Codex CLI: `.codex/config.toml`
- **Required Environment Variable:** `ORS_API_KEY` must be active in the server environment before invoking routing or geocoding tools.

## 1.2 Standard Tool Invocation Workflow
1. **Resolve Coordinates First:** If the user provides a place name rather than coordinates, resolve `latitude` and `longitude` (and `dest_latitude` / `dest_longitude` for `point_to_point` missions) via the geocoding tool before invoking route synthesis.
2. **Primary Mission Tool (`trail_scout_simple`):** Use `trail_scout_simple` as the unified orchestrator for route generation and tactical overlays.
3. **Preserve Multi-Turn Mission Context:** On follow-up requests (e.g., *"make it harder"*, *"add mud analysis"*, *"shift it south"*), retain prior `latitude`, `longitude`, `bike_type`, `tire_size`, and routing biases unless explicitly overridden by the user.

## 1.3 Parameter Mapping & Normalization Rules
Agents MUST normalize natural-language user constraints into the exact typed parameters expected by BikeScout schemas (`src/bikescout/schemas.py`):

| Parameter | Allowed Values / Type | Agent Mapping Rule |
| :--- | :--- | :--- |
| `bike_type` | `"mtb"`, `"road"`, `"gravel"`, `"e-mtb"`, `"enduro"` | Infer `"mtb"` if user specifies `29"` or `27.5"` wheels without naming a discipline; set `is_ebike=true` when `bike_type="e-mtb"`. |
| `profile` | `"cycling-mountain"`, `"cycling-road"`, `"cycling-electric"` | Map `"road"`/`"gravel"` $\rightarrow$ `"cycling-road"` (or `"cycling-mountain"` for technical gravel), `"mtb"`/`"enduro"` $\rightarrow$ `"cycling-mountain"`, `"e-mtb"` $\rightarrow$ `"cycling-electric"`. |
| `complexity` | `integer` (`1`–`5`, default `3`) | Map difficulty cues (`easy`=1–2, `moderate`=3, `hard`=4, `very hard`/`extreme`=5). |
| `route_mode` | `"round_trip"`, `"point_to_point"` | Use `"point_to_point"` only when both origin and destination are specified; otherwise `"round_trip"` with `total_length_km` / `distance`. |
| `direction_bias` | `list[str]` (`"north"`, `"south"`, `"east"`, `"west"`) | Extract cardinal/intercardinal constraints (e.g., *"south-east"* $\rightarrow$ `["south", "east"]`). |
| `avoid_urban` / `prefer_rural` | `boolean` | Set `true` when user requests avoiding city traffic or preferring countryside/quiet roads. |
| `priority_mode` & `distance_flex_percent` | `"balanced"`, `"distance_first"`, `"ride_character_first"`; `0`–`30` | Set `distance_flex_percent` (`10`–`20`) when user specifies approximate distance (*"more or less"*, *"about"*); set `0` with `"distance_first"` when exact mileage is requested. |
| `include_*` flags | `boolean` (`include_weather`, `include_mud_analysis`, `include_nutrition_plan`, `include_poi`, `include_gpx`, `include_map`, `include_altimetry`) | Explicitly set to `true` whenever requested by the user regardless of `bike_type` (do not let `bike_type == "road"` suppress an explicit `"mud"` request). Default `include_mud_analysis` to `true` for non-road disciplines. |

## 1.4 Local GGUF LLM Planner Integration (`app.py` / `llama-cpp-python`)
When operating via BikeScout's built-in local LLM planner instead of an external host LLM:
- **Supported Quantized Models:** `Qwen3.5-9B`, `Ministral-3-8B-Instruct`, `Qwen2.5-7B-Instruct` (stored in `models/`).
- **Grammar Enforcement:** Calls use `response_format=json_schema` at `temperature=0.0` to guarantee valid tool argument payloads.
- **Reasoning Suppression:** On reasoning-capable models (`Qwen3.5`), `chat_template_kwargs={"enable_thinking": False}` MUST remain enabled so `<think>` tokens do not exhaust `max_tokens` or corrupt JSON fields.
- **Chat Template Integrity:** Never override `chat_format` manually in `Llama(...)`; rely on native GGUF metadata templates.

## 1.5 Response & Error Handling Contract
- Every BikeScout tool returns a structured payload containing `"status": "Success"` or `"status": "Error"` with a diagnostic `"message"`.
- If `"status" == "Error"`, agents MUST inspect the error message (e.g., geocoding ambiguity, missing `ORS_API_KEY`, infeasible distance/terrain constraints), adjust parameters or prompt the user for clarification, and never fabricate route metrics, elevation gain, or GPX data.