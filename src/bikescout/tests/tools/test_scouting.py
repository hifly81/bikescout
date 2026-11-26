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

import inspect
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import requests

import bikescout.tools.scouting as scouting_module
from bikescout.schemas import (
    BikeSetup,
    MissionConstraints,
    RiderProfile,
    TireSetupRecommendation,
)
from bikescout.tools.scouting import (
    TrailScoutConfig,
    TrailScoutService,
    _map_surface_id,
    calculate_detailed_difficulty,
    calculate_performance_metrics,
    generate_tactical_gpx,
    get_complete_trail_scout,
)


class FakeResponse:
    def __init__(self, payload=None, raise_exc=None):
        self.payload = payload if payload is not None else {}
        self.raise_exc = raise_exc

    def raise_for_status(self):
        if self.raise_exc:
            raise self.raise_exc

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.response = response
        self.exc = exc
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        if self.exc:
            raise self.exc
        return self.response


def make_rider(
    weight_kg=75.0, fitness_level="intermediate", gender="male", sweat_profile="standard"
) -> RiderProfile:
    return cast(
        RiderProfile,
        SimpleNamespace(
            weight_kg=weight_kg,
            fitness_level=fitness_level,
            gender=gender,
            sweat_profile=sweat_profile,
        ),
    )


def make_bike(bike_type="gravel", is_ebike=False) -> BikeSetup:
    return cast(
        BikeSetup,
        SimpleNamespace(
            bike_type=bike_type,
            is_ebike=is_ebike,
        ),
    )


def make_mission(
    profile="cycling-regular",
    total_length_km=40.0,
    seed=42,
    direction_bias=None,
    avoid_urban=False,
    prefer_rural=False,
    distance_flex_percent=10,
    priority_mode="balanced",
    complexity=3,
) -> MissionConstraints:
    return cast(
        MissionConstraints,
        SimpleNamespace(
            profile=profile,
            total_length_km=total_length_km,
            seed=seed,
            direction_bias=direction_bias or [],
            avoid_urban=avoid_urban,
            prefer_rural=prefer_rural,
            distance_flex_percent=distance_flex_percent,
            priority_mode=priority_mode,
            complexity=complexity,
        ),
    )


def test_calculate_detailed_difficulty_unknown():
    assert calculate_detailed_difficulty(0, 100) == "Unknown"


def test_calculate_detailed_difficulty_expert():
    assert (
        calculate_detailed_difficulty(60, 200)
        == "Expert (Challenging distance or very steep climbs)"
    )


def test_calculate_detailed_difficulty_advanced():
    assert calculate_detailed_difficulty(35, 200) == "Advanced (Requires good fitness and stamina)"


def test_calculate_detailed_difficulty_moderate():
    assert calculate_detailed_difficulty(20, 200) == "Moderate (Accessible for regular cyclists)"


def test_calculate_detailed_difficulty_beginner():
    assert (
        calculate_detailed_difficulty(10, 100)
        == "Beginner (Short and relatively flat, ideal for everyone)"
    )


def test_calculate_detailed_difficulty_honors_requested_complexity():
    assert calculate_detailed_difficulty(10, 100, complexity=4).startswith("Advanced")
    assert calculate_detailed_difficulty(10, 100, complexity=5).startswith("Expert")


def test_calculate_detailed_difficulty_uses_sustained_climb_gradient():
    assert calculate_detailed_difficulty(20, 200, avg_climb_gradient=8.0).startswith("Advanced")
    assert calculate_detailed_difficulty(20, 200, avg_climb_gradient=11.0).startswith("Expert")


def test_calculate_detailed_difficulty_ignores_invalid_intent_values():
    assert calculate_detailed_difficulty(
        20,
        200,
        complexity=cast(Any, "bad"),
        avg_climb_gradient=cast(Any, "bad"),
    ) == ("Moderate (Accessible for regular cyclists)")


def test_generate_tactical_gpx_with_routegeometry_and_amenities(tmp_path, monkeypatch):
    monkeypatch.setattr(scouting_module.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(scouting_module.time, "time", lambda: 1000000)

    geojson_data = SimpleNamespace(
        coordinates=[
            [10.0, 45.0, 100],
            [10.001, 45.001, 0],
            [10.002, 45.002, 120],
            [10.003, 45.003, 130],
            [10.004, 45.004, 140],
            [10.005, 45.005, 150],
            [10.006, 45.006, 170],
            [10.007, 45.007, 190],
            [10.008, 45.008, 210],
            [10.009, 45.009, 230],
            [10.010, 45.010, 250],
            [10.011, 45.011, 270],
            [10.012, 45.012, 290],
            [10.013, 45.013, 310],
            [10.014, 45.014, 330],
            [10.015, 45.015, 350],
        ]
    )

    amenities = [{"name": "Water", "location": {"lat": 45.1, "lon": 10.1}}]

    result = generate_tactical_gpx("abc123", geojson_data, amenities)

    assert result["status"] == "Success"
    assert result["mcp_resource_uri"] == "bikescout://gpx/tactical_route_abc123.gpx"
    assert Path(result["file_location"]).exists()
    assert result["tactical_stats"]["healed_points"] >= 1


def test_generate_tactical_gpx_with_feature_dict(tmp_path, monkeypatch):
    monkeypatch.setattr(scouting_module.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(scouting_module.time, "time", lambda: 1000000)

    geojson_data = {
        "features": [
            {
                "geometry": {
                    "coordinates": [
                        [10.0, 45.0, 100],
                        [10.001, 45.001, 101],
                    ]
                }
            }
        ]
    }

    result = generate_tactical_gpx("xyz789", geojson_data, [])
    assert result["status"] == "Success"


def test_generate_tactical_gpx_cleanup_old_files(tmp_path, monkeypatch):
    gpx_dir = tmp_path / ".bikescout" / "gpx"
    gpx_dir.mkdir(parents=True, exist_ok=True)
    old_file = gpx_dir / "old.gpx"
    old_file.write_text("old", encoding="utf-8")

    with monkeypatch.context() as patch:
        patch.setattr(scouting_module.Path, "home", lambda: tmp_path)
        patch.setattr(scouting_module.time, "time", lambda: 2000000)
        original_stat = scouting_module.Path.stat

        def fake_stat(self, follow_symlinks=True):
            real_stat = original_stat(self, follow_symlinks=follow_symlinks)

            class Stat:
                st_mtime = 1
                st_mode = real_stat.st_mode

            return Stat()

        patch.setattr(scouting_module.Path, "stat", fake_stat)

        result = generate_tactical_gpx("cleanme", [[10.0, 45.0, 100], [10.001, 45.001, 101]], [])

    assert result["status"] == "Success"
    assert "follow_symlinks" in inspect.signature(Path.stat).parameters


def test_generate_tactical_gpx_error():
    result = generate_tactical_gpx("bad", None, [])
    assert result["status"] == "Error"
    assert "GPX Generation failed" in result["message"]


def test_calculate_performance_metrics_standard():
    rider = make_rider()
    bike = make_bike("gravel", False)

    result = calculate_performance_metrics(40.0, 500.0, rider, bike)

    assert result["estimated_hours"] > 0
    assert result["intensity_score"] == 2
    assert result["applied_vam"] == 700.0
    assert result["applied_base_speed"] == 20.0


def test_calculate_performance_metrics_ebike_boost():
    rider = make_rider(fitness_level="beginner")
    bike = make_bike("e-mtb", True)

    result = calculate_performance_metrics(70.0, 1000.0, rider, bike)

    assert result["applied_vam"] == 850.0
    assert result["applied_base_speed"] == 21.0
    assert result["intensity_score"] == 3


def test_map_surface_id():
    assert _map_surface_id(1) == "asphalt"
    assert _map_surface_id(2) == "unpaved"
    assert _map_surface_id(5) == "gravel"
    assert _map_surface_id(10) == "dirt"
    assert _map_surface_id(11) == "grass"
    assert _map_surface_id(12) == "compact"
    assert _map_surface_id(999) == "dirt"


def test_routing_payload_round_trip():
    mission = make_mission()
    payload = TrailScoutService._routing_payload(45.0, 10.0, mission, None, None)

    assert payload["coordinates"] == [[10.0, 45.0]]
    assert payload["options"]["round_trip"]["seed"] == 42
    assert payload["options"]["round_trip"]["points"] == 3
    assert payload["options"]["round_trip"]["length"] == 38000.0


def test_routing_payload_a_to_b():
    mission = make_mission()
    payload = TrailScoutService._routing_payload(45.0, 10.0, mission, 46.0, 11.0)

    assert payload["coordinates"] == [[10.0, 45.0], [11.0, 46.0]]
    assert "options" not in payload


def test_build_directional_anchor_south_east():
    mission = make_mission(
        total_length_km=60.0,
        direction_bias=["south", "east"],
        priority_mode="ride_character_first",
    )

    anchor = TrailScoutService._build_directional_anchor(45.0, 10.0, mission)

    assert anchor is not None
    assert anchor["direction_bias"] == ["south", "east"]
    assert anchor["latitude"] < 45.0
    assert anchor["longitude"] > 10.0
    assert anchor["offset_km"] >= 3.0


def test_routing_payload_includes_preferred_anchor_when_direction_bias_present():
    mission = make_mission(
        total_length_km=50.0,
        direction_bias=["south", "east"],
        prefer_rural=True,
    )

    payload = TrailScoutService._routing_payload(45.0, 10.0, mission, None, None)

    assert payload["coordinates"] == [[10.0, 45.0]]
    assert "preferred_anchor" in payload
    assert payload["preferred_anchor"]["direction_bias"] == ["south", "east"]


def test_distance_to_anchor_m_prefers_route_closer_to_anchor():
    anchor = {
        "latitude": 44.95,
        "longitude": 10.05,
        "direction_bias": ["south", "east"],
        "offset_km": 7.0,
    }

    near_route = {
        "features": [
            {
                "properties": {"summary": {"distance": 40000}, "ascent": 500},
                "geometry": {"coordinates": [[10.049, 44.951, 100], [10.03, 44.97, 110]]},
            }
        ]
    }

    far_route = {
        "features": [
            {
                "properties": {"summary": {"distance": 40000}, "ascent": 500},
                "geometry": {"coordinates": [[9.90, 45.10, 100], [9.91, 45.11, 110]]},
            }
        ]
    }

    near_dist = TrailScoutService._distance_to_anchor_m(near_route, anchor)
    far_dist = TrailScoutService._distance_to_anchor_m(far_route, anchor)

    assert near_dist < far_dist


def test_route_candidate_score_prefers_anchor_when_ride_character_first():
    mission = make_mission(
        total_length_km=40.0,
        direction_bias=["south", "east"],
        priority_mode="ride_character_first",
    )

    anchor = {
        "latitude": 44.95,
        "longitude": 10.05,
        "direction_bias": ["south", "east"],
        "offset_km": 7.0,
    }

    closer_to_anchor_but_less_exact_distance = {
        "features": [
            {
                "properties": {"summary": {"distance": 37000}, "ascent": 500},
                "geometry": {"coordinates": [[10.049, 44.951, 100], [10.03, 44.97, 110]]},
            }
        ]
    }

    exact_distance_but_far_from_anchor = {
        "features": [
            {
                "properties": {"summary": {"distance": 40000}, "ascent": 500},
                "geometry": {"coordinates": [[9.90, 45.10, 100], [9.91, 45.11, 110]]},
            }
        ]
    }

    score_close = TrailScoutService._route_candidate_score(
        closer_to_anchor_but_less_exact_distance,
        mission,
        anchor,
    )
    score_far = TrailScoutService._route_candidate_score(
        exact_distance_but_far_from_anchor,
        mission,
        anchor,
    )

    assert score_close < score_far


def _route_with_surface(summary):
    return {
        "features": [
            {
                "properties": {
                    "summary": {"distance": 40000},
                    "ascent": 500,
                    "extras": {"surface": {"summary": summary}},
                },
                "geometry": {"coordinates": [[10.0, 45.0, 100], [10.01, 45.01, 101]]},
            }
        ]
    }


def test_offroad_share_accepts_ors_amount_and_legacy_distance():
    route = _route_with_surface(
        [
            {"value": 5, "amount": 3000},
            {"value": 1, "amount": 1000},
        ]
    )
    assert TrailScoutService._offroad_share_from_route(route) == 0.75

    legacy = _route_with_surface(
        [
            {"value": 10, "distance": 2000},
            {"value": 1, "distance": 2000},
        ]
    )
    assert TrailScoutService._offroad_share_from_route(legacy) == 0.5
    assert TrailScoutService._offroad_share_from_route({"features": []}) == 0.0


def test_route_candidate_score_prefers_offroad_when_requested():
    mission = make_mission(
        avoid_urban=True,
        prefer_rural=True,
        priority_mode="ride_character_first",
    )
    bike = make_bike("mtb")
    offroad = _route_with_surface([{"value": 5, "amount": 40000}])
    paved = _route_with_surface([{"value": 1, "amount": 40000}])

    assert TrailScoutService._route_candidate_score(offroad, mission, None, bike) < (
        TrailScoutService._route_candidate_score(paved, mission, None, bike)
    )


def test_prefers_offroad_reads_bike_type_from_bike_setup():
    mission = make_mission(
        avoid_urban=True,
        prefer_rural=True,
        priority_mode="ride_character_first",
    )
    assert not hasattr(mission, "bike_type")
    assert TrailScoutService._prefers_offroad(mission, make_bike("mtb"))
    assert not TrailScoutService._prefers_offroad(mission, make_bike("road"))


def test_route_candidate_score_ignores_surface_without_offroad_preference():
    mission = make_mission()
    offroad = _route_with_surface([{"value": 5, "amount": 40000}])
    paved = _route_with_surface([{"value": 1, "amount": 40000}])

    assert TrailScoutService._route_candidate_score(offroad, mission, None) == (
        TrailScoutService._route_candidate_score(paved, mission, None)
    )


def test_get_complete_trail_scout_reports_offroad_share_without_extra_routing():
    payload = _route_with_surface(
        [
            {"value": 5, "amount": 3000},
            {"value": 1, "amount": 1000},
        ]
    )
    session = FakeSession(response=FakeResponse(payload=payload))
    service = make_service(session)
    mission = make_mission(
        avoid_urban=True,
        prefer_rural=True,
        priority_mode="ride_character_first",
    )

    result = service.get_complete_trail_scout(
        api_key="key",
        latitude=45.0,
        longitude=10.0,
        rider=make_rider(),
        bike=make_bike("mtb", False),
        mission=mission,
    )

    result_payload = cast(dict[str, Any], result)
    info = cast(dict[str, Any], result_payload["info"])
    surface = cast(dict[str, Any], info["surface_analysis"])
    metadata = cast(dict[str, Any], surface["metadata"])
    assert metadata["offroad_share_percent"] == 75.0
    assert metadata["offroad_request_status"] == "met"
    assert len(session.calls) == 1


def test_get_complete_trail_scout_warns_when_offroad_target_is_not_met():
    payload = _route_with_surface([{"value": 1, "amount": 40000}])
    service = make_service(FakeSession(response=FakeResponse(payload=payload)))
    mission = make_mission(
        avoid_urban=True,
        prefer_rural=True,
        priority_mode="ride_character_first",
    )

    result = service.get_complete_trail_scout(
        api_key="key",
        latitude=45.0,
        longitude=10.0,
        rider=make_rider(),
        bike=make_bike("mtb", False),
        mission=mission,
    )

    result_payload = cast(dict[str, Any], result)
    info = cast(dict[str, Any], result_payload["info"])
    surface = cast(dict[str, Any], info["surface_analysis"])
    metadata = cast(dict[str, Any], surface["metadata"])
    assert metadata["offroad_share_percent"] == 0.0
    assert metadata["offroad_request_status"] == "not_met"
    assert "Try another seed" in metadata["offroad_request_note"]


def test_select_best_route_candidate_uses_multiple_seeds_and_picks_best_anchor_match():
    payload_seed_42 = {
        "features": [
            {
                "properties": {"summary": {"distance": 40000}, "ascent": 500},
                "geometry": {"coordinates": [[9.90, 45.10, 100], [9.91, 45.11, 110]]},
            }
        ]
    }
    payload_seed_59 = {
        "features": [
            {
                "properties": {"summary": {"distance": 38500}, "ascent": 500},
                "geometry": {"coordinates": [[10.048, 44.952, 100], [10.03, 44.97, 110]]},
            }
        ]
    }
    payload_seed_85 = {
        "features": [
            {
                "properties": {"summary": {"distance": 39200}, "ascent": 500},
                "geometry": {"coordinates": [[10.02, 45.00, 100], [10.01, 44.99, 110]]},
            }
        ]
    }

    class MultiSeedSession:
        def __init__(self):
            self.calls = []

        def post(self, url, json=None, headers=None, timeout=None):
            self.calls.append(json)
            seed = cast(dict[str, Any], json)["options"]["round_trip"]["seed"]

            if seed == 42:
                return FakeResponse(payload=payload_seed_42)
            if seed == 59:
                return FakeResponse(payload=payload_seed_59)
            if seed == 85:
                return FakeResponse(payload=payload_seed_85)

            return FakeResponse(payload=payload_seed_42)

    session = MultiSeedSession()
    service = make_service(session)

    mission = make_mission(
        total_length_km=40.0,
        seed=42,
        direction_bias=["south", "east"],
        priority_mode="ride_character_first",
    )

    payload = TrailScoutService._routing_payload(45.0, 10.0, mission, None, None)
    anchor = payload.pop("preferred_anchor", None)

    result = service._select_best_route_candidate(
        api_key="key",
        mission=mission,
        payload=payload,
        anchor=anchor,
    )

    assert result == payload_seed_59
    used_seeds = [call["options"]["round_trip"]["seed"] for call in session.calls]
    assert used_seeds == [42, 59, 85]


def test_select_best_route_candidate_falls_back_to_single_request_without_anchor():
    payload = {
        "coordinates": [[10.0, 45.0]],
        "options": {"round_trip": {"length": 38000.0, "seed": 42, "points": 3}},
        "elevation": "true",
        "extra_info": ["surface", "steepness"],
    }

    expected = {
        "features": [
            {
                "properties": {"summary": {"distance": 38000}, "ascent": 450},
                "geometry": {"coordinates": [[10.0, 45.0, 100], [10.01, 45.01, 101]]},
            }
        ]
    }

    session = FakeSession(response=FakeResponse(payload=expected))
    service = make_service(session)
    mission = make_mission()

    result = service._select_best_route_candidate(
        api_key="key",
        mission=mission,
        payload=payload,
        anchor=None,
    )

    assert result == expected
    assert len(session.calls) == 1


def test_select_best_route_candidate_falls_back_when_all_multi_seed_attempts_fail():
    class FailingSession:
        def __init__(self):
            self.calls = []

        def post(self, url, json=None, headers=None, timeout=None):
            self.calls.append(json)
            seed = cast(dict[str, Any], json)["options"]["round_trip"]["seed"]
            if seed in {42, 59, 85}:
                raise requests.exceptions.RequestException("temporary failure")
            return FakeResponse(
                payload={
                    "features": [
                        {
                            "properties": {"summary": {"distance": 40000}, "ascent": 500},
                            "geometry": {"coordinates": [[10.0, 45.0, 100], [10.01, 45.01, 101]]},
                        }
                    ]
                }
            )

    session = FailingSession()
    service = make_service(session)

    mission = make_mission(
        total_length_km=40.0,
        seed=42,
        direction_bias=["south"],
        priority_mode="balanced",
    )

    payload = TrailScoutService._routing_payload(45.0, 10.0, mission, None, None)
    anchor = payload.pop("preferred_anchor", None)

    safe_payload = dict(payload)
    safe_options = dict(safe_payload["options"])
    safe_round_trip = dict(safe_options["round_trip"])
    safe_round_trip["seed"] = 999
    safe_options["round_trip"] = safe_round_trip
    safe_payload["options"] = safe_options

    result = service._select_best_route_candidate(
        api_key="key",
        mission=mission,
        payload=safe_payload,
        anchor=anchor,
    )

    assert result["features"][0]["properties"]["summary"]["distance"] == 40000
    assert len(session.calls) == 4


def test_base_response_payload():
    result = TrailScoutService._base_response_payload(40.0, 500.0, None, None)
    assert result["info"]["route_type"] == "Round Trip"

    result_ab = TrailScoutService._base_response_payload(40.0, 500.0, 46.0, 11.0)
    assert result_ab["info"]["route_type"] == "A to B"


def test_dominant_surface_from_breakdown():
    breakdown = [{"type": "Gravel", "percentage": "70%"}, {"type": "Asphalt", "percentage": "30%"}]
    assert TrailScoutService._dominant_surface_from_breakdown(breakdown) == "Gravel"
    assert TrailScoutService._dominant_surface_from_breakdown([]) == "Unknown"
    assert (
        TrailScoutService._dominant_surface_from_breakdown([{"type": "Gravel", "percentage": None}])
        == "Unknown"
    )


def test_weather_snapshot_list():
    weather_report = {
        "tactical_forecast": [
            {
                "time": "09:00",
                "temp": 20,
                "app_temp": 19,
                "rain_prob": 10,
                "rain_mm": 0.0,
                "wind": 12,
                "gusts": 20,
            },
            {"hour": "10:00", "temp": 21},
        ]
    }

    result = TrailScoutService._weather_snapshot_list(weather_report)

    assert result[0]["time"] == "09:00"
    assert result[1]["time"] == "10:00"


def test_ensure_logistics():
    payload = {}
    TrailScoutService._ensure_logistics(payload)
    assert payload["logistics"] == {}

    payload = {"logistics": None}
    TrailScoutService._ensure_logistics(payload)
    assert payload["logistics"] == {}


def make_service(session):
    return TrailScoutService(
        config=TrailScoutConfig(),
        http_session=session,
        map_saver=lambda filename_part, data: {
            "status": "Success",
            "file_location": f"/tmp/{filename_part}.html",
            "mcp_resource_uri": f"bikescout://map/{filename_part}",
        },
        weather_getter=lambda lat, lon, target_date=None: {
            "status": "Success",
            "tactical_forecast": [
                {
                    "time": "09:00",
                    "temp": 20,
                    "app_temp": 19,
                    "rain_prob": 10,
                    "rain_mm": 0.0,
                    "wind": 12,
                    "gusts": 20,
                }
            ],
            "reference_conditions": {"temp_max": 24},
            "safety_advice": {"status": "? [GO]"},
        },
        weather_windowing=lambda weather_report, start, end: weather_report,
        surface_analyzer=lambda api_key, latitude, longitude, rider, bike, mission, target_date=None, route_feature=None: {
            "status": "Success",
            "tactical_briefing": {
                "distance_km": 42.0,
                "elevation_gain_m": 600.0,
                "max_gradient": 12.5,
                "climb_list": [{"category": "C3 - Challenging", "gain_m": 120.0}],
                "data_confidence": 0.82,
            },
            "surface_breakdown": [{"type": "Gravel", "percentage": "70%"}],
        },
        poi_scout=lambda api_key, latitude, longitude, total_length_km: {
            "status": "Success",
            "amenities": [{"name": "Water", "location": {"lat": 45.1, "lon": 10.1}}],
        },
        mud_analyzer=lambda latitude, longitude, dominant_surface, target_date=None: {
            "status": "Success" if dominant_surface == "Gravel" else "Error",
            "mud_risk": "medium",
        },
        altimetry_getter=lambda geometry, uuid_input, style: {
            "status": "Success",
            "file_location": f"/tmp/{uuid_input}.png",
            "mcp_resource_uri": f"bikescout://altimetry/{uuid_input}",
        },
        nutrition_getter=lambda estimated_hours, max_temp, intensity_score, weight_kg, gender, sweat_profile: {
            "status": "Success",
            "mission_nutrition_briefing": {},
        },
        gpx_generator=lambda filename_part, geojson_data, amenities=None: {
            "status": "Success",
            "file_location": f"/tmp/{filename_part}.gpx",
            "mcp_resource_uri": f"bikescout://gpx/{filename_part}",
        },
        uuid_func=lambda: "fixedid",
    )


def test_get_complete_trail_scout_success_all_features():
    payload = {
        "features": [
            {
                "properties": {"summary": {"distance": 40000}, "ascent": 500},
                "geometry": {"coordinates": [[10.0, 45.0, 100], [10.001, 45.001, 101]]},
            }
        ]
    }
    session = FakeSession(response=FakeResponse(payload=payload))
    service = make_service(session)

    rider = make_rider()
    bike = make_bike("gravel", False)
    mission = make_mission()

    result = service.get_complete_trail_scout(
        api_key="key",
        latitude=45.0,
        longitude=10.0,
        rider=rider,
        bike=bike,
        mission=mission,
        include_gpx=True,
        include_map=True,
        include_poi=True,
        include_altimetry=True,
        include_weather=True,
        include_mud_analysis=True,
        include_nutrition_plan=True,
    )

    info = cast(dict[str, Any], result["info"])

    assert result["status"] == "Success"
    assert info["surface_analysis"]["status"] == "Success"
    assert info["max_gradient"] == 12.5
    assert info["climb_list"][0]["category"] == "C3 - Challenging"
    assert info["data_confidence"] == 0.82
    assert result["conditions"]["weather"] is not None
    assert result["conditions"]["mud_risk"]["status"] == "Success"
    assert result["logistics"]["nutrition_plan"]["status"] == "Success"
    assert result["logistics"]["nearby_amenities"]
    assert result["map_path"] == "/tmp/fixedid.html"
    assert result["gpx_export_path"] == "/tmp/fixedid.gpx"
    assert result["elevation_profile_path"] == "/tmp/fixedid.png"


def test_get_complete_trail_scout_uses_complexity_and_canonical_climbs():
    payload = {
        "features": [
            {
                "properties": {"summary": {"distance": 35000}, "ascent": 300},
                "geometry": {"coordinates": [[10.0, 45.0, 100], [10.001, 45.001, 101]]},
            }
        ]
    }
    service = make_service(FakeSession(response=FakeResponse(payload=payload)))
    climbs = [{"category": "C4 - Short Burner", "gain_m": 84.0}]
    service.surface_analyzer = (
        lambda api_key, latitude, longitude, rider, bike, mission, target_date=None, route_feature=None: {
            "status": "Success",
            "tactical_briefing": {
                "distance_km": 35.0,
                "elevation_gain_m": 300.0,
                "terrain_analysis": {"climbs": climbs, "avg_climb_gradient": 0.0},
            },
            "surface_breakdown": [{"type": "Gravel", "percentage": "100%"}],
        }
    )

    result = service.get_complete_trail_scout(
        api_key="key",
        latitude=45.0,
        longitude=10.0,
        rider=make_rider(),
        bike=make_bike("gravel", False),
        mission=make_mission(complexity=5),
    )
    info = cast(dict[str, Any], result["info"])

    assert info["difficulty"].startswith("Expert")
    assert info["climb_list"] == climbs
    assert "climb_list" not in info["surface_analysis"]["tactical_briefing"]


def test_get_complete_trail_scout_uses_selected_route_for_surface_and_exports():
    """Surface metrics, GPX and altimetry must describe one and the same route."""
    route_coords = [
        [10.0, 45.0, 100],
        [10.001, 45.001, 102],
        [10.002, 45.002, 105],
        [10.003, 45.003, 103],
        [10.004, 45.004, 108],
    ]
    payload = {
        "features": [
            {
                "properties": {
                    "summary": {"distance": 40000},
                    "ascent": 500,
                    "extras": {"surface": {"summary": [{"value": 5, "distance": 2000}]}},
                },
                "geometry": {"coordinates": route_coords},
            }
        ]
    }
    service = make_service(FakeSession(response=FakeResponse(payload=payload)))
    seen: dict[str, Any] = {}

    def recording_surface(
        api_key,
        latitude,
        longitude,
        rider,
        bike,
        mission,
        target_date=None,
        route_feature=None,
    ):
        seen["route_feature"] = route_feature
        return {
            "status": "Success",
            "tactical_briefing": {
                "distance_km": 4.2,
                "elevation_gain_m": 120.0,
                "max_gradient": 8.0,
                "climb_list": [],
                "data_confidence": 0.9,
            },
            "surface_breakdown": [{"type": "Gravel", "percentage": "80%"}],
        }

    def recording_gpx(filename_part, geojson_data, amenities=None):
        seen["gpx_coords"] = geojson_data.coordinates
        return {
            "status": "Success",
            "file_location": f"/tmp/{filename_part}.gpx",
            "mcp_resource_uri": f"bikescout://gpx/{filename_part}",
        }

    def recording_altimetry(geometry, uuid_input, style):
        seen["altimetry_coords"] = geometry.coordinates
        return {
            "status": "Success",
            "file_location": f"/tmp/{uuid_input}.png",
            "mcp_resource_uri": f"bikescout://altimetry/{uuid_input}",
        }

    service.surface_analyzer = recording_surface
    service.gpx_generator = recording_gpx
    service.altimetry_getter = recording_altimetry

    result = service.get_complete_trail_scout(
        api_key="key",
        latitude=45.0,
        longitude=10.0,
        rider=make_rider(),
        bike=make_bike(),
        mission=make_mission(),
        include_gpx=True,
        include_altimetry=True,
    )

    assert result["status"] == "Success"
    assert seen["route_feature"] == payload["features"][0]
    assert seen["gpx_coords"] == route_coords
    assert seen["altimetry_coords"] == route_coords
    assert seen["route_feature"]["geometry"]["coordinates"] == seen["gpx_coords"]


def test_get_complete_trail_scout_does_not_fetch_second_route_for_surface():
    """The real surface service must analyze the supplied route, not re-query ORS."""
    from bikescout.tools.surface import SurfaceAnalyzerConfig, SurfaceAnalyzerService

    route_coords = [
        [10.0, 45.0, 100],
        [10.001, 45.001, 102],
        [10.002, 45.002, 105],
        [10.003, 45.003, 103],
        [10.004, 45.004, 108],
        [10.005, 45.005, 110],
        [10.006, 45.006, 115],
        [10.007, 45.007, 111],
    ]
    payload = {
        "features": [
            {
                "properties": {
                    "summary": {"distance": 8000},
                    "ascent": 300,
                    "extras": {"surface": {"summary": [{"value": 5, "distance": 5000}]}},
                },
                "geometry": {"coordinates": route_coords},
            }
        ]
    }
    routing_session = FakeSession(response=FakeResponse(payload=payload))

    class NoCallSession:
        def __init__(self):
            self.calls: list[Any] = []

        def post(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            raise AssertionError("Surface analysis issued a second ORS request")

    surface_session = NoCallSession()
    real_surface = SurfaceAnalyzerService(
        config=SurfaceAnalyzerConfig(),
        http_session=surface_session,
        mud_analyzer=lambda lat, lon, surface, target_date=None: {
            "metadata": {},
            "tactical_analysis": {},
        },
        compatibility_analyzer=lambda *args, **kwargs: ([], [], True),
        tire_setup_getter=lambda **kwargs: TireSetupRecommendation(
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
        ),
        battery_drain_calculator=lambda **kwargs: {},
    )

    service = make_service(routing_session)
    service.surface_analyzer = real_surface.get_surface_analyzer

    bike = SimpleNamespace(
        bike_type="gravel",
        is_ebike=False,
        tire_size="700c",
        tire_width_mm=40,
        battery_wh=0,
    )
    result = service.get_complete_trail_scout(
        api_key="key",
        latitude=45.0,
        longitude=10.0,
        rider=make_rider(),
        bike=cast(BikeSetup, bike),
        mission=make_mission(),
    )

    assert result["status"] == "Success"
    assert result["info"]["surface_analysis"]["status"] == "Success"
    assert len(routing_session.calls) == 1
    assert surface_session.calls == []
    assert (
        result["info"]["distance_km"]
        == result["info"]["surface_analysis"]["tactical_briefing"]["distance_km"]
    )


def test_get_complete_trail_scout_surface_failure_weather_unavailable():
    payload = {
        "features": [
            {
                "properties": {"summary": {"distance": 40000}, "ascent": 500},
                "geometry": {"coordinates": [[10.0, 45.0, 100], [10.001, 45.001, 101]]},
            }
        ]
    }
    session = FakeSession(response=FakeResponse(payload=payload))
    service = TrailScoutService(
        config=TrailScoutConfig(),
        http_session=session,
        surface_analyzer=lambda *args, **kwargs: {"status": "Error"},
        weather_getter=lambda *args, **kwargs: {"status": "Error"},
        weather_windowing=lambda x, start, end: x,
        gpx_generator=lambda *args, **kwargs: {
            "status": "Success",
            "file_location": "/tmp/x.gpx",
            "mcp_resource_uri": "uri",
        },
        uuid_func=lambda: "fixedid",
    )

    rider = make_rider()
    bike = make_bike()
    mission = make_mission()

    result = service.get_complete_trail_scout(
        api_key="key",
        latitude=45.0,
        longitude=10.0,
        rider=rider,
        bike=bike,
        mission=mission,
        include_weather=True,
    )

    assert result["status"] == "Success"
    assert result["conditions"]["weather_status"] == "Unavailable"


def test_get_complete_trail_scout_weather_exception():
    payload = {
        "features": [
            {
                "properties": {"summary": {"distance": 40000}, "ascent": 500},
                "geometry": {"coordinates": [[10.0, 45.0, 100], [10.001, 45.001, 101]]},
            }
        ]
    }
    session = FakeSession(response=FakeResponse(payload=payload))
    service = TrailScoutService(
        config=TrailScoutConfig(),
        http_session=session,
        surface_analyzer=lambda *args, **kwargs: {"status": "Error"},
        weather_getter=lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
        weather_windowing=lambda x, start, end: x,
        gpx_generator=lambda *args, **kwargs: {
            "status": "Success",
            "file_location": "/tmp/x.gpx",
            "mcp_resource_uri": "uri",
        },
        uuid_func=lambda: "fixedid",
    )

    rider = make_rider()
    bike = make_bike()
    mission = make_mission()

    result = service.get_complete_trail_scout(
        api_key="key",
        latitude=45.0,
        longitude=10.0,
        rider=rider,
        bike=bike,
        mission=mission,
        include_weather=True,
    )

    assert result["status"] == "Success"
    assert "Technical bypass: boom" == result["conditions"]["weather_error"]


def test_get_complete_trail_scout_gpx_and_altimetry_errors():
    payload = {
        "features": [
            {
                "properties": {"summary": {"distance": 40000}, "ascent": 500},
                "geometry": {"coordinates": [[10.0, 45.0, 100], [10.001, 45.001, 101]]},
            }
        ]
    }
    session = FakeSession(response=FakeResponse(payload=payload))
    service = TrailScoutService(
        config=TrailScoutConfig(),
        http_session=session,
        surface_analyzer=lambda *args, **kwargs: {"status": "Error"},
        gpx_generator=lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("gpx fail")),
        altimetry_getter=lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("alt fail")),
        uuid_func=lambda: "fixedid",
    )

    rider = make_rider()
    bike = make_bike()
    mission = make_mission()

    result = service.get_complete_trail_scout(
        api_key="key",
        latitude=45.0,
        longitude=10.0,
        rider=rider,
        bike=bike,
        mission=mission,
        include_gpx=True,
        include_altimetry=True,
    )

    assert result["status"] == "Success"
    assert result["gpx_error"] == "GPX failed: gpx fail"
    assert result["elevation_error"] == "Altimetry failed: alt fail"


def test_request_route_candidate_uses_heigit_endpoint():
    session = FakeSession(response=FakeResponse(payload={"features": []}))
    service = TrailScoutService(http_session=session)

    service._request_route_candidate(
        "key",
        make_mission(profile="cycling-mountain"),
        {"coordinates": [[9.0, 45.0], [9.1, 45.1]]},
    )

    assert session.calls[0]["url"] == (
        "https://api.heigit.org/openrouteservice/v2/directions/cycling-mountain/geojson"
    )


def test_get_complete_trail_scout_master_error():
    session = FakeSession(exc=requests.exceptions.RequestException("network down"))
    service = make_service(session)

    rider = make_rider()
    bike = make_bike()
    mission = make_mission()

    result = service.get_complete_trail_scout(
        api_key="key",
        latitude=45.0,
        longitude=10.0,
        rider=rider,
        bike=bike,
        mission=mission,
    )

    assert result["status"] == "Error"
    assert "Master Orchestrator failed: network down" == result["error_message"]
    assert "network down" in result["error_traceback"]


def test_module_level_wrapper(monkeypatch):
    class FakeService:
        def __init__(self):
            self.calls = []

        def get_complete_trail_scout(self, **kwargs):
            self.calls.append(kwargs)
            return {"status": "Success"}

    fake_service = FakeService()
    monkeypatch.setattr(scouting_module, "service", fake_service)

    result = get_complete_trail_scout(
        api_key="key",
        latitude=45.0,
        longitude=10.0,
        rider=make_rider(),
        bike=make_bike(),
        mission=make_mission(),
    )

    assert result == {"status": "Success"}
    assert len(fake_service.calls) == 1
