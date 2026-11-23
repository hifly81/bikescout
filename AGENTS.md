# AGENTS.md

This file provides operational instructions for AI agents and developers working on the **BikeScout** repository.

## Project

BikeScout is an open-source AI engine for MTB, gravel, road and e-bike route planning. It turns raw map data into "Tactical Intelligence": terrain condition prediction, risk analysis, bike setup advice, and GPX generation.

- License: AGPL-3.0-only
- Language: Python >= 3.10
- Source package: `src/bikescout`
- MCP server (FastMCP): `src/bikescout/mcp_server.py`
- GUI: Streamlit (`src/bikescout/app.py`)
- Tests: `pytest` in `src/bikescout/tests`
- Coding standards: `docs/CODE_STANDARDS.md`

## Tech stack (from pyproject.toml)

Main dependencies: `fastmcp`, `requests`, `pydantic`, `streamlit`, `matplotlib`, `numpy`, `gpxpy`, `geopy`, `staticmap`, `pillow`, `fpdf`, `astral`, `timezonefinder`, `polyline`, `watchdog`, `huggingface_hub`, `llama-cpp-python`.

## Repository structure

```
bikescout/
├── AGENTS.md                 # this file (instructions for AI agents)
├── README.md                 # user guide and contributing
├── docs/CODE_STANDARDS.md    # detailed coding standards
├── pyproject.toml            # metadata, dependencies, pytest/coverage config
├── Dockerfile / docker-compose.yml
├── src/
│   └── bikescout/
│       ├── __init__.py
│       ├── app.py              # Streamlit GUI
│       ├── app_helpers.py
│       ├── app_ui_helpers.py
│       ├── config.toml         # Streamlit theme
│       ├── mcp_server.py       # MCP server + tool registration
│       ├── schemas.py          # Pydantic request/response models
│       └── tools/
│           ├── __init__.py
│           ├── surface.py      # example: surface/route analysis
│           ├── weather.py, geocoding.py, mud.py, ...  # domain tools
│           └── race/           # race analysis
│       └── tests/
│           ├── conftest.py     # shared pytest fixtures
│           ├── test_*.py       # tests for each tool
│           └── race/
├── scripts/                  # release, changelog, maintenance scripts
├── demo/                     # demos (ignored by git)
├── dist/                     # builds (ignored by git)
├── models/                   # ML models (ignored by git)
└── venv/                     # environment (ignored by git)
```

## Environment variables

Create a `.env` file (not versioned) from `.env.example`. The key variable is:

- `ORS_API_KEY` — OpenRouteService API key required for routing and surface analysis.

## How to start the project

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install dependencies (editable mode)
pip install -e .

# 3. Configure environment variables
cp .env.example .env
# edit .env and insert ORS_API_KEY

# 4. Start the MCP server
bikescout   # entry point declared in pyproject.toml

# 5. Or start the Streamlit GUI
streamlit run src/bikescout/app.py
```

Note: `src/` is not a standalone package; `pyproject.toml` declares `packages = ["src/bikescout"]` and tests use `pythonpath = ["src"]`.

## How to run tests

```bash
pytest
# or explicitly setting the pythonpath:
PYTHONPATH=src pytest src/bikescout/tests
```

Tests live in `src/bikescout/tests/`, with one file per tool module (e.g. `test_surface.py`) and shared fixtures in `conftest.py`. `asyncio_mode = auto`.

## How to add a new MCP tool

1. Create `src/bikescout/tools/<tool_name>.py` following `docs/CODE_STANDARDS.md`.
2. Define input/output schemas in `src/bikescout/schemas.py` (Pydantic v2) if they do not exist yet.
3. Implement the logic in the tool module using the pattern already present in the repo:
   - service class (e.g. `SurfaceAnalyzerService`) with injectable dependencies in the constructor;
   - module-level global instance (e.g. `service = SurfaceAnalyzerService()`);
   - public wrapper function (e.g. `get_surface_analyzer(...)`) that delegates to the instance.
4. Register the tool in `src/bikescout/mcp_server.py` with the `@mcp.tool()` decorator.
5. Add tests in `src/bikescout/tests/tools/test_<tool_name>.py`.
6. Document an example query in `README.md` (Example Queries section) if relevant to users.
7. Open a PR with a conventional commit, e.g. `feat(tools): add <tool_name>`.

## Coding conventions

See `docs/CODE_STANDARDS.md`. Summary:

- Comments and docstrings in **English** (international collaboration).
- Every Python file starts with the AGPLv3 license header (see `src/bikescout/mcp_server.py`).
- `from __future__ import annotations` at the top of modules.
- Type hints on all public functions; modern generic syntax (`list[...]`, `dict[...]`).
- `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants, `_` prefix for privates.
- Google-style docstrings (`Args:`, `Returns:`).
- Error handling with `try/except` and returning dictionaries like `{"status": "Error", "message": ...}`; avoid `print`.
- Tests are mandatory for every new tool with `pytest`.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/) with scope, as in the repo history:

- `feat(tools): ...`
- `fix(analysis): ...`
- `refactor(chat): ...`
- `race: ...`

## License and contributions

AGPL-3.0-only. By contributing you agree that your code is released under this license. See `README.md` → Contributing and `LICENSE`.
