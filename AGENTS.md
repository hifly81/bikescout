# AGENTS.md — BikeScout agent harness

Authoritative entry point for humans and AI agents working on **BikeScout** (AGPL-3.0-only, Python >= 3.10). This file defines the reading contract, decision rights, verification gates and handoff format. Product intent lives in `docs/SPEC.md`; current behavior is defined by the code.

## 0. Precedence and drift rule

- **Product intent:** `docs/SPEC.md` (what) and `docs/BRAND.md` (voice, terms, visual identity).
- **Build and verification rules:** `docs/CODE_STANDARDS.md` and `docs/PROCESS.md`.
- **Current behavior:** code and configuration are ground truth when documentation disagrees with them.
- If two documents conflict, or docs conflict with code: **stop, do not guess**. Record the conflict in the *Drift register* in `docs/PROCESS.md` and ask the owner when the resolution would change public behavior, schemas or state contracts. Doc-only corrections that align text with verified code may be applied in place and reported in the handoff.

## 1. Bootstrap — read before acting

Before planning, building, changing code or docs, or answering product questions, read these in full:

1. `docs/SPEC.md` — business needs and acceptance criteria.
2. `docs/TECH_STACK.md` — architecture, runtime modes, tool surface, configuration.
3. `docs/CODE_STANDARDS.md` — how to write code.
4. `docs/PROCESS.md` — task lifecycle, quality gates, MCP invocation contract.
5. `docs/BRAND.md` — mandatory for user-facing copy, naming and UI work.

Load progressively, only when relevant:

- `.agents/skills/<name>/SKILL.md` for a matching domain persona. Skills are optional guidance and never override this file.
- The MCP client config for your host (`.claude/`, `.cursor/`, `.codex/`, `.gemini/`, `.codeium/`). These now launch `uv run bikescout`; `ORS_API_KEY` must come from the local, untracked `.env`, never from committed config.
- `README.md` for public examples and data credits.

## 2. Classify the task (decision rights)

| Class | Examples | Authority |
| :--- | :--- | :--- |
| Routine | Bugfix, test, doc typo, copy consistent with `BRAND.md` | Proceed; run the gates in §4 |
| Public contract | `pyproject.toml` dependencies, `schemas.py` models/tool names/parameters, Streamlit session or mission state, provider endpoints | **Ask first** — do not change unilaterally |
| Ambiguous behavior | Conflicting docs, complexity ranges, overlay defaults | **Stop** and open a drift entry |
| Forbidden | Secrets, ignored/generated directories, `git push`, `--no-verify`, forced `chat_format` | **Never** |

## 3. Operating loop

1. **Read** (§1) and **classify** (§2).
2. **Plan:** state affected files, contracts touched, and required gates in one short message.
3. **Implement** the smallest coherent change; keep docs in sync with behavior.
4. **Verify** with §4; fix failures rather than weakening gates.
5. **Report** with §9.

No task is "done" without executed gates and a handoff report. Do not expand scope silently.

## 4. Verification gates

| Change | Required checks |
| :--- | :--- |
| Python under `src/` | `uv run ruff check --fix <files>`, `uv run ruff format <files>`, `uv run pyright`, `uv run pytest --cov=src/bikescout --cov-fail-under=80` |
| Any code commit | `git add ...` then `uv run lefthook run pre-commit` (or a clean `git commit` without `--no-verify`); never push |
| MCP tool / schema | Python gates + verify tool registration, parameters and return model in `mcp_server.py` / `schemas.py` + tests for new behavior |
| Streamlit UI / session state | Python gates + manual smoke: `uv run streamlit run src/bikescout/app.py` |
| Docs only | Check every referenced path, tool name and parameter against the code; update cross-references. Python gates only if code was touched |
| User-facing copy | `docs/BRAND.md` checklist + verify terminology against the glossary |

Lefthook runs lint, format, type and test gates on staged `src/**/*.py`. Keep the working tree green; never bypass the hook. Current status: all four gates pass — ruff, format, `pyright` (0 errors) and pytest (547 tests, 88% coverage). DR-12 in `PROCESS.md` records how the pre-existing type debt was cleared without weakening the gate or adding blanket ignores.

## 5. Boundaries

**Always**

- Use the `uv`-based environment from §6 for development gates; keep `PYTHONPATH=src` in mind for ad-hoc scripts.
- Use English for code comments, docstrings, identifiers and error messages; follow `docs/BRAND.md` for user-facing wording.
- Run relevant `pytest` tests after code changes; tests use stubs/fakes, never a live GGUF model or live HTTP.
- Update the affected docs in the same change when behavior, tools or contracts change.

**Ask first**

- Adding or upgrading dependencies in `pyproject.toml`.
- Changing public tool schemas in `src/bikescout/schemas.py`, tool/resource names or parameters.
- Altering Streamlit session/mission state contracts or external provider endpoints.
- Renaming/deleting harness docs, or changing brand identity (wordmark, palette, tagline).

**Never**

- Commit secrets, `.env` or API keys in client configs.
- Modify generated/ignored directories (`models/`, `dist/`, `venv/`, `demo/`, `scripts/`, `.agents/skills/developing-with-streamlit`).
- Force `chat_format` in `Llama(...)` unless a model's chat template explicitly requires it.
- Use `git commit --no-verify` or push.
- Fabricate route metrics, elevation, mud risk, nutrition values or GPX data when a tool fails or data is missing.

## 6. Setup, run and test (canonical `uv`)

```bash
uv sync --extra test --extra dev
uv run lefthook install
cp .env.example .env          # set ORS_API_KEY; never commit .env

uv run bikescout                              # FastMCP stdio server (default)
BIKESCOUT_TRANSPORT=sse uv run bikescout       # optional SSE (BIKESCOUT_HOST/PORT)
uv run streamlit run src/bikescout/app.py     # tactical UI + local planner
uv run pytest                                 # full suite
```

A plain `venv` + `pip install -e .` is enough to run the apps, but **not** to run the quality gates: the `test` and `dev` extras are not installed that way. Use `uv` for all verification.

## 7. Repo map and entry points

- `src/bikescout/mcp_server.py` — `FastMCP("BikeScout")`; tools: `geocode_location`, `trail_scout`, `trail_scout_simple` (unified orchestrator), `check_trail_weather`, `ride_window_planner`, `hydration_scout`, `analyze_gpx_track`; resources `bikescout://{altimetry,maps,gpx}/{filename}` read from `~/.bikescout`.
- `src/bikescout/app.py` — Streamlit page composition and mission orchestration; `app_helpers.py` — session defaults and intent normalization; `app_llm.py` — LangChain adapter, model catalog, cached loader and tactical prompt chain; `app_ui_helpers.py` — reusable renderers and CSS design tokens.
- `src/bikescout/schemas.py` — Pydantic v2 contracts; tool-facing inputs `RiderProfile`, `BikeSetup`, `MissionConstraints` and six response models.
- `src/bikescout/tools/` — stateless domain services; ORS-compatible routing/POI (HeiGIT), weather, offline terrain truth, GPX/map/altimetry exports.
- `src/bikescout/tests/` — pytest suite (`asyncio_mode = auto`, `pythonpath = ["src"]`) with stub LLM and fake HTTP sessions; no live model/network.
- `src/bikescout/config.toml` — Streamlit theme; `models/` — ignored local GGUF cache; `~/.bikescout` — generated artifacts.
- `docs/` — this harness's documentation set; `.agents/skills/` — optional domain personas; `site/` — public website (separate visual tokens, see `BRAND.md`).

## 8. Domain and LLM gotchas

- **GGUF / `llama-cpp-python`:** rely on GGUF metadata chat templates; never hardcode `chat_format`.
- **Structured JSON:** the planner passes a local `json_schema` payload (`"type": "json_object"`) with `temperature=0.0`, `max_tokens=1024`; disable thinking on Qwen3.5 via `chat_template_kwargs={"enable_thinking": False}` so `<think>` blocks do not exhaust tokens or pollute JSON.
- **Overlays:** MCP tools use the seven `include_*` flags; the guided form emits short keys (`include_mud`, `include_nutrition`) mapped in `execute_plan_request`; the planner uses `wants_overlay` from `app_helpers.py`. Explicit user requests must never be silently overridden by bike-type defaults.
- **Complexity:** the planner UI treats it as difficulty `1–5`, while `MissionConstraints.complexity` is a waypoint count `3–10` (alias `points`). `difficulty_to_waypoints()` maps UI values to `3–5` at both UI→tool boundaries; never pass `1–2` to `trail_scout_simple` (DR-02 resolved).
- **Caching:** `@st.cache_resource` caches loaded `Llama` instances; account for VRAM/reload when switching models.

## 9. Git conventions and handoff

Use Conventional Commits with scope, e.g. `feat(tools): ...`, `fix(planner): ...`, `refactor(chat): ...`, `docs(harness): ...`, `chore(release): ...`.

End every task with a short report:

1. Changed files and why.
2. Commands executed and results.
3. Contracts touched (and approval, if required).
4. Residual risks / drift entries opened.
5. Follow-ups deliberately not done.
