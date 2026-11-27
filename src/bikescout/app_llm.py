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

import json
import os
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import Any, cast

import streamlit as st

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from llama_cpp import Llama
from pydantic import ConfigDict

AVAILABLE_MODELS = {
    "Qwen3.5-9B": {
        "repo": "unsloth/Qwen3.5-9B-GGUF",
        "file": "Qwen3.5-9B-Q4_K_M.gguf",
        "description": "Size: ~5.7 GB",
    },
    "Ministral-3-8B-Instruct": {
        "repo": "unsloth/Ministral-3-8B-Instruct-2512-GGUF",
        "file": "Ministral-3-8B-Instruct-2512-Q4_K_M.gguf",
        "description": "Size: ~5.2 GB",
    },
    "Qwen2.5-7B-Instruct": {
        "repo": "bartowski/Qwen2.5-7B-Instruct-GGUF",
        "file": "Qwen2.5-7B-Instruct-Q6_K.gguf",
        "description": "Size: ~6.3 GB",
    },
}

CUSTOM_MODEL_OPTION = "Custom GGUF (Hugging Face)"
CUSTOM_MODEL_CONFIG_PATH = os.path.join("models", "custom_model.json")

LOCAL_MODELS_DIR = "models"

PLACEHOLDER_ASSISTANT = "Connection established. Provide input..."


def to_langchain_messages(
    history: Sequence[dict[str, Any]], limit: int | None = None
) -> list[BaseMessage]:
    """Convert planner chat history to LangChain messages, dropping UI placeholders.

    Args:
        history: Chat messages with ``role`` and ``content`` keys.
        limit: Optional maximum number of recent messages to keep after filtering.

    Returns:
        System, human and AI messages in the same order as the input.
    """
    messages: list[BaseMessage] = []
    for item in history:
        role = str(item.get("role", ""))
        content = str(item.get("content", ""))
        if role == "system":
            messages.append(SystemMessage(content=content))
        elif role == "assistant":
            if content == PLACEHOLDER_ASSISTANT:
                continue
            messages.append(AIMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))
    return messages[-limit:] if limit is not None else messages


class LlamaChatModel(BaseChatModel):
    """LangChain chat model backed by a local llama-cpp-python ``Llama`` instance.

    The adapter keeps the GGUF-specific call options (structured JSON, disabled
    thinking via the model chat template) while exposing the standard LangChain
    message and runnable interfaces.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm: Any
    temperature: float = 0.0
    max_tokens: int = 1024
    response_format: dict[str, Any] | None = None

    @property
    def _llm_type(self) -> str:
        return "bikescout_llama"

    def with_response_format(self, response_format: dict[str, Any]) -> LlamaChatModel:
        """Return a copy of the model bound to a structured response format."""
        return self.model_copy(update={"response_format": response_format})

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        payload: dict[str, Any] = {
            "messages": [_to_llama_message(message) for message in messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.response_format is not None:
            payload["response_format"] = self.response_format
        if stop:
            payload["stop"] = stop

        response = cast(
            dict[str, Any],
            self.llm.create_chat_completion(**payload),
        )
        content = response["choices"][0]["message"]["content"]
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=str(content).strip()))]
        )


def _to_llama_message(message: BaseMessage) -> dict[str, str]:
    """Map a LangChain message to the role/content shape expected by llama.cpp."""
    if isinstance(message, SystemMessage):
        role = "system"
    elif isinstance(message, AIMessage):
        role = "assistant"
    else:
        role = "user"
    return {"role": role, "content": str(message.content)}


def build_tactical_chain(model: BaseChatModel, system_prompt: str) -> Runnable[dict[str, Any], str]:
    """Build the LCEL chain used for every tactical planner turn.

    Args:
        model: Chat model that performs the completion.
        system_prompt: Already-rendered prompt; passed as a message so JSON braces
            in the active mission snapshot are never interpreted as template fields.

    Returns:
        A runnable that accepts ``chat_history`` and returns the assistant text.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder("system_message"),
            MessagesPlaceholder("chat_history"),
        ]
    ).partial(system_message=[SystemMessage(content=system_prompt)])
    return prompt | model | StrOutputParser()


def load_custom_model_config() -> dict[str, Any] | None:
    if not os.path.exists(CUSTOM_MODEL_CONFIG_PATH):
        return None
    try:
        with open(CUSTOM_MODEL_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    repo = str(data.get("repo", "")).strip()
    filename = str(data.get("file", "")).strip()
    if not repo or not filename or not filename.lower().endswith(".gguf"):
        return None
    size_gb = data.get("size_gb")
    try:
        size_gb_val = float(size_gb) if size_gb is not None and str(size_gb).strip() else None
    except (TypeError, ValueError):
        size_gb_val = None
    return {
        "repo": repo,
        "file": filename,
        "size_gb": size_gb_val,
        "name": str(data.get("name") or Path(filename).stem),
    }


def save_custom_model_config(config: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(CUSTOM_MODEL_CONFIG_PATH) or ".", exist_ok=True)
    with open(CUSTOM_MODEL_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_model_config(model_name: str) -> dict[str, Any] | None:
    if model_name == CUSTOM_MODEL_OPTION:
        return load_custom_model_config()
    return AVAILABLE_MODELS.get(model_name)


def get_model_size_label(model_name: str) -> str:
    cfg = get_model_config(model_name)
    if not cfg:
        return "Size: unknown"
    if "description" in cfg and cfg["description"]:
        return str(cfg["description"])
    size_gb = cfg.get("size_gb")
    if isinstance(size_gb, (int, float)):
        return f"Size: ~{float(size_gb):.2f} GB"
    return "Size: unknown"


def get_local_model_path(model_name: str) -> str:
    cfg = get_model_config(model_name)
    if not cfg:
        return os.path.join(LOCAL_MODELS_DIR, f"{model_name}.gguf")
    return os.path.join(LOCAL_MODELS_DIR, str(cfg["file"]))


@st.cache_resource
def load_llm(model_name: str, n_gpu_layers: int) -> LlamaChatModel | None:
    cfg = get_model_config(model_name)
    if not cfg:
        return None
    path = get_local_model_path(model_name)
    if not os.path.exists(path):
        return None

    kwargs: dict[str, Any] = {}
    model_id = f"{cfg.get('repo', '')} {cfg.get('file', '')} {model_name}".lower()
    if "qwen3.5" in model_id:
        kwargs["chat_template_kwargs"] = {"enable_thinking": False}

    llm = Llama(
        model_path=path,
        n_ctx=8192,
        n_gpu_layers=n_gpu_layers,
        verbose=False,
        **kwargs,
    )
    return LlamaChatModel(llm=llm)


def generate_tactical_response(
    messages_history: Sequence[dict[str, Any]],
    model: LlamaChatModel,
    mission_context: dict[str, Any] | None = None,
) -> str:
    json_schema = {
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {
                "briefing": {"type": "string"},
                "can_execute": {"type": "boolean"},
                "tool": {
                    "anyOf": [
                        {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "enum": ["trail_scout_simple"]},
                                "args": {
                                    "type": "object",
                                    "properties": {
                                        "bike_type": {
                                            "type": "string",
                                            "enum": ["mtb", "road", "gravel", "e-mtb", "enduro"],
                                        },
                                        "tire_size": {"type": "string"},
                                        "distance": {"type": "number"},
                                        "route_mode": {
                                            "type": "string",
                                            "enum": ["round_trip", "point_to_point"],
                                        },
                                        "location_name": {"type": "string"},
                                        "destination_name": {"type": "string"},
                                        "dest_latitude": {"type": "number"},
                                        "dest_longitude": {"type": "number"},
                                        "latitude": {"type": "number"},
                                        "longitude": {"type": "number"},
                                        "include_weather": {"type": "boolean"},
                                        "include_mud_analysis": {"type": "boolean"},
                                        "include_nutrition_plan": {"type": "boolean"},
                                        "include_poi": {"type": "boolean"},
                                        "include_gpx": {"type": "boolean"},
                                        "include_map": {"type": "boolean"},
                                        "include_altimetry": {"type": "boolean"},
                                        "is_ebike": {"type": "boolean"},
                                        "battery_wh": {
                                            "type": "integer",
                                            "minimum": 100,
                                            "maximum": 2000,
                                        },
                                        "motor_power_limit_w": {
                                            "type": ["integer", "null"],
                                            "minimum": 100,
                                            "maximum": 1200,
                                        },
                                        "weight_kg": {"type": "number"},
                                        "sweat_rate_ml_per_hour": {
                                            "type": "number",
                                            "minimum": 100,
                                            "maximum": 5000,
                                        },
                                        "seed": {"type": "number"},
                                        "complexity": {
                                            "type": "integer",
                                            "minimum": 1,
                                            "maximum": 5,
                                        },
                                        "profile": {
                                            "type": "string",
                                            "enum": [
                                                "cycling-mountain",
                                                "cycling-road",
                                                "cycling-regular",
                                                "cycling-electric",
                                            ],
                                        },
                                        "fitness_level": {
                                            "type": "string",
                                            "enum": ["beginner", "intermediate", "pro"],
                                        },
                                        "gender": {
                                            "type": "string",
                                            "enum": ["male", "female"],
                                        },
                                        "direction_bias": {
                                            "type": "array",
                                            "items": {
                                                "type": "string",
                                                "enum": ["north", "south", "east", "west"],
                                            },
                                        },
                                        "avoid_urban": {"type": "boolean"},
                                        "prefer_rural": {"type": "boolean"},
                                        "distance_flex_percent": {
                                            "type": "integer",
                                            "minimum": 0,
                                            "maximum": 30,
                                        },
                                        "priority_mode": {
                                            "type": "string",
                                            "enum": [
                                                "balanced",
                                                "distance_first",
                                                "ride_character_first",
                                            ],
                                        },
                                        "target_date": {
                                            "type": "string",
                                            "description": "Analysis date YYYY-MM-DD. Default tomorrow, max 5 days ahead.",
                                        },
                                    },
                                    "required": ["bike_type", "tire_size", "location_name"],
                                },
                            },
                            "required": ["name", "args"],
                        },
                        {"type": "null"},
                    ]
                },
            },
            "required": ["briefing", "tool", "can_execute"],
        },
    }

    mission_block = ""
    if mission_context:
        mission_block = f"""
=== ACTIVE MISSION ===
{json.dumps(mission_context, ensure_ascii=False)}
Reuse mission location unless user explicitly changes it.
Reuse mission routing preferences unless user explicitly changes them.
"""

    today = date.today()
    default_date = (today + timedelta(days=1)).isoformat()
    max_date = (today + timedelta(days=5)).isoformat()
    system_prompt = f"""
You are BikeScout Tactical AI.
Return ONLY valid JSON matching the schema.
Set can_execute=true only when the user clearly wants a cycling route or route-related analysis.
When can_execute=true, use tool trail_scout_simple.
Always preserve location context for follow-up requests.
Always preserve routing preference context for follow-up requests unless the user changes it.
Distance must be in kilometers.
Complexity range is 1..5, default 3.
Use point_to_point only for A to B routes.
Date rules:
- Today is {today.isoformat()}. If user does not mention a date, set target_date to {default_date}.
- Accept only target_date from {default_date} to {max_date} inclusive.
- If user asks for a date beyond {max_date}, set can_execute=false and explain clearly in briefing that analysis cannot be generated because forecasts beyond 5 days ahead are not reliable.
- If user mentions "today", use {default_date} as target_date and state it in briefing.

Bike and difficulty normalization rules:
- Infer bike_type="mtb" when the user only names 29"/29er/27.5"/650b wheels; explicit disciplines win.
- Map difficulty wording to complexity: easy=1-2, moderate=3, hard=4, very hard/extreme=5.
- Map profile from bike_type: mtb/enduro/gravel -> cycling-mountain, road -> cycling-road, e-mtb -> cycling-electric.
- Set every explicitly requested include_* flag to true, even for road rides.

Routing preference extraction rules:
- If the user asks to stay south, north, east, or west of the start area, set direction_bias accordingly.
- If the user asks for south-east, south and east, or similar, set direction_bias to multiple values, e.g. ["south", "east"].
- If the user asks to avoid the city, avoid urban streets, or avoid traffic-heavy urban riding, set avoid_urban=true.
- If the user asks for countryside, quieter roads, open country, rural roads, or scenic non-urban riding, set prefer_rural=true.
- If the user asks for mostly MTB singletrack, off-road/dirt trails, or to avoid paved roads, also set profile="cycling-mountain", avoid_urban=true, prefer_rural=true, priority_mode="ride_character_first", and distance_flex_percent between 15 and 20.
- If the user cares more about the ride character than exact distance, set priority_mode="ride_character_first".
- If the user explicitly wants the route as close as possible to the requested distance, set priority_mode="distance_first".
- Otherwise use priority_mode="balanced".
- If the user allows some tolerance on distance, set distance_flex_percent between 10 and 20 depending on wording.
- If the user strongly prioritizes exact target distance, set distance_flex_percent=0.
- If no directional or routing preference is mentioned, omit these fields or preserve them from active mission context.

Examples:
- "keep it south and east of town" -> direction_bias ["south", "east"]
- "avoid the city and prefer countryside roads" -> avoid_urban true, prefer_rural true
- "mostly singletrack MTB trails, no asphalt" -> profile cycling-mountain, avoid_urban true, prefer_rural true, priority_mode ride_character_first, distance_flex_percent 15 or 20
- "about 60 km, doesn't have to be exact" -> distance_flex_percent 10 or 15, priority_mode "balanced"
- "the vibe matters more than exact mileage" -> priority_mode "ride_character_first"
- "make it exactly 60 km if possible" -> priority_mode "distance_first", distance_flex_percent 0

{mission_block}
"""

    history = to_langchain_messages(messages_history, limit=6)
    chain = build_tactical_chain(model.with_response_format(json_schema), system_prompt)
    return chain.invoke({"chat_history": history}).strip()
