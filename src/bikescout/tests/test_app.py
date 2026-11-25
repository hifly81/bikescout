from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

import bikescout.app as app_module

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


class StubLLM:
    """Minimal stand-in for Llama that records the completion calls it receives."""

    def __init__(self, content: str):
        self.content = content
        self.calls: list[dict] = []

    def create_chat_completion(self, messages, **kwargs):
        self.calls.append({"messages": messages, **kwargs})
        return {"choices": [{"message": {"content": self.content}}]}


class TestGenerateTacticalResponse:
    def test_returns_stripped_llm_content(self):
        llm = StubLLM('  {"briefing": "ok", "can_execute": false, "tool": null}  ')
        result = app_module.generate_tactical_response(
            [{"role": "user", "content": "45 km loop near Trento"}], llm
        )
        assert result == '{"briefing": "ok", "can_execute": false, "tool": null}'

    def test_system_prompt_states_identity_and_json_contract(self):
        llm = StubLLM("{}")
        app_module.generate_tactical_response(
            [{"role": "user", "content": "a ride"}], llm
        )
        system = llm.calls[0]["messages"][0]
        assert system["role"] == "system"
        assert "You are BikeScout Tactical AI." in system["content"]
        assert "Return ONLY valid JSON" in system["content"]

    def test_system_prompt_documents_intent_mapping_rules(self):
        llm = StubLLM("{}")
        app_module.generate_tactical_response(
            [{"role": "user", "content": "a ride"}], llm
        )
        system = llm.calls[0]["messages"][0]["content"]
        assert 'Infer bike_type="mtb"' in system
        assert "very hard/extreme=5" in system
        assert "explicitly requested include_* flag" in system
        assert "mostly MTB singletrack" in system

    def test_user_messages_reach_the_llm(self):
        llm = StubLLM("{}")
        app_module.generate_tactical_response(
            [{"role": "user", "content": "Ride plan near Trento please"}], llm
        )
        assert "Ride plan near Trento please" in llm.calls[0]["messages"][1]["content"]

    def test_mission_context_is_included_in_system_prompt(self):
        llm = StubLLM("{}")
        app_module.generate_tactical_response(
            [], llm, mission_context={"location_name": "Trento", "bike_type": "mtb"}
        )
        system = llm.calls[0]["messages"][0]["content"]
        assert "ACTIVE MISSION" in system
        assert '"location_name": "Trento"' in system

    def test_excludes_placeholder_assistant_messages(self):
        llm = StubLLM("{}")
        messages = [
            {"role": "user", "content": "first question"},
            {
                "role": "assistant",
                "content": "Connection established. Provide input...",
            },
            {"role": "assistant", "content": "real answer"},
        ]
        app_module.generate_tactical_response(messages, llm)
        contents = [m["content"] for m in llm.calls[0]["messages"]]
        assert "Connection established. Provide input..." not in contents
        assert "first question" in contents
        assert "real answer" in contents

    def test_limits_history_to_last_six_messages(self):
        llm = StubLLM("{}")
        messages = [{"role": "user", "content": f"message {i}"} for i in range(10)]
        app_module.generate_tactical_response(messages, llm)
        history = llm.calls[0]["messages"][1:]
        assert [m["content"] for m in history] == [f"message {i}" for i in range(4, 10)]

    def test_uses_json_schema_and_temperature_zero(self):
        llm = StubLLM("{}")
        app_module.generate_tactical_response([{"role": "user", "content": "hi"}], llm)
        call = llm.calls[0]
        assert call["temperature"] == 0.0
        assert call["max_tokens"] == 1024
        assert call["response_format"]["type"] == "json_object"
        properties = call["response_format"]["schema"]["properties"]
        assert "briefing" in properties
        assert "can_execute" in properties
        assert "tool" in properties


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
            "metadata": {
                "elevation_source": "ORS geometry elevation (offline terrain engine)"
            },
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
        fake_geo = SimpleNamespace(
            status="Success", lat=45.51, lon=11.90, display_name="Trento"
        )
        monkeypatch.setattr(
            "bikescout.mcp_server.geocode_location",
            lambda location_name, language="en": fake_geo,
        )
        monkeypatch.setattr(
            "bikescout.mcp_server.trail_scout_simple",
            lambda **kwargs: FAKE_MISSION_RESULT,
        )

        at = AppTest.from_file(str(APP_PATH)).run()
        assert not at.exception

        at.text_input(key="guided_start_location").set_value("Trento")
        at.form_submit_button[0].click().run()

        assert not at.exception
        assert at.session_state["mission_context"]["location_name"] == "Trento"
        assert "Trento" in at.session_state["mission_history"][0]
        assert at.session_state["messages"]
        assert at.session_state["messages"][-1]["role"] == "assistant"
        assert (
            "Mission generated successfully"
            in at.session_state["messages"][-1]["content"]
        )
        assert any("TACTICAL MISSION OVERVIEW" in m.value for m in at.markdown)
        assert any("Trento Fountain" in m.value for m in at.markdown)

        markdown_values = [m.value for m in at.markdown]
        assert any("Max gradient" in value and "22.5%" in value for value in markdown_values)
        assert any("Data confidence" in value and "82%" in value for value in markdown_values)
        assert any("Technical grade" in value and "S2 - Technical" in value for value in markdown_values)
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
