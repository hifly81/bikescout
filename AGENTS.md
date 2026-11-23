# AGENTS.md

Operational guide for AI coding agents working on **BikeScout** (AGPL-3.0-only, Python >= 3.10).

## Boundaries

- **Always:** Keep `PYTHONPATH=src` in mind when running tests/scripts; follow `docs/CODE_STANDARDS.md`; run relevant `pytest` tests after code changes.
- **Ask first:** Adding or upgrading dependencies in `pyproject.toml`, changing public tool schemas in `src/bikescout/schemas.py`, or altering Streamlit session/mission state contracts.
- **Never:** Commit secrets or `.env`; modify generated/ignored directories (`models/`, `dist/`, `venv/`, `demo/`); force `chat_format` in `Llama(...)` unless explicitly required by a model's chat template.

## Key entry points & layout

- `src/bikescout/mcp_server.py` — FastMCP server and `@mcp.tool()` registrations.
- `src/bikescout/app.py`, `app_helpers.py`, `app_ui_helpers.py` — Streamlit GUI, local GGUF downloader/loader, and chat planner.
- `src/bikescout/schemas.py` — Pydantic v2 models.
- `src/bikescout/tools/` — Domain tools (`surface.py`, `weather.py`, `geocoding.py`, `mud.py`, `race/`, etc.).
- `src/bikescout/tests/` — `pytest` suite (`asyncio_mode = auto`, `pythonpath = ["src"]`).

## Setup, run & test

```bash
python -m venv venv && source venv/bin/activate
pip install -e .
cp .env.example .env   # set ORS_API_KEY

bikescout                           # start MCP server
streamlit run src/bikescout/app.py  # start Streamlit GUI
pytest                              # run test suite
```

## Adding a new MCP tool

1. Create `src/bikescout/tools/<tool_name>.py` with AGPLv3 header, `from __future__ import annotations`, Google-style docstrings, and `try/except` returning structured error dicts/models (no `print`).
2. Follow the repo service pattern: `<Name>Service` class with injectable dependencies, module-level `service = <Name>Service()`, and a public wrapper function delegating to `service`.
3. Add Pydantic v2 schemas in `src/bikescout/schemas.py` if needed, and register the tool in `src/bikescout/mcp_server.py`.
4. Add unit/async tests under `src/bikescout/tests/` and update `README.md` example queries if user-facing.

## Domain & LLM gotchas

- **GGUF + `llama-cpp-python`:** Newer model families require a compatible `llama-cpp-python` build; rely on GGUF metadata chat templates rather than hardcoding `chat_format`.
- **Structured JSON outputs (`response_format=json_schema`):** Disable thinking mode on reasoning models (such as `Qwen3.5` via `chat_template_kwargs={"enable_thinking": False}`) so `<think>` blocks do not consume `max_tokens` or pollute JSON fields.
- **Planner flags & overlays:** Keep option keys consistent across `generate_tactical_response`, `process_local_mcp_request` (`wants_overlay`), and `execute_plan_request` so explicit user requests are not silently overridden by bike-type defaults.
- **Streamlit model caching:** `@st.cache_resource` caches loaded `Llama` instances; account for VRAM/reloads when switching models.

## Git conventions

Use Conventional Commits with scope (e.g., `feat(tools): ...`, `fix(planner): ...`, `refactor(chat): ...`, `chore(release): ...`).