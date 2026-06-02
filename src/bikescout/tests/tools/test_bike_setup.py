import pytest

import bikescout.tools.bike_setup as bike_setup_module
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

    result = service._aggregate_surface_summary(extras, surface_map)

    assert result == {
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

    result = service._aggregate_surface_summary(extras, surface_map)

    assert result == {"Gravel": 2.0}


def test_aggregate_surface_summary_returns_empty_for_invalid_extras(service, surface_map):
    assert service._aggregate_surface_summary([], surface_map) == {}
    assert service._aggregate_surface_summary(None, surface_map) == {}


def test_aggregate_surface_summary_returns_empty_for_invalid_surface_map(service):
    assert service._aggregate_surface_summary({}, []) == {}
    assert service._aggregate_surface_summary({}, None) == {}


def test_aggregate_surface_summary_returns_empty_for_invalid_surface_container(service, surface_map):
    extras = {"surface": "bad"}
    assert service._aggregate_surface_summary(extras, surface_map) == {}


def test_aggregate_surface_summary_returns_empty_for_invalid_summary(service, surface_map):
    extras = {"surface": {"summary": "bad"}}
    assert service._aggregate_surface_summary(extras, surface_map) == {}


def test_base_setup_for_known_bike_type(service):
    assert service._base_setup_for_bike_type("gravel") == (35.0, 40, "700c")


def test_base_setup_for_unknown_bike_type_defaults_to_road(service):
    assert service._base_setup_for_bike_type("weird-bike") == (85.0, 25, "700c")


def test_analyze_compatibility_gravel_critical_for_narrow_road_tires(service, surface_map):
    extras = {
        "surface": {
            "summary": [
                {"value": "gravel_code", "amount": 20.0},
            ]
        }
    }

    breakdown, warnings, is_compatible = service.analyze_compatibility(
        bike_type="road",
        tire_mm=25,
        extras=extras,
        surface_map=surface_map,
    )

    assert is_compatible is False
    assert breakdown == [{"type": "Gravel", "percentage": "20.0%"}]
    assert any("CRITICAL" in w for w in warnings)
    assert any("Geometry Warning" in w for w in warnings)


def test_analyze_compatibility_gravel_caution(service, surface_map):
    extras = {
        "surface": {
            "summary": [
                {"value": "gravel_code", "amount": 8.0},
            ]
        }
    }

    breakdown, warnings, is_compatible = service.analyze_compatibility(
        bike_type="gravel",
        tire_mm=30,
        extras=extras,
        surface_map=surface_map,
    )

    assert is_compatible is True
    assert breakdown == [{"type": "Gravel", "percentage": "8.0%"}]
    assert any("Caution" in w for w in warnings)


def test_analyze_compatibility_stones_warning_variants(service, surface_map):
    for value in ["stone_code", "pebbles_code", "cobble_code"]:
        extras = {
            "surface": {
                "summary": [
                    {"value": value, "amount": 12.0},
                ]
            }
        }

        _, warnings, is_compatible = service.analyze_compatibility(
            bike_type="gravel",
            tire_mm=30,
            extras=extras,
            surface_map=surface_map,
        )

        assert is_compatible is True
        assert any("Safety Alert" in w for w in warnings)


def test_analyze_compatibility_soft_terrain_warning_variants(service, surface_map):
    for value in ["grass_code", "mud_code", "earth_code"]:
        extras = {
            "surface": {
                "summary": [
                    {"value": value, "amount": 18.0},
                ]
            }
        }

        _, warnings, is_compatible = service.analyze_compatibility(
            bike_type="gravel",
            tire_mm=40,
            extras=extras,
            surface_map=surface_map,
        )

        assert is_compatible is True
        assert any("Traction Alert" in w for w in warnings)


def test_analyze_compatibility_road_unmapped_geometry_warning(service, surface_map):
    extras = {
        "surface": {
            "summary": [
                {"value": "unknown_code", "amount": 16.0},
            ]
        }
    }

    breakdown, warnings, is_compatible = service.analyze_compatibility(
        bike_type="road",
        tire_mm=35,
        extras=extras,
        surface_map=surface_map,
    )

    assert is_compatible is True
    assert breakdown == [{"type": "Unmapped/Mixed", "percentage": "16.0%"}]
    assert any("Geometry Warning" in w for w in warnings)


def test_analyze_compatibility_handles_other_unmapped_labels(service, surface_map):
    extras = {
        "surface": {
            "summary": [
                {"value": "other_code", "amount": 5.0},
                {"value": "null_code", "amount": 3.0},
                {"value": "none_code", "amount": 2.0},
            ]
        }
    }

    breakdown, warnings, is_compatible = service.analyze_compatibility(
        bike_type="gravel",
        tire_mm=45,
        extras=extras,
        surface_map=surface_map,
    )

    assert is_compatible is True
    assert breakdown == [{"type": "Unmapped/Mixed", "percentage": "10.0%"}]
    assert warnings == []


def test_analyze_compatibility_sorts_breakdown_desc(service, surface_map):
    extras = {
        "surface": {
            "summary": [
                {"value": "asphalt_code", "amount": 30.0},
                {"value": "gravel_code", "amount": 40.0},
                {"value": "grass_code", "amount": 20.0},
            ]
        }
    }

    breakdown, _, _ = service.analyze_compatibility(
        bike_type="gravel",
        tire_mm=40,
        extras=extras,
        surface_map=surface_map,
    )

    assert breakdown == [
        {"type": "Gravel", "percentage": "40.0%"},
        {"type": "Asphalt", "percentage": "30.0%"},
        {"type": "Grass", "percentage": "20.0%"},
    ]


def test_analyze_compatibility_invalid_tire_width_falls_back_to_25(service, surface_map):
    extras = {
        "surface": {
            "summary": [
                {"value": "gravel_code", "amount": 20.0},
            ]
        }
    }

    _, warnings, is_compatible = service.analyze_compatibility(
        bike_type="road",
        tire_mm="bad",
        extras=extras,
        surface_map=surface_map,
    )

    assert is_compatible is False
    assert any("25mm tires are unsafe" in w for w in warnings)


def test_analyze_compatibility_handles_empty_inputs(service):
    breakdown, warnings, is_compatible = service.analyze_compatibility(
        bike_type=None,
        tire_mm=28,
        extras={},
        surface_map={},
    )

    assert breakdown == []
    assert warnings == []
    assert is_compatible is True


def test_get_tire_setup_for_unknown_bike_type_defaults_to_road(service):
    width_mm, display = service.get_tire_setup(
        bike_type="unknown",
        tire_size_option="weird",
        mud_index=0.0,
        surface_type="mixed",
        rider_weight_kg=80.0,
    )

    assert width_mm == 25
    assert "700c wheels" in display
    assert "[Standard Setup]" in display


def test_get_tire_setup_mtb_wheel_label_normalization(service):
    width_mm, display = service.get_tire_setup(
        bike_type="mtb",
        tire_size_option="700c",
        mud_index=0.0,
        surface_type="mixed",
        rider_weight_kg=85.0,
    )

    assert width_mm == 58
    assert '29" wheels' in display


def test_get_tire_setup_mtb_uses_custom_wheel_label(service):
    width_mm, display = service.get_tire_setup(
        bike_type="mtb",
        tire_size_option="27.5",
        mud_index=0.0,
        surface_type="mixed",
        rider_weight_kg=85.0,
    )

    assert width_mm == 58
    assert '27.5 wheels' in display


def test_get_tire_setup_gravel_650b(service):
    width_mm, display = service.get_tire_setup(
        bike_type="gravel",
        tire_size_option="650b",
        mud_index=0.0,
        surface_type="mixed",
        rider_weight_kg=85.0,
    )

    assert width_mm == 40
    assert "650b wheels" in display


def test_get_tire_setup_gravel_invalid_size_falls_back_to_700c(service):
    width_mm, display = service.get_tire_setup(
        bike_type="gravel",
        tire_size_option="weird",
        mud_index=0.0,
        surface_type="mixed",
        rider_weight_kg=85.0,
    )

    assert width_mm == 40
    assert "700c wheels" in display


def test_get_tire_setup_mud_strategy(service):
    width_mm, display = service.get_tire_setup(
        bike_type="gravel",
        tire_size_option="700c",
        mud_index=0.9,
        surface_type="mixed",
        rider_weight_kg=85.0,
    )

    assert width_mm == 40
    assert "[Mud Flotation Setup]" in display


def test_get_tire_setup_compliance_strategy(service):
    _, display = service.get_tire_setup(
        bike_type="gravel",
        tire_size_option="700c",
        mud_index=0.2,
        surface_type="technical rocky root trail",
        rider_weight_kg=85.0,
    )

    assert "[Compliance Setup]" in display


def test_get_tire_setup_efficiency_strategy(service):
    _, display = service.get_tire_setup(
        bike_type="road",
        tire_size_option="700c",
        mud_index=0.0,
        surface_type="smooth asphalt",
        rider_weight_kg=85.0,
    )

    assert "[Efficiency Setup]" in display


def test_get_tire_setup_weight_adjustment(service):
    _, display = service.get_tire_setup(
        bike_type="road",
        tire_size_option="700c",
        mud_index=0.0,
        surface_type="mixed",
        rider_weight_kg=90.0,
    )

    assert "86.0 PSI" in display


def test_get_tire_setup_invalid_weight_falls_back_to_default(service):
    _, display = service.get_tire_setup(
        bike_type="road",
        tire_size_option="700c",
        mud_index=0.0,
        surface_type="mixed",
        rider_weight_kg="bad",
    )

    assert "84.0 PSI" in display


def test_get_tire_setup_invalid_mud_index_falls_back_to_zero(service):
    _, display = service.get_tire_setup(
        bike_type="gravel",
        tire_size_option="700c",
        mud_index="bad",
        surface_type="mixed",
        rider_weight_kg=85.0,
    )

    assert "[Standard Setup]" in display


def test_get_tire_setup_non_string_surface_type_falls_back_to_mixed(service):
    _, display = service.get_tire_setup(
        bike_type="road",
        tire_size_option="700c",
        mud_index=0.0,
        surface_type=None,
        rider_weight_kg=85.0,
    )

    assert "[Standard Setup]" in display


def test_get_tire_setup_non_string_tire_size_option_falls_back(service):
    width_mm, display = service.get_tire_setup(
        bike_type="gravel",
        tire_size_option=None,
        mud_index=0.0,
        surface_type="mixed",
        rider_weight_kg=85.0,
    )

    assert width_mm == 40
    assert "700c wheels" in display


def test_module_level_analyze_compatibility_wrapper(monkeypatch):
    class FakeService:
        def analyze_compatibility(self, bike_type, tire_mm, extras, surface_map):
            return ([{"type": "Asphalt", "percentage": "100.0%"}], [], True)

    monkeypatch.setattr(bike_setup_module, "service", FakeService())

    result = analyze_compatibility("road", 28, {}, {})
    assert result == ([{"type": "Asphalt", "percentage": "100.0%"}], [], True)


def test_module_level_get_tire_setup_wrapper(monkeypatch):
    class FakeService:
        def get_tire_setup(self, bike_type, tire_size_option, mud_index=0.0, surface_type="mixed", rider_weight_kg=80.0):
            return (40, "700c wheels | 35.0 PSI (2.41 Bar) [Standard Setup]")

    monkeypatch.setattr(bike_setup_module, "service", FakeService())

    result = get_tire_setup("gravel", "700c")
    assert result == (40, "700c wheels | 35.0 PSI (2.41 Bar) [Standard Setup]")