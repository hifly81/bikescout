import pytest

import bikescout.tools.nutrition as nutrition_module
from bikescout.tools.nutrition import (
    NutritionConfig,
    NutritionService,
    get_nutrition_plan,
)


@pytest.fixture
def service():
    return NutritionService(NutritionConfig())


def test_coerce_float(service):
    assert service._coerce_float("12.5", 1.0) == 12.5
    assert service._coerce_float("bad", 1.0) == 1.0


def test_coerce_positive_float(service):
    assert service._coerce_positive_float(2.0, 1.0) == 2.0
    assert service._coerce_positive_float(0, 1.0) == 1.0
    assert service._coerce_positive_float(-1, 1.0) == 1.0
    assert service._coerce_positive_float("bad", 1.0) == 1.0


def test_normalize_gender(service):
    assert service._normalize_gender("male") == "male"
    assert service._normalize_gender(" Female ") == "female"
    assert service._normalize_gender("") == "male"
    assert service._normalize_gender(None) == "male"


def test_normalize_sweat_profile(service):
    assert service._normalize_sweat_profile("high") == "high"
    assert service._normalize_sweat_profile(" Extreme ") == "extreme"
    assert service._normalize_sweat_profile("") == "standard"
    assert service._normalize_sweat_profile(None) == "standard"


def test_normalize_intensity_score(service):
    assert service._normalize_intensity_score(1) == 1
    assert service._normalize_intensity_score(5) == 5
    assert service._normalize_intensity_score(0) == 1
    assert service._normalize_intensity_score(9) == 5
    assert service._normalize_intensity_score("bad") == 2


def test_intensity_factor(service):
    assert service._intensity_factor(1) == 0.60
    assert service._intensity_factor(2) == 0.75
    assert service._intensity_factor(3) == 0.85
    assert service._intensity_factor(4) == 0.95
    assert service._intensity_factor(5) == 1.05
    assert service._intensity_factor(99) == 0.75


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
    assert service._sodium_concentration("weird") == 800


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
    )

    assert len(alerts) == 5
    assert any("FUELING ALERT" in alert for alert in alerts)
    assert any("HEAT STRESS" in alert for alert in alerts)
    assert any("BONK RISK" in alert for alert in alerts)
    assert any("ELECTROLYTE CRITICAL" in alert for alert in alerts)
    assert any("HYPER-HYDRATION RISK" in alert for alert in alerts)


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
    assert briefing["carbohydrates"]["recommended_ratio"] == "2:1 Glucose-to-Fructose (or 1:0.8 ratio)"
    assert briefing["carbohydrates"]["intensity_context"] == "Race / Threshold"
    assert len(briefing["tactical_advice"]) >= 4


def test_get_nutrition_plan_female_changes_fluid_model(service):
    male_result = service.get_nutrition_plan(
        duration_hours=2.0,
        temp_c=20.0,
        intensity_score=2,
        weight_kg=70.0,
        gender="male",
        sweat_profile="standard",
    )
    female_result = service.get_nutrition_plan(
        duration_hours=2.0,
        temp_c=20.0,
        intensity_score=2,
        weight_kg=70.0,
        gender="female",
        sweat_profile="standard",
    )

    male_hourly = male_result["mission_nutrition_briefing"]["fluids"]["hourly_average_ml"]
    female_hourly = female_result["mission_nutrition_briefing"]["fluids"]["hourly_average_ml"]

    assert female_hourly < male_hourly


def test_get_nutrition_plan_low_sweat_profile_changes_sodium(service):
    result = service.get_nutrition_plan(
        duration_hours=2.0,
        temp_c=20.0,
        intensity_score=2,
        weight_kg=70.0,
        gender="male",
        sweat_profile="low",
    )

    sodium = result["mission_nutrition_briefing"]["electrolytes"]["hourly_sodium_mg"]
    assert sodium > 0
    assert sodium < 1000


def test_get_nutrition_plan_invalid_inputs_fall_back(service):
    result = service.get_nutrition_plan(
        duration_hours="bad",
        temp_c="bad",
        intensity_score="bad",
        weight_kg="bad",
        gender=None,
        sweat_profile=None,
    )

    briefing = result["mission_nutrition_briefing"]
    assert result["status"] == "Success"
    assert briefing["carbohydrates"]["hourly_target_g"] == 40
    assert briefing["carbohydrates"]["intensity_context"] == "Endurance / Recovery"


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
    )

    assert result["status"] == "Success"
    assert len(fake_service.calls) == 1