import pytest
from bikescout.tools.bike_setup import analyze_compatibility, get_tire_setup

class TestBikeSetup:


    def test_road_bike_incompatibility_on_gravel(self, surface_map):
        extras = {
            'surface': {'summary': [{'value': '2', 'amount': 15.1}]}
        }
        breakdown, warnings, is_compatible = analyze_compatibility(
            "road", 25, extras, surface_map
        )

        assert is_compatible is False
        assert any("CRITICAL" in w for w in warnings)
        assert any("Geometry Warning" in w for w in warnings)

    def test_surface_aggregation_unmapped(self, surface_map):
        extras = {
            'surface': {'summary': [
                {'value': '6', 'amount': 5.0},
                {'value': 'unknown_id', 'amount': 5.0}
            ]}
        }
        breakdown, _, _ = analyze_compatibility("mtb", 54, extras, surface_map)

        mixed_entry = next(item for item in breakdown if item["type"] == "Unmapped/Mixed")
        assert mixed_entry["percentage"] == "10.0%"

    def test_mud_traction_alert(self, surface_map):
        extras = {
            'surface': {'summary': [{'value': '4', 'amount': 100.0}]}
        }

        _, warnings, _ = analyze_compatibility("gravel", 38, extras, surface_map)
        assert any("Traction Alert" in w for w in warnings)


    def test_psi_weight_adjustment(self):
        _, tactical_85 = get_tire_setup("road", "700c", rider_weight_kg=85.0)
        _, tactical_95 = get_tire_setup("road", "700c", rider_weight_kg=95.0)

        assert "85.0 PSI" in tactical_85
        assert "87.0 PSI" in tactical_95

    @pytest.mark.parametrize("mud_index, expected_strategy", [
        (0.8, "Mud Flotation"),
        (0.1, "Standard")
    ])
    def test_mud_strategy_reduction(self, mud_index, expected_strategy):
        _, tactical = get_tire_setup("mtb", "29\"", mud_index=mud_index, rider_weight_kg=85.0)
        assert expected_strategy in tactical
        if mud_index > 0.6:
            assert "20.4 PSI" in tactical

    def test_surface_strategy_compliance(self):
        _, tactical = get_tire_setup("gravel", "700c", surface_type="technical roots")
        # 35 (base) - 1 (weight 80kg) - 2 (compliance) = 32.0
        assert "32.0 PSI" in tactical

    def test_stony_surface_warning(self, surface_map):
        extras = {
            'surface': {'summary': [{'value': '5', 'amount': 10.0}]} # 5 = Stony
        }
        _, warnings, _ = analyze_compatibility("gravel", 28, extras, surface_map)
        assert any("Safety Alert: Loose stones" in w for w in warnings)

    def test_traction_alert_muddy_grass(self, surface_map):
        extras = {
            'surface': {'summary': [{'value': '4', 'amount': 5.0}]} # 4 = Muddy
        }
        _, warnings, _ = analyze_compatibility("mtb", 38, extras, surface_map)
        assert any("Traction Alert" in w for w in warnings)

    def test_get_tire_setup_efficiency_strategy(self):
        _, tactical = get_tire_setup("road", "700c", surface_type="smooth asphalt", rider_weight_kg=85.0)
        assert "Efficiency Setup" in tactical
        # Base road 85 + 3.0 (Efficiency) = 88.0 PSI
        assert "88.0 PSI" in tactical

    def test_stony_surface_safety_alert(self, surface_map):
        extras = {
            'surface': {
                'summary': [{'value': '5', 'amount': 10.0}]
            }
        }

        _, warnings, _ = analyze_compatibility("gravel", 28, extras, surface_map)

        assert any("Safety Alert: Loose stones" in w for w in warnings)
        assert any("(Stony) detected" in w for w in warnings)

    def test_stony_surface_no_alert_if_wide_tires(self, surface_map):
        extras = {
            'surface': {
                'summary': [{'value': '5', 'amount': 10.0}]
            }
        }

        _, warnings, _ = analyze_compatibility("gravel", 35, extras, surface_map)

        assert not any("Safety Alert: Loose stones" in w for w in warnings)

    def test_stony_surface_coverage_final(self):
        local_surface_map = {"stone_id": "Stony"}
        extras = {
            'surface': {
                'summary': [{'value': 'stone_id', 'amount': 10.0}]
            }
        }

        breakdown, warnings, is_compatible = analyze_compatibility(
            "gravel", 28, extras, local_surface_map
        )

        assert any(b['type'] == "Stony" for b in breakdown)
        assert any("Safety Alert: Loose stones (Stony)" in w for w in warnings)

    def test_coverage_stones_and_pebbles(self):
        surface_map = {"10": "Cobblestone"}
        extras = {
            'surface': {
                'summary': [{'value': '10', 'amount': 20.0}]
            }
        }

        breakdown, warnings, is_compatible = analyze_compatibility(
            "mtb", 30, extras, surface_map
        )

        assert any("Safety Alert: Loose stones (Cobblestone)" in w for w in warnings)
        assert is_compatible is True