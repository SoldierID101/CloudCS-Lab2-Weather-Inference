# -*- coding: utf-8 -*-

import pytest
from fastapi.testclient import TestClient


# Фикстура создает тестовый клиент FastAPI.
# Здесь же мы "подменяем" настоящую модель на фиктивную,
# чтобы тесты были быстрыми и не зависели от реального файла модели.
@pytest.fixture
def init_test_client(monkeypatch) -> TestClient:
    def mock_make_inference(*args, **kwargs):
        return {"temperature": 27.5}

    def mock_load_model(*args, **kwargs):
        return None

    monkeypatch.setenv("MODEL_PATH", "faked/model.pkl")

    # 🔥 ДОБАВИТЬ ЭТО
    monkeypatch.setenv("INFERENCE_CLIENT_ID", "test-client")
    monkeypatch.setenv("INFERENCE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("PRIVILEGED_CLIENT_ID", "privileged-client")
    monkeypatch.setenv("KEYCLOAK_SERVER_URL", "http://localhost:8080")
    monkeypatch.setenv("KEYCLOAK_REALM", "inference")

    monkeypatch.setattr("model_utils.make_inference", mock_make_inference)
    monkeypatch.setattr("model_utils.load_model", mock_load_model)

    from main import app
    return TestClient(app)


# Пример корректного тела запроса.
# Используется во многих тестах, чтобы не дублировать JSON.
sample_json = {
    "hour": 12,
    "month": 6,
    "precipitation": 0.0,
    "pressure": 1008.0,
    "humidity": 75.0,
    "wind_speed": 3.5,
    "latitude": -3.1,
    "longitude": -60.0,
    "height": 61.25
}


# Проверка, что endpoint /healthcheck доступен и работает корректно.
def test_healthcheck(init_test_client) -> None:
    response = init_test_client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# Проверка корректного токена.
# Ожидаем успешный ответ и наличие поля temperature.
def test_token_correctness(init_test_client) -> None:
    response = init_test_client.post(
        "/predictions",
        headers={"Authorization": "Bearer 00000"},
        json=sample_json
    )
    assert response.status_code == 200
    assert "temperature" in response.json()


# Проверка некорректного токена.
# Сервис должен вернуть 401 Unauthorized.
def test_token_not_correctness(init_test_client):
    response = init_test_client.post(
        "/predictions",
        headers={"Authorization": "Bearer kedjkj"},
        json=sample_json
    )
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid authentication credentials"
    }


# Проверка отсутствия токена.
# В этом случае FastAPI сам возвращает ошибку авторизации.
def test_token_absent(init_test_client):
    response = init_test_client.post(
        "/predictions",
        json=sample_json
    )
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }


# Проверка самого инференса.
# Так как make_inference замокан, ожидаем ровно то значение,
# которое вернул mock_make_inference.
def test_inference(init_test_client):
    response = init_test_client.post(
        "/predictions",
        headers={"Authorization": "Bearer 00000"},
        json=sample_json
    )
    assert response.status_code == 200
    assert response.json()["temperature"] == 27.5
