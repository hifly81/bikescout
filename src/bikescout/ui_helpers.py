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

import streamlit as st


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


def render_summary_card(title: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="bs-card">
            <div class="bs-card-title">{title}</div>
            <div class="bs-card-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str) -> None:
    st.markdown(f'<div class="bs-section-title">{title}</div>', unsafe_allow_html=True)


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