from unittest.mock import patch, MagicMock
from bikescout.tools.weather import get_safety_advice, get_weather_forecast, apply_weather_windowing

class TestWeather:

    def test_safety_advice_logic(self):
        go_advice = get_safety_advice(app_temp=28, rain_prob=0, rain_mm=0, wind_speed=10, wind_gusts=15)
        assert "[GO]" in go_advice["status"]
        assert "High Summer" in go_advice["gear_advice"]

        danger_advice = get_safety_advice(app_temp=10, rain_prob=0, rain_mm=0, wind_speed=50, wind_gusts=70)
        assert "NOT RECOMMENDED" in danger_advice["status"]
        assert danger_advice["wind_risk_score"] > 55

        winter_advice = get_safety_advice(app_temp=2, rain_prob=0, rain_mm=0, wind_speed=5, wind_gusts=5)
        assert "Deep Winter" in winter_advice["gear_advice"]

    @patch("requests.get")
    def test_weather_forecast_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hourly": {
                "time": ["2026-05-08T07:00", "2026-05-08T08:00", "2026-05-08T09:00"],
                "temperature_2m": [15, 16, 17],
                "apparent_temperature": [14, 15, 16],
                "precipitation_probability": [0, 0, 10],
                "precipitation": [0, 0, 0],
                "windspeed_10m": [10, 12, 11],
                "windgusts_10m": [15, 18, 16],
                "winddirection_10m": [180, 190, 200],
                "weathercode": [0, 0, 1]
            }
        }
        mock_get.return_value = mock_response

        result = get_weather_forecast(41.9, 12.4, target_date="2026-05-08", target_hour=9)

        assert result["status"] == "Success"
        assert result["metadata"]["local_timezone"] == "Europe/Rome"
        assert len(result["tactical_forecast"]) == 3

    def test_apply_weather_windowing(self):
        fake_data = {
            "tactical_forecast": [
                {"time": "09:00", "temp": "10°C", "wind": "10 km/h"},
                {"time": "10:00", "temp": "20°C", "wind": "20 km/h"},
                {"time": "11:00", "temp": "30°C", "wind": "30 km/h"}
            ]
        }
        windowed = apply_weather_windowing(fake_data, 9, 10)

        assert windowed["reference_conditions"]["temp"] == 15.0
        assert windowed["reference_conditions"]["wind_speed"] == 15.0
        assert len(windowed["tactical_forecast"]) == 2

    @patch("requests.get")
    def test_weather_api_failure(self, mock_get):
        mock_get.side_effect = Exception("Open-Meteo Down")
        result = get_weather_forecast(41.9, 12.4)
        assert result["status"] == "Error"
        assert "Unexpected Weather Engine Error" in result["message"]