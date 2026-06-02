import pytest

import bikescout.tools.battery as battery_module
from bikescout.tools.battery import (
    BatteryConfig,
    BatteryService,
    calculate_battery_drain,
)


@pytest.fixture
def service():
    return BatteryService(BatteryConfig())


def test_normalize_assist_level(service):
    assert service._normalize_assist_level("eco") == "Eco"
    assert service._normalize_assist_level(" Trail ") == "Trail"
    assert service._normalize_assist_level("BOOST") == "Boost"
    assert service._normalize_assist_level("") == "Trail"
    assert service._normalize_assist_level(None) == "Trail"
    assert service._normalize_assist_level("weird") == "Trail"


def test_coerce_float(service):
    assert service._coerce_float("12.5", 0.0) == 12.5
    assert service._coerce_float("bad", 3.0) == 3.0


def test_coerce_positive_float(service):
    assert service._coerce_positive_float(10, 5.0) == 10.0
    assert service._coerce_positive_float(0, 5.0) == 5.0
    assert service._coerce_positive_float(-2, 5.0) == 5.0
    assert service._coerce_positive_float("bad", 5.0) == 5.0


def test_coerce_non_negative_float(service):
    assert service._coerce_non_negative_float(10, 5.0) == 10.0
    assert service._coerce_non_negative_float(0, 5.0) == 0.0
    assert service._coerce_non_negative_float(-2, 5.0) == 5.0
    assert service._coerce_non_negative_float("bad", 5.0) == 5.0


def test_clamp_float(service):
    assert service._clamp_float(0.5, 0.0, 1.0, 0.0) == 0.5
    assert service._clamp_float(-1, 0.0, 1.0, 0.0) == 0.0
    assert service._clamp_float(2, 0.0, 1.0, 0.0) == 1.0
    assert service._clamp_float("bad", 0.0, 1.0, 0.2) == 0.2


def test_usable_capacity_at_temperature_no_penalty(service):
    result = service._usable_capacity_at_temperature(500.0, 20.0)
    assert result == 465.0


def test_usable_capacity_at_temperature_with_cold_penalty(service):
    result = service._usable_capacity_at_temperature(500.0, 10.0)
    assert result == pytest.approx(441.75)


def test_weighted_crr_default_for_invalid_input(service):
    assert service._weighted_crr(None) == 0.015
    assert service._weighted_crr({}) == 0.015


def test_weighted_crr_computes_weighted_value(service):
    result = service._weighted_crr({
        "Asphalt": 50,
        "Gravel": 50,
    })
    assert result == pytest.approx(0.0095)


def test_weighted_crr_uses_unknown_surface_default(service):
    result = service._weighted_crr({
        "Unknown Surface": 100,
    })
    assert result == pytest.approx(0.020)


def test_weighted_crr_handles_invalid_percentages(service):
    result = service._weighted_crr({
        "Asphalt": "bad",
        "Gravel": 50,
    })
    assert result == pytest.approx(0.0075)

def test_battery_status(service):
    assert service._battery_status(50) == "SAFE"
    assert service._battery_status(20) == "WARNING"
    assert service._battery_status(10) == "CRITICAL"


def test_calculate_battery_drain_basic_success(service):
    result = service.calculate_battery_drain(
        battery_wh=500.0,
        assist_level="Trail",
        weight_kg=85.0,
        ascent_m=500.0,
        distance_km=25.0,
        surface_breakdown={"Gravel": 100},
        mud_index=0.2,
        avg_speed_kmh=18.0,
        ambient_temp_c=20.0,
        rider_ftp_w=200,
        intensity_score=3,
    )

    assert result["status"] == "Success"
    assert "battery_metrics" in result
    assert "power_breakdown_w" in result
    assert "estimated_drain_wh" in result["battery_metrics"]
    assert "remaining_battery_pct" in result["battery_metrics"]
    assert "safety_buffer_status" in result["battery_metrics"]
    assert "usable_wh_at_temp" in result["battery_metrics"]
    assert "gravity_resistance" in result["power_breakdown_w"]
    assert "rolling_resistance" in result["power_breakdown_w"]
    assert "aerodynamic_drag" in result["power_breakdown_w"]
    assert "rider_contribution" in result["power_breakdown_w"]
    assert "motor_net_output" in result["power_breakdown_w"]


def test_calculate_battery_drain_safe_status_and_pace_advice(service):
    result = service.calculate_battery_drain(
        battery_wh=1000.0,
        assist_level="Eco",
        weight_kg=75.0,
        ascent_m=100.0,
        distance_km=20.0,
        surface_breakdown={"Asphalt": 100},
        mud_index=0.0,
        avg_speed_kmh=18.0,
        ambient_temp_c=20.0,
        rider_ftp_w=250,
        intensity_score=5,
    )

    assert result["battery_metrics"]["safety_buffer_status"] == "SAFE"
    assert result["tactical_advice"] == "Pace maintained"


def test_calculate_battery_drain_warning_or_critical_advice(service):
    result = service.calculate_battery_drain(
        battery_wh=200.0,
        assist_level="Boost",
        weight_kg=95.0,
        ascent_m=1500.0,
        distance_km=30.0,
        surface_breakdown={"Deep Mud": 100},
        mud_index=1.0,
        avg_speed_kmh=20.0,
        ambient_temp_c=35.0,
        rider_ftp_w=120,
        intensity_score=1,
    )

    assert result["battery_metrics"]["safety_buffer_status"] in {"WARNING", "CRITICAL"}
    assert result["tactical_advice"] == "Switch to lower assist on flats to save range"


def test_calculate_battery_drain_zero_distance(service):
    result = service.calculate_battery_drain(
        battery_wh=500.0,
        assist_level="Trail",
        weight_kg=85.0,
        ascent_m=500.0,
        distance_km=0.0,
        surface_breakdown={"Gravel": 100},
        mud_index=0.0,
    )

    assert result["status"] == "Success"
    assert result["battery_metrics"]["estimated_drain_wh"] == 0.0


def test_calculate_battery_drain_caps_motor_by_assist_ratio(service):
    result = service.calculate_battery_drain(
        battery_wh=500.0,
        assist_level="Eco",
        weight_kg=120.0,
        ascent_m=3000.0,
        distance_km=20.0,
        surface_breakdown={"Deep Mud": 100},
        mud_index=1.0,
        avg_speed_kmh=25.0,
        ambient_temp_c=20.0,
        rider_ftp_w=100,
        intensity_score=1,
    )

    rider = result["power_breakdown_w"]["rider_contribution"]
    motor = result["power_breakdown_w"]["motor_net_output"]

    assert motor <= (rider * 0.6) + 0.2


def test_calculate_battery_drain_invalid_inputs_fall_back(service):
    result = service.calculate_battery_drain(
        battery_wh="bad",
        assist_level=None,
        weight_kg="bad",
        ascent_m="bad",
        distance_km=-10,
        surface_breakdown="bad",
        mud_index="bad",
        avg_speed_kmh=0,
        ambient_temp_c="bad",
        rider_ftp_w="bad",
        intensity_score="bad",
    )

    assert result["status"] == "Success"
    assert result["battery_metrics"]["usable_wh_at_temp"] == 465.0
    assert result["power_breakdown_w"]["rider_contribution"] == 140.0


def test_module_level_wrapper(monkeypatch):
    class FakeService:
        def __init__(self):
            self.calls = []

        def calculate_battery_drain(self, **kwargs):
            self.calls.append(kwargs)
            return {"status": "Success", "battery_metrics": {}, "power_breakdown_w": {}, "tactical_advice": "Pace maintained"}

    fake_service = FakeService()
    monkeypatch.setattr(battery_module, "service", fake_service)

    result = calculate_battery_drain(
        battery_wh=500.0,
        assist_level="Trail",
        weight_kg=85.0,
        ascent_m=500.0,
        distance_km=25.0,
        surface_breakdown={"Gravel": 100},
        mud_index=0.2,
    )

    assert result["status"] == "Success"
    assert len(fake_service.calls) == 1

def test_motor_efficiency_base(service):
    assert service._motor_efficiency(0.05, 20.0) == pytest.approx(0.85)


def test_motor_efficiency_steep_penalty(service):
    assert service._motor_efficiency(0.10, 20.0) == pytest.approx(0.75)


def test_motor_efficiency_heat_penalty(service):
    assert service._motor_efficiency(0.05, 35.0) == pytest.approx(0.80)


def test_motor_efficiency_both_penalties(service):
    assert service._motor_efficiency(0.10, 35.0) == pytest.approx(0.70)