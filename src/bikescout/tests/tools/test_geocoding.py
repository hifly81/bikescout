import pytest
from unittest.mock import MagicMock, patch
from bikescout.tools.geocoding import GeoEngine, NominatimProvider, get_coordinates

class TestGeocoding:

    @pytest.fixture
    def mock_provider(self):
        return MagicMock(spec=NominatimProvider)

    @pytest.fixture
    def engine(self, mock_provider):
        engine = GeoEngine(mock_provider)
        engine.min_interval = 0
        return engine

    def test_geocoding_success_with_ranking(self, engine, mock_provider):
        mock_provider.geocode.return_value = [
            {
                "lat": "45.0", "lon": "9.0",
                "display_name": "Office Complex",
                "class": "office", "type": "building", "importance": 0.9
            },
            {
                "lat": "46.0", "lon": "10.0",
                "display_name": "National Park",
                "class": "leisure", "type": "park", "importance": 0.6
            }
        ]

        result = engine.get_coordinates("Test Location")

        assert result["status"] == "Success"
        assert result["lat"] == 46.0
        assert "Park" in result["display_name"]

    def test_geocoding_not_found(self, engine, mock_provider):
        mock_provider.geocode.return_value = []

        result = engine.get_coordinates("Unknown Place")

        assert result["status"] == "Error"
        assert "not found" in result["message"]

    @patch("time.sleep")
    def test_exponential_backoff(self, mock_sleep, engine, mock_provider):
        mock_provider.geocode.side_effect = [Exception("Network Error"), []]

        engine.get_coordinates("Retry Place", retries=2)

        mock_sleep.assert_any_call(1)
        assert mock_provider.geocode.call_count == 2

    @patch("time.time")
    @patch("time.sleep")
    def test_rate_limiting_wait(self, mock_sleep, mock_time, engine, mock_provider):
        engine.min_interval = 1.1
        engine.last_request_time = 100.0

        mock_time.return_value = 100.1

        engine._wait_for_slot()

        mock_sleep.assert_called_with(pytest.approx(1.0))

    def test_ranking_penalization(self, engine):
        results = [
            {"class": "shop", "type": "bicycle", "importance": 0.5},
            {"class": "place", "type": "village", "importance": 0.3}
        ]
        # Shop: 0.5 - 0.4 = 0.1
        # Village: 0.3 + 0.3 = 0.6
        best = engine._rank_results(results)
        assert best["type"] == "village"