# Code Standards — BikeScout

Coding standards for the BikeScout project. They apply to all Python code under `src/bikescout`.

## 1. License and file header

Every Python file must start with the AGPLv3 license header (16 lines), as in `src/bikescout/mcp_server.py`:

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

- Comments, docstrings, variable names, and error messages: **English**.
- Documentation files (AGENTS.md, README.md, docs/) may be in Italian or English depending on the target audience.

## 3. Versions and imports

- Python >= 3.10.
- Start every module with `from __future__ import annotations`.
- Import order (PEP 8):
  1. standard library
  2. third-party libraries (e.g. `numpy`, `requests`, `pydantic`, `fastmcp`)
  3. local package imports (`bikescout.*`)
- Separate groups with a blank line. Use absolute imports (`from bikescout.tools.mud import ...`), never relative imports (`from . import ...`).

## 4. Type hints

- Type hints are mandatory on all parameters and return values of public functions.
- Use modern generic syntax (PEP 585, Python 3.10+): `list[str]`, `dict[str, int]`, `tuple[str, ...]`, instead of `typing.List`, `typing.Dict`.
- Use `typing.Optional[T]`, `typing.Literal[...]`, `typing.Any` when needed.
- Example:

```python
def get_surface_analyzer(
        api_key: str,
        lat: float,
        lon: float,
        rider: RiderProfile,
        bike: BikeSetup,
        mission: MissionConstraints,
        target_date: str = None,
) -> dict:
```

## 5. Naming conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | `snake_case` | `surface.py`, `bike_setup.py` |
| Functions / methods | `snake_case` | `get_surface_analyzer`, `_safe_complexity` |
| Variables / arguments | `snake_case` | `clean_ascent`, `real_dist_m` |
| Classes | `PascalCase` | `SurfaceAnalyzerService`, `SurfaceAnalyzerConfig` |
| Module constants | `UPPER_CASE` | `BIKESCOUT_PROTOCOL_VERSION` |
| Private | `_` prefix | `_sanitize_elevation_profile` |

## 6. Docstrings

Use Google style with `Args:` and `Returns:` sections. Document parameters, behavior, and return value. Example:

```python
def geocode_location(location_name: str, language: str = "en") -> GeocodingResponse:
    """
    Finds latitude and longitude for any place name (city, mountain pass, address).
    Use this BEFORE other tools if you only have a location name and not coordinates.

    Args:
        location_name: The natural language name of the location (e.g., "Stelvio Pass").
        language: header Accept-Language , e.g. en,it,fr,es
    Returns:
        A GeocodingResponse containing:
        - lat/lon: Precise coordinates for routing.
        - display_name: The formal name used for the mission report.
    """
```

## 7. MCP tool pattern

Each domain tool in `src/bikescout/tools/` must follow the pattern already used in the repo:

1. Service class (e.g. `SurfaceAnalyzerService`) with injectable dependencies in the constructor (falling back to real functions).
2. Module-level global instance (e.g. `service = SurfaceAnalyzerService()`).
3. Public wrapper function (e.g. `get_surface_analyzer(...)`) that delegates to the instance.
4. Returns dictionaries with a `status` key: `"Success"` or `"Error"`; on error include `message`.
5. Do not use `print` for diagnostic output; handle exceptions with `try/except`.

## 8. Error handling

- Wrap network calls and JSON parsing in `try/except`.
- Never let unhandled exceptions propagate to the MCP client; always return a structured response object (Pydantic) or a dictionary like `{"status": "Error", "message": ...}`.
- Use safe defaults (e.g. `getattr(obj, "attr", default)`) instead of directly accessing potentially missing attributes.
- Avoid bare `except`; always catch specific exceptions.

## 9. Configuration

- Use `frozen=True` dataclasses for configuration objects (e.g. `SurfaceAnalyzerConfig`).
- Streamlit theme in `src/bikescout/config.toml`.

## 10. Tests

- Framework: `pytest` (configured in `pyproject.toml`: `pythonpath = ["src"]`, `testpaths = ["src/bikescout/tests"]`, `asyncio_mode = auto`).
- One test file per tool module: `tests/tools/test_<module>.py`.
- Shared fixtures in `tests/conftest.py`.
- Run with `pytest` from the project root.
- Coverage: `pytest-cov`, configured in `[tool.coverage.run]` with `source = ["src/bikescout"]`.

## 11. Formatting

- PEP 8 as base reference.
- Recommended maximum line length: 100 characters.
- Four spaces for indentation, no tabs.
- One blank line between top-level functions, two between top-level classes.

## 12. Commits

Use Conventional Commits with scope, consistent with the repo history:

```
feat(tools): add surface analysis
fix(analysis): add fallbacks for route-based GPX parsing
refactor(chat): extract shared plan execution helpers
race: added wc elite men 2026 montreal
```

Typical scopes: `tools`, `analysis`, `chat`, `ui`, `race`, `deps`, `docs`.

## 13. What to avoid

- `print` statements in production code.
- Relative imports.
- Commented-out code left in files (use git for history).
- Magic numbers without a named constant.
- Bare generic exceptions caught without handling.
