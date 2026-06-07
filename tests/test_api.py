from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.gemini import GeminiClient
from tests.conftest import TEST_API_KEY


def test_ui_serves_html(test_client: TestClient) -> None:
    resp = test_client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert b"raw-api-agent" in resp.content


def test_health_ok(test_client: TestClient) -> None:
    resp = test_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "model" in data
    assert "timestamp" in data


def test_health_no_auth_needed(test_client: TestClient) -> None:
    resp = test_client.get("/health")
    assert resp.status_code == 200


def test_run_valid_goal(test_client: TestClient) -> None:
    resp = test_client.post(
        "/agent/run",
        json={"goal": "say hello"},
        headers={"X-API-Key": TEST_API_KEY},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Final answer from agent."
    assert data["partial"] is False


def test_run_missing_api_key(test_client: TestClient) -> None:
    resp = test_client.post("/agent/run", json={"goal": "say hello"})
    assert resp.status_code == 422


def test_run_wrong_api_key(test_client: TestClient) -> None:
    resp = test_client.post(
        "/agent/run",
        json={"goal": "say hello"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401


def test_run_empty_goal(test_client: TestClient) -> None:
    resp = test_client.post(
        "/agent/run",
        json={"goal": ""},
        headers={"X-API-Key": TEST_API_KEY},
    )
    assert resp.status_code == 422


def test_run_goal_too_long(test_client: TestClient) -> None:
    resp = test_client.post(
        "/agent/run",
        json={"goal": "x" * 4001},
        headers={"X-API-Key": TEST_API_KEY},
    )
    assert resp.status_code == 422


def test_stream_returns_sse(
    settings: Settings, mock_gemini_tool_then_final: GeminiClient
) -> None:
    from app.core.config import get_settings
    from app.core.gemini import get_gemini_client
    from app.main import create_app

    application = create_app()
    application.dependency_overrides[get_settings] = lambda: settings
    application.dependency_overrides[get_gemini_client] = (
        lambda: mock_gemini_tool_then_final
    )

    with (
        patch("app.main.get_settings", return_value=settings),
        TestClient(application) as client,
    ):
        resp = client.post(
            "/agent/stream",
            json={"goal": "stream this"},
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "event:" in body
    assert "data:" in body

    application.dependency_overrides.clear()


def test_stream_wrong_key(test_client: TestClient) -> None:
    resp = test_client.post(
        "/agent/stream",
        json={"goal": "stream this"},
        headers={"X-API-Key": "bad"},
    )
    assert resp.status_code == 401


def test_run_partial_result(
    settings: Settings, mock_gemini_max_iter: GeminiClient
) -> None:
    from app.core.config import get_settings
    from app.core.gemini import get_gemini_client
    from app.main import create_app

    application = create_app()
    application.dependency_overrides[get_settings] = lambda: settings
    application.dependency_overrides[get_gemini_client] = lambda: mock_gemini_max_iter

    with (
        patch("app.main.get_settings", return_value=settings),
        TestClient(application) as client,
    ):
        resp = client.post(
            "/agent/run",
            json={"goal": "loop forever"},
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["partial"] is True
    assert data["error"] == "max_iterations_reached"

    application.dependency_overrides.clear()
