from types import SimpleNamespace

import pytest

import bikescout.tools.surface as surface_module
from bikescout.tools.surface import (
    SurfaceAnalyzerConfig,
    SurfaceAnalyzerService,
    _categorize_climb,
    _extract_dominant_surface,
    _sanitize_elevation_profile,
    _cap_implausible_ascent,
    get_surface_analyzer,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self.payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses=None):
        self.responses = responses or []
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
        if not self.responses:
            raise RuntimeError("No fake responses available")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture
def rider():
    return SimpleNamespace(weight_kg=78.0, fitness_level="medium")


@pytest.fixture
def bike():
    return SimpleNamespace(
        bike_type="gravel",
        tire_size="700c",
        tire_width_mm=40,
        battery_wh=0,
    )


@pytest.fixture
def mission():
    return SimpleNamespace(
        total_length_km=25.0,
        profile="cycling-regular",
        complexity=10,
        seed=42,
        surface_preference=None,
        assist_mode="Trail",
    )


def test_sanitize_elevation_profile_short_geometry_returns_zero():
    geometry = [[10, 45, 100], [10.001, 45.001, 101]]
    assert _sanitize_elevation_profile(geometry, window_size=11, threshold=2.0) == 0.0


def test_sanitize_elevation_profile_accumulates_ascent():
    geometry = []
    elevations = [100, 101, 103, 106, 108, 110, 111, 109, 107, 105, 104, 106, 108, 110, 112]
    for idx, ele in enumerate(elevations):
        geometry.append([10 + idx * 0.001, 45 + idx * 0.001, ele])

    result = _sanitize_elevation_profile(geometry, window_size=3, threshold=1.0)
    assert result >= 0.0


def test_categorize_climb_flat():
    category, gradient = _categorize_climb(20, 10000, "road")
    assert category == "Flat / Rolling"
    assert gradient >= 0


def test_categorize_climb_hc():
    category, gradient = _categorize_climb(1200, 20000, "road")
    assert category == "Hors Catégorie (HC)"
    assert gradient <= 20.0


def test_categorize_climb_enduro_prefix():
    category, gradient = _categorize_climb(400, 5000, "enduro")
    assert category.startswith("Enduro Tech:")
    assert gradient <= 25.0


def test_categorize_climb_mtb_branch():
    category, gradient = _categorize_climb(250, 4000, "mtb")
    assert category in {
        "C1 - Brutal Ascent",
        "C2 - Hard Climb",
        "C3 - Challenging",
        "C4 - Short Burner",
        "Hors Catégorie (HC)",
    }
    assert gradient <= 20.0


def test_extract_dominant_surface_missing_returns_unknown():
    assert _extract_dominant_surface(None, {}) == "Unknown"
    assert _extract_dominant_surface({}, {}) == "Unknown"


def test_extract_dominant_surface_success():
    surface_extra = {
        "summary": [
            {"value": 1, "distance": 1000},
            {"value": 5, "distance": 2000},
        ]
    }
    surface_map = {1: "Asphalt", 5: "Gravel"}
    assert _extract_dominant_surface(surface_extra, surface_map) == "Gravel"


@pytest.fixture
def service():
    return SurfaceAnalyzerService(
        config=SurfaceAnalyzerConfig(),
        http_session=FakeSession(),
        mud_analyzer=lambda lat, lon, surface, target_date: {
            "metadata": {"target_date": "2026-06-03T00:00:00+00:00"},
            "tactical_analysis": {
                "mud_risk_numeric": 3.5,
                "mud_risk_score": "Medium",
                "traction_risk": {"level": "Medium"},
                "trail_damage_risk": {"level": "Low"},
                "dry_time_eta": "8 hours",
            },
        },
        compatibility_analyzer=lambda bike_type, tire_width_mm, extras, surface_map: (
            [{"type": "Gravel", "percentage": "70%"}, {"type": "Asphalt", "percentage": "30%"}],
            ["Caution"],
            True,
        ),
        tire_setup_getter=lambda **kwargs: (40, "700c wheels | 35.0 PSI (2.41 Bar) [Standard Setup]"),
        battery_drain_calculator=lambda **kwargs: {"status": "Success", "battery_metrics": {}},
    )


def test_safe_complexity(service):
    assert service._safe_complexity(1) == 3
    assert service._safe_complexity(50) == 30
    assert service._safe_complexity("bad") == 10


def test_safe_length_m(service):
    assert service._safe_length_m(12.5) == 12500
    assert service._safe_length_m("bad") == 0


def test_attempts_for_profile(service):
    assert service._attempts_for_profile("cycling-electric")[0][0] == "cycling-mountain"
    assert service._attempts_for_profile("cycling-mountain")[0][0] == "cycling-mountain"
    assert service._attempts_for_profile("cycling-road")[0][0] == "cycling-road"
    assert service._attempts_for_profile("other")[0][0] == "cycling-regular"


def test_request_body_avoid_unpaved(service, mission):
    mission.surface_preference = "avoid_unpaved"
    body = service._request_body(45.0, 10.0, mission, 10000, 8, ["surface"])

    assert body["coordinates"] == [[10.0, 45.0]]
    assert body["extra_info"] == ["surface"]
    assert body["options"]["avoid_features"] == ["unpaved"]


def test_request_body_prefer_paved(service, mission):
    mission.surface_preference = "prefer_paved"
    body = service._request_body(45.0, 10.0, mission, 10000, 8, ["surface"])

    assert body["options"]["avoid_polygons"] == {}
    assert body["options"]["avoid_features"] == ["unpaved"]


def test_geometry_distance_m(service):
    geometry = [
        [10.0, 45.0, 100],
        [10.001, 45.001, 101],
        [10.002, 45.002, 102],
    ]
    assert service._geometry_distance_m(geometry) > 0


def test_flat_surface_breakdown(service):
    breakdown = [{"type": "gravel", "percentage": "70%"}, {"type": "asphalt", "percentage": "30%"}]
    assert service._flat_surface_breakdown(breakdown) == {"Gravel": 70, "Asphalt": 30}


def test_flat_surface_breakdown_invalid(service):
    assert service._flat_surface_breakdown("bad") == {}
    assert service._flat_surface_breakdown([{"type": "gravel", "percentage": None}]) == {}


def test_emtb_analysis_non_emtb(service, bike, rider, mission):
    result = service._emtb_analysis(bike, rider, mission, 500, 20000, [], 2.0)
    assert result is None


def test_emtb_analysis_success(service, rider, mission):
    bike = SimpleNamespace(
        bike_type="E-MTB",
        battery_wh=625,
    )
    result = service._emtb_analysis(
        bike=bike,
        rider=rider,
        mission=mission,
        clean_ascent=500,
        real_dist_m=20000,
        breakdown=[{"type": "gravel", "percentage": "70%"}],
        mud_score_val=2.0,
    )
    assert result == {"status": "Success", "battery_metrics": {}}


def test_emtb_analysis_battery_failure(rider, mission):
    service = SurfaceAnalyzerService(
        config=SurfaceAnalyzerConfig(),
        http_session=FakeSession(),
        mud_analyzer=lambda *args, **kwargs: {},
        compatibility_analyzer=lambda *args, **kwargs: ([], [], True),
        tire_setup_getter=lambda **kwargs: (40, "setup"),
        battery_drain_calculator=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    bike = SimpleNamespace(
        bike_type="E-MTB",
        battery_wh=625,
    )

    result = service._emtb_analysis(
        bike=bike,
        rider=rider,
        mission=mission,
        clean_ascent=500,
        real_dist_m=20000,
        breakdown=[],
        mud_score_val=2.0,
    )
    assert result == {"error": "Battery calculation failed"}


def test_get_surface_analyzer_success(service, rider, bike, mission):
    payload = {
        "features": [
            {
                "properties": {
                    "extras": {
                        "surface": {
                            "summary": [
                                {"value": 5, "distance": 2000},
                                {"value": 1, "distance": 1000},
                            ]
                        },
                        "waytype": {},
                    }
                },
                "geometry": {
                    "coordinates": [
                        [10.0, 45.0, 100],
                        [10.001, 45.001, 102],
                        [10.002, 45.002, 105],
                        [10.003, 45.003, 103],
                        [10.004, 45.004, 108],
                        [10.005, 45.005, 110],
                        [10.006, 45.006, 115],
                        [10.007, 45.007, 111],
                    ]
                },
            }
        ]
    }

    service.http_session = FakeSession(responses=[FakeResponse(status_code=200, payload=payload)])

    result = service.get_surface_analyzer("key", 45.0, 10.0, rider, bike, mission)

    assert result["status"] == "Success"
    assert result["profile_used"] == "cycling-regular"
    assert result["metadata"]["api_extras"] == ["surface", "waytype"]
    assert result["mechanical_setup"]["compatible"] is True
    assert result["emtb_tactical"] is None


def test_get_surface_analyzer_success_with_emtb(service, rider, mission):
    bike = SimpleNamespace(
        bike_type="E-MTB",
        tire_size="29",
        tire_width_mm=60,
        battery_wh=625,
    )
    payload = {
        "features": [
            {
                "properties": {"extras": {"surface": {"summary": [{"value": 5, "distance": 1000}]}}},
                "geometry": {
                    "coordinates": [
                        [10.0, 45.0, 100],
                        [10.001, 45.001, 102],
                        [10.002, 45.002, 105],
                        [10.003, 45.003, 103],
                        [10.004, 45.004, 108],
                        [10.005, 45.005, 110],
                        [10.006, 45.006, 115],
                        [10.007, 45.007, 111],
                    ]
                },
            }
        ]
    }
    service.http_session = FakeSession(responses=[FakeResponse(status_code=200, payload=payload)])

    result = service.get_surface_analyzer("key", 45.0, 10.0, rider, bike, mission)

    assert result["status"] == "Success"
    assert result["emtb_tactical"] == {"status": "Success", "battery_metrics": {}}


def test_get_surface_analyzer_fallback_after_ors_error(service, rider, bike, mission):
    mission.profile = "cycling-mountain"
    service.http_session = FakeSession(
        responses=[
            FakeResponse(status_code=400, payload={"error": {"message": "bad request"}}, text="bad request"),
            FakeResponse(
                status_code=200,
                payload={
                    "features": [
                        {
                            "properties": {"extras": {"surface": {"summary": [{"value": 1, "distance": 1000}]}}},
                            "geometry": {
                                "coordinates": [
                                    [10.0, 45.0, 100],
                                    [10.001, 45.001, 101],
                                    [10.002, 45.002, 102],
                                    [10.003, 45.003, 103],
                                    [10.004, 45.004, 104],
                                    [10.005, 45.005, 105],
                                    [10.006, 45.006, 106],
                                    [10.007, 45.007, 107],
                                ]
                            },
                        }
                    ]
                },
            ),
        ]
    )

    result = service.get_surface_analyzer("key", 45.0, 10.0, rider, bike, mission)

    assert result["status"] == "Success"
    assert result["profile_used"] == "cycling-regular"


def test_get_surface_analyzer_returns_global_failure_after_all_attempts(service, rider, bike, mission):
    service.http_session = FakeSession(
        responses=[
            FakeResponse(status_code=400, payload={"error": {"message": "bad1"}}, text="bad1"),
            FakeResponse(status_code=500, payload={}, text="bad2"),
        ]
    )

    result = service.get_surface_analyzer("key", 45.0, 10.0, rider, bike, mission)

    assert result["status"] == "Error"
    assert "Global failure:" in result["message"]


def test_get_surface_analyzer_handles_local_processing_error(service, rider, bike, mission):
    service.http_session = FakeSession(
        responses=[
            FakeResponse(status_code=200, payload={"features": []}),
            FakeResponse(status_code=200, payload={"features": []}),
        ]
    )

    result = service.get_surface_analyzer("key", 45.0, 10.0, rider, bike, mission)

    assert result["status"] == "Error"
    assert "Global failure: Local processing error:" in result["message"]


def test_module_level_wrapper(monkeypatch, rider, bike, mission):
    class FakeService:
        def __init__(self):
            self.calls = []

        def get_surface_analyzer(self, **kwargs):
            self.calls.append(kwargs)
            return {"status": "Success"}

    fake_service = FakeService()
    monkeypatch.setattr(surface_module, "service", fake_service)

    result = get_surface_analyzer("key", 45.0, 10.0, rider, bike, mission)

    assert result == {"status": "Success"}
    assert len(fake_service.calls) == 1

def test_sanitize_elevation_profile_limits_spiky_ascent():
    geometry = [
        [10.0, 45.0, 100],
        [10.001, 45.001, 500],
        [10.002, 45.002, 105],
        [10.003, 45.003, 520],
        [10.004, 45.004, 110],
        [10.005, 45.005, 530],
        [10.006, 45.006, 115],
        [10.007, 45.007, 540],
        [10.008, 45.008, 120],
        [10.009, 45.009, 125],
        [10.010, 45.010, 130],
        [10.011, 45.011, 132],
    ]

    result = _sanitize_elevation_profile(
        geometry,
        window_size=5,
        threshold=3.0,
        max_step_up_m=25.0,
        max_step_down_m=25.0,
    )

    assert result < 300

def test_cap_implausible_ascent_for_mtb_route():
    capped = _cap_implausible_ascent(
        total_ascent_m=7284,
        total_dist_m=44950,
        bike_type="mtb",
    )

    assert capped == round((44.95 * 140.0), 0)