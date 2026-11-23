# Tech stack

- `src/bikescout/mcp_server.py`: FastMCP server (`bikescout` entry point) exposing route planning, geocoding, weather, mud analysis, nutrition, and race intelligence tools via `@mcp.tool()` with Pydantic v2 schemas in `src/bikescout/schemas.py`.
- `src/bikescout/app.py`: Streamlit tactical UI (`app_helpers.py`, `app_ui_helpers.py`) with a local GGUF chat planner powered by `llama-cpp-python` (`>=0.3.16`) and `huggingface_hub` (`>=0.27.0`), using structured JSON outputs (`response_format=json_schema`) and thinking disabled on reasoning models (`Qwen3.5-9B`, `Ministral-3-8B-Instruct`, `Qwen2.5-7B-Instruct`).
- `src/bikescout/tools/`: Stateless domain services (`surface.py`, `weather.py`, `geocoding.py`, `mud.py`, `race/`, etc.) backed by OpenRouteService (`requests`, `polyline`, `geopy`), astronomical/timezone utilities (`astral`, `timezonefinder`), and export generators (`gpxpy`, `matplotlib`, `staticmap`, `pillow`, `fpdf`).
- `src/bikescout/tests/`: `pytest` suite (`asyncio_mode = auto`, `pythonpath = ["src"]`) mirroring tool modules with shared fixtures in `conftest.py`.
- `models/`: Local GGUF weights directory (git-ignored) downloaded on demand from Hugging Face.

Python >= 3.10 in a single root `pyproject.toml` (`packages = ["src/bikescout"]`). External routing and geocoding require `ORS_API_KEY` in `.env` (or entered in the Streamlit sidebar).