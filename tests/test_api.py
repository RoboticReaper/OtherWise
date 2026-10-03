"""API privacy/auth/resource contracts exercised through real ASGI requests."""

import importlib
import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
import httpx
from fastapi.testclient import TestClient

from test_service import make_engine


TOKEN = "test-local-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
PAYLOAD = {"keywords": ["First"], "mode": "path", "focus": "First", "expansion_level": 0, "limit": 10}


def app_factory(**kwargs):
    try:
        create_app = importlib.import_module("service.api").create_app
    except ModuleNotFoundError:
        pytest.fail("The recommendation API has not been implemented.")
    return create_app(**kwargs)


@pytest.fixture
def client():
    engine = make_engine(["Bridge", "Outside"], [.32, .8])
    with TestClient(app_factory(engine=engine, token=TOKEN)) as session:
        yield session


def test_authenticated_post_and_health_have_no_secrets(client):
    response = client.post("/api/recommend", headers=AUTH, json=PAYLOAD)
    assert response.status_code == 200
    result = response.json()
    assert set(result) == {"recommendations", "mode", "expansion_level"}
    assert result["recommendations"][0]["id"] == "Bridge"
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ready"] is True
    assert TOKEN not in health.text


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong"}, {"Authorization": "Basic test-local-token"}])
def test_missing_or_wrong_bearer_cannot_recommend(client, headers):
    assert client.post("/api/recommend", headers=headers, json=PAYLOAD).status_code == 401


def test_absent_configuration_denies_even_a_supplied_token(monkeypatch):
    monkeypatch.delenv("OTHERWISE_API_TOKEN", raising=False)
    with TestClient(app_factory(engine=make_engine(["A"], [.32]))) as session:
        assert session.post("/api/recommend", headers=AUTH, json=PAYLOAD).status_code == 401


def test_environment_token_is_used(monkeypatch):
    monkeypatch.setenv("OTHERWISE_API_TOKEN", TOKEN)
    with TestClient(app_factory(engine=make_engine(["A"], [.32]))) as session:
        assert session.post("/api/recommend", headers=AUTH, json=PAYLOAD).status_code == 200


@pytest.mark.parametrize("patch", [
    {"keywords": []}, {"keywords": ["A"] * 41}, {"keywords": [" "]},
    {"keywords": ["x" * 121]}, {"keywords": ["private\ntext"]}, {"keywords": [42]},
    {"keywords": ["!!!"]}, {"focus": "Not approved"}, {"mode": "invalid"},
    {"expansion_level": -1}, {"expansion_level": 9}, {"expansion_level": True},
    {"expansion_level": "1"}, {"limit": 0}, {"limit": 101}, {"limit": 1.5}, {"limit": True},
    {"raw_url": "https://private.example/secret"}, {"history": ["private browsing record"]},
])
def test_invalid_extra_and_unbounded_inputs_are_rejected_without_echo(client, patch):
    response = client.post("/api/recommend", headers=AUTH, json=PAYLOAD | patch)
    assert response.status_code == 422
    assert "private" not in response.text
    assert "Not approved" not in response.text
    assert "https://" not in response.text


@pytest.mark.parametrize("name", ["radius", "expansion", "overlap", "diversity", "max_overlap_fraction", "randomness"])
@pytest.mark.parametrize("value", [True, "0.2", None, -0.01, 1.01, float("nan"), float("inf"), -float("inf")])
def test_recommendation_controls_reject_invalid_numbers_without_echo(client, name, value):
    response = client.post("/api/recommend", headers=AUTH | {"Content-Type": "application/json"},
                           content=json.dumps(PAYLOAD | {name: value}))
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid recommendation request."}


def test_overlap_share_has_a_stricter_upper_bound(client):
    assert client.post("/api/recommend", headers=AUTH,
                       json=PAYLOAD | {"max_overlap_fraction": .96}).status_code == 422


def test_custom_controls_change_the_band_and_actual_familiar_share():
    engine = make_engine(["Too close", "Overlap A", "Overlap B", "New A", "New B", "Too far"],
                         [.1, .22, .24, .31, .34, .6])
    controls = {"radius": .3, "expansion": .1, "overlap": .1,
                "diversity": 0, "max_overlap_fraction": .5, "randomness": 0}
    with TestClient(app_factory(engine=engine, token=TOKEN)) as session:
        response = session.post("/api/recommend", headers=AUTH, json=PAYLOAD | controls)
        assert response.status_code == 200
        recommendations = response.json()["recommendations"]
        assert {row["id"] for row in recommendations} == {"Overlap A", "Overlap B", "New A", "New B"}
        assert sum(row["zone"] == "Familiar overlap" for row in recommendations) == 2
        without_overlap = session.post("/api/recommend", headers=AUTH,
                                       json=PAYLOAD | controls | {"max_overlap_fraction": 0})
        assert {row["id"] for row in without_overlap.json()["recommendations"]} == {"New A", "New B"}


def test_api_returns_more_than_twenty_when_the_requested_band_has_room():
    engine = make_engine([f"Topic {i}" for i in range(60)], [.30 + i * .0005 for i in range(60)])
    with TestClient(app_factory(engine=engine, token=TOKEN)) as session:
        response = session.post("/api/recommend", headers=AUTH, json=PAYLOAD | {"limit": 50, "randomness": 0})
        assert response.status_code == 200
        recommendations = response.json()["recommendations"]
        assert len(recommendations) == len({row["id"] for row in recommendations}) == 50
        sparse = session.post("/api/recommend", headers=AUTH, json=PAYLOAD | {"limit": 100, "randomness": 0})
        assert sparse.status_code == 200
        assert len(sparse.json()["recommendations"]) == 60


def test_missing_fields_and_malformed_json_never_echo_input(client):
    incomplete = client.post("/api/recommend", headers=AUTH, json={"keywords": ["private phrase"]})
    malformed = client.post("/api/recommend", headers=AUTH, content='{"private phrase":', )
    assert incomplete.status_code == malformed.status_code == 422
    assert "private phrase" not in incomplete.text + malformed.text


def test_body_limit_applies_without_trusting_content_length(client):
    response = client.post("/api/recommend", headers=AUTH, content=b"x" * 17000)
    assert response.status_code == 413
    assert len(response.text) < 200


def test_streamed_body_is_bounded_even_without_content_length():
    async def check():
        app = app_factory(engine=make_engine(["A"], [.32]), token=TOKEN)
        async def chunks():
            yield b"x" * 8000
            yield b"x" * 9000

        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://local.test") as session:
                response = await session.post("/api/recommend", headers=AUTH, content=chunks())
                assert response.status_code == 413
                assert len(response.text) < 200

    asyncio.run(check())


def test_unauthenticated_body_is_denied_before_payload_parsing(client):
    result = client.post("/api/recommend", content=b"private phrase" * 2000)
    assert result.status_code == 401
    assert "private phrase" not in result.text


def test_focus_membership_uses_trimmed_approved_keyword(client):
    response = client.post("/api/recommend", headers=AUTH, json=PAYLOAD | {"keywords": [" First "], "focus": "First"})
    assert response.status_code == 200


def test_cors_accepts_extension_and_refuses_unconfigured_web_origin(client):
    preflight = {"Origin": "chrome-extension://" + "a" * 32, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,content-type"}
    extension = client.options("/api/recommend", headers=preflight)
    assert extension.status_code == 200
    assert extension.headers["access-control-allow-origin"] == preflight["Origin"]
    other = client.options("/api/recommend", headers=preflight | {"Origin": "https://unconfigured.example"})
    assert "access-control-allow-origin" not in other.headers


def test_rate_limit_does_not_keep_profile_or_echo_payload(client):
    responses = [client.post("/api/recommend", headers=AUTH, json=PAYLOAD) for _ in range(31)]
    assert responses[-1].status_code == 429
    assert "First" not in responses[-1].text
    assert responses[-1].headers.get("retry-after")


def test_model_failure_is_unready_and_never_a_synthetic_success():
    class BrokenEngine:
        ready = False

        def initialize(self):
            raise RuntimeError("private model download credential")

    with TestClient(app_factory(engine=BrokenEngine(), token=TOKEN)) as session:
        health = session.get("/health")
        assert health.status_code == 503
        assert health.json()["ready"] is False
        result = session.post("/api/recommend", headers=AUTH, json=PAYLOAD)
        assert result.status_code == 503
        assert "private" not in health.text + result.text


def test_inference_failure_is_safe_and_next_request_can_recover(caplog):
    class FlakyEngine:
        ready = True
        first = True

        def initialize(self):
            pass

        def recommend(self, *args, **kwargs):
            if self.first:
                self.first = False
                raise RuntimeError("private interest in model error")
            return []

    with TestClient(app_factory(engine=FlakyEngine(), token=TOKEN)) as session:
        failed = session.post("/api/recommend", headers=AUTH, json=PAYLOAD)
        assert failed.status_code == 503
        assert "private" not in failed.text
        assert session.post("/api/recommend", headers=AUTH, json=PAYLOAD).status_code == 200
    assert "private interest" not in caplog.text


def test_second_compute_is_rejected_while_first_runs():
    started, release = threading.Event(), threading.Event()

    class SlowEngine:
        ready = True

        def initialize(self):
            pass

        def recommend(self, *args, **kwargs):
            started.set()
            assert release.wait(5)
            return []

    with TestClient(app_factory(engine=SlowEngine(), token=TOKEN)) as session:
        with ThreadPoolExecutor(max_workers=1) as pool:
            first = pool.submit(session.post, "/api/recommend", headers=AUTH, json=PAYLOAD)
            try:
                assert started.wait(5)
                second = session.post("/api/recommend", headers=AUTH, json=PAYLOAD)
                assert second.status_code == 429
            finally:
                release.set()
            assert first.result().status_code == 200
