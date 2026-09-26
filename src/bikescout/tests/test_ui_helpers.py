from unittest.mock import MagicMock

import bikescout.ui_helpers as ui_helpers


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
        assert 'https://fonts.googleapis.com/css2?family=Inter' in args[0]
        assert kwargs["unsafe_allow_html"] is True


class TestRenderSummaryCard:
    def test_renders_summary_card(self, monkeypatch):
        mock_markdown = MagicMock()
        monkeypatch.setattr(ui_helpers.st, "markdown", mock_markdown)

        ui_helpers.render_summary_card("Distance", "42 km")

        mock_markdown.assert_called_once()
        args, kwargs = mock_markdown.call_args
        html = args[0]

        assert '<div class="bs-card">' in html
        assert '<div class="bs-card-title">Distance</div>' in html
        assert '<div class="bs-card-value">42 km</div>' in html
        assert kwargs["unsafe_allow_html"] is True


class TestRenderSectionHeader:
    def test_renders_section_header(self, monkeypatch):
        mock_markdown = MagicMock()
        monkeypatch.setattr(ui_helpers.st, "markdown", mock_markdown)

        ui_helpers.render_section_header("Mission Overview")

        mock_markdown.assert_called_once_with(
            '<div class="bs-section-title">Mission Overview</div>',
            unsafe_allow_html=True,
        )


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