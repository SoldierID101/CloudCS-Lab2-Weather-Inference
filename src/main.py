# -*- coding: utf-8 -*-
import os
from model_utils import load_model, make_inference
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


# Описание входных данных для инференса.
# Этот класс определяет, какие поля сервис ожидает от клиента.
# FastAPI автоматически валидирует входной JSON по этой схеме.
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

# Создаем экземпляр FastAPI-приложения
app = FastAPI()

# Настраиваем схему авторизации через Bearer Token.
# tokenUrl здесь нужен Swagger/FastAPI для описания безопасности.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")

# Читаем путь к модели из переменной окружения.
# Это удобно: один и тот же код можно запускать с разными моделями.
model_path: str = os.getenv("MODEL_PATH")

# Если путь не передан, сервис не должен запускаться.
if model_path is None:
    raise ValueError("The environment variable $MODEL_PATH is empty!")

# Функция проверки токена.
# В учебной работе используется "заглушка":
# корректным токеном считается строка "00000".
async def is_token_correct(token: str) -> bool:
    dummy_correct_token = "00000"
    return token == dummy_correct_token

# Зависимость FastAPI для проверки токена перед доступом к защищенному endpoint.
# Если токен неверный, возвращаем ошибку 401 Unauthorized.
async def check_token(token: str = Depends(oauth2_scheme)) -> None:
    if not await is_token_correct(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Простейший endpoint для проверки, что сервис запущен и отвечает.
@app.get("/healthcheck")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

# Основной endpoint для инференса.
# Сюда клиент отправляет погодные признаки,
# а сервис возвращает предсказанную температуру.
@app.post("/predictions")
async def predictions(
    instance: Instance,
    token: str = Depends(check_token)
) -> dict[str, float]:
    # instance.dict() превращает Pydantic-модель в обычный словарь
    # load_model(model_path) загружает pipeline из файла
    # make_inference(...) выполняет предсказание
    return make_inference(load_model(model_path), instance.dict())
