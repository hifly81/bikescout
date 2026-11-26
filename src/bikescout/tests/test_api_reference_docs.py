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

from __future__ import annotations

import asyncio
import inspect
import re
from pathlib import Path
from typing import Any, Literal, get_args, get_origin, get_type_hints

from pydantic import BaseModel

from bikescout import mcp_server, schemas

API_REFERENCE = (
    Path(__file__).resolve().parents[3] / "site" / "documentation" / "api-reference.html"
)


def _html() -> str:
    return API_REFERENCE.read_text(encoding="utf-8")


def _models() -> dict[str, type[BaseModel]]:
    return {
        name: obj
        for name, obj in vars(schemas).items()
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel
    }


def _public_tools() -> dict[str, Any]:
    """Return the MCP tools defined in mcp_server, excluding helpers and resources."""
    return {
        name: obj
        for name, obj in vars(mcp_server).items()
        if inspect.isfunction(obj)
        and getattr(obj, "__module__", None) == mcp_server.__name__
        and not name.startswith("_")
        and name != "main"
        and not name.startswith("serve_")
    }


def _registered_tool_names() -> set[str]:
    """Return the tool names actually registered with FastMCP."""
    return {tool.name for tool in asyncio.run(mcp_server.mcp.list_tools())}


def _schema_tables(html: str) -> dict[str, str]:
    pattern = re.compile(
        r"<h4[^>]*>([^<]+)</h4>\s*<div[^>]*>\s*<table[^>]*>(.*?)</table>",
        re.DOTALL,
    )
    return {title.strip(): table for title, table in pattern.findall(html)}


def _rows(table: str) -> list[str]:
    return re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.DOTALL)


def _row_text(row: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", row)).strip().lower()


def _doc_names(row: str) -> set[str]:
    cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
    if not cells:
        return set()
    names: set[str] = set()
    for code in re.findall(r"<code>([^<]+)</code>", cells[0]):
        for part in code.split("/"):
            if part.strip():
                names.add(part.strip())
    return names


def _doc_fields(table: str) -> set[str]:
    fields: set[str] = set()
    for row in _rows(table):
        fields.update(_doc_names(row))
    return fields


def _find_row(table: str, name: str) -> str:
    for row in _rows(table):
        if name in _doc_names(row):
            return row
    raise AssertionError(f"{name!r} is missing from the API reference table")


def _literal_values(annotation: Any) -> set[str]:
    """Collect Literal choices, including Literals nested in containers."""
    if get_origin(annotation) is Literal:
        return {str(value).lower() for value in get_args(annotation)}
    values: set[str] = set()
    for arg in get_args(annotation):
        values.update(_literal_values(arg))
    return values


def _default_token(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).lower()


def _tool_section(html: str, tool_name: str) -> str:
    marker = f'<h3 class="text-2xl font-bold text-white font-mono">{tool_name}</h3>'
    start = html.find(marker)
    assert start >= 0, f"Tool section {tool_name!r} is missing"
    next_marker = html.find("<!-- Tool:", start + len(marker))
    end = next_marker if next_marker >= 0 else len(html)
    return html[start:end]


def _parameters_table(section: str) -> str:
    match = re.search(
        r"<h4[^>]*>Parameters</h4>\s*<div[^>]*>\s*<table[^>]*>(.*?)</table>",
        section,
        re.DOTALL,
    )
    assert match, "Parameters table is missing from the tool section"
    return match.group(1)


def _returns_text(section: str) -> str:
    match = re.search(r"<h4[^>]*>Returns</h4>(.*?)</div>", section, re.DOTALL)
    assert match, "Returns section is missing from the tool section"
    return _row_text(match.group(1))


def test_api_reference_matches_schema_fields_defaults_and_choices() -> None:
    tables = _schema_tables(_html())
    models = _models()

    assert set(models).issubset(tables), (
        f"Missing schema sections: {sorted(set(models) - set(tables))}"
    )

    for name, model in models.items():
        table = tables[name]
        assert _doc_fields(table) == set(model.model_fields), (
            f"{name}: documented fields differ from {sorted(model.model_fields)}"
        )

        for field_name, field in model.model_fields.items():
            text = _row_text(_find_row(table, field_name))
            for choice in _literal_values(field.annotation):
                assert choice in text, f"{name}.{field_name}: missing choice {choice!r}"
            if field.is_required() or field.default_factory is not None:
                continue
            token = _default_token(field.default)
            assert token in text, f"{name}.{field_name}: missing default {token!r}"


def test_api_reference_matches_tool_parameters_defaults_and_choices() -> None:
    html = _html()
    tools = _public_tools()

    assert tools, "No MCP tools were discovered in mcp_server"
    assert set(tools) == _registered_tool_names(), (
        f"Registered tools differ from documented functions: "
        f"registered={sorted(_registered_tool_names())}, documented={sorted(tools)}"
    )

    for name, tool in tools.items():
        section = _tool_section(html, name)
        table = _parameters_table(section)
        signature = inspect.signature(tool)
        hints = get_type_hints(tool)
        assert _doc_fields(table) == set(signature.parameters), (
            f"{name}: documented parameters differ from {sorted(signature.parameters)}"
        )

        for param_name, param in signature.parameters.items():
            text = _row_text(_find_row(table, param_name))
            for choice in _literal_values(hints.get(param_name, param.annotation)):
                assert choice in text, f"{name}.{param_name}: missing choice {choice!r}"
            if param.default is inspect.Parameter.empty or param.default is None:
                continue
            token = _default_token(param.default)
            assert token in text, f"{name}.{param_name}: missing default {token!r}"

        return_type = hints.get("return")
        if isinstance(return_type, type) and issubclass(return_type, BaseModel):
            assert return_type.__name__.lower() in _returns_text(section), (
                f"{name}: Returns section must mention {return_type.__name__}"
            )
