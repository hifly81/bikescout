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

import base64
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
)


class TestAppScript:
    @pytest.fixture
    def app_test(self, tmp_path, monkeypatch):
        # The repo ships a real GGUF model in models/; running the app with a
        # CWD without it makes the app skip loading the local LLM, keeping the
        # AppTest run fast and offline.
        monkeypatch.chdir(tmp_path)
        return AppTest.from_file(str(APP_PATH)).run()

    def test_app_renders_plan_tab_by_default(self, app_test):
        assert not app_test.exception
        assert app_test.radio(key="workspace_tab_selector").value == "Plan a Ride"
        assert any("Guided ride planning" in m.value for m in app_test.markdown)

    def test_chat_planner_tab_shows_empty_state(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        at = AppTest.from_file(str(APP_PATH))
        at.session_state["workspace_tab_selector"] = "Chat Planner"
        at.run()
        assert not at.exception
        assert at.radio(key="workspace_tab_selector").value == "Chat Planner"
        assert any("Start a mission" in m.value for m in at.markdown)

    def test_gpx_tab_renders(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        at = AppTest.from_file(str(APP_PATH))
        at.session_state["workspace_tab_selector"] = "GPX Audit"
        at.run()
        assert not at.exception
        assert any("GPX tactical audit" in m.value for m in at.markdown)

    def test_rider_profile_fields_are_in_plan_tab(self, app_test):
        assert not any(button.key == "rider_profile_launcher" for button in app_test.sidebar.button)
        assert app_test.selectbox(key="rider_profile_fitness_level").value == "intermediate"
        assert app_test.number_input(key="rider_profile_weight").value == 75.0
        assert app_test.selectbox(key="rider_profile_gender").value == "male"

    def test_rider_profile_fields_absent_in_chat_tab(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        at = AppTest.from_file(str(APP_PATH))
        at.session_state["workspace_tab_selector"] = "Chat Planner"
        at.run()

        assert not at.exception
        assert not any(button.key == "rider_profile_launcher" for button in at.sidebar.button)
        assert not any(box.key == "rider_profile_fitness_level" for box in at.selectbox)

    def test_rider_profile_fields_edit_defaults(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        at = AppTest.from_file(str(APP_PATH))
        at.session_state["rider_profile_fitness_level"] = "pro"
        at.session_state["rider_profile_weight"] = 82.0
        at.run()

        assert not at.exception
        assert at.selectbox(key="rider_profile_fitness_level").value == "pro"
        assert at.number_input(key="rider_profile_weight").value == 82.0
        assert at.session_state["rider_profile"]["fitness_level"] == "pro"
        assert at.session_state["rider_profile"]["weight_kg"] == 82.0
        assert not any(button.key == "rider_profile_done" for button in at.button)


FAKE_MISSION_RESULT = {
    "status": "Success",
    "info": {
        "route_type": "Round Trip",
        "distance_km": 30,
        "ascent_m": 300,
        "difficulty": "Easy",
        "surface_analysis": {
            "tactical_briefing": {
                "avg_gradient": "2.4%",
                "climb_category": "C3 - Challenging",
                "avg_climb_gradient": "7.1%",
                "max_gradient": 22.5,
                "data_confidence": 0.82,
                "technical_difficulty": {
                    "label": "S2 - Technical",
                    "confidence": 0.75,
                    "source": "osm:mtb_scale",
                },
                "climb_list": [
                    {
                        "start_index": 12,
                        "end_index": 48,
                        "length_m": 1800.0,
                        "gain_m": 120.0,
                        "avg_gradient": 6.7,
                        "max_gradient": 22.5,
                        "summit_elevation_m": 1120.0,
                        "fiets_index": 2.4,
                        "category": "C3 - Challenging",
                    }
                ],
                "terrain_analysis": {
                    "noise_floor_m": 0.6,
                    "profile_points": 240,
                    "profile_length_m": 30000.0,
                    "warnings": [
                        "Micro-pitch up to 22.5%: expect hike-a-bike or high battery drain."
                    ],
                },
            },
            "metadata": {"elevation_source": "ORS geometry elevation (offline terrain engine)"},
            "surface_breakdown": [{"type": "Paved", "percentage": "60%"}],
            "mechanical_setup": {
                "setup_details": {
                    "wheel_label": '29"',
                    "tire_width_mm": 58,
                    "rim_internal_width_mm": 25,
                    "casing_type": "trail",
                    "tubeless": True,
                    "psi_front": 19.9,
                    "psi_rear": 25.4,
                    "bar_front": 1.37,
                    "bar_rear": 1.75,
                    "strategy": "Standard",
                    "load_split": {"front": 0.4, "rear": 0.6},
                    "knob_choice": "All-Terrain / Trail",
                    "advice": ["Tire Inserts Recommended (rear wheel first) for S3+ terrain"],
                    "warnings": [],
                    "tactical_display": '29" wheels | F: 19.9 PSI | R: 25.4 PSI [Standard Setup]',
                },
                "compatible": True,
                "safety_warnings": [],
            },
        },
    },
    "conditions": {
        "weather": [
            {"time": "06:00", "temp": 12, "app_temp": 12, "rain_prob": 0, "wind": 5},
            {"time": "09:00", "temp": 14, "app_temp": 14, "rain_prob": 10, "wind": 4},
        ],
        "safety_advice": {
            "status": "Stable",
            "wind_risk_score": 3,
            "gear_advice": "Take a light jacket.",
            "message": "Good conditions.",
        },
        "mud_risk": {
            "tactical_analysis": {
                "mud_risk_score": "low",
                "dry_time_eta": "2h",
                "traction_risk": {
                    "level": "Good",
                    "advice": "Normal traction expected.",
                },
                "trail_damage_risk": {
                    "level": "Low",
                    "advice": "Minimal damage expected.",
                },
            },
            "environmental_context": {"total_rain_72h_mm": 0},
        },
    },
    "logistics": {
        "nearby_amenities": [
            {
                "name": "Trento Fountain",
                "type": "water",
                "distance_m": 300,
                "location": {"latitude": 45.51, "longitude": 11.90},
            },
        ],
        "nutrition_plan": {
            "mission_nutrition_briefing": {
                "fluids": {"total_liters": 2.5, "hourly_average_ml": 600},
                "carbohydrates": {"total_grams": 90, "hourly_target_g": 25},
                "electrolytes": {"total_sodium_mg": 800, "hourly_sodium_mg": 200},
                "tactical_advice": ["Carry enough water."],
            }
        },
    },
}


class TestPlanFlow:
    def test_plan_tab_submit_renders_mission_results(self, tmp_path, monkeypatch):
        # Stub the network layer so the full plan-tab -> chat-planner flow runs offline.
        monkeypatch.chdir(tmp_path)
        fake_geo = SimpleNamespace(status="Success", lat=45.51, lon=11.90, display_name="Trento")
        monkeypatch.setattr(
            "bikescout.mcp_server.geocode_location",
            lambda location_name, language="en": fake_geo,
        )
        scout_calls = []

        def fake_scout(**kwargs):
            scout_calls.append(kwargs)
            return FAKE_MISSION_RESULT

        monkeypatch.setattr("bikescout.mcp_server.trail_scout_simple", fake_scout)

        at = AppTest.from_file(str(APP_PATH)).run()
        assert not at.exception

        at.text_input(key="guided_start_location").set_value("Trento")
        at.form_submit_button[0].click().run()

        assert not at.exception
        assert at.session_state["mission_context"]["location_name"] == "Trento"
        assert "Trento" in at.session_state["mission_history"][0]
        assert at.session_state["messages"]
        assert at.session_state["messages"][-1]["role"] == "assistant"
        assert "Mission generated successfully" in at.session_state["messages"][-1]["content"]
        assert any("TACTICAL MISSION OVERVIEW" in m.value for m in at.markdown)
        assert any("Trento Fountain" in m.value for m in at.markdown)

        markdown_values = [m.value for m in at.markdown]
        assert any("Max gradient" in value and "22.5%" in value for value in markdown_values)
        assert any("Data confidence" in value and "82%" in value for value in markdown_values)
        assert any(
            "Technical grade" in value and "S2 - Technical" in value for value in markdown_values
        )
        assert any("Profile points" in value and "240" in value for value in markdown_values)

        caption_values = [caption.value for caption in at.caption]
        assert any("Elevation source" in value for value in caption_values)

        expander_labels = [expander.label for expander in at.expander]
        assert "Climb list" in expander_labels
        assert "Terrain warnings" in expander_labels
        assert "Mechanical setup" in expander_labels
        assert any("F: 19.9 / R: 25.4 PSI" in value for value in markdown_values)
        assert any("Tire Inserts Recommended" in value for value in markdown_values)

        climb_tables = [
            table.value for table in at.dataframe if "C3 - Challenging" in str(table.value)
        ]
        assert climb_tables
        climb_row = climb_tables[0].iloc[0]
        assert climb_row["Gain (m)"] == "120.0"
        assert climb_row["Length (km)"] == "1.80"
        assert scout_calls
        assert 3 <= scout_calls[0]["complexity"] <= 5

    def test_climb_profile_dialog_opens_for_long_climb(self, tmp_path):
        climb_path = tmp_path / "bs_altimetry_fixed_climb_1.png"
        climb_path.write_bytes(PNG_1PX)
        climb = {
            "category": "C3 - Challenging",
            "length_m": 1800.0,
            "gain_m": 120.0,
            "summit_elevation_m": 1120.0,
        }
        script = f"""
import streamlit as st
st.session_state["climb_list_table"] = {{"selection": {{"rows": [], "columns": [], "cells": []}}}}
if "dialog_shown" not in st.session_state:
    st.session_state["dialog_shown"] = True
    from bikescout.app_ui_helpers import _render_climb_profile_dialog
    _render_climb_profile_dialog(1, {climb!r}, {str(climb_path)!r})
"""
        at = AppTest.from_string(script)
        at.run()

        assert not at.exception
        captions = [caption.value for caption in at.caption]
        assert any("Climb 1" in value for value in captions)
        assert any("1000.0 m → 1120.0 m · 1.80 km · 120.0 m gained" in value for value in captions)
        assert not any(button.key == "climb_profile_done" for button in at.button)

    def test_selected_climb_dialog_does_not_reopen_on_rerun(self, tmp_path):
        (tmp_path / "bs_altimetry_fixed.png").write_bytes(PNG_1PX)
        (tmp_path / "bs_altimetry_fixed_climb_1.png").write_bytes(PNG_1PX)
        result = deepcopy(FAKE_MISSION_RESULT)
        result["elevation_profile_path"] = str(tmp_path / "bs_altimetry_fixed.png")
        script = f"""
import streamlit as st
from bikescout.app_ui_helpers import render_route_results
st.session_state["climb_list_table"] = {{"selection": {{"rows": [0], "columns": [], "cells": []}}}}
render_route_results({result!r})
"""
        at = AppTest.from_string(script)
        at.run()

        assert not at.exception
        assert any("Climb 1" in caption.value for caption in at.caption)
        assert not any(button.key == "climb_profile_done" for button in at.button)

        at.run()

        assert not at.exception
        assert not any("Climb 1" in caption.value for caption in at.caption)
