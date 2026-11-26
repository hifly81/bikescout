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

import pytest

import bikescout.tools.nutrition as nutrition_module
from bikescout.tools.nutrition import (
    NUTRITION_REFERENCES,
    NutritionConfig,
    NutritionService,
    get_nutrition_plan,
)


@pytest.fixture
def service():
    return NutritionService(NutritionConfig())


def test_require_number_accepts_numeric_strings(service):
    assert service._require_number("duration_hours", "2.5", 0.1, 24.0) == 2.5


@pytest.mark.parametrize("bad", ["bad", None, True, float("nan"), 0.0, 25.0])
def test_require_number_rejects_invalid_values(service, bad):
    with pytest.raises(ValueError, match="duration_hours"):
        service._require_number("duration_hours", bad, 0.1, 24.0)


@pytest.mark.parametrize("good", [1, "5", 3.0])
def test_require_int_accepts_whole_numbers(service, good):
    assert service._require_int("intensity_score", good, 1, 5) == int(good)


@pytest.mark.parametrize("bad", ["bad", None, True, 3.5, 0, 6])
def test_require_int_rejects_invalid_values(service, bad):
    with pytest.raises(ValueError, match="intensity_score"):
        service._require_int("intensity_score", bad, 1, 5)


def test_require_choice_uses_default_for_missing_values(service):
    assert service._require_choice("gender", None, ("male", "female"), "male") == "male"
    assert service._require_choice("gender", " ", ("male", "female"), "male") == "male"


def test_require_choice_normalizes_valid_values(service):
    assert service._require_choice("gender", " Female ", ("male", "female"), "male") == "female"


def test_require_choice_rejects_unknown_values(service):
    with pytest.raises(ValueError, match="must be one of"):
        service._require_choice("gender", "alien", ("male", "female"), "male")


def test_intensity_factor(service):
    assert service._intensity_factor(1) == 0.60
    assert service._intensity_factor(2) == 0.75
    assert service._intensity_factor(3) == 0.85
    assert service._intensity_factor(4) == 0.95
    assert service._intensity_factor(5) == 1.05


def test_avg_hourly_fluid_short_duration(service):
    result = service._avg_hourly_fluid_ml(
        duration_hours=1.0,
        temp_c=20.0,
        intensity_factor=0.75,
        weight_kg=70.0,
        gender_factor=1.0,
    )
    assert result == pytest.approx(787.5)


def test_avg_hourly_fluid_long_duration(service):
    result = service._avg_hourly_fluid_ml(
        duration_hours=3.0,
        temp_c=20.0,
        intensity_factor=0.75,
        weight_kg=70.0,
        gender_factor=1.0,
    )
    assert result == pytest.approx(962.5)


def test_carb_rate_and_label_endurance(service):
    carb_rate, label = service._carb_rate_and_label(2.0, 0.75)
    assert carb_rate == 40
    assert label == "Endurance / Recovery"


def test_carb_rate_and_label_tempo(service):
    carb_rate, label = service._carb_rate_and_label(2.0, 0.85)
    assert carb_rate == 60
    assert label == "Tempo"


def test_carb_rate_and_label_race(service):
    carb_rate, label = service._carb_rate_and_label(2.0, 0.95)
    assert carb_rate == 90
    assert label == "Race / Threshold"


def test_carb_rate_and_label_duration_bonus(service):
    carb_rate, label = service._carb_rate_and_label(4.0, 0.85)
    assert carb_rate == 90
    assert label == "Tempo"


def test_carb_rate_and_label_ceiling(service):
    carb_rate, label = service._carb_rate_and_label(4.0, 1.05)
    assert carb_rate == 120
    assert label == "Race / Threshold"


def test_sodium_concentration(service):
    assert service._sodium_concentration("low") == 400
    assert service._sodium_concentration("standard") == 800
    assert service._sodium_concentration("high") == 1200
    assert service._sodium_concentration("extreme") == 1800


def test_build_alerts_none(service):
    alerts = service._build_alerts(
        carb_rate=40,
        ratios="Standard isotonic or whole foods",
        temp_c=20.0,
        duration_hours=1.5,
        intensity_factor=0.75,
        hourly_sodium_mg=500.0,
        total_fluid_l=1.0,
        weight_kg=70.0,
        estimated_fluid_ml=700.0,
    )
    assert alerts == []


def test_build_alerts_all(service):
    alerts = service._build_alerts(
        carb_rate=90,
        ratios="2:1 Glucose-to-Fructose (or 1:0.8 ratio)",
        temp_c=30.0,
        duration_hours=4.0,
        intensity_factor=0.95,
        hourly_sodium_mg=1200.0,
        total_fluid_l=6.0,
        weight_kg=70.0,
        estimated_fluid_ml=1100.0,
        humidity_pct=75.0,
        temperature_basis="daily_max",
    )

    assert len(alerts) == 8
    assert any("FUELING ALERT" in alert for alert in alerts)
    assert any("HEAT STRESS" in alert for alert in alerts)
    assert any("BONK RISK" in alert for alert in alerts)
    assert any("ELECTROLYTE CRITICAL" in alert for alert in alerts)
    assert any("HYPER-HYDRATION RISK" in alert for alert in alerts)
    assert any("FLUID CEILING" in alert for alert in alerts)
    assert any("HUMIDITY LOAD" in alert for alert in alerts)
    assert any("TEMPERATURE CONTEXT" in alert for alert in alerts)


def test_measured_sweat_rate_skips_fluid_ceiling_alert(service):
    alerts = service._build_alerts(
        carb_rate=40,
        ratios="Standard isotonic or whole foods",
        temp_c=22.0,
        duration_hours=2.0,
        intensity_factor=0.75,
        hourly_sodium_mg=400.0,
        total_fluid_l=3.0,
        weight_kg=70.0,
        estimated_fluid_ml=1000.0,
        sweat_rate_ml_per_hour=1500.0,
    )
    assert not any("FLUID CEILING" in alert for alert in alerts)


def test_measured_sweat_rate_above_2_5_l_warns(service):
    alerts = service._build_alerts(
        carb_rate=40,
        ratios="Standard isotonic or whole foods",
        temp_c=22.0,
        duration_hours=2.0,
        intensity_factor=0.75,
        hourly_sodium_mg=400.0,
        total_fluid_l=6.0,
        weight_kg=70.0,
        estimated_fluid_ml=2600.0,
        sweat_rate_ml_per_hour=3000.0,
    )
    assert any("SWEAT CHECK" in alert for alert in alerts)


def test_get_nutrition_plan_basic_success(service):
    result = service.get_nutrition_plan(
        duration_hours=2.0,
        temp_c=20.0,
        intensity_score=3,
        weight_kg=70.0,
        gender="male",
        sweat_profile="standard",
    )

    assert result["status"] == "Success"
    briefing = result["mission_nutrition_briefing"]
    assert "fluids" in briefing
    assert "carbohydrates" in briefing
    assert "electrolytes" in briefing
    assert "tactical_advice" in briefing
    assert briefing["estimate_confidence"] == "low"
    assert "population estimate" in briefing["data_basis"]
    assert "timed weigh-in" in briefing["uncertainty_note"]
    assert briefing["inputs_used"]["sweat_rate_source"] == "estimated"
    assert briefing["references"] == list(NUTRITION_REFERENCES)


def test_get_nutrition_plan_bounds_population_fluid_estimate(service):
    result = service.get_nutrition_plan(
        duration_hours=3.0,
        temp_c=20.0,
        intensity_score=2,
        weight_kg=70.0,
    )
    fluids = result["mission_nutrition_briefing"]["fluids"]
    assert fluids["hourly_average_ml"] == 800
    assert any(
        "FLUID CEILING" in alert
        for alert in result["mission_nutrition_briefing"]["tactical_advice"]
    )


def test_get_nutrition_plan_high_intensity_hot_long_ride(service):
    result = service.get_nutrition_plan(
        duration_hours=4.0,
        temp_c=32.0,
        intensity_score=5,
        weight_kg=85.0,
        gender="male",
        sweat_profile="extreme",
    )

    briefing = result["mission_nutrition_briefing"]
    assert briefing["carbohydrates"]["hourly_target_g"] == 120
    assert (
        briefing["carbohydrates"]["recommended_ratio"] == "2:1 Glucose-to-Fructose (or 1:0.8 ratio)"
    )
    assert briefing["carbohydrates"]["intensity_context"] == "Race / Threshold"
    assert len(briefing["tactical_advice"]) >= 4
    assert briefing["fluids"]["hourly_average_ml"] == 800


def test_get_nutrition_plan_measured_sweat_rate_overrides_estimate(service):
    result = service.get_nutrition_plan(
        duration_hours=2.0,
        temp_c=30.0,
        intensity_score=2,
        weight_kg=70.0,
        sweat_rate_ml_per_hour=1200.0,
    )

    briefing = result["mission_nutrition_briefing"]
    assert briefing["fluids"]["hourly_average_ml"] == 1200
    assert briefing["fluids"]["total_liters"] == 2.4
    assert briefing["estimate_confidence"] == "moderate"
    assert "measured sweat rate" in briefing["data_basis"]
    assert "sodium concentration remains" in briefing["uncertainty_note"]
    assert briefing["inputs_used"]["sweat_rate_source"] == "measured"


def test_get_nutrition_plan_reports_humidity_and_temperature_basis(service):
    result = service.get_nutrition_plan(
        duration_hours=2.0,
        temp_c=26.0,
        intensity_score=2,
        relative_humidity_pct=70.0,
        temperature_basis="daily_max",
    )
    briefing = result["mission_nutrition_briefing"]
    assert any("HUMIDITY LOAD" in alert for alert in briefing["tactical_advice"])
    assert any("TEMPERATURE CONTEXT" in alert for alert in briefing["tactical_advice"])
    assert "not the ride window" in briefing["uncertainty_note"]
    assert briefing["inputs_used"]["relative_humidity_pct"] == 70.0


def test_get_nutrition_plan_gender_alone_does_not_change_fluid(service):
    kwargs = {
        "duration_hours": 2.0,
        "temp_c": 20.0,
        "intensity_score": 2,
        "weight_kg": 70.0,
        "sweat_profile": "standard",
    }
    male = service.get_nutrition_plan(**kwargs, gender="male")
    female = service.get_nutrition_plan(**kwargs, gender="female")
    assert (
        male["mission_nutrition_briefing"]["fluids"]
        == female["mission_nutrition_briefing"]["fluids"]
    )


def test_get_nutrition_plan_low_sweat_profile_changes_sodium(service):
    result = service.get_nutrition_plan(
        duration_hours=2.0,
        temp_c=20.0,
        intensity_score=2,
        weight_kg=70.0,
        sweat_profile="low",
    )

    sodium = result["mission_nutrition_briefing"]["electrolytes"]["hourly_sodium_mg"]
    assert sodium > 0
    assert sodium < 1000


@pytest.mark.parametrize(
    "overrides, field",
    [
        ({"duration_hours": "bad"}, "duration_hours"),
        ({"duration_hours": 0}, "duration_hours"),
        ({"temp_c": "bad"}, "temp_c"),
        ({"temp_c": 100}, "temp_c"),
        ({"intensity_score": "bad"}, "intensity_score"),
        ({"intensity_score": 9}, "intensity_score"),
        ({"weight_kg": -1}, "weight_kg"),
        ({"gender": "alien"}, "gender"),
        ({"sweat_profile": "salty"}, "sweat_profile"),
        ({"sweat_rate_ml_per_hour": 0}, "sweat_rate_ml_per_hour"),
        ({"relative_humidity_pct": 120}, "relative_humidity_pct"),
        ({"temperature_basis": "yesterday"}, "temperature_basis"),
    ],
)
def test_get_nutrition_plan_invalid_inputs_return_error(service, overrides, field):
    payload = {
        "duration_hours": 2.0,
        "temp_c": 20.0,
        "intensity_score": 2,
        "weight_kg": 70.0,
    }
    payload.update(overrides)
    result = service.get_nutrition_plan(**payload)
    assert result["status"] == "Error"
    assert field in result["error_message"]
    assert "mission_nutrition_briefing" not in result


def test_module_level_wrapper(monkeypatch):
    class FakeService:
        def __init__(self):
            self.calls = []

        def get_nutrition_plan(self, **kwargs):
            self.calls.append(kwargs)
            return {"status": "Success", "mission_nutrition_briefing": {}}

    fake_service = FakeService()
    monkeypatch.setattr(nutrition_module, "service", fake_service)

    result = get_nutrition_plan(
        duration_hours=2.0,
        temp_c=20.0,
        intensity_score=3,
        weight_kg=70.0,
        gender="male",
        sweat_profile="standard",
        sweat_rate_ml_per_hour=900.0,
        relative_humidity_pct=55.0,
        temperature_basis="ride_window",
    )

    assert result["status"] == "Success"
    assert len(fake_service.calls) == 1
    assert fake_service.calls[0]["sweat_rate_ml_per_hour"] == 900.0
