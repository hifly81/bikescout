# PROCESS.md — Delivery process and agent operating contract

Normative workflow. `AGENTS.md` is the entry point and defines decision rights; this file defines how work is planned, verified and invoked.

## 1. Bootstrap (once per workspace)

```bash
uv sync --extra test --extra dev
uv run lefthook install
cp .env.example .env          # set ORS_API_KEY; never commit .env
```

`test` provides pytest/pytest-cov/pytest-asyncio; `dev` provides lefthook/ruff/pyright. These are the only two extras in `pyproject.toml`. A plain `venv` + `pip install -e .` runs the apps but cannot run the quality gates. There is no committed lockfile yet (DR-09).

## 2. Task lifecycle

| Step | Action |
| :--- | :--- |
| 1. Intake | Classify the task per `AGENTS.md` §2; read the bootstrap docs in full; identify touched contracts |
| 2. Plan | State affected files, contracts and gates in one short message before editing |
| 3. Implement | Smallest coherent change; English in code; `BRAND.md` for user-facing copy; docs updated with behavior |
| 4. Verify | Run the gates in §3; fix failures instead of weakening the gates |
| 5. Report | Handoff per `AGENTS.md` §9; open drift entries for unresolved conflicts |

**Definition of done:**

- [ ] All applicable gates are green and the commands/results are recorded in the handoff.
- [ ] Tests cover new behavior with stubs/fakes; no live model or HTTP calls.
- [ ] `SPEC.md` traceability, `TECH_STACK.md` inventory and this file's parameter table still match the code.
- [ ] `BRAND.md` checklist satisfied for user-facing copy.
- [ ] No secrets, ignored files or contract changes without approval.
- [ ] Drift registered or resolved; no silent scope expansion.

## 3. Quality gates

`lefthook.yml` runs a piped `python` job on staged `src/**/*.py` (`glob_matcher: doublestar`) with these exact commands:

```bash
uv run ruff check --fix <staged_files>       # stage_fixed: true
uv run ruff format <staged_files>            # stage_fixed: true
uv run pyright
uv run pytest --cov=src/bikescout --cov-fail-under=80
```

- Explicit agent check before finishing a code task: `git add ... && uv run lefthook run pre-commit`.
- Never use `git commit --no-verify`; never push.
- Docs-only changes: verify paths, tool names and parameters against the code; Python gates only if code was touched. There is no automated docs-consistency test yet.

## 4. MCP invocation contract (agent hosts)

### 4.1 Prerequisites

- Server entry point: `bikescout` (FastMCP stdio by default; SSE via `BIKESCOUT_TRANSPORT=sse`).
- Host configs in `.claude/`, `.cursor/`, `.codex/`, `.gemini/`, `.codeium/` launch `uv run bikescout` and carry no key override; `ORS_API_KEY` is read from the local, untracked `.env` per `AGENTS.md` §6.
- `ORS_API_KEY` must be available to the server before routing, geocoding or POI calls.

### 4.2 Workflow

1. **Resolve coordinates first:** if the user supplies a place name, call `geocode_location` to obtain `latitude`/`longitude` (and `dest_latitude`/`dest_longitude` for an A-to-B mission) before route synthesis.
2. **Primary mission tool:** use `trail_scout_simple`, the unified orchestrator, for route generation and overlays. `trail_scout` remains available for typed `RiderProfile`/`BikeSetup`/`MissionConstraints` inputs.
3. **Preserve multi-turn context:** on follow-ups (e.g. "make it harder", "add mud analysis", "shift it south"), retain prior coordinates, bike type, tire size and routing biases unless explicitly overridden.
4. **Never fabricate** metrics or artifacts when a tool returns an error; adjust inputs or ask the user.

### 4.3 Parameter mapping and normalization

Agents normalize natural-language constraints to the exact typed parameters in `src/bikescout/schemas.py` and `mcp_server.py`.

| Parameter | Allowed values / type | Mapping rule |
| :--- | :--- | :--- |
| `bike_type` | Canonical lowercase `"mtb"`, `"road"`, `"gravel"`, `"e-mtb"`, `"enduro"` (the schema also accepts capitalized variants) | Infer `"mtb"` if only `29"`/`27.5"` wheels are given; set `is_ebike=true` for `"e-mtb"` |
| `profile` | Both the schema and the planner enum accept `"cycling-mountain"`, `"cycling-road"`, `"cycling-regular"`, `"cycling-electric"` (DR-04) | `road`/`gravel` → `cycling-road` (technical gravel → `cycling-mountain`); `mtb`/`enduro` → `cycling-mountain`; `e-mtb` → `cycling-electric`; `resolve_profile()` still derives the value from bike type |
| `complexity` | Planner UI encodes difficulty `1–5`; `MissionConstraints.complexity` is a **waypoint count** `3–10` (alias `points`) | UI→tool boundaries use `difficulty_to_waypoints()` (1–3 → 3, 4 → 4, 5 → 5); for direct MCP calls pass `3–10` as a waypoint count, never `1–2` |
| Point-to-point | No `route_mode` parameter on the MCP tool | Supply both `dest_latitude` and `dest_longitude`; otherwise a round trip is generated. The UI plan request may carry `route_mode`, which is mapped to coordinates |
| Distance | `total_length_km` | Use this name; `target_distance_km` is not a parameter (DR-03 resolved) |
| `direction_bias` | `list[str]` of `"north"`, `"south"`, `"east"`, `"west"` | `"south-east"` → `["south", "east"]` |
| `avoid_urban` / `prefer_rural` | `boolean` | Set `true` when the user wants quiet countryside or no city traffic; combine with `priority_mode="ride_character_first"` and an MTB/enduro/e-MTB `bike_type` for off-road candidate ranking (DR-06 resolved) |
| `priority_mode`, `distance_flex_percent` | `"balanced"`, `"distance_first"`, `"ride_character_first"`; `0–30` | Use `10–20` for approximate distances ("about", "more or less"); use `0` with `distance_first` for exact mileage |
| `include_*` flags | `include_weather`, `include_mud_analysis`, `include_nutrition_plan`, `include_poi`, `include_gpx`, `include_map`, `include_altimetry` | Set explicitly to `true` when requested, regardless of bike type; MCP mud default is `false`, so non-road defaults must be requested explicitly. The guided form emits `include_mud`/`include_nutrition`, mapped in `execute_plan_request`; the local planner uses `wants_overlay` from `app_helpers.py` and forces `include_map`, `include_weather`, `include_altimetry` to `true` |

### 4.4 Local GGUF planner (`app.py`)

- Supported models: `Qwen3.5-9B`, `Ministral-3-8B-Instruct`, `Qwen2.5-7B-Instruct` in the ignored `models/` directory.
- Calls use `response_format=json_schema` (a local payload whose declared type is `"json_object"`), `temperature=0.0`, `max_tokens=1024`.
- On reasoning models (`Qwen3.5`), `chat_template_kwargs={"enable_thinking": False}` must stay enabled; `<think>` blocks would consume tokens and corrupt JSON fields.
- Never override `chat_format` in `Llama(...)`; rely on the GGUF metadata template.
- `@st.cache_resource` caches loaded `Llama` instances; account for VRAM/reloads when switching models.
- `app_llm.py` wraps the cached `Llama` in a `BaseChatModel` (`LlamaChatModel`) and exposes the turn as an LCEL chain (`prompt | model | StrOutputParser`). The system prompt is injected as a message so JSON braces in the active mission snapshot are not parsed as template fields.
- History conversion keeps the UI placeholder filter and the last six turns. Session/mission state keys and the deterministic `process_local_mcp_request` tool dispatch are unchanged; no autonomous LangChain agent is introduced.

### 4.5 Response and error contract

- Tools return `{"status": "Success" | "Error", ...}` or a Pydantic response model.
- On `"Error"`, inspect `message` (geocoding ambiguity, missing `ORS_API_KEY`, infeasible constraints), adjust parameters or ask the user; never invent route data.
- Report estimates as estimates, with their inputs, following `BRAND.md` §2.

## 5. Docs and brand maintenance

Behavior changes must be reflected in the same change: `SPEC.md` (intent + traceability), `TECH_STACK.md` (tool inventory/config), `CODE_STANDARDS.md` (rules), this file (parameter tables), `BRAND.md` (new terms or visual tokens) and `README.md` (public examples). Do not change a public schema or session/mission contract to make documentation look correct — open a drift entry instead.

## 6. Drift register

Entries record verified conflicts between docs, configs and code. Agents must not resolve behavioral drift incidentally; propose a fix and wait for approval when public behavior is involved.

| ID | Observation (evidence) | Status | Action needed |
| :--- | :--- | :--- | :--- |
| DR-01 | `AGENTS.md` documented venv/pip while `PROCESS.md` mandated `uv` with extras | Resolved in this revision | Canonical `uv` setup in `AGENTS.md` §6 and §1; venv/pip is runtime-only |
| DR-02 | Planner encodes complexity as difficulty `1–5` but `MissionConstraints.complexity` is a waypoint count `3–10` (alias `points`) | Resolved at the UI boundary | `difficulty_to_waypoints()` maps 1–3 → 3, 4 → 4, 5 → 5; public schema unchanged; tests cover the mapping |
| DR-03 | `route_mode` / `target_distance_km` were documented as tool parameters | Resolved | Tool docstrings now use `total_length_km`, drop the invalid `target_date` note, and describe the real waypoint semantics; `route_mode` stays a UI-only key |
| DR-04 | `profile` accepted `cycling-regular` in the schema but not in the planner enum | Resolved | Planner enum now exposes all four schema values; `resolve_profile()` still derives it from bike type |
| DR-05 | Overlay defaults/keys differ by surface | Documented — intentional layering | Preserve explicit-request precedence in all layers |
| DR-06 | Off-road ranking read `mission.bike_type`, absent from `MissionConstraints` | Resolved | `_prefers_offroad()` now reads `BikeSetup.bike_type`; ranking and metadata work on real missions; regression test added |
| DR-07 | Skills referenced unregistered tools and `trail_scout` instead of the orchestrator | Resolved | All skills now use the seven registered tools, `trail_scout_simple` for scalar intents, and `info.surface_analysis.mechanical_setup` for tire setup |
| DR-08 | Python files missing the AGPL header / `from __future__ import annotations` | Resolved | All 44 files under `src/bikescout` now comply; `compileall` passes |
| DR-09 | No `ruff`/`pyright` config; `uv.lock` ignored by a leading-space pattern; `.venv/` not ignored | Resolved | Config added to `pyproject.toml`; `uv.lock` and `.venv/` correctly ignored |
| DR-10 | Palette divergence between `config.toml`, app CSS and site | Resolved by alignment | Streamlit primary is now `#7c3aed`, matching app CSS; site `#bef264` remains intentionally surface-specific |
| DR-11 | Host configs used `/app/...` paths and placeholder keys; README had a broken push instruction | Resolved | Host configs launch `uv run bikescout` with no key override; README fixes the push command and states agents never push |
| DR-12 | `uv run pyright` reported 175 pre-existing errors (65 production, 110 tests) once a deterministic config exists; implicit `None` defaults, missing return types, narrowing external dependencies to concrete classes, and `SimpleNamespace` test fakes | Resolved | Gate is green: `pyright` 0 errors, ruff/format clean, 547 tests at 88% coverage. Internal signatures now use accurate annotations (`target_date: str \| None`, `dict[str, Any]` returns); public MCP tool schemas are unchanged. Test doubles and deliberately invalid inputs use localized `cast(Any, ...)`; no blanket ignores and no weakened gate |

To open an entry: add a short row with the conflicting sources, mark status `Open`, and reference it from the handoff. Do not delete entries without resolving the underlying conflict.
