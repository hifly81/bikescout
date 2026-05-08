import pytest
from bikescout.tools.battery import calculate_battery_drain

class TestBattery:

    def test_baseline_safe_ride(self):
        surface = {"Asphalt": 100}
        result = calculate_battery_drain(
            battery_wh=500, assist_level="Eco", weight_kg=85,
            ascent_m=0, distance_km=20, surface_breakdown=surface,
            mud_index=0, avg_speed_kmh=20
        )
        assert result["status"] == "Success"
        assert result["battery_metrics"]["safety_buffer_status"] == "SAFE"
        assert result["battery_metrics"]["remaining_battery_pct"] > 50

    def test_cold_weather_penalty(self):
        res_warm = calculate_battery_drain(500, "Eco", 85, 0, 10, {"Asphalt": 100}, 0, ambient_temp_c=20)
        res_cold = calculate_battery_drain(500, "Eco", 85, 0, 10, {"Asphalt": 100}, 0, ambient_temp_c=5)

        assert res_cold["battery_metrics"]["usable_wh_at_temp"] < res_warm["battery_metrics"]["usable_wh_at_temp"]

    def test_steep_climb_efficiency_and_heat(self):
        surface = {"Gravel": 100}
        result = calculate_battery_drain(
            battery_wh=500, assist_level="Boost", weight_kg=90,
            ascent_m=3000, distance_km=30, surface_breakdown=surface,
            mud_index=0.1, ambient_temp_c=35
        )

        assert result["battery_metrics"]["safety_buffer_status"] in ["WARNING", "CRITICAL"]

    def test_critical_battery_status(self):
        surface = {"Deep Mud": 100}
        result = calculate_battery_drain(
            battery_wh=250, assist_level="Boost", weight_kg=100,
            ascent_m=1500, distance_km=30, surface_breakdown=surface,
            mud_index=0.8
        )
        assert result["battery_metrics"]["safety_buffer_status"] == "CRITICAL"
        assert "Switch to lower assist" in result["tactical_advice"]

    def test_surface_and_mud_impact(self):
        res_clean = calculate_battery_drain(500, "Trail", 80, 100, 10, {"Gravel": 100}, mud_index=0)
        res_muddy = calculate_battery_drain(500, "Trail", 80, 100, 10, {"Gravel": 100}, mud_index=0.5)

        assert res_muddy["battery_metrics"]["estimated_drain_wh"] > res_clean["battery_metrics"]["estimated_drain_wh"]

    def test_invalid_surface_fallback(self):
        result = calculate_battery_drain(500, "Eco", 80, 0, 10, surface_breakdown=None, mud_index=0)
        assert result["status"] == "Success"
        assert result["power_breakdown_w"]["rolling_resistance"] > 0