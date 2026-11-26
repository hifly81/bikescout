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

from unittest.mock import MagicMock

import bikescout.app_ui_helpers as ui_helpers


class TestInjectGlobalStyles:
    def test_calls_markdown_with_html_and_unsafe_flag(self, monkeypatch):
        mock_markdown = MagicMock()
        monkeypatch.setattr(ui_helpers.st, "markdown", mock_markdown)

        ui_helpers.inject_global_styles()

        mock_markdown.assert_called_once()
        args, kwargs = mock_markdown.call_args

        assert "<style>" in args[0]
        assert "--bg:" in args[0]
        assert ".bs-hero" in args[0]
        assert "https://fonts.googleapis.com/css2?family=Inter" in args[0]
        assert kwargs["unsafe_allow_html"] is True


class TestRenderEmptyState:
    def test_renders_empty_state(self, monkeypatch):
        mock_markdown = MagicMock()
        monkeypatch.setattr(ui_helpers.st, "markdown", mock_markdown)

        ui_helpers.render_empty_state("No routes yet", "Start by selecting an area.")

        mock_markdown.assert_called_once()
        args, kwargs = mock_markdown.call_args
        html = args[0]

        assert '<div class="bs-empty">' in html
        assert "<strong>No routes yet</strong><br/>" in html
        assert "Start by selecting an area." in html
        assert kwargs["unsafe_allow_html"] is True


class TestTerrainClimbRows:
    def test_shows_start_and_summit_without_max_grade(self):
        rows = ui_helpers._terrain_climb_rows(
            {
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
                ]
            },
            {},
        )

        assert rows[0]["Start (m)"] == "1000.0"
        assert rows[0]["Summit (m)"] == "1120.0"
        assert "Max grade" not in rows[0]


class TestNormalizeTireSetup:
    def test_normalizes_structured_model(self):
        from bikescout.schemas import TireSetupRecommendation

        setup = TireSetupRecommendation(
            wheel_label='29"',
            tire_width_mm=58,
            rim_internal_width_mm=25,
            casing_type="trail",
            tubeless=True,
            knob_choice="All-Terrain / Trail",
            psi_front=19.9,
            psi_rear=25.4,
            bar_front=1.37,
            bar_rear=1.75,
            strategy="Compliance",
            load_split={"front": 0.4, "rear": 0.6},
            tactical_display='29" wheels | F: 19.9 PSI | R: 25.4 PSI',
        )

        result = ui_helpers.normalize_tire_setup(setup)

        assert result["psi_front"] == 19.9
        assert result["psi_rear"] == 25.4
        assert result["strategy"] == "Compliance"

    def test_normalizes_legacy_display_string(self):
        legacy = (
            40,
            "700c wheels | F: 22 PSI | R: 25 PSI (1.52/1.72 Bar) [Mud Flotation Setup]",
        )

        result = ui_helpers.normalize_tire_setup(legacy)

        assert result["wheel_label"] == "700c"
        assert result["tire_width_mm"] == 40
        assert result["psi_front"] == 22.0
        assert result["psi_rear"] == 25.0
        assert result["strategy"] == "Mud Flotation"

    def test_empty_payload_returns_defaults(self):
        result = ui_helpers.normalize_tire_setup([])

        assert result["psi_front"] is None
        assert result["strategy"] == "Standard"
        assert result["advice"] == []


class TestNutritionNote:
    def test_combines_basis_confidence_and_uncertainty(self):
        note = ui_helpers._nutrition_note(
            {
                "data_basis": "Fluid target is a population estimate.",
                "estimate_confidence": "low",
                "uncertainty_note": "Validate with a timed weigh-in.",
            }
        )
        assert note == (
            "Fluid target is a population estimate. Confidence: low. "
            "Validate with a timed weigh-in."
        )

    def test_returns_none_when_provenance_is_missing(self):
        assert ui_helpers._nutrition_note({}) is None


class TestAltimetryCaption:
    def test_combines_source_and_uncertainty(self):
        caption = ui_helpers._altimetry_caption(
            {
                "elevation_source": "Elevation data: ORS-compatible routing (HeiGIT)",
                "elevation_samples_total": 42,
                "elevation_samples_interpolated": 3,
            }
        )

        assert caption == (
            "Elevation data: ORS-compatible routing (HeiGIT) "
            "3 of 42 elevation samples estimated from neighbours."
        )

    def test_omits_uncertainty_when_no_samples_are_estimated(self):
        caption = ui_helpers._altimetry_caption(
            {
                "elevation_source": "Elevation data: ORS-compatible routing (HeiGIT)",
                "elevation_samples_total": 42,
                "elevation_samples_interpolated": 0,
            }
        )

        assert caption == "Elevation data: ORS-compatible routing (HeiGIT)"

    def test_returns_none_when_provenance_is_missing(self):
        assert ui_helpers._altimetry_caption({}) is None
