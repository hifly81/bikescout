# CODE_STANDARDS.md — BikeScout code standards

Normative for new and modified Python code under `src/bikescout`. Some existing files predate these rules; see drift entry DR-08 in `PROCESS.md`. New code and touched code must comply — do not mass-reformat unrelated files without approval.

## 1. License header and file scope

Every Python file must start with the standard 15-line AGPLv3 header, as in `src/bikescout/mcp_server.py`:

```python
# BikeScout - Tactical Intelligence for Cyclists
# Copyright (C) 2026 hifly81 (https://github.com/hifly81/bikescout)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
```

## 2. Language of the code

- Comments, docstrings, variable names and error messages: **English**.
- Documentation files may be Italian or English, but keep one language per file; the current harness docs are English.
- User-facing copy follows `BRAND.md` for voice, terminology, units and capitalization.

## 3. Versions and imports

- Python >= 3.10.
- Start every module with `from __future__ import annotations` (after the license header).
- Import order (PEP 8): standard library → third-party (`numpy`, `requests`, `pydantic`, `fastmcp`, ...) → local package (`bikescout.*`), separated by blank lines.
- Use absolute imports (`from bikescout.tools.mud import ...`); never relative imports.
- Keep `PYTHONPATH=src` in mind for ad-hoc scripts; `uv run` and pytest already configure it.

## 4. Type hints

- Mandatory on all parameters and return values of public functions.
- Use PEP 585/604 syntax: `list[str]`, `dict[str, Any]`, `tuple[str, ...]`, `str | None`. `typing.Optional`, `Literal` and `Any` remain available where clearer.
- Avoid implicit `None` defaults on non-optional types.

```python
from typing import Any

def get_surface_analyzer(
    api_key: str,
    lat: float,
    lon: float,
    rider: RiderProfile,
    bike: BikeSetup,
    mission: MissionConstraints,
    target_date: str | None = None,
) -> dict[str, Any]:
    ...
```

## 5. Naming conventions

| Element | Convention | Example |
| :--- | :--- | :--- |
| Modules | `snake_case` | `surface.py`, `bike_setup.py` |
| Functions / methods | `snake_case` | `get_surface_analyzer`, `_safe_complexity` |
| Variables / arguments | `snake_case` | `clean_ascent`, `real_dist_m` |
| Classes | `PascalCase` | `SurfaceAnalyzerService`, `SurfaceAnalyzerConfig` |
| Module constants | `UPPER_CASE` | `BIKESCOUT_PROTOCOL_VERSION` |
| Private members | `_` prefix | `_sanitize_elevation_profile` |

## 6. Docstrings

- Google style with `Args:` and `Returns:` sections; document behavior, parameters and return value.

```python
def geocode_location(location_name: str, language: str = "en") -> GeocodingResponse:
    """
    Finds latitude and longitude for any place name (city, mountain pass, address).
    Use this BEFORE other tools if you only have a location name and not coordinates.

    Args:
        location_name: Natural language name of the location (e.g., "Stelvio Pass").
        language: Accept-Language header, e.g. en,it,fr,es.

    Returns:
        GeocodingResponse with precise lat/lon for routing and the display name.
    """
```

- **MCP tool docstrings are agent-facing API documentation.** Every documented parameter must exist in the tool signature; describe defaults and the exact semantics of `include_*` flags. Do not advertise removed or nonexistent parameters (see DR-03).
- Keep tool descriptions aligned with the parameter table in `PROCESS.md` §4.3 and with `site/documentation/api-reference.html`.

## 7. MCP tool pattern

1. Service class (e.g. `SurfaceAnalyzerService`) with injectable dependencies in the constructor, falling back to real functions.
2. Module-level instance (`service = SurfaceAnalyzerService()`).
3. Public wrapper function (e.g. `get_surface_analyzer(...)`) delegating to the instance.
4. Return a Pydantic model or a dictionary with `status`: `"Success"` or `"Error"`; error payloads include `message`.
5. Register new tools in `src/bikescout/mcp_server.py`; add Pydantic schemas in `schemas.py` only with approval (`AGENTS.md` §2).
6. No `print` for diagnostics; use logging/tracebacks server-side and return structured results to clients.

## 8. Error handling

- Wrap network calls and JSON parsing in `try/except`; catch specific exceptions, never bare `except`.
- Never let an unhandled exception reach the MCP client; return `{"status": "Error", "message": ...}` or a structured error model.
- Use safe defaults (`getattr(obj, "attr", default)`) for possibly missing fields.
- Never invent route metrics, elevation, mud risk, nutrition values or GPX data when a dependency fails. State the failure and, when possible, a next step.

## 9. Configuration

- Use `frozen=True` dataclasses for configuration objects (e.g. `SurfaceAnalyzerConfig`).
- Read secrets from `.env` / environment via `python-dotenv`; never hardcode keys.
- Streamlit theme lives in `src/bikescout/config.toml`; visual tokens are defined in `BRAND.md`.

## 10. Tests

- Framework: `pytest` (`pythonpath = ["src"]`, `testpaths = ["src/bikescout/tests"]`, `asyncio_mode = "auto"`).
- Layout: one test file per module under `src/bikescout/tests/tools/`, plus `tests/tools/race/` and UI tests at the suite root; shared fixtures in `src/bikescout/tests/conftest.py`.
- Use stub LLMs (`StubLLM`) and fake HTTP sessions (`FakeSession`); never call a live GGUF model or live external API.
- Add tests with every behavior change; the pre-commit gate requires at least **80% coverage** (`uv run pytest --cov=src/bikescout --cov-fail-under=80`).
- Run from the project root with `uv run pytest`.

## 11. Formatting and linting

- PEP 8 baseline; recommended maximum line length 100 characters.
- Four spaces for indentation, no tabs; one blank line between top-level functions, two between classes.
- `ruff check --fix` and `ruff format` run on staged `src/**/*.py` via Lefthook; `pyright` type-checks the project. Do not add a competing formatter config without updating `PROCESS.md` (DR-09).

## 12. Schema and state evolution

- Public Pydantic schemas, MCP tool signatures/resources, and Streamlit session/mission state keys require approval before modification (`AGENTS.md` §2).
- When a schema or MCP tool signature changes, update `PROCESS.md` §4.3, `TECH_STACK.md` §3, `site/documentation/api-reference.html` and the tests in the same change.
- `src/bikescout/tests/test_api_reference_docs.py` is the automated consistency gate: it compares HTML fields, defaults and `Literal` choices with the Pydantic models, and tool names, parameters, defaults and return models with FastMCP. Run `uv run pytest src/bikescout/tests/test_api_reference_docs.py` after touching `mcp_server.py` or `schemas.py`; fix the HTML, not the assertions.
- Keep natural-language docs and tool docstrings in sync with the actual field names (`total_length_km`, not `target_distance_km`; no `route_mode` on `trail_scout_simple`).

## 13. Commits

Use Conventional Commits with scope, consistent with the repo history:

```text
feat(tools): add surface analysis
fix(analysis): add fallbacks for route-based GPX parsing
refactor(chat): extract shared plan execution helpers
docs(harness): align process with MCP tool signatures
```

Typical scopes: `tools`, `analysis`, `chat`, `ui`, `race`, `deps`, `docs`.

## 14. What to avoid

- `print` statements in production code; relative imports; commented-out code; bare `except`.
- Magic numbers without a named constant; undocumented defaults; fabricated data on failure.
- Hardcoded `chat_format`; live model/HTTP calls in tests; secrets in code or docs.
- Documentation of parameters that do not exist in the tool signature.
