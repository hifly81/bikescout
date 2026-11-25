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

import re
from typing import Any

import streamlit as st

from bikescout.app_helpers import ext_cast
from bikescout.tools.bike_setup import (
    default_casing_type,
    default_rim_internal_width_mm,
    default_tire_width_mm,
)


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
        normalized.update(
            {key: value for key, value in data.items() if key in normalized}
        )
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

        .bs-section h3 {
            margin: 0 0 8px 0 !important;
            font-size: 1.12rem !important;
            font-weight: 800 !important;
        }

        .bs-section p {
            color: #aeb8d0 !important;
            margin: 0 !important;
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
            <h3>{title}</h3>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mini_kpi(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="bs-mini-kpi">
            <div class="k-label">{label}</div>
            <div class="k-value">{value}</div>
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
                {''.join([f'<div class="bs-badge {"safe" if status=="Go" else "warn" if status=="Caution" else "risk"}">{b}</div>' for b in badges[:5]])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mission_hud(
        title: str,
        bike_type: str,
        route_mode: str,
        distance_km: float | None = None,
        elevation_m: float | None = None,
        eta_text: str | None = None,
        weather_text: str | None = None,
        surface_text: str | None = None,
) -> None:
    chips = []

    if distance_km is not None:
        chips.append(f'<div class="bs-hud-chip"><span>Distance</span><strong>{distance_km:.1f} km</strong></div>')
    if elevation_m is not None:
        chips.append(f'<div class="bs-hud-chip"><span>Elevation</span><strong>{int(elevation_m)} m</strong></div>')
    if eta_text:
        chips.append(f'<div class="bs-hud-chip"><span>ETA</span><strong>{eta_text}</strong></div>')
    if weather_text:
        chips.append(f'<div class="bs-hud-chip"><span>Weather</span><strong>{weather_text}</strong></div>')
    if surface_text:
        chips.append(f'<div class="bs-hud-chip"><span>Surface</span><strong>{surface_text}</strong></div>')

    st.markdown(
        f"""
        <div class="bs-hud">
            <div class="bs-hud-top">
                <div class="bs-hud-title-wrap">
                    <div class="bs-hud-kicker">{bike_type.upper()} · {route_mode.upper()}</div>
                    <div class="bs-hud-title">{title}</div>
                </div>
            </div>
            <div class="bs-hud-grid">
                {''.join(chips)}
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

    rows = [weather_data[i:i + 5] for i in range(0, len(weather_data), 5)]

    for row in rows:
        cols = st.columns(len(row))
        for idx, w in enumerate(row):
            with cols[idx]:
                time_label = str(w.get("time", "Time"))
                temp_raw = str(w.get("temp", "N/A"))
                app_raw = str(w.get("app_temp", "N/A"))
                rain_raw = str(w.get("rain_prob", "N/A"))
                wind_raw = str(w.get("wind", w.get("wind_speed", "N/A")))

                st.markdown(
                    f"""
                    <div class="bs-risk-box">
                        <div class="bs-risk-title">{time_label}</div>
                        <div class="bs-risk-value">{temp_raw}</div>
                        <div class="bs-risk-copy">
                            Apparent: {app_raw}<br/>
                            Rain: {rain_raw}<br/>
                            Wind: {wind_raw}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_rider_profile_panel() -> None:
    profile = st.session_state["rider_profile"]

    section_intro(
        "Rider profile",
        "Personal defaults used across planning, fueling, and route recommendations.",
    )

    with st.expander("Open rider settings", expanded=False):
        c1, c2, c3 = st.columns(3)

        with c1:
            profile["bike_type"] = st.selectbox(
                "Default bike",
                ["mtb", "road", "gravel", "e-mtb", "enduro"],
                index=["mtb", "road", "gravel", "e-mtb", "enduro"].index(profile["bike_type"]),
                key="rider_profile_bike_type",
            )

            available_tires = ["32", "29", "27.5", "700c", "650b"]
            current_tire = profile["tire_size"] if profile["tire_size"] in available_tires else "29"
            profile["tire_size"] = st.selectbox(
                "Default tire size",
                available_tires,
                index=available_tires.index(current_tire),
                key="rider_profile_tire_size",
            )

        with c2:
            profile["fitness_level"] = st.selectbox(
                "Fitness level",
                ["beginner", "intermediate", "pro"],
                index=["beginner", "intermediate", "pro"].index(profile["fitness_level"]),
                key="rider_profile_fitness_level",
            )

            profile["weight_kg"] = st.number_input(
                "Weight (kg)",
                min_value=40.0,
                max_value=150.0,
                value=float(profile["weight_kg"]),
                key="rider_profile_weight",
            )

        with c3:
            profile["gender"] = st.selectbox(
                "Gender",
                ["male", "female"],
                index=["male", "female"].index(profile["gender"]),
                key="rider_profile_gender",
            )

            metric_card("Bike", profile["bike_type"], "🚲", "#7c3aed", "Default ride setup")
            metric_card("Tire", profile["tire_size"], "🛞", "#38bdf8", "Tool-safe normalized value")

        default_width = default_tire_width_mm(profile["bike_type"])
        default_rim = default_rim_internal_width_mm(profile["bike_type"])
        setup1, setup2, setup3, setup4 = st.columns(4)
        with setup1:
            profile["tire_width_mm"] = st.number_input(
                "Tire width (mm)",
                min_value=18,
                max_value=75,
                value=int(profile.get("tire_width_mm") or default_width),
                key="rider_profile_tire_width_mm",
            )
        with setup2:
            profile["rim_internal_width_mm"] = st.number_input(
                "Rim internal (mm)",
                min_value=10,
                max_value=45,
                value=int(profile.get("rim_internal_width_mm") or default_rim),
                key="rider_profile_rim_internal_width_mm",
            )
        with setup3:
            casing_options = ["xc", "trail", "enduro", "dh"]
            current_casing = profile.get("casing_type") or default_casing_type(profile["bike_type"])
            if current_casing not in casing_options:
                current_casing = "trail"
            profile["casing_type"] = st.selectbox(
                "Casing",
                casing_options,
                index=casing_options.index(current_casing),
                key="rider_profile_casing_type",
            )
        with setup4:
            profile["tubeless"] = st.checkbox(
                "Tubeless setup",
                value=bool(profile.get("tubeless", True)),
                key="rider_profile_tubeless",
            )

        st.session_state["rider_profile"] = profile