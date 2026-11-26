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

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from bikescout.app_llm import (
    PLACEHOLDER_ASSISTANT,
    LlamaChatModel,
    build_tactical_chain,
    generate_tactical_response,
    to_langchain_messages,
)


class StubLlama:
    """Minimal llama-cpp backend that records the options used for each call."""

    def __init__(self, content: str):
        self.content = content
        self.calls: list[dict[str, Any]] = []

    def create_chat_completion(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"choices": [{"message": {"content": self.content}}]}


def _model(backend: StubLlama, **kwargs: Any) -> LlamaChatModel:
    return LlamaChatModel(llm=backend, **kwargs)


class TestLlamaChatModel:
    def test_maps_roles_and_strips_completion_content(self):
        backend = StubLlama('  {"briefing": "ok"}  ')
        result = _model(backend).invoke(
            [
                SystemMessage(content="system rules"),
                HumanMessage(content="a ride"),
                AIMessage(content="previous answer"),
            ]
        )
        assert result.content == '{"briefing": "ok"}'
        assert backend.calls[0]["messages"] == [
            {"role": "system", "content": "system rules"},
            {"role": "user", "content": "a ride"},
            {"role": "assistant", "content": "previous answer"},
        ]

    def test_passes_generation_options_and_structured_response(self):
        backend = StubLlama("{}")
        schema = {"type": "json_object", "schema": {"type": "object"}}
        model = _model(
            backend,
            temperature=0.0,
            max_tokens=1024,
            response_format=schema,
        )
        model.invoke([HumanMessage(content="hi")])
        call = backend.calls[0]
        assert call["temperature"] == 0.0
        assert call["max_tokens"] == 1024
        assert call["response_format"] == schema

    def test_with_response_format_returns_a_new_model(self):
        backend = StubLlama("{}")
        model = _model(backend)
        bound = model.with_response_format({"type": "json_object"})
        assert model.response_format is None
        assert bound.response_format == {"type": "json_object"}
        assert bound.llm is model.llm

    def test_forwards_stop_sequences(self):
        backend = StubLlama("{}")
        _model(backend).invoke([HumanMessage(content="hi")], stop=["END"])
        assert backend.calls[0]["stop"] == ["END"]


class TestHistoryConversion:
    def test_drops_placeholder_and_keeps_recent_messages(self):
        history = [
            {"role": "assistant", "content": PLACEHOLDER_ASSISTANT},
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "answer"},
            {"role": "user", "content": "second"},
            {"role": "user", "content": "third"},
        ]
        messages = to_langchain_messages(history, limit=3)
        assert [str(message.content) for message in messages] == [
            "answer",
            "second",
            "third",
        ]
        assert [message.type for message in messages] == ["ai", "human", "human"]

    def test_keeps_system_messages_as_system_role(self):
        messages = to_langchain_messages([{"role": "system", "content": "rules"}])
        assert messages == [SystemMessage(content="rules")]


class TestTacticalChain:
    def test_keeps_json_braces_literal_in_system_prompt(self):
        backend = StubLlama("done")
        system_prompt = 'Mission snapshot: {"location_name": "Trento"}'
        chain = build_tactical_chain(_model(backend), system_prompt)
        result = chain.invoke({"chat_history": [HumanMessage(content="plan a ride")]})
        assert result == "done"
        assert backend.calls[0]["messages"][0] == {
            "role": "system",
            "content": system_prompt,
        }
        assert backend.calls[0]["messages"][1] == {
            "role": "user",
            "content": "plan a ride",
        }


class TestGenerateTacticalResponse:
    def test_returns_stripped_llm_content(self):
        llm = StubLlama('  {"briefing": "ok", "can_execute": false, "tool": null}  ')
        result = generate_tactical_response(
            [{"role": "user", "content": "45 km loop near Trento"}], _model(llm)
        )
        assert result == '{"briefing": "ok", "can_execute": false, "tool": null}'

    def test_system_prompt_states_identity_and_json_contract(self):
        llm = StubLlama("{}")
        generate_tactical_response([{"role": "user", "content": "a ride"}], _model(llm))
        system = llm.calls[0]["messages"][0]
        assert system["role"] == "system"
        assert "You are BikeScout Tactical AI." in system["content"]
        assert "Return ONLY valid JSON" in system["content"]

    def test_system_prompt_documents_intent_mapping_rules(self):
        llm = StubLlama("{}")
        generate_tactical_response([{"role": "user", "content": "a ride"}], _model(llm))
        system = llm.calls[0]["messages"][0]["content"]
        assert 'Infer bike_type="mtb"' in system
        assert "very hard/extreme=5" in system
        assert "explicitly requested include_* flag" in system
        assert "mostly MTB singletrack" in system

    def test_user_messages_reach_the_llm(self):
        llm = StubLlama("{}")
        generate_tactical_response(
            [{"role": "user", "content": "Ride plan near Trento please"}], _model(llm)
        )
        assert "Ride plan near Trento please" in llm.calls[0]["messages"][1]["content"]

    def test_mission_context_is_included_in_system_prompt(self):
        llm = StubLlama("{}")
        generate_tactical_response(
            [], _model(llm), mission_context={"location_name": "Trento", "bike_type": "mtb"}
        )
        system = llm.calls[0]["messages"][0]["content"]
        assert "ACTIVE MISSION" in system
        assert '"location_name": "Trento"' in system

    def test_excludes_placeholder_assistant_messages(self):
        llm = StubLlama("{}")
        messages = [
            {"role": "user", "content": "first question"},
            {
                "role": "assistant",
                "content": "Connection established. Provide input...",
            },
            {"role": "assistant", "content": "real answer"},
        ]
        generate_tactical_response(messages, _model(llm))
        contents = [m["content"] for m in llm.calls[0]["messages"]]
        assert "Connection established. Provide input..." not in contents
        assert "first question" in contents
        assert "real answer" in contents

    def test_limits_history_to_last_six_messages(self):
        llm = StubLlama("{}")
        messages = [{"role": "user", "content": f"message {i}"} for i in range(10)]
        generate_tactical_response(messages, _model(llm))
        history = llm.calls[0]["messages"][1:]
        assert [m["content"] for m in history] == [f"message {i}" for i in range(4, 10)]

    def test_uses_json_schema_and_temperature_zero(self):
        llm = StubLlama("{}")
        generate_tactical_response([{"role": "user", "content": "hi"}], _model(llm))
        call = llm.calls[0]
        assert call["temperature"] == 0.0
        assert call["max_tokens"] == 1024
        assert call["response_format"]["type"] == "json_object"
        properties = call["response_format"]["schema"]["properties"]
        assert "briefing" in properties
        assert "can_execute" in properties
        assert "tool" in properties
        args = properties["tool"]["anyOf"][0]["properties"]["args"]["properties"]
        assert args["complexity"]["minimum"] == 1
        assert args["complexity"]["maximum"] == 5
        assert args["profile"]["enum"] == [
            "cycling-mountain",
            "cycling-road",
            "cycling-regular",
            "cycling-electric",
        ]
