import pytest

from bikescout.domain_logic import (
    build_mission_snapshot,
    clamp_complexity,
    ext_cast,
    extract_location_hint,
    extract_point_to_point,
    normalize_bike_type,
    normalize_tire_size,
    resolve_profile,
    resolve_route_mode,
    summarize_mission,
    wants_overlay,
)


class TestExtCast:
    def test_returns_default_for_empty_values(self):
        assert ext_cast(None, int, 99) == 99
        assert ext_cast("", int, 99) == 99
        assert ext_cast("None", int, 99) == 99
        assert ext_cast("null", int, 99) == 99

    def test_casts_numeric_strings(self):
        assert ext_cast("42", int, 0) == 42
        assert ext_cast("42.9", int, 0) == 42
        assert ext_cast("12.5", float, 0.0) == 12.5

    def test_extracts_numbers_from_text(self):
        assert ext_cast("distance: 12.5 km", float, 0.0) == 12.5
        assert ext_cast("about -7 meters", int, 0) == -7

    def test_returns_default_when_number_missing(self):
        assert ext_cast("abc", int, 5) == 5
        assert ext_cast("abc", float, 5.5) == 5.5

    def test_casts_bool_values(self):
        assert ext_cast("true", bool, False) is True
        assert ext_cast("YES", bool, False) is True
        assert ext_cast("0", bool, True) is False
        assert ext_cast(1, bool, False) is True
        assert ext_cast(0, bool, True) is False

    def test_returns_default_on_invalid_cast(self):
        assert ext_cast([], int, 3) == 3


class TestExtractLocationHint:
    def test_returns_none_for_empty_text(self):
        assert extract_location_hint("") is None
        assert extract_location_hint(None) is None

    def test_extracts_near_location(self):
        assert extract_location_hint("Find trails near Boulder") == "Boulder"

    def test_extracts_in_location(self):
        assert extract_location_hint("Best routes in Finale Ligure") == "Finale Ligure"

    def test_extracts_italian_location_pattern(self):
        assert extract_location_hint("Percorsi vicino a Trento") == "Trento"
        assert extract_location_hint("Giri intorno a Verona") == "Verona"

    def test_stops_on_im_add_with(self):
        assert extract_location_hint("Find routes near Turin I'm beginner") == "Turin"
        assert extract_location_hint("Find routes near Milan add climbs") == "Milan"
        assert extract_location_hint("Find routes near Rome with waterfalls") == "Rome"

    def test_returns_none_for_too_short_hint(self):
        assert extract_location_hint("in a") is None


class TestExtractPointToPoint:
    def test_returns_none_for_empty_input(self):
        assert extract_point_to_point("") is None

    def test_extracts_from_to_pattern(self):
        assert extract_point_to_point("from Milan to Bergamo") == ("Milan", "Bergamo")

    def test_extracts_italian_da_a_pattern(self):
        assert extract_point_to_point("da Torino a Cuneo") == ("Torino", "Cuneo")

    def test_extracts_arrow_pattern(self):
        assert extract_point_to_point("Genova -> Savona") == ("Genova", "Savona")

    def test_stops_on_with_and_comma(self):
        assert extract_point_to_point("from Como to Lecco with coffee stop") == ("Como", "Lecco")
        assert extract_point_to_point("from Pisa to Lucca, easy ride") == ("Pisa", "Lucca")

    def test_returns_none_for_invalid_values(self):
        assert extract_point_to_point("x -> y") is None


class TestResolveRouteMode:
    def test_uses_explicit_point_to_point_mode(self):
        assert resolve_route_mode({"route_mode": "point_to_point"}, "anything") == "point_to_point"
        assert resolve_route_mode({"route_mode": "a_to_b"}, "anything") == "point_to_point"
        assert resolve_route_mode({"route_mode": "a-b"}, "anything") == "point_to_point"

    def test_detects_point_to_point_from_user_input(self):
        assert resolve_route_mode({}, "from Como to Lecco") == "point_to_point"

    def test_defaults_to_round_trip(self):
        assert resolve_route_mode({}, "loop ride near Como") == "round_trip"


class TestNormalizeBikeType:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("electric", ("e-mtb", True)),
            ("e-mtb", ("e-mtb", True)),
            ("emtb", ("e-mtb", True)),
            ("ebike", ("e-mtb", True)),
            ("road bike", ("road", False)),
            ("gravel", ("gravel", False)),
            ("enduro", ("enduro", False)),
            ("downhill", ("enduro", False)),
            ("other", ("mtb", False)),
            (None, ("mtb", False)),
        ],
    )
    def test_normalize_bike_type(self, raw, expected):
        assert normalize_bike_type(raw) == expected


class TestNormalizeTireSize:
    @pytest.mark.parametrize(
        "raw,bike_type,expected",
        [
            ("28", "road", "700c"),
            ("28c", "road", "700c"),
            ("32c", "road", "32"),
            ("700c", "road", "700c"),
            ("29er", "mtb", "29"),
            ("29in", "mtb", "29"),
            ("27,5", "mtb", "27.5"),
            ("650b", "gravel", "650b"),
            ("32", "road", "32"),
        ],
    )
    def test_known_aliases(self, raw, bike_type, expected):
        assert normalize_tire_size(raw, bike_type) == expected

    def test_defaults_for_road(self):
        assert normalize_tire_size(None, "road") == "700c"

    def test_defaults_for_gravel(self):
        assert normalize_tire_size(None, "gravel") == "700c"

    def test_defaults_for_mtb_family(self):
        assert normalize_tire_size(None, "mtb") == "29"
        assert normalize_tire_size(None, "enduro") == "29"
        assert normalize_tire_size(None, "e-mtb") == "29"

    def test_unknown_bike_type_falls_back_to_29(self):
        assert normalize_tire_size("unknown", "city") == "29"


class TestResolveProfile:
    @pytest.mark.parametrize(
        "bike,expected",
        [
            ("mtb", "cycling-mountain"),
            ("enduro", "cycling-mountain"),
            ("downhill", "cycling-mountain"),
            ("gravel", "cycling-mountain"),
            ("road", "cycling-road"),
            ("e-mtb", "cycling-electric"),
            ("other", "cycling-regular"),
        ],
    )
    def test_resolve_profile(self, bike, expected):
        assert resolve_profile(bike) == expected


class TestWantsOverlay:
    def test_returns_true_when_llm_value_true(self):
        assert wants_overlay("anything", True, ("map",)) is True

    def test_matches_keywords_in_user_input(self):
        assert wants_overlay("show map overlay please", None, ("overlay", "map")) is True

    def test_falls_back_to_bool_llm_value(self):
        assert wants_overlay("", 1, ("overlay",)) is True
        assert wants_overlay("", 0, ("overlay",)) is False

    def test_returns_false_when_no_match(self):
        assert wants_overlay("hello world", None, ("overlay", "map")) is False


class TestClampComplexity:
    def test_returns_default_for_invalid_values(self):
        assert clamp_complexity(None) == 3
        assert clamp_complexity("abc") == 3

    def test_clamps_to_range(self):
        assert clamp_complexity(0) == 1
        assert clamp_complexity(1) == 1
        assert clamp_complexity(3) == 3
        assert clamp_complexity(5) == 5
        assert clamp_complexity(9) == 5


class TestBuildMissionSnapshot:
    def test_builds_round_trip_snapshot(self):
        ctx = build_mission_snapshot(
            location_name="Brescia",
            lat=45.54,
            lon=10.22,
            args={"bike_type": "mtb", "tire_size": "29"},
            distance_km=35.5,
        )

        assert ctx["route_mode"] == "round_trip"
        assert ctx["location_name"] == "Brescia"
        assert ctx["latitude"] == 45.54
        assert ctx["longitude"] == 10.22
        assert ctx["distance_km"] == 35.5
        assert ctx["bike_type"] == "mtb"
        assert ctx["tire_size"] == "29"
        assert ctx["destination_name"] is None
        assert ctx["dest_latitude"] is None
        assert ctx["dest_longitude"] is None

    def test_builds_point_to_point_snapshot(self):
        ctx = build_mission_snapshot(
            location_name="Trento",
            lat=46.07,
            lon=11.12,
            args={"bike_type": "road", "tire_size": "700c"},
            distance_km=80,
            route_mode="point_to_point",
            destination_name="Bolzano",
            dest_lat=46.50,
            dest_lon=11.35,
        )

        assert ctx["route_mode"] == "point_to_point"
        assert ctx["destination_name"] == "Bolzano"
        assert ctx["dest_latitude"] == 46.50
        assert ctx["dest_longitude"] == 11.35


class TestSummarizeMission:
    def test_returns_no_active_mission_without_context(self):
        assert summarize_mission({}) == "No active mission"
        assert summarize_mission({"location_name": None}) == "No active mission"

    def test_summarizes_point_to_point(self):
        ctx = {
            "route_mode": "point_to_point",
            "location_name": "Milan",
            "destination_name": "Pavia",
            "bike_type": "road",
        }
        assert summarize_mission(ctx) == "Milan → Pavia · road"

    def test_summarizes_round_trip(self):
        ctx = {
            "route_mode": "round_trip",
            "location_name": "Como",
            "distance_km": 45,
            "bike_type": "gravel",
        }
        assert summarize_mission(ctx) == "Como · 45 km · gravel"