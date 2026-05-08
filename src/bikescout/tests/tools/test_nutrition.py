import pytest
from bikescout.tools.nutrition import get_nutrition_plan

class TestNutrition:

    def test_baseline_nutrition_plan(self):
        """Test standard: 2 ore, 20°C, Intensità 3 (Tempo)."""
        result = get_nutrition_plan(duration_hours=2.0, temp_c=20, intensity_score=3)

        data = result["mission_nutrition_briefing"]
        assert result["status"] == "Success"
        # Verifica target carboidrati (Intensity 3 -> IF 0.85 -> 60g/hr)
        assert data["carbohydrates"]["hourly_target_g"] == 60
        assert data["carbohydrates"]["total_grams"] == 120
        # Verifica idratazione (presenza di valori numerici ragionevoli)
        assert data["fluids"]["total_liters"] > 0
        assert data["fluids"]["hourly_average_ml"] > 0

    def test_thermal_drift_impact(self):
        """Verifica che il tasso di sudore aumenti dopo la prima ora (Thermal Drift)."""
        # Piano da 1 ora
        plan_1h = get_nutrition_plan(1.0, 25, 3)["mission_nutrition_briefing"]
        # Piano da 3 ore (stesse condizioni)
        plan_3h = get_nutrition_plan(3.0, 25, 3)["mission_nutrition_briefing"]

        # La media oraria su 3 ore deve essere superiore a quella su 1 ora
        # perché dopo la 1ª ora il sudore passa dal 75% al 100% dello steady state.
        assert plan_3h["fluids"]["hourly_average_ml"] > plan_1h["fluids"]["hourly_average_ml"]

    def test_gender_scaling(self):
        """Le donne (gender_factor 0.85) dovrebbero avere target di idratazione inferiori."""
        male_plan = get_nutrition_plan(2.0, 25, 3, gender="male")["mission_nutrition_briefing"]
        female_plan = get_nutrition_plan(2.0, 25, 3, gender="female")["mission_nutrition_briefing"]

        assert female_plan["fluids"]["total_liters"] < male_plan["fluids"]["total_liters"]

    @pytest.mark.parametrize("intensity, expected_carbs", [
        (1, 40),  # Endurance / Recovery
        (4, 90),  # Race / Threshold
        (5, 90)   # Race / Threshold (capped or race logic)
    ])
    def test_intensity_carb_scaling(self, intensity, expected_carbs):
        """Verifica che i carboidrati aumentino con l'intensità."""
        plan = get_nutrition_plan(2.0, 20, intensity)["mission_nutrition_briefing"]
        assert plan["carbohydrates"]["hourly_target_g"] == expected_carbs

    def test_extreme_heat_and_sodium_alerts(self):
        """Forza gli alert per calore estremo e perdita critica di sodio."""
        # 35°C, profilo sudore Extreme, Intensità alta
        result = get_nutrition_plan(
            duration_hours=4.0,
            temp_c=35,
            intensity_score=4,
            sweat_profile="extreme"
        )
        alerts = result["mission_nutrition_briefing"]["tactical_advice"]

        assert any("HEAT STRESS" in a for a in alerts)
        assert any("ELECTROLYTE CRITICAL" in a for a in alerts)
        assert any("BONK RISK" in a for a in alerts) # Perché durata > 2.5 e IF >= 0.85

    def test_high_carb_ratio_advice(self):
        """Verifica il consiglio sul rapporto 2:1 per target carboidrati > 60g/hr."""
        # Un'attività lunga (>3h) a intensità alta aumenta il carb_rate di 30
        # Quindi 60 (base tempo) + 30 = 90g/hr
        result = get_nutrition_plan(duration_hours=4.0, temp_c=20, intensity_score=3)
        data = result["mission_nutrition_briefing"]

        assert data["carbohydrates"]["hourly_target_g"] > 60
        assert "2:1 Glucose-to-Fructose" in data["carbohydrates"]["recommended_ratio"]
        assert any("FUELING ALERT" in a for a in data["tactical_advice"])

    def test_hyper_hydration_risk_(self):
        result = get_nutrition_plan(
            duration_hours=4.0,
            temp_c=35,
            intensity_score=4,
            weight_kg=75.0
        )

        briefing = result["mission_nutrition_briefing"]
        alerts = briefing["tactical_advice"]

        assert any("HYPER-HYDRATION RISK" in a for a in alerts)