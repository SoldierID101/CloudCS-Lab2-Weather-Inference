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
    monkeypatch.setenv("PRIVILEGED_CLIENT_ID", "privileged-client")

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


def test_predictions_for_privileged_client(client, test_app, monkeypatch) -> None:
    def mock_decode_token(token: str):
        return {"client_id": "privileged-client"}

    monkeypatch.setattr(test_app, "decode_token", mock_decode_token)

    response = client.post(
        "/predictions",
        headers={"Authorization": "Bearer fake-token"},
        json=sample_json,
    )

    assert response.status_code == 200
    assert response.json() == {
        "prediction": {"temperature": 27.5},
        "client_id": "privileged-client",
    }


def test_predictions_for_unprivileged_client(
    client,
    test_app,
    monkeypatch,
) -> None:
    def mock_decode_token(token: str):
        return {"client_id": "unprivileged-client"}

    monkeypatch.setattr(test_app, "decode_token", mock_decode_token)

    response = client.post(
        "/predictions",
        headers={"Authorization": "Bearer fake-token"},
        json=sample_json,
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "This client is not allowed to access /predictions",
    }


def test_predictions_without_token(client) -> None:
    response = client.post("/predictions", json=sample_json)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_predictions_with_invalid_token_format(
    client,
    test_app,
    monkeypatch,
) -> None:
    def mock_decode_token(token: str):
        raise test_app.HTTPException(
            status_code=test_app.status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )

    monkeypatch.setattr(test_app, "decode_token", mock_decode_token)

    response = client.post(
        "/predictions",
        headers={"Authorization": "Bearer bad-token"},
        json=sample_json,
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token format"}
