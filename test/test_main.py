# -*- coding: utf-8 -*-

import importlib
import sys

import pytest
from fastapi.testclient import TestClient


sample_json = {
    "hour": 12,
    "month": 6,
    "precipitation": 0.0,
    "pressure": 1008.0,
    "humidity": 75.0,
    "wind_speed": 3.5,
    "latitude": -3.1,
    "longitude": -60.0,
    "height": 61.25,
}


@pytest.fixture
def test_app(monkeypatch):
    def mock_make_inference(*args, **kwargs):
        return {"temperature": 27.5}

    def mock_load_model(*args, **kwargs):
        return None

    monkeypatch.setenv("MODEL_PATH", "faked/model.pkl")
    monkeypatch.setenv("INFERENCE_CLIENT_ID", "test-client")
    monkeypatch.setenv("INFERENCE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("PRIVILEGED_CLIENT_ID", "privileged-client")
    monkeypatch.setenv("KEYCLOAK_SERVER_URL", "http://localhost:8080")
    monkeypatch.setenv("KEYCLOAK_REALM", "inference")

    monkeypatch.setattr("model_utils.make_inference", mock_make_inference)
    monkeypatch.setattr("model_utils.load_model", mock_load_model)

    if "main" in sys.modules:
        main_module = importlib.reload(sys.modules["main"])
    else:
        import main as main_module

    main_module.app.dependency_overrides = {}
    yield main_module
    main_module.app.dependency_overrides = {}


@pytest.fixture
def client(test_app):
    return TestClient(test_app.app)


def test_healthcheck(client) -> None:
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predictions_for_privileged_client(client, test_app) -> None:
    def mock_verify_privileged_client():
        return {"client_id": "privileged-client"}

    test_app.app.dependency_overrides[
        test_app.verify_privileged_client
    ] = mock_verify_privileged_client

    response = client.post("/predictions", json=sample_json)

    assert response.status_code == 200
    assert response.json() == {
        "prediction": {"temperature": 27.5},
        "client_id": "privileged-client",
    }


def test_predictions_without_token(client) -> None:
    response = client.post("/predictions", json=sample_json)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_predictions_for_unprivileged_client(client) -> None:
    response = client.post(
        "/predictions",
        headers={"Authorization": "Bearer fake-unprivileged-token"},
        json=sample_json,
    )
    assert response.status_code == 503


def test_inference_response_contains_temperature(client, test_app) -> None:
    def mock_verify_privileged_client():
        return {"client_id": "privileged-client"}

    test_app.app.dependency_overrides[
        test_app.verify_privileged_client
    ] = mock_verify_privileged_client

    response = client.post("/predictions", json=sample_json)

    assert response.status_code == 200
    assert response.json()["prediction"]["temperature"] == 27.5
