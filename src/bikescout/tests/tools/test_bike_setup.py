import pytest

import bikescout.tools.bike_setup as bike_setup_module
from bikescout.schemas import TireSetupRecommendation
from bikescout.tools.bike_setup import (
    BikeSetupConfig,
    BikeSetupService,
    analyze_compatibility,
    get_tire_setup,
)


@pytest.fixture
def service():
    return BikeSetupService(BikeSetupConfig())


@pytest.fixture
def surface_map():
    return {
        "gravel_code": "Gravel",
        "unpaved_code": "Unpaved",
        "pebbles_code": "Pebbles",
        "grass_code": "Grass",
        "mud_code": "Muddy",
        "earth_code": "Earth",
        "stone_code": "Stony",
        "cobble_code": "Cobblestone",
        "asphalt_code": "Asphalt",
        "unknown_code": "Unknown",
        "other_code": "Other",
        "null_code": "Null",
        "none_code": "None",
    }


def test_normalize_bike_type_defaults_to_road_for_invalid(service):
    assert service._normalize_bike_type("") == "road"
    assert service._normalize_bike_type(None) == "road"
    assert service._normalize_bike_type(" ROAD ") == "road"


def test_coerce_tire_mm_accepts_valid_value(service):
    assert service._coerce_tire_mm(32) == 32
    assert service._coerce_tire_mm("28") == 28


def test_coerce_tire_mm_falls_back_for_invalid_value(service):
    assert service._coerce_tire_mm("bad") == 25
    assert service._coerce_tire_mm(None) == 25


def test_coerce_optional_int_ignores_invalid_values(service):
    assert service._coerce_optional_int("25") == 25
    assert service._coerce_optional_int(0) is None
    assert service._coerce_optional_int("bad") is None


def test_normalize_surface_type(service):
    assert service._normalize_surface_type(" Asphalt ") == "asphalt"
    assert service._normalize_surface_type("") == "mixed"
    assert service._normalize_surface_type(None) == "mixed"


def test_normalize_tire_size_option(service):
    assert service._normalize_tire_size_option(" 700c ") == "700c"
    assert service._normalize_tire_size_option(None) == ""


def test_coerce_rider_weight_accepts_valid(service):
    assert service._coerce_rider_weight(80) == 80.0
    assert service._coerce_rider_weight("82.5") == 82.5


def test_coerce_rider_weight_falls_back_for_invalid(service):
    assert service._coerce_rider_weight("bad") == 80.0
    assert service._coerce_rider_weight(None) == 80.0
    assert service._coerce_rider_weight(0) == 80.0
    assert service._coerce_rider_weight(-5) == 80.0


def test_clamp_mud_index(service):
    assert service._clamp_mud_index(0.5) == 0.5
    assert service._clamp_mud_index(-1) == 0.0
    assert service._clamp_mud_index(2) == 1.0
    assert service._clamp_mud_index("bad") == 0.0


def test_technical_difficulty_level_parses_s_label_and_dict(service):
    assert service._technical_difficulty_level("S3 - Technical") == 3
    assert service._technical_difficulty_level({"label": "S4 - Alpine"}) == 4
    assert service._technical_difficulty_level("unknown") == 0


def test_aggregate_surface_summary_success(service, surface_map):
    extras = {
        "surface": {
            "summary": [
                {"value": "gravel_code", "amount": 12.5},
                {"value": "unknown_code", "amount": 5.0},
                {"value": "gravel_code", "amount": 2.5},
            ]
        }
    }

    assert service._aggregate_surface_summary(extras, surface_map) == {
        "Gravel": 15.0,
        "Unmapped/Mixed": 5.0,
    }


def test_aggregate_surface_summary_skips_invalid_items(service, surface_map):
    extras = {
        "surface": {
            "summary": [
                "bad",
                {"value": "gravel_code", "amount": "bad"},
                {"value": "gravel_code", "amount": 2.0},
            ]
        }
    }
    assert service._aggregate_surface_summary(extras, surface_map) == {"Gravel": 2.0}


def test_aggregate_surface_summary_returns_empty_for_invalid_extras(
    service, surface_map
):
    assert service._aggregate_surface_summary([], surface_map) == {}
    assert service._aggregate_surface_summary(None, surface_map) == {}
    assert service._aggregate_surface_summary({}, []) == {}
    assert service._aggregate_surface_summary({"surface": "bad"}, surface_map) == {}
    assert (
        service._aggregate_surface_summary({"surface": {"summary": "bad"}}, surface_map)
        == {}
    )


def test_base_setup_for_known_bike_type(service):
    assert service._base_setup_for_bike_type("gravel") == (35.0, 40, "700c")


def test_base_setup_for_unknown_bike_type_defaults_to_road(service):
    assert service._base_setup_for_bike_type("weird-bike") == (85.0, 25, "700c")


def test_analyze_compatibility_gravel_critical_for_narrow_road_tires(
    service, surface_map
):
    extras = {"surface": {"summary": [{"value": "gravel_code", "amount": 20.0}]}}

    breakdown, warnings, is_compatible = service.analyze_compatibility(
        bike_type="ROAD", tire_mm=25, extras=extras, surface_map=surface_map
    )

    assert is_compatible is False
    assert breakdown == [{"type": "Gravel", "percentage": "20.0%"}]
    assert any("CRITICAL" in warning for warning in warnings)
    assert any("Geometry Warning" in warning for warning in warnings)


def test_analyze_compatibility_gravel_caution(service, surface_map):
    extras = {"surface": {"summary": [{"value": "gravel_code", "amount": 8.0}]}}

    breakdown, warnings, is_compatible = service.analyze_compatibility(
        bike_type="gravel", tire_mm=30, extras=extras, surface_map=surface_map
    )

    assert is_compatible is True
    assert breakdown == [{"type": "Gravel", "percentage": "8.0%"}]
    assert any("Caution" in warning for warning in warnings)


@pytest.mark.parametrize("surface_key", ["stone_code", "pebbles_code", "cobble_code"])
def test_analyze_compatibility_stones_warning_variants(
    service, surface_map, surface_key
):
    extras = {"surface": {"summary": [{"value": surface_key, "amount": 30.0}]}}

    _, warnings, is_compatible = service.analyze_compatibility(
        bike_type="mtb", tire_mm=30, extras=extras, surface_map=surface_map
    )

    assert is_compatible is True
    assert any("Safety Alert" in warning for warning in warnings)


@pytest.mark.parametrize("surface_key", ["grass_code", "mud_code", "earth_code"])
def test_analyze_compatibility_soft_terrain_warning_variants(
    service, surface_map, surface_key
):
    extras = {"surface": {"summary": [{"value": surface_key, "amount": 30.0}]}}

    _, warnings, is_compatible = service.analyze_compatibility(
        bike_type="mtb", tire_mm=40, extras=extras, surface_map=surface_map
    )

    assert is_compatible is True
    assert any("Traction Alert" in warning for warning in warnings)


def test_analyze_compatibility_unmapped_label_geometry_warning(service, surface_map):
    extras = {"surface": {"summary": [{"value": "unknown_code", "amount": 16.0}]}}

    breakdown, warnings, is_compatible = service.analyze_compatibility(
        bike_type="road", tire_mm=35, extras=extras, surface_map=surface_map
    )

    assert breakdown == [{"type": "Unmapped/Mixed", "percentage": "16.0%"}]
    assert any("Geometry Warning" in warning for warning in warnings)
    assert is_compatible is True


def test_analyze_compatibility_sorts_breakdown_desc(service, surface_map):
    extras = {
        "surface": {
            "summary": [
                {"value": "gravel_code", "amount": 30.0},
                {"value": "asphalt_code", "amount": 40.0},
                {"value": "grass_code", "amount": 20.0},
            ]
        }
    }

    breakdown, _, _ = service.analyze_compatibility(
        bike_type="gravel", tire_mm=40, extras=extras, surface_map=surface_map
    )

    assert [entry["type"] for entry in breakdown] == ["Asphalt", "Gravel", "Grass"]


def test_analyze_compatibility_invalid_tire_width_falls_back_to_25(
    service, surface_map
):
    extras = {"surface": {"summary": [{"value": "gravel_code", "amount": 20.0}]}}

    _, warnings, is_compatible = service.analyze_compatibility(
        bike_type="road", tire_mm="bad", extras=extras, surface_map=surface_map
    )

    assert is_compatible is False
    assert any("25mm tires are unsafe" in warning for warning in warnings)


def test_analyze_compatibility_handles_empty_inputs(service):
    assert service.analyze_compatibility(None, 28, {}, {}) == ([], [], True)


def test_analyze_compatibility_rim_width_mismatch_is_warning_only(service, surface_map):
    breakdown, warnings, is_compatible = service.analyze_compatibility(
        bike_type="mtb",
        tire_mm=64,
        extras={},
        surface_map=surface_map,
        rim_internal_width_mm=19,
    )

    assert breakdown == []
    assert is_compatible is True
    assert any(
        "Rim-Width Mismatch" in warning and "19mm" in warning for warning in warnings
    )


def test_analyze_compatibility_accepts_valid_rim_width(service, surface_map):
    _, warnings, is_compatible = service.analyze_compatibility(
        bike_type="mtb",
        tire_mm=58,
        extras={},
        surface_map=surface_map,
        rim_internal_width_mm=25,
    )

    assert is_compatible is True
    assert not any("Rim-Width Mismatch" in warning for warning in warnings)


def test_get_tire_setup_for_unknown_bike_type_defaults_to_road(service):
    setup = service.get_tire_setup(
        bike_type="unknown",
        tire_size_option="weird",
        mud_index=0.0,
        surface_type="mixed",
        rider_weight_kg=80.0,
    )

    assert isinstance(setup, TireSetupRecommendation)
    assert setup.tire_width_mm == 25
    assert setup.wheel_label == "700c"
    assert setup.strategy == "Standard"
    assert setup.psi_rear > setup.psi_front
    assert "F:" in setup.tactical_display and "R:" in setup.tactical_display


@pytest.mark.parametrize(
    "bike_type, tire_size, expected_label, expected_width",
    [
        ("mtb", "700c", '29"', 58),
        ("mtb", "27.5", "27.5", 58),
        ("gravel", "650b", "650b", 40),
        ("gravel", "weird", "700c", 40),
    ],
)
def test_get_tire_setup_wheel_labels(
    service, bike_type, tire_size, expected_label, expected_width
):
    setup = service.get_tire_setup(bike_type, tire_size, rider_weight_kg=85.0)

    assert setup.wheel_label == expected_label
    assert setup.tire_width_mm == expected_width


def test_get_tire_setup_mud_flotation(service):
    baseline = service.get_tire_setup("gravel", "700c", rider_weight_kg=85.0)
    muddy = service.get_tire_setup(
        "gravel", "700c", mud_index=0.9, rider_weight_kg=85.0
    )

    assert muddy.strategy == "Mud Flotation"
    assert muddy.knob_choice == "Mud Spikes"
    assert muddy.psi_rear < baseline.psi_rear
    assert any("Sealant Check Required" in advice for advice in muddy.advice)


def test_get_tire_setup_compliance_on_rocky_surface(service):
    baseline = service.get_tire_setup("gravel", "700c", rider_weight_kg=85.0)
    rocky = service.get_tire_setup(
        "gravel",
        "700c",
        surface_type="technical rocky root trail",
        rider_weight_kg=85.0,
    )

    assert rocky.strategy == "Compliance"
    assert rocky.psi_rear < baseline.psi_rear


def test_get_tire_setup_efficiency_on_smooth_surface(service):
    baseline = service.get_tire_setup("road", "700c", rider_weight_kg=85.0)
    smooth = service.get_tire_setup(
        "road", "700c", surface_type="smooth asphalt", rider_weight_kg=85.0
    )

    assert smooth.strategy == "Efficiency"
    assert smooth.knob_choice == "Semi-Slick"
    assert smooth.psi_rear > baseline.psi_rear


def test_get_tire_setup_weight_scaling_is_non_linear(service):
    light = service.get_tire_setup("road", "700c", rider_weight_kg=70.0)
    baseline = service.get_tire_setup("road", "700c", rider_weight_kg=85.0)
    heavy = service.get_tire_setup("road", "700c", rider_weight_kg=100.0)

    assert light.psi_rear < baseline.psi_rear < heavy.psi_rear
    assert heavy.psi_rear - baseline.psi_rear > 15.0
    assert baseline.psi_rear - light.psi_rear > 15.0


def test_get_tire_setup_invalid_weight_falls_back_to_default(service):
    setup = service.get_tire_setup("road", "700c", rider_weight_kg="bad")

    assert setup.psi_rear == 84.1
    assert setup.psi_front == 74.5


def test_get_tire_setup_invalid_mud_index_falls_back_to_zero(service):
    setup = service.get_tire_setup(
        "gravel", "700c", mud_index="bad", rider_weight_kg=85.0
    )
    assert setup.strategy == "Standard"


def test_get_tire_setup_non_string_surface_type_falls_back_to_mixed(service):
    setup = service.get_tire_setup(
        "road", "700c", surface_type=None, rider_weight_kg=85.0
    )
    assert setup.strategy == "Standard"


def test_get_tire_setup_non_string_tire_size_option_falls_back(service):
    setup = service.get_tire_setup("gravel", None, rider_weight_kg=85.0)
    assert setup.tire_width_mm == 40
    assert setup.wheel_label == "700c"


@pytest.mark.parametrize(
    "bike_type, expected_front_share, expected_rear_share",
    [
        ("road", 0.45, 0.55),
        ("gravel", 0.45, 0.55),
        ("mtb", 0.40, 0.60),
        ("e-mtb", 0.40, 0.60),
        ("enduro", 0.40, 0.60),
    ],
)
def test_get_tire_setup_differentiates_front_rear_for_all_profiles(
    service, bike_type, expected_front_share, expected_rear_share
):
    setup = service.get_tire_setup(bike_type, "29", rider_weight_kg=85.0)

    assert setup.load_split == {
        "front": expected_front_share,
        "rear": expected_rear_share,
    }
    assert setup.psi_rear > setup.psi_front


def test_get_tire_setup_casing_stiffness_reduces_pressure(service):
    lightweight = service.get_tire_setup(
        "mtb", "29", rider_weight_kg=85.0, casing_type="xc"
    )
    downhill = service.get_tire_setup(
        "mtb", "29", rider_weight_kg=85.0, casing_type="dh"
    )

    assert downhill.psi_rear < lightweight.psi_rear


def test_get_tire_setup_tubes_require_more_pressure_than_tubeless(service):
    tubeless = service.get_tire_setup("mtb", "29", rider_weight_kg=85.0, tubeless=True)
    tubes = service.get_tire_setup("mtb", "29", rider_weight_kg=85.0, tubeless=False)

    assert tubes.psi_rear > tubeless.psi_rear
    assert tubes.tubeless is False


def test_get_tire_setup_narrower_rim_requires_more_pressure(service):
    wide_rim = service.get_tire_setup(
        "gravel", "700c", rider_weight_kg=85.0, rim_internal_width_mm=25
    )
    narrow_rim = service.get_tire_setup(
        "gravel", "700c", rider_weight_kg=85.0, rim_internal_width_mm=19
    )

    assert narrow_rim.psi_rear > wide_rim.psi_rear


def test_get_tire_setup_tire_width_volume_scaling(service):
    wide = service.get_tire_setup("mtb", "29", rider_weight_kg=85.0, tire_width_mm=65)
    narrow = service.get_tire_setup("mtb", "29", rider_weight_kg=85.0, tire_width_mm=50)

    assert narrow.psi_rear > wide.psi_rear


def test_get_tire_setup_s3_terrain_recommends_inserts_and_warns_on_pinch_flat(service):
    setup = service.get_tire_setup(
        "mtb",
        "29",
        surface_type="rocky root trail",
        rider_weight_kg=85.0,
        technical_difficulty={"label": "S3 - Technical"},
        ascent_m=200.0,
    )

    assert setup.strategy == "Pinch-Flat Protection"
    assert any("Pinch-Flat Warning" in warning for warning in setup.warnings)
    assert any("Tire Inserts Recommended" in advice for advice in setup.advice)
    assert any("tubeless" in advice.lower() for advice in setup.advice)


def test_get_tire_setup_high_ascent_triggers_pinch_flat_warning(service):
    setup = service.get_tire_setup(
        "enduro",
        "29",
        surface_type="rocky technical descent",
        rider_weight_kg=85.0,
        ascent_m=1200.0,
    )

    assert any("Pinch-Flat Warning" in warning for warning in setup.warnings)
    assert "ascent" in " ".join(setup.warnings)


def test_get_tire_setup_uses_surface_breakdown_for_pinch_risk(service):
    setup = service.get_tire_setup(
        "enduro",
        "29",
        surface_type="gravel",
        rider_weight_kg=85.0,
        ascent_m=1200.0,
        surface_analysis=[{"type": "Stony", "percentage": "35.0%"}],
    )

    assert setup.strategy == "Pinch-Flat Protection"
    assert any("Pinch-Flat Warning" in warning for warning in setup.warnings)


def test_get_tire_setup_s3_technical_grade_is_treated_as_rocky(service):
    setup = service.get_tire_setup(
        "mtb",
        "29",
        surface_type="gravel",
        rider_weight_kg=85.0,
        technical_difficulty={"label": "S3 - Difficult"},
    )

    assert setup.strategy == "Pinch-Flat Protection"
    assert any("Pinch-Flat Warning" in warning for warning in setup.warnings)


def test_get_tire_setup_rim_width_mismatch_warning(service):
    setup = service.get_tire_setup(
        "mtb",
        "29",
        rider_weight_kg=85.0,
        tire_width_mm=64,
        rim_internal_width_mm=19,
    )

    assert any("Rim-Width Mismatch" in warning for warning in setup.warnings)


def test_module_level_analyze_compatibility_wrapper(monkeypatch):
    class FakeService:
        def analyze_compatibility(self, **kwargs):
            assert kwargs["rim_internal_width_mm"] == 19
            return ([{"type": "Asphalt", "percentage": "100.0%"}], [], True)

    monkeypatch.setattr(bike_setup_module, "service", FakeService())

    result = analyze_compatibility("road", 28, {}, {}, rim_internal_width_mm=19)
    assert result == ([{"type": "Asphalt", "percentage": "100.0%"}], [], True)


def test_module_level_get_tire_setup_wrapper(monkeypatch):
    expected = TireSetupRecommendation(
        wheel_label="700c",
        tire_width_mm=40,
        rim_internal_width_mm=21,
        casing_type="xc",
        tubeless=True,
        psi_front=32.9,
        psi_rear=37.1,
        bar_front=2.27,
        bar_rear=2.56,
        strategy="Standard",
        load_split={"front": 0.45, "rear": 0.55},
        knob_choice="All-Terrain / Trail",
        tactical_display="700c wheels | F: 32.9 PSI | R: 37.1 PSI",
    )

    class FakeService:
        def get_tire_setup(self, **kwargs):
            assert kwargs["tire_width_mm"] == 40
            assert kwargs["ascent_m"] == 500.0
            return expected

    monkeypatch.setattr(bike_setup_module, "service", FakeService())

    result = get_tire_setup("gravel", "700c", tire_width_mm=40, ascent_m=500.0)
    assert result == expected
