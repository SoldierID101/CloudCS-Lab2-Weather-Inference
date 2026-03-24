# -*- coding: utf-8 -*-

import os

import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from model_utils import load_model, make_inference


# Загружаем .env из корня проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH, override=True)

# Конфигурация
MODEL_PATH_ENV = os.getenv("MODEL_PATH")
if not MODEL_PATH_ENV:
    raise ValueError("The environment variable MODEL_PATH is empty!")

# Превращаем путь к модели в абсолютный
if os.path.isabs(MODEL_PATH_ENV):
    MODEL_PATH = MODEL_PATH_ENV
else:
    MODEL_PATH = os.path.join(BASE_DIR, MODEL_PATH_ENV)

KEYCLOAK_SERVER_URL = os.getenv(
    "KEYCLOAK_SERVER_URL",
    "http://localhost:8080",
)
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "inference")

INFERENCE_CLIENT_ID = os.getenv("INFERENCE_CLIENT_ID")
INFERENCE_CLIENT_SECRET = os.getenv("INFERENCE_CLIENT_SECRET")
PRIVILEGED_CLIENT_ID = os.getenv("PRIVILEGED_CLIENT_ID")

if (
    not INFERENCE_CLIENT_ID
    or not INFERENCE_CLIENT_SECRET
    or not PRIVILEGED_CLIENT_ID
):
    raise ValueError("Keycloak client settings are missing in .env")

INTROSPECT_URL = (
    f"{KEYCLOAK_SERVER_URL}/realms/"
    f"{KEYCLOAK_REALM}/protocol/openid-connect/token/introspect"
)

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Instance(BaseModel):
    hour: int
    month: int
    precipitation: float
    pressure: float
    humidity: float
    wind_speed: float
    latitude: float
    longitude: float
    height: float


def introspect_token(token: str) -> dict:
    try:
        response = requests.post(
            INTROSPECT_URL,
            data={"token": token},
            auth=(INFERENCE_CLIENT_ID, INFERENCE_CLIENT_SECRET),
            timeout=10,
        )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Keycloak is unavailable: {str(e)}",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to introspect token",
        )

    data = response.json()

    if not data.get("active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive token",
        )

    return data


def verify_privileged_client(token: str = Depends(oauth2_scheme)) -> dict:
    token_data = introspect_token(token)
    token_client_id = token_data.get("client_id") or token_data.get("azp")

    if token_client_id != PRIVILEGED_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This client is not allowed to access /predictions",
        )

    return token_data


@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}


@app.post("/predictions")
def predict(
    instance: Instance,
    token_data: dict = Depends(verify_privileged_client),
):
    try:
        model = load_model(MODEL_PATH)
        prediction = make_inference(model, instance.dict())
        return {
            "prediction": prediction,
            "client_id": token_data.get(
                "client_id",
                token_data.get("azp"),
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
