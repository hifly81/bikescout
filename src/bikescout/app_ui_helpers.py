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

import html
import os
import re
from pathlib import Path
from typing import Any, cast

import streamlit as st
from huggingface_hub import hf_hub_download

from bikescout.app_helpers import (
    compute_mission_intensity,
    compute_readiness_score,
    ext_cast,
)
from bikescout.app_llm import AVAILABLE_MODELS, LOCAL_MODELS_DIR, get_local_model_path
from bikescout.tools.terrain import CLIMB_PROFILE_MIN_LENGTH_M


def normalize_tire_setup(details: Any) -> dict[str, Any]:
    """Normalize structured or legacy tire setup payloads for display."""
    normalized: dict[str, Any] = {
        "wheel_label": "Standard",
        "tire_width_mm": None,
        "rim_internal_width_mm": None,
        "casing_type": "trail",
        "tubeless": True,
        "psi_front": None,
        "psi_rear": None,
        "bar_front": None,
        "bar_rear": None,
        "strategy": "Standard",
        "knob_choice": None,
        "advice": [],
        "warnings": [],
        "tactical_display": "",
    }

    data: Any = details
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    if isinstance(data, dict):
        normalized.update({key: value for key, value in data.items() if key in normalized})
        return normalized

    if isinstance(data, (list, tuple)) and len(data) > 1 and isinstance(data[1], str):
        raw_text = data[1]
        normalized["tire_width_mm"] = data[0]
        wheel_match = re.search(r"(\S+)\s*wheels", raw_text)
        front_match = re.search(r"F:\s*([\d.]+)\s*PSI", raw_text)
        rear_match = re.search(r"R:\s*([\d.]+)\s*PSI", raw_text)
        single_psi_match = re.search(r"([\d.]+)\s*PSI", raw_text)
        bar_match = re.search(r"\(([\d.]+)\s*Bar\)", raw_text)
        type_match = re.search(r"\[(.*?)\]", raw_text)

        if wheel_match:
            normalized["wheel_label"] = wheel_match.group(1)
        if front_match:
            normalized["psi_front"] = float(front_match.group(1))
        if rear_match:
            normalized["psi_rear"] = float(rear_match.group(1))
        if single_psi_match:
            single_psi = float(single_psi_match.group(1))
            normalized["psi_front"] = normalized["psi_front"] or single_psi
            normalized["psi_rear"] = normalized["psi_rear"] or single_psi
        if bar_match:
            normalized["bar_front"] = float(bar_match.group(1))
            normalized["bar_rear"] = normalized["bar_front"]
        if type_match:
            normalized["strategy"] = type_match.group(1).removesuffix(" Setup")
        normalized["tactical_display"] = raw_text

    return normalized


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --bg: #0b1020;
            --bg-soft: #121933;
            --card: rgba(20, 27, 52, 0.78);
            --card-2: rgba(30, 39, 72, 0.78);
            --border: rgba(148, 163, 184, 0.16);
            --text: #edf2ff;
            --muted: #aeb8d0;
            --primary: #7c3aed;
            --primary-2: #22c55e;
            --info: #38bdf8;
            --warn: #f59e0b;
            --danger: #ef4444;
            --radius: 18px;
            --shadow: 0 12px 40px rgba(0, 0, 0, 0.28);
        }

        .stApp, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top left, rgba(124, 58, 237, 0.18), transparent 30%),
                radial-gradient(circle at top right, rgba(34, 197, 94, 0.12), transparent 25%),
                linear-gradient(180deg, #0b1020 0%, #0f172a 100%) !important;
            color: var(--text) !important;
            font-family: 'Inter', system-ui, sans-serif !important;
        }

        [data-testid="stHeader"] {
            background: transparent !important;
            border: none !important;
        }

        footer, .stDeployButton, button[title="Change theme"] {
            visibility: hidden !important;
        }

        h1, h2, h3, h4, h5, h6, p, label, span, div {
            color: var(--text);
        }

        [data-testid="stSidebar"], 
        [data-testid="stSidebarContent"] {
            background:
                radial-gradient(circle at top left, rgba(124, 58, 237, 0.18), transparent 30%),
                radial-gradient(circle at top right, rgba(34, 197, 94, 0.12), transparent 25%),
                linear-gradient(180deg, #0b1020 0%, #0f172a 100%) !important;
            border-right: 1px solid var(--border);
        }

        .bs-hero {
            background: linear-gradient(135deg, rgba(124,58,237,0.18), rgba(34,197,94,0.10)), var(--card);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 24px 24px 18px 24px;
            box-shadow: var(--shadow);
            margin-bottom: 16px;
        }

        .bs-kicker {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #c4b5fd;
            font-weight: 700;
        }

        .bs-title {
            font-size: 2.5rem;
            font-weight: 800;
            line-height: 1.05;
            margin-top: 8px;
            margin-bottom: 8px;
        }

        .bs-subtitle {
            font-size: 1rem;
            line-height: 1.6;
            color: var(--muted);
            max-width: 800px;
        }

        .bs-chip-row {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 14px;
        }

        .bs-chip {
            background: rgba(255,255,255,0.06);
            border: 1px solid var(--border);
            color: var(--text);
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.82rem;
        }

        .bs-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 16px;
            box-shadow: var(--shadow);
        }

        .bs-card-title {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--muted);
            font-weight: 700;
            margin-bottom: 8px;
        }

        .bs-card-value {
            font-size: 1.4rem;
            font-weight: 800;
        }

        .bs-section-title {
            font-size: 1.15rem;
            font-weight: 800;
            margin: 14px 0 10px 0;
        }

        .stButton > button {
            border-radius: 12px !important;
            border: 1px solid var(--border) !important;
            font-weight: 700 !important;
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
            color: white !important;
            border: none !important;
        }

        div[data-testid="stForm"] {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.25rem;
        }

        [data-testid="stMetric"], .stExpander, [data-testid="stChatMessage"] {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
        }

        [data-testid="stChatInput"] textarea {
            background: var(--bg-soft) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-radius: 14px !important;
        }

        .bs-empty {
            background: rgba(255,255,255,0.04);
            border: 1px dashed var(--border);
            border-radius: 18px;
            padding: 18px;
            color: var(--muted);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_component_styles() -> None:
    """Injects custom CSS styles for BikeScout cards, HUDs, badges, and panels."""
    st.markdown(
        """
        <style>
        .bs-sidebar-brand {
            display: flex;
            align-items: baseline;
            gap: 0.18rem;
            margin-bottom: 0.35rem;
            line-height: 1;
        }

        .bs-sidebar-bike {
            font-size: 1.35rem;
            font-weight: 900;
            font-style: italic;
            text-transform: uppercase;
            letter-spacing: -0.06em;
            color: #ffffff;
        }

        .bs-sidebar-scout {
            font-size: 1.35rem;
            font-weight: 900;
            font-style: italic;
            text-transform: uppercase;
            letter-spacing: -0.04em;
            color: #4ade80;
            text-shadow:
                0 0 6px rgba(74, 222, 128, 0.75),
                0 0 12px rgba(34, 197, 94, 0.60),
                0 0 20px rgba(22, 163, 74, 0.50);
        }

        .bs-grid-gap { margin-top: 0.35rem; }

        .bs-panel {
            background: rgba(20, 27, 52, 0.78);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 20px;
            padding: 18px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.24);
            margin-bottom: 14px;
        }

        .bs-panel-title {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #a5b4fc;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .bs-section {
            margin-top: 16px;
            margin-bottom: 10px;
        }

        .bs-section h2 {
            margin: 0 0 8px 0 !important;
            font-size: 1.25rem !important;
            font-weight: 800 !important;
            line-height: 1.2 !important;
        }

        .bs-section p {
            color: #aeb8d0 !important;
            margin: 0 !important;
            font-size: 0.95rem !important;
        }

        /* Align form fields in multi-column guided forms */
        div[data-testid="stForm"] [data-testid="stHorizontalBlock"] {
            align-items: flex-end;
        }
        div[data-testid="stForm"] [data-testid="stHorizontalBlock"] > div {
            min-width: 0;
        }

        .bs-metric-card {
            position: relative;
            overflow: hidden;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: linear-gradient(180deg, rgba(30, 41, 59, 0.82), rgba(15, 23, 42, 0.9));
            padding: 16px;
            min-height: 110px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.22);
        }

        .bs-metric-card::after {
            content: "";
            position: absolute;
            inset: 0 auto auto 0;
            width: 100%;
            height: 4px;
            background: var(--accent, #7c3aed);
            opacity: 0.95;
        }

        .bs-metric-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }

        .bs-metric-label {
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #9fb0d1;
            font-weight: 800;
        }

        .bs-metric-icon {
            font-size: 1.1rem;
            opacity: 0.95;
        }

        .bs-metric-value {
            margin-top: 12px;
            font-size: 1.7rem;
            font-weight: 900;
            line-height: 1.05;
            color: #f8fbff;
        }

        .bs-metric-sub {
            margin-top: 8px;
            font-size: 0.86rem;
            color: #aeb8d0;
        }

        .bs-score-card {
            border-radius: 22px;
            padding: 20px;
            background:
                radial-gradient(circle at top left, rgba(124,58,237,0.25), transparent 35%),
                linear-gradient(135deg, rgba(30,41,59,0.92), rgba(15,23,42,0.98));
            border: 1px solid rgba(148, 163, 184, 0.16);
            box-shadow: 0 12px 40px rgba(0,0,0,0.26);
        }

        .bs-score-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #c4b5fd;
            font-weight: 800;
        }

        .bs-score-value {
            font-size: 3rem;
            font-weight: 900;
            margin-top: 8px;
            line-height: 1;
        }

        .bs-score-sub {
            margin-top: 8px;
            font-size: 0.95rem;
            color: #cbd5e1;
        }

        .bs-badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }

        .bs-badge {
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.78rem;
            font-weight: 700;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(255,255,255,0.06);
        }

        .bs-badge.safe { color: #86efac; }
        .bs-badge.warn { color: #fde68a; }
        .bs-badge.risk { color: #fca5a5; }
        .bs-badge.info { color: #93c5fd; }

        .bs-mini-kpi {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 16px;
            padding: 12px 14px;
            min-height: 84px;
        }

        .bs-mini-kpi .k-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #9fb0d1;
            font-weight: 800;
        }

        .bs-mini-kpi .k-value {
            margin-top: 8px;
            font-size: 1.15rem;
            font-weight: 800;
            color: #f8fbff;
        }

        .bs-poi-card {
            background: linear-gradient(180deg, rgba(30,41,59,0.78), rgba(15,23,42,0.9));
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-left: 4px solid var(--poi-accent, #38bdf8);
            border-radius: 16px;
            padding: 14px 14px 12px 14px;
            min-height: 140px;
            box-shadow: 0 8px 28px rgba(0,0,0,0.18);
        }

        .bs-poi-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
        }

        .bs-poi-title {
            font-size: 0.98rem;
            font-weight: 800;
            line-height: 1.25;
        }

        .bs-poi-type {
            margin-top: 4px;
            color: #9fb0d1;
            font-size: 0.82rem;
        }

        .bs-poi-distance {
            margin-top: 10px;
            font-size: 0.86rem;
            font-weight: 800;
            color: var(--poi-accent, #38bdf8);
        }

        .bs-poi-actions {
            margin-top: 12px;
            font-size: 0.84rem;
        }

        .bs-risk-box {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 16px;
            padding: 14px;
            min-height: 120px;
        }

        .bs-risk-title {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #9fb0d1;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .bs-risk-value {
            font-size: 1.1rem;
            font-weight: 800;
            margin-bottom: 6px;
        }

        .bs-risk-copy {
            color: #cbd5e1;
            font-size: 0.9rem;
            line-height: 1.45;
        }

        .bs-weather-strip {
            display: flex;
            gap: 10px;
            overflow-x: auto;
            padding-bottom: 4px;
        }

        .bs-weather-tile {
            min-width: 128px;
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(255,255,255,0.04);
            padding: 12px;
        }

        .bs-weather-time {
            font-size: 0.78rem;
            color: #9fb0d1;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .bs-weather-temp {
            margin-top: 10px;
            font-size: 1.3rem;
            font-weight: 900;
        }

        .bs-weather-meta {
            margin-top: 6px;
            font-size: 0.84rem;
            color: #cbd5e1;
            line-height: 1.45;
        }

        .bs-surface-row {
            margin-bottom: 12px;
        }

        .bs-callout {
            border-radius: 18px;
            padding: 16px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: linear-gradient(135deg, rgba(34,197,94,0.08), rgba(56,189,248,0.06));
        }

        .bs-callout strong {
            display: block;
            margin-bottom: 6px;
        }

        .bs-hud {
            margin: 0.1rem 0 1rem 0;
            padding: 0.9rem 1rem;
            border-radius: 18px;
            background:
                linear-gradient(135deg, rgba(17, 24, 39, 0.92), rgba(15, 23, 42, 0.88)),
                radial-gradient(circle at top right, rgba(34, 197, 94, 0.10), transparent 35%);
            border: 1px solid rgba(148, 163, 184, 0.14);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
        }

        .bs-hud-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.7rem;
        }

        .bs-hud-kicker {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #86efac;
            font-weight: 800;
            margin-bottom: 0.18rem;
        }

        .bs-hud-title {
            font-size: 1.15rem;
            font-weight: 900;
            font-style: italic;
            letter-spacing: -0.03em;
            color: #ffffff;
        }

        .bs-hud-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
            gap: 0.55rem;
        }

        .bs-hud-chip {
            padding: 0.55rem 0.7rem;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(148, 163, 184, 0.10);
        }

        .bs-hud-chip span {
            display: block;
            font-size: 0.64rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted, #9fb0d1);
            margin-bottom: 0.15rem;
        }

        .bs-hud-chip strong {
            display: block;
            font-size: 0.92rem;
            font-weight: 800;
            color: #f8fafc;
        }

        .bs-intensity-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.55rem 0.9rem;
            border-radius: 999px;
            background: color-mix(in srgb, var(--badge-color) 16%, rgba(15, 23, 42, 0.92));
            border: 1px solid color-mix(in srgb, var(--badge-color) 45%, rgba(255, 255, 255, 0.10));
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
            margin-bottom: 0.75rem;
        }

        .bs-intensity-dot {
            width: 0.6rem;
            height: 0.6rem;
            border-radius: 999px;
            background: var(--badge-color);
            box-shadow: 0 0 12px var(--badge-color);
            display: inline-block;
        }

        .bs-intensity-label {
            font-size: 0.78rem;
            font-weight: 900;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: #f8fafc;
        }

        .bs-warning-ribbon {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 1rem;
        }

        .bs-warning-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.45rem 0.7rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            color: #f8fafc;
            background: color-mix(in srgb, var(--chip-color) 14%, rgba(15, 23, 42, 0.92));
            border: 1px solid color-mix(in srgb, var(--chip-color) 38%, rgba(255, 255, 255, 0.10));
            line-height: 1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="bs-empty">
            <strong>{title}</strong><br/>
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_poi_style(poi_type: str) -> tuple[str, str]:
    t = poi_type.lower()
    if "water" in t or "fontan" in t or "drink" in t:
        return "💧", "#38bdf8"
    if "shop" in t or "repair" in t or "bike" in t or "meccan" in t:
        return "🔧", "#f59e0b"
    if "food" in t or "restaur" in t or "bar" in t or "caf" in t:
        return "☕", "#22c55e"
    if "shelter" in t or "hotel" in t or "camp" in t:
        return "🏠", "#a78bfa"
    if "hospital" in t or "first aid" in t or "med" in t:
        return "🚨", "#ef4444"
    return "📍", "#94a3b8"


def get_surface_icon(surface_type: str) -> str:
    s = surface_type.lower()
    if "asphalt" in s or "tarmac" in s or "paved" in s:
        return "🛣️"
    if "gravel" in s or "sterrato" in s:
        return "🪨"
    if "dirt" in s or "trail" in s or "singletrack" in s:
        return "🌲"
    if "mud" in s:
        return "🟤"
    if "sand" in s:
        return "🏖️"
    return "🗺️"


def metric_card(label: str, value: str, icon: str, accent: str, sub: str = "") -> None:
    st.markdown(
        f"""
        <div class="bs-metric-card" style="--accent:{accent};">
            <div class="bs-metric-top">
                <div class="bs-metric-label">{label}</div>
                <div class="bs-metric-icon">{icon}</div>
            </div>
            <div class="bs-metric-value">{value}</div>
            <div class="bs-metric-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_intro(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="bs-section">
            <h2>{html.escape(title)}</h2>
            <p>{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_card(score: int, status: str, badges: list[str]) -> None:
    color = "#22c55e" if status == "Go" else "#f59e0b" if status == "Caution" else "#ef4444"
    st.markdown(
        f"""
        <div class="bs-score-card">
            <div class="bs-score-label">Ride readiness score</div>
            <div class="bs-score-value" style="color:{color};">{score}/100</div>
            <div class="bs-score-sub">Decision: <strong>{status}</strong></div>
            <div class="bs-badge-row">
                {"".join([f'<div class="bs-badge {"safe" if status == "Go" else "warn" if status == "Caution" else "risk"}">{b}</div>' for b in badges[:5]])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mission_intensity_badge(label: str, color: str) -> None:
    html = f"""
    <div class="bs-intensity-badge" style="--badge-color:{color};">
        <span class="bs-intensity-dot"></span>
        <span class="bs-intensity-label">{label}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_warning_ribbon(warnings: list[tuple[str, str]]) -> None:
    if not warnings:
        return

    chips_html = "".join(
        f'<div class="bs-warning-chip" style="--chip-color:{color};">{text}</div>'
        for text, color in warnings
    )

    html = f"""
    <div class="bs-warning-ribbon">
        {chips_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def build_warning_ribbon(info: dict, conditions: dict, logistics: dict) -> list[tuple[str, str]]:
    warnings = []

    safety = conditions.get("safety_advice", {}) or {}
    wind_risk = ext_cast(safety.get("wind_risk_score"), float, 0)
    if wind_risk >= 7:
        warnings.append(("High wind exposure", "#f59e0b"))
    elif wind_risk >= 4:
        warnings.append(("Moderate wind exposure", "#fbbf24"))

    mud_data = conditions.get("mud_risk", {}) or {}
    tactical_mud = mud_data.get("tactical_analysis", {}) or {}
    mud_level = str(tactical_mud.get("mud_risk_score", "")).lower()
    if "high" in mud_level:
        warnings.append(("High mud risk", "#8b5cf6"))
    elif "medium" in mud_level:
        warnings.append(("Moderate mud risk", "#a78bfa"))

    ascent = ext_cast(info.get("ascent_m"), float, 0)
    if ascent >= 1800:
        warnings.append(("Major climbing load", "#fb7185"))
    elif ascent >= 900:
        warnings.append(("Sustained climbing", "#f97316"))

    pois = logistics.get("nearby_amenities", {}) or []
    if isinstance(pois, list) and len(pois) <= 2:
        warnings.append(("Limited support coverage", "#38bdf8"))

    nutrition = logistics.get("nutrition_plan", {}) or {}
    if nutrition:
        briefing_nut = nutrition.get("mission_nutrition_briefing", {}) or {}
        fluids = briefing_nut.get("fluids", {}) or {}
        total_liters = ext_cast(fluids.get("total_liters"), float, 0)
        if total_liters >= 2.5:
            warnings.append(("High hydration demand", "#06b6d4"))

    surface_analysis = info.get("surface_analysis", {}) or {}
    mechanical = surface_analysis.get("mechanical_setup", {}) or {}
    if mechanical and not mechanical.get("compatible", True):
        warnings.append(("Bike setup mismatch", "#ef4444"))

    return warnings[:5]


def render_weather_tiles_native(weather_data) -> None:
    if not weather_data:
        return

    rows = [weather_data[i : i + 5] for i in range(0, len(weather_data), 5)]

    for row in rows:
        cols = st.columns(len(row))
        for idx, w in enumerate(row):
            with cols[idx]:
                time_label = str(w.get("time", "Time"))
                temp_raw = _format_weather_metric(w.get("temp"), "°C", 1)
                app_raw = _format_weather_metric(w.get("app_temp"), "°C", 1)
                rain_raw = _format_weather_metric(w.get("rain_prob"), "%", 0)
                wind_raw = _format_weather_metric(w.get("wind", w.get("wind_speed")), " km/h", 1)
                condition = str(w.get("condition") or "")

                st.markdown(
                    f"""
                    <div class="bs-risk-box">
                        <div class="bs-risk-title">{time_label}</div>
                        <div class="bs-risk-value">{temp_raw}</div>
                        <div class="bs-risk-copy">
                            Apparent: {app_raw}<br/>
                            Rain: {rain_raw}<br/>
                            Wind: {wind_raw}<br/>
                            {condition}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _format_weather_metric(value: Any, unit: str, decimals: int) -> str:
    """Format a numeric forecast value with its metric unit, or N/A when absent."""
    number = ext_cast(value, float, None)
    if number is None:
        return "N/A"
    return f"{number:.{decimals}f}{unit}"


def render_rider_profile_fields() -> None:
    """Render rider defaults inside the guided Plan a Ride tab."""
    profile = st.session_state["rider_profile"]

    fitness_options = ["beginner", "intermediate", "pro"]
    current_fitness = profile.get("fitness_level", "intermediate")
    if current_fitness not in fitness_options:
        current_fitness = "intermediate"
    gender_options = ["male", "female"]
    current_gender = profile.get("gender", "male")
    if current_gender not in gender_options:
        current_gender = "male"

    st.markdown("### Rider profile")
    st.caption("Defaults for guided planning. In chat, state your details in the message.")
    rider_col, weight_col, gender_col, sweat_col = st.columns(4)
    with rider_col:
        profile["fitness_level"] = st.selectbox(
            "Fitness level",
            fitness_options,
            index=fitness_options.index(current_fitness),
            key="rider_profile_fitness_level",
        )
    with weight_col:
        profile["weight_kg"] = st.number_input(
            "Weight (kg)",
            min_value=40.0,
            max_value=150.0,
            value=ext_cast(profile.get("weight_kg"), float, 75.0),
            key="rider_profile_weight",
        )
    with gender_col:
        profile["gender"] = st.selectbox(
            "Gender",
            gender_options,
            index=gender_options.index(current_gender),
            key="rider_profile_gender",
        )
    with sweat_col:
        measured_rate = st.number_input(
            "Measured sweat (ml/h)",
            min_value=0.0,
            max_value=5000.0,
            value=ext_cast(profile.get("sweat_rate_ml_per_hour"), float, 0.0),
            help="Optional timed weigh-in result; 0 means use the population estimate.",
            key="rider_profile_sweat_rate",
        )
        profile["sweat_rate_ml_per_hour"] = measured_rate or None

    st.session_state["rider_profile"] = profile


def render_sidebar() -> tuple[str, int]:
    with st.sidebar:
        st.markdown(
            """
            <div class="bs-sidebar-brand">
                <span class="bs-sidebar-bike">Bike</span><span class="bs-sidebar-scout">Scout</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("AI for tactical cycling intelligence")

        st.subheader("Routing & API")
        ors_key = st.text_input(
            "OpenRouteService key",
            value=st.session_state.get("ors_api_key", ""),
            type="password",
            help="Required for routing, geocoding, and trail analysis.",
        )
        if ors_key:
            st.session_state["ors_api_key"] = ors_key
            os.environ["ORS_API_KEY"] = ors_key

        st.subheader("Local model")
        selected_model_name = cast(str, st.selectbox("Model", list(AVAILABLE_MODELS.keys())))
        st.caption(AVAILABLE_MODELS[selected_model_name]["description"])

        gpu_enabled = st.toggle("GPU acceleration", value=True)
        n_layers = -1 if gpu_enabled else 0

        model_path = get_local_model_path(selected_model_name)
        if not os.path.exists(model_path):
            if st.button(f"Download {selected_model_name}", use_container_width=True):
                with st.status("Downloading local model...", expanded=True):
                    os.makedirs(LOCAL_MODELS_DIR, exist_ok=True)
                    hf_hub_download(
                        repo_id=AVAILABLE_MODELS[selected_model_name]["repo"],
                        filename=AVAILABLE_MODELS[selected_model_name]["file"],
                        local_dir=LOCAL_MODELS_DIR,
                    )
                    st.success("Model downloaded. Reloading...")
                    st.rerun()
            st.warning("A local model is required to use the chat planner.")

        if st.button("Clear chat & mission", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["mission_context"] = {}
            st.session_state["mission_history"] = []
            st.session_state["last_location_query"] = None
            st.session_state["last_raw_distance"] = 25.0
            st.rerun()

        return selected_model_name, n_layers


def _is_number(value) -> bool:
    """Return True for real numbers, excluding booleans."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _format_terrain_value(value, digits: int = 1, suffix: str = "") -> str:
    """Format an optional terrain number for display."""
    if not _is_number(value):
        return "N/A"
    return f"{float(value):.{digits}f}{suffix}"


def _format_terrain_percent(value) -> str:
    """Format a 0.0-1.0 confidence score as a percentage."""
    if not _is_number(value):
        return "N/A"
    return f"{float(value) * 100:.0f}%"


def _terrain_climbs(tactical_briefing: dict, terrain_analysis: dict) -> list[dict[str, Any]]:
    """Return the geometry-detected climbs used by the Streamlit climb list."""
    climbs = (
        tactical_briefing.get("climb_list")
        or terrain_analysis.get("climbs")
        or terrain_analysis.get("climb_list")
        or []
    )
    return [climb for climb in climbs if isinstance(climb, dict)]


def _climb_start_elevation(climb: dict[str, Any]) -> float | None:
    """Derive the climb base elevation from the terrain engine's summit and gain."""
    summit = climb.get("summit_elevation_m")
    gain = climb.get("gain_m")
    if not _is_number(summit) or not _is_number(gain):
        return None
    return float(cast(float, summit)) - float(cast(float, gain))


def _terrain_climb_rows(tactical_briefing: dict, terrain_analysis: dict) -> list[dict[str, str]]:
    """Format geometry-detected climbs for the Streamlit climb list table."""
    rows: list[dict[str, str]] = []
    for number, climb in enumerate(_terrain_climbs(tactical_briefing, terrain_analysis), start=1):
        length_m = climb.get("length_m")
        length_km = None
        if isinstance(length_m, (int, float)) and not isinstance(length_m, bool):
            length_km = length_m / 1000.0
        rows.append(
            {
                "#": str(number),
                "Category": str(climb.get("category", "N/A")),
                "Gain (m)": _format_terrain_value(climb.get("gain_m")),
                "Length (km)": _format_terrain_value(length_km, 2),
                "Avg grade": _format_terrain_value(climb.get("avg_gradient"), 1, "%"),
                "Start (m)": _format_terrain_value(_climb_start_elevation(climb)),
                "Summit (m)": _format_terrain_value(climb.get("summit_elevation_m")),
                "FIETS": _format_terrain_value(climb.get("fiets_index"), 2),
                "Profile samples": f"{climb.get('start_index', '?')}–{climb.get('end_index', '?')}",
            }
        )
    return rows


def _empty_dataframe_selection() -> dict[str, dict[str, list[Any]]]:
    """Return the session-state value that clears a dataframe row selection."""
    return {"selection": {"rows": [], "columns": [], "cells": []}}


def reset_climb_profile_state() -> None:
    """Clear the climb-list selection before rendering a new mission result."""
    st.session_state["climb_list_table"] = _empty_dataframe_selection()
    st.session_state.pop("climb_profile_handled_selection", None)


def _climb_chart_path(res_data: dict, number: int) -> str | None:
    """Locate the per-climb PNG generated beside the mission elevation profile."""
    profile_path = res_data.get("elevation_profile_path")
    if not isinstance(profile_path, str) or not profile_path:
        return None
    return str(Path(profile_path).with_name(f"{Path(profile_path).stem}_climb_{number}.png"))


def _nutrition_note(briefing: dict) -> str | None:
    """Build a compact evidence and uncertainty note for the fueling plan."""
    parts: list[str] = []
    basis = briefing.get("data_basis")
    confidence = briefing.get("estimate_confidence")
    uncertainty = briefing.get("uncertainty_note")
    if isinstance(basis, str) and basis:
        parts.append(basis)
    if isinstance(confidence, str) and confidence:
        parts.append(f"Confidence: {confidence}.")
    if isinstance(uncertainty, str) and uncertainty:
        parts.append(uncertainty)
    return " ".join(parts) or None


def render_gonogo_report(gonogo: dict[str, Any] | None, error: str | None = None) -> None:
    """Render a Go/No-Go planner report in the Streamlit UI."""
    if error:
        st.warning(f"Go/No-Go report unavailable: {error}")
        return
    if not isinstance(gonogo, dict):
        st.warning("Go/No-Go report unavailable.")
        return

    if gonogo.get("status") != "Success":
        msg = str(gonogo.get("message") or "Go/No-Go planning failed.")
        next_step = gonogo.get("next_step")
        st.error(msg)
        if next_step:
            st.info(f"**Next step:** {next_step}")
        return

    report = gonogo.get("planner_report") or {}
    metadata = gonogo.get("metadata") or {}
    briefing = report.get("environmental_briefing") or {}
    verdict = str(report.get("verdict") or "UNKNOWN").upper()
    tactical_color = str(report.get("tactical_color") or "RED").upper()
    best_window = str(report.get("best_window") or "N/A")
    confidence = str(report.get("confidence_score") or "0/100")
    mud_impact = str(report.get("mud_risk_impact") or "Unavailable")

    color = (
        "#22c55e"
        if tactical_color == "GREEN"
        else "#f59e0b"
        if tactical_color == "YELLOW"
        else "#ef4444"
    )
    verdict_label = "Go" if verdict == "GO" else "Caution" if verdict == "CAUTION" else "No-Go"

    st.markdown(
        f"""
        <div class="bs-score-card" style="margin-top:0.25rem;">
            <div class="bs-score-label">Go/No-Go verdict</div>
            <div class="bs-score-value" style="color:{color};">{html.escape(verdict_label)}</div>
            <div class="bs-score-sub">Confidence: {html.escape(confidence)} · Best window: {html.escape(best_window)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Rain avg", str(briefing.get("rain_avg") or "N/A"), "🌧️", "#38bdf8")
    with c2:
        metric_card("Wind max", str(briefing.get("wind_max") or "N/A"), "💨", "#a78bfa")
    with c3:
        metric_card("Temp avg", str(briefing.get("temp_avg") or "N/A"), "🌡️", "#f59e0b")
    with c4:
        metric_card("Mud impact", mud_impact, "🟤", "#d97706", "TAEL mm index")

    briefing_message = briefing.get("message")
    if briefing_message:
        if verdict == "GO":
            st.success(str(briefing_message))
        elif verdict == "CAUTION":
            st.warning(str(briefing_message))
        else:
            st.error(str(briefing_message))

    solar = metadata.get("solar_window")
    mud_status = metadata.get("mud_status")
    mud_conf = metadata.get("model_confidence")
    caption_parts = []
    if solar:
        caption_parts.append(f"Solar window: {solar}")
    if mud_status:
        caption_parts.append(f"Mud status: {mud_status}")
    if mud_conf:
        caption_parts.append(f"Mud confidence: {mud_conf}")
    if caption_parts:
        st.caption(" · ".join(str(p) for p in caption_parts))


def _altimetry_caption(res_data: dict) -> str | None:
    """Build a compact data-credit and uncertainty note for the elevation chart."""
    source = res_data.get("elevation_source")
    interpolated = res_data.get("elevation_samples_interpolated")
    total = res_data.get("elevation_samples_total")

    parts: list[str] = []
    if isinstance(source, str) and source:
        parts.append(source)
    if isinstance(interpolated, int) and interpolated > 0 and isinstance(total, int):
        parts.append(f"{interpolated} of {total} elevation samples estimated from neighbours.")
    return " ".join(parts) or None


@st.dialog("Climb profile", icon=":material/show_chart:", width="medium")
def _render_climb_profile_dialog(number: int, climb: dict[str, Any], chart_path: str) -> None:
    """Show the elevation profile generated for a single long climb."""
    start = _format_terrain_value(_climb_start_elevation(climb))
    summit = _format_terrain_value(climb.get("summit_elevation_m"))
    length_km = _format_terrain_value(
        float(climb["length_m"]) / 1000.0 if _is_number(climb.get("length_m")) else None,
        2,
        " km",
    )
    gain = _format_terrain_value(climb.get("gain_m"))

    st.caption(f"Climb {number} · {str(climb.get('category', 'N/A'))}")
    st.caption(f"{start} m → {summit} m · {length_km} · {gain} m gained")
    st.image(chart_path, caption="Elevation profile", width="stretch")


@st.fragment
def render_route_results(res_data: dict) -> None:
    info = res_data.get("info", {}) or {}
    logistics = res_data.get("logistics", {}) or {}
    conditions = res_data.get("conditions", {}) or {}

    if not info:
        st.warning("Route not found.")
        return

    score, status, badges = compute_readiness_score(info, conditions, logistics)

    intensity_label, intensity_color = compute_mission_intensity(info, conditions, logistics)
    warning_items = build_warning_ribbon(info, conditions, logistics)

    route_type = str(info.get("route_type", "Round Trip"))
    distance_km = info.get("distance_km", "N/A")
    ascent_m = info.get("ascent_m", "N/A")
    difficulty = info.get("difficulty", "N/A")

    weather_data = (conditions.get("weather") or []) if conditions else []
    safety_advice = conditions.get("safety_advice", {}) if conditions else {}
    mud_data = conditions.get("mud_risk", {}) if conditions else {}
    surface_analysis = info.get("surface_analysis", {}) or {}

    weather_summary = safety_advice.get("status", "Stable") if safety_advice else "Stable"
    surface_mix = "Mixed terrain" if surface_analysis else "Standard route"

    st.markdown(
        f"""
        <div class="bs-hud">
            <div class="bs-hud-top">
                <div class="bs-hud-title-wrap">
                    <div class="bs-hud-kicker">TACTICAL MISSION OVERVIEW</div>
                    <div class="bs-hud-title">{route_type}</div>
                </div>
            </div>
            <div class="bs-hud-grid">
                <div class="bs-hud-chip">
                    <span>Distance</span>
                    <strong>{distance_km} km</strong>
                </div>
                <div class="bs-hud-chip">
                    <span>Ascent</span>
                    <strong>{ascent_m} m</strong>
                </div>
                <div class="bs-hud-chip">
                    <span>Difficulty</span>
                    <strong>{difficulty}</strong>
                </div>
                <div class="bs-hud-chip">
                    <span>Weather</span>
                    <strong>{weather_summary}</strong>
                </div>
                <div class="bs-hud-chip">
                    <span>Terrain</span>
                    <strong>{surface_mix}</strong>
                </div>
                <div class="bs-hud-chip">
                    <span>Readiness</span>
                    <strong>{status}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_left, top_right = st.columns([1, 3])
    with top_left:
        render_mission_intensity_badge(intensity_label, intensity_color)
    with top_right:
        render_warning_ribbon(warning_items)

    section_intro(
        "Mission summary",
        "High-level overview before diving into terrain, weather, mud, and support logistics.",
    )

    c0, c1 = st.columns([1.05, 2.15])
    with c0:
        render_score_card(score, status, badges)

    with c1:
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            metric_card("Distance", f"{distance_km} km", "📏", "#38bdf8", "Target route length")
        with g2:
            metric_card("Ascent", f"{ascent_m} m", "⛰️", "#a78bfa", "Total elevation gain")
        with g3:
            metric_card("Difficulty", str(difficulty), "⚡", "#f472b6", "Estimated route challenge")
        with g4:
            metric_card("Route type", route_type, "🧭", "#22c55e", "Loop or A→B")

    st.markdown('<div class="bs-grid-gap"></div>', unsafe_allow_html=True)

    if surface_analysis:
        section_intro(
            "Terrain intelligence", "Surface mix, gradient profile, and tactical setup signals."
        )

        tactical = surface_analysis.get("tactical_briefing", {}) or {}
        terrain = tactical.get("terrain_analysis", {}) or {}
        metadata = surface_analysis.get("metadata", {}) or {}
        elevation_source = metadata.get("elevation_source")

        max_gradient = tactical.get("max_gradient", terrain.get("max_gradient"))
        confidence = tactical.get("data_confidence", terrain.get("data_confidence"))
        technical = (
            tactical.get("technical_difficulty") or terrain.get("technical_difficulty") or {}
        )
        if not isinstance(technical, dict):
            technical = {}

        noise_floor = terrain.get("noise_floor_m")
        profile_points = terrain.get("profile_points")
        profile_length_m = terrain.get("profile_length_m")
        profile_length_km = None
        if isinstance(profile_length_m, (int, float)) and not isinstance(profile_length_m, bool):
            profile_length_km = profile_length_m / 1000.0
        terrain_warnings = [str(warning) for warning in (terrain.get("warnings", []) or [])]

        r1, r2, r3, r4 = st.columns(4)

        with r1:
            metric_card(
                "Avg gradient",
                str(tactical.get("avg_gradient", "N/A")),
                "📈",
                "#2dd4bf",
                "Overall gradient profile",
            )
        with r2:
            metric_card(
                "Climb profile",
                str(tactical.get("climb_category", "N/A")),
                "🧗",
                "#fb923c",
                "Climbing classification",
            )
        with r3:
            metric_card(
                "Climb gradient",
                str(tactical.get("avg_climb_gradient", "N/A")),
                "🔺",
                "#f87171",
                "Climbing intensity",
            )
        with r4:
            metric_card(
                "Max gradient",
                f"{max_gradient}%" if max_gradient is not None else "N/A",
                "⚡",
                "#facc15",
                "Steepest measured pitch",
            )

        q1, q2, q3, q4 = st.columns(4)

        with q1:
            confidence_sub = (
                f"Noise floor {noise_floor} m"
                if noise_floor is not None
                else "Elevation trust score"
            )
            metric_card(
                "Data confidence",
                _format_terrain_percent(confidence),
                "🧪",
                "#22d3ee",
                confidence_sub,
            )
        with q2:
            tech_confidence = technical.get("confidence")
            tech_source = str(technical.get("source", ""))
            tech_sub = "Terrain grade confidence"
            if _is_number(tech_confidence):
                tech_sub = f"{_format_terrain_percent(tech_confidence)} confidence"
                if tech_source:
                    tech_sub += f" · {tech_source}"
            metric_card(
                "Technical grade",
                str(technical.get("label", "N/A")),
                "🥷",
                "#c084fc",
                tech_sub,
            )
        with q3:
            metric_card(
                "Profile length",
                _format_terrain_value(profile_length_km, 2, " km"),
                "🛰️",
                "#60a5fa",
                "Analyzed route geometry",
            )
        with q4:
            metric_card(
                "Profile points",
                str(profile_points) if profile_points is not None else "N/A",
                "🔬",
                "#fbbf24",
                "Usable elevation samples",
            )

        if elevation_source:
            st.caption(f"Elevation source: {elevation_source}")

        with st.expander("Climb list", expanded=True):
            climbs = _terrain_climbs(tactical, terrain)
            climb_rows = _terrain_climb_rows(tactical, terrain)
            if not climb_rows:
                st.info("No significant climbs detected or climb data unavailable.")
            else:
                selection = st.dataframe(
                    climb_rows,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="climb_list_table",
                )
                selected_rows = list(selection.selection.rows)
                if selected_rows:
                    row_index = int(selected_rows[0])
                    profile_path = res_data.get("elevation_profile_path")
                    signature = (str(profile_path or ""), row_index)
                    if st.session_state.get("climb_profile_handled_selection") != signature:
                        st.session_state["climb_profile_handled_selection"] = signature
                        number = row_index + 1
                        chart_path = _climb_chart_path(res_data, number)
                        climb = climbs[row_index] if row_index < len(climbs) else {}
                        is_long_climb = (
                            _is_number(climb.get("length_m"))
                            and float(climb["length_m"]) >= CLIMB_PROFILE_MIN_LENGTH_M
                        )
                        if chart_path and os.path.exists(chart_path) and is_long_climb:
                            _render_climb_profile_dialog(number, climb, chart_path)
                        else:
                            st.caption(
                                "An elevation profile is available only for climbs of at least 1.00 km."
                            )

        if terrain_warnings:
            with st.expander("Terrain warnings", expanded=True):
                for warning in terrain_warnings:
                    st.warning(warning)

        surfaces = surface_analysis.get("surface_breakdown", []) or []
        if surfaces:
            with st.expander("Surface breakdown", expanded=True):
                for s in surfaces:
                    s_type = s.get("type", "Unknown")
                    s_pct_str = str(s.get("percentage", "0%"))
                    icon = get_surface_icon(s_type)
                    try:
                        pct_val = float(s_pct_str.replace("%", "").strip()) / 100.0
                    except Exception:
                        pct_val = 0.0

                    st.markdown(
                        f'<div class="bs-surface-row"><strong>{icon} {s_type}</strong></div>',
                        unsafe_allow_html=True,
                    )
                    st.progress(max(0.0, min(1.0, pct_val)), text=s_pct_str)

        mechanical = surface_analysis.get("mechanical_setup", {}) or {}
        if mechanical:
            with st.expander("Mechanical setup", expanded=True):
                setup = normalize_tire_setup(mechanical.get("setup_details"))
                wheel_label = str(setup.get("wheel_label") or "Standard")
                tire_width_mm = setup.get("tire_width_mm")
                tire_label = f"{wheel_label} · {tire_width_mm}mm" if tire_width_mm else wheel_label

                psi_front = setup.get("psi_front")
                psi_rear = setup.get("psi_rear")
                pressure_label = (
                    f"F: {psi_front} / R: {psi_rear} PSI"
                    if psi_front is not None and psi_rear is not None
                    else "N/A"
                )
                bar_front = setup.get("bar_front")
                bar_rear = setup.get("bar_rear")
                bar_label = (
                    f"≈ {bar_front}/{bar_rear} Bar"
                    if bar_front is not None and bar_rear is not None
                    else ""
                )

                m1, m2, m3 = st.columns(3)
                with m1:
                    metric_card("Wheels / tires", tire_label, "🛞", "#60a5fa", "Volume-based setup")
                with m2:
                    metric_card("Pressure F / R", pressure_label, "🔩", "#34d399", bar_label)
                with m3:
                    metric_card(
                        "Setup strategy",
                        str(setup.get("strategy") or "Standard"),
                        "🧰",
                        "#f59e0b",
                        "Terrain optimization",
                    )

                if setup.get("knob_choice"):
                    st.caption(f"Tread choice: **{setup['knob_choice']}**")
                confidence = setup.get("confidence")
                model_basis = setup.get("model_basis")
                if confidence or model_basis:
                    st.caption(
                        f"Model: **{confidence or 'N/A'}** confidence"
                        + (f" — {model_basis}" if model_basis else "")
                    )

                advice = [str(item) for item in (setup.get("advice") or [])]
                if advice:
                    st.markdown("**Setup intelligence**")
                    for item in advice:
                        st.markdown(f"- {item}")

                if not mechanical.get("compatible", True):
                    st.error(
                        "This bike/setup may not be fully compatible with the current route profile."
                    )

                warnings = []
                for warning in list(setup.get("warnings") or []) + list(
                    mechanical.get("safety_warnings") or []
                ):
                    if warning and warning not in terrain_warnings and warning not in warnings:
                        warnings.append(warning)
                for warning in warnings:
                    st.warning(warning)

        emtb_tactical = surface_analysis.get("emtb_tactical", {}) or {}
        if emtb_tactical and emtb_tactical.get("status") == "Success":
            with st.expander("eMTB tactical analytics", expanded=True):
                advice = emtb_tactical.get("tactical_advice", "No tactical advice available")
                st.markdown(
                    f"""
                    <div class="bs-callout">
                        <strong>Battery strategy</strong>
                        {advice}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                b_metrics = emtb_tactical.get("battery_metrics", {}) or {}
                assumptions = emtb_tactical.get("assumptions", {}) or {}
                e1, e2, e3 = st.columns(3)
                with e1:
                    metric_card(
                        "Estimated drain",
                        f"{b_metrics.get('estimated_drain_wh', 0):.1f} Wh",
                        "🔋",
                        "#38bdf8",
                    )
                with e2:
                    metric_card(
                        "Remaining battery",
                        f"{b_metrics.get('remaining_battery_pct', 0):.1f}%",
                        "⚡",
                        "#22c55e",
                    )
                with e3:
                    metric_card(
                        "Usable capacity",
                        f"{b_metrics.get('usable_wh_at_temp', 0):.1f} Wh",
                        "🌡️",
                        "#a78bfa",
                    )
                if assumptions:
                    st.caption(
                        "Battery estimate assumptions: "
                        f"speed {assumptions.get('avg_speed_kmh', 'N/A')} km/h, "
                        f"temp {assumptions.get('ambient_temp_c', 'N/A')} °C, "
                        f"FTP {assumptions.get('rider_ftp_w', 'N/A')} W, "
                        f"intensity {assumptions.get('intensity_score', 'N/A')}/5, "
                        f"motor limit {assumptions.get('motor_power_limit_w', 'N/A')} W. "
                        f"Confidence: {assumptions.get('confidence', 'low')}."
                    )

    if weather_data:
        section_intro(
            "Weather & safety",
            "Full-day tactical conditions for confidence, pacing, and kit planning.",
        )

        with st.expander("Forecast details", expanded=True):
            peak_temp = None
            max_rain = None

            for w in weather_data:
                peak_temp = max(peak_temp or -999, ext_cast(w.get("temp"), float, -999))
                max_rain = max(max_rain or -999, ext_cast(w.get("rain_prob"), float, -999))

            t1, t2, t3 = st.columns(3)

            with t1:
                metric_card(
                    "Peak temp",
                    f"{peak_temp if peak_temp != -999 else 'N/A'} °C",
                    "🌡️",
                    "#f97316",
                    "Max forecast temperature",
                )
            with t2:
                metric_card(
                    "Max rain prob",
                    f"{max_rain if max_rain != -999 else 'N/A'} %",
                    "🌧️",
                    "#38bdf8",
                    "Highest rain probability",
                )
            with t3:
                metric_card(
                    "Wind risk",
                    f"{safety_advice.get('wind_risk_score', 'N/A')}/100",
                    "💨",
                    "#f59e0b",
                    "Wind exposure index from the worst forecast hour",
                )

            render_weather_tiles_native(weather_data)

            try:
                import pandas as pd

                chart_data = []
                for w in weather_data:
                    try:
                        t_val = float(str(w.get("temp")).replace("°C", "").replace("C", "").strip())
                        r_val = float(str(w.get("rain_prob")).replace("%", "").strip())
                        chart_data.append(
                            {
                                "Time": w.get("time"),
                                "Temp (°C)": t_val,
                                "Rain Prob (%)": r_val,
                            }
                        )
                    except Exception:
                        continue

                if chart_data:
                    st.line_chart(pd.DataFrame(chart_data).set_index("Time"), height=240)
            except Exception:
                st.write("Weather chart unavailable.")

            if safety_advice:
                left, right = st.columns([1, 2])
                with left:
                    metric_card(
                        "Safety status",
                        str(safety_advice.get("status", "N/A")),
                        "🛡️",
                        "#22c55e" if status == "Go" else "#f59e0b",
                        "Operational decision signal",
                    )
                with right:
                    st.info(
                        f"**Gear advice:** {safety_advice.get('gear_advice', 'N/A')}  \n\n"
                        f"**Assessment:** {safety_advice.get('message', 'No message')}"
                    )

    mud_data = conditions.get("mud_risk", {}) if conditions else {}
    if mud_data:
        section_intro(
            "Mud & environmental risk", "Trail rideability, traction, and preservation signals."
        )

        if str(mud_data.get("status", "")).lower() == "error":
            st.error(mud_data.get("message", "Mud analysis unavailable."))
            if mud_data.get("next_step"):
                st.info(f"**Next step:** {mud_data['next_step']}")
        else:
            tactical_mud = mud_data.get("tactical_analysis", {}) or {}
            env_context = mud_data.get("environmental_context", {}) or {}

            m1, m2, m3 = st.columns(3)
            with m1:
                metric_card(
                    "Mud risk",
                    str(tactical_mud.get("mud_risk_score", "Unknown")),
                    "🟤",
                    "#8b5cf6",
                    "Overall terrain softness",
                )
            with m2:
                metric_card(
                    "Dry time ETA",
                    str(tactical_mud.get("dry_time_eta", "N/A")),
                    "⏳",
                    "#f59e0b",
                    "Estimated recovery window",
                )
            with m3:
                metric_card(
                    "Rain 72h",
                    f"{env_context.get('total_rain_72h_mm', 'N/A')} mm",
                    "🌧️",
                    "#38bdf8",
                    "Recent accumulated rainfall",
                )

            traction = tactical_mud.get("traction_risk", {}) or {}
            damage = tactical_mud.get("trail_damage_risk", {}) or {}

            b1, b2 = st.columns(2)
            with b1:
                st.markdown(
                    f"""
                    <div class="bs-risk-box">
                        <div class="bs-risk-title">Traction analysis</div>
                        <div class="bs-risk-value">{traction.get("level", "N/A")}</div>
                        <div class="bs-risk-copy">{traction.get("advice", "No advice available.")}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with b2:
                st.markdown(
                    f"""
                    <div class="bs-risk-box">
                        <div class="bs-risk-title">Trail integrity</div>
                        <div class="bs-risk-value">{damage.get("level", "N/A")}</div>
                        <div class="bs-risk-copy">{damage.get("advice", "No advice available.")}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    pois = logistics.get("nearby_amenities", {}) if logistics else {}
    if pois:
        section_intro(
            "POI & logistics", "Nearby support points for water, food, repairs, safety, and rest."
        )
        with st.expander("Amenities on route", expanded=True):
            for i in range(0, len(pois), 3):
                cols = st.columns(3)
                for idx, poi in enumerate(pois[i : i + 3]):
                    with cols[idx]:
                        p_name = poi.get("name", "Unknown POI")
                        p_type = poi.get("type", "Amenity")
                        p_dist = poi.get("distance_m", 0)
                        icon, border_color = get_poi_style(p_type)
                        opening_hours = poi.get("opening_hours")
                        potability = poi.get("potability")
                        drinking_water = poi.get("drinking_water")
                        route_km = poi.get("route_km")
                        route_total_km = info.get("distance_km")

                        if isinstance(p_dist, (int, float)):
                            dist_str = (
                                f"{p_dist / 1000:.1f} km" if p_dist >= 1000 else f"{int(p_dist)} m"
                            )
                        else:
                            dist_str = "N/A"
                        route_str = None
                        if isinstance(route_km, (int, float)):
                            if isinstance(route_total_km, (int, float)) and route_total_km > 0:
                                route_str = f"km {route_km:.1f} / {route_total_km:.1f}"
                            else:
                                route_str = f"km {route_km:.1f}"
                        extra = []
                        if route_str:
                            extra.append(f"At {route_str}")
                        if opening_hours:
                            extra.append(f"Hours: {opening_hours}")
                        if potability:
                            extra.append(f"Water: {potability.replace('_', ' ')}")
                        elif drinking_water:
                            extra.append(f"Drinking water: {drinking_water}")
                        extra_html = (
                            f"<div style='font-size:0.72rem;color:#93a4b8;margin-top:4px;'>{' · '.join(extra)}</div>"
                            if extra
                            else ""
                        )

                        link = None
                        p_loc = poi.get("location")
                        if isinstance(p_loc, dict):
                            lat = p_loc.get("latitude", p_loc.get("lat"))
                            lon = p_loc.get("longitude", p_loc.get("lon"))
                            if lat is not None and lon is not None:
                                link = (
                                    f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                                )

                        action_html = (
                            f'<a href="{link}" target="_blank">Open in Maps ↗</a>'
                            if link
                            else "No coordinates available"
                        )
                        card_html = (
                            f'<div class="bs-poi-card" style="--poi-accent:{border_color};">'
                            f'<div class="bs-poi-head"><div>'
                            f'<div class="bs-poi-title">{icon} {p_name}</div>'
                            f'<div class="bs-poi-type">{p_type}</div>'
                            f"</div></div>"
                            f'<div class="bs-poi-distance">{dist_str} from route</div>'
                            f"{extra_html}"
                            f'<div class="bs-poi-actions">{action_html}</div>'
                            f"</div>"
                        )
                        st.markdown(card_html, unsafe_allow_html=True)

    gonogo = res_data.get("ride_window_planner")
    gonogo_error = res_data.get("ride_window_planner_error")
    if gonogo or gonogo_error:
        section_intro(
            "Go/No-Go ride window",
            "Heuristic daylight, weather, and TAEL mud-risk planning signal. Verify local conditions before riding.",
        )
        render_gonogo_report(gonogo, gonogo_error)

    nutrition = logistics.get("nutrition_plan", {}) if logistics else {}
    if nutrition:
        briefing_nut = nutrition.get("mission_nutrition_briefing", {}) or {}
        section_intro(
            "Nutrition & hydration",
            "Fueling strategy aligned with distance, intensity, and environmental load.",
        )
        with st.expander("Fueling details", expanded=True):
            fluids = briefing_nut.get("fluids", {}) or {}
            carbs = briefing_nut.get("carbohydrates", {}) or {}
            sodium = briefing_nut.get("electrolytes", {}) or {}

            n1, n2, n3 = st.columns(3)
            with n1:
                metric_card(
                    "Fluids",
                    f"{fluids.get('total_liters', 'N/A')} L",
                    "💧",
                    "#38bdf8",
                    f"{fluids.get('hourly_average_ml', 'N/A')} ml/h",
                )
            with n2:
                metric_card(
                    "Carbs",
                    f"{carbs.get('total_grams', 'N/A')} g",
                    "🍌",
                    "#22c55e",
                    f"{carbs.get('hourly_target_g', 'N/A')} g/h",
                )
            with n3:
                metric_card(
                    "Sodium",
                    f"{sodium.get('total_sodium_mg', 'N/A')} mg",
                    "🧂",
                    "#f59e0b",
                    f"{sodium.get('hourly_sodium_mg', 'N/A')} mg/h",
                )

            tactical_advice = briefing_nut.get("tactical_advice", []) or []
            for advice in tactical_advice:
                st.info(advice)

            note = _nutrition_note(briefing_nut)
            if note:
                st.caption(note)
            references = briefing_nut.get("references") or []
            if references:
                with st.expander("Fueling sources", expanded=False):
                    for reference in references:
                        st.markdown(f"- {reference}")

    nutrition_error = res_data.get("nutrition_error")
    if nutrition_error:
        st.warning(
            f"Nutrition plan unavailable: {nutrition_error} "
            "Check the input values or add a measured sweat rate and retry."
        )

    map_uri = res_data.get("map_path")
    alt_uri = res_data.get("elevation_profile_path")
    if map_uri or alt_uri:
        section_intro("Visuals", "Route map and elevation profile for tactical validation.")
        v1, v2 = st.columns(2)
        if map_uri:
            v1.image(map_uri, caption="Tactical map", use_container_width=True)
        if alt_uri:
            v2.image(alt_uri, caption="Elevation profile", use_container_width=True)
            caption = _altimetry_caption(res_data)
            if caption:
                v2.caption(caption)
        elevation_error = res_data.get("elevation_error")
        if elevation_error:
            st.warning(
                f"Elevation profile unavailable: {elevation_error} Check the route data and retry."
            )

    gpx_path = res_data.get("gpx_export_path")
    if gpx_path and os.path.exists(gpx_path):
        dl_col, _ = st.columns([1, 5])
        with dl_col, open(gpx_path, "rb") as file:
            st.download_button(
                "Download GPX",
                file,
                file_name="mission.gpx",
                mime="application/gpx+xml",
                type="primary",
                use_container_width=True,
            )
