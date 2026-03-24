# -*- coding: utf-8 -*-

import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import BaseModel

from model_utils import load_model, make_inference


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH, override=True)

MODEL_PATH_ENV = os.getenv("MODEL_PATH")
if not MODEL_PATH_ENV:
    raise ValueError("The environment variable MODEL_PATH is empty!")

if os.path.isabs(MODEL_PATH_ENV):
    MODEL_PATH = MODEL_PATH_ENV
else:
    MODEL_PATH = os.path.join(BASE_DIR, MODEL_PATH_ENV)

PRIVILEGED_CLIENT_ID = os.getenv("PRIVILEGED_CLIENT_ID")
if not PRIVILEGED_CLIENT_ID:
    raise ValueError("PRIVILEGED_CLIENT_ID is missing in .env")

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


def decode_token(token: str) -> dict:
    try:
        return jwt.get_unverified_claims(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )


def verify_privileged_client(token: str = Depends(oauth2_scheme)) -> dict:
    token_data = decode_token(token)

    token_client_id = token_data.get("client_id") or token_data.get("azp")

    if not token_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain client identity",
        )

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
